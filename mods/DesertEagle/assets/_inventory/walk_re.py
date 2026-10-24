"""Dump the HDF5 group tree of a .re file (up to depth 4)."""

import sys

import h5py


def walk(node, depth=0, prefix=""):
    for key in node.keys():
        item = node[key]
        path = f"{prefix}/{key}"
        if isinstance(item, h5py.Group):
            print(f"{'  ' * depth}[G] {path}  ({len(item.keys())} keys)")
            if depth < 3:
                walk(item, depth + 1, path)
        else:
            print(f"{'  ' * depth}[D] {path}  shape={item.shape} dtype={item.dtype}")


with h5py.File(sys.argv[1], "r") as f:
    print("root keys:", list(f.keys()))
    walk(f)
