"""Walk the RE-SERIALIZED app JSON (from CR2W) for anim refs."""

import json
import sys

path = sys.argv[1]
doc = json.load(open(path, encoding="utf-8"))
rc = doc["Data"]["RootChunk"]

anim_refs = []


def walk(node):
    if isinstance(node, dict):
        for k, v in node.items():
            if k in ("DepotPath", "depotPath") and isinstance(v, dict):
                val = v.get("$value")
                if isinstance(val, str) and val.endswith(".anims"):
                    anim_refs.append((val, v.get("$storage")))
            else:
                walk(v)
    elif isinstance(node, list):
        for item in node:
            walk(item)


walk(rc)
print(f"anim refs: {len(anim_refs)}")
ours = [(v, s) for v, s in anim_refs if v.startswith("desert_eagle\\animations\\")]
print(f"ours: {len(ours)}")
for v, s in ours[:4]:
    print("  ", repr(v), "storage=", s)
odd = [(v, s) for v, s in anim_refs if not isinstance(v, str) or not v.endswith(".anims")][:0]
