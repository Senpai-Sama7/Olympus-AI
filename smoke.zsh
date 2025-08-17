#!/usr/bin/env zsh
# Smoke & triage harness for Olympus AI FastAPI app (zsh edition)

set -e
set -u
set -o pipefail

# ------- Config -------
: ${BASE:="http://127.0.0.1:8000"}

# Generate a correlation id that survives across calls
if command -v uuidgen >/dev/null 2>&1; then
  CID="$(uuidgen)"
elif [ -r /proc/sys/kernel/random/uuid ]; then
  CID="$(cat /proc/sys/kernel/random/uuid)"
else
  CID="rnd-$(date +%s)-$$-$RANDOM"
fi

# Pretty print JSON if jq exists
have_jq() { command -v jq >/dev/null 2>&1 }
pp() { if have_jq; then jq .; else cat; fi }

say() { printf "\n==== %s ====\n" "$*"; }

# ------- 0) Target info -------
say "Target $BASE  (Correlation-ID: $CID)"

# ------- 1) Health (build/config fingerprints) -------
say "GET /healthz"
curl -sS -H "x-correlation-id: $CID" "$BASE/healthz" | pp

# ------- 2) Happy path -------
say "GET /compute?x=2 (should be ok)"
curl -sS -H "x-correlation-id: $CID" "$BASE/compute?x=2" | pp

# ------- 3) Invariant failure (expect 500 with OLY-CMP-001 in logs) -------
say "GET /compute?x=-1 (expect 500 invariant OLY-CMP-001)"
code=$(curl -sS -o /tmp/olympus_resp.json -w "%{http_code}" -H "x-correlation-id: $CID" "$BASE/compute?x=-1" || true)
cat /tmp/olympus_resp.json | pp
echo "HTTP $code"

# ------- 4) Trip the breaker (simulate flaky dep) -------
say "Hammer /compute to trigger circuit breaker (watch for 503s)"
for i in {1..20}; do
  curl -sS -o /dev/null -w "%{http_code} " -H "x-correlation-id: $CID" "$BASE/compute?x=100"
done
echo
sleep 1

# ------- 5) Metrics snapshot (key signals) -------
say "GET /metrics (key lines)"
curl -sS "$BASE/metrics" | grep -E '(^#|circuit_open|errors_total|requests_total|request_duration_seconds_bucket|queue_depth)' | sed 's/^/# /'

# ------- 6) Consent gate demo -------
say "POST /act (should require consent -> 403 OLY-ACT-401)"
code=$(curl -sS -o /tmp/olympus_resp.json -w "%{http_code}" \
  -H "Content-Type: application/json" -H "x-correlation-id: $CID" \
  -d '{"action":"touch /tmp/olympus_probe"}' "$BASE/act" || true)
cat /tmp/olympus_resp.json | pp
echo "HTTP $code"

echo
echo "Tail your server logs filtered by correlation id to see the exact path:"
echo "  tail -f uvicorn.log | jq -c 'select(.correlation_id==\"$CID\")'"

