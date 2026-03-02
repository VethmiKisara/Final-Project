import os
import uuid
from datetime import datetime, timedelta

from flask import Blueprint, current_app, jsonify, request
from sqlalchemy import text

from ..db import get_db_session

api_bp = Blueprint("api", __name__)

def _parse_int_list(raw: str):
    if not raw:
        return []
    out = []
    for p in raw.split(","):
        p = p.strip()
        if not p:
            continue
        try:
            out.append(int(p))
        except ValueError:
            continue
    # de-dupe preserve order
    seen = set()
    uniq = []
    for x in out:
        if x not in seen:
            seen.add(x)
            uniq.append(x)
    return uniq

def _parse_dt_local(raw: str):
    # HTML datetime-local is like '2026-02-27T12:30'
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None

@api_bp.get("/health")
def health():
    return jsonify({"status": "ok"})

@api_bp.get("/disaster-classes")
def get_disaster_classes():
    db = get_db_session()
    try:
        rows = db.execute(
            text("SELECT id, name FROM disaster_classes ORDER BY id ASC")
        ).mappings().all()
        return jsonify([{"id": int(r["id"]), "name": r["name"]} for r in rows])
    finally:
        db.close()

@api_bp.get("/posts")
def get_map_posts():
    """Points for the Leaflet map (only informative = 1, not expired)."""
    type_ids = _parse_int_list(request.args.get("types"))
    try:
        min_a = int(request.args.get("min_a_conf", "0"))
        max_a = int(request.args.get("max_a_conf", "10"))
    except ValueError:
        return jsonify({"error": "min_a_conf/max_a_conf must be integers"}), 400

    min_a = max(0, min(10, min_a))
    max_a = max(0, min(10, max_a))
    if min_a > max_a:
        min_a, max_a = max_a, min_a

    created_after = _parse_dt_local(request.args.get("created_after"))
    created_before = _parse_dt_local(request.args.get("created_before"))

    params = {
        "min_a": min_a,
        "max_a": max_a,
    }

    sql = """
        SELECT
          p.id AS post_id,
          p.created_at AS created_at,
          l.latitude AS lat,
          l.longitude AS lon,
          l.name AS location_name,
          ta.a_confidence_level AS a_conf,
          tb.b_confidence_level AS b_conf,
          dc.id AS disaster_id,
          dc.name AS disaster_name,
          p.original_text AS original_text
        FROM posts p
        JOIN pipeline_runs r ON r.post_id = p.id
        JOIN task_a_results ta ON ta.run_id = r.id
        LEFT JOIN task_b_results tb ON tb.run_id = r.id
        LEFT JOIN disaster_classes dc ON dc.id = tb.b_label_class_id
        LEFT JOIN locations l ON l.id = r.location_id
        WHERE
          p.expires_at > NOW()
          AND ta.a_label = 1
          AND l.latitude IS NOT NULL
          AND l.longitude IS NOT NULL
          AND ta.a_confidence_level BETWEEN :min_a AND :max_a
    """

    if created_after:
        sql += " AND p.created_at >= :created_after"
        params["created_after"] = created_after
    if created_before:
        sql += " AND p.created_at <= :created_before"
        params["created_before"] = created_before

    if type_ids:
        in_params = {f"t{i}": v for i, v in enumerate(type_ids)}
        sql += " AND dc.id IN (" + ",".join([f":t{i}" for i in range(len(type_ids))]) + ")"
        params.update(in_params)

    sql += " ORDER BY p.created_at DESC LIMIT 5000"

    db = get_db_session()
    try:
        rows = db.execute(text(sql), params).mappings().all()
        out = []
        for r in rows:
            out.append({
                "post_id": int(r["post_id"]),
                "created_at": r["created_at"].isoformat(sep=" ", timespec="seconds") if r["created_at"] else None,
                "lat": float(r["lat"]),
                "lon": float(r["lon"]),
                "location_name": r["location_name"],
                "a_confidence_level": int(r["a_conf"]) if r["a_conf"] is not None else None,
                "disaster_class_id": int(r["disaster_id"]) if r["disaster_id"] is not None else None,
                "disaster_type": (r["disaster_name"] or "unknown"),
                "b_confidence_level": int(r["b_conf"]) if r["b_conf"] is not None else None,
                "text": r["original_text"] or "",
            })
        return jsonify(out)
    finally:
        db.close()

@api_bp.get("/alerts")
def get_active_alerts():
    """Rows for Alert Logs page (same 'active alerts' definition as the map)."""
    type_ids = _parse_int_list(request.args.get("types"))
    try:
        min_a = int(request.args.get("min_a_conf", "0"))
        max_a = int(request.args.get("max_a_conf", "10"))
    except ValueError:
        return jsonify({"error": "min_a_conf/max_a_conf must be integers"}), 400

    min_a = max(0, min(10, min_a))
    max_a = max(0, min(10, max_a))
    if min_a > max_a:
        min_a, max_a = max_a, min_a

    created_after = _parse_dt_local(request.args.get("created_after"))
    created_before = _parse_dt_local(request.args.get("created_before"))

    params = {"min_a": min_a, "max_a": max_a}

    sql = """
        SELECT
          p.id AS post_id,
          p.created_at AS created_at,
          l.name AS location_name,
          ta.a_confidence_level AS a_conf,
          dc.name AS disaster_name,
          tb.b_confidence_level AS b_conf
        FROM posts p
        JOIN pipeline_runs r ON r.post_id = p.id
        JOIN task_a_results ta ON ta.run_id = r.id
        LEFT JOIN task_b_results tb ON tb.run_id = r.id
        LEFT JOIN disaster_classes dc ON dc.id = tb.b_label_class_id
        LEFT JOIN locations l ON l.id = r.location_id
        WHERE
          p.expires_at > NOW()
          AND ta.a_label = 1
          AND l.latitude IS NOT NULL
          AND l.longitude IS NOT NULL
          AND ta.a_confidence_level BETWEEN :min_a AND :max_a
    """

    if created_after:
        sql += " AND p.created_at >= :created_after"
        params["created_after"] = created_after
    if created_before:
        sql += " AND p.created_at <= :created_before"
        params["created_before"] = created_before

    if type_ids:
        in_params = {f"t{i}": v for i, v in enumerate(type_ids)}
        sql += " AND dc.id IN (" + ",".join([f":t{i}" for i in range(len(type_ids))]) + ")"
        params.update(in_params)

    sql += " ORDER BY p.created_at DESC LIMIT 5000"

    db = get_db_session()
    try:
        rows = db.execute(text(sql), params).mappings().all()
        out = []
        for r in rows:
            out.append({
                "post_id": int(r["post_id"]),
                "created_at": r["created_at"].isoformat(sep=" ", timespec="seconds") if r["created_at"] else None,
                "location_name": r["location_name"],
                "disaster_type": (r["disaster_name"] or "unknown"),
                "a_confidence_level": int(r["a_conf"]) if r["a_conf"] is not None else None,
                "b_confidence_level": int(r["b_conf"]) if r["b_conf"] is not None else None,
            })
        return jsonify(out)
    finally:
        db.close()

@api_bp.post("/posts")
def create_post():
    """Save user input into posts (original_text, image_path, expires_at)."""
    input_text = (request.form.get("text") or "").strip()
    if not input_text:
        return jsonify({"error": "text is required"}), 400

    image = request.files.get("image")
    image_path = None

    if image and image.filename:
        ext = os.path.splitext(image.filename)[1].lower()
        if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
            return jsonify({"error": "Only .jpg, .jpeg, .png, .webp allowed"}), 400

        fname = f"{uuid.uuid4().hex}{ext}"

        store_dir = current_app.config["IMAGE_STORE_DIR"]
        os.makedirs(store_dir, exist_ok=True)

        abs_path = os.path.abspath(os.path.join(store_dir, fname))
        image.save(abs_path)
        image_path = abs_path.replace("\\", "/")

    expires_at = datetime.now() + timedelta(hours=int(current_app.config.get("ALERT_TTL_HOURS", 24)))

    db = get_db_session()
    try:
        res = db.execute(
            text("""
                INSERT INTO posts (original_text, image_path, expires_at)
                VALUES (:t, :p, :e)
            """),
            {"t": input_text, "p": image_path, "e": expires_at},
        )
        db.commit()
        # SQLAlchemy text insert doesn't always return id across all drivers; fetch LAST_INSERT_ID
        post_id = db.execute(text("SELECT LAST_INSERT_ID() AS id")).mappings().first()["id"]
        return jsonify({"ok": True, "post_id": int(post_id), "saved_image_path": image_path})
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()
