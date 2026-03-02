"""
Core scraper logic — shared by the Flask scheduler and the standalone CLI.

Reads from the training CSV dataset and POSTs rows to the dashboard's
/api/posts endpoint, simulating live tweet ingestion without calling the X API.
"""

import logging
import os
import time

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger(__name__)

DASHBOARD_URL = os.getenv("DASHBOARD_URL", "http://localhost:5000")
BATCH_SIZE    = int(os.getenv("DUMMY_BATCH_SIZE", "20"))
TEXT_COLUMN   = "tweet_text"

DUMMY_CSV_PATH = os.getenv(
    "DUMMY_CSV_PATH",
    os.path.join(
        os.path.dirname(__file__),
        "..", "..", "..", "src", "notebooks", "data", "train.csv"
    ),
)

# Tracks position across scheduler runs (resets on process restart)
_csv_offset = 0


def fetch_dummy_tweets(csv_path: str, batch_size: int) -> list[dict]:
    """Read the next batch of rows from the CSV, wrapping at the end."""
    global _csv_offset

    if not os.path.exists(csv_path):
        raise FileNotFoundError(
            f"Dummy CSV not found: {csv_path}\n"
            "Set DUMMY_CSV_PATH in .env to point to one of the training CSVs."
        )

    df = pd.read_csv(csv_path)

    if TEXT_COLUMN not in df.columns:
        raise ValueError(
            f"Column '{TEXT_COLUMN}' not found in CSV. "
            f"Available columns: {list(df.columns)}"
        )

    df = df[df[TEXT_COLUMN].notna()]
    total = len(df)

    if _csv_offset >= total:
        _csv_offset = 0
        log.info("CSV exhausted — looping back to start")

    batch = df.iloc[_csv_offset : _csv_offset + batch_size]
    _csv_offset += len(batch)

    return [{"text": str(row[TEXT_COLUMN]).strip()} for _, row in batch.iterrows()]


def ingest_tweet(tweet: dict) -> bool:
    """POST a single tweet to /api/posts. Returns True on success."""
    text = (tweet.get("text") or "").strip()
    if not text:
        return False

    try:
        resp = requests.post(
            f"{DASHBOARD_URL}/api/posts",
            data={"text": text},
            timeout=10,
        )
        resp.raise_for_status()
        result = resp.json()
        log.info("Ingested → post_id=%s | %.60s...", result.get("post_id"), text)
        return True
    except requests.RequestException as e:
        log.warning("Failed to ingest tweet: %s", e)
        return False


def run_once():
    """Fetch one batch from the CSV and POST each tweet to the dashboard."""
    log.info("Scraper run started (batch_size=%d)", BATCH_SIZE)

    try:
        tweets = fetch_dummy_tweets(DUMMY_CSV_PATH, BATCH_SIZE)
    except (FileNotFoundError, ValueError) as e:
        log.error("%s", e)
        return

    log.info("Loaded %d tweets", len(tweets))
    success = 0
    for tweet in tweets:
        if ingest_tweet(tweet):
            success += 1
        time.sleep(0.1)

    log.info("Scraper run done — %d/%d ingested", success, len(tweets))
