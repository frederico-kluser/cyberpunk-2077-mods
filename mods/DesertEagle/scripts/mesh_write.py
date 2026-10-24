"""Write the REDengine mesh render buffer from a geometry JSON.

The exact inverse of `mesh_buffer.py --dump`: takes a template `.mesh.json`
(the Tsunami Nue one — keeps materials, vertex layouts, chunk metadata) and a
geometry JSON ({chunks: [{positions, normals, tangents, uvs, skin_indices,
skin_weights, indices}]}), and rewrites:

  * quantizationScale/Offset (recomputed from the new geometry bbox),
  * the vertex region (stream 0/1/2/3 per chunk) and the index region,
  * numVertices/numIndices/byteOffsets/teOffset per chunk,
  * vertexBufferSize/indexBufferOffset/indexBufferSize,
  * renderBuffer.Bytes (base64).

Usage: python3 mesh_write.py <template.mesh.json> <geometry.json> <out.mesh.json>
"""

import base64
import json
import math
import struct
import sys

import mesh_buffer as mb

ALIGN = 16


def align16(value):
    return (value + ALIGN - 1) & ~(ALIGN - 1)


def float_to_half(value):
    return struct.unpack("<H", struct.pack("<e", value))[0]


def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


def quantize_position(p, offset, scale):
    out = []
    for a, key in enumerate("XYZ"):
        denom = scale[key] if abs(scale[key]) > 1e-12 else 1.0
        n = (p[a] - offset[key]) / denom
        out.append(int(round(clamp(n, -1.0, 1.0) * 32767.0)))
    return out


def pack_dec4(vec3, w):
    b = []
    for v in list(vec3)[:3]:
        b.append(int(round(clamp(v, -1.0, 1.0) * 127.5 + 127.5)))
    b.append(int(round(clamp(w, -1.0, 1.0) * 127.5 + 127.5)))
    return bytes(b)


def main():
    template_path, geometry_path, out_path = sys.argv[1:4]

    doc = json.load(open(template_path, encoding="utf-8"))
    rc = doc["Data"]["RootChunk"]
    blob = mb.find_render_resource(rc)
    render_buffer = mb.find_node_with_key(rc, "BufferId")
    geo = json.load(open(geometry_path, encoding="utf-8"))["chunks"]

    template_chunks = blob["renderChunkInfos"]
    if len(geo) > len(template_chunks):
        raise SystemExit(f"MESH_WRITE_FAIL geometry has {len(geo)} chunks, template only {len(template_chunks)}")
    blob["renderChunkInfos"] = template_chunks[: len(geo)]
    chunks = blob["renderChunkInfos"]

    # ---- quantization from the new bbox -------------------------------
    gmin = [1e30, 1e30, 1e30]
    gmax = [-1e30, -1e30, -1e30]
    for ch in geo:
        for p in ch["positions"]:
            for a in range(3):
                gmin[a] = min(gmin[a], p[a])
                gmax[a] = max(gmax[a], p[a])
    scale = {"W": 0}
    offset = {"W": 1}
    for a, key in enumerate("XYZ"):
        half = (gmax[a] - gmin[a]) / 2.0
        scale[key] = half if half > 1e-9 else 1.0
        offset[key] = (gmax[a] + gmin[a]) / 2.0
    blob["quantizationScale"] = {"$type": "Vector4", **scale}
    blob["quantizationOffset"] = {"$type": "Vector4", **offset}
    print(f"MESH_WRITE quant scale=({scale['X']:.6f},{scale['Y']:.6f},{scale['Z']:.6f}) offset=({offset['X']:.6f},{offset['Y']:.6f},{offset['Z']:.6f})")

    # ---- pack streams -------------------------------------------------
    vertex_blob = bytearray()
    index_blob = bytearray()
    total_v = total_i = 0

    for ci, (chunk, g) in enumerate(zip(chunks, geo)):
        nv = len(g["positions"])
        ni = len(g["indices"])
        if ni % 3 != 0:
            raise SystemExit(f"MESH_WRITE_FAIL chunk{ci}: index count {ni} not divisible by 3")
        total_v += nv
        total_i += ni

        s0 = align16(len(vertex_blob))
        stream0 = bytearray()
        for v in range(nv):
            px, py, pz = quantize_position(g["positions"][v], offset, scale)
            si = g["skin_indices"][v] if g.get("skin_indices") else [0, 0, 0, 0]
            sw = g["skin_weights"][v] if g.get("skin_weights") else [1.0, 0, 0, 0]
            stream0 += struct.pack("<4h", px, py, pz, 0)
            stream0 += struct.pack("<4B", *(int(clamp(x, 0, 255)) for x in si[:4]))
            stream0 += struct.pack("<4B", *(int(round(clamp(x, 0.0, 1.0) * 255.0)) for x in sw[:4]))
        vertex_blob += b"\x00" * (s0 - len(vertex_blob)) + stream0

        s1 = align16(len(vertex_blob))
        stream1 = bytearray()
        for v in range(nv):
            uv = g["uvs"][v] if g.get("uvs") else [0.0, 0.0]
            stream1 += struct.pack("<2e", float(uv[0]), float(uv[1]))
        vertex_blob += b"\x00" * (s1 - len(vertex_blob)) + stream1

        s2 = align16(len(vertex_blob))
        stream2 = bytearray()
        for v in range(nv):
            n = g["normals"][v] if g.get("normals") else [0.0, 0.0, 1.0]
            t = g["tangents"][v] if g.get("tangents") else [1.0, 0.0, 0.0, 1.0]
            stream2 += pack_dec4(n, 1.0)
            stream2 += pack_dec4(t[:3], t[3] if len(t) > 3 else 1.0)
        vertex_blob += b"\x00" * (s2 - len(vertex_blob)) + stream2

        s3 = align16(len(vertex_blob))
        vertex_blob += b"\x00" * (nv * 8)  # stream 3 placeholder (same shape as template)

        te = len(index_blob)
        index_blob += struct.pack(f"<{ni}H", *(int(i) for i in g["indices"]))

        chunk["numVertices"] = nv
        chunk["numIndices"] = ni
        chunk["chunkVertices"]["byteOffsets"] = {"Elements": [s0, s1, s2, s3, 0]}
        chunk["chunkIndices"]["teOffset"] = te
        print(f"MESH_WRITE chunk{ci} verts={nv} idx={ni} s0={s0} s1={s1} s2={s2} s3={s3} te={te}")

    vertex_size = align16(len(vertex_blob))
    vertex_blob += b"\x00" * (vertex_size - len(vertex_blob))
    index_offset = align16(vertex_size)
    index_size = len(index_blob)

    blob["vertexBufferSize"] = vertex_size
    blob["indexBufferOffset"] = index_offset
    blob["indexBufferSize"] = index_size
    render_buffer["Bytes"] = base64.b64encode(bytes(vertex_blob) + b"\x00" * (index_offset - vertex_size) + bytes(index_blob)).decode("ascii")

    json.dump(doc, open(out_path, "w", encoding="utf-8"), indent=1)
    print(f"MESH_WRITE totals verts={total_v} indices={total_i} vertexSize={vertex_size} indexOffset={index_offset} indexSize={index_size}")
    print(f"MESH_WRITE_OK {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
