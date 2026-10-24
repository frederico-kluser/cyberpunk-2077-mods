"""Export stage: write the finished mesh as .glb for WolvenKit.

Preference order:
  1. the WolvenKit Cyberpunk Blender add-on (IO Suite) exporter, when its
     operator is registered — it writes exactly what WolvenKit wants to import
     back into the .mesh container;
  2. Blender's built-in glTF exporter (also accepted by WolvenKit).
"""

from __future__ import annotations

import hashlib
import os
import re

import bpy


def find_cyberpunk_exporter():
    """Return (module, operator) for the IO Suite exporter, or None."""
    pattern = re.compile(r"(cp2077|cyberpunk|wolvenkit|wk_)", re.IGNORECASE)
    for module_name in dir(bpy.ops):
        if not pattern.search(module_name):
            continue
        module = getattr(bpy.ops, module_name)
        for operator_name in dir(module):
            if "export" not in operator_name.lower():
                continue
            if pattern.search(operator_name) or pattern.search(module_name):
                return module_name, operator_name
    return None


def export_glb(filepath: str, with_materials: bool = True, with_rig: bool = True) -> dict:
    """Export the whole scene to `filepath` (.glb). Returns export metadata."""
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)

    exporter = find_cyberpunk_exporter()
    used = "gltf"
    if exporter is not None:
        module_name, operator_name = exporter
        try:
            getattr(getattr(bpy.ops, module_name), operator_name)(filepath=filepath)
            used = f"{module_name}.{operator_name}"
        except Exception:
            exporter = None  # fall through to the built-in exporter

    if exporter is None:
        bpy.ops.export_scene.gltf(
            filepath=filepath,
            export_format="GLB",
            export_materials="EXPORT" if with_materials else "NONE",
            export_skins=with_rig,
            export_animations=True,
        )

    if not os.path.isfile(filepath):
        raise RuntimeError(f"export produced no file: {filepath}")

    with open(filepath, "rb") as handle:
        digest = hashlib.sha256(handle.read()).hexdigest()

    return {
        "path": filepath,
        "bytes": os.path.getsize(filepath),
        "sha256": digest,
        "exporter": used,
    }


def save_blend(filepath: str) -> str:
    """Save the working .blend next to the export (debug artifact)."""
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=filepath)
    return filepath
