"""Probe the transforms: object scales, armature world, bone locals."""

import bpy
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "src", "blender"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scripts"))

MODEL = os.path.join(HERE, "..", "..", "assets", "raw", "desert_eagle_cs2.glb")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=MODEL)

for o in bpy.data.objects:
    print(f"{o.type:9s} {o.name[:40]:40s} scale={tuple(round(s,4) for s in o.scale)} "
          f"loc={tuple(round(v,3) for v in o.location)} parent={o.parent.name[:20] if o.parent else None}")

arm = next((o for o in bpy.data.objects if o.type == "ARMATURE"), None)
if arm:
    print("\narmature world scale:", tuple(round(s, 5) for s in arm.matrix_world.to_scale()))
    print("bone locals:")
    for pb in list(arm.pose.bones)[:6]:
        m = pb.bone.matrix_local
        print(f"  {pb.name:32s} head={tuple(round(v,4) for v in pb.bone.head_local)} scale={tuple(round(s,4) for s in m.to_scale())}")
