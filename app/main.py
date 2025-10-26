# app/main.py
from __future__ import annotations

import datetime
import json
import pathlib
import subprocess
from typing import Any, Dict, List, Literal, Optional

from fastapi import Body, FastAPI, HTTPException, Path, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

# ────────────────────────────────────────────────────────────────────────────────
# 📚 HGL-CORE-005 KNOWLEDGE — App wiring
# ────────────────────────────────────────────────────────────────────────────────

app = FastAPI(title="HELIX-TTD Triad Orchestrator API", version="0.2.0")

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "out"
LEDGER = ROOT / "ledger"
ROLLUPS = ROOT / "rollups"
BIN = ROOT / "src" / "triad_orchestrator_mvp.py"


def _run(cmd: List[str], input_bytes: bytes | None = None) -> subprocess.CompletedProcess:
    """Subprocess runner that never raises, captures all output."""
    return subprocess.run(cmd, input=input_bytes, capture_output=True, check=False)


# ────────────────────────────────────────────────────────────────────────────────
# 🔍 HGL-CORE-001 INVESTIGATE — Schemas
# ────────────────────────────────────────────────────────────────────────────────

class ParadoxZone(BaseModel):
    contradiction_pair: str = Field(..., example="G1|G2")
    resolution_protocol: str = Field(..., example="TTD.PRX/001")


class OpticalParams(BaseModel):
    resolution: str = Field(..., example="8192x8192")
    compression_target: float = Field(..., example=25.0)


class OrchestrateRequest(BaseModel):
    cultural_context: str = Field(..., example="CAN_CA_EN")
    sovereign_level: Literal[
        "SOVEREIGN_TRANSITION_GOV", "SOVEREIGN", "nation-state", "corporate", "global", "western"
    ] = "SOVEREIGN_TRANSITION_GOV"
    glyph_matrix: List[str] = Field(..., min_items=1, example=["G1", "G2", "G3"])
    optical_params: OpticalParams
    paradox_zones: Optional[List[ParadoxZone]] = []

    @field_validator("optical_params")
    @classmethod
    def _resolution_ok(cls, v: OpticalParams) -> OpticalParams:
        if "x" not in v.resolution:
            raise ValueError("optical_params.resolution must be like 8192x8192")
        return v


class OrchestrateResponse(BaseModel):
    ledger_hash: str
    computational_fidelity: float
    paradox_resolution_rate: float
    temporal_anchor: str
    status: Literal["IMMUTABLE_ENTRY", "SUCCESS", "ERROR"] = "IMMUTABLE_ENTRY"


class VerifyRequest(BaseModel):
    result_json_path: str
    signature_path: str
    allowed_signers_path: str
    identity: str = Field(..., example="sbhop@helix")
    namespace: str = "ttd-proof"


class RollupResponse(BaseModel):
    date: str
    count: int
    merkle_root: str
    status: Literal["OK", "EMPTY"] = "OK"


class CapsuleIndex(BaseModel):
    ledger_hash: str
    has_result: bool
    has_signature: bool
    has_envelope: bool


class CapsuleBundle(BaseModel):
    ledger_hash: str
    result: Dict[str, Any]
    signature_path: Optional[str] = None
    envelope: Optional[Dict[str, Any]] = None


class RollupBundle(BaseModel):
    date: str
    count: int
    hashes: List[str]
    merkle_root: str
    canonical_sig: Optional[str] = None
    status: Literal["OK", "EMPTY"] = "OK"


# ────────────────────────────────────────────────────────────────────────────────
# 🩺 Health
# ────────────────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.datetime.utcnow().isoformat() + "Z"}


# ────────────────────────────────────────────────────────────────────────────────
# 🔗 HGL-CORE-004 INTEGRATE — Orchestration endpoint
# ────────────────────────────────────────────────────────────────────────────────

@app.post("/cosmos/computation/triad-orchestrator", response_model=OrchestrateResponse)
def orchestrate(req: OrchestrateRequest, deterministic: bool = True):
    """
    Builds a transient HGL session file from the request,
    invokes the orchestrator with --json and --proof-out, and returns a summary.
    """
    hgl = {
        "hgl_session": {
            "metadata": {
                "timestamp": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
                "cultural_context": req.cultural_context,
                "sovereign_level": req.sovereign_level,
                "scope": "API_ORCHESTRATION"
            },
            "glyphs": req.glyph_matrix,
            "optical_encoding": {
                "resolution": req.optical_params.resolution,
                "compression_target": req.optical_params.compression_target
            },
            "paradox_zones": [
                {"glyph_pair": z.contradiction_pair, "resolution_protocol": z.resolution_protocol}
                for z in (req.paradox_zones or [])
            ]
        }
    }

    OUT.mkdir(parents=True, exist_ok=True)
    # Create a temp session file within OUT so orchestrator can find it easily.
    tmp = (OUT / f"api_session_{int(datetime.datetime.utcnow().timestamp())}.json")
    tmp.write_text(json.dumps(hgl))

    cmd = [
        "python3", str(BIN),
        "--test", str(tmp),
        "--json",
        "--deterministic" if deterministic else "",
        "--seed", "api-route",
        "--proof-out", str(OUT),
    ]
    # filter empty args (from optional flag)
    cmd = [c for c in cmd if c]

    run = _run(cmd)
    if run.returncode != 0:
        raise HTTPException(500, detail=f"orchestrator failed: {run.stderr.decode() if isinstance(run.stderr, bytes) else run.stderr or run.stdout}")

    # The orchestrator prints logs + a final JSON line; parse the last JSON line.
    stdout = run.stdout if isinstance(run.stdout, str) else run.stdout.decode()
    last_line = ""
    for line in stdout.strip().splitlines()[::-1]:
        last_line = line
        if line.startswith("{") and line.endswith("}"):
            break

    try:
        result = json.loads(last_line)
    except Exception as e:
        raise HTTPException(500, detail=f"parse error: {e}; out={stdout}")

    try:
        resp = OrchestrateResponse(
            ledger_hash=result["ledger_hash"],
            computational_fidelity=float(result["fidelity_verified"]),
            paradox_resolution_rate=float(result["paradox_resolution_rate"]),
            temporal_anchor=result.get("timestamp_utc") or datetime.datetime.utcnow().isoformat() + "Z",
            status="IMMUTABLE_ENTRY",
        )
    except KeyError as e:
        raise HTTPException(500, detail=f"missing expected field from orchestrator: {e}")

    return resp


# ────────────────────────────────────────────────────────────────────────────────
# ✅ HGL-CORE-007 VALIDATE — Signature verification (stdin form)
# ────────────────────────────────────────────────────────────────────────────────

@app.post("/cosmos/proofs/verify")
def verify(r: VerifyRequest):
    msgp = pathlib.Path(r.result_json_path)
    sigp = pathlib.Path(r.signature_path)
    asp = pathlib.Path(r.allowed_signers_path)

    if not msgp.exists():
        raise HTTPException(400, detail="result_json_path not found")
    if not sigp.exists():
        raise HTTPException(400, detail="signature_path not found")
    if not asp.exists():
        raise HTTPException(400, detail="allowed_signers_path not found")

    msg = msgp.read_bytes()
    cmd = [
        "ssh-keygen", "-Y", "verify",
        "-f", str(asp),
        "-I", r.identity,
        "-n", r.namespace,
        "-s", str(sigp),
    ]
    run = _run(cmd, input_bytes=msg)
    ok = (run.returncode == 0)
    return JSONResponse({
        "verified": ok,
        "stdout": (run.stdout if isinstance(run.stdout, str) else run.stdout.decode()),
        "stderr": (run.stderr if isinstance(run.stderr, str) else run.stderr.decode()),
    }, status_code=200 if ok else 400)


# ────────────────────────────────────────────────────────────────────────────────
# 📊 HGL-CORE-013 ANALYTICS — Build daily Merkle rollup (read/write)
# ────────────────────────────────────────────────────────────────────────────────

@app.post("/cosmos/rollups/daily", response_model=RollupResponse)
def rollup(date: Optional[str] = Body(None, embed=True)):
    if not date:
        date = datetime.date.today().isoformat()

    hashes: List[str] = []
    for p in sorted(LEDGER.glob("*/result.json")):
        try:
            d = json.loads(p.read_text())
        except Exception:
            continue
        ts = d.get("timestamp_utc", "")
        if ts.startswith(date):
            h = d.get("ledger_hash")
            if h:
                hashes.append(h)

    import hashlib as _hl

    def _h(b: bytes) -> bytes:
        return _hl.sha3_256(b).digest()

    if not hashes:
        # Still write files for observability
        day = ROLLUPS / date
        day.mkdir(parents=True, exist_ok=True)
        (day / "hashes.txt").write_text("")
        (day / "merkle_root.txt").write_text("0" * 64 + "\n")
        return RollupResponse(date=date, count=0, merkle_root="0" * 64, status="EMPTY")

    layer = [_h(h.encode()) for h in hashes]
    while len(layer) > 1:
        if len(layer) % 2 == 1:
            layer.append(layer[-1])
        layer = [_h(layer[i] + layer[i + 1]) for i in range(0, len(layer), 2)]
    root_hex = layer[0].hex()

    day = ROLLUPS / date
    day.mkdir(parents=True, exist_ok=True)
    (day / "hashes.txt").write_text("\n".join(hashes) + "\n")
    (day / "merkle_root.txt").write_text(root_hex + "\n")

    return RollupResponse(date=date, count=len(hashes), merkle_root=root_hex, status="OK")


# ────────────────────────────────────────────────────────────────────────────────
# 📚 HGL-CORE-005 KNOWLEDGE — Read-only ledger views
# ────────────────────────────────────────────────────────────────────────────────

@app.get("/cosmos/ledger", response_model=List[CapsuleIndex])
def list_ledger(prefix: Optional[str] = Query(None), limit: int = Query(200, ge=1, le=5000)):
    items: List[CapsuleIndex] = []
    for d in sorted(LEDGER.glob("*")):
        if not d.is_dir():
            continue
        h = d.name
        if prefix and not h.startswith(prefix):
            continue
        r = d / "result.json"
        s = d / "result.json.sig"
        e = d / "envelope.json"
        items.append(CapsuleIndex(
            ledger_hash=h,
            has_result=r.exists(),
            has_signature=s.exists(),
            has_envelope=e.exists(),
        ))
        if len(items) >= limit:
            break
    return items


@app.get("/cosmos/ledger/{ledger_hash}", response_model=CapsuleBundle)
def get_capsule(ledger_hash: str = Path(..., min_length=10, max_length=128)):
    # basic traversal guard
    if "/" in ledger_hash or "\\" in ledger_hash or ".." in ledger_hash:
        raise HTTPException(400, detail="invalid hash")
    d = LEDGER / ledger_hash
    r = d / "result.json"
    s = d / "result.json.sig"
    e = d / "envelope.json"

    if not r.exists():
        raise HTTPException(404, detail="capsule not found")

    try:
        result = json.loads(r.read_text())
    except Exception as ex:
        raise HTTPException(500, detail=f"malformed result.json: {ex}")

    envelope = None
    if e.exists():
        try:
            envelope = json.loads(e.read_text())
        except Exception:
            envelope = None

    sig_path = str(s) if s.exists() else None
    return CapsuleBundle(ledger_hash=ledger_hash, result=result, signature_path=sig_path, envelope=envelope)
