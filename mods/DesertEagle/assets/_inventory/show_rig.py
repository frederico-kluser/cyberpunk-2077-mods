"""Print the bone list and transform format of the serialized Nue rig."""

import json

path = r"C:\Users\kluse\Projects\cyberpunk-2077-desert-eagle\mods\DesertEagle\assets\_inventory\nue_rig.json"
d = json.load(open(path, encoding="utf-8"))
rc = d["Data"]["RootChunk"]
print("KEYS:", list(rc.keys()))
names = [b["$value"] for b in rc["boneNames"]]
print("boneNames:", names)
print("parents:", rc["boneParentIndexes"])
for i in (0, 1, 5):
    t = rc["boneTransforms"][i]
    print(f"\ntransform[{i}] ({names[i]}):")
    print(json.dumps(t, indent=1))
