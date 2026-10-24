"""Decode the REDengine mesh render buffer (the geometry side of .mesh).

Layout (decoded from `w_handgun__tsunami_nue__base1_01.mesh.json`):

  renderBuffer.Bytes (base64) =
    [vertex region .. vertexBufferSize)
      per chunk, per stream, all vertices of the stream contiguous:
        stream 0 (16 B/vert): PS_Position  PT_Short4N  (x,y,z,w int16 normalized)
                             PS_SkinIndices PT_UByte4  (4 bone indices)
                             PS_SkinWeights PT_UByte4N (4 weights 0..255)
        stream 1 (4 B/vert):  PS_TexCoord   PT_Float16_2 (uv0)
        stream 2 (8 B/vert):  PS_Normal     PT_Dec4     (packed xyzw)
                             PS_Tangent     PT_Dec4
        stream 3 (8 B/vert):  extra (color/uv1 per vertex layout)
    [index region .. indexBufferOffset + indexBufferSize)
      uint16 triangles; each chunk has teOffset within this region.

Position decode:  p = (int16 / 32767) * quantizationScale + quantizationOffset
(meters; the weapon is ~0.25 m long).

Usage: python3 mesh_buffer.py <mesh.json>
"""

import base64
import json
import struct
import sys


def load_mesh(path):
    d = json.load(open(path, encoding="utf-8"))
    return d["Data"]["RootChunk"]


def find_node_with_key(node, key):
    if isinstance(node, dict):
        if key in node and "Bytes" in node:
            return node
        for v in node.values():
            found = find_node_with_key(v, key)
            if found is not None:
                return found
    elif isinstance(node, list):
        for v in node:
            found = find_node_with_key(v, key)
            if found is not None:
                return found
    return None


def find_render_resource(node):
    if isinstance(node, dict):
        if "quantizationOffset" in node:
            return node
        for v in node.values():
            found = find_render_resource(v)
            if found is not None:
                return found
    elif isinstance(node, list):
        for v in node:
            found = find_render_resource(v)
            if found is not None:
                return found
    return None


def main():
    path = sys.argv[1]
    rc = load_mesh(path)
    blob = find_render_resource(rc)
    if blob is None:
        print("MESHBUF_FAIL no rendRenderMeshBlob")
        return 1

    render_buffer = find_node_with_key(rc, "BufferId")
    buf_b64 = render_buffer["Bytes"]
    raw = base64.b64decode(buf_b64)
    qoff = blob["quantizationOffset"]
    qscl = blob["quantizationScale"]
    ib_off = blob["indexBufferOffset"]
    ib_size = blob["indexBufferSize"]
    vb_size = blob["vertexBufferSize"]
    print(f"MESHBUF buffer={len(raw)}B vertexRegion=0..{vb_size} indexRegion={ib_off}..{ib_off+ib_size}")
    print(f"MESHBUF quant offset=({qoff['X']:.6f},{qoff['Y']:.6f},{qoff['Z']:.6f}) scale=({qscl['X']:.6f},{qscl['Y']:.6f},{qscl['Z']:.6f})")

    total_v = 0
    total_i = 0
    gmin = [1e9, 1e9, 1e9]
    gmax = [-1e9, -1e9, -1e9]

    for ci, chunk in enumerate(blob["renderChunkInfos"]):
        nv = chunk["numVertices"]
        ni = chunk["numIndices"]
        total_v += nv
        total_i += ni
        offsets = chunk["chunkVertices"]["byteOffsets"]["Elements"]
        s0 = offsets[0]
        te = chunk["chunkIndices"]["teOffset"]
        pe = chunk["chunkIndices"]["pe"]

        # positions: 16-byte stride, first 8 bytes = 4x int16
        pmin = [1e9, 1e9, 1e9]
        pmax = [-1e9, -1e9, -1e9]
        for v in range(nv):
            base = s0 + v * 16
            x, y, z, _w = struct.unpack_from("<4h", raw, base)
            px = x / 32767.0 * qscl["X"] + qoff["X"]
            py = y / 32767.0 * qscl["Y"] + qoff["Y"]
            pz = z / 32767.0 * qscl["Z"] + qoff["Z"]
            for a, val in enumerate((px, py, pz)):
                pmin[a] = min(pmin[a], val)
                pmax[a] = max(pmax[a], val)
                gmin[a] = min(gmin[a], val)
                gmax[a] = max(gmax[a], val)

        # indices: uint16 at ib region
        first = struct.unpack_from("<H", raw, ib_off + te)[0]
        last = struct.unpack_from("<H", raw, ib_off + te + (ni - 1) * 2)[0]
        valid = first < nv and last < nv

        print(
            f"MESHBUF chunk{ci} verts={nv} idx={ni} ({pe}) "
            f"s0={s0} te={te} "
            f"bbox=({pmin[0]:.3f},{pmin[1]:.3f},{pmin[2]:.3f})..({pmax[0]:.3f},{pmax[1]:.3f},{pmax[2]:.3f}) "
            f"idx_range={first}..{last} valid={valid}"
        )

    size = [gmax[a] - gmin[a] for a in range(3)]
    print(f"MESHBUF TOTAL verts={total_v} indices={total_i}")
    print(f"MESHBUF GLOBAL bbox=({gmin[0]:.4f},{gmin[1]:.4f},{gmin[2]:.4f})..({gmax[0]:.4f},{gmax[1]:.4f},{gmax[2]:.4f}) size=({size[0]:.4f},{size[1]:.4f},{size[2]:.4f})")
    print("MESHBUF_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
