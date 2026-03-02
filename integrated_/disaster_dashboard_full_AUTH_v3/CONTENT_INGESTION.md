# Content Ingestion Guide

This document explains how live content should flow into DisasterWatch, why
real-time scraping from X (Twitter) is not feasible for this project, what
the dummy ingestion system does instead, and how to use it during development.

---

## High-Level Architecture

In a production system, content ingestion is a pipeline that runs independently
of the web application. The dashboard does not collect data — it only displays
data that has already been processed and stored in the database.

```
[ Data Source ]          [ Ingestion Layer ]         [ ML Pipeline ]         [ Dashboard ]

  X / Twitter     --->    Scraper (cron job)  --->   Classification   --->   Flask app reads
  RSS feeds               fetches new posts           models write            from DB and
  Web forms               POSTs to /api/posts         results to DB           renders map
```

The three layers are decoupled on purpose:
- The **scraper** runs on a schedule and feeds raw text into the `posts` table.
- The **ML pipeline** reads from `posts`, runs inference, and writes results to
  `pipeline_runs`, `task_a_results`, `task_b_results`, and `locations`.
- The **Flask app** only reads — it never runs inference or scrapes.

---

## What a Cron Job Is

A cron job is a scheduled task that runs automatically at a fixed interval on a
server. It is not a continuously running process — it wakes up, does its work,
and exits. A new instance starts at the next scheduled time.

For ingestion, the cron job would:

1. Authenticate with the data source (e.g. X API).
2. Fetch the latest posts matching disaster-related keywords.
3. Filter out duplicates (by tweet ID or text hash).
4. POST each new item to `POST /api/posts`.
5. Exit. The next run picks up from where this one left off.

A 15-minute interval is a reasonable default — short enough to surface breaking
disaster events quickly, long enough to stay within API rate limits.

```
# Example crontab entry (every 15 minutes)
*/15 * * * * /path/to/.venv/bin/python /path/to/scraper.py >> /var/log/scraper.log 2>&1
```

---

## Real-Time Scraping Limitations

Pulling tweets directly from X in real time is not possible for most projects.
The reasons are:

| Constraint | Detail |
|---|---|
| **API access tier** | Free and Basic X API tiers have strict monthly read limits (500k–1M tweets/month on Basic). Real-time filtered streams require the Pro tier ($5,000/month). |
| **Rate limits** | Even on paid tiers, endpoints have per-15-minute request caps. Exceeding them results in 429 errors and temporary bans. |
| **Search latency** | The recent search endpoint returns tweets from the last 7 days. There is no push mechanism — you must poll. |
| **Authentication** | Bearer tokens expire; OAuth 2.0 flows require secure credential storage and rotation. |
| **Cost** | At scale, tweet volume for terms like "earthquake" or "flood" during an actual disaster event can reach hundreds of thousands per hour. |

Because this project is an academic submission without production API credentials,
implementing a live scraper would block development and testing entirely.

---

## What We Built Instead

The dummy scraper reads from the same CSV files used to train the ML models. This
gives a realistic stream of disaster-related tweets without any API dependency.

**How it works:**

1. On each run, it reads the next `BATCH_SIZE` rows from the training CSV.
2. Each row's `tweet_text` value is POSTed to `POST /api/posts`.
3. An offset tracks position in the file across runs — the next run continues
   from where the previous one ended.
4. When the CSV is exhausted it loops back to the beginning.

**Where the scheduler lives:**

The scraper is integrated directly into the Flask app via APScheduler. When
`FLASK_ENV=production` is set, a background thread wakes up every 15 minutes
and calls `run_once()` automatically. No separate process or cron entry needed.

In development (`FLASK_ENV=development`, the default) the scheduler is skipped
so it does not interfere with the reloader or test runs.

---

## Development Usage

### 1. Install dependencies

```bash
cd integrated_/disaster_dashboard_full_AUTH_v3
pip install -r requirements.txt
```

### 2. Create a dummy CSV

The scraper expects a CSV with a `tweet_text` column. If you do not have the
training dataset locally, create a minimal one by hand:

```csv
tweet_text
"Earthquake magnitude 6.2 strikes coastal region near Colombo"
"Flooding reported in low-lying areas of Galle after heavy rainfall"
"Wildfire spreading rapidly through dry forest northeast of Kandy"
"Landslide blocks main highway following overnight storm in Nuwara Eliya"
"Tsunami warning issued for southern coastline after offshore tremor"
"Rescue teams deployed to flood-affected villages in Matara district"
"Strong winds damage rooftops across Western Province"
"River levels rising rapidly — residents urged to evacuate flood plains"
```

Save it anywhere convenient, e.g. `dummy_tweets.csv` in the project root.

### 3. Configure your `.env`

Copy `.env.example` to `.env` and point `DUMMY_CSV_PATH` at the CSV you created
(or at the training CSV from `src/` if you have it):

```env
FLASK_ENV=development
DASHBOARD_URL=http://localhost:5000
DUMMY_CSV_PATH=dummy_tweets.csv
DUMMY_BATCH_SIZE=20
```

### 4. Start the Flask app

```bash
python run.py
```

### 5. Trigger the scraper manually

With the app running, open a second terminal and run:

```bash
# Single batch (20 tweets by default)
python scraper.py

# Watch the CSV stream continuously
python scraper.py --loop
```

Each run POSTs a batch to `/api/posts`. You will see log lines like:

```
2026-03-03 12:00:01 [INFO] Scraper run started (batch_size=20)
2026-03-03 12:00:01 [INFO] Loaded 20 tweets
2026-03-03 12:00:03 [INFO] Ingested → post_id=42 | Massive earthquake hits...
```

### 6. Verify in the database

```sql
SELECT id, LEFT(original_text, 60), created_at FROM posts ORDER BY id DESC LIMIT 10;
```

Posts will appear in the `posts` table. They will **not** appear on the
dashboard map until the ML pipeline has processed them and written results to
`pipeline_runs`, `task_a_results`, and `task_b_results`. That step is outside
the scope of the dashboard itself.

---

## Switching to a Real Scraper

When an X API key is available, replace the dummy scraper with a Tweepy-based
implementation. The only contract that must be preserved is:

```
POST /api/posts
Content-Type: multipart/form-data

text=<tweet text>
image=<optional image file>
```

Everything else — authentication, deduplication, keyword filtering — lives
inside `scraper.py` and has no effect on the Flask app.
