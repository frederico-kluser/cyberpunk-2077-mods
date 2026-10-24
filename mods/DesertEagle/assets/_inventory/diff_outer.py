"""Compare OUTER values of weapon_empty (works) vs recoil_shoulder (fails)."""

import json

base = r"C:\Users\kluse\Projects\cyberpunk-2077\mods\DesertEagle\assets\_inventory\anims_json\w_handgun__tsunami_nue__base1.anims.json"
d = json.load(open(base, encoding="utf-8"))
for entry in d["Data"]["RootChunk"]["animations"]:
    anim = entry["Data"]["animation"]["Data"]
    name = anim["name"]["$value"]
    if name in ("weapon_empty", "recoil_shoulder", "first_equip", "empty_reload"):
        print(f"\n== {name} ==")
        for k in ("animationType", "frameClamping", "frameClampingStartFrame", "frameClampingEndFrame", "motionExtraction", "tags", "additionalTracks", "additionalTransforms"):
            print(f"  {k} = {json.dumps(anim.get(k), default=str)[:100]}")
        buf = anim["animBuffer"]["Data"]
        print(f"  bufferType = {buf.get('$type')}")
