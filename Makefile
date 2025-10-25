# =========================
# HELIX–TTD Makefile
# =========================
# Works in WSL with Windows-side signing.
# Verifies using stdin form to support older OpenSSH in WSL.

SHELL := /bin/bash

# ---- Paths / Vars ----
BIN     := src/triad_orchestrator_mvp.py
TEST    := tests/session.min.json
OUT     := out
LEDGER  := ledger
ROLLDIR := rollups
DATE    := $(shell date +%F)
ROLL    := $(ROLLDIR)/$(DATE)

# ---- Signing / Verify identity ----
# Principal must match the left token in ~/.ssh/allowed_signers
IDENTITY := sbhop@helix
NAMESPACE := ttd-proof

# Windows paths for convenience echo (do not execute in WSL)
WSLUNCROOT := \\wsl.localhost\\Ubuntu\\mnt\\GitHub\\helix-and-triad-schema-v3

# ---- Phony targets ----
.PHONY: help proof verify append clean rollup verify-rollup windows-sign-rollup windows-sign-out

help:
	@echo "Targets:"
	@echo "  make proof            # Run orchestrator, emit $(OUT)/result.json (+hash.txt, envelope.json)"
	@echo "  make verify           # Verify $(OUT)/result.json.sig against ~/.ssh/allowed_signers (stdin form)"
	@echo "  make append           # Copy $(OUT)/* into $(LEDGER)/<ledger_hash>/"
	@echo "  make rollup           # Build daily Merkle rollup under $(ROLLDIR)/YYYY-MM-DD/"
	@echo "  make verify-rollup    # Verify daily merkle_root.txt.sig (stdin form)"
	@echo "  make windows-sign-out # Echo Windows signing cmd for $(OUT)/result.json"
	@echo "  make windows-sign-rollup # Echo Windows signing cmd for daily merkle_root.txt"
	@echo "  make clean            # Remove files in $(OUT)/"

# 1) Produce proof capsule in $(OUT)
proof:
	python3 $(BIN) --test $(TEST) --json --deterministic --seed helix-ttd-v1 --proof-out $(OUT)

# 2) Verify capsule in $(OUT) (stdin form; version-agnostic)
verify:
	@if [ ! -f $(OUT)/result.json ] || [ ! -f $(OUT)/result.json.sig ]; then \
	  echo "Missing $(OUT)/result.json or $(OUT)/result.json.sig. Run 'make proof' and sign first."; exit 2; fi
	ssh-keygen -Y verify \
	  -f ~/.ssh/allowed_signers \
	  -I $(IDENTITY) \
	  -n $(NAMESPACE) \
	  -s $(OUT)/result.json.sig < $(OUT)/result.json && echo "Capsule verify: OK"

# 3) Append capsule to immutable ledger/<hash>/
append:
	@if [ ! -f $(OUT)/result.json ]; then echo "No $(OUT)/result.json; run 'make proof' first."; exit 2; fi
	@HASH=$$(jq -r .ledger_hash $(OUT)/result.json); \
	mkdir -p $(LEDGER)/$$HASH; \
	cp $(OUT)/result.json $(LEDGER)/$$HASH/; \
	[ -f $(OUT)/result.json.sig ] && cp $(OUT)/result.json.sig $(LEDGER)/$$HASH/ || true; \
	[ -f $(OUT)/envelope.json ] && cp $(OUT)/envelope.json $(LEDGER)/$$HASH/ || true; \
	echo "# TTD Proof Capsule\n- Namespace: $(NAMESPACE)\n- Principal: $(IDENTITY)\n- Status: appended" > $(LEDGER)/$$HASH/AUDIT.md; \
	echo "Ledger append complete: $$HASH"

# 4) Build daily Merkle rollup (writes hashes.txt, merkle_root.txt)
rollup:
	python3 tools/merkle_rollup.py | jq

# 5) Verify daily Merkle root (stdin form)
verify-rollup:
	@if [ ! -f $(ROLL)/merkle_root.txt ] || [ ! -f $(ROLL)/merkle_root.txt.sig ]; then \
	  echo "Missing $(ROLL)/merkle_root.txt(.sig). Sign from Windows or create rollup first."; exit 2; fi
	ssh-keygen -Y verify \
	  -f ~/.ssh/allowed_signers \
	  -I $(IDENTITY) \
	  -n $(NAMESPACE) \
	  -s $(ROLL)/merkle_root.txt.sig < $(ROLL)/merkle_root.txt && echo "Rollup verify: OK"

# 6) Windows signing helpers (echo commands you run in PowerShell)
windows-sign-out:
	@echo "Run in Windows PowerShell (normal):"
	@echo "ssh-keygen -Y sign -f %USERPROFILE%\\.ssh\\id_ed25519_sk -n $(NAMESPACE) \"$(WSLUNCROOT)\\$(OUT)\\result.json\""

windows-sign-rollup:
	@echo "Run in Windows PowerShell (normal):"
	@echo "ssh-keygen -Y sign -f %USERPROFILE%\\.ssh\\id_ed25519_sk -n $(NAMESPACE) \"$(WSLUNCROOT)\\$(ROLL)/merkle_root.txt\""

# 7) Clean working output
clean:
	rm -f $(OUT)/*
