"""Audit every depot reference inside our compiled .app and .ent (and their
JSON forms): flag anything still pointing at vanilla tsunami_nue assets."""

import json
import sys

FILES = {
    "app": r"C:\Users\kluse\Projects\cyberpunk-2077\mods\DesertEagle\assets\work\de_app\desert_eagle.app.json",
    "ent": r"C:\Users\kluse\Projects\cyberpunk-2077\mods\DesertEagle\assets\work\de_app\desert_eagle.ent.json",
}


def walk(node, hits, where=""):
    if isinstance(node, dict):
        for k, v in node.items():
            if k in ("DepotPath", "depotPath", "path"):
                val = v.get("$value") if isinstance(v, dict) else v
                if isinstance(val, str) and val.strip():
                    hits.append((where, val))
            elif k in ("name",) and isinstance(v, dict):
                pass
            else:
                walk(v, hits, where)
    elif isinstance(node, list):
        for i, item in enumerate(node):
            walk(item, hits, where)


for label, path in FILES.items():
    d = json.load(open(path, encoding="utf-8"))
    hits = []
    walk(d, hits, label)
    print(f"\n== {label}: {len(hits)} depot references ==")
    seen = {}
    for where, val in hits:
        seen[val] = seen.get(val, 0) + 1
    for val, n in sorted(seen.items()):
        flag = "  <-- VANILLA NUE" if "tsunami_nue" in val.lower() else ""
        print(f"  [{n:2d}x] {val}{flag}")
