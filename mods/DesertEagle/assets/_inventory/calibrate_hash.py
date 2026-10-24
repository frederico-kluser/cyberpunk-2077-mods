"""Calibrate the FNV1a-64 convention against vanilla CR2W hash values.

Some vanilla ResourcePaths are stored as uint64 hashes. Where the intended
path is known (the Nue's own files), our fnv1a64 must reproduce the stored
hash — this proves the convention the anims resolution relies on.

python3 calibrate_hash.py
"""

import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scripts"))
from verify_release import fnv1a64  # noqa: E402

JSONS = os.path.join(HERE, "app_json")


def collect_hash_values(node, out):
    if isinstance(node, dict):
        for k, v in node.items():
            if k in ("DepotPath", "depotPath") and isinstance(v, dict):
                st = v.get("$storage")
                val = v.get("$value")
                if st == "uint64" and isinstance(val, str) and val.isdigit():
                    out.add(int(val))
            else:
                collect_hash_values(v, out)
    elif isinstance(node, list):
        for x in node:
            collect_hash_values(x, out)


def collect_string_paths(node, out):
    if isinstance(node, dict):
        for k, v in node.items():
            if k in ("DepotPath", "depotPath") and isinstance(v, dict):
                val = v.get("$value")
                if isinstance(val, str) and "\\" in val:
                    out.add(val)
            else:
                collect_string_paths(v, out)
    elif isinstance(node, list):
        for x in node:
            collect_string_paths(x, out)


hashes = set()
strings = set()
for path in glob.glob(os.path.join(JSONS, "*.json")):
    d = json.load(open(path, encoding="utf-8"))
    collect_hash_values(d, hashes)
    collect_string_paths(d, strings)

print(f"vanilla hash values found: {len(hashes)}")
print(f"vanilla string paths found: {len(strings)}")

# candidate paths: every known Nue path (strings) — their hashes must appear
# among the stored hash values if the convention matches
hits = []
for s in strings:
    h = fnv1a64(s)
    if h in hashes:
        hits.append((s, h))

print(f"\nstring paths whose fnv1a64 matches a stored hash: {len(hits)}")
for s, h in hits[:8]:
    print(f"  MATCH {h}  {s}")

ok = len(hits) > 0
print("HASH_CONVENTION_OK" if ok else "HASH_CONVENTION_UNPROVEN")
