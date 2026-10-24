"""Read/write `animAnimationBufferSimd` buffers (the REDengine SIMD codec).

Binary layout (decoded from WolvenKit.Modkit/RED4/Tools/Animation/AnimSIMD.cs —
this module is its exact Python inverse):

  1. Rotations, per frame, per SIMD block of 4 joints:
       quantized (quantizationBits>0): bit-packed smallest-three x',y',z'
         totalFloatCount = ((frames * jointsAligned * 3) + 3) & ~3
         stream size     = (totalFloatCount * bits / 8 + 15) & ~15   (16-aligned)
         value v in [-1,1] -> packed = round((v+1)/2 * mask), bit offset i*bits
         decode: x*=sqrt(2-dotPr), w = 1-dotPr, then normalize
       else: floats xs[4], ys[4], zs[4], ws[4] per block
  2. Eval translations: frames * evalAligned * 3 floats (blocks of 4: x[4],y[4],z[4])
  3. Scales: isScaleConstant -> 4 floats; else frames*jointsAligned*3 floats
  4. Tracks: isTrackConstant -> 1 float; else per frame numTracks floats + pad to 4
  5. Copy translations: numToCopy * 3 floats  (static-translation joints)
  6. Copy indices: numToCopy * int16
  7. Eval indices: evalAligned * int16  (padding slots = -1)

jointsAligned = (numJoints - numExtraJoints + 3) & ~3. Coordinates here are
GAME coordinates (no glTF flips — those exist only in WolvenKit's exporter).
"""

from __future__ import annotations

import base64
import json
import math
import struct

SIMD = 4


def _align4(n: int) -> int:
    return (n + 3) & ~3


def _to_smallest_three(q):
    """Unit quaternion (x,y,z,w) -> (x',y',z') for the Simd variant. The sign
    is flipped so w >= 0 (the format stores no w sign)."""
    x, y, z, w = q
    n = math.sqrt(x * x + y * y + z * z + w * w) or 1.0
    x, y, z, w = x / n, y / n, z / n, w / n
    if w < 0:
        x, y, z, w = -x, -y, -z, -w
    d = 1.0 - w
    scale = math.sqrt(2.0 - d) or 1.0
    return (x / scale, y / scale, z / scale)


def _from_smallest_three(xp, yp, zp):
    dot = xp * xp + yp * yp + zp * zp
    f = math.sqrt(2.0 - dot)
    x, y, z, w = xp * f, yp * f, zp * f, 1.0 - dot
    n = math.sqrt(x * x + y * y + z * z + w * w) or 1.0
    return (x / n, y / n, z / n, w / n)


def decode_simd(blob: bytes, hdr: dict) -> dict:
    """Decode a Simd buffer -> {'frames': [[(px,py,pz),(rx,ry,rz,rw)], ...] per joint]}.

    hdr keys: numFrames, numJoints, numExtraJoints, duration, isScaleConstant,
              isTrackConstant, numTranslationsToCopy,
              numTranslationsToEvalAlignedToSimd, quantizationBits, numTracks.
    """
    frames = hdr["numFrames"]
    joints = hdr["numJoints"]
    extra = hdr["numExtraJoints"]
    joints_aligned = _align4(joints - extra)
    to_copy = hdr["numTranslationsToCopy"]
    to_eval = hdr["numTranslationsToEvalAlignedToSimd"]
    bits = hdr["quantizationBits"]

    pos = 0
    # --- rotations ---------------------------------------------------------
    rot = [[[0.0, 0.0, 0.0, 1.0] for _ in range(joints)] for _ in range(frames)]
    if bits:
        total_floats = _align4(frames * joints_aligned * 3)
        mask = (1 << bits) - 1
        bit_stream = int.from_bytes(blob[: (total_floats * bits + 7) // 8 + 4], "little")
        dec = []
        for i in range(total_floats):
            dec.append(((bit_stream >> (i * bits)) & mask) / mask * 2.0 - 1.0)
        size = (total_floats * bits // 8 + 15) & ~15
        pos = size
        for f in range(frames):
            for j in range(0, joints_aligned, SIMD):
                for b in range(SIMD):
                    base = f * joints_aligned * 3 + j * 3 + b
                    xp, yp, zp = dec[base], dec[base + 4], dec[base + 8]
                    if j + b < joints:
                        rot[f][j + b] = list(_from_smallest_three(xp, yp, zp))
    else:
        for f in range(frames):
            for j in range(0, joints_aligned, SIMD):
                xs = struct.unpack_from("<4f", blob, pos); pos += 16
                ys = struct.unpack_from("<4f", blob, pos); pos += 16
                zs = struct.unpack_from("<4f", blob, pos); pos += 16
                ws = struct.unpack_from("<4f", blob, pos); pos += 16
                for b in range(min(SIMD, joints - j)):
                    rot[f][j + b] = [xs[b], ys[b], zs[b], ws[b]]

    # --- eval translations -------------------------------------------------
    eval_pos = struct.unpack_from(f"<{frames * to_eval * 3}f", blob, pos)
    pos += frames * to_eval * 3 * 4
    eval_slots = [{} for _ in range(frames)]
    for f in range(frames):
        for e in range(0, to_eval, SIMD):
            for b in range(SIMD):
                base = f * to_eval * 3 + e * 3 + b
                v = (eval_pos[base], eval_pos[base + 4], eval_pos[base + 8])
                eval_slots[f][e + b] = list(v)  # slot -> resolved via eval indices

    # --- scales ------------------------------------------------------------
    scales = [1.0, 1.0, 1.0]
    if hdr["isScaleConstant"]:
        scales = list(struct.unpack_from("<4f", blob, pos))[:3]
        pos += 16
    else:
        pos += frames * joints_aligned * 3 * 4  # skipped: we only write constant

    # --- tracks ------------------------------------------------------------
    pos += 4 if (hdr["numTracks"] > 0 and hdr["isTrackConstant"]) else 0

    # --- copy translations + indices --------------------------------------
    copies = [struct.unpack_from("<3f", blob, pos + 12 * i) for i in range(to_copy)]
    pos += 12 * to_copy
    copy_idx = list(struct.unpack_from(f"<{to_copy}h", blob, pos)) if to_copy else []
    pos += 2 * to_copy
    eval_idx = list(struct.unpack_from(f"<{to_eval}h", blob, pos)) if to_eval else []

    # resolve slot keys -> joint indices
    trans = [{} for _ in range(frames)]
    for f in range(frames):
        for slot in range(to_eval):
            j = eval_idx[slot] if slot < len(eval_idx) else -1
            if 0 <= j < joints:
                trans[f][j] = eval_slots[f].get(slot, [0.0, 0.0, 0.0])
        for i, j in enumerate(copy_idx):
            if 0 <= j < joints:
                trans[f][j] = list(copies[i])
        for j in range(joints):
            trans[f].setdefault(j, [0.0, 0.0, 0.0])

    out_frames = []
    for f in range(frames):
        out_frames.append([
            {"t": trans[f][j], "r": rot[f][j], "s": scales}
            for j in range(joints)
        ])
    return {"frames": out_frames, "duration": hdr["duration"], "numFrames": frames}


def encode_simd(frames_data: list, duration: float, quantization_bits: int = 12) -> dict:
    """frames_data: [[{'t': (x,y,z), 'r': (x,y,z,w)}, ... per joint], ... per frame]

    Returns {'blob': bytes, 'header': fields for the Simd node}.
    """
    num_frames = len(frames_data)
    joints = len(frames_data[0])
    joints_aligned = _align4(joints)

    # classify translations: static (copy) vs dynamic (eval)
    static, dynamic = [], []
    for j in range(joints):
        first = frames_data[0][j]["t"]
        is_static = all(
            all(abs(frames_data[f][j]["t"][c] - first[c]) < 1e-4 for c in range(3))
            for f in range(num_frames)
        )
        (static if is_static else dynamic).append(j)
    to_copy = len(static)
    to_eval = _align4(len(dynamic))

    out = bytearray()

    # --- 1. rotations (quantized smallest-three) ---------------------------
    total_floats = _align4(num_frames * joints_aligned * 3)
    mask = (1 << quantization_bits) - 1
    bit_stream = 0
    for f in range(num_frames):
        for j in range(0, joints_aligned, SIMD):
            for b in range(SIMD):
                idx = j + b
                q = frames_data[f][idx]["r"] if idx < joints else (0.0, 0.0, 0.0, 1.0)
                xp, yp, zp = _to_smallest_three(q)
                for comp, v in zip((0, 1, 2), (xp, yp, zp)):
                    i = f * joints_aligned * 3 + j * 3 + comp * SIMD + b
                    packed = int(round((max(-1.0, min(1.0, v)) + 1.0) / 2.0 * mask))
                    bit_stream |= (packed & mask) << (i * quantization_bits)
    stream_bytes = (total_floats * quantization_bits + 7) // 8
    size = (total_floats * quantization_bits // 8 + 15) & ~15
    out += bit_stream.to_bytes(stream_bytes, "little")
    out += b"\x00" * (size - stream_bytes)

    # --- 2. eval translations (dynamic joints, block-interleaved) ---------
    for f in range(num_frames):
        for e in range(0, to_eval, SIMD):
            for comp in range(3):
                for b in range(SIMD):
                    slot = e + b
                    j = dynamic[slot] if slot < len(dynamic) else None
                    v = frames_data[f][j]["t"][comp] if j is not None else 0.0
                    out += struct.pack("<f", v)

    # --- 3. scales (constant) ---------------------------------------------
    out += struct.pack("<4f", 1.0, 1.0, 1.0, 0.0)

    # --- 4. tracks (none) --------------------------------------------------

    # --- 5. copy translations ---------------------------------------------
    for j in static:
        out += struct.pack("<3f", *frames_data[0][j]["t"])

    # --- 6. copy indices --------------------------------------------------
    for j in static:
        out += struct.pack("<h", j)

    # --- 7. eval indices --------------------------------------------------
    for slot in range(to_eval):
        out += struct.pack("<h", dynamic[slot] if slot < len(dynamic) else -1)

    return {
        "blob": bytes(out),
        "header": {
            "duration": duration,
            "numFrames": num_frames,
            "numJoints": joints,
            "numExtraJoints": 0,
            "numExtraTracks": 0,
            "numTracks": 0,
            "isScaleConstant": 1,
            "isTrackConstant": 0,
            "numTranslationsToCopy": to_copy,
            "numTranslationsToEvalAlignedToSimd": to_eval,
            "quantizationBits": quantization_bits,
        },
    }


def _next_buffer_id(anims_doc: dict) -> int:
    """Pick a BufferId not used by any inplace/temp/deferred buffer in the file."""
    used = set()

    def visit(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if k in ("inplaceCompressedBuffer", "tempBuffer", "defferedBuffer",
                         "fallbackAnimDataBuffer") and isinstance(v, dict):
                    used.add(str(v.get("BufferId")))
                visit(v)
        elif isinstance(node, list):
            for v in node:
                visit(v)

    visit(anims_doc["Data"]["RootChunk"])
    n = 2
    while str(n) in used:
        n += 1
    return n


def write_clip(anims_doc: dict, clip_name: str, frames_data: list, duration: float,
               quantization_bits: int = 12) -> dict:
    """Replace one clip's Simd buffer (SAME TYPE — the JSON converter cannot
    switch animBuffer types) with our data."""
    rc = anims_doc["Data"]["RootChunk"]
    for entry in rc.get("animations") or []:
        anim = entry["Data"]["animation"]["Data"]
        name = anim.get("name", {})
        if (name.get("$value") if isinstance(name, dict) else name) != clip_name:
            continue

        built = encode_simd(frames_data, duration, quantization_bits)
        h = built["header"]
        node = anim["animBuffer"]["Data"]
        node["$type"] = "animAnimationBufferSimd"
        node["duration"] = h["duration"]
        node["numFrames"] = h["numFrames"]
        node["numJoints"] = h["numJoints"]
        node["numExtraJoints"] = h["numExtraJoints"]
        node["numExtraTracks"] = h["numExtraTracks"]
        node["numTracks"] = h["numTracks"]
        node["isScaleConstant"] = h["isScaleConstant"]
        node["isTrackConstant"] = h["isTrackConstant"]
        node["numTranslationsToCopy"] = h["numTranslationsToCopy"]
        node["numTranslationsToEvalAlignedToSimd"] = h["numTranslationsToEvalAlignedToSimd"]
        node["quantizationBits"] = h["quantizationBits"]
        node["fallbackFrameIndices"] = []
        node["extraDataNames"] = []
        node["defferedBuffer"] = None
        node["dataAddress"] = {
            "$type": "animAnimDataAddress",
            "fsetInBytes": 4294967295,
            "unkIndex": 4294967295,
            "zeInBytes": 4294967295,
        }
        node["inplaceCompressedBuffer"] = {
            # BufferId must be unique across the file (vanilla ids: 1, 2, ...)
            "BufferId": str(_next_buffer_id(anims_doc)),
            "Flags": 7471104,
            "Bytes": base64.b64encode(built["blob"]).decode("ascii"),
        }
        return {"clip": clip_name, "blob_bytes": len(built["blob"]),
                "copy": h["numTranslationsToCopy"], "eval": h["numTranslationsToEvalAlignedToSimd"]}
    raise ValueError(f"clip not found: {clip_name}")
