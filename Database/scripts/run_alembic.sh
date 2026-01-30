#!/usr/bin/env bash
set -euo pipefail

DB_URL=${DATABASE_URL:-postgresql+psycopg2://rtmd_user:change_me@localhost:5432/rtmd}
export DATABASE_URL="$DB_URL"

echo "Running alembic upgrade head against $DATABASE_URL"
alembic upgrade head

echo "Alembic migrations applied."