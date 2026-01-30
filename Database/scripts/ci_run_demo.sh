#!/usr/bin/env bash
set -euo pipefail

export DB_HOST=${DB_HOST:-localhost}
export DB_PORT=${DB_PORT:-5432}
export DB_NAME=${DB_NAME:-rtmd}
export DB_USER=${DB_USER:-rtmd_user}
export DB_PASS=${DB_PASS:-change_me}

echo "Running Python demo..."
python3 python/connect_and_demo.py

echo "Demo complete."