"""Report stage: one JSON file describing everything the pipeline did."""

from __future__ import annotations

import datetime
import json
import os


class Report:
    """Collects per-stage results and writes them as one JSON document."""

    def __init__(self, pipeline_name: str = "desert-eagle"):
        self.data = {
            "pipeline": pipeline_name,
            "started": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "stages": {},
        }

    def stage(self, name: str, result) -> None:
        self.data["stages"][name] = result

    def note(self, message: str) -> None:
        self.data.setdefault("notes", []).append(message)

    def save(self, path: str) -> str:
        self.data["finished"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(self.data, handle, indent=2, ensure_ascii=False)
        return os.path.abspath(path)

    def as_json(self) -> str:
        return json.dumps(self.data, indent=2, ensure_ascii=False)
