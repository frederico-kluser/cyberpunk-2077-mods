"""Show HandleIds of all animation nodes in the pristine .anims JSON."""

import json

path = r"C:\Users\kluse\Projects\cyberpunk-2077\mods\DesertEagle\assets\_inventory\anims_json\w_handgun__tsunami_nue__base1.anims.json"
d = json.load(open(path, encoding="utf-8"))
for entry in d["Data"]["RootChunk"]["animations"]:
    a = entry["Data"]["animation"]
    anim = a["Data"]
    name = anim["name"]["$value"]
    print(
        f"{name:20s} entry={entry.get('HandleId')} animation={a.get('HandleId')} "
        f"buffer={anim['animBuffer'].get('HandleId')}"
    )
