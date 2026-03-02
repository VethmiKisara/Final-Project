# DisasterWatch – Map Dashboard (Flask + Leaflet)

This UI is wired to the **new normalized database**:

- `posts` (user inputs): `original_text`, `image_path`, `created_at`, `expires_at`
- `pipeline_runs` (one run per post): `post_id`, `location_id`, `used_text`, `used_image`
- `task_a_results` (informative): `a_label` (map shows only when `a_label = 1`), `a_confidence_level` (0–10)
- `task_b_results` (disaster type): `b_label_class_id` → `disaster_classes.id`, `b_confidence_level` (0–10)
- `locations` (map points): `name`, `latitude`, `longitude`
- `disaster_classes` (for filters + popups)

## What the UI does

### Dashboard
- **Map on top** (clear + large) with markers only for **active, informative alerts**:
  - Active: `posts.expires_at > NOW()`
  - Informative: `task_a_results.a_label = 1`
- Sidebar filters:
  - Disaster type (from `disaster_classes`)
  - Informative confidence (0–10) from `task_a_results.a_confidence_level`
  - Created time range (`posts.created_at`)
- Popup shows:
  - Post id
  - Location name
  - Informative confidence (`a_confidence_level/10`)
  - Disaster type + its confidence: `disaster_classes.name (b_confidence_level/10)`

### Alert Logs
- Same navbar/theme.
- Lists the same **active alerts** as the map:
  - Post id, disaster type, location, both confidence levels, created time.
- Filters: disaster type, informative confidence, created time.

### Test Input
- Saves into `posts`:
  - Text → `posts.original_text`
  - Image → saved to disk, stored as absolute forward-slash path in `posts.image_path`
- **Note:** a new post will not show on the map until your ML pipeline writes `pipeline_runs`, `task_a_results`, `task_b_results`, and `locations`.

## Setup (local)

1. Create your DB using your schema dump (tables: posts, pipeline_runs, task_a_results, task_b_results, locations, disaster_classes, users, password_reset_tokens).
2. Create `.env` from `.env.example` and update credentials if needed.
3. Install:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
4. Run:
   ```bash
   python run.py
   ```
5. Open: http://127.0.0.1:5000

## Config knobs
- `DB_*` in `.env`
- `ALERT_TTL_HOURS` (default 24)
- `IMAGE_STORE_DIR` (default: `<project>/data`) — images are stored there and the DB path uses forward slashes.
