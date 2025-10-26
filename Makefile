.RECIPEPREFIX := >
# =========================
# HELIX–TTD Minimal Make
# =========================
ROLL=rollups/$(shell date +%F)

.PHONY: help rollup verify-rollup

help:
> @echo "Targets:"
> @echo "  make rollup         # build today's Merkle root from ledger/*/result.json"
> @echo "  make verify-rollup  # verify today's merkle_root signature (stdin form)"

rollup:
> python3 tools/merkle_rollup.py | jq

verify-rollup:
> ssh-keygen -Y verify \
>   -f ~/.ssh/allowed_signers \
>   -I sbhop@helix \
>   -n ttd-proof \
>   -s $(ROLL)/merkle_root.txt.sig < $(ROLL)/merkle_root.txt
