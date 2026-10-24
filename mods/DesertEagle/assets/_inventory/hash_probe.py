"""Find the ResourcePath hash convention by matching the original value."""

import json

path = r"C:\Users\kluse\Projects\cyberpunk-2077\mods\DesertEagle\assets\_inventory\app_json\w_handgun__tsunami_nue.app.json"
d = json.load(open(path, encoding="utf-8"))
be = d["Data"]["RootChunk"]["baseEntity"]["DepotPath"]
print("baseEntity DepotPath:", be)

# the .ent JSON has string paths — check what path the baseEntity should hold
ent_path = r"C:\Users\kluse\Projects\cyberpunk-2077\mods\DesertEagle\assets\_inventory\app_json\w_handgun__tsunami_nue__base1_01.ent.json"
e = json.load(open(ent_path, encoding="utf-8"))
print("ent RootChunk type:", e["Data"]["RootChunk"].get("$type"))


def fnv1a64(s: str) -> int:
    h = 0xCBF29CE484222325
    for ch in s.encode("utf-8"):
        h ^= ch
        h = (h * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return h


target = be.get("$value")
print("\ntarget value:", target, type(target))

candidates = [
    "base\\weapons\\firearms\\handgun\\tsunami_nue\\entities\\w_handgun__tsunami_nue__base1_01.ent",
    "base\\weapons\\firearms\\handgun\\tsunami_nue\\w_handgun__tsunami_nue__base1.ent",
    "base\\weapons\\firearms\\handgun\\tsunami_nue\\entities\\meshes\\w_handgun__tsunami_nue__base1_01.mesh",
]
for c in candidates:
    for variant in (c, c.lower()):
        h = fnv1a64(variant)
        print(f"{'MATCH ' if h == target else '      '} {h:20d}  {variant}")
