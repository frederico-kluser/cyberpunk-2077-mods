"""Headless studio preview renders for the Desert Eagle model.

Usage (from anywhere, no GUI needed):

    blender --background --python mods/DesertEagle/docs/renders/render_preview.py

What it does:
  1. resets to an empty scene and imports the desert_eagle_poly.glb,
  2. selects every imported MESH (EMPTies are ignored) and computes the combined
     world bounding box of the gun,
  3. builds a small studio: dark grey world (strength 0.3), a big area key light
     (upper front-left), a weaker fill (front-right) and a rim light behind,
  4. renders three 1600x1000 PNGs (opaque background):
        deagle_preview_34.png    3/4 hero view, front-right, slightly above
        deagle_preview_side.png  pure left profile, 85mm long lens
        deagle_preview_top.png   from above at a slight angle
     with the gun framed to fill ~80% of the frame in every shot.

Engine policy: EEVEE first (fast, reliable headless on this machine), falling
back to Cycles (24 samples + OpenImageDenoise) per shot if EEVEE raises or
writes a uniform/black image.

Console contract:
    IMGC <axis> ...            orientation facts used for the camera
    RENDER_OK <absolute path>  once per finished image
    RENDERS_DONE               after all three images

Writes ONLY inside this docs/renders folder. No project file is touched.
"""

from __future__ import annotations

import math
import os
import sys
import traceback

import bpy
from mathutils import Matrix, Vector

# --------------------------------------------------------------------------
# configuration
# --------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = (
    r"C:\Users\kluse\Projects\cyberpunk-2077-desert-eagle\mods\DesertEagle"
    r"\assets\raw\desert_eagle_poly.glb"
)

RES_X, RES_Y = 1600, 1000
LENS_MM = 85.0
SENSOR_W = 36.0
FILL = 0.8  # gun should cover ~80% of the frame

CYCLES_SAMPLES = 24
EEVEE_SAMPLES = 32


def log(msg: str) -> None:
    print(msg, flush=True)


# --------------------------------------------------------------------------
# scene / model
# --------------------------------------------------------------------------
def reset_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)


def import_model():
    bpy.ops.import_scene.gltf(filepath=MODEL_PATH)
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    empties = [o for o in bpy.context.scene.objects if o.type == "EMPTY"]
    if not meshes:
        raise RuntimeError("no MESH objects were imported from the GLB")
    # select the meshes (ignore the empties) so the scene is 'framed' on them
    try:
        bpy.ops.object.select_all(action="DESELECT")
        for obj in meshes:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = meshes[0]
    except Exception as exc:  # selection is cosmetic in background mode
        log(f"WARN selection failed: {exc}")
    log(
        f"IMGC meshes={len(meshes)} empties={len(empties)} "
        f"names={[o.name for o in meshes]}"
    )
    return meshes


def combined_bbox(meshes):
    mn = Vector((1e18, 1e18, 1e18))
    mx = Vector((-1e18, -1e18, -1e18))
    for obj in meshes:
        for corner in obj.bound_box:
            world = obj.matrix_world @ Vector(corner)
            for i in range(3):
                mn[i] = min(mn[i], world[i])
                mx[i] = max(mx[i], world[i])
    return mn, mx


def sample_points(meshes, cap: int = 4000):
    pts = []
    total = sum(len(o.data.vertices) for o in meshes)
    step = max(1, total // cap)
    for obj in meshes:
        mw = obj.matrix_world
        for idx in range(0, len(obj.data.vertices), step):
            pts.append(mw @ obj.data.vertices[idx].co)
    return pts


def classify_model(mn, mx, pts):
    """Return (center, front, up, side) unit vectors in world space.

    Gun proportions: length > height > width, so the middle bbox extent is the
    height (up axis) and the largest is the barrel direction. The muzzle half
    is all slide/barrel (high), the rear half carries the grip (low), so the
    half with the higher mean 'up' coordinate is the front.
    """
    size = mx - mn
    center = (mn + mx) * 0.5
    axes = [Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))]
    order = sorted(range(3), key=lambda i: size[i], reverse=True)  # big->small
    len_axis = axes[order[0]]
    up_axis = axes[order[1]]
    side_axis = axes[order[2]]

    # up sign: prefer world +Z when Z is the height axis (glTF import is Z-up)
    if up_axis != Vector((0, 0, 1)):
        up_axis = up_axis.copy()
    else:
        up_axis = Vector((0, 0, 1))

    front_sign = 1.0
    hi_mean, lo_mean = None, None
    hi_pts, lo_pts = [], []
    for p in pts:
        d = (p - center).dot(len_axis)
        (hi_pts if d >= 0 else lo_pts).append(p)
    if hi_pts and lo_pts:
        hi_mean = sum(p.dot(up_axis) for p in hi_pts) / len(hi_pts)
        lo_mean = sum(p.dot(up_axis) for p in lo_pts) / len(lo_pts)
        front_sign = 1.0 if hi_mean >= lo_mean else -1.0
    front = (len_axis * front_sign).normalized()
    up = up_axis.normalized()
    side = up.cross(front).normalized()  # gun's left side
    log(
        f"IMGC size={tuple(round(v, 4) for v in size)} "
        f"len_axis={tuple(len_axis)} up_axis={tuple(up_axis)} "
        f"side_axis={tuple(side_axis)} front={tuple(front)} up={tuple(up)} "
        f"left={tuple(side)} mean_hi={hi_mean} mean_lo={lo_mean}"
    )
    return center, front, up, side


# --------------------------------------------------------------------------
# studio
# --------------------------------------------------------------------------
def build_world(scene) -> None:
    world = bpy.data.worlds.new("StudioWorld")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs[0].default_value = (0.055, 0.06, 0.07, 1.0)  # dark grey
    bg.inputs[1].default_value = 0.3  # strength ~0.3


def aim(obj, target) -> None:
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def camera_basis(look_dir, up_hint):
    """(right, up, backwards) unit vectors of a camera looking along look_dir."""
    fwd = Vector(look_dir).normalized()
    hint = Vector(up_hint).normalized()
    if abs(fwd.dot(hint)) > 0.999:  # degenerate straight-down case
        hint = Vector((0, 1, 0)) if abs(fwd.y) < 0.9 else Vector((1, 0, 0))
    right = fwd.cross(hint).normalized()
    upv = right.cross(fwd).normalized()
    return right, upv, fwd


def aim_with_up(obj, target, up_hint) -> None:
    """Point obj at target keeping its image-up aligned with up_hint."""
    fwd = (Vector(target) - obj.location).normalized()
    right, upv, fwd = camera_basis(fwd, up_hint)
    mat = Matrix(
        (
            (right.x, upv.x, -fwd.x),
            (right.y, upv.y, -fwd.y),
            (right.z, upv.z, -fwd.z),
        )
    )
    obj.rotation_euler = mat.to_euler()


def add_area(scene, name, position, target, energy, size, color):
    data = bpy.data.lights.new(name=name, type="AREA")
    data.energy = energy
    data.size = size
    data.color = color
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = Vector(position)
    aim(obj, target)
    return obj


def build_lights(scene, center, hero, up, diag):
    """3-point studio: big key upper front-left, weak fill front-right, rim behind."""
    d = diag
    right, _upv, _fwd = camera_basis(-hero, up)  # camera-right of the hero shot

    key_pos = center + hero * (0.9 * d) - right * (1.1 * d) + up * (1.3 * d)
    fill_pos = center + hero * (1.1 * d) + right * (1.2 * d) + up * (0.25 * d)
    rim_pos = center - hero * (1.3 * d) - right * (0.4 * d) + up * (0.9 * d)

    # The model is authored at ~metre scale (bbox diag ~5.5 units), so light
    # power must scale with distance^2 to expose the metal properly.
    key = add_area(
        scene, "Key", key_pos, center,
        energy=6.0 * (key_pos - center).length ** 2,
        size=0.9 * d, color=(1.0, 0.97, 0.92),
    )
    fill = add_area(
        scene, "Fill", fill_pos, center,
        energy=2.9 * (fill_pos - center).length ** 2,
        size=1.1 * d, color=(0.85, 0.9, 1.0),
    )
    rim = add_area(
        scene, "Rim", rim_pos, center,
        energy=7.0 * (rim_pos - center).length ** 2,
        size=0.55 * d, color=(0.95, 0.97, 1.0),
    )
    log(
        f"IMGC lights key={tuple(round(v, 3) for v in key.location)} "
        f"fill={tuple(round(v, 3) for v in fill.location)} "
        f"rim={tuple(round(v, 3) for v in rim.location)} diag={d:.4f}"
    )
    return hero


# --------------------------------------------------------------------------
# camera framing
# --------------------------------------------------------------------------
def frame_camera(cam, center, pts, view_dir, up_hint, fill=FILL):
    """Place cam so the real silhouette fills ~`fill` of the frame.

    Fits against sampled mesh points (not just the bbox corners) with exact
    perspective: every point must land inside the frustum at `fill` size.
    """
    view_dir = Vector(view_dir).normalized()  # object -> camera
    right, upv, _back = camera_basis(-view_dir, up_hint)

    half_h = math.atan((SENSOR_W * 0.5) / LENS_MM)
    sensor_h = SENSOR_W * (RES_Y / RES_X)
    half_v = math.atan((sensor_h * 0.5) / LENS_MM)
    denom_h = fill * math.tan(half_h)
    denom_v = fill * math.tan(half_v)

    dist = 0.0
    for p in pts:
        rel = p - center
        along = rel.dot(view_dir)  # >0 = closer to the camera
        dist = max(
            dist,
            along + abs(rel.dot(right)) / denom_h,
            along + abs(rel.dot(upv)) / denom_v,
        )
    dist *= 1.02  # tiny safety margin

    cam.location = Vector(center) + view_dir * dist
    aim_with_up(cam, center, up_hint)
    return dist


# --------------------------------------------------------------------------
# engines
# --------------------------------------------------------------------------
def setup_eevee(scene) -> str:
    for engine in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        try:
            scene.render.engine = engine
            for attr, value in (
                ("taa_render_samples", EEVEE_SAMPLES),
                ("taa_samples", EEVEE_SAMPLES),
            ):
                try:
                    setattr(scene.eevee, attr, value)
                except Exception:
                    pass
            return engine
        except Exception:
            continue
    raise RuntimeError("no EEVEE engine id accepted")


def setup_cycles(scene) -> str:
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = CYCLES_SAMPLES
    try:
        scene.cycles.use_adaptive_sampling = True
    except Exception:
        pass
    try:
        scene.cycles.use_denoising = True
        scene.cycles.denoiser = "OPENIMAGEDENOISE"
    except Exception as exc:
        log(f"WARN denoise setup: {exc}")
    try:
        scene.cycles.max_bounces = 6
    except Exception:
        pass
    return "CYCLES"


def image_stats(path):
    """(mean, std, uniform) luminance of the written PNG, or None."""
    try:
        import numpy as np
    except Exception:
        np = None
    try:
        img = bpy.data.images.load(path)
        try:
            if np is not None:
                buf = np.empty(len(img.pixels), dtype=np.float32)
                img.pixels.foreach_get(buf)
                rgb = buf.reshape(-1, 4)[:, :3]
                lum = rgb @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
                mean = float(lum.mean())
                std = float(lum.std())
                uniform = bool(std < 1e-4)
                return mean, std, uniform
            px = list(img.pixels)
            vals = px[0::4]
            mean = sum(vals) / max(1, len(vals))
            uniform = (max(vals) - min(vals)) < 1e-4
            return mean, 0.0, uniform
        finally:
            bpy.data.images.remove(img)
    except Exception as exc:
        log(f"WARN image stats failed for {path}: {exc}")
        return None


# --------------------------------------------------------------------------
# rendering
# --------------------------------------------------------------------------
def render_shot(scene, cam, filename, view_dir, up_hint, pts, center):
    path = os.path.join(HERE, filename)
    dist = frame_camera(cam, center, pts, view_dir, up_hint)
    log(f"IMGC shot={filename} view={tuple(round(v, 3) for v in view_dir)} "
        f"dist={dist:.4f} cam={tuple(round(v, 3) for v in cam.location)}")

    attempts = []
    try:
        attempts.append(("EEVEE", setup_eevee(scene)))
    except Exception as exc:
        log(f"WARN EEVEE unavailable: {exc}")
    attempts.append(("CYCLES", setup_cycles(scene)))

    for label, engine in attempts:
        scene.render.engine = engine
        scene.render.filepath = path
        try:
            bpy.ops.render.render(write_still=True)
        except Exception as exc:
            log(f"RENDER_WARN {filename} {label} raised: {exc}")
            traceback.print_exc()
            continue
        if not os.path.isfile(path):
            log(f"RENDER_WARN {filename} {label} produced no file")
            continue
        size = os.path.getsize(path)
        stats = image_stats(path)
        if stats is None:
            if size < 20000:
                log(f"RENDER_WARN {filename} {label} tiny file ({size} bytes)")
                continue
        else:
            mean, std, uniform = stats
            log(f"IMGSTAT {filename} engine={label} bytes={size} "
                f"mean={mean:.4f} std={std:.4f} uniform={'yes' if uniform else 'no'}")
            if uniform:
                log(f"RENDER_WARN {filename} {label} uniform/black image, "
                    f"falling back")
                continue
        log(f"RENDER_OK {path}")
        return True
    log(f"RENDER_FAIL {path}")
    return False


def main() -> int:
    log("RENDER_START")
    reset_scene()
    meshes = import_model()
    mn, mx = combined_bbox(meshes)
    pts = sample_points(meshes)
    center, front, up, left = classify_model(mn, mx, pts)
    diag = (mx - mn).length
    log(f"IMGC bbox_min={tuple(round(v, 4) for v in mn)} "
        f"bbox_max={tuple(round(v, 4) for v in mx)} center={tuple(round(v, 4) for v in center)}")

    scene = bpy.context.scene
    scene.render.resolution_x = RES_X
    scene.render.resolution_y = RES_Y
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.color_depth = "8"

    build_world(scene)
    hero = (front * 0.72 + (-left) * 0.62 + up * 0.42).normalized()  # front-right
    build_lights(scene, center, hero, up, diag)

    cam_data = bpy.data.cameras.new("PreviewCam")
    cam_data.lens = LENS_MM
    cam_data.sensor_width = SENSOR_W
    cam_data.clip_start = 0.01
    cam_data.clip_end = 100.0
    cam = bpy.data.objects.new("PreviewCam", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam

    shots = [
        # 3/4 hero: front-right of the gun, slightly above
        ("deagle_preview_34.png", hero, up),
        # pure left-side profile (85mm long lens keeps proportions true)
        ("deagle_preview_side.png", left, up),
        # from above at a slight angle; roll pinned along the gun's width axis
        ("deagle_preview_top.png", up * 0.95 + left * 0.22 + front * 0.15, left),
    ]

    ok = 0
    for filename, view, up_hint in shots:
        if render_shot(scene, cam, filename, view, up_hint, pts, center):
            ok += 1

    if ok == len(shots):
        log("RENDERS_DONE")
        return 0
    log(f"RENDERS_FAIL {ok}/{len(shots)}")
    return 1


if __name__ == "__main__":
    try:
        code = main()
    except Exception:
        traceback.print_exc()
        print("RENDERS_FAIL exception", flush=True)
        code = 1
    sys.exit(code)