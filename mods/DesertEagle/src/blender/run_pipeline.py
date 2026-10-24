"""Pipeline entry point — run inside Blender.

Usage:
  blender --background --python run_pipeline.py -- --config configs/desert_eagle.json --stage all
  blender --background --python run_pipeline.py -- --config <json> --stage rig --stage export

Stages run in canonical order regardless of the order on the command line:
  import -> align -> rig -> lods -> export -> report

The script prints one line per stage and finishes with PIPELINE_OK (or exits
non-zero with PIPELINE_FAIL and the reason), so callers can assert on output.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import traceback

# Make the de_pipeline package importable when Blender runs this file directly.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from de_pipeline import STAGES  # noqa: E402
from de_pipeline import align as dp_align  # noqa: E402
from de_pipeline import export as dp_export  # noqa: E402
from de_pipeline import lods as dp_lods  # noqa: E402
from de_pipeline import report as dp_report  # noqa: E402
from de_pipeline import retarget as dp_retarget  # noqa: E402
from de_pipeline import rigging as dp_rigging  # noqa: E402
from de_pipeline import scene as dp_scene  # noqa: E402
from de_pipeline.config import load_config  # noqa: E402


class Pipeline:
    """Runs the Desert Eagle stages and keeps the objects between them."""

    def __init__(self, config):
        self.config = config
        self.report = dp_report.Report()
        self.source_objects = []
        self.template_objects = []

    # -- stages ----------------------------------------------------------

    def stage_import(self) -> dict:
        dp_scene.new_scene()
        self.source_objects = dp_scene.import_model(self.config.source_model_path)
        merged = dp_scene.merge_by_distance(self.source_objects)

        template = self.config.base_template_path
        if template:
            self.template_objects = dp_scene.import_model(template)

        return {
            "source_model": self.config.source_model_path,
            "base_template": template or None,
            "source_objects": [obj.name for obj in self.source_objects],
            "template_objects": [obj.name for obj in self.template_objects],
            "vertices_welded": merged,
            "scene": dp_scene.scene_stats(),
        }

    def stage_retarget(self) -> dict:
        """Rename source bones/vertex groups to the .rig bone names and drop
        junk animation actions (e.g. leftovers from other weapons)."""
        if not self.source_objects:
            raise RuntimeError("retarget needs the import stage first")
        config = self.config.retarget
        result = {}
        bone_map = dict(config.get("bone_map", {}))
        if bone_map:
            result["bones"] = dp_retarget.retarget_bones(
                self.source_objects,
                bone_map,
                armature_name=str(config.get("armature", "")),
            )
        drop_names = list(config.get("drop_objects", []))
        if drop_names:
            dropped, kept = dp_retarget.drop_objects(self.source_objects, drop_names)
            result["dropped_objects"] = dropped
            self.source_objects = kept
        result["actions"] = dp_retarget.prune_actions(
            keep_prefixes=list(config.get("keep_action_prefixes", [])),
            drop_substrings=list(config.get("drop_action_substrings", [])),
        )
        return result

    def stage_align(self) -> dict:
        if not self.source_objects:
            raise RuntimeError("align needs the import stage first")
        if not self.template_objects:
            raise RuntimeError("align needs a base_template in the config")
        return dp_align.align_objects(
            self.source_objects, self.template_objects, self.config.align
        )

    def stage_rig(self) -> dict:
        if not self.source_objects:
            raise RuntimeError("rig needs the import stage first")
        bone_names = self.config.rig.get("bones") or None
        return dp_rigging.rig_objects(
            self.source_objects, self.config.rig, bone_names=bone_names
        )

    def stage_lods(self) -> dict:
        if not self.source_objects:
            raise RuntimeError("lods needs the import stage first")
        names = dp_lods.duplicate_for_lods(
            self.source_objects, self.config.lod_levels, self.config.lod_naming
        )
        return {
            "levels": names,
            "problems": dp_lods.validate_lods(self.config.lod_levels, self.config.lod_naming),
        }

    def stage_export(self) -> dict:
        out_dir = self.config.out_path
        os.makedirs(out_dir, exist_ok=True)
        glb = dp_export.export_glb(
            os.path.join(out_dir, self.config.export_filename()),
            with_materials=bool(self.config.export.get("with_materials", True)),
            with_rig=bool(self.config.export.get("with_rig", True)),
        )
        blend = dp_export.save_blend(os.path.join(out_dir, "desert_eagle_work.blend"))
        return {"glb": glb, "blend": blend}

    def stage_report(self, report_path: str) -> dict:
        path = self.report.save(report_path)
        return {"report_path": path}

    # -- driver ----------------------------------------------------------

    def run(self, stages, report_path: str) -> None:
        ordered = [name for name in STAGES if name in stages]
        for name in ordered:
            try:
                if name == "report":
                    result = self.stage_report(report_path)
                else:
                    result = getattr(self, f"stage_{name}")()
                self.report.stage(name, result)
                print(f"STAGE {name} OK")
            except Exception as exc:  # noqa: BLE001 - pipeline must fail loudly
                self.report.stage(name, {"error": str(exc)})
                self.report.save(report_path)
                print(f"STAGE {name} FAIL: {exc}")
                traceback.print_exc()
                print("PIPELINE_FAIL")
                raise SystemExit(1)


def parse_args(argv):
    parser = argparse.ArgumentParser(prog="de-pipeline")
    parser.add_argument("--config", required=True, help="pipeline config JSON")
    parser.add_argument("--stage", action="append", default=[], help="stage name or 'all'")
    parser.add_argument("--report", default=None, help="where to write the JSON report")
    return parser.parse_args(argv)


def main() -> None:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else sys.argv[1:]
    args = parse_args(argv)

    stages = set()
    for entry in args.stage or ["all"]:
        if entry == "all":
            stages.update(STAGES)
        elif entry in STAGES:
            stages.add(entry)
        else:
            print(f"unknown stage: {entry} (valid: {STAGES})")
            print("PIPELINE_FAIL")
            raise SystemExit(2)

    config = load_config(args.config)
    report_path = args.report or os.path.join(config.out_path, "pipeline_report.json")

    print(f"PIPELINE_START stages={sorted(stages)}")
    pipeline = Pipeline(config)
    pipeline.run(stages, report_path)
    print("PIPELINE_OK")


if __name__ == "__main__":
    main()
