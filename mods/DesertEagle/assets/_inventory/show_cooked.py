"""Inspect the cooked appearance blob of chunk[28] in compiledData."""

import json

path = r"C:\Users\kluse\Projects\cyberpunk-2077\mods\DesertEagle\assets\work\de_app\desert_eagle.app.json"
d = json.load(open(path, encoding="utf-8"))
a0 = d["Data"]["RootChunk"]["appearances"][0]["Data"]
chunks = a0["compiledData"]["Data"]["Chunks"]
c28 = chunks[28].get("Data", chunks[28])

cad = c28.get("cookedAppearanceData")
print("cookedAppearanceData type:", type(cad))
if isinstance(cad, dict):
    print("keys:", sorted(cad.keys()))
    print(json.dumps(cad, default=str)[:1500])
print("\nmeshProxy:", json.dumps(c28.get("meshProxy"), default=str)[:300])

data = a0["compiledData"]["Data"]
for k in ("CruidDict", "CruidIndex", "Sections", "Version"):
    v = data.get(k)
    if isinstance(v, list):
        print(f"{k}: list[{len(v)}] sample={json.dumps(v[:2], default=str)[:200]}")
    elif isinstance(v, dict):
        els = v.get("Elements")
        print(f"{k}: dict keys={list(v.keys())} elements={len(els) if isinstance(els, list) else els}")
    else:
        print(f"{k}: {v}")
