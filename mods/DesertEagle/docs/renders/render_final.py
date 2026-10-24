"""Beauty render of the final Desert Eagle: our geometry + our CS2 textures.

Proves the UV/texture pairing visually: the packed mesh's materials point at
desert_eagle_bc.xbm / desert_eagle_n.xbm (CS2 maps) — here we rebuild that
look in Blender from the same sources (geometry.json + extracted PNGs).

Run: blender.exe --background --python render_final.py
Outputs to docs/renders/final/.
"""

from __future__ import annotations

import importlib.util
import json
import os

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
MOD_ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
GEO = os.path.join(MOD_ROOT, "assets", "work", "de_geometry.json")
TEX = os.path.join(MOD_ROOT, "assets", "work", "cs2_textures")
OUT = os.path.join(HERE, "final")

_spec = importlib.util.spec_from_file_location("rp", os.path.join(HERE, "render_preview.py"))
rp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rp)


def build_scene():
    geo = json.load(open(GEO, encoding="utf-8"))["chunks"][0]

    # textures: texture_00 = albedo, texture_01 = normal (from glb_textures.py)
    albedo = bpy.data.images.load(os.path.join(TEX, "texture_00.png"))
    normal = bpy.data.images.load(os.path.join(TEX, "texture_01.png"))

    mat = bpy.data.materials.new("DesertEagle")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")

    tex_a = nodes.new("ShaderNodeTexImage")
    tex_a.image = albedo
    tex_a.location = (-600, 300)
    links.new(tex_a.outputs["Color"], bsdf.inputs["Base Color"])

    tex_n = nodes.new("ShaderNodeTexImage")
    tex_n.image = normal
    tex_n.location = (-600, -100)
    nmap = nodes.new("ShaderNodeNormalMap")
    nmap.location = (-300, -100)
    links.new(tex_n.outputs["Color"], nmap.inputs["Color"])
    links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])

    bsdf.inputs["Metallic"].default_value = 0.85
    bsdf.inputs["Roughness"].default_value = 0.45

    mesh = bpy.data.meshes.new("deagle")
    mesh.from_pydata(
        [tuple(p) for p in geo["positions"]],
        [],
        [tuple(t) for t in zip(*[iter(geo["indices"])] * 3)],
    )
    mesh.update()
    uv = mesh.uv_layers.new(name="UVMap")
    for loop in mesh.loops:
        uv.data[loop.index].uv = geo["uvs"][loop.vertex_index]
    obj = bpy.data.objects.new("DesertEagle", mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(mat)
    return [obj]


def main():
    os.makedirs(OUT, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    meshes = build_scene()

    pts = []
    for obj in meshes:
        mw = obj.matrix_world
        pts.extend((mw @ v.co) for v in obj.data.vertices)

    scene = bpy.context.scene
    scene.render.resolution_x = rp.RES_X
    scene.render.resolution_y = rp.RES_Y
    scene.render.image_settings.file_format = "PNG"

    rp.build_world(scene)
    mn = Vector((min(p[i] for p in pts) for i in range(3)))
    mx = Vector((max(p[i] for p in pts) for i in range(3)))
    center = (mn + mx) / 2
    diag = (mx - mn).length
    # hero view: front-right slightly above, same rule as the studio renders
    front = Vector((0, -1, 0))
    left = Vector((1, 0, 0))
    up = Vector((0, 0, 1))
    hero = (front * 0.72 + (-left) * 0.62 + up * 0.42).normalized()
    rp.build_lights(scene, center, hero, up, diag)

    cam_data = bpy.data.cameras.new("Cam")
    cam_data.lens = rp.LENS_MM
    cam_data.sensor_width = rp.SENSOR_W
    cam = bpy.data.objects.new("Cam", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam

    ok = 0
    for filename, view, up_hint in (
        ("final/deagle_final_34.png", hero, up),
        ("final/deagle_final_side.png", left, up),
    ):
        if rp.render_shot(scene, cam, filename, view, up_hint, pts, center):
            ok += 1

    print(f"FINAL_RENDERS_DONE {ok}/2", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception:
        import traceback

        traceback.print_exc()
        print("FINAL_RENDER_FAIL", flush=True)
        raise SystemExit(1)
