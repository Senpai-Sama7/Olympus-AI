#!/usr/bin/env zsh
# Start uvicorn, wait for readiness, run smoke, then cleanly shut down.
set -euo pipefail

BASE=${BASE:-http://127.0.0.1:8000}

cleanup() {
  # Try to stop reloader and its child; then belt-and-suspenders kill
  [[ -n "${UVICORN_PID:-}" ]] && { pkill -TERM -P $UVICORN_PID || true; kill -TERM $UVICORN_PID || true; }
  sleep 0.3
  pkill -f "uvicorn.*app:app" || true
}
trap cleanup EXIT INT TERM

echo ">> starting uvicorn…"
uvicorn app:app --reload 2>&1 | tee uvicorn.log & 
UVICORN_PID=$!

echo ">> waiting for /healthz…"
for i in {1..50}; do
  if curl -sSf "$BASE/healthz" >/dev/null; then
    echo ">> ready"
    break
  fi
  sleep 0.2
done

echo ">> running smoke.zsh…"
./smoke.zsh

echo ">> done; shutting down uvicorn"

