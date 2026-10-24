"""Video of a CS2 clip applied to the shipped mesh (LBS skinning per frame).

Renders the `empty_reload` clip (101 frames @ 30 fps = 3.4 s) with the real
grip alignment (A in the root) and the CS2 textures, encoded to MP4 with
Blender's built-in FFMPEG writer (no system ffmpeg needed).

The per-frame reskin happens in a frame_change_pre handler so the standard
animation renderer can write the video.

Run: blender.exe --background --python render_anim_video.py
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
TEX = os.path.join(MOD_ROOT, "assets", "work", "cs2_textures")
CLIP_RE = os.path.join(MOD_ROOT, "assets", "work", "re", "base1", "empty_reload.re")
ALIGN = os.path.join(MOD_ROOT, "assets", "work", "de_align.json")
OUT = os.path.join(HERE, "deagle_reload.mp4")

_spec = importlib.util.spec_from_file_location("rac", os.path.join(HERE, "render_anim_check.py"))
rac = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rac)
_spec2 = importlib.util.spec_from_file_location("rp", os.path.join(HERE, "render_preview.py"))
rp = importlib.util.module_from_spec(_spec2)
_spec2.loader.exec_module(rp)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)

    geo = json.load(open(GEO, encoding="utf-8"))["chunks"][0]
    rac.RE = CLIP_RE
    names, parents, rest_local, poses = rac.load_re()
    rest_arm = rac.chain(rest_local, parents)

    # grip alignment (the same the shipped .anims carry in the root local)
    A = np.eye(4)
    if os.path.exists(ALIGN):
        ad = json.load(open(ALIGN, encoding="utf-8"))
        A[:3, :3] = np.array(ad["R"])
        A[:3, 3] = ad["t"]

    clip_rows = poses.get("slide")
    nframes = len(clip_rows) if clip_rows is not None else 24

    scene = bpy.context.scene
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 800
    scene.render.fps = 30
    scene.frame_start = 0
    scene.frame_end = nframes - 1

    # video output (media_type BEFORE the ffmpeg settings, Blender 5.x)
    scene.render.image_settings.media_type = "VIDEO"
    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.constant_rate_factor = "MEDIUM"
    scene.render.ffmpeg.gopsize = 12
    scene.render.filepath = OUT

    rp.build_world(scene)

    cam_data = bpy.data.cameras.new("Cam")
    cam_data.lens = rp.LENS_MM
    cam_data.sensor_width = rp.SENSOR_W
    cam = bpy.data.objects.new("Cam", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam

    side = Vector((1, 0, 0))
    up = Vector((0, 0, 1))
    hero = (Vector((0, -1, 0)) * 0.72 + (-side) * 0.62 + up * 0.42).normalized()

    # fixed framing around the whole motion envelope
    all_pts = []
    for f in range(nframes):
        locals_ = rac.pose_local(poses, names, f)
        locals_[0] = A @ locals_[0]
        pose_arm = rac.chain(locals_, parents)
        for p in rac.skin_positions(geo, names, parents, rest_arm, pose_arm):
            all_pts.append(p)
    mn = Vector((min(p[i] for p in all_pts) for i in range(3)))
    mx = Vector((max(p[i] for p in all_pts) for i in range(3)))
    center = (mn + mx) / 2
    diag = (mx - mn).length
    rp.build_lights(scene, center, hero, up, diag)

    rp.frame_camera(cam, center, [Vector(p) for p in all_pts], hero, up)

    # per-frame reskin
    state = {"obj": None}

    def on_frame(scene_, _deps):
        f = scene_.frame_current
        locals_ = rac.pose_local(poses, names, f)
        locals_[0] = A @ locals_[0]
        pose_arm = rac.chain(locals_, parents)
        posed = rac.skin_positions(geo, names, parents, rest_arm, pose_arm)
        if state["obj"] is not None:
            bpy.data.objects.remove(state["obj"], do_unlink=True)
        state["obj"] = rac.build_mesh(posed, geo)
        bpy.context.view_layer.update()

    bpy.app.handlers.frame_change_pre.append(on_frame)
    on_frame(scene, None)
    bpy.ops.render.render(animation=True)
    bpy.app.handlers.frame_change_pre.remove(on_frame)

    ok = os.path.exists(OUT) and os.path.getsize(OUT) > 50_000
    print(f"VIDEO_{'OK' if ok else 'FAIL'} {OUT} {os.path.getsize(OUT) if os.path.exists(OUT) else 0} bytes", flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception:
        import traceback

        traceback.print_exc()
        print("VIDEO_FAIL", flush=True)
        raise SystemExit(1)
