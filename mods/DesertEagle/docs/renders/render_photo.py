"""One hero photo of the final Desert Eagle (high resolution).

Shows the GAME look: the shipped mesh with the grip alignment A that the
shipped .anims carry in the root local (de_align.json). Reuses the render
studio helpers and the textured mesh builder from render_anim_check.

Run: blender.exe --background --python render_photo.py
"""

from __future__ import annotations

import importlib.util
import json
import os

import bpy
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
MOD_ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
GEO = os.path.join(MOD_ROOT, "assets", "work", "de_geometry.json")
ALIGN = os.path.join(MOD_ROOT, "assets", "work", "de_align.json")

_spec = importlib.util.spec_from_file_location("rac", os.path.join(HERE, "render_anim_check.py"))
rac = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rac)
_spec2 = importlib.util.spec_from_file_location("rp", os.path.join(HERE, "render_preview.py"))
rp = importlib.util.module_from_spec(_spec2)
_spec2.loader.exec_module(rp)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)

    geo = json.load(open(GEO, encoding="utf-8"))["chunks"][0]

    # the grip alignment A lives in the .anims root — apply it like the game
    # does at rest: v' = A @ v
    A = np.eye(4)
    if os.path.exists(ALIGN):
        ad = json.load(open(ALIGN, encoding="utf-8"))
        A[:3, :3] = np.array(ad["R"])
        A[:3, 3] = ad["t"]
    posed = []
    for p in geo["positions"]:
        v = A @ np.array([p[0], p[1], p[2], 1.0])
        posed.append((float(v[0]), float(v[1]), float(v[2])))
    obj = rac.build_mesh(posed, geo)
    bpy.context.view_layer.update()

    scene = bpy.context.scene
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1200
    scene.render.image_settings.file_format = "PNG"
    rp.build_world(scene)

    cam_data = bpy.data.cameras.new("Cam")
    cam_data.lens = rp.LENS_MM  # 85mm — the studio default (58mm distorts)
    cam_data.sensor_width = rp.SENSOR_W
    cam = bpy.data.objects.new("Cam", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam

    pts = [obj.matrix_world @ v.co for v in obj.data.vertices]
    mn = Vector((min(p[i] for p in pts) for i in range(3)))
    mx = Vector((max(p[i] for p in pts) for i in range(3)))
    center = (mn + mx) / 2
    diag = (mx - mn).length

    up = Vector((0, 0, 1))
    hero = (Vector((0, -1, 0)) * 0.80 + Vector((-1, 0, 0)) * 0.52 + up * 0.30).normalized()
    rp.build_lights(scene, center, hero, up, diag)

    ok = rp.render_shot(scene, cam, "deagle_photo.png", hero, up, pts, center)
    # pure side view as a sanity image (no perspective ambiguity)
    ok = rp.render_shot(scene, cam, "deagle_photo_side.png", Vector((1, 0, 0)), up, pts, center) and ok
    if ok:
        print("PHOTO_OK", flush=True)
        return 0
    print("PHOTO_FAIL", flush=True)
    return 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception:
        import traceback

        traceback.print_exc()
        print("PHOTO_FAIL", flush=True)
        raise SystemExit(1)
