"""Inspect the HDF5 structure of a REDmod .re starter file."""

import sys

import h5py

path = sys.argv[1]
with h5py.File(path, "r") as f:
    def walk(name, obj):
        if isinstance(obj, h5py.Dataset):
            print(f"DS  {name:72s} shape={obj.shape} dtype={obj.dtype}")
        else:
            print(f"GRP {name}")

    print("ROOT KEYS:", list(f.keys()))
    f.visititems(walk)
    clip = f[".re_asset_node"][".re_animation_container"][".re_animation"][".re_anim_clip"]
    print("\nCURVE GROUPS:", [k for k in clip.keys() if isinstance(clip[k], h5py.Group)][:30])
    skel = f[".re_asset_node"][".re_asset_description_node"][".re_skeleton"]
    print("SKELETON GROUPS:", [k for k in skel.keys()][:30])
    for key in list(clip.keys())[:1]:
        grp = clip[key]
        if isinstance(grp, h5py.Group) and "xformframes" in grp:
            rows = grp["xformframes"][:]
            print(f"\nSAMPLE CURVE '{key}': rows={rows.shape} dtype={rows.dtype}")
            print("first 3 rows:", rows[:3])
            print("last row:", rows[-1])
