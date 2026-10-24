"""De-pipeline: automated Blender stages for the Desert Eagle weapon mod.

Each module is pure bpy logic that also runs in `blender --background`, so the
whole pipeline is scriptable and testable without a GUI.

Stages (see run_pipeline.py):
  import  - load source model + base template into a clean scene
  align   - bounding-box driven scale/rotate/translate onto the template
  rig     - vertex groups per .rig bone name, weight limit 8, normalization
  lods    - duplicate final geometry into LOD 0 and LOD 1 containers
  export  - write .glb for WolvenKit (Cyberpunk IO Suite exporter if present)
  report  - JSON summary of every stage
"""

__version__ = "0.1.0"

STAGES = ("import", "align", "rig", "lods", "export", "report")
