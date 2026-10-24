"""Compare key sets: my patched clip buffer vs the pristine compressed buffer."""

import json

base = r"C:\Users\kluse\Projects\cyberpunk-2077\mods\DesertEagle\assets\_inventory\anims_json\w_handgun__tsunami_nue__base1.anims.json"
patched = r"C:\Users\kluse\Projects\cyberpunk-2077\mods\DesertEagle\assets\work\anims_test\w_handgun__tsunami_nue__base1.anims.json"


def clips(path):
    d = json.load(open(path, encoding="utf-8"))
    out = {}
    for entry in d["Data"]["RootChunk"]["animations"]:
        anim = entry["Data"]["animation"]["Data"]
        out[anim["name"]["$value"]] = anim
    return out


a = clips(base)
b = clips(patched)

ref = a["weapon_empty"]["animBuffer"]
mine = b["recoil_shoulder"]["animBuffer"]
print("pristine weapon_empty buffer keys:", sorted(k for k in ref if k != "Data"))
print("mine buffer wrapper keys:", sorted(k for k in mine if k != "Data"))
print("pristine inner keys:", sorted(ref["Data"].keys()))
print("mine inner keys:", sorted(mine["Data"].keys()))
print("only in pristine:", sorted(set(ref["Data"]) - set(mine["Data"])))
print("only in mine:", sorted(set(mine["Data"]) - set(ref["Data"])))

print("\nouter anim keys pristine:", sorted(a["weapon_empty"].keys()))
print("outer anim keys mine:", sorted(b["recoil_shoulder"].keys()))
print("outer only in mine:", sorted(set(b["recoil_shoulder"]) - set(a["weapon_empty"])))
