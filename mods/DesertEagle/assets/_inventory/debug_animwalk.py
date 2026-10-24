"""Debug the verify anim walk against the current app JSON."""

import json

path = r"C:\Users\kluse\Projects\cyberpunk-2077\mods\DesertEagle\assets\work\de_app\desert_eagle.app.json"
doc = json.load(open(path, encoding="utf-8"))
rc = doc["Data"]["RootChunk"]

anim_refs = []


def anim_refs_walk(node):
    if isinstance(node, dict):
        for k, v in node.items():
            if k in ("DepotPath", "depotPath") and isinstance(v, dict):
                val = v.get("$value")
                if isinstance(val, str) and val.endswith(".anims"):
                    anim_refs.append(val)
            else:
                anim_refs_walk(v)
    elif isinstance(node, list):
        for item in node:
            anim_refs_walk(item)


anim_refs_walk(rc)
print(f"anim_refs found: {len(anim_refs)}")
ours = [r for r in anim_refs if r.startswith("desert_eagle\\animations\\")]
print(f"ours: {len(ours)}")
for r in anim_refs[:6]:
    print("  ", repr(r))
