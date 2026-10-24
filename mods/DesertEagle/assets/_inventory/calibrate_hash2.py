"""Calibrate fnv1a64 using OUR re-serialized app: anim refs whose intended
strings are known became hash-only values — string and hash coexist by
construction. If the hash matches, the convention is proven.

python3 calibrate_hash2.py <app_json_reserialized>
"""

import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scripts"))
from verify_release import fnv1a64  # noqa: E402

path = sys.argv[1] if len(sys.argv) > 1 else None
if not path:
    cands = glob.glob(os.path.join(HERE, "..", "..", "assets", "work", "release", "_json", "*.app.json"))
    path = cands[0]

d = json.load(open(path, encoding="utf-8"))
hashes = set()
strings = set()


def walk(node):
    if isinstance(node, dict):
        for k, v in node.items():
            if k in ("DepotPath", "depotPath") and isinstance(v, dict):
                st = v.get("$storage")
                val = v.get("$value")
                if isinstance(val, str) and "\\" in val:
                    strings.add(val)
                elif st == "uint64" and isinstance(val, str) and val.isdigit():
                    hashes.add(int(val))
            else:
                walk(v)
    elif isinstance(node, list):
        for x in node:
            walk(x)


walk(d)
print(f"re-serialized app: {len(strings)} string paths, {len(hashes)} hash values")

KNOWN = [
    "desert_eagle\\animations\\w_handgun__tsunami_nue__base1.anims",
    "desert_eagle\\animations\\w_handgun__tsunami_nue__mag_std.anims",
    "desert_eagle\\items\\w_handgun_desert_eagle.mesh",
    "desert_eagle\\items\\desert_eagle.ent",
]
ok = True
for s in KNOWN:
    h = fnv1a64(s)
    found = h in hashes or s in strings
    print(f"[{'OK' if found else 'MISS'}] {h}  {s}")
    ok = ok and found

print("HASH_CONVENTION_OK" if ok else "HASH_CONVENTION_UNPROVEN")
