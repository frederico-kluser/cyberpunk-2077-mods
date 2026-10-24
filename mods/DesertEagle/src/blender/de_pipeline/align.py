"""Alignment stage: put the source model exactly over the base template.

REDengine 4 needs the new weapon to sit where the vanilla one sits: same grip
position, same trigger position, same overall scale. This stage does that with
data, not eyeballing:

  1. compute world-space bounding boxes of source and template;
  2. apply a uniform scale so the sizes match (config: align.match_bbox,
     align.scale_mode = "diagonal" (default) or "mean");
  3. translate so the configured anchor points coincide.

Anchors can be:
  "bbox_min" | "bbox_center" | "bbox_max"   - corners/centers of the bbox
  "object:<name>"                           - origin of a named object/empty
"""

from __future__ import annotations

import math

import mathutils


def world_bbox(objects) -> tuple:
    """World-space (min, max) corners across the given objects."""
    mins = mathutils.Vector((math.inf, math.inf, math.inf))
    maxs = mathutils.Vector((-math.inf, -math.inf, -math.inf))

    for obj in objects:
        for corner in obj.bound_box:
            world = obj.matrix_world @ mathutils.Vector(corner)
            for axis in range(3):
                mins[axis] = min(mins[axis], world[axis])
                maxs[axis] = max(maxs[axis], world[axis])

    if not math.isfinite(mins[0]):
        raise ValueError("cannot compute bounding box of an empty selection")
    return mins, maxs


def anchor_point(objects, anchor: str) -> mathutils.Vector:
    """Resolve an anchor spec to a world-space point."""
    anchor = (anchor or "bbox_min").strip()

    if anchor.startswith("object:"):
        name = anchor.split(":", 1)[1]
        for obj in objects:
            if obj.name == name:
                return obj.matrix_world.translation.copy()
        raise ValueError(f"anchor object not found: {name}")

    mins, maxs = world_bbox(objects)
    if anchor == "bbox_min":
        return mins.copy()
    if anchor == "bbox_center":
        return (mins + maxs) / 2.0
    if anchor == "bbox_max":
        return maxs.copy()
    raise ValueError(f"unknown anchor spec: {anchor}")


def align_objects(source_objects, template_objects, config: dict) -> dict:
    """Scale/translate `source_objects` onto `template_objects` in place.

    Returns a dict describing the applied transform (goes into the report).
    """
    import bpy

    config = config or {}
    match_bbox = bool(config.get("match_bbox", True))
    source_anchor = config.get("anchor_source", "bbox_min")
    template_anchor = config.get("anchor_template", "bbox_min")

    src_min, src_max = world_bbox(source_objects)
    tpl_min, tpl_max = world_bbox(template_objects)

    src_size = src_max - src_min
    tpl_size = tpl_max - tpl_min

    scale = 1.0
    if match_bbox:
        # Uniform scale — a pistol must never be stretched per axis or the
        # REDengine hitbox math goes wrong. Default metric is the bounding-box
        # diagonal (robust when one axis of the source is very thin); "mean"
        # averages the per-axis ratios instead.
        scale_mode = str(config.get("scale_mode", "diagonal"))
        if scale_mode == "diagonal":
            src_diag = src_size.length
            tpl_diag = tpl_size.length
            if src_diag <= 1e-9:
                raise ValueError("source bounding box is degenerate")
            scale = tpl_diag / src_diag
        elif scale_mode == "mean":
            ratios = [
                tpl_size[axis] / src_size[axis]
                for axis in range(3)
                if src_size[axis] > 1e-9
            ]
            if not ratios:
                raise ValueError("source bounding box is degenerate")
            scale = sum(ratios) / len(ratios)
        else:
            raise ValueError(f"unknown scale_mode: {scale_mode}")
        if not math.isfinite(scale) or scale <= 0:
            raise ValueError(f"computed nonsense scale: {scale}")

    pivot = anchor_point(source_objects, source_anchor)

    # 1) uniform scale around the source anchor
    scale_matrix = mathutils.Matrix.Scale(scale, 4)
    for obj in source_objects:
        obj.matrix_world = (
            mathutils.Matrix.Translation(pivot)
            @ scale_matrix
            @ mathutils.Matrix.Translation(-pivot)
            @ obj.matrix_world
        )

    # 2) translate so both anchors coincide
    source_anchor_now = anchor_point(source_objects, source_anchor)
    target_anchor = anchor_point(template_objects, template_anchor)
    delta = target_anchor - source_anchor_now
    for obj in source_objects:
        obj.matrix_world = mathutils.Matrix.Translation(delta) @ obj.matrix_world

    bpy.context.view_layer.update()

    return {
        "scale": round(scale, 6),
        "translation": [round(v, 6) for v in delta],
        "source_anchor": source_anchor,
        "template_anchor": template_anchor,
        "source_bbox_min": [round(v, 6) for v in src_min],
        "source_bbox_max": [round(v, 6) for v in src_max],
        "template_bbox_min": [round(v, 6) for v in tpl_min],
        "template_bbox_max": [round(v, 6) for v in tpl_max],
    }
