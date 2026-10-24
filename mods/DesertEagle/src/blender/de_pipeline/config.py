"""Pipeline configuration: one JSON file drives every stage.

Example config (see configs/desert_eagle.json):

{
  "project_root": "C:/path/to/mods/DesertEagle",
  "source_model": "assets/raw/desert_eagle.fbx",
  "base_template": "assets/extracted/w_handgun_nue.glb",
  "out_dir": "assets/work",
  "units_per_meter": 1.0,
  "align": {
    "anchor_source": "grip",
    "anchor_template": "grip",
    "match_bbox": true
  },
  "rig": {
    "armature": "w_handgun_nue_rig",
    "max_influences": 8,
    "vertex_groups": {
      "Slide": ["slide", "barrel_slide"],
      "Magazine": ["mag", "magazine"],
      "Trigger": ["trigger", "trigger_guard"]
    },
    "weights": 1.0
  },
  "lods": {
    "levels": [0, 1],
    "naming": "{name}_LOD{level}"
  },
  "export": {
    "filename": "w_handgun_desert_eagle.glb",
    "with_materials": true,
    "with_rig": true
  }
}
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any


@dataclass
class PipelineConfig:
    project_root: str
    source_model: str = ""
    base_template: str = ""
    out_dir: str = "assets/work"
    units_per_meter: float = 1.0
    align: dict = field(default_factory=dict)
    rig: dict = field(default_factory=dict)
    lods: dict = field(default_factory=dict)
    export: dict = field(default_factory=dict)
    raw: dict = field(default_factory=dict)

    # ---- helpers -------------------------------------------------------

    def path(self, relative: str) -> str:
        """Absolute path for `relative`, resolved against the project root."""
        if not relative:
            return ""
        if os.path.isabs(relative):
            return os.path.normpath(relative)
        return os.path.normpath(os.path.join(self.project_root, relative))

    @property
    def out_path(self) -> str:
        return self.path(self.out_dir)

    @property
    def source_model_path(self) -> str:
        return self.path(self.source_model)

    @property
    def base_template_path(self) -> str:
        return self.path(self.base_template)

    @property
    def max_influences(self) -> int:
        return int(self.rig.get("max_influences", 8))

    @property
    def vertex_groups(self) -> dict:
        """Map of .rig bone name -> list of source object/part names."""
        return dict(self.rig.get("vertex_groups", {}))

    @property
    def lod_levels(self) -> list:
        return list(self.lods.get("levels", [0, 1]))

    @property
    def lod_naming(self) -> str:
        return str(self.lods.get("naming", "{name}_LOD{level}"))

    def export_filename(self) -> str:
        return str(self.export.get("filename", "w_handgun_desert_eagle.glb"))


def load_config(path: str) -> PipelineConfig:
    """Load a pipeline config JSON file."""
    with open(path, "r", encoding="utf-8") as handle:
        data: dict[str, Any] = json.load(handle)

    known = {
        "project_root",
        "source_model",
        "base_template",
        "out_dir",
        "units_per_meter",
        "align",
        "rig",
        "lods",
        "export",
    }
    kwargs = {key: data[key] for key in known if key in data}
    if "project_root" not in kwargs:
        # Default to the mod folder that contains this source tree.
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        kwargs["project_root"] = os.path.dirname(os.path.dirname(here))

    return PipelineConfig(raw=data, **kwargs)
