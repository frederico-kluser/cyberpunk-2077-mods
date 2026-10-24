"""Does the VANILLA Nue mesh align with the .re bone tree? Compare spaces."""

import json
import os
import sys

import h5py
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))
import mesh_buffer as mb  # noqa: E402


def xform_matrix(rows12):
    v = [float(x) for x in rows12]
    m = np.eye(4)
    m[:3, 0] = v[0:3]
    m[:3, 1] = v[3:6]
    m[:3, 2] = v[6:9]
    m[:3, 3] = v[9:12]
    return m


van = json.load(open(r"C:\Users\kluse\Projects\cyberpunk-2077\mods\DesertEagle\assets\_inventory\mesh_json\w_handgun__tsunami_nue__base1_01.mesh.json", encoding="utf-8"))
chunks = mb.decode_geometry(van["Data"]["RootChunk"])
pts = np.array([p for ch in chunks for p in ch["positions"]])
print("VANILLA mesh bbox:")
print("  min:", np.round(pts.min(axis=0), 3).tolist())
print("  max:", np.round(pts.max(axis=0), 3).tolist())
print("  size:", np.round(pts.max(axis=0) - pts.min(axis=0), 3).tolist())

geo = json.load(open(r"C:\Users\kluse\Projects\cyberpunk-2077\mods\DesertEagle\assets\work\de_geometry.json", encoding="utf-8"))
gpts = np.array([p for ch in geo["chunks"] for p in ch["positions"]])
print("\nOUR mesh bbox:")
print("  min:", np.round(gpts.min(axis=0), 3).tolist())
print("  max:", np.round(gpts.max(axis=0), 3).tolist())
print("  size:", np.round(gpts.max(axis=0) - gpts.min(axis=0), 3).tolist())

RE = r"C:\Users\kluse\Projects\cyberpunk-2077\mods\DesertEagle\assets\work\re\base1\recoil_shoulder.re"
with h5py.File(RE, "r") as f:
    sk = f["/.re_asset_node/.re_asset_description_node/.re_skeleton"]
    root = sk["barrel_plug"]
    names, parents, locals_ = [], [], []

    def visit(group, parent_idx):
        idx = len(names)
        names.append(group.name.rsplit("/", 1)[-1])
        parents.append(parent_idx)
        locals_.append(xform_matrix(group["xform"][:].reshape(-1)))
        for key in group.keys():
            item = group[key]
            if isinstance(item, h5py.Group) and not key.startswith("."):
                visit(item, idx)

    visit(root, -1)
    world = {}
    for i in range(len(names)):
        p = parents[i]
        world[names[i]] = (world[names[p]] @ locals_[i] if p >= 0 else locals_[i])

print("\nBone world positions (rest):")
for n in ("barrel_plug", "barrel", "slide", "hammer", "mag_slot", "fx_muzzle"):
    print(f"  {n:12s}", np.round(world[n][:3, 3], 3).tolist())
