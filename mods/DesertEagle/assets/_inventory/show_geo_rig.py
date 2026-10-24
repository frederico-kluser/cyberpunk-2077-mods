"""Show geometry + rig JSON structure for the animation pose render."""

import json

g = json.load(open(r"C:\Users\kluse\Projects\cyberpunk-2077\mods\DesertEagle\assets\work\de_geometry.json", encoding="utf-8"))
print("top keys:", sorted(g.keys()))
c = g["chunks"][0]
print("chunk keys:", sorted(c.keys()))
for k in sorted(c.keys()):
    v = c[k]
    n = len(v) if hasattr(v, "__len__") else v
    print(f"  {k}: {type(v).__name__} len/val={n}")

r = json.load(open(r"C:\Users\kluse\Projects\cyberpunk-2077\mods\DesertEagle\assets\_inventory\nue_rig.json", encoding="utf-8"))
print("\nrig keys:", sorted(r.keys()))
for k in sorted(r.keys()):
    v = r[k]
    n = len(v) if hasattr(v, "__len__") else v
    print(f"  {k}: {type(v).__name__} len/val={n}")
if "bones" in r:
    print("bone[0]:", json.dumps(r["bones"][0], default=str)[:200])
