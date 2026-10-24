"""Convert sampled CS2 clips (.re HDF5) into .anims JSONs via the Simd codec.

Each `.re` clip (produced by src/blender/export_re_anims.py) carries
per-bone `xformframes` (K,11) = [pos.xyz rot.xyzw scale.xyz time] in game
coordinates. The `.anims` Simd buffer wants exactly those transforms, one
frame per joint. Run with Blender's python (h5py):

  blender --background --python re_to_anims.py -- <re_root> <anims_json_root> <out_dir>

Layouts expected:
  <re_root>/<set>/<clip>.re
  <anims_json_root>/w_handgun__tsunami_nue__<set>.anims.json
"""

from __future__ import annotations

import json
import os
import sys

import h5py

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import anims_write_simd as sw  # noqa: E402

# rig joint order (w_handgun rig: parents [-1,0,1,1,1,1,1,1,1,1,5])
JOINT_ORDER = [
    "barrel_plug", "barrel", "muzzle_slot", "fx_muzzle", "weapon_trigger",
    "slide", "hammer", "slider_down", "mag_slot", "scope_slot", "pos_ironsight",
]

SETS = {
    "base1": [
        "recoil_shoulder", "first_equip", "empty_reload", "empty_reload_01",
        "empty_reload_02", "weapon_empty",
    ],
    "mag_std": [
        "first_equip", "reload", "reload_01", "reload_02",
        "empty_reload", "empty_reload_01", "empty_reload_02",
    ],
}


def load_re_clip(path: str) -> dict:
    """bone name -> (K,11) xformframes [pos.xyz rot.xyzw scale.xyz time]."""
    out = {}
    with h5py.File(path, "r") as f:
        # real layout: /.re_asset_node/.re_animation_container/.re_animation/.re_anim_clip
        group = f["/.re_asset_node/.re_animation_container/.re_animation/.re_anim_clip"]
        for bone in group.keys():
            if bone not in JOINT_ORDER:
                continue
            out[bone] = group[bone]["xformframes"][:]
    return out


def resample(rows, target_frames: int):
    """rows: (K,11) xformframes -> list of length target_frames (nearest)."""
    k = len(rows)
    if k == target_frames:
        return rows
    out = []
    for i in range(target_frames):
        j = min(k - 1, int(round(i * (k - 1) / max(1, target_frames - 1))))
        out.append(rows[j])
    return out


def to_frames_data(rows_per_bone: dict, target_frames: int) -> list:
    frames = []
    for f in range(target_frames):
        joints = []
        for bone in JOINT_ORDER:
            rows = rows_per_bone.get(bone)
            if rows is None:
                joints.append({"t": (0.0, 0.0, 0.0), "r": (0.0, 0.0, 0.0, 1.0), "s": (1.0, 1.0, 1.0)})
                continue
            row = resample(rows, target_frames)[f]
            joints.append({
                "t": (float(row[0]), float(row[1]), float(row[2])),
                "r": (float(row[3]), float(row[4]), float(row[5]), float(row[6])),
                "s": (float(row[7]), float(row[8]), float(row[9])),
            })
        frames.append(joints)
    return frames


def main():
    re_root, json_root, out_dir = sys.argv[sys.argv.index("--") + 1:][:3]
    os.makedirs(out_dir, exist_ok=True)

    for set_name, clips in SETS.items():
        anims_path = os.path.join(json_root, f"w_handgun__tsunami_nue__{set_name}.anims.json")
        doc = json.load(open(anims_path, encoding="utf-8"))

        # target frame counts / durations from the template clips
        meta = {}
        for entry in doc["Data"]["RootChunk"]["animations"]:
            anim = entry["Data"]["animation"]["Data"]
            buf = anim["animBuffer"]["Data"]
            meta[anim["name"]["$value"]] = (buf["numFrames"], buf["duration"])

        for clip in clips:
            re_path = os.path.join(re_root, set_name, f"{clip}.re")
            if not os.path.exists(re_path):
                print(f"ANIMS_SKIP {set_name}/{clip}: no .re")
                continue
            num_frames, duration = meta[clip]
            rows = load_re_clip(re_path)
            frames_data = to_frames_data(rows, num_frames)

            # dispatch by the ORIGINAL buffer type — the CR2W JSON converter
            # refuses animBuffer type swaps (proven by the isolate bisects)
            clip_type = None
            for entry in doc["Data"]["RootChunk"]["animations"]:
                anim = entry["Data"]["animation"]["Data"]
                if anim["name"]["$value"] == clip:
                    clip_type = anim["animBuffer"]["Data"]["$type"]
            if clip_type == "animAnimationBufferCompressed":
                joint_keys = {}
                for j, joint in enumerate(frames_data[0]):
                    joint_keys[j] = {
                        "position": [(0.0, tuple(joint["t"]))],
                        "rotation": [(0.0, tuple(joint["r"]))],
                    }
                import anims_write as cw
                result = cw.write_clip(doc, clip, joint_keys, duration, num_frames)
            else:
                result = sw.write_clip(doc, clip, frames_data, duration)
            print(f"ANIMS_CLIP {set_name}/{clip}: frames={num_frames} type={clip_type} -> {result}")

        out_path = os.path.join(out_dir, f"w_handgun__tsunami_nue__{set_name}.anims.json")
        json.dump(doc, open(out_path, "w", encoding="utf-8"), indent=1)
        print(f"ANIMS_SET_OK {out_path}")

    print("ANIMS_RE_DONE")


if __name__ == "__main__":
    main()
