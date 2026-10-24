"""Build the Desert Eagle .app/.ent JSON from the extracted Tsunami Nue ones.

Pipeline:  Nue CR2W --serialize--> JSON --(this script)--> JSON --deserialize--> CR2W

Transformations (per docs/PIPELINE.md §5):
  * keep ONE appearance (dry-run rule) and rename it `desert_eagle`;
  * add the DesertEagleDefault visual tag;
  * repoint the main body entSkinnedMeshComponent to our exported mesh and
    remove the vanilla part meshes (diodes, decals, sights, rails, shadows) —
    our mesh replaces the whole body;
  * clear resolvedDependencies (Soft/Embedded entries make the game load the
    vanilla weapon over ours);
  * repoint baseEntity to our mesh_entity .ent.

Usage: python3 build_app_json.py <app_json> <ent_json> <out_dir>
"""

import copy
import json
import os
import sys

OUR_MESH = "desert_eagle\\items\\w_handgun_desert_eagle.mesh"
OUR_ENT = "desert_eagle\\items\\desert_eagle.ent"
MAIN_MESH_MARKER = "__base1_01.mesh"  # the vanilla main body mesh
KEEP_COMPONENT_MESHES = {MAIN_MESH_MARKER}


def cname(value):
    return {"$type": "CName", "$storage": "string", "$value": value}


def fnv1a64(text: str) -> int:
    h = 0xCBF29CE484222325
    for byte in text.encode("utf-8"):
        h ^= byte
        h = (h * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return h


def set_resource_path(dp, value):
    """Write a ResourcePath as `$storage: string` (the deserializer computes the
    hash itself). Hash-only (`uint64`) values are 'not resolvable' for
    WolvenKit's JSON reader — always keep the path string."""
    return {"$type": "ResourcePath", "$storage": "string", "$value": value}


def get_name(node):
    name = node.get("name") if isinstance(node, dict) else None
    if isinstance(name, dict):
        return name.get("$value", "")
    return name or ""


def mesh_depot(component):
    mesh = component.get("mesh")
    if not isinstance(mesh, dict):
        return ""
    dp = mesh.get("DepotPath") or mesh.get("depotPath")
    if isinstance(dp, dict):
        return dp.get("$value", "")
    return dp or ""


def set_mesh_depot(component, value):
    mesh = component.get("mesh")
    dp = mesh.get("DepotPath") or mesh.get("depotPath")
    mesh["DepotPath"] = set_resource_path(dp, value)


def transform_app(app):
    rc = app["Data"]["RootChunk"]

    # baseEntity -> our mesh_entity
    be = rc.get("baseEntity") or {}
    be["DepotPath"] = set_resource_path(be.get("DepotPath"), OUR_ENT)
    rc["baseEntity"] = be

    appearances = rc.get("appearances") or []
    kept = appearances[:1]  # dry-run rule: ONE appearance
    rc["appearances"] = kept

    for entry in kept:
        a = entry.get("Data", entry)
        a["name"] = cname("desert_eagle")

        # visual tags
        a["visualTags"] = {
            "$type": "redTagList",
            "tags": [cname("DesertEagleDefault"), cname("default")],
        }

        # components
        comps = a.get("components") or []
        new_comps = []
        for comp in comps:
            cd = comp.get("Data", comp)
            ctype = cd.get("$type", "")
            if ctype == "entSkinnedMeshComponent":
                depot = mesh_depot(cd)
                if depot.endswith(MAIN_MESH_MARKER) or depot.endswith("base1_01.mesh"):
                    set_mesh_depot(cd, OUR_MESH)
                    new_comps.append(comp)
                # vanilla part meshes are dropped (our mesh has the whole body)
                continue
            if ctype == "entMeshComponent":
                # vanilla part SHADOW meshes do not exist in our mod; the body
                # component casts its own shadows (castShadows=Always)
                depot = mesh_depot(cd)
                if depot and "desert_eagle" not in depot:
                    continue
            if ctype == "entVisualControllerComponent":
                # stale cooked dependency list of vanilla part meshes
                cd["appearanceDependency"] = []
            new_comps.append(comp)
        a["components"] = new_comps

        # resolvedDependencies must be empty or the game loads the vanilla mesh
        a["resolvedDependencies"] = []

        # compiledData is the cooked mirror of the component list — the engine
        # renders from the components (cookedAppearanceData is empty here), but
        # the stale mirror would keep vanilla chunk references alive. Mirror
        # the cleaned components so no vanilla mesh survives anywhere.
        cd = a.get("compiledData")
        # EXPERIMENTAL (DE_MIRROR=1): mirror the cleaned components into the
        # cooked cache. WolvenKit's RedPackage converter currently rejects the
        # mirrored form, and the cache is provably INERT while
        # cookedAppearanceData is empty (the engine renders from the
        # components) — so the mirror stays off by default.
        if os.environ.get("DE_MIRROR") == "1" and isinstance(cd, dict):
            data = cd.get("Data", cd)
            if isinstance(data, dict) and isinstance(data.get("Chunks"), list):
                before = len(data["Chunks"])
                data["Chunks"] = copy.deepcopy(new_comps)
                # CruidDict maps chunk index -> component id; rebuild it in step
                # or the RedPackage converter rejects the file
                data["CruidDict"] = {
                    str(i): comp.get("Data", comp).get("id", "0")
                    for i, comp in enumerate(new_comps)
                }
                print(f"APP_SUMMARY compiledData chunks={before} -> {len(new_comps)} (mirrored components + CruidDict)")

    return app


def transform_ent(ent, app_components=None):
    rc = ent["Data"]["RootChunk"]

    # The .ent components are CR2W types distinct from the .app appearance
    # ones (copying them across breaks WolvenKit's cast) — so instead of a
    # blind copy we keep the ent's own components and drop the extra
    # entSkinnedMeshComponents (they referenced vanilla part meshes that do
    # not exist in our mesh and would double-render in Photo Mode). One body
    # component remains, repointed to our mesh by the walk below.
    comps = rc.get("components") or []
    kept = []
    skinned_seen = 0
    for comp in comps:
        cd = comp.get("Data", comp)
        if cd.get("$type") == "entSkinnedMeshComponent":
            skinned_seen += 1
            if skinned_seen > 1:
                continue
        kept.append(comp)
    rc["components"] = kept
    print(f"ENT_SUMMARY components={len(kept)} (dropped {len(comps) - len(kept)} duplicate skinned)")

    def walk(node):
        if isinstance(node, dict):
            for key, value in list(node.items()):
                if key in ("DepotPath", "depotPath"):
                    cur = value.get("$value") if isinstance(value, dict) else value
                    if isinstance(cur, str) and cur.endswith(".mesh"):
                        node[key] = set_resource_path(value, OUR_MESH)
                else:
                    walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(rc)
    if "resolvedDependencies" in rc and isinstance(rc["resolvedDependencies"], list):
        rc["resolvedDependencies"] = []
    return ent


def main():
    app_json, ent_json, out_dir = sys.argv[1:4]
    os.makedirs(out_dir, exist_ok=True)

    app = json.load(open(app_json, encoding="utf-8"))
    app = transform_app(app)
    app_out = os.path.join(out_dir, "desert_eagle.app.json")
    json.dump(app, open(app_out, "w", encoding="utf-8"), indent=1)
    print("APP_JSON_OK", app_out)

    ent = json.load(open(ent_json, encoding="utf-8"))
    app_components = app["Data"]["RootChunk"]["appearances"][0]["Data"].get("components")
    ent = transform_ent(ent, app_components)
    ent_out = os.path.join(out_dir, "desert_eagle.ent.json")
    json.dump(ent, open(ent_out, "w", encoding="utf-8"), indent=1)
    print("ENT_JSON_OK", ent_out)

    # summary
    a0 = app["Data"]["RootChunk"]["appearances"][0]["Data"]
    meshes = [
        mesh_depot(c.get("Data", c))
        for c in a0["components"]
        if (c.get("Data", c).get("$type") == "entSkinnedMeshComponent")
    ]
    print("APP_SUMMARY components=", len(a0["components"]), "meshes=", meshes)
    print("APP_SUMMARY baseEntity=", app["Data"]["RootChunk"]["baseEntity"])
    print("BUILD_APP_DONE")


if __name__ == "__main__":
    main()
