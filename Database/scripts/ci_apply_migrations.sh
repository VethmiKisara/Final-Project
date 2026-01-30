#!/usr/bin/env bash
set -euo pipefail

DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME:-rtmd}
DB_USER=${DB_USER:-rtmd_user}
DB_PASS=${DB_PASS:-change_me}

export PGPASSWORD="$DB_PASS"
PSQL_CMD="psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME"

echo "Waiting for Postgres to accept connections..."
for i in {1..30}; do
  if $PSQL_CMD -c '\q' 2>/dev/null; then
    echo "Postgres is available"
    break
  fi
  echo "Waiting... ($i)"
  sleep 2
done

echo "Applying migrations..."
for f in migrations/*.sql; do
  echo "--- Applying $f"
  $PSQL_CMD -f "$f"
done

echo "Seeding dev data..."
$PSQL_CMD -f migrations/seed_dev_data.sql

echo "Migrations and seed complete."