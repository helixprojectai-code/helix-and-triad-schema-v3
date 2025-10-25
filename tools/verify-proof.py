#!/usr/bin/env python3
import sys, subprocess, json, pathlib, os

def main():
    if len(sys.argv) != 4:
        print("usage: verify-proof.py <result.json> <signature.sig> <allowed_signers>", file=sys.stderr)
        sys.exit(2)
    msg, sig, allow = map(pathlib.Path, sys.argv[1:])
    # identity label defaults to "<USERNAME>@helix" for convenience
    identity = os.environ.get("TTD_IDENTITY") or (os.environ.get("USERNAME") or os.environ.get("USER") or "unknown") + "@helix"
    ns = os.environ.get("TTD_NAMESPACE") or "ttd-proof"

    proc = subprocess.run([
        "ssh-keygen","-Y","verify",
        "-f", str(allow),
        "-I", identity,
        "-n", ns,
        "-s", str(sig),
        "-m", str(msg)
    ], capture_output=True, text=True)

    print(json.dumps({
        "message": str(msg),
        "signature": str(sig),
        "allowed_signers": str(allow),
        "identity": identity,
        "namespace": ns,
        "verified": proc.returncode == 0,
        "stderr": proc.stderr.strip()
    }, indent=2))
    sys.exit(0 if proc.returncode == 0 else 1)

if __name__ == "__main__":
    main()
