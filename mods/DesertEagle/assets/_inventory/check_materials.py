"""Compare chunk materialId / materialEntries: ours vs the vanilla Nue mesh."""

import json


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


def survey(path, label):
    d = json.load(open(path, encoding="utf-8"))
    rc = d["Data"]["RootChunk"]
    print(f"\n== {label} ==")
    entries = find(rc, "materialEntries") or []
    print(f"materialEntries: {len(entries)}")
    for i, e in enumerate(entries[:6]):
        n = e.get("name", {})
        n = n.get("$value") if isinstance(n, dict) else n
        isd = e.get("isDepotPath")
        print(f"  [{i}] name={n} index={e.get('index')} isDepotPath={isd}")
    chunks = find(rc, "renderChunkInfos") or []
    print(f"renderChunkInfos: {len(chunks)}")
    for i, ch in enumerate(chunks):
        print(f"  chunk{i}: materialId={ch.get('materialId')} numLods={ch.get('numLods')} "
              f"numVertices={ch.get('numVertices')}")
    buf = find(rc, "localMaterialBuffer") or {}
    mats = buf.get("materials") or []
    print(f"localMaterialBuffer.materials: {len(mats)}")
    for i, m in enumerate(mats[:4]):
        cd = m.get("Data", m)
        base = find(cd, "baseMaterial")
        bpath = base.get("DepotPath", {}).get("$value") if isinstance(base, dict) else None
        print(f"  [{i}] base={bpath}")


survey(r"C:\Users\kluse\Projects\cyberpunk-2077\mods\DesertEagle\assets\_inventory\mesh_json\w_handgun__tsunami_nue__base1_01.mesh.json", "VANILLA NUE")
survey(r"C:\Users\kluse\Projects\cyberpunk-2077\mods\DesertEagle\assets\work\mesh_test\desert_eagle.mesh.json", "OURS")
