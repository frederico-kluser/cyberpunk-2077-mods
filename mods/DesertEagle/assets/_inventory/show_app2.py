"""Print the kept appearance's component structure of the Nue .app JSON."""

import json

path = r"C:\Users\kluse\Projects\cyberpunk-2077\mods\DesertEagle\assets\_inventory\app_json\w_handgun__tsunami_nue.app.json"
d = json.load(open(path, encoding="utf-8"))
apps = d["Data"]["RootChunk"]["appearances"]

a0 = apps[0]["Data"]
print("appearance0 keys:", list(a0.keys()))
name = a0.get("name")
print("name:", name.get("$value") if isinstance(name, dict) else name)
print("visualTags:", json.dumps(a0.get("visualTags"))[:200])

comps = a0.get("components") or []
print(f"\ncomponents: {len(comps)}")
for c in comps[:12]:
    cd = c.get("Data", c)
    ctype = cd.get("$type")
    label = cd.get("name", {})
    label = label.get("$value") if isinstance(label, dict) else label
    mesh = cd.get("mesh")
    meshpath = ""
    if isinstance(mesh, dict):
        dp = mesh.get("DepotPath") or mesh.get("depotPath")
        if isinstance(dp, dict):
            meshpath = dp.get("$value", "")
        elif isinstance(dp, str):
            meshpath = dp
    print(f"  - {ctype} name={label} mesh={meshpath}")

deps = a0.get("resolvedDependencies")
print("\nresolvedDependencies:", type(deps), (len(deps) if isinstance(deps, list) else ""))
if isinstance(deps, list) and deps:
    print("  dep0:", json.dumps(deps[0])[:300])
