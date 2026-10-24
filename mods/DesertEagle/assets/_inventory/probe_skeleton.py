"""Probe the .re skeleton shapes and key mapping."""

import h5py

RE = r"C:\Users\kluse\Projects\cyberpunk-2077\mods\DesertEagle\assets\work\re\base1\recoil_shoulder.re"
with h5py.File(RE, "r") as f:
    sk = f["/.re_asset_node/.re_asset_description_node/.re_skeleton"]
    print("skeleton keys:", list(sk.keys()))
    names = sk["bonenames"][:]
    parents = sk["parents"][:]
    bx = sk["bonexforms"][:]
    print("bonenames shape:", names.shape, "sample:", names[:3])
    print("parents shape:", parents.shape, parents)
    print("bonexforms shape:", bx.shape)
    print("row0:", bx[0] if bx.ndim == 2 else bx[:10])
