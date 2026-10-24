"""Print inplace/temp buffer ids and flags of every clip in the pristine anims."""

import json

path = r"C:\Users\kluse\Projects\cyberpunk-2077\mods\DesertEagle\assets\_inventory\anims_json\w_handgun__tsunami_nue__base1.anims.json"
d = json.load(open(path, encoding="utf-8"))
for entry in d["Data"]["RootChunk"]["animations"]:
    anim = entry["Data"]["animation"]["Data"]
    buf = anim["animBuffer"]["Data"]
    name = anim["name"]["$value"]
    ip = buf.get("inplaceCompressedBuffer")
    tb = buf.get("tempBuffer")
    ip_s = f"BufferId={ip.get('BufferId')} Flags={ip.get('Flags')}" if ip else "None"
    tb_s = f"BufferId={tb.get('BufferId')} Flags={tb.get('Flags')}" if tb else "None"
    print(f"{name:20s} type={buf.get('$type'):32s} inplace[{ip_s}] temp[{tb_s}]")
