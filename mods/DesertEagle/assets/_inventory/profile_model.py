# -*- coding: utf-8 -*-
"""Profile a 3D model (glb/gltf/fbx/blend) inside Blender --background.

Usage:
    blender.exe --background --python profile_model.py -- <model path>

Prints: Blender version, objects (name + type), per-mesh vertex/polygon counts,
total counts, world bounding-box size (X/Y/Z), material names, armature names +
all bone names, and whether separate parts named slide/barrel/trigger/mag/
magazine/grip/frame/sight exist. Ends with PROFILE_OK on success.
"""
import os
import sys

import bpy
from mathutils import Vector

PART_KEYWORDS = [
    "slide", "barrel", "trigger", "mag", "magazine",
    "grip", "frame", "sight",
]


def model_path_from_argv():
    argv = sys.argv
    if "--" in argv:
        tail = argv[argv.index("--") + 1:]
        if tail:
            return os.path.abspath(tail[0])
    raise SystemExit("ERROR: no model path given after '--'")


def import_model(path):
    ext = os.path.splitext(path)[1].lower()
    # Start from a clean scene
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if ext == ".blend":
        bpy.ops.wm.open_mainfile(filepath=path)
        return "opened .blend"
    if ext in (".glb", ".gltf"):
        bpy.ops.import_scene.gltf(filepath=path)
        return "bpy.ops.import_scene.gltf"
    if ext == ".fbx":
        bpy.ops.import_scene.fbx(filepath=path)
        return "bpy.ops.import_scene.fbx"
    raise SystemExit("ERROR: unsupported extension: %s" % ext)


def world_bbox(objs):
    lo = Vector((1e30, 1e30, 1e30))
    hi = Vector((-1e30, -1e30, -1e30))
    found = False
    for ob in objs:
        if ob.type != "MESH":
            continue
        mw = ob.matrix_world
        for corner in ob.bound_box:
            v = mw @ Vector(corner)
            for i in range(3):
                lo[i] = min(lo[i], v[i])
                hi[i] = max(hi[i], v[i])
        found = True
    if not found:
        return None
    return hi - lo, lo, hi


def main():
    path = model_path_from_argv()
    if not os.path.isfile(path):
        raise SystemExit("ERROR: model file not found: %s" % path)

    print("=" * 72)
    print("MODEL PROFILE")
    print("model_path=%s" % path)
    print("blender_version=%s" % bpy.app.version_string)
    how = import_model(path)
    print("import_method=%s" % how)
    print("=" * 72)

    objs = list(bpy.data.objects)
    print("\n-- OBJECTS (%d) --" % len(objs))
    for ob in objs:
        print("  %-40s type=%s" % (ob.name, ob.type))

    print("\n-- MESH COUNTS --")
    total_v = 0
    total_p = 0
    for ob in objs:
        if ob.type != "MESH":
            continue
        me = ob.data
        nv = len(me.vertices)
        npoly = len(me.polygons)
        total_v += nv
        total_p += npoly
        print("  %-40s vertices=%d polygons=%d" % (ob.name, nv, npoly))
    print("  TOTAL vertices=%d polygons=%d" % (total_v, total_p))

    print("\n-- WORLD BOUNDING BOX (whole model) --")
    bb = world_bbox(objs)
    if bb is None:
        print("  (no mesh objects)")
    else:
        size, lo, hi = bb
        print("  size_x=%.4f" % size.x)
        print("  size_y=%.4f" % size.y)
        print("  size_z=%.4f" % size.z)
        print("  min=(%.4f, %.4f, %.4f)" % (lo.x, lo.y, lo.z))
        print("  max=(%.4f, %.4f, %.4f)" % (hi.x, hi.y, hi.z))

    print("\n-- MATERIALS --")
    mats = sorted({slot.material.name
                   for ob in objs if ob.type == "MESH"
                   for slot in ob.material_slots
                   if slot.material is not None})
    if not mats:
        print("  (none)")
    for m in mats:
        print("  %s" % m)

    print("\n-- ARMATURES / BONES --")
    arms = [ob for ob in objs if ob.type == "ARMATURE"]
    if not arms:
        print("  (no armature)")
    for ob in arms:
        bones = list(ob.data.bones)
        print("  armature=%s bones=%d" % (ob.name, len(bones)))
        for b in bones:
            print("    bone: %s" % b.name)

    print("\n-- PART DETECTION (slide/barrel/trigger/mag/magazine/grip/frame/sight) --")
    for kw in PART_KEYWORDS:
        hits = [ob.name for ob in objs if kw in ob.name.lower()]
        status = "YES" if hits else "no"
        print("  %-9s -> %s %s" % (kw, status, hits if hits else ""))

    print("\nPROFILE_OK")


main()
