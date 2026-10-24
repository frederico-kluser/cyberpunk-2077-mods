"""Show storage + value of anim refs in the source app JSON."""

import json

path = r"C:\Users\kluse\Projects\cyberpunk-2077\mods\DesertEagle\assets\work\de_app\desert_eagle.app.json"
doc = json.load(open(path, encoding="utf-8"))


def walk(node):
    if isinstance(node, dict):
        for k, v in node.items():
            if k in ("DepotPath", "depotPath") and isinstance(v, dict):
                val = v.get("$value")
                if isinstance(val, str) and val.endswith(".anims"):
                    print(f"  storage={v.get('$storage'):8s} value={val}")
            else:
                walk(v)
    elif isinstance(node, list):
        for item in node:
            walk(item)


walk(doc["Data"]["RootChunk"])
