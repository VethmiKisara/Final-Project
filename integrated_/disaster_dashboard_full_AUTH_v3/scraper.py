"""
Disaster tweet scraper — DUMMY VERSION (standalone CLI)

Wraps the core scraper logic in app/scraper.py for use as a standalone
script or cron job, independent of the Flask app.

The Flask app also runs this automatically via APScheduler (see app/__init__.py).
Use this CLI only if you want to run the scraper outside the app process,
or if SCRAPER_ENABLED=false in your .env.

Usage:
  python scraper.py                  # run once (one batch)
  python scraper.py --loop           # run continuously every 15 minutes

Cron (every 15 minutes):
  */15 * * * * /path/to/.venv/bin/python /path/to/scraper.py >> /var/log/scraper.log 2>&1

Setup:
  pip install -r requirements.txt
  Set DASHBOARD_URL and DUMMY_CSV_PATH in .env (or use defaults)
"""

import argparse
import logging
import time

from app.scraper import run_once

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

INTERVAL_SECS = 15 * 60


def run_loop():
    log.info("Starting scraper loop (interval: %d seconds)", INTERVAL_SECS)
    while True:
        run_once()
        log.info("Sleeping %d seconds until next run...", INTERVAL_SECS)
        time.sleep(INTERVAL_SECS)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DisasterWatch dummy tweet scraper")
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Run continuously every 15 minutes",
    )
    args = parser.parse_args()

    if args.loop:
        run_loop()
    else:
        run_once()
