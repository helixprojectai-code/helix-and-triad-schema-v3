#!/usr/bin/env python3
import sys, json, hashlib, pathlib, datetime

def h(x): return hashlib.sha3_256(x).digest()
def merkle_root(leaves):
    if not leaves: return hashlib.sha3_256(b'').hexdigest()
    layer = [hashlib.sha3_256(s.encode()).digest() for s in leaves]
    while len(layer) > 1:
        if len(layer) % 2 == 1: layer.append(layer[-1])
        layer = [h(layer[i]+layer[i+1]) for i in range(0,len(layer),2)]
    return layer[0].hex()

root = pathlib.Path("ledger")
today = datetime.date.today().isoformat()  # YYYY-MM-DD
hashes = []
for p in sorted(root.iterdir()):
    j = p/"result.json"
    if j.is_file():
        d = json.loads(j.read_text())
        ts = d.get("timestamp_utc","")
        if ts.startswith(today):
            hashes.append(d["ledger_hash"])

mr = merkle_root(hashes)
out = pathlib.Path("rollups")/today
out.mkdir(parents=True, exist_ok=True)
(pathlib.Path(out/"hashes.txt")).write_text("\n".join(hashes)+"\n", encoding="utf-8")
(pathlib.Path(out/"merkle_root.txt")).write_text(mr+"\n", encoding="utf-8")
print(json.dumps({"date":today,"count":len(hashes),"merkle_root":mr}, indent=2))
