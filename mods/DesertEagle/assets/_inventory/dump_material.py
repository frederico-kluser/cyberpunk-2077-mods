"""Dump the raw JSON of the first material instance (structure discovery)."""

import json

path = r"C:\Users\kluse\Projects\cyberpunk-2077\mods\DesertEagle\assets\_inventory\mesh_json\w_handgun__tsunami_nue__base1_01.mesh.json"
d = json.load(open(path, encoding="utf-8"))
rc = d["Data"]["RootChunk"]


def find(node, key):
    if isinstance(node, dict):
        if key in node:
            return node[key]
        for v in node.values():
            r = find(v, key)
            if r is not None:
                return r
    elif isinstance(node, list):
        for v in node:
            r = find(v, key)
            if r is not None:
                return r
    return None


buf = find(rc, "localMaterialBuffer")
mats = buf.get("materials") or []
print(json.dumps(mats[0], default=str)[:2000])
print("...")
# and a material that has a texture value (the decal one references an xbm)
for i, m in enumerate(mats):
    s = json.dumps(m, default=str)
    if "_d01.xbm" in s or "white.xbm" in s:
        print(f"\n=== material[{i}] (has direct xbm ref) ===")
        print(s[:2500])
        break
