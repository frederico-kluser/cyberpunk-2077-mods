"""Export calibrated .re animsets: CS2 motion retimed onto the Nue rig.

The .re xformframes store each bone's LOCAL (parent-relative) transform per
frame. We write:

    out_local(t) = nue_rest_local  @  (cs2_rest_local^-1 @ cs2_local(t))

i.e. the CS2 *motion delta* expressed in the Nue rest space — the design rule
is "Nue rest pose, CS2 motion", so parts never drift from the .rig rest.

Run:
  blender.exe --background --python export_re_anims.py -- <out_dir>
"""

from __future__ import annotations

import json
import os
import sys

import bpy
from mathutils import Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from de_pipeline import re_export  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
MOD_ROOT = os.path.dirname(os.path.dirname(HERE))
MODEL = os.path.join(MOD_ROOT, "assets", "raw", "desert_eagle_cs2.glb")
RIG_JSON = os.path.join(MOD_ROOT, "assets", "_inventory", "nue_rig.json")

# source CS2 bone -> Nue .rig bone
BONE_MAP = {
    "GLTF_created_0_rootJoint": "barrel_plug",
    "weapon_hand_r_4": "barrel",
    "v_weapon_deagle_slide_0": "slide",
    "v_weapon_deagle_trigger_1": "weapon_trigger",
    "v_weapon_deagle_clip_2": "mag_slot",
    "v_weapon_deagle_hammer_3": "hammer",
}

# target animset -> {anim name: (CS2 action, source frames, target frames)}
# The two Nue sets use overlapping names, and the .re filename IS the internal
# anim name, so each set exports into its own folder.
SETS = {
    "base1": {
        "recoil_shoulder": ("firstperson_shoot1", 16, 11),
        "first_equip": ("firstperson_draw", 24, 90),
        "empty_reload": ("firstperson_reload", 52, 101),
        "empty_reload_01": ("firstperson_reload", 52, 101),
        "empty_reload_02": ("firstperson_reload", 52, 101),
        "weapon_empty": ("firstperson_idle", 0, 2),
    },
    "mag_std": {
        "first_equip": ("firstperson_draw", 24, 108),
        "reload": ("firstperson_reload", 52, 81),
        "reload_01": ("firstperson_reload", 52, 81),
        "reload_02": ("firstperson_reload", 52, 81),
        "empty_reload": ("firstperson_reload", 52, 101),
        "empty_reload_01": ("firstperson_reload", 52, 101),
        "empty_reload_02": ("firstperson_reload", 52, 101),
    },
}


def local_matrix(arm, pb):
    """Pose-bone transform relative to its parent (armature space based)."""
    if pb.parent is None:
        return pb.matrix.copy()
    return pb.parent.matrix.inverted() @ pb.matrix


def rest_local_matrix(pb):
    if pb.parent is None:
        return pb.bone.matrix_local.copy()
    return pb.parent.bone.matrix_local.inverted() @ pb.bone.matrix_local


def nue_rest_locals(bones):
    out = {}
    for b in bones:
        t = Matrix.Translation(b["pos"])
        r = b["quat"]  # x,y,z,w
        rot = Matrix((  # 3x3 from quaternion
            (1 - 2 * (r[1] ** 2 + r[2] ** 2), 2 * (r[0] * r[1] - r[2] * r[3]), 2 * (r[0] * r[2] + r[1] * r[3])),
            (2 * (r[0] * r[1] + r[2] * r[3]), 1 - 2 * (r[0] ** 2 + r[2] ** 2), 2 * (r[1] * r[2] - r[0] * r[3])),
            (2 * (r[0] * r[2] - r[1] * r[3]), 2 * (r[1] * r[2] + r[0] * r[3]), 1 - 2 * (r[0] ** 2 + r[1] ** 2)),
        )).to_4x4()
        s = Matrix.Diagonal((*b["scale"], 1.0))
        out[b["name"]] = t @ rot @ s
    return out


def matrix_to_row(m: Matrix, time: float) -> tuple:
    loc, quat, scale = m.decompose()
    return (
        loc.x, loc.y, loc.z,
        quat.x, quat.y, quat.z, quat.w,
        scale.x, scale.y, scale.z,
        time,
    )


def sample_action(arm, action, src_last: int, dst_frames: int):
    """Re-timed local matrices per mapped bone: {nue_bone: [Matrix * dst_frames]}."""
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    try:
        if action.slots:
            arm.animation_data.action_slot = action.slots[0]
    except Exception:
        pass

    scene = bpy.context.scene
    result = {target: [] for target in BONE_MAP.values()}

    for i in range(dst_frames):
        f_src = 0.0 if dst_frames == 1 else src_last * i / (dst_frames - 1)
        scene.frame_set(round(f_src))
        bpy.context.view_layer.update()
        for src_name, target in BONE_MAP.items():
            pb = arm.pose.bones[src_name]
            result[target].append(local_matrix(arm, pb).copy())
    return result


def main() -> int:
    out_dir = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else os.path.join(MOD_ROOT, "assets", "work", "re")
    os.makedirs(out_dir, exist_ok=True)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=MODEL)
    arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")

    bones = re_export.load_rig_json(RIG_JSON)
    nue_rest = nue_rest_locals(bones)

    # CS2 rest locals (armature rest pose)
    cs2_rest = {}
    for src_name, target in BONE_MAP.items():
        pb = arm.pose.bones[src_name]
        cs2_rest[target] = rest_local_matrix(pb)

    template = os.path.join(out_dir, "_template_weapon.re")
    re_export.build_template(template, bones, num_frames=2)
    print("RE_TEMPLATE_OK", template)

    for set_name, targets in SETS.items():
        set_dir = os.path.join(out_dir, set_name)
        os.makedirs(set_dir, exist_ok=True)
        for target_name, (action_name, src_last, dst_frames) in targets.items():
            action = bpy.data.actions.get(action_name)
            if action is None:
                print("RE_MISSING_ACTION", action_name)
                continue

            sampled = sample_action(arm, action, src_last, dst_frames)

            rows = {}
            for bone in bones:
                name = bone["name"]
                if name in sampled:
                    mats = []
                    for m in sampled[name]:
                        delta = cs2_rest[name].inverted() @ m
                        mats.append(nue_rest[name] @ delta)
                else:
                    mats = [nue_rest[name]] * dst_frames
                rows[name] = [matrix_to_row(m, float(i)) for i, m in enumerate(mats)]

            out_path = os.path.join(set_dir, f"{target_name}.re")
            re_export.replace_curves(template, out_path, rows, times=range(dst_frames))
            print(f"RE_OK {out_path} frames={dst_frames} action={action_name}")

    print("RE_EXPORT_DONE")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception:
        import traceback

        traceback.print_exc()
        print("RE_EXPORT_FAIL")
        raise SystemExit(1)
