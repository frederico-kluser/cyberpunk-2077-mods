"""Are the two mesh chunks identical copies? And what do vanilla chunks look like?"""

import json

geo = json.load(open(r"C:\Users\kluse\Projects\cyberpunk-2077\mods\DesertEagle\assets\work\de_geometry.json", encoding="utf-8"))
chunks = geo["chunks"]
print(f"our chunks: {len(chunks)}")
c0, c1 = chunks[0], chunks[1]
for k in ("positions", "indices", "uvs", "skin_indices", "skin_weights"):
    same = c0[k] == c1[k]
    print(f"  {k:14s} identical: {same}  (len {len(c0[k])})")

# vanilla mesh chunk structure for comparison
van = json.load(open(r"C:\Users\kluse\Projects\cyberpunk-2077\mods\DesertEagle\assets\_inventory\mesh_json\w_handgun__tsunami_nue__base1_01.mesh.json", encoding="utf-8"))


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


blob = find(van, "renderChunkInfos")
print(f"\nvanilla renderChunkInfos: {len(blob)} chunks")
for i, ch in enumerate(blob):
    print(f"  chunk{i}: numVertices={ch.get('numVertices')} numIndices={ch.get('numIndices')} "
          f"lod={ch.get('lod')} chunkMask={ch.get('chunkMask')}")

ours = json.load(open(r"C:\Users\kluse\Projects\cyberpunk-2077\mods\DesertEagle\assets\work\mesh_test\desert_eagle.mesh.json", encoding="utf-8"))
oblob = find(ours, "renderChunkInfos")
print(f"\nour packed renderChunkInfos: {len(oblob)} chunks")
for i, ch in enumerate(oblob):
    print(f"  chunk{i}: numVertices={ch.get('numVertices')} numIndices={ch.get('numIndices')} "
          f"lod={ch.get('lod')} chunkMask={ch.get('chunkMask')}")
