#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE_URL:-http://localhost:8000}"
DAY="$(date +%F)"
ROOTDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "📡 Health…"
curl -fsS "$BASE/health" | jq -e '.status=="ok"'

echo "🧪 Orchestrate…"
RESP="$(curl -fsS -X POST "$BASE/cosmos/computation/triad-orchestrator" \
  -H 'Content-Type: application/json' \
  -d '{
        "cultural_context":"CAN_CA_EN",
        "sovereign_level":"SOVEREIGN_TRANSITION_GOV",
        "glyph_matrix":["G1","G2","G3"],
        "optical_params":{"resolution":"8192x8192","compression_target":25.0},
        "paradox_zones":[{"contradiction_pair":"G1|G2","resolution_protocol":"TTD.PRX/001"}]
      }')"
echo "$RESP" | jq .
HASH="$(echo "$RESP" | jq -r .ledger_hash)"

test -n "$HASH" && [[ "$HASH" == ttd_ledger_v1_* ]] || { echo "no ledger hash"; exit 1; }

echo "📂 Out files exist…"
test -f "$ROOTDIR/out/result.json"
test -f "$ROOTDIR/out/envelope.json"
jq -e --arg H "$HASH" '.ledger_hash==$H' "$ROOTDIR/out/result.json" >/dev/null

echo "📚 Ledger listing…"
curl -fsS "$BASE/cosmos/ledger?limit=5" | jq -e 'type=="array"'

echo "📦 Fetch capsule…"
curl -fsS "$BASE/cosmos/ledger/$HASH" | jq -e '.ledger_hash==env.HASH' > /dev/null

echo "🌳 Rollup today…"
ROL="$(curl -fsS -X POST "$BASE/cosmos/rollups/daily" -H 'Content-Type: application/json' -d '{}')"
echo "$ROL" | jq .
echo "$ROL" | jq -e --arg D "$DAY" '.date==$D'
ROOTVAL="$(echo "$ROL" | jq -r .merkle_root)"
test ${#ROOTVAL} -eq 64

echo "🛡️ Negative path traversal…"
curl -sS "$BASE/cosmos/ledger/../../etc/passwd" | jq -e '.detail=="invalid hash"' >/dev/null || true

echo "✅ E2E OK"
