"""Write animation buffers into .anims JSON (the REDengine anim key codec).

Buffer layout (decoded from WolvenKit.RED4 CustomData/animAnimationBufferCompressed):

  animKeys       xN  [time:u16][bits:u16][x:u16][y:u16][z:u16]   quantized
  animKeysRaw    xN  [time:u16][bits:u16][x:f32][y:f32][z:f32]   raw floats
  constAnimKeys  xN  [bits:u16][time:u16][x:f32][y:f32][z:f32]   (note order!)
  trackKeys      xN  [time:u16][idx:u16][value:f32]
  constTrackKeys xN  [idx:u16][time:u16][value:f32]

  bits: wSign(bit15) | component(bits14-13) | boneIdx(bits12-0)
  component: 0=position, 1=rotation (smallest-three), 2=scale
  time = time_seconds / duration * 65535

We write the RAW variant (hasRawRotations=True): positions AND rotations as
full-precision floats in animKeysRaw; constant joints go to constAnimKeys.
No quantization error, no compressed stream — exactly what a first-party
authoring tool would emit for an uncompressed anim.
"""

from __future__ import annotations

import base64
import json
import struct

W_SIGN_SHIFT = 15
COMPONENT_SHIFT = 13
BONE_IDX_MASK = 0x1FFF


def _bits(component: int, bone_idx: int, w_sign: bool) -> int:
    return ((1 if w_sign else 0) << W_SIGN_SHIFT) | (component << COMPONENT_SHIFT) | (bone_idx & BONE_IDX_MASK)


def _pack_time(time_s: float, duration: float) -> int:
    if duration <= 0:
        return 0
    return max(0, min(65535, int(round(time_s / duration * 65535.0))))


def _rot_to_smallest_three(quat):
    """Return (x, y, z, w_sign) for a quaternion (x, y, z, w) — the engine's
    smallest-three variant (see WolvenKit FromAnimKey)."""
    x, y, z, w = quat
    w_sign = w < 0
    w_abs = -w if w_sign else w
    dot_pr = 1.0 - w_abs
    denom = math_sqrt(2.0 - dot_pr) or 1.0
    return (x / denom, y / denom, z / denom, w_sign)


def math_sqrt(v: float) -> float:
    return v ** 0.5 if v > 0 else 0.0


def build_buffer(joint_keys: dict, duration: float, is_scale_constant: bool = True) -> dict:
    """joint_keys: {bone_idx: {"position": [(t, (x,y,z)), ...],
                               "rotation": [(t, (x,y,z,w)), ...]}}
    Returns {tempBuffer bytes, counts dict}.
    """
    anim_keys_raw = bytearray()
    const_keys = bytearray()
    n_raw = 0
    n_const = 0

    for bone_idx in sorted(joint_keys):
        for component_name, component_id in (("position", 0), ("rotation", 1)):
            entries = joint_keys[bone_idx].get(component_name, [])
            if not entries:
                continue
            is_const = len(entries) == 1
            for t, value in entries:
                if component_id == 1:
                    x, y, z, w_sign = _rot_to_smallest_three(value)
                else:
                    x, y, z = value[0], value[1], value[2]
                    w_sign = False
                bits = _bits(component_id, bone_idx, w_sign)
                t_norm = _pack_time(t, duration)
                if is_const:
                    const_keys += struct.pack("<HHfff", bits, t_norm, x, y, z)
                    n_const += 1
                else:
                    anim_keys_raw += struct.pack("<HHfff", t_norm, bits, x, y, z)
                    n_raw += 1

    blob = bytes(anim_keys_raw) + bytes(const_keys)
    return {
        "blob": blob,
        "num_anim_keys": 0,
        "num_anim_keys_raw": n_raw,
        "num_const_anim_keys": n_const,
        "num_track_keys": 0,
        "num_const_track_keys": 0,
        "is_scale_constant": is_scale_constant,
        "has_raw_rotations": True,
    }


def bone_name_key(component_name: str) -> str:
    return component_name


def write_clip(anims_doc: dict, clip_name: str, joint_keys: dict, duration: float, num_frames: int) -> dict:
    """Replace one animation's buffer inside a serialized .anims JSON."""
    rc = anims_doc["Data"]["RootChunk"]
    for entry in rc.get("animations") or []:
        anim = entry["Data"]["animation"]["Data"]
        name = anim.get("name", {})
        if (name.get("$value") if isinstance(name, dict) else name) != clip_name:
            continue

        built = build_buffer(joint_keys, duration)
        # rebuild the buffer node with ONLY the fields of
        # animAnimationBufferCompressed — leftover fields from a Simd buffer
        # (quantizationBits, inplaceCompressedBuffer, ...) make the CR2W
        # converter choke
        anim["animBuffer"]["Data"] = {
            "$type": "animAnimationBufferCompressed",
            "duration": duration,
            "numFrames": num_frames,
            "numExtraJoints": 0,
            "numExtraTracks": 0,
            "numJoints": len(joint_keys),
            "numTracks": 0,
            "numAnimKeys": built["num_anim_keys"],
            "numAnimKeysRaw": built["num_anim_keys_raw"],
            "numConstAnimKeys": built["num_const_anim_keys"],
            "numTrackKeys": 0,
            "numConstTrackKeys": 0,
            "isScaleConstant": 1 if built["is_scale_constant"] else 0,
            "hasRawRotations": 1,
            "animKeys": None,
            "animKeysRaw": None,
            "constAnimKeys": None,
            "constTrackKeys": None,
            "trackKeys": None,
            "fallbackFrameIndices": [],
            "extraDataNames": [],
            "defferedBuffer": None,
            "inplaceCompressedBuffer": None,
            "dataAddress": {
                "$type": "animAnimDataAddress",
                "fsetInBytes": 0,
                "unkIndex": 0,
                "zeInBytes": len(built["blob"]),
            },
            "tempBuffer": {
                "BufferId": "1",
                "Flags": 0,
                "Bytes": base64.b64encode(built["blob"]).decode("ascii"),
            },
        }
        return {
            "clip": clip_name,
            "raw_keys": built["num_anim_keys_raw"],
            "const_keys": built["num_const_anim_keys"],
            "blob_bytes": len(built["blob"]),
        }
    raise ValueError(f"clip not found: {clip_name}")


def decode_buffer(blob: bytes, counts: dict, duration: float) -> dict:
    """Decode a buffer written by build_buffer (verification)."""
    off = 0
    out = {"raw": [], "const": []}
    for _ in range(counts["num_anim_keys_raw"]):
        t, bits, x, y, z = struct.unpack_from("<HHfff", blob, off)
        off += 16
        out["raw"].append({
            "time": t / 65535.0 * duration,
            "component": (bits >> COMPONENT_SHIFT) & 0x3,
            "bone": bits & BONE_IDX_MASK,
            "w_sign": (bits >> W_SIGN_SHIFT) & 1,
            "value": (x, y, z),
        })
    for _ in range(counts["num_const_anim_keys"]):
        bits, t, x, y, z = struct.unpack_from("<HHfff", blob, off)
        off += 16
        out["const"].append({
            "time": t / 65535.0 * duration,
            "component": (bits >> COMPONENT_SHIFT) & 0x3,
            "bone": bits & BONE_IDX_MASK,
            "w_sign": (bits >> W_SIGN_SHIFT) & 1,
            "value": (x, y, z),
        })
    return out
