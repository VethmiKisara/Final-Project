# RTMD Database (SQLAlchemy) — Quickstart

This folder contains SQLAlchemy ORM models, schema creation, and seed scripts for the Real-Time Multimodal Disaster Detection project.

Quick steps:
1. Install requirements: `pip install -r requirements-sqlalchemy.txt`
2. Configure DATABASE_URL env var or edit `python/create_db.py` default.
3. Create the schema: `python python/create_db.py`
4. Seed example data: `python python/seed_data.py`
5. Generate ER diagram (optional): `python python/er_diagram.py` (requires graphviz)

Notes:
- The models use PostgreSQL types (UUID) and constraints suitable for production.
- Indexes are provided on common filter columns (timestamp, platform, confidence).
- Authentication is supported via `users` table (see `AUTH.md`) and was added in migration V2.
