"""Retarget stage: rename source bones/vertex groups to the .rig bone names.

The CS2 Desert Eagle ships pre-skinned with its own bone names
(`v_weapon_deagle_slide_0`, `v_weapon_deagle_trigger_1`,
`v_weapon_deagle_clip_2`, `v_weapon_deagle_hammer_3`, `weapon_hand_r_4`,
`GLTF_created_0_rootJoint`). REDengine 4 binds purely by name, so the whole
retarget is a faithful rename of:

  * mesh vertex groups (the skinning),
  * armature bones (the skeleton, including their hierarchy),
  * nothing else — the animation curves follow automatically because
    `fcurve.data_path` references the bone by name and Blender updates the
    paths when bones are renamed through the API.

This preserves every weight exactly — no re-sampling, no distortion — which is
safer than any transfer-based retarget for hard-mechanical parts.
"""

from __future__ import annotations


def retarget_bones(objects, bone_map: dict, armature_name: str = "") -> dict:
    """Rename vertex groups and armature bones per `bone_map` ({old: new}).

    Returns a report: renamed groups/bones, unknown names, collisions.
    """
    renamed_groups = {}
    unknown_groups = []
    renamed_bones = {}
    unknown_bones = []

    # 1) mesh vertex groups
    for obj in objects:
        if obj.type != "MESH":
            continue
        for group in obj.vertex_groups:
            if group.name in bone_map:
                new_name = bone_map[group.name]
                old = group.name
                group.name = new_name
                renamed_groups.setdefault(old, new_name)
            elif group.name not in bone_map.values():
                unknown_groups.append(f"{obj.name}:{group.name}")

    # 2) armature bones (keep hierarchy — Blender fixes constraints/paths)
    for obj in objects:
        if obj.type != "ARMATURE":
            continue
        if armature_name and obj.name != armature_name:
            continue
        for bone in obj.data.bones:
            if bone.name in bone_map:
                new_name = bone_map[bone.name]
                old = bone.name
                bone.name = new_name
                renamed_bones.setdefault(old, new_name)
            elif bone.name not in bone_map.values():
                unknown_bones.append(bone.name)

    # 3) collisions: two groups renamed onto the same target on one object
    collisions = []
    for obj in objects:
        if obj.type != "MESH":
            continue
        seen = set()
        for group in obj.vertex_groups:
            if group.name in seen:
                collisions.append(f"{obj.name}:{group.name}")
            seen.add(group.name)

    return {
        "renamed_groups": renamed_groups,
        "renamed_bones": renamed_bones,
        "unknown_groups": unknown_groups,
        "unknown_bones": unknown_bones,
        "collisions": collisions,
    }


def drop_objects(objects, names):
    """Delete stray objects by exact name (exporter junk, e.g. 'Icosphere').

    Returns (dropped_names, kept_objects).
    """
    import bpy

    wanted = set(names)
    dropped, kept = [], []
    for obj in list(objects):
        if obj.name in wanted:
            dropped.append(obj.name)
            bpy.data.objects.remove(obj, do_unlink=True)
        else:
            kept.append(obj)
    return dropped, kept


def prune_actions(keep_prefixes, drop_substrings=None) -> dict:
    """Delete animation actions whose name matches nothing in `keep_prefixes`.

    The CS2 file carries junk actions from other weapons (names containing
    'awp') — those must not reach the export.
    """
    import bpy

    drop_substrings = [s.lower() for s in (drop_substrings or [])]
    kept, dropped = [], []
    for action in list(bpy.data.actions):
        name = action.name
        low = name.lower()
        if any(sub in low for sub in drop_substrings):
            bpy.data.actions.remove(action)
            dropped.append(name)
            continue
        if keep_prefixes and not any(name.startswith(p) for p in keep_prefixes):
            bpy.data.actions.remove(action)
            dropped.append(name)
            continue
        kept.append(name)
    return {"kept": kept, "dropped": dropped}
