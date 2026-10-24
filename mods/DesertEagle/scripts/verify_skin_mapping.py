"""Skinning semantics check: are each bone's vertices where the bone is?

For every rig joint: take vertices whose dominant weight is that joint,
compute their centroid, and compare against the bone's rest position
(composed from the .re bone tree). A wrong name mapping (e.g. clip->hammer)
puts a centroid far from its bone.

Run: blender.exe --background --python verify_skin_mapping.py
"""

from __future__ import annotations

import json
import math
import os

import bpy  # noqa: F401  (needed for h5py's numpy only, but keep Blender context)
import h5py
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
MOD_ROOT = os.path.abspath(os.path.join(HERE, ".."))
GEO = os.path.join(MOD_ROOT, "assets", "work", "de_geometry.json")
RE = os.path.join(MOD_ROOT, "assets", "work", "re", "base1", "recoil_shoulder.re")

JOINT_ORDER = [
    "barrel_plug", "barrel", "muzzle_slot", "fx_muzzle", "weapon_trigger",
    "slide", "hammer", "slider_down", "mag_slot", "scope_slot", "pos_ironsight",
]


def xform_matrix(rows12):
    v = [float(x) for x in rows12]
    m = np.eye(4)
    m[:3, 0] = v[0:3]
    m[:3, 1] = v[3:6]
    m[:3, 2] = v[6:9]
    m[:3, 3] = v[9:12]
    return m


def load_rest_world():
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
        return world


def main():
    world = load_rest_world()
    geo = json.load(open(GEO, encoding="utf-8"))["chunks"][0]

    buckets = {j: [] for j in range(len(JOINT_ORDER))}
    for pos, si, sw in zip(geo["positions"], geo["skin_indices"], geo["skin_weights"]):
        k = int(np.argmax(sw))
        if sw[k] > 0:
            buckets[si[k]].append(pos)

    fails = []
    print(f"{'joint':15s} {'verts':>6s} {'centroid':>28s} {'bone':>28s} {'dist':>8s}")
    for j, name in enumerate(JOINT_ORDER):
        pts = buckets.get(j, [])
        m = world.get(name)
        if m is None:
            print(f"{name:15s} MISSING BONE")
            fails.append(name)
            continue
        bone = m[:3, 3]
        if not pts:
            print(f"{name:15s} {0:6d} {'-':>28s} {str(np.round(bone,3).tolist()):>28s} {'-':>8s}")
            continue
        centroid = np.mean(np.array(pts), axis=0)
        dist = float(np.linalg.norm(centroid - bone))
        ok = dist < 0.06  # 6 cm — parts are small and close to their bones
        print(f"{name:15s} {len(pts):6d} {str(np.round(centroid,3).tolist()):>28s} "
              f"{str(np.round(bone,3).tolist()):>28s} {dist:8.4f}")
        if not ok:
            fails.append(f"{name}:{dist:.3f}m")

    total = sum(len(v) for v in buckets.values())
    print(f"\ntotal dominant-bound vertices: {total}/{len(geo['positions'])}")
    if total != len(geo["positions"]):
        fails.append("coverage")

    print("SKIN_MAPPING_VERIFY_OK" if not fails else f"SKIN_MAPPING_VERIFY_FAIL {fails}")
    return 0 if not fails else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception:
        import traceback

        traceback.print_exc()
        print("SKIN_MAPPING_VERIFY_FAIL", flush=True)
        raise SystemExit(1)
