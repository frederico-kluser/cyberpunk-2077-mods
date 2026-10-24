"""Profile the CS2 Desert Eagle GLB: objects, meshes, armature, bones AND actions.

Run:  blender.exe --background --python profile_cs2.py -- <model.glb>
"""

from __future__ import annotations

import sys

import bpy


def main() -> None:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else sys.argv[1:]
    path = argv[0]

    bpy.ops.wm.read_factory_settings(use_empty=True)
    ext = path.rsplit(".", 1)[-1].lower()
    if ext in ("glb", "gltf"):
        bpy.ops.import_scene.gltf(filepath=path)
    else:
        raise SystemExit(f"unsupported: {path}")

    print("=" * 72)
    print("CS2 MODEL PROFILE")
    print(f"model_path={path}")
    print(f"blender_version={bpy.app.version_string}")
    print("=" * 72)

    print("\n-- OBJECTS --")
    for obj in sorted(bpy.data.objects, key=lambda o: o.name):
        extra = ""
        if obj.type == "MESH":
            extra = f" verts={len(obj.data.vertices)} polys={len(obj.data.polygons)}"
        if obj.parent:
            extra += f" parent={obj.parent.name}"
        print(f"  {obj.name:40s} type={obj.type}{extra}")

    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    total_v = sum(len(o.data.vertices) for o in meshes)
    total_p = sum(len(o.data.polygons) for o in meshes)
    print(f"\n-- MESH TOTALS -- meshes={len(meshes)} vertices={total_v} polygons={total_p}")

    print("\n-- VERTEX GROUPS (skinning) --")
    for obj in meshes:
        groups = sorted(g.name for g in obj.vertex_groups)
        print(f"  {obj.name}: {groups}")

    print("\n-- MATERIALS --")
    for mat in sorted(bpy.data.materials, key=lambda m: m.name):
        print(f"  {mat.name}")

    print("\n-- ARMATURES / BONES --")
    arms = [o for o in bpy.data.objects if o.type == "ARMATURE"]
    if not arms:
        print("  (no armature)")
    for arm in arms:
        bones = arm.data.bones
        print(f"  armature '{arm.name}' bones={len(bones)}")
        for bone in bones:
            parent = bone.parent.name if bone.parent else "<root>"
            print(f"    {bone.name:32s} parent={parent}")

    print("\n-- ACTIONS (animations) --")

    def count_fcurves(action):
        try:
            return len(action.fcurves)
        except AttributeError:  # Blender 5.x slotted actions
            total = 0
            for layer in action.layers:
                for strip in layer.strips:
                    for slot in action.slots:
                        bag = strip.channelbag(slot)
                        if bag is not None:
                            total += len(bag.fcurves)
            return total

    def iter_fcurves(action):
        try:
            yield from action.fcurves
        except AttributeError:
            for layer in action.layers:
                for strip in layer.strips:
                    for slot in action.slots:
                        bag = strip.channelbag(slot)
                        if bag is not None:
                            yield from bag.fcurves

    if not bpy.data.actions:
        print("  (no actions)")
    for action in sorted(bpy.data.actions, key=lambda a: a.name):
        curves = list(iter_fcurves(action))
        if curves:
            frame_start = min(c.keyframe_points[0].co.x for c in curves)
            frame_end = max(c.keyframe_points[-1].co.x for c in curves)
        else:
            frame_start = frame_end = 0.0
        targets = sorted({c.data_path.split('"')[1] for c in curves if '"' in c.data_path})
        print(
            f"  {action.name:40s} frames={frame_start:.1f}..{frame_end:.1f} "
            f"fcurves={len(curves)} targets={targets}"
        )

    # world bbox of all meshes
    import mathutils

    mins = mathutils.Vector((1e9, 1e9, 1e9))
    maxs = mathutils.Vector((-1e9, -1e9, -1e9))
    for obj in meshes:
        for corner in obj.bound_box:
            world = obj.matrix_world @ mathutils.Vector(corner)
            for i in range(3):
                mins[i] = min(mins[i], world[i])
                maxs[i] = max(maxs[i], world[i])
    size = maxs - mins
    print("\n-- WORLD BOUNDING BOX --")
    print(f"  size_x={size.x:.4f} size_y={size.y:.4f} size_z={size.z:.4f}")
    print(f"  min=({mins.x:.4f},{mins.y:.4f},{mins.z:.4f}) max=({maxs.x:.4f},{maxs.y:.4f},{maxs.z:.4f})")

    print("\nPROFILE_CS2_OK")


if __name__ == "__main__":
    main()
