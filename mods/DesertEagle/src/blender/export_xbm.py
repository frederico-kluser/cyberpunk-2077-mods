"""Build .xbm texture JSONs from PNG maps (CS2 -> Cyberpunk 2077).

Formats (decoded in docs/PIPELINE.md):
  color  : RGBA8 raw      (rowPitch = width*4)   <- template w_tsunami_decal_01_d01.xbm
  normal : BC5 blocks     (rowPitch = blocks_x*16, green channel flipped)

Runs inside Blender (bpy decodes/resizes the PNGs; numpy does the rest):

  blender --background --python export_xbm.py -- <out_dir> \
      color:<png> <template.xbm.json> <name> \
      normal:<png> <template.xbm.json> <name> ...
"""

from __future__ import annotations

import base64
import json
import os
import sys

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scripts"))
import bcn  # noqa: E402


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


def load_png(path, size):
    """Load a PNG via Blender and return an (size,size,4) uint8 RGBA array."""
    img = bpy.data.images.load(path)
    if img.size[0] != size or img.size[1] != size:
        img.scale(size, size)
    w, h = img.size
    px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
    out = np.clip(px * 255.0 + 0.5, 0, 255).astype(np.uint8)
    bpy.data.images.remove(img)
    return out


def mips_of(rgba):
    """Box-filter mip chain down to 1x1 (vectorized)."""
    mips = [rgba]
    cur = rgba
    while cur.shape[0] > 1 or cur.shape[1] > 1:
        h, w = cur.shape[0], cur.shape[1]
        nh, nw = max(1, h // 2), max(1, w // 2)
        if h % 2 == 0 and w % 2 == 0 and h > 1 and w > 1:
            nxt = cur.reshape(nh, 2, nw, 2, 4).mean(axis=(1, 3)).astype(np.uint8)
        else:
            nxt = np.zeros((nh, nw, 4), dtype=np.uint8)
            for y in range(nh):
                for x in range(nw):
                    blk = cur[y * 2:y * 2 + 2, x * 2:x * 2 + 2].reshape(-1, 4)
                    nxt[y, x] = blk.mean(axis=0).astype(np.uint8)
        mips.append(nxt)
        cur = nxt
    return mips


def encode_mips(kind, mips):
    """Return (rows, blob) where rows = per-mip dict with offsets/pitch/size."""
    blob = bytearray()
    rows = []
    for m in mips:
        h, w = m.shape[0], m.shape[1]
        offset = len(blob)
        if kind == "color":
            data = m.tobytes()
            row_pitch = w * 4
        elif kind == "normal":
            rg = m[:, :, :2].copy()
            rg[:, :, 1] = 255 - rg[:, :, 1]  # OpenGL -> DirectX green flip
            data = bcn.encode_bc5(rg)
            row_pitch = max(1, w // 4) * 16
        else:
            raise ValueError(f"unknown kind {kind}")
        blob += data
        rows.append({
            "width": w, "height": h, "offset": offset,
            "size": len(data), "rowPitch": row_pitch,
            "slicePitch": len(data),
        })
    return rows, bytes(blob)


def build_xbm(template_path, out_path, kind, png, name, size=1024):
    doc = json.load(open(template_path, encoding="utf-8"))
    rc = doc["Data"]["RootChunk"]

    rgba = load_png(png, size)
    mips = mips_of(rgba)
    rows, blob = encode_mips(kind, mips)

    rc["width"] = size
    rc["height"] = size

    size_info = find(rc, "rendRenderTextureBlobSizeInfo")
    size_info["width"] = size
    size_info["height"] = size

    tex_info = find(rc, "rendRenderTextureBlobTextureInfo")
    tex_info["mipCount"] = len(rows)
    tex_info["sliceSize"] = len(blob)
    tex_info["textureDataSize"] = len(blob)

    header = find(rc, "rendRenderTextureBlobHeader")
    old_mips = header.get("mipMapInfo") or []
    template_item = json.loads(json.dumps(old_mips[0]))
    new_mips = []
    for r in rows:
        item = json.loads(json.dumps(template_item))
        ml = find(item, "rendRenderTextureBlobMemoryLayout")
        pl = find(item, "rendRenderTextureBlobPlacement")
        ml["rowPitch"] = r["rowPitch"]
        ml["slicePitch"] = r["slicePitch"]
        pl["offset"] = r["offset"]
        pl["size"] = r["size"]
        new_mips.append(item)
    header["mipMapInfo"] = new_mips

    td = find(rc, "textureData")
    td["Bytes"] = base64.b64encode(blob).decode("ascii")

    json.dump(doc, open(out_path, "w", encoding="utf-8"), indent=1)
    print(f"XBM_OK {out_path} kind={kind} size={size} mips={len(rows)} bytes={len(blob)}")


def main():
    out_dir = sys.argv[sys.argv.index("--") + 1]
    args = sys.argv[sys.argv.index("--") + 2:]
    os.makedirs(out_dir, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for i in range(0, len(args), 4):
        kind_png, template, name = args[i], args[i + 1], args[i + 2]
        size = int(args[i + 3])
        kind, png = kind_png.split(":", 1)
        build_xbm(template, os.path.join(out_dir, f"{name}.xbm.json"), kind, png, name, size)
    print("XBM_DONE")


if __name__ == "__main__":
    main()
