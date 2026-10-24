"""Decode the vanilla static clip's const keys and compare with the rig rest."""

import base64
import json
import sys

sys.path.insert(0, r"C:\Users\kluse\Projects\cyberpunk-2077\mods\DesertEagle\scripts")
sys.path.insert(0, r"C:\Users\kluse\Projects\cyberpunk-2077\mods\DesertEagle\src\blender")
import anims_write as cw  # noqa: E402
from de_pipeline.re_export import load_rig_json  # noqa: E402

ANIMS = r"C:\Users\kluse\Projects\cyberpunk-2077\mods\DesertEagle\assets\_inventory\anims_json\w_handgun__tsunami_nue__base1.anims.json"
RIG = r"C:\Users\kluse\Projects\cyberpunk-2077\mods\DesertEagle\assets\_inventory\nue_rig.json"

d = json.load(open(ANIMS, encoding="utf-8"))
for entry in d["Data"]["RootChunk"]["animations"]:
    anim = entry["Data"]["animation"]["Data"]
    if anim["name"]["$value"] != "weapon_empty":
        continue
    buf = anim["animBuffer"]["Data"]
    counts = {"num_anim_keys_raw": 0, "num_const_anim_keys": buf["numConstAnimKeys"]}
    blob = base64.b64decode(buf["tempBuffer"]["Bytes"])
    keys = cw.decode_buffer(blob, counts, buf.get("duration", 1.0))

rig = json.load(open(RIG, encoding="utf-8"))
bones = load_rig_json(RIG)
by_name = {b["name"]: b for b in bones}
names = [b["name"] for b in bones]
print(f"{'bone':16s} {'clip pos':>26s} {'rig pos':>26s}  match")
maxerr = 0.0
for k in keys["const"]:
    b = k["bone"]
    if k["component"] != 0:
        continue
    clip_p = k["value"]
    rig_p = by_name[names[b]]["pos"]
    err = max(abs(a - c) for a, c in zip(clip_p, rig_p))
    maxerr = max(maxerr, err)
    print(f"{names[b]:16s} {str(tuple(round(x,4) for x in clip_p)):>26s} {str(tuple(round(x,4) for x in rig_p)):>26s}  {'OK' if err < 1e-4 else 'DIFF'}")
print(f"\nmax position error clip-vs-rigrest: {maxerr:.6f} m")
print("REST_CONVENTION_RIG" if maxerr < 1e-4 else "REST_CONVENTION_OTHER")
