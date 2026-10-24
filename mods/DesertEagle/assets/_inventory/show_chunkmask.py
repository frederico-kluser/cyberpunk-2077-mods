"""Inspect chunkMask/LOD fields of the kept mesh component in our .app JSON."""

import json

path = r"C:\Users\kluse\Projects\cyberpunk-2077\mods\DesertEagle\assets\work\de_app\desert_eagle.app.json"
d = json.load(open(path, encoding="utf-8"))
a0 = d["Data"]["RootChunk"]["appearances"][0]["Data"]

for c in a0["components"]:
    cd = c.get("Data", c)
    if cd.get("$type") == "entSkinnedMeshComponent":
        print("component keys:", sorted(cd.keys()))
        for k in sorted(cd.keys()):
            if any(t in k.lower() for t in ("chunk", "lod", "mask", "mesh", "render", "cast", "name")):
                val = cd[k]
                text = json.dumps(val, default=str)
                print(f"  {k} = {text[:220]}")
