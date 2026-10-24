"""Rigging stage: vertex groups named exactly like the .rig bone names.

REDengine 4 binds mesh vertices to the weapon skeleton purely by name: every
vertex group must match a bone in the .rig, and everything else is a runtime
deformation bug. This stage therefore:

  * creates one vertex group per bone and assigns the configured parts to it
    with full weight (1.0) — the REDengine rule for hard-mechanical parts like
    Slide, Magazine and Trigger;
  * deletes inherited vertex groups whose names do not exist in the .rig;
  * limits every vertex to `max_influences` (8) weights and normalizes them
    (Limit Total + Normalize All with Lock Active off, done in pure Python so
    it behaves identically in `blender --background`).
"""

from __future__ import annotations


def matching_objects(objects, tokens) -> list:
    """Objects whose name contains any of the given tokens (case-insensitive)."""
    wanted = [token.lower() for token in tokens]
    hits = []
    for obj in objects:
        name = obj.name.lower()
        if any(token in name for token in wanted):
            hits.append(obj)
    return hits


def assign_vertex_groups(objects, mapping: dict, weight: float = 1.0) -> dict:
    """Create one vertex group per bone name and paint whole objects into it.

    `mapping` is {bone_name: [object-name tokens]}. Returns per-bone stats.
    """
    stats = {}
    for bone_name, tokens in mapping.items():
        targets = matching_objects(objects, tokens)
        touched_vertices = 0
        for obj in targets:
            if obj.type != "MESH":
                continue
            group = obj.vertex_groups.get(bone_name) or obj.vertex_groups.new(name=bone_name)
            indices = list(range(len(obj.data.vertices)))
            group.add(indices, float(weight), "REPLACE")
            touched_vertices += len(indices)
        stats[bone_name] = {
            "objects": [obj.name for obj in targets],
            "vertices": touched_vertices,
        }
    return stats


def drop_unknown_groups(objects, bone_names) -> list:
    """Remove vertex groups that have no matching .rig bone (engine rule)."""
    known = set(bone_names)
    removed = []
    for obj in objects:
        if obj.type != "MESH":
            continue
        for group in list(obj.vertex_groups):
            if group.name not in known:
                removed.append(f"{obj.name}:{group.name}")
                obj.vertex_groups.remove(group)
    return removed


def limit_influences(objects, max_influences: int = 8) -> int:
    """Keep only the N heaviest weights per vertex. Returns vertices trimmed."""
    trimmed = 0
    for obj in objects:
        if obj.type != "MESH":
            continue
        for vertex in obj.data.vertices:
            groups = list(vertex.groups)
            if len(groups) <= max_influences:
                continue
            keep = sorted(groups, key=lambda g: g.weight, reverse=True)[:max_influences]
            keep_ids = {g.group for g in keep}
            for entry in groups:
                if entry.group not in keep_ids:
                    obj.vertex_groups[entry.group].remove([vertex.index])
            trimmed += 1
        obj.data.update()
    return trimmed


def normalize_weights(objects) -> int:
    """Normalize every vertex's weights to sum 1.0. Returns vertices touched."""
    touched = 0
    for obj in objects:
        if obj.type != "MESH":
            continue
        changed = False
        for vertex in obj.data.vertices:
            entries = list(vertex.groups)
            total = sum(entry.weight for entry in entries)
            if total <= 1e-9:
                continue
            if abs(total - 1.0) <= 1e-6:
                continue
            for entry in entries:
                obj.vertex_groups[entry.group].add(
                    [vertex.index], entry.weight / total, "REPLACE"
                )
            touched += 1
            changed = True
        if changed:
            obj.data.update()
    return touched


def unweighted_vertices(objects, bone_names) -> list:
    """Vertices that have no weight in any known bone group (engine crash risk)."""
    known = set(bone_names)
    problems = []
    for obj in objects:
        if obj.type != "MESH":
            continue
        known_ids = {
            obj.vertex_groups[name].index
            for name in known
            if name in obj.vertex_groups
        }
        for vertex in obj.data.vertices:
            if not any(entry.group in known_ids for entry in vertex.groups):
                problems.append(f"{obj.name}:{vertex.index}")
    return problems


def rig_objects(objects, config: dict, bone_names=None) -> dict:
    """Run the whole rigging stage. `bone_names` is the .rig bone list when
    known; when omitted, the vertex-group mapping keys are used."""
    mapping = dict(config.get("vertex_groups", {}))
    known = list(bone_names) if bone_names else list(mapping.keys())
    weight = float(config.get("weights", 1.0))
    max_influences = int(config.get("max_influences", 8))

    assigned = assign_vertex_groups(objects, mapping, weight)
    removed = drop_unknown_groups(objects, known)
    trimmed = limit_influences(objects, max_influences)
    normalized = normalize_weights(objects)
    problems = unweighted_vertices(objects, known)

    return {
        "assigned": assigned,
        "dropped_groups": removed,
        "vertices_trimmed": trimmed,
        "vertices_normalized": normalized,
        "unweighted_vertices": problems,
        "max_influences": max_influences,
    }
