"""Extract embedded textures from a GLB (binary glTF) container.

GLB layout: 12-byte header + chunks (JSON + BIN). Images live in the BIN
buffer as bufferViews (PNG/JPEG bytes) referenced by glTF.images.

Usage: python3 glb_textures.py <model.glb> <out_dir>
"""

import json
import os
import struct
import sys


def main():
    glb, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    raw = open(glb, "rb").read()

    magic, version, length = struct.unpack_from("<III", raw, 0)
    assert magic == 0x46546C67, "not a GLB"
    off = 12
    gltf = None
    binblob = b""
    while off < length:
        clen, ctype = struct.unpack_from("<II", raw, off)
        off += 8
        chunk = raw[off:off + clen]
        off += clen
        if ctype == 0x4E4F534A:
            gltf = json.loads(chunk.decode("utf-8"))
        elif ctype == 0x004E4942:
            binblob = chunk

    images = gltf.get("images") or []
    views = gltf.get("bufferViews") or []
    print(f"GLB_TEXT images={len(images)} bin={len(binblob)} bytes")
    for i, img in enumerate(images):
        if "bufferView" not in img:
            print(f"  [{i}] uri-embedded (skipped): {img.get('uri')}")
            continue
        v = views[img["bufferView"]]
        start = v.get("byteOffset", 0)
        data = binblob[start:start + v["byteLength"]]
        mime = img.get("mimeType", "image/png")
        ext = "png" if "png" in mime else "jpg" if "jp" in mime else "bin"
        name = img.get("name") or f"texture_{i:02d}"
        path = os.path.join(out, f"{name}.{ext}")
        open(path, "wb").write(data)
        print(f"  [{i}] {path}  {len(data)} bytes  {mime}")
    print("GLB_TEXT_OK")


if __name__ == "__main__":
    main()
