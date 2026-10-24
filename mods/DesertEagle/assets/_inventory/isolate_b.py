"""Isolation B: verbatim buffer copy with a UNIQUE HandleId."""

import json
import os
import subprocess

base = r"C:\Users\kluse\Projects\cyberpunk-2077\mods\DesertEagle\assets\_inventory\anims_json\w_handgun__tsunami_nue__base1.anims.json"
out = r"C:\Users\kluse\Projects\cyberpunk-2077\mods\DesertEagle\assets\work\anims_test"

doc = json.load(open(base, encoding="utf-8"))
clips = {}
for entry in doc["Data"]["RootChunk"]["animations"]:
    anim = entry["Data"]["animation"]["Data"]
    clips[anim["name"]["$value"]] = anim

node = json.loads(json.dumps(clips["weapon_empty"]["animBuffer"]))
node["HandleId"] = clips["recoil_shoulder"]["animBuffer"]["HandleId"]  # keep unique
clips["recoil_shoulder"]["animBuffer"] = node

patched = os.path.join(out, "isolate_unique.anims.json")
json.dump(doc, open(patched, "w", encoding="utf-8"), indent=1)

res = subprocess.run(
    [r"C:\Users\kluse\Tools\WolvenKit\9.1.0\wolvenkit-cli.cmd",
     "convert", "deserialize", patched, "-o", out, "-v", "Detailed"],
    capture_output=True, text=True)
ok = "Success" in (res.stdout + res.stderr)
print("ISOLATE_B_OK unique-handle copy works" if ok else "ISOLATE_B_FAIL unique-handle copy fails")
if not ok:
    for line in (res.stdout + res.stderr).splitlines():
        if "Exception" in line:
            print("  ", line.strip()[:180])
