"""Extract sample frames from the rendered MP4 via the VSE (works in Blender 5.x)."""

import bpy
import os

HERE = os.path.dirname(os.path.abspath(__file__))
MP4 = os.path.join(HERE, "deagle_reload.mp4")

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.sequence_editor_create()
se = scene.sequence_editor

new_movie = getattr(getattr(se, "strips", None), "new_movie", None) or se.sequences.new_movie
strip = new_movie("reload", MP4, 1, 1)

scene.render.resolution_x = 1280
scene.render.resolution_y = 800
scene.render.image_settings.file_format = "PNG"
scene.render.use_sequencer = True

for frame in (1, 50, 100):
    scene.frame_start = frame
    scene.frame_end = frame
    scene.frame_set(frame)
    scene.render.filepath = os.path.join(HERE, f"deagle_reload_f{frame:03d}.png")
    bpy.ops.render.render(write_still=True)
    print("saved", scene.render.filepath)
print("VIDEO_FRAMES_OK")
