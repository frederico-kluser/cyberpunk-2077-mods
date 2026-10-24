"""Patch a template .mesh.json to use our own textured material.

Replaces material[0] (the one the merged body chunk renders with) with a
`engine\materials\metal_base.mt` instance pointing at our CS2-derived maps:

  BaseColor -> desert_eagle\items\textures\desert_eagle_bc.xbm   (RGBA)
  Normal    -> desert_eagle\items\textures\desert_eagle_n.xbm    (BC5)

Property names are the ones the WolvenKit Blender add-on reads for metal_base
(material_types/metalbase.py used_params).

Usage: python3 build_materials.py <template.mesh.json> <out.mesh.json>
"""

import json
import os
import sys

BC_XBM = "desert_eagle\\items\\textures\\desert_eagle_bc.xbm"
N_XBM = "desert_eagle\\items\\textures\\desert_eagle_n.xbm"
BASE_MT = "engine\\materials\\metal_base.mt"


def res_path(value):
    return {"$type": "ResourcePath", "$storage": "string", "$value": value}


def tex_value(prop, path):
    return {"$type": "rRef:ITexture", prop: {"DepotPath": res_path(path), "Flags": "Default"}}


def float_value(prop, value):
    return {"$type": "Float", prop: value}


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


def main():
    src, out = sys.argv[1], sys.argv[2]
    doc = json.load(open(src, encoding="utf-8"))
    rc = doc["Data"]["RootChunk"]

    buf = find(rc, "localMaterialBuffer")
    mats = buf.get("materials") or []
    if not mats:
        raise SystemExit("BUILD_MATERIALS_FAIL: template has no materials")

    envelope = mats[0]
    mat = {
        "$type": "CMaterialInstance",
        "audioTag": {"$type": "CName", "$storage": "string", "$value": "None"},
        "baseMaterial": {"DepotPath": res_path(BASE_MT), "Flags": "Default"},
        "cookingPlatform": envelope.get("cookingPlatform", "PLATFORM_None"),
        "enableMask": envelope.get("enableMask", 0),
        "metadata": None,
        "resourceVersion": envelope.get("resourceVersion", 4),
        "values": [
            tex_value("BaseColor", BC_XBM),
            tex_value("Normal", N_XBM),
            float_value("Metalness", 0.9),
            float_value("Roughness", 0.45),
            float_value("NormalStrength", 1.0),
        ],
    }
    # keep the envelope identity of the original entry
    if isinstance(envelope, dict) and "Data" in envelope:
        mat = {"HandleId": envelope.get("HandleId", "0"), "Data": mat}

    mats[0] = mat
    buf["materials"] = mats

    json.dump(doc, open(out, "w", encoding="utf-8"), indent=1)
    print(f"BUILD_MATERIALS_OK {out}")
    print(f"  material[0] -> {BASE_MT}")
    print(f"    BaseColor = {BC_XBM}")
    print(f"    Normal    = {N_XBM}")
    print(f"  materials kept: {len(mats)}")


if __name__ == "__main__":
    main()
