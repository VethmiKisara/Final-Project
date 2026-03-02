import os
import time
import traceback
from typing import Optional, Dict, Any

from db.mysql_conn import get_conn, fetchall_dict
from ai.model_integration_MOD import run_full_pipeline


# ---------- SQL helpers ----------
SQL_SELECT_UNPROCESSED = """
SELECT p.id, p.original_text, p.image_path
FROM posts p
LEFT JOIN pipeline_runs r ON r.post_id = p.id
WHERE r.post_id IS NULL
ORDER BY p.created_at ASC
LIMIT %s
"""

SQL_INSERT_PIPELINE_RUN = """
INSERT INTO pipeline_runs (post_id, used_text, used_image, location_id)
VALUES (%s, %s, %s, %s)
"""

SQL_INSERT_TASK_A = """
INSERT INTO task_a_results (run_id, a_text_prob, a_image_prob, a_fused_prob, a_label, a_confidence_level)
VALUES (%s, %s, %s, %s, %s, %s)
"""

SQL_INSERT_TASK_B = """
INSERT INTO task_b_results (run_id, b_text_prob, b_image_prob, b_fused_prob, b_label_class_id, b_confidence_level)
VALUES (%s, %s, %s, %s, %s, %s)
"""

# Upsert location by unique key (name,latitude,longitude)
# Use LAST_INSERT_ID trick to get id for both insert and update.
SQL_UPSERT_LOCATION = """
INSERT INTO locations (name, latitude, longitude, provider, place_id)
VALUES (%s, %s, %s, NULL, NULL)
ON DUPLICATE KEY UPDATE
  id = LAST_INSERT_ID(id),
  name = VALUES(name),
  latitude = VALUES(latitude),
  longitude = VALUES(longitude)
"""

SQL_SELECT_LOCATION_BY_ID = "SELECT id FROM locations WHERE id = %s"


def resolve_image_path(image_path: Optional[str]) -> Optional[str]:
    if image_path is None:
        return None
    p = str(image_path).strip()
    if not p:
        return None
    # If DB stores relative paths, resolve from project root (scripts/..)
    if not os.path.isabs(p):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        candidate = os.path.join(project_root, p)
        if os.path.exists(candidate):
            return candidate
    return p if os.path.exists(p) else None


def upsert_location(cur, selected_name: str, lat: float, lon: float) -> int:
    cur.execute(SQL_UPSERT_LOCATION, (selected_name, lat, lon))
    # mysql-connector provides lastrowid; with LAST_INSERT_ID trick, this is the location id
    return int(cur.lastrowid)


def process_one_post(cur, post: Dict[str, Any]) -> None:
    post_id = int(post["id"])
    text = post["original_text"]
    img_path_db = post.get("image_path")
    img_path = resolve_image_path(img_path_db)

    used_text = 1
    used_image = 1 if img_path is not None else 0

    result = run_full_pipeline(text=text, image_path=img_path)

    if not result.get("ok"):
        # If pipeline errors on text missing, skip insert; but your posts.original_text is NOT NULL anyway
        raise RuntimeError(f"Pipeline failed for post_id={post_id}: {result}")

    stageA = result["stageA"]
    is_informative = (stageA["prediction"] == "informative")
    a_label = 1 if is_informative else 0

    # location: insert only if informative and location resolved
    location_id = None
    if is_informative:
        loc = result.get("location") or {}
        selected_name = loc.get("selected_name")
        lat = loc.get("lat")
        lon = loc.get("lon")
        if selected_name is not None and lat is not None and lon is not None:
            location_id = upsert_location(cur, str(selected_name), float(lat), float(lon))

    # 1) pipeline_runs
    cur.execute(SQL_INSERT_PIPELINE_RUN, (post_id, used_text, used_image, location_id))
    run_id = int(cur.lastrowid)

    # 2) task_a_results
    cur.execute(
        SQL_INSERT_TASK_A,
        (
            run_id,
            float(stageA["text_prob_informative"]) if stageA["text_prob_informative"] is not None else None,
            float(stageA["image_prob_informative"]) if stageA["image_prob_informative"] is not None else None,
            float(stageA["fused_prob_informative"]),
            int(a_label),
            int(stageA["fused_confidence_1to10"]),
        )
    )

    # 3) task_b_results only if informative
    if is_informative:
        stageB = result.get("stageB") or {}
        pred_id = stageB.get("prediction_id")  # assumes matches disaster_classes.id
        cur.execute(
            SQL_INSERT_TASK_B,
            (
                run_id,
                float(stageB.get("b_text_prob_pred")) if stageB.get("b_text_prob_pred") is not None else None,
                float(stageB.get("b_image_prob_pred")) if stageB.get("b_image_prob_pred") is not None else None,
                float(stageB.get("confidence_prob")),
                int(pred_id) if pred_id is not None else None,
                int(stageB.get("confidence_1to10")),
            )
        )


def process_batch(limit: int = 25) -> int:
    processed = 0
    with get_conn() as conn:
        conn.start_transaction()
        try:
            cur = conn.cursor()
            cur.execute(SQL_SELECT_UNPROCESSED, (limit,))
            posts = fetchall_dict(cur)

            for p in posts:
                process_one_post(cur, p)
                processed += 1

            conn.commit()
            return processed
        except Exception:
            conn.rollback()
            raise


if __name__ == "__main__":
    # Run once (batch). You can also loop this in a scheduler.
    try:
        n = process_batch(limit=50)
        print(f"Processed {n} posts.")
    except Exception as e:
        print("ERROR:", e)
        traceback.print_exc()