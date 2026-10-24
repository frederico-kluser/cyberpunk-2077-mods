"""Probe: does a vanilla static clip's keys equal the rig rest?

Convention check for the grip-alignment design: if the vanilla `weapon_empty`
(a static clip) has the root/bone transforms EQUAL to the rig's rest, the
engine derives the skinning rest from the .rig (standard) and our A-in-root
design behaves as intended.
"""

import json
import sys

ANIMS = r"C:\Users\kluse\Projects\cyberpunk-2077\mods\DesertEagle\assets\_inventory\anims_json\w_handgun__tsunami_nue__base1.anims.json"
RIG = r"C:\Users\kluse\Projects\cyberpunk-2077\mods\DesertEagle\assets\_inventory\nue_rig.json"
sys.path.insert(0, r"C:\Users\kluse\Projects\cyberpunk-2077\mods\DesertEagle\scripts")

d = json.load(open(ANIMS, encoding="utf-8"))
for entry in d["Data"]["RootChunk"]["animations"]:
    anim = entry["Data"]["animation"]["Data"]
    if anim["name"]["$value"] != "weapon_empty":
        continue
    buf = anim["animBuffer"]["Data"]
    print("weapon_empty buffer type:", buf.get("$type"), "| const keys:", buf.get("numConstAnimKeys"),
          "| anim keys:", buf.get("numAnimKeys"), "| raw:", buf.get("numAnimKeysRaw"))
    tb = buf.get("tempBuffer") or buf.get("inplaceCompressedBuffer") or {}
    print("has buffer bytes:", bool(tb.get("Bytes")))

rig = json.load(open(RIG, encoding="utf-8"))


def find(node, key):
    if isinstance(node, dict):
        if key in node:
            return node[key]
        for v in node.values():
            r = find(v, key)
            if r is not None:
                return r
    elif isinstance(node, list):
        for v in node:
            r = find(v, key)
            if r is not None:
                return r
    return None


names = find(rig["Data"], "boneNames")
print("\nrig root bone:", names[0] if names else "?")
print("(the static clip's const keys should match these rest transforms)")
