#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

python3 src/triad_orchestrator_mvp.py \
  --test tests/session.min.json \
  --json --deterministic --seed helix-ttd-v1 --proof-out out > /tmp/run1.txt

H1="$(jq -r .ledger_hash </tmp/run1.txt)"
sleep 1

python3 src/triad_orchestrator_mvp.py \
  --test tests/session.min.json \
  --json --deterministic --seed helix-ttd-v1 --proof-out out > /tmp/run2.txt

H2="$(jq -r .ledger_hash </tmp/run2.txt)"

echo "H1=$H1"
echo "H2=$H2"

[[ "$H1" == "$H2" ]] && echo "Deterministic: PASS" || { echo "Deterministic: FAIL"; exit 1; }
