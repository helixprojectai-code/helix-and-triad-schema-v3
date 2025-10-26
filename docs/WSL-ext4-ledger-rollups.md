# 🧭 WSL ext4 mounts for HELIX-TTD ledger & rollups (prod)
**File path:** `/mnt/GitHub/helix-and-triad-schema-v3/docs/WSL-ext4-ledger-rollups.md`  
**Last updated:** 2025-10-26  
**Author:** victusadmin@Helix (WSL Ubuntu environment)  

---

## 📚 KNOWLEDGE (HGL-CORE-005)
The production rollup endpoint (`/cosmos/rollups/daily`) failed in WSL because Docker was writing to Windows-mounted paths (`/mnt/...`) that use **DrvFs**.  
DrvFs does not honor POSIX permissions. `chmod` and `chown` appear to succeed but don’t apply real ACLs.  

The failing path was:
/mnt/GitHub/helix-and-triad-schema-v3/rollups/2025-10-26/hashes.txt

Error:


PermissionError: [Errno 13] Permission denied: '/app/rollups/2025-10-26/hashes.txt'


Solution: move the writable data out of the repo and into a **native ext4 path** under WSL.  
This ensures proper ownership, consistent inode behavior, and working UID/GID mapping.

---

## 🔗 INTEGRATE — Move data to ext4 & mount (HGL-CORE-004)
### 1️⃣ Move and remap the data to WSL ext4:
```bash
cd /mnt/GitHub/helix-and-triad-schema-v3
docker compose down

# Create native ext4 directories under /home
mkdir -p /home/victusadmin/helix-data/ledger
mkdir -p /home/victusadmin/helix-data/rollups

# Non-destructive sync from repo
rsync -a ledger/  /home/victusadmin/helix-data/ledger/ 2>/dev/null || true
rsync -a rollups/ /home/victusadmin/helix-data/rollups/ 2>/dev/null || true
