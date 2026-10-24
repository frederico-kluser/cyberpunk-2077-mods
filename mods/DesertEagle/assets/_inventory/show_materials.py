"""Print the material instances of the Nue mesh JSON (baseMaterial + values)."""

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
print(f"materials: {len(mats)}")
for i, m in enumerate(mats):
    cd = m.get("Data", m)
    base = find(cd, "baseMaterial")
    bpath = base.get("DepotPath", {}).get("$value") if isinstance(base, dict) else None
    vals = cd.get("values") or []
    print(f"\n[{i}] type={cd.get('$type')} base={bpath}")
    for v in vals[:14]:
        vd = v.get("Data", v) if isinstance(v, dict) else {}
        name = vd.get("key") or vd.get("name") or vd.get("property")
        val = vd.get("value")
        val = val.get("$value") if isinstance(val, dict) else val
        if isinstance(val, str) and len(val) > 70:
            val = val[:67] + "..."
        print(f"    {name} = {val}")
    if len(vals) > 14:
        print(f"    ... +{len(vals)-14} values")

entries = find(rc, "materialEntries") or []
print(f"\nmaterialEntries: {len(entries)}")
for e in entries[:6]:
    n = e.get("name", {})
    print(f"  idx={e.get('index')} name={n.get('$value') if isinstance(n, dict) else n}")
