"""Micro-bisect: change ONLY the inner duration of recoil_shoulder."""

import json
import os
import subprocess

base = r"C:\Users\kluse\Projects\cyberpunk-2077\mods\DesertEagle\assets\_inventory\anims_json\w_handgun__tsunami_nue__base1.anims.json"
out = r"C:\Users\kluse\Projects\cyberpunk-2077\mods\DesertEagle\assets\work\anims_test"

doc = json.load(open(base, encoding="utf-8"))
for entry in doc["Data"]["RootChunk"]["animations"]:
    anim = entry["Data"]["animation"]["Data"]
    if anim["name"]["$value"] == "recoil_shoulder":
        anim["animBuffer"]["Data"]["duration"] = 0.333

patched = os.path.join(out, "micro_duration.anims.json")
json.dump(doc, open(patched, "w", encoding="utf-8"), indent=1)

res = subprocess.run(
    [r"C:\Users\kluse\Tools\WolvenKit\9.1.0\wolvenkit-cli.cmd",
     "convert", "deserialize", patched, "-o", out, "-v", "Detailed"],
    capture_output=True, text=True)
ok = "Success" in (res.stdout + res.stderr)
print("MICRO_OK duration-only change works" if ok else "MICRO_FAIL duration-only change fails")
if not ok:
    for line in (res.stdout + res.stderr).splitlines():
        if "Exception" in line:
            print("  ", line.strip()[:180])
