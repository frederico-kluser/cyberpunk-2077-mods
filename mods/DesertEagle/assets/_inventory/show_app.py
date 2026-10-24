"""Print the top-level structure of the Nue .app JSON."""

import json

path = r"C:\Users\kluse\Projects\cyberpunk-2077\mods\DesertEagle\assets\_inventory\app_json\w_handgun__tsunami_nue.app.json"
d = json.load(open(path, encoding="utf-8"))
rc = d["Data"]["RootChunk"]
print("RootChunk type:", rc.get("$type"))
print("RootChunk keys:", list(rc.keys()))

for key in rc:
    val = rc[key]
    if isinstance(val, list):
        print(f"\n{key}: list[{len(val)}]")
        if val:
            first = val[0]
            print("  item0 type:", first.get("$type") if isinstance(first, dict) else type(first))
            if isinstance(first, dict):
                print("  item0 keys:", list(first.keys())[:15])
    elif isinstance(val, dict):
        print(f"\n{key}: dict keys={list(val.keys())[:12]}")

# appearance names
apps = rc.get("appearances") or []
print("\nappearances:", len(apps))
for a in apps[:20]:
    name = a.get("name", {})
    print("  -", name.get("$value") if isinstance(name, dict) else name)
