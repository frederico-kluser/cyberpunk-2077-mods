"""Print xformframes dataset shapes per bone in a .re clip."""

import h5py

RE = r"C:\Users\kluse\Projects\cyberpunk-2077\mods\DesertEagle\assets\work\re\base1\recoil_shoulder.re"
with h5py.File(RE, "r") as f:
    clip = f["/.re_asset_node/.re_animation_container/.re_animation/.re_anim_clip"]
    for key in clip.keys():
        item = clip[key]
        if isinstance(item, h5py.Group):
            for sub in item.keys():
                d = item[sub]
                print(f"{key}/{sub}: shape={getattr(d, 'shape', None)}")
        else:
            print(f"{key}: shape={item.shape} dtype={item.dtype}")
