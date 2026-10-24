"""LOD stage: every custom mesh must exist in LOD 0 *and* LOD 1.

REDengine 4 derives weapon hitboxes from the lower LOD meshes: replacing only
LOD 0 leaves an invisible, stale hitbox. This stage duplicates the finished
geometry into each LOD container using the configured naming pattern.
"""

from __future__ import annotations

import bpy


def _lod_collection(level: int):
    name = f"LOD_{level}"
    collection = bpy.data.collections.get(name)
    if collection is None:
        collection = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(collection)
    return collection


def duplicate_for_lods(source_objects, levels, naming: str = "{name}_LOD{level}") -> dict:
    """Copy `source_objects` once per LOD level. Copies keep their own mesh
    datablock (editing one LOD never silently edits another)."""
    result = {}
    for level in levels:
        collection = _lod_collection(int(level))
        names = []
        for obj in source_objects:
            if obj.type != "MESH":
                continue
            new_name = naming.format(name=_strip_lod_suffix(obj.name), level=level)
            copy = obj.copy()
            copy.data = obj.data.copy()
            copy.name = new_name
            collection.objects.link(copy)
            names.append(copy.name)
        result[str(level)] = names
    return result


def _strip_lod_suffix(name: str) -> str:
    """'slide_LOD0' -> 'slide' so re-runs do not stack suffixes."""
    marker = "_lod"
    lowered = name.lower()
    index = lowered.rfind(marker)
    if index > 0 and lowered[index + len(marker):].isdigit():
        return name[:index]
    return name


def validate_lods(levels, naming: str = "{name}_LOD{level}") -> list:
    """Return a list of problems (empty list = all LOD objects exist)."""
    problems = []
    for level in levels:
        collection = bpy.data.collections.get(f"LOD_{level}")
        if collection is None or not collection.objects:
            problems.append(f"LOD {level}: missing or empty collection")
    return problems
