"""Show the pristine recoil_shoulder node structure (type + wrapper)."""

import json

base = r"C:\Users\kluse\Projects\cyberpunk-2077\mods\DesertEagle\assets\_inventory\anims_json\w_handgun__tsunami_nue__base1.anims.json"
d = json.load(open(base, encoding="utf-8"))
for entry in d["Data"]["RootChunk"]["animations"]:
    anim = entry["Data"]["animation"]["Data"]
    if anim["name"]["$value"] == "recoil_shoulder":
        buf_wrap = anim["animBuffer"]
        print("animBuffer wrapper keys:", sorted(buf_wrap.keys()))
        buf = buf_wrap["Data"]
        print("buffer $type:", buf.get("$type"))
        print("buffer keys:", sorted(buf.keys()))
        for k in sorted(buf.keys()):
            v = buf[k]
            if isinstance(v, (dict, list)):
                s = json.dumps(v, default=str)
                print(f"  {k}: {s[:120]}")
            else:
                print(f"  {k} = {v}")
        print("\nouter duration:", anim.get("duration"))
        break
