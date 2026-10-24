"""Show the texture format details and pixel data encoding of an xbm JSON."""

import base64
import json
import sys

path = sys.argv[1]
d = json.load(open(path, encoding="utf-8"))
rc = d["Data"]["RootChunk"]
tex = rc.get("Data", rc)
print("CBitmapTexture keys:", sorted(rc.keys()))
print("width/height:", rc.get("width"), rc.get("height"))
print("compression:", rc.get("compression"))

res = rc.get("renderTextureResource", {})
blob = res
for key in ("Data",):
    blob = blob.get(key, blob)
print("\nrenderTextureResource keys:", sorted(res.keys()))
inner = res
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

hdr = find(rc, "rendRenderTextureBlobHeader")
if isinstance(hdr, dict):
    print("\nheader keys:", sorted(hdr.keys()))
    for k in hdr:
        if k not in ("$type", "mipMapInfo", "sliceInfo"):
            print(f"  {k} =", json.dumps(hdr[k], default=str)[:300])
    mips = hdr.get("mipMapInfo") or []
    print(f"mipmaps: {len(mips)}")
    if mips:
        print("  mip0:", json.dumps(mips[0], default=str)[:400])

td = find(rc, "textureData")
print("\ntextureData type:", type(td))
if isinstance(td, dict):
    print("textureData keys:", sorted(td.keys()))
    for k, v in td.items():
        s = str(v)
        print(f"  {k}: {s[:80]}{'...' if len(s) > 80 else ''}")
