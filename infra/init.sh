#!/usr/bin/env bash
set -euo pipefail

# Determine repo root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

# Create directories that likely exist in this repo
mkdir -p "$REPO_ROOT/.data" "$REPO_ROOT/.sandbox"

# Create .env if missing (from .env.dev template)
if [[ ! -f "$REPO_ROOT/.env" ]]; then
  if [[ -f "$REPO_ROOT/.env.dev" ]]; then
    echo "Creating .env from .env.dev"
    cp "$REPO_ROOT/.env.dev" "$REPO_ROOT/.env"
  else
    echo "ERROR: .env.dev not found." >&2
    exit 1
  fi
fi

# Load env
set -a
source "$REPO_ROOT/.env"
set +a

# Ensure directories per env settings
DB_PATH_DIR="$(dirname "${DB_PATH:-.data/olympus.db}")"
SANDBOX_DIR="${SANDBOX_ROOT:-.sandbox}"
mkdir -p "$DB_PATH_DIR" "$SANDBOX_DIR" "$SANDBOX_DIR/.status"

# Initialize SQLite database (idempotent)
python3 - "$DB_PATH" <<'PY'
import os, sqlite3, sys
path = sys.argv[1]
os.makedirs(os.path.dirname(path), exist_ok=True)
conn = sqlite3.connect(path)
try:
    conn.execute("""
    CREATE TABLE IF NOT EXISTS schema_migrations (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      version TEXT UNIQUE NOT NULL,
      applied_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    """)
    conn.commit()
finally:
    conn.close()
print(f"Initialized SQLite at: {path}")
PY

echo "Init complete."
