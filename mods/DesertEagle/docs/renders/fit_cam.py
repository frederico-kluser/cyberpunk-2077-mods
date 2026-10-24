"""Empirical camera fit: converge camera distance until the gun fills 80% of the
frame, measured via world_to_camera_view on the EVALUATED mesh (with a proper
depsgraph update). Then renders one test frame."""

from __future__ import annotations

import os

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = os.path.join(HERE, "..", "..", "assets", "raw", "desert_eagle_cs2.glb")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=MODEL)
meshes = [o for o in bpy.data.objects if o.type == "MESH"]

dg = bpy.context.evaluated_depsgraph_get()
pts = []
for obj in meshes:
    ev = obj.evaluated_get(dg)
    me = ev.to_mesh()
    pts.extend((ev.matrix_world @ v.co).copy() for v in me.vertices)
    ev.to_mesh_clear()

mn = Vector((min(p[i] for p in pts) for i in range(3)))
mx = Vector((max(p[i] for p in pts) for i in range(3)))
center = (mn + mx) / 2
print(f"FIT diag={(mx-mn).length:.4f} center={tuple(round(v,3) for v in center)}")

scene = bpy.context.scene
scene.render.resolution_x = 1600
scene.render.resolution_y = 1000
cam_data = bpy.data.cameras.new("cam")
cam_data.lens = 85.0
cam_data.sensor_width = 36.0
cam = bpy.data.objects.new("cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam

view_dir = Vector((0.597, 0.404, -0.693)).normalized()  # hero
up_hint = Vector((0, 0, 1))


def ndc_extent(dist):
    cam.location = center + view_dir * dist
    d = (center - cam.location).normalized()
    right = d.cross(up_hint).normalized()
    upv = right.cross(d).normalized()
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    bpy.context.view_layer.update()  # <-- the missing step
    xs, ys = [], []
    for p in pts[::23]:
        c = world_to_camera_view(scene, cam, Vector(p))
        xs.append(c.x)
        ys.append(c.y)
    return max(xs) - min(xs), max(ys) - min(ys), min(xs), max(xs), min(ys), max(ys)


dist = 1.0
for i in range(12):
    w, h, x0, x1, y0, y1 = ndc_extent(dist)
    print(f"FIT iter={i} dist={dist:.3f} ndc_w={w:.3f} ndc_h={h:.3f}")
    biggest = max(w, h)
    if abs(biggest - 0.8) < 0.01:
        break
    dist *= biggest / 0.8

w, h, x0, x1, y0, y1 = ndc_extent(dist)
print(f"FIT final dist={dist:.3f} ndc_x={x0:.3f}..{x1:.3f} ndc_y={y0:.3f}..{y1:.3f}")

# studio + one test render
world = bpy.data.worlds.new("W")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[1].default_value = 0.3
for name, loc, energy in (
    ("key", center + view_dir * 2 - Vector((3, 0, 3)), 3000),
    ("fill", center + view_dir * 3 + Vector((3, 0, 1)), 1500),
    ("rim", center - view_dir * 3 + Vector((0, 0, 3)), 3500),
):
    ld = bpy.data.lights.new(name, "AREA")
    ld.energy = energy
    ld.size = 4.0
    lo = bpy.data.objects.new(name, ld)
    lo.location = loc
    scene.collection.objects.link(lo)
    lo.rotation_euler = (center - lo.location).to_track_quat("-Z", "Y").to_euler()

scene.render.image_settings.file_format = "PNG"
scene.render.filepath = os.path.join(HERE, "cs2", "cs2_fit_test.png")
bpy.ops.render.render(write_still=True)
print("FIT_RENDER_OK", scene.render.filepath)
print("FIT_OK")
