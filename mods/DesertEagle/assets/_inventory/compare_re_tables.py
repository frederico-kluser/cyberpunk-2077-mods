"""Compare flat bonexforms rows against the bone tree xforms in a .re file."""

import h5py
import numpy as np

RE = r"C:\Users\kluse\Projects\cyberpunk-2077\mods\DesertEagle\assets\work\re\base1\recoil_shoulder.re"

with h5py.File(RE, "r") as f:
    sk = f["/.re_asset_node/.re_asset_description_node/.re_skeleton"]
    names = [b.decode() if isinstance(b, bytes) else str(b) for b in sk["bonenames"][:]]
    bx = sk["bonexforms"][:]
    parents = sk["parents"][:]

    print("parents:", parents.reshape(-1).tolist())
    print()

    tree = {}

    def visit(group):
        name = group.name.rsplit("/", 1)[-1]
        tree[name] = group["xform"][:].reshape(-1)
        for key in group.keys():
            item = group[key]
            if isinstance(item, h5py.Group) and not key.startswith("."):
                visit(item)

    visit(sk["barrel_plug"])

    for i, name in enumerate(names):
        row = bx[i]
        # flat: pos(3) quat(x,y,z,w) scale(3); tree: 4 vectors of 3 = axes+trans
        flat_pos = row[0:3]
        flat_quat = row[3:7]
        flat_scale = row[7:10]
        tx = tree.get(name)
        tree_pos = tx[9:12] if tx is not None else None
        same = tree_pos is not None and np.allclose(flat_pos, tree_pos, atol=1e-5)
        print(f"{name:15s} flat_pos={np.round(flat_pos,4).tolist()} tree_pos="
              f"{np.round(tree_pos,4).tolist() if tree_pos is not None else None} match={same}")
        print(f"{'':15s} flat_quat={np.round(flat_quat,4).tolist()} scale={np.round(flat_scale,3).tolist()}")
