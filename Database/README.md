# Real-Time Multimodal Disaster Detection — Database

This folder contains a production-oriented PostgreSQL schema, deployment helpers, migration files, partition automation, and demo scripts for the Real-Time Multimodal Disaster Detection (RTMD) project.

Files added:
- `docker-compose.yml` — service definition for a local PostgreSQL instance for development.
- `migrations/V1__create_schema.sql` — migration that creates tables, indexes, helper functions, and an initial partition template.
- `migrations/seed_dev_data.sql` — sample data for development testing.
- `scripts/apply_migrations.ps1` — PowerShell script to apply SQL migration files using `psql`.
- `scripts/create_month_partitions.ps1` — PowerShell helper to create monthly partitions ahead of time.
- `python/connect_and_demo.py` — simple Python demo to connect, seed sample data, query, and create partitions.
- `.env.example` and `requirements.txt` — environment file template and Python dependencies.

Quick start (development):

1. Copy and edit `.env.example` -> `.env` (or set env vars in your shell).
2. Start PostgreSQL with Docker: `docker compose up -d` (uses `docker-compose.yml`).
3. Apply migrations (after DB is up):
   - On Windows PowerShell: `.\	ools\apply_migrations.ps1 -DbHost localhost -DbName rtmd -DbUser rtmd_user -DbPassword change_me` or run `scripts\apply_migrations.ps1` from this repo root.
   - Or let Docker run the SQL in `migrations/` at initial container creation (files under `/docker-entrypoint-initdb.d`).
4. Create partitions ahead of time (optional but recommended):
   - `.\scripts\create_month_partitions.ps1 -MonthsAhead 3`
5. Seed demo data: run the `migrations/seed_dev_data.sql` file or use the included Python demo to seed and query.

Running the Python demo:
- Install dependencies: `pip install -r requirements.txt`.
- Export env vars from your `.env` (or use PowerShell to set them) then run: `python python\connect_and_demo.py`.

Production notes & recommendations:
- Use connection pooling (pgbouncer) and bulk ingest techniques for high throughput.
- Use monthly range partitioning for timestamped tables and drop/archive old partitions to manage storage costs.
- Schedule `create_month_partitions.ps1` via Windows Task Scheduler or external orchestrator to create partitions ahead of time.
- Monitor and tune autovacuum, WAL settings, and checkpointing for insert-heavy workloads.

CI / Automated verification

- A GitHub Actions workflow (`.github/workflows/ci.yml`) has been added to run a Postgres service, apply migrations, seed dev data, and run the Python demo on push or pull request to `main`.
- The workflow uses `scripts/ci_apply_migrations.sh` and `scripts/ci_run_demo.sh` to perform migration and demo steps; it is useful to validate changes and to run simple integration checks.

If you'd like, I can:
- Add Task Scheduler `.xml` or PowerShell to register a scheduled job for partition creation.
- Create a Flyway/Liquibase migration skeleton for production migrations.
- Insert larger synthetic dataset for performance testing and add example benchmark queries.
