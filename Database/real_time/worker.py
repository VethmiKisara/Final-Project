"""
Worker that consumes Redis Stream 'rtmd:posts', runs mock detection/credibility, and writes results.
- Uses XREADGROUP to form consumer groups (idempotent processing)
- Performs DB writes in a transaction for each post

Run: python real_time/worker.py --group worker-group --consumer worker-1
"""
import os
import time
import json
import random
import argparse
from typing import Tuple

import redis
from sqlalchemy import select

from python.db import get_session
from python.models import SocialMediaPost, Result, Credibility, Disaster, Alert  # Alert may not exist; we'll create alerts via table insert

# Note: the models currently use `alerts` table in earlier schema; import if present

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.Redis.from_url(REDIS_URL)
STREAM_KEY = "rtmd:posts"

# Thresholds - tune per your application
ALERT_CONFIDENCE_THRESHOLD = float(os.getenv("ALERT_CONFIDENCE_THRESHOLD", "0.8"))


def mock_disaster_detection(post_text: str) -> Tuple[str, float]:
    """Mock function that returns disaster type and confidence.
    Replace this with actual model call in production.
    """
    disasters = ["fire", "flood", "earthquake", "storm", None]
    choice = random.choices(disasters, weights=[0.25, 0.2, 0.1, 0.15, 0.3])[0]
    confidence = round(random.uniform(0.4, 0.95), 2) if choice else 0.0
    return choice, confidence


def mock_credibility_score(post_text: str) -> float:
    return round(random.uniform(0.0, 1.0), 2)


def ensure_consumer_group():
    try:
        redis_client.xgroup_create(STREAM_KEY, "rtmd_group", id="$", mkstream=True)
    except redis.exceptions.ResponseError:
        # Group already exists
        pass


def process_message(message_id: str, values: dict):
    post_id = values.get(b"post_id").decode()

    session = get_session()
    try:
        stmt = select(SocialMediaPost).where(SocialMediaPost.post_id == post_id)
        post = session.execute(stmt).scalars().first()
        if not post:
            print(f"Post {post_id} not found; skipping")
            return

        # idempotency: skip if there is already a result from same model (simplified)
        # Real implementation should check unique job ids or processed flags
        # Run mock detection
        disaster_label, conf = mock_disaster_detection(post.post_text or "")
        cred_score = mock_credibility_score(post.post_text or "")

        # Write Result and Credibility in a transaction
        res = Result(post=post, accuracy=round(random.uniform(0.7, 0.98), 2), disaster_label=disaster_label or "none", model_type="mock", confidence_score=conf)
        cred = Credibility(post=post, score=cred_score, source_verification_status=(cred_score > 0.8))
        session.add_all([res, cred])

        # If high confidence, create or update a Disaster and insert an alert
        if disaster_label and conf >= ALERT_CONFIDENCE_THRESHOLD:
            d = Disaster(disaster_type=disaster_label, severity="high", confidence_score=conf, status="active")
            session.add(d)
            session.flush()  # get d.disaster_id
            post.disaster = d
            # Create an alert in alerts table if present
            try:
                from python.models import Alert as AlertModel  # local import to avoid circular issues

                alert = AlertModel(detection_id=None, alert_severity="high", alert_status="pending")
                session.add(alert)
            except Exception:
                # Alerts table may not be in ORM; try raw SQL
                session.execute("INSERT INTO alerts (detection_id, alert_severity, alert_status) VALUES (NULL, 'high', 'pending')")

        session.commit()
        print(f"Processed post {post_id}: disaster={disaster_label} conf={conf} cred={cred_score}")
    except Exception as exc:
        session.rollback()
        print(f"Error processing post {post_id}: {exc}")
    finally:
        session.close()


def worker_loop(group: str, consumer: str, count: int = 1):
    ensure_consumer_group()
    while True:
        try:
            items = redis_client.xreadgroup(groupname="rtmd_group", consumername=consumer, streams={STREAM_KEY: ">"}, count=count, block=5000)
            if not items:
                continue
            for stream_key, messages in items:
                for msg_id, msg in messages:
                    process_message(msg_id.decode(), msg)
                    # Acknowledge
                    redis_client.xack(STREAM_KEY, "rtmd_group", msg_id)
        except Exception as exc:
            print('Worker error:', exc)
            time.sleep(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--group", default="rtmd_group")
    parser.add_argument("--consumer", default="worker-1")
    args = parser.parse_args()
    worker_loop(args.group, args.consumer)
