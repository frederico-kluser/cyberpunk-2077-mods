"""Replicate the rest-to-rest math and print scales/sample vertices."""

import bpy
import os
import sys
from mathutils import Matrix, Quaternion, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "src", "blender"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scripts"))
from de_pipeline.re_export import load_rig_json  # noqa: E402

MODEL = os.path.join(HERE, "..", "..", "assets", "raw", "desert_eagle_cs2.glb")
RIG = os.path.join(HERE, "..", "..", "assets", "_inventory", "nue_rig.json")
BONE_MAP = {
    "GLTF_created_0_rootJoint": "barrel_plug",
    "weapon_hand_r_4": "barrel",
    "v_weapon_deagle_slide_0": "slide",
    "v_weapon_deagle_trigger_1": "weapon_trigger",
    "v_weapon_deagle_clip_2": "mag_slot",
    "v_weapon_deagle_hammer_3": "hammer",
}
RIG_ORDER = ["barrel_plug", "barrel", "muzzle_slot", "fx_muzzle", "weapon_trigger",
             "slide", "hammer", "slider_down", "mag_slot", "scope_slot", "pos_ironsight"]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=MODEL)
arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")


def local_of(pb):
    if pb.parent is None:
        return pb.bone.matrix_local.copy()
    return pb.parent.bone.matrix_local.inverted() @ pb.bone.matrix_local


cs2_local = {BONE_MAP.get(pb.name, pb.name): local_of(pb) for pb in arm.pose.bones}
nue_local = {}
for b in load_rig_json(RIG):
    x, y, z, w = b["quat"]
    nue_local[b["name"]] = Matrix.Translation(Vector(b["pos"])) @ Quaternion((w, x, y, z)).to_matrix().to_4x4()

parents = [-1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 5]


def chain(local, order, parents):
    out = {}
    for i, name in enumerate(order):
        if name not in local:
            continue
        p = parents[i]
        while p >= 0 and order[p] not in local:
            p = parents[p]
        out[name] = (out[order[p]] @ local[name] if p >= 0 else local[name].copy())
    return out


nue_arm = chain(nue_local, RIG_ORDER, parents)
cs2_arm = chain(cs2_local, RIG_ORDER, parents)
cs2_world = {n: arm.matrix_world @ m for n, m in cs2_arm.items()}

for name in ("barrel", "slide", "hammer"):
    if name in nue_arm and name in cs2_world:
        d = nue_arm[name] @ cs2_world[name].inverted()
        print(f"{name:8s} nue_scale={tuple(round(s,4) for s in nue_arm[name].to_scale())} "
              f"cs2w_scale={tuple(round(s,5) for s in cs2_world[name].to_scale())} "
              f"delta_scale={tuple(round(s,5) for s in d.to_scale())}")
        print(f"         nue_pos={tuple(round(v,3) for v in nue_arm[name].to_translation())} "
              f"cs2w_pos={tuple(round(v,3) for v in cs2_world[name].to_translation())}")

obj = next(o for o in bpy.data.objects if o.type == "MESH" and o.name != "Icosphere")
vs = [obj.matrix_world @ v.co for v in list(obj.data.vertices)[:3]]
print("sample world verts:", [tuple(round(c, 4) for c in v) for v in vs])
