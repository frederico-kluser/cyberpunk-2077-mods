"""Integration render: our mesh SKINNED by our CS2 animation.

Proves mesh + animation compose correctly: linear blend skinning with
  v' = sum_i w_i * (pose_arm_i @ rest_arm_i^-1) @ v
using the rest skeleton and the clip poses stored together in the .re files.

Two frames of `recoil_shoulder`: frame 0 (neutral) and frame 5 (slide back).

Run: blender.exe --background --python render_anim_check.py
"""

from __future__ import annotations

import importlib.util
import json
import math
import os

import bpy
import h5py
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
MOD_ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
GEO = os.path.join(MOD_ROOT, "assets", "work", "de_geometry.json")
RE = os.path.join(MOD_ROOT, "assets", "work", "re", "base1", "recoil_shoulder.re")
TEX = os.path.join(MOD_ROOT, "assets", "work", "cs2_textures")
OUT = os.path.join(HERE, "anim")

_spec = importlib.util.spec_from_file_location("rp", os.path.join(HERE, "render_preview.py"))
rp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rp)


def trs(pos, quat, scale):
    """(pos3, quat xyzw, scale3) -> 4x4 local matrix."""
    x, y, z, w = quat
    n = math.sqrt(x * x + y * y + z * z + w * w) or 1.0
    x, y, z, w = x / n, y / n, z / n, w / n
    r = np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ], dtype=np.float64)
    m = np.eye(4)
    m[:3, :3] = r @ np.diag(scale)
    m[:3, 3] = pos
    return m


def chain(local_by_bone, parents):
    out = {}
    for i in range(len(parents)):
        p = parents[i]
        local = local_by_bone[i] if isinstance(local_by_bone, dict) else local_by_bone[i]
        out[i] = out[p] @ local if p >= 0 else local.copy()
    return out


JOINT_ORDER = [
    "barrel_plug", "barrel", "muzzle_slot", "fx_muzzle", "weapon_trigger",
    "slide", "hammer", "slider_down", "mag_slot", "scope_slot", "pos_ironsight",
]


def xform_matrix(rows12):
    """The .re bone `xform` dataset: 4 vectors of 3 = x/y/z axes + translation
    (column-major affine)."""
    v = [float(x) for x in rows12]
    c0, c1, c2, t = v[0:3], v[3:6], v[6:9], v[9:12]
    m = np.eye(4)
    m[:3, 0] = c0
    m[:3, 1] = c1
    m[:3, 2] = c2
    m[:3, 3] = t
    return m


def load_re():
    """Returns names, parents, rest local matrices (from the bone TREE) and
    clip poses. The flat tables and the bone tree are CONSISTENT (verified:
    every flat pos matches the tree translation); `parents` is all-zero BY
    CDPR CONVENTION (hierarchy = nested bone groups), which is what this
    loader walks."""
    with h5py.File(RE, "r") as f:
        sk = f["/.re_asset_node/.re_asset_description_node/.re_skeleton"]
        root = sk["barrel_plug"]
        names, parents, rest_local = [], [], []

        def visit(group, parent_idx):
            idx = len(names)
            names.append(group.name.rsplit("/", 1)[-1])
            parents.append(parent_idx)
            rest_local.append(xform_matrix(group["xform"][:].reshape(-1)))
            for key in group.keys():
                item = group[key]
                if isinstance(item, h5py.Group) and not key.startswith("."):
                    visit(item, idx)

        visit(root, -1)

        # re-index to the RIG joint order (skin indices follow it, not the
        # alphabetical tree order)
        by_name = {}
        for n, p, m in zip(names, parents, rest_local):
            by_name[n] = (names[p] if p >= 0 else None, m)
        names = list(JOINT_ORDER)
        parents = [JOINT_ORDER.index(by_name[n][0]) if by_name[n][0] else -1 for n in names]
        rest_local = [by_name[n][1] for n in names]

        clip = f["/.re_asset_node/.re_animation_container/.re_animation/.re_anim_clip"]
        poses = {}
        for name in names:
            if name in clip:
                poses[name] = clip[name]["xformframes"][:]
        return names, parents, rest_local, poses


def pose_local(poses, names, frame):
    out = {}
    for i, name in enumerate(names):
        rows = poses.get(name)
        if rows is None:
            out[i] = np.eye(4)
            continue
        # xformframes rows are structured records [pos3 rot4 scale3 time] —
        # integer indexing works, slicing does not
        rec = rows[min(frame, len(rows) - 1)]
        vals = [float(rec[j]) for j in range(11)]
        out[i] = trs(vals[0:3], vals[3:7], vals[7:10])
    return out


def skin_positions(geo, names, parents, rest_arm, pose_arm):
    inv_rest = {i: np.linalg.inv(rest_arm[i]) for i in rest_arm}
    idx = geo["skin_indices"]
    wts = geo["skin_weights"]
    out = []
    for v, (pos, si, sw) in enumerate(zip(geo["positions"], idx, wts)):
        acc = np.zeros(3)
        p = np.array([pos[0], pos[1], pos[2], 1.0])
        for k in range(4):
            w = sw[k]
            if w == 0:
                continue
            b = si[k]
            m = pose_arm.get(b, np.eye(4)) @ inv_rest.get(b, np.eye(4))
            acc += w * (m @ p)[:3]
        out.append(tuple(acc))
    return out


def build_mesh(positions, geo):
    mesh = bpy.data.meshes.new("deagle_anim")
    mesh.from_pydata(
        [tuple(p) for p in positions],
        [],
        [tuple(t) for t in zip(*[iter(geo["indices"])] * 3)],
    )
    mesh.update()
    uv = mesh.uv_layers.new(name="UVMap")
    for loop in mesh.loops:
        uv.data[loop.index].uv = geo["uvs"][loop.vertex_index]
    obj = bpy.data.objects.new("DesertEagle", mesh)
    bpy.context.scene.collection.objects.link(obj)

    mat = bpy.data.materials.new("DesertEagle")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    tex_a = nodes.new("ShaderNodeTexImage")
    tex_a.image = bpy.data.images.load(os.path.join(TEX, "texture_00.png"))
    links.new(tex_a.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Metallic"].default_value = 0.85
    bsdf.inputs["Roughness"].default_value = 0.45
    obj.data.materials.append(mat)
    return obj


def main():
    os.makedirs(OUT, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)

    geo = json.load(open(GEO, encoding="utf-8"))["chunks"][0]
    names, parents, rest_local, poses = load_re()
    rest_arm = chain(rest_local, parents)

    scene = bpy.context.scene
    scene.render.resolution_x = rp.RES_X
    scene.render.resolution_y = rp.RES_Y
    scene.render.image_settings.file_format = "PNG"
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

    ok = 0
    for frame, tag in ((0, "frame00"), (5, "frame05_slideback")):
        pose_arm = chain(pose_local(poses, names, frame), parents)
        posed = skin_positions(geo, names, parents, rest_arm, pose_arm)
        obj = build_mesh(posed, geo)
        bpy.context.view_layer.update()
        pts = [obj.matrix_world @ v.co for v in obj.data.vertices]
        mn = Vector((min(p[i] for p in pts) for i in range(3)))
        mx = Vector((max(p[i] for p in pts) for i in range(3)))
        center = (mn + mx) / 2
        diag = (mx - mn).length
        rp.build_lights(scene, center, hero, up, diag)
        if rp.render_shot(scene, cam, f"anim/deagle_{tag}.png", hero, up, pts, center):
            ok += 1
        bpy.data.objects.remove(obj, do_unlink=True)

    print(f"ANIM_CHECK_RENDERS_DONE {ok}/2", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception:
        import traceback

        traceback.print_exc()
        print("ANIM_CHECK_RENDER_FAIL", flush=True)
        raise SystemExit(1)
