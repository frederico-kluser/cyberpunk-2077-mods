"""Render the CS2 Desert Eagle: studio stills + key frames of its REAL CS2 actions.

Reuses the tuned studio/framing from render_preview.py (lights scaled by
distance^2, camera fitted on sampled mesh points).

Run: blender.exe --background --python render_cs2.py
Outputs to docs/renders/cs2/.
"""

from __future__ import annotations

import importlib.util
import os

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = os.path.join(HERE, "..", "..", "assets", "raw", "desert_eagle_cs2.glb")

_spec = importlib.util.spec_from_file_location("rp", os.path.join(HERE, "render_preview.py"))
rp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rp)


def assign_action(arm, action):
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    try:  # Blender 4.4+ slotted actions
        if action.slots:
            arm.animation_data.action_slot = action.slots[0]
    except Exception:
        pass


def sample_world(meshes, cap: int = 4000):
    """World-space points of the EVALUATED (skinned) mesh — the geometry the
    camera actually sees. The CS2 GLB's undeformed bound_box is ~10x larger
    than its skinned result, so fitting must use the evaluated mesh."""
    pts = []
    dg = bpy.context.evaluated_depsgraph_get()
    for obj in meshes:
        ev = obj.evaluated_get(dg)
        me = ev.to_mesh()
        try:
            pts.extend(ev.matrix_world @ v.co for v in me.vertices)
        finally:
            ev.to_mesh_clear()
    step = max(1, len(pts) // cap)
    return pts[::step]


def bbox_of(pts):
    mn = pts[0].copy()
    mx = pts[0].copy()
    for p in pts:
        for i in range(3):
            mn[i] = min(mn[i], p[i])
            mx[i] = max(mx[i], p[i])
    return mn, mx


def main() -> int:
    rp.log("CS2_RENDER_START")
    rp.reset_scene()
    bpy.ops.import_scene.gltf(filepath=MODEL)

    # The Sketchfab export carries an invisible 'Icosphere' (~10x the gun's
    # size) that would dominate every camera fit — drop it, like the pipeline
    # does (retarget.drop_objects).
    junk = bpy.data.objects.get("Icosphere")
    if junk is not None:
        bpy.data.objects.remove(junk, do_unlink=True)
        rp.log("CS2 dropped junk object 'Icosphere'")

    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")

    pts = sample_world(meshes)
    mn, mx = bbox_of(pts)
    center, front, up, left = rp.classify_model(mn, mx, pts)
    diag = (mx - mn).length
    rp.log(f"CS2 diag={diag:.4f} center={tuple(round(v, 3) for v in center)}")

    scene = bpy.context.scene
    scene.render.resolution_x = rp.RES_X
    scene.render.resolution_y = rp.RES_Y
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"

    rp.build_world(scene)
    hero = (front * 0.72 + (-left) * 0.62 + up * 0.42).normalized()
    rp.build_lights(scene, center, hero, up, diag)

    cam_data = bpy.data.cameras.new("CS2Cam")
    cam_data.lens = rp.LENS_MM
    cam_data.sensor_width = rp.SENSOR_W
    cam_data.clip_start = 0.01
    cam_data.clip_end = 100.0
    cam = bpy.data.objects.new("CS2Cam", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam

    # ---- studio stills (rest pose) ----
    ok = 0
    for filename, view, up_hint in (
        ("cs2/cs2_preview_34.png", hero, up),
        ("cs2/cs2_preview_side.png", left, up),
    ):
        if rp.render_shot(scene, cam, filename, view, up_hint, pts, center):
            ok += 1

    # ---- real CS2 action key frames (camera re-fits per frame) ----
    def play(action_name, frames, tag):
        action = bpy.data.actions.get(action_name)
        if action is None:
            rp.log(f"CS2_MISSING_ACTION {action_name}")
            return
        assign_action(arm, action)
        for f in frames:
            scene.frame_set(f)
            meshes_now = [o for o in bpy.data.objects if o.type == "MESH"]
            pts_now = sample_world(meshes_now)
            mn2, mx2 = bbox_of(pts_now)
            center_now = (mn2 + mx2) / 2
            rp.render_shot(
                scene, cam, f"cs2/cs2_{tag}_f{f:03d}.png", hero, up, pts_now, center_now
            )

    play("firstperson_shoot1", [0, 3, 6, 9, 12, 16], "shoot")
    play("firstperson_reload", [0, 12, 24, 36, 48, 52], "reload")

    print("CS2_RENDERS_DONE", flush=True)
    return 0


if __name__ == "__main__":
    try:
        code = main()
    except Exception:
        import traceback

        traceback.print_exc()
        print("CS2_RENDERS_FAIL exception", flush=True)
        code = 1

