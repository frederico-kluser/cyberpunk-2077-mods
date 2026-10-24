"""Print the compiledData chunk table of our app appearance."""

import json

path = r"C:\Users\kluse\Projects\cyberpunk-2077\mods\DesertEagle\assets\work\de_app\desert_eagle.app.json"
d = json.load(open(path, encoding="utf-8"))
a0 = d["Data"]["RootChunk"]["appearances"][0]["Data"]
cd = a0.get("compiledData")
print("compiledData keys:", sorted(cd.keys()) if isinstance(cd, dict) else type(cd))
data = cd.get("Data", cd)
print("Data keys:", sorted(data.keys()) if isinstance(data, dict) else type(data))
chunks = data.get("Chunks") if isinstance(data, dict) else None
if isinstance(chunks, dict):
    chunks = chunks.get("Elements") or chunks.get("items") or []
print(f"chunks: {len(chunks) if chunks is not None else None}")
for i, ch in enumerate(chunks or []):
    c = ch.get("Data", ch) if isinstance(ch, dict) else {}
    ctype = c.get("$type", "?")
    mesh = c.get("mesh")
    mpath = ""
    if isinstance(mesh, dict):
        dp = mesh.get("DepotPath", {})
        mpath = dp.get("$value", "")
    deps = c.get("appearanceDependency")
    ndeps = len(deps) if isinstance(deps, list) else 0
    other = [k for k in c.keys() if k not in ("$type", "mesh", "appearanceDependency")]
    print(f"  [{i:2d}] {ctype} mesh=({mpath.split(chr(92))[-1] if mpath else '-'}) deps={ndeps} keys={other}")
