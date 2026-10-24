"""Inspect skeleton + header + sample curve of a REDmod .re starter."""

import sys

import h5py

path = sys.argv[1]
with h5py.File(path, "r") as f:
    print("ROOT KEYS:", list(f.keys()))
    hdr = f[".re_header"]
    print("\n-- .re_header --", type(hdr))
    if isinstance(hdr, h5py.Dataset):
        print("shape", hdr.shape, "dtype", hdr.dtype)
        print(hdr[:])
    else:
        for k in hdr.keys():
            print(" ", k, hdr[k])

    skel = f[".re_asset_node"][".re_asset_description_node"][".re_skeleton"]
    print("\n-- .re_skeleton keys --", list(skel.keys()))
    root = skel["Root"]
    print("Root type:", type(root))
    if isinstance(root, h5py.Group):
        print("Root keys:", list(root.keys()))
        for k in root.keys():
            node = root[k]
            if isinstance(node, h5py.Dataset):
                print(f"  Root/{k}: shape={node.shape} dtype={node.dtype}")
                if node.size <= 20:
                    print("   data:", node[:])
            else:
                print(f"  Root/{k}: GROUP keys={list(node.keys())}")

    clip = f[".re_asset_node"][".re_animation_container"][".re_animation"][".re_anim_clip"]
    print("\n-- anim_clip keys --", list(clip.keys()))
    extra = clip["*extraTransforms"]
    print("extraTransforms type:", type(extra))
    if isinstance(extra, h5py.Group):
        for k in extra.keys():
            print("  ", k, extra[k])

    grp = clip["Hips"]
    rows = grp["xformframes"][:]
    print(f"\nHIPS curve rows={rows.shape}")
    print("first:", rows[0])
    print("last :", rows[-1])

    anim = f[".re_asset_node"][".re_animation_container"][".re_animation"]
    print("\n.re_animation keys:", list(anim.keys()))
    for k in anim.keys():
        if isinstance(anim[k], h5py.Dataset):
            print("  ", k, anim[k].shape, anim[k][:])
