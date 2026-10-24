"""Probe: what fraction of the camera frame does the CS2 gun actually occupy?"""

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

# world points of the evaluated (skinned) mesh
dg = bpy.context.evaluated_depsgraph_get()
pts = []
for obj in meshes:
    ev = obj.evaluated_get(dg)
    me = ev.to_mesh()
    pts.extend(ev.matrix_world @ v.co for v in me.vertices)
    ev.to_mesh_clear()

mn = Vector((min(p[i] for p in pts) for i in range(3)))
mx = Vector((max(p[i] for p in pts) for i in range(3)))
center = (mn + mx) / 2
diag = (mx - mn).length
print(f"PROBE pts={len(pts)} diag={diag:.4f} center={tuple(round(v,3) for v in center)}")

cam_data = bpy.data.cameras.new("cam")
cam = bpy.data.objects.new("cam", cam_data)
bpy.context.scene.collection.objects.link(cam)
bpy.context.scene.camera = cam
print(f"PROBE default lens={cam_data.lens} sensor={cam_data.sensor_width} fit={cam_data.sensor_fit} angle_x={cam_data.angle_x:.4f}")

scene = bpy.context.scene
scene.render.resolution_x = 1600
scene.render.resolution_y = 1000

cam_data.lens = 85.0
cam_data.sensor_width = 36.0
cam.location = Vector((5.4, 3.6, -6.4))
direction = center - cam.location
cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

print(f"PROBE lens=85 sensor=36 angle_x={cam_data.angle_x:.4f} angle_y={cam_data.angle_y:.4f}")

ndc = [world_to_camera_view(scene, cam, Vector(p)) for p in pts[::37]]
xs = [c.x for c in ndc]
ys = [c.y for c in ndc]
print(f"PROBE ndc_x={min(xs):.3f}..{max(xs):.3f} width={max(xs)-min(xs):.3f}")
print(f"PROBE ndc_y={min(ys):.3f}..{max(ys):.3f} height={max(ys)-min(ys):.3f}")
print("PROBE_OK")
