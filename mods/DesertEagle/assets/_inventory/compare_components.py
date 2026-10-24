"""Compare component arrays of our .app appearance vs our .ent."""

import json

app = json.load(open(r"C:\Users\kluse\Projects\cyberpunk-2077\mods\DesertEagle\assets\work\de_app\desert_eagle.app.json", encoding="utf-8"))
ent = json.load(open(r"C:\Users\kluse\Projects\cyberpunk-2077\mods\DesertEagle\assets\work\de_app\desert_eagle.ent.json", encoding="utf-8"))

a0 = app["Data"]["RootChunk"]["appearances"][0]["Data"]
app_comps = a0.get("components") or []
ent_rc = ent["Data"]["RootChunk"]
ent_comps = ent_rc.get("components") or []


def names(comps):
    out = []
    for c in comps:
        cd = c.get("Data", c)
        n = cd.get("name")
        n = n.get("$value") if isinstance(n, dict) else n
        out.append(f"{cd.get('$type')}:{n}")
    return out


print(f"app components: {len(app_comps)}")
for n in names(app_comps):
    print("  A", n)
print(f"ent components: {len(ent_comps)}")
for n in names(ent_comps):
    print("  E", n)
print("\nent RootChunk keys:", sorted(ent_rc.keys()))
