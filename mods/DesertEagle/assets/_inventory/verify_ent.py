"""Verify the .ent inside the final archive has the synced component matrix."""

import json
import sys

path = sys.argv[1]
d = json.load(open(path, encoding="utf-8"))
rc = d["Data"]["RootChunk"]
comps = rc.get("components") or []
print("ENT components:", len(comps))
meshy = []
for c in comps:
    cd = c.get("Data", c)
    if cd.get("$type") == "entSkinnedMeshComponent":
        mesh = cd.get("mesh", {})
        dp = mesh.get("DepotPath", {})
        meshy.append(dp.get("$value"))
print("skinned mesh comps:", meshy)
name = rc.get("defaultAppearance")
print("defaultAppearance:", name.get("$value") if isinstance(name, dict) else name)
print("ENT_VERIFY_OK" if len(comps) == 17 and all("desert_eagle" in (m or "") for m in meshy) else "ENT_VERIFY_FAIL")
