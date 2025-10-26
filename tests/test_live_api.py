import os, json, datetime, httpx

BASE = os.getenv("BASE_URL", "http://localhost:8000")

def test_health():
    r = httpx.get(f"{BASE}/health", timeout=5.0)
    j = r.json()
    assert j["status"] == "ok"

def test_orchestrate_and_rollup():
    payload = {
        "cultural_context":"CAN_CA_EN",
        "sovereign_level":"SOVEREIGN_TRANSITION_GOV",
        "glyph_matrix":["G1","G2","G3"],
        "optical_params":{"resolution":"8192x8192","compression_target":25.0},
        "paradox_zones":[{"contradiction_pair":"G1|G2","resolution_protocol":"TTD.PRX/001"}]
    }
    r = httpx.post(f"{BASE}/cosmos/computation/triad-orchestrator", json=payload, timeout=30.0)
    r.raise_for_status()
    j = r.json()
    assert j["status"] == "IMMUTABLE_ENTRY"
    assert j["ledger_hash"].startswith("ttd_ledger_v1_")

    today = datetime.date.today().isoformat()
    r2 = httpx.post(f"{BASE}/cosmos/rollups/daily", json={}, timeout=10.0)
    r2.raise_for_status()
    j2 = r2.json()
    assert j2["date"] == today
    assert len(j2["merkle_root"]) == 64
