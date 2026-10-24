"""Show the animBuffer JSON layout of an ANIMATED animation entry."""

import json

path = r"C:\Users\kluse\Projects\cyberpunk-2077-desert-eagle\mods\DesertEagle\assets\_inventory\anims_json\w_handgun__tsunami_nue__base1.anims.json"
d = json.load(open(path, encoding="utf-8"))
for entry in d["Data"]["RootChunk"]["animations"]:
    anim = entry["Data"]["animation"]["Data"]
    name = anim["name"]["$value"]
    buf = anim["animBuffer"]["Data"]
    keys = sorted(buf.keys())
    interesting = {k: buf[k] for k in keys if k not in ("$type",)}
    # shrink big base64-looking values
    for k, v in list(interesting.items()):
        s = str(v)
        if len(s) > 120:
            interesting[k] = s[:100] + f"... <{len(s)} chars>"
    print(f"\n=== {name} === type={buf.get('$type')}")
    print(json.dumps(interesting, indent=1)[:1800])
