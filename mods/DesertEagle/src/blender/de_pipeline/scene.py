"""Scene helpers: clean start, model import, inventory of scene objects."""

from __future__ import annotations

import os

import bpy


# Extensions the pipeline knows how to import, and the operator that loads them.
IMPORTERS = {
    ".fbx": ("import_scene", "fbx"),
    ".obj": ("wm", "obj_import"),
    ".glb": ("import_scene", "gltf"),
    ".gltf": ("import_scene", "gltf"),
}


def new_scene() -> None:
    """Reset Blender to an empty scene (factory settings, no default cube)."""
    bpy.ops.wm.read_factory_settings(use_empty=True)


def import_model(path: str) -> list:
    """Import `path` and return the list of newly created top-level objects.

    Supported: .fbx, .obj, .glb, .gltf. Anything else raises ValueError so the
    failure is loud instead of silently producing an empty stage.
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"model not found: {path}")

    ext = os.path.splitext(path)[1].lower()
    if ext not in IMPORTERS:
        raise ValueError(f"unsupported model format '{ext}' (supported: {sorted(IMPORTERS)})")

    before = set(bpy.data.objects)
    module, operator = IMPORTERS[ext]

    # Blender renamed the OBJ importer in 4.x; fall back to the legacy one.
    try:
        getattr(getattr(bpy.ops, module), operator)(filepath=path)
    except Exception:
        if ext == ".obj" and operator == "obj_import":
            bpy.ops.import_scene.obj(filepath=path)
        else:
            raise

    imported = [obj for obj in bpy.data.objects if obj not in before]
    if not imported:
        raise RuntimeError(f"import produced no objects: {path}")
    return imported


def mesh_objects(objects=None) -> list:
    """Mesh datablock-backed objects, optionally filtered to `objects`."""
    pool = objects if objects is not None else list(bpy.data.objects)
    return [obj for obj in pool if obj.type == "MESH"]


def armature_objects(objects=None) -> list:
    pool = objects if objects is not None else list(bpy.data.objects)
    return [obj for obj in pool if obj.type == "ARMATURE"]


def scene_stats() -> dict:
    """Cheap numeric summary of the scene, used by the report stage."""
    meshes = mesh_objects()
    return {
        "objects": len(bpy.data.objects),
        "meshes": len(meshes),
        "armatures": len(armature_objects()),
        "vertices": sum(len(obj.data.vertices) for obj in meshes),
        "polygons": sum(len(obj.data.polygons) for obj in meshes),
        "materials": len(bpy.data.materials),
        "actions": len(bpy.data.actions),
        "names": sorted(obj.name for obj in bpy.data.objects),
    }


def merge_by_distance(objects, distance: float = 0.0001) -> int:
    """Weld coincident vertices on each mesh (Merge by Distance) and return
    the number of vertices removed. Runs without an edit-mode context so it is
    safe in `blender --background`."""
    import bmesh

    removed = 0
    for obj in mesh_objects(objects):
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        before = len(bm.verts)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=distance)
        removed += before - len(bm.verts)
        bm.to_mesh(obj.data)
        bm.free()
        obj.data.update()
    return removed
