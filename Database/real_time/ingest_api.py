"""
FastAPI ingestion endpoint for RTMD.
- Accepts POST requests with social post data
- Inserts into `social_media_posts` with status 'queued'
- Pushes `post_id` to Redis stream 'rtmd:posts' for workers to process

Run: `uvicorn real_time.ingest_api:app --reload --host 0.0.0.0 --port 8000`
"""
from datetime import datetime
import os
import json
from typing import Optional

import redis
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from python.db import get_session
from python.models import SocialMediaPost

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.Redis.from_url(REDIS_URL)

app = FastAPI(title="RTMD Ingest API")


class IngestPost(BaseModel):
    platform: str = Field(..., example="twitter")
    post_text: Optional[str] = Field(None, example="Smoke seen near riverbank")
    post_image: Optional[str] = Field(None, example="https://example.org/image.jpg")
    language: Optional[str] = Field(None, example="en")
    timestamp: Optional[datetime] = None


@app.post("/ingest", status_code=201)
def ingest(post: IngestPost):
    payload = post.dict()
    payload["timestamp"] = payload.get("timestamp") or datetime.utcnow().isoformat()

    # Insert into DB
    session = get_session()
    try:
        smp = SocialMediaPost(
            post_text=payload.get("post_text"),
            post_image=payload.get("post_image"),
            language=payload.get("language"),
            platform=payload.get("platform"),
            timestamp=payload.get("timestamp"),
        )
        session.add(smp)
        session.commit()
        session.refresh(smp)

        # Push to Redis stream for processing
        event = {"post_id": str(smp.post_id), "platform": smp.platform}
        redis_client.xadd("rtmd:posts", event)

        return {"post_id": str(smp.post_id)}
    except Exception as exc:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        session.close()
