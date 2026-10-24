"""REDmod .re writer: synthesize weapon animset .re files.

Format decoded from the official CDPR starter files (`starter_standing_basic_model.re`):

  .re (HDF5)
  ├── .re_header/                                  (empty group)
  └── .re_asset_node/
      ├── .re_asset_description_node/
      │   └── .re_skeleton/
      │       ├── bonenames   (N,)   object/bytes  — bone names
      │       ├── bonexforms  (N,10) float32       — pos(3) quat(x,y,z,w) scale(3)
      │       ├── parents     (1,N)  int32         — (zeroed in CDPR files)
      │       ├── channels    (M,)   object/bytes  — float-track names
      │       ├── curves      (1,M)  float32       — constant values per channel
      │       └── Root/ …                           — nested bone tree (.transform/.attributes/xform)
      └── .re_animation_container/
          └── .re_animation/
              ├── animation          (0,10) — empty
              ├── .re_anim_clip/
              │   ├── <bone>/xformframes (K,11) float32
              │   │     pos.x,y,z rot.x,y,z,w scale.x,y,z time
              │   ├── <channel>/keyframes  (K,) [value,time]
              │   └── *extraTransforms/    (empty group)
              └── .re_anim_event_container/

The game names the animation in the .anims set after the .re FILE name, so every
export is written as e.g. `recoil_shoulder.re` for the internal anim of the same
name (REDmod rule).
"""

from __future__ import annotations

import json
import shutil

import h5py
import numpy as np

XFORM_DTYPE = np.dtype(
    [
        ("pos.x", "<f4"), ("pos.y", "<f4"), ("pos.z", "<f4"),
        ("rot.x", "<f4"), ("rot.y", "<f4"), ("rot.z", "<f4"), ("rot.w", "<f4"),
        ("scale.x", "<f4"), ("scale.y", "<f4"), ("scale.z", "<f4"),
        ("time", "<f4"),
    ]
)

ATTR_DTYPE = np.dtype([("name", h5py.special_dtype(vlen=bytes)), ("value", "<f8")])
STR_DTYPE = h5py.special_dtype(vlen=bytes)
ATTR_NAMES = [
    ("translateX", 0.0), ("translateY", 0.0), ("translateZ", 0.0),
    ("rotateX", 0.0), ("rotateY", 0.0), ("rotateZ", 0.0),
    ("scaleX", 1.0), ("scaleY", 1.0), ("scaleZ", 1.0),
    ("rotateOrder", 0.0),
    ("jointOrientX", 0.0), ("jointOrientY", 0.0), ("jointOrientZ", 0.0),
]


def load_rig_json(path: str) -> list:
    """Parse the serialized CP2077 .rig into bone specs.

    Returns [{name, parent, pos(3), quat(x,y,z,w), scale(3)}] in rig order.
    The QsTransform is local (parent-relative) — the same space the .re
    xformframes use.
    """
    with open(path, encoding="utf-8") as handle:
        rc = json.load(handle)["Data"]["RootChunk"]

    names = [entry["$value"] for entry in rc["boneNames"]]
    parents = rc["boneParentIndexes"]
    bones = []
    for i, name in enumerate(names):
        t = rc["boneTransforms"][i]
        rot = t["Rotation"]
        scl = t["Scale"]
        trs = t["Translation"]
        bones.append(
            {
                "name": name,
                "parent": int(parents[i]),
                "pos": (float(trs["X"]), float(trs["Y"]), float(trs["Z"])),
                "quat": (float(rot["i"]), float(rot["j"]), float(rot["k"]), float(rot["r"])),
                "scale": (float(scl["X"]), float(scl["Y"]), float(scl["Z"])),
            }
        )
    return bones


def _row(pos, quat, scale, time) -> tuple:
    return (
        pos[0], pos[1], pos[2],
        quat[0], quat[1], quat[2], quat[3],
        scale[0], scale[1], scale[2],
        time,
    )


def _rest_rows(bones, num_frames: int) -> dict:
    """Constant xformframes (rest pose) per bone."""
    rows = {}
    for bone in bones:
        rows[bone["name"]] = np.array(
            [_row(bone["pos"], bone["quat"], bone["scale"], float(f)) for f in range(num_frames)],
            dtype=XFORM_DTYPE,
        )
    return rows


def build_template(path: str, bones: list, num_frames: int = 2) -> str:
    """Write a complete weapon .re whose curves hold the REST pose."""
    rows = _rest_rows(bones, num_frames)
    write_re(path, bones, rows)
    return path


def write_re(path: str, bones: list, curve_rows: dict) -> str:
    """Write a .re file: skeleton = `bones`, curves = {bone_name: xformframes}."""
    names = [b["name"] for b in bones]

    with h5py.File(path, "w") as f:
        f.create_group(".re_header")

        node = f.create_group(".re_asset_node")
        desc = node.create_group(".re_asset_description_node")
        skel = desc.create_group(".re_skeleton")

        skel.create_dataset(
            "bonenames",
            data=np.array([n.encode("utf-8") for n in names], dtype=object),
            dtype=STR_DTYPE,
        )
        skel.create_dataset("bonexforms", data=np.array(
            [
                list(b["pos"]) + list(b["quat"]) + list(b["scale"])
                for b in bones
            ],
            dtype=np.float32,
        ))
        skel.create_dataset("parents", data=np.zeros((1, len(bones)), dtype=np.int32))
        skel.create_dataset("channels", data=np.array([], dtype=object), dtype=STR_DTYPE)
        skel.create_dataset("curves", data=np.zeros((1, 0), dtype=np.float32))

        # Bone tree: every TOP-LEVEL group of .re_skeleton is a root bone
        # (the CDPR starters have 'Root' simply because their root bone is
        # named 'Root'); children are nested under their parent.
        for bone in bones:
            if bone["parent"] < 0:
                _write_bone_group(skel, bone, bones)

        cont = node.create_group(".re_animation_container")
        anim = cont.create_group(".re_animation")
        anim.create_dataset("animation", data=np.zeros((0, 10), dtype=np.float32))
        clip = anim.create_group(".re_anim_clip")
        clip.create_group("*extraTransforms")
        anim.create_group(".re_anim_event_container")

        for name in names:
            grp = clip.create_group(name)
            grp.create_dataset("xformframes", data=np.asarray(curve_rows[name], dtype=XFORM_DTYPE))

    return path


def _write_bone_group(parent_group, bone: dict, bones: list) -> None:
    grp = parent_group.create_group(bone["name"])
    attrs = np.array(
        [(name.encode("utf-8"), value) for name, value in ATTR_NAMES],
        dtype=ATTR_DTYPE,
    )
    grp.create_dataset(".attributes", data=attrs)

    pos = np.array(bone["pos"], dtype=np.float32)
    quat = bone["quat"]
    # rotation matrix rows from the quaternion (x,y,z,w)
    x, y, z, w = quat
    rot = np.array(
        [
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
        ],
        dtype=np.float32,
    )
    flat = np.concatenate([rot.reshape(-1), pos])  # rows then translation
    grp.create_dataset("xform", data=flat.reshape(1, 12))
    grp.create_dataset(".transform", data=np.concatenate([pos, rot.reshape(-1)]).reshape(1, 12))

    for child in bones:
        if child["parent"] == bones.index(bone):
            _write_bone_group(grp, child, bones)


def replace_curves(template_path: str, out_path: str, curve_rows: dict, times) -> str:
    """Copy `template_path` and overwrite the per-bone xformframes."""
    shutil.copyfile(template_path, out_path)
    with h5py.File(out_path, "a") as f:
        clip = f[".re_asset_node"][".re_animation_container"][".re_animation"][".re_anim_clip"]
        for name, rows in curve_rows.items():
            if name not in clip:
                grp = clip.create_group(name)
            else:
                grp = clip[name]
            data = np.asarray(rows, dtype=XFORM_DTYPE)
            for i, t in enumerate(times):
                data[i]["time"] = float(t)
            if "xformframes" in grp:
                del grp["xformframes"]
            grp.create_dataset("xformframes", data=data)
    return out_path
