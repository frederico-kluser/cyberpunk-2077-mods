"""Isolation test: copy weapon_empty's buffer node verbatim into recoil_shoulder."""

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

# verbatim copy of the working buffer node
clips["recoil_shoulder"]["animBuffer"] = json.loads(json.dumps(clips["weapon_empty"]["animBuffer"]))

patched = os.path.join(out, "isolate_copy.anims.json")
json.dump(doc, open(patched, "w", encoding="utf-8"), indent=1)

res = subprocess.run(
    [r"C:\Users\kluse\Tools\WolvenKit\9.1.0\wolvenkit-cli.cmd",
     "convert", "deserialize", patched, "-o", out, "-v", "Detailed"],
    capture_output=True, text=True)
ok = "Success" in (res.stdout + res.stderr)
print("ISOLATE_OK verbatim-copy works" if ok else "ISOLATE_FAIL verbatim-copy fails")
if not ok:
    for line in (res.stdout + res.stderr).splitlines():
        if "Error" in line or "Exception" in line:
            print("  ", line.strip()[:160])
