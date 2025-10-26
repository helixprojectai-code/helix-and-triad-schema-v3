#!/usr/bin/env python3
"""
HELIX-TTD Triad Orchestrator MVP (cumulative hardened)
- Deterministic hashing (optional seed/nonce)
- Canonical JSON hashing + float quantization
- Minimal JSON schema gate
- Per-phase metrics + meaningful total time
- ISO-8601 UTC timestamp (or fixed for reproducibility)
- Proof capsule writer (--proof-out)
- Ed25519 detached signature via OpenSSH ssh-keygen -Y (YubiKey-friendly)
"""

import json
import sys
import argparse
import hashlib
import time
import subprocess
from decimal import Decimal, ROUND_HALF_EVEN
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# ------------------------ 🔍 Minimal schema gate ------------------------
def _schema_validate(obj: Dict[str, Any]) -> None:
    def req(d, keys, path):
        for k in keys:
            if k not in d:
                raise ValueError(f"Schema: missing key '{'.'.join(path+[k])}'")
    if not isinstance(obj, dict):
        raise ValueError("Top-level JSON must be an object")
    req(obj, ["hgl_session"], [])
    hs = obj["hgl_session"]; 
    if not isinstance(hs, dict):
        raise ValueError("hgl_session must be an object")

    req(hs, ["metadata", "glyphs", "optical_encoding"], ["hgl_session"])
    md = hs["metadata"]
    if not isinstance(md, dict):
        raise ValueError("hgl_session.metadata must be an object")
    req(md, ["timestamp", "cultural_context", "sovereign_level"], ["hgl_session","metadata"])

    if not isinstance(hs["glyphs"], list):
        raise ValueError("hgl_session.glyphs must be an array")
    oe = hs["optical_encoding"]
    if not isinstance(oe, dict):
        raise ValueError("hgl_session.optical_encoding must be an object")
    req(oe, ["resolution", "compression_target"], ["hgl_session","optical_encoding"])

    pz = hs.get("paradox_zones", [])
    if pz is not None:
        if not isinstance(pz, list):
            raise ValueError("hgl_session.paradox_zones must be an array if present")
        for i, z in enumerate(pz):
            if not isinstance(z, dict):
                raise ValueError(f"paradox_zones[{i}] must be an object")
            req(z, ["glyph_pair", "resolution_protocol"], ["hgl_session","paradox_zones", str(i)])

# ------------------------ 📚 Canonical JSON -----------------------------
def canonical_json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(',', ':')).encode('utf-8')

# ------------------------ 📊 Float quantization -------------------------
def qfloat(x: float, ndp: int = 3) -> str:
    # Platform-stable decimal rounding for hash inputs
    return str(Decimal(x).quantize(Decimal('1.' + '0'*ndp), rounding=ROUND_HALF_EVEN))

# ------------------------ 🔐 Ledger hash -------------------------------
def generate_ledger_hash(session_data: Dict[str, Any],
                         paradoxes_resolved: int,
                         compression_achieved: float,
                         deterministic: bool = False,
                         nonce: Optional[int] = None,
                         seed: Optional[str] = None) -> str:
    hs = session_data['hgl_session']
    md = hs['metadata']

    if nonce is None and deterministic:
        seed_material = {
            "session_id": md["timestamp"],
            "glyph_count": len(hs["glyphs"]),
            "cultural_context": md["cultural_context"],
            "sovereign_level": md["sovereign_level"],
            "scope": md.get("scope", ""),
            "compression_ratio": qfloat(compression_achieved, 3),
            "paradox_resolved": paradoxes_resolved,
            "seed": seed or ""
        }
        nonce = int.from_bytes(hashlib.sha3_256(canonical_json_bytes(seed_material)).digest()[:8], 'big')
    if nonce is None:
        nonce = time.time_ns()

    hash_input = {
        "session_id": md["timestamp"],
        "glyph_count": len(hs["glyphs"]),
        "paradox_resolved": paradoxes_resolved,
        "compression_ratio": qfloat(compression_achieved, 3),
        "cultural_context": md["cultural_context"],
        "sovereign_level": md["sovereign_level"],
        "scope": md.get("scope", ""),
        "nonce": nonce
    }
    full_hash = hashlib.sha3_256(canonical_json_bytes(hash_input)).hexdigest()
    return f"ttd_ledger_v1_{full_hash}"

# ------------------------ 🔮 Simulated phases --------------------------
def simulate_optical_rendering(hs: Dict[str, Any]) -> Dict[str, Any]:
    print("🔮 Phase 1: Optical Rendering")
    glyphs = len(hs['glyphs'])
    res = hs['optical_encoding']['resolution']
    ctx = hs['metadata']['cultural_context']
    print(f"   - Glyphs: {glyphs}")
    print(f"   - Resolution: {res}")
    print(f"   - Cultural Context: {ctx}")
    complexity = glyphs * len(hs.get('paradox_zones', []))
    render_time = max(0.05, complexity * 0.005)
    return {"success": True, "render_time": render_time, "image_size_mb": 67.1,
            "paradox_zones": len(hs.get('paradox_zones', []))}

def simulate_deepseek_compression(hs: Dict[str, Any]) -> Dict[str, Any]:
    print("\n🔮 Phase 2: DeepSeek OCR Compression")
    target_ratio = float(hs['optical_encoding']['compression_target'])
    achieved_ratio = target_ratio * 0.988
    print(f"   - Target Ratio: {target_ratio}x")
    print(f"   - Achieved Ratio: {achieved_ratio:.2f}x")
    print(f"   - Fidelity: 98.1%")
    print(f"   - Output Tokens: ~2,700 vision tokens")
    return {"success": True, "compression_ratio": achieved_ratio,
            "fidelity": 0.981, "processing_time": 1.2}

def simulate_grok_validation(hs: Dict[str, Any]) -> Dict[str, Any]:
    print("\n🔮 Phase 3: Grok Truth Validation")
    pz = hs.get('paradox_zones', []) or []
    resolved = len(pz)
    print(f"   - Paradox Zones: {len(pz)}")
    print(f"   - Resolved: {resolved}/{len(pz)}")
    for i, z in enumerate(pz, 1):
        print(f"     {i}. {z['glyph_pair']} → {z['resolution_protocol']} ✅")
    rate = 1.0 if len(pz) == 0 else resolved / len(pz)
    return {"success": True, "paradoxes_resolved": resolved,
            "total_paradoxes": len(pz), "resolution_rate": rate,
            "validation_time": 0.8}

def simulate_ttd_ledger_broadcast(session_data: Dict[str, Any],
                                  validation: Dict[str, Any],
                                  compression: Dict[str, Any],
                                  deterministic: bool,
                                  nonce: Optional[int],
                                  seed: Optional[str],
                                  block_height: Optional[int],
                                  fixed_timestamp: Optional[str]) -> Dict[str, Any]:
    print("\n🔮 Phase 4: TTD Ledger Broadcast")
    ledger_hash = generate_ledger_hash(
        session_data,
        paradoxes_resolved=validation['paradoxes_resolved'],
        compression_achieved=compression['compression_ratio'],
        deterministic=deterministic,
        nonce=nonce,
        seed=seed
    )
    ts = fixed_timestamp or datetime.now(timezone.utc).isoformat(timespec='seconds')
    print(f"   - Ledger Hash: {ledger_hash}")
    print("   - Algorithm: SHA3-256")
    print("   - Status: IMMUTABLE_ENTRY")
    print(f"   - Timestamp: {ts}")
    if block_height is not None:
        print(f"   - Block Height: {block_height}")
    return {
        "success": True,
        "ledger_hash": ledger_hash,
        "algorithm": "SHA3-256",
        "block_height": block_height,
        "broadcast_time": 0.5,
        "status": "IMMUTABLE_ENTRY",
        "timestamp": ts
    }

# ------------------------ 🛡️ Proof capsule ----------------------------
def write_proof_capsule(outdir: Path, result: Dict[str, Any]) -> Dict[str, str]:
    outdir.mkdir(parents=True, exist_ok=True)
    result_json = json.dumps(result, separators=(',', ':'), sort_keys=True)
    (outdir/"result.json").write_text(result_json, encoding="utf-8")
    (outdir/"hash.txt").write_text(result["ledger_hash"] + "\n", encoding="utf-8")
    # Minimal audit envelope
    envelope = {
        "type": "TTD_PROOF",
        "alg": result["ledger_algorithm"],
        "hash": result["ledger_hash"],
        "ts": result["timestamp_utc"],
        "meta": {
            "cultural_context": result["cultural_context"],
            "sovereign_level": result["sovereign_level"]
        }
    }
    (outdir/"envelope.json").write_text(
        json.dumps(envelope, separators=(',', ':'), sort_keys=True), encoding="utf-8"
    )
    return {"result": str(outdir/"result.json"),
            "hash": str(outdir/"hash.txt"),
            "envelope": str(outdir/"envelope.json")}

# ------------------------ 🔑 SSH/YubiKey signing -----------------------
def ssh_sign_file(message_path: Path,
                  signer_key_path: Path,
                  namespace: str,
                  signature_out: Path) -> None:
    """
    Uses `ssh-keygen -Y sign` to produce a detached signature.
    Works with YubiKey-backed SSH keys via agent.
    signer_key_path: path to the *public* key file (e.g., ~/.ssh/id_ed25519_sk.pub)
    """
    # ssh-keygen writes <message>.sig by default; we'll control path using -O
    cmd = [
        "ssh-keygen", "-Y", "sign",
        "-f", str(signer_key_path),
        "-n", namespace,
        "-O", f"sigfile={signature_out}",
        str(message_path)
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"❌ ssh-keygen sign failed: {e.stderr.decode('utf-8', errors='ignore')}\n")
        raise

def ssh_verify_file(message_path: Path,
                    signature_path: Path,
                    allowed_signers: Path,
                    identity: str,
                    namespace: str) -> bool:
    cmd = [
        "ssh-keygen", "-Y", "verify",
        "-f", str(allowed_signers),
        "-I", identity,
        "-n", namespace,
        "-s", str(signature_path),
        "-m", str(message_path)
    ]
    proc = subprocess.run(cmd, capture_output=True)
    return proc.returncode == 0

# ------------------------ 🎯 Orchestration -----------------------------
def execute_triad_orchestration(session_data: Dict[str, Any],
                                deterministic: bool,
                                nonce: Optional[int],
                                seed: Optional[str],
                                block_height: Optional[int],
                                fixed_timestamp: Optional[str],
                                quiet_json: bool,
                                proof_out: Optional[Path],
                                ssh_pubkey: Optional[Path],
                                allowed_signers: Optional[Path],
                                ssh_identity: Optional[str],
                                namespace: str) -> Dict[str, Any]:
    print("🚀 HELIX-TTD Triad Orchestrator MVP")
    print("=" * 50)

    hs = session_data['hgl_session']
    r1 = simulate_optical_rendering(hs)
    r2 = simulate_deepseek_compression(hs)
    r3 = simulate_grok_validation(hs)
    r4 = simulate_ttd_ledger_broadcast(session_data, r3, r2, deterministic, nonce, seed, block_height, fixed_timestamp)

    total_time = r1["render_time"] + r2["processing_time"] + r3["validation_time"] + r4["broadcast_time"]
    result = {
        "status": "success",
        "total_execution_time_s": total_time,
        "metrics": {
            "render_time_s": r1["render_time"],
            "ocr_time_s": r2["processing_time"],
            "validate_time_s": r3["validation_time"],
            "broadcast_time_s": r4["broadcast_time"]
        },
        "compression_achieved": r2["compression_ratio"],
        "fidelity_verified": r2["fidelity"],
        "paradox_resolution_rate": r3["resolution_rate"],
        "ledger_hash": r4["ledger_hash"],
        "ledger_algorithm": r4["algorithm"],
        "block_height": r4["block_height"],
        "cultural_context": hs["metadata"]["cultural_context"],
        "sovereign_level": hs["metadata"]["sovereign_level"],
        "timestamp_utc": r4["timestamp"]
    }

    print("\n" + "=" * 50)
    print("🎯 EXECUTION COMPLETE")
    print("=" * 50)
    if quiet_json:
        print(json.dumps(result, separators=(',', ':'), sort_keys=True))
    else:
        print(json.dumps(result, indent=2, sort_keys=True))

    # Write capsule & sign if requested
    if proof_out:
        paths = write_proof_capsule(proof_out, result)
        if ssh_pubkey:
            sig_path = proof_out/"result.json.sig"
            ssh_sign_file(Path(paths["result"]), ssh_pubkey, namespace, sig_path)
            # Optional immediate verify if allowed_signers+identity provided
            if allowed_signers and ssh_identity:
                ok = ssh_verify_file(Path(paths["result"]), sig_path, allowed_signers, ssh_identity, namespace)
                print(f"Signature verify: {'OK' if ok else 'FAIL'}")

    return result

# ------------------------ 🧭 CLI --------------------------------------
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="HELIX-TTD Triad Orchestrator MVP (simulated)")
    p.add_argument("--test", required=True, help="Path to test session JSON file")
    p.add_argument("--json", action="store_true", help="Emit machine-friendly JSON only")
    p.add_argument("--deterministic", action="store_true", help="Deterministic ledger hashing (nonce derived)")
    p.add_argument("--nonce", type=int, help="Explicit nonce (overrides deterministic/time-based)")
    p.add_argument("--seed", type=str, help="Optional seed material for deterministic nonce")
    p.add_argument("--block-height", type=int, help="Optional block height to record")
    p.add_argument("--fixed-timestamp", type=str, help="Use this UTC timestamp (e.g., 2025-10-25T14:21:08Z)")
    p.add_argument("--proof-out", type=str, help="Directory to write proof capsule (result.json, hash.txt, envelope.json, result.json.sig)")
    # SSH/YubiKey signing options
    p.add_argument("--ssh-pubkey", type=str, help="Path to signer *public* key (e.g., ~/.ssh/id_ed25519_sk.pub)")
    p.add_argument("--allowed-signers", type=str, help="Path to allowed_signers file (for verify)")
    p.add_argument("--ssh-identity", type=str, help="Identity label in allowed_signers (e.g., steve@helix)")
    p.add_argument("--namespace", type=str, default="ttd-proof", help="Signature namespace for ssh-keygen -Y")
    return p.parse_args()

def load_session_config(config_path: str) -> Dict[str, Any]:
    try:
        data = json.loads(Path(config_path).read_text(encoding='utf-8'))
        _schema_validate(data)
        return data
    except Exception as e:
        print(f"❌ Error loading/validating session config: {e}")
        sys.exit(1)

def main():
    args = parse_args()
    test_path = Path(args.test)
    if not test_path.exists():
        print(f"❌ Test file not found: {args.test}")
        sys.exit(1)

    session_data = load_session_config(str(test_path))
    proof_out = Path(args.proof_out).resolve() if args.proof_out else None
    ssh_pubkey = Path(args.ssh_pubkey).expanduser().resolve() if args.ssh_pubkey else None
    allowed_signers = Path(args.allowed_signers).expanduser().resolve() if args.allowed_signers else None

    result = execute_triad_orchestration(
        session_data=session_data,
        deterministic=bool(args.deterministic),
        nonce=args.nonce,
        seed=args.seed,
        block_height=args.block_height,
        fixed_timestamp=args.fixed_timestamp,
        quiet_json=bool(args.json),
        proof_out=proof_out,
        ssh_pubkey=ssh_pubkey,
        allowed_signers=allowed_signers,
        ssh_identity=args.ssh_identity,
        namespace=args.namespace
    )
    sys.exit(0 if result.get("status") == "success" else 2)

if __name__ == "__main__":
    main()

