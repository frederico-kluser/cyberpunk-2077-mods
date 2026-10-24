"""End-to-end CONTENT verification of the shipped .xbm textures.

Chain: source PNG -> Blender resize -> encode (BC5/RGBA) -> CR2W -> decode
-> compare pixels against the source. This is the only check that catches
channel-order or green-flip mistakes (wrong normals = broken lighting).

Run: blender.exe --background --python verify_xbm_content.py
"""

from __future__ import annotations

import base64
import json
import os
import subprocess
import sys

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
MOD_ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(MOD_ROOT, "scripts"))
import bcn  # noqa: E402

WK = r"C:\Users\kluse\Tools\WolvenKit\9.1.0\wolvenkit-cli.cmd"
WORK = os.path.join(MOD_ROOT, "assets", "work")
TEX = os.path.join(WORK, "cs2_textures")


def load_png(path, size):
    img = bpy.data.images.load(path)
    if img.size[0] != size or img.size[1] != size:
        img.scale(size, size)
    w, h = img.size
    px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
    out = np.clip(px * 255.0 + 0.5, 0, 255).astype(np.uint8)
    bpy.data.images.remove(img)
    return out


def texture_data(xbm_json):
    doc = json.load(open(xbm_json, encoding="utf-8"))
    rc = doc["Data"]["RootChunk"]

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
    hdr = find(rc, "rendRenderTextureBlobHeader")
    mips = hdr.get("mipMapInfo") or []
    pl = find(mips[0], "rendRenderTextureBlobPlacement")
    return base64.b64decode(td["Bytes"]), pl["offset"], pl["size"]


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    verify_dir = os.path.join(WORK, "xbms", "verify")
    results = []

    # --- color map (RGBA) ---
    blob, off, size = texture_data(os.path.join(verify_dir, "desert_eagle_bc.xbm.json"))
    got = np.frombuffer(blob[off:off + size], dtype=np.uint8).reshape(1024, 1024, 4)
    src = load_png(os.path.join(TEX, "texture_00.png"), 1024)
    err = np.abs(got.astype(np.int32) - src.astype(np.int32)).mean()
    ok = err < 1.0
    results.append(ok)
    print(f"[{'OK' if ok else 'FAIL'}] color map: mean abs err = {err:.3f}/255 (exact RGBA copy expected)")

    # --- normal map (BC5, green flipped on encode) ---
    blob, off, size = texture_data(os.path.join(verify_dir, "desert_eagle_n.xbm.json"))
    data = blob[off:off + size]
    rg = bcn.decode_bc5(data, 1024, 1024)
    src = load_png(os.path.join(TEX, "texture_01.png"), 1024)
    src_rg = src[:, :, :2].copy()
    src_rg[:, :, 1] = 255 - src_rg[:, :, 1]  # the flip applied on encode
    err = np.abs(rg.astype(np.int32) - src_rg.astype(np.int32)).mean()
    ok = err < 12.0  # BC5 is lossy but should track the source closely
    results.append(ok)
    print(f"[{'OK' if ok else 'FAIL'}] normal map (BC5): mean abs err = {err:.3f}/255 vs green-flipped source")

    # sanity: WITHOUT the flip the error must be much larger (flip is real)
    err_noflip = np.abs(rg.astype(np.int32) - src[:, :, :2].astype(np.int32)).mean()
    print(f"       (green channel check: err without flip = {err_noflip:.3f} — must be >> flipped err)")

    ok_all = all(results) and err_noflip > err * 3
    print("XBM_CONTENT_VERIFY_OK" if ok_all else "XBM_CONTENT_VERIFY_FAIL")
    return 0 if ok_all else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception:
        import traceback

        traceback.print_exc()
        print("XBM_CONTENT_VERIFY_FAIL", flush=True)
        raise SystemExit(1)
