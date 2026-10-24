"""Inspect the flat skeleton tables + float-track curves of a .re starter."""

import sys

import h5py

path = sys.argv[1]
with h5py.File(path, "r") as f:
    skel = f[".re_asset_node"][".re_asset_description_node"][".re_skeleton"]
    for key in ("channels", "curves", "bonexforms", "bonenames", "parents"):
        ds = skel[key]
        print(f"\n{key}: shape={ds.shape} dtype={ds.dtype}")
        print("  head:", ds[:6])

    clip = f[".re_asset_node"][".re_animation_container"][".re_animation"][".re_anim_clip"]
    for name in ("Root.headBodyPartVis", "Root", "Trajectory"):
        grp = clip[name]
        print(f"\ncurve '{name}': keys={list(grp.keys())}")
        for k in grp.keys():
            ds = grp[k]
            print(f"   {k}: shape={ds.shape} dtype={ds.dtype}")
            if ds.size:
                print("    head:", ds[:3])
                print("    tail:", ds[-2:])
