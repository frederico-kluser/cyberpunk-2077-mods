"""Bisect: patch the already-compressed weapon_empty clip and deserialize."""

import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))
import anims_write as aw

base = r"C:\Users\kluse\Projects\cyberpunk-2077\mods\DesertEagle\assets\_inventory\anims_json\w_handgun__tsunami_nue__base1.anims.json"
out = r"C:\Users\kluse\Projects\cyberpunk-2077\mods\DesertEagle\assets\work\anims_test"
os.makedirs(out, exist_ok=True)

joints = {
    0: {"position": [(0.0, (1.0, 2.0, 3.0))]},
    5: {
        "position": [(0.0, (0.0, 0.0, 0.0)), (0.033, (0.0, 0.0, 0.15))],
        "rotation": [(0.0, (0.0, 0.0, 0.0, 1.0)), (0.033, (0.0, 0.26, 0.0, 0.966))],
    },
}

for clip, duration, frames in (("weapon_empty", 0.0333333351, 2),):
    doc = json.load(open(base, encoding="utf-8"))
    r = aw.write_clip(doc, clip, joints, duration, frames)
    patched = os.path.join(out, f"bisect_{clip}.anims.json")
    json.dump(doc, open(patched, "w", encoding="utf-8"), indent=1)
    print("patched:", r)

    res = subprocess.run(
        [r"C:\Users\kluse\Tools\WolvenKit\9.1.0\wolvenkit-cli.cmd",
         "convert", "deserialize", patched, "-o", out, "-v", "Detailed"],
        capture_output=True, text=True)
    tail = "\n".join((res.stdout + res.stderr).splitlines()[-6:])
    ok = "Success" in (res.stdout + res.stderr)
    print(("BISECT_OK " if ok else "BISECT_FAIL ") + clip)
    if not ok:
        print(tail)
