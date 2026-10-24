"""Measure the pixel buffer and print mip layout / texture info of an xbm."""

import base64
import json
import sys

path = sys.argv[1]
d = json.load(open(path, encoding="utf-8"))
rc = d["Data"]["RootChunk"]


def find(node, key):
    if isinstance(node, dict):
        if key in node or node.get("$type") == key:
            return node if node.get("$type") == key else node[key]
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


td = find(rc, "textureData")
raw = base64.b64decode(td["Bytes"])
print(f"textureData bytes={len(raw)}")

hdr = find(rc, "rendRenderTextureBlobHeader")
for key in ("rendRenderTextureBlobTextureInfo", "rendRenderTextureBlobSizeInfo"):
    info = find(rc, key)
    if isinstance(info, dict):
        print(f"{key}:", json.dumps({k: v for k, v in info.items() if k != '$type'}, default=str))

mips = hdr.get("mipMapInfo") or []
print(f"mipmaps: {len(mips)}")
for i, m in enumerate(mips[:4]):
    ml = find(m, "rendRenderTextureBlobMemoryLayout") or {}
    pl = find(m, "rendRenderTextureBlobPlacement") or {}
    print(f"  mip{i}: layout={json.dumps(ml, default=str)[:160]}")
    print(f"         placement={json.dumps(pl, default=str)[:160]}")

setup = rc.get("setup", {})
print("setup:", json.dumps(setup, default=str)[:300])
