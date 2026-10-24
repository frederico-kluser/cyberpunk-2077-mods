"""Locate WHERE vanilla mesh references live inside the .app/.ent JSON."""

import json

FILES = {
    "app": r"C:\Users\kluse\Projects\cyberpunk-2077\mods\DesertEagle\assets\work\de_app\desert_eagle.app.json",
    "ent": r"C:\Users\kluse\Projects\cyberpunk-2077\mods\DesertEagle\assets\work\de_app\desert_eagle.ent.json",
}


def walk(node, chain, hits):
    if isinstance(node, dict):
        for k, v in node.items():
            if k in ("DepotPath", "depotPath"):
                val = v.get("$value") if isinstance(v, dict) else v
                if isinstance(val, str) and val.endswith(".mesh"):
                    hits.append((">".join(chain + [k]), val))
            else:
                walk(v, chain + [k], hits)
    elif isinstance(node, list):
        for i, item in enumerate(node):
            walk(item, chain + [f"[{i}]"], hits)


for label, path in FILES.items():
    d = json.load(open(path, encoding="utf-8"))
    hits = []
    walk(d, [label], hits)
    print(f"\n== {label}: {len(hits)} .mesh references ==")
    for chain, val in hits:
        short = val.split("\\")[-1]
        print(f"  {chain}")
        print(f"      -> {short}")
