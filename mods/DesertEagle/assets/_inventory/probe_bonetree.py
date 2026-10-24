"""Probe the .re bone TREE (nested groups) for the real rest transforms."""

import h5py

RE = r"C:\Users\kluse\Projects\cyberpunk-2077\mods\DesertEagle\assets\work\re\base1\recoil_shoulder.re"


def walk(node, depth=0):
    for key in node.keys():
        item = node[key]
        if isinstance(item, h5py.Group):
            print(f"{'  ' * depth}[G] {key}  keys={list(item.keys())}")
            if depth < 2:
                walk(item, depth + 1)
        else:
            print(f"{'  ' * depth}[D] {key}  shape={item.shape} dtype={item.dtype}")
            if item.size <= 12 and item.size > 0:
                print(f"{'  ' * depth}    value={item[:].reshape(-1)[:12]}")


with h5py.File(RE, "r") as f:
    sk = f["/.re_asset_node/.re_asset_description_node/.re_skeleton"]
    walk(sk["barrel_plug"])
