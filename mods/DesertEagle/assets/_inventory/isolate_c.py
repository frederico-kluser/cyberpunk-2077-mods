"""Isolation C: Simd->Compressed type swap on the FIRST_EQUIP clip (2nd)."""

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
node["HandleId"] = clips["first_equip"]["animBuffer"]["HandleId"]
clips["first_equip"]["animBuffer"] = node

patched = os.path.join(out, "isolate_c.anims.json")
json.dump(doc, open(patched, "w", encoding="utf-8"), indent=1)

res = subprocess.run(
    [r"C:\Users\kluse\Tools\WolvenKit\9.1.0\wolvenkit-cli.cmd",
     "convert", "deserialize", patched, "-o", out, "-v", "Detailed"],
    capture_output=True, text=True)
ok = "Success" in (res.stdout + res.stderr)
print("ISOLATE_C_OK first_equip swap works" if ok else "ISOLATE_C_FAIL first_equip swap fails")

# and the reverse: keep type Simd but change ONLY its inplace buffer content
doc2 = json.load(open(base, encoding="utf-8"))
clips2 = {}
for entry in doc2["Data"]["RootChunk"]["animations"]:
    anim = entry["Data"]["animation"]["Data"]
    clips2[anim["name"]["$value"]] = anim
b = clips2["first_equip"]["animBuffer"]["Data"]
b["inplaceCompressedBuffer"]["Bytes"] = clips2["weapon_empty"]["animBuffer"]["Data"]["tempBuffer"]["Bytes"]
patched2 = os.path.join(out, "isolate_d.anims.json")
json.dump(doc2, open(patched2, "w", encoding="utf-8"), indent=1)
res2 = subprocess.run(
    [r"C:\Users\kluse\Tools\WolvenKit\9.1.0\wolvenkit-cli.cmd",
     "convert", "deserialize", patched2, "-o", out, "-v", "Detailed"],
    capture_output=True, text=True)
ok2 = "Success" in (res2.stdout + res2.stderr)
print("ISOLATE_D_OK inplace-content change works" if ok2 else "ISOLATE_D_FAIL inplace-content change fails")
