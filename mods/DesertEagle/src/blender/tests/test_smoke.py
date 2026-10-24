"""End-to-end smoke test for the Desert Eagle pipeline — run inside Blender.

  blender --background --python tests/test_smoke.py

It builds a synthetic weapon (three parts: slide, magazine, trigger) and a
synthetic base template, exports both to .glb, then drives the REAL Pipeline
(import -> align -> rig -> lods -> export -> report) over them and asserts the
contracts the REDengine 4 rules require:

  * uniform scale + anchor coincidence after alignment;
  * vertex groups named exactly Trigger/Slide/Magazine with weight 1.0;
  * no vertex left without weights; at most 8 influences per vertex;
  * LOD 0 and LOD 1 collections both populated (hitbox rule);
  * .glb export and JSON report written to disk.

Prints SMOKE_TEST_OK on success; prints SMOKE_TEST_FAIL and exits 1 otherwise.
"""

from __future__ import annotations

import json
import math
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bpy  # noqa: E402

from de_pipeline import align as dp_align  # noqa: E402
from de_pipeline import report as dp_report  # noqa: E402
from de_pipeline.config import PipelineConfig, load_config  # noqa: E402
from de_pipeline.scene import mesh_objects  # noqa: E402
from run_pipeline import Pipeline  # noqa: E402


TOLERANCE = 1e-3
FAILURES = []


def check(condition: bool, message: str) -> None:
    if condition:
        print(f"  [OK]   {message}")
    else:
        print(f"  [FAIL] {message}")
        FAILURES.append(message)


# ---------------------------------------------------------------------------
# synthetic input models
# ---------------------------------------------------------------------------

def build_source_model() -> None:
    """Three hard-mechanical parts at a wrong scale and position."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    parts = {
        "deagle_slide": (10.0, 5.0, 3.0),
        "deagle_mag": (11.0, 5.0, 3.0),
        "deagle_trigger": (12.0, 5.0, 3.0),
    }
    for name, location in parts.items():
        bpy.ops.mesh.primitive_cube_add(size=0.5, location=location)
        bpy.context.active_object.name = name


def build_template_model() -> None:
    """The vanilla weapon stand-in: one block of a different size."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0.0, 0.0, 0.0))
    bpy.context.active_object.name = "w_handgun_nue_template"


def export_scene(path: str) -> None:
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB")


# ---------------------------------------------------------------------------
# the test
# ---------------------------------------------------------------------------

def main() -> None:
    workdir = tempfile.mkdtemp(prefix="de_pipeline_smoke_")
    source_path = os.path.join(workdir, "source_deagle.glb")
    template_path = os.path.join(workdir, "template_nue.glb")
    config_path = os.path.join(workdir, "config.json")
    report_path = os.path.join(workdir, "pipeline_report.json")

    print(f"smoke: workdir = {workdir}")

    build_source_model()
    export_scene(source_path)
    build_template_model()
    export_scene(template_path)
    check(os.path.isfile(source_path), "synthetic source model exported")
    check(os.path.isfile(template_path), "synthetic template model exported")

    config = {
        "project_root": workdir,
        "source_model": source_path,
        "base_template": template_path,
        "out_dir": os.path.join(workdir, "out"),
        "align": {
            "match_bbox": True,
            "scale_mode": "diagonal",
            "anchor_source": "bbox_min",
            "anchor_template": "bbox_min",
        },
        "rig": {
            "max_influences": 8,
            "weights": 1.0,
            "bones": ["Slide", "Magazine", "Trigger"],
            "vertex_groups": {
                "Slide": ["deagle_slide"],
                "Magazine": ["deagle_mag"],
                "Trigger": ["deagle_trigger"],
            },
        },
        "lods": {"levels": [0, 1], "naming": "{name}_LOD{level}"},
        "export": {
            "filename": "w_handgun_desert_eagle.glb",
            "with_materials": True,
            "with_rig": True,
        },
    }
    with open(config_path, "w", encoding="utf-8") as handle:
        json.dump(config, handle, indent=2)

    # ---- run the real pipeline -----------------------------------------
    pipeline = Pipeline(load_config(config_path))
    try:
        pipeline.run({"import", "align", "rig", "lods", "export", "report"}, report_path)
    except SystemExit:
        check(False, "pipeline completed without SystemExit")
        print("SMOKE_TEST_FAIL")
        raise SystemExit(1)

    # ---- contracts ------------------------------------------------------
    stats = pipeline.report.data["stages"]
    check("import" in stats and "error" not in stats["import"], "import stage ran")

    source_meshes = mesh_objects(pipeline.source_objects)
    tpl_meshes = mesh_objects(pipeline.template_objects)
    src_min, src_max = dp_align.world_bbox(source_meshes)
    tpl_min, tpl_max = dp_align.world_bbox(tpl_meshes)

    diag_src = (src_max - src_min).length
    diag_tpl = (tpl_max - tpl_min).length
    check(
        abs(diag_src - diag_tpl) <= TOLERANCE,
        f"uniform scale matched bbox diagonals ({diag_src:.4f} vs {diag_tpl:.4f})",
    )
    delta = (src_min - tpl_min).length
    check(delta <= TOLERANCE, f"anchor points coincide (delta={delta:.6f})")

    # rig contracts
    rig_result = stats.get("rig", {})
    check(not rig_result.get("unweighted_vertices"), "no unweighted vertices")
    for bone in ("Slide", "Magazine", "Trigger"):
        assigned = rig_result.get("assigned", {}).get(bone, {})
        check(bool(assigned.get("vertices")), f"vertex group '{bone}' has weights")
    for obj in source_meshes:
        for vertex in obj.data.vertices:
            total = sum(entry.weight for entry in vertex.groups)
            if vertex.groups:
                check(
                    abs(total - 1.0) <= TOLERANCE,
                    f"weights normalized on {obj.name}:{vertex.index} (sum={total:.3f})",
                )
            check(
                len(vertex.groups) <= 8,
                f"influence limit respected on {obj.name}:{vertex.index}",
            )

    # LOD contracts (REDengine hitbox rule)
    for level in (0, 1):
        collection = bpy.data.collections.get(f"LOD_{level}")
        check(
            collection is not None and len(collection.objects) == 3,
            f"LOD_{level} holds all 3 parts",
        )

    # export contracts
    glb = stats.get("export", {}).get("glb", {})
    check(glb.get("bytes", 0) > 0, f".glb exported ({glb.get('bytes', 0)} bytes)")
    check(os.path.isfile(report_path), "JSON report written")

    if FAILURES:
        print(f"SMOKE_TEST_FAIL ({len(FAILURES)} problem(s))")
        raise SystemExit(1)
    print("SMOKE_TEST_OK")


if __name__ == "__main__":
    main()
