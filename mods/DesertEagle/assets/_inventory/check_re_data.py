"""Sanity-check the .re clip data: do any bone positions vary across frames?"""

import sys

import h5py

JOINT_ORDER = [
    "barrel_plug", "barrel", "muzzle_slot", "fx_muzzle", "weapon_trigger",
    "slide", "hammer", "slider_down", "mag_slot", "scope_slot", "pos_ironsight",
]

path = sys.argv[1]
with h5py.File(path, "r") as f:
    group = f[".re_anim_clip"] if ".re_anim_clip" in f else f
    print("bones in file:", sorted(group.keys())[:12])
    for bone in JOINT_ORDER:
        if bone not in group:
            print(f"{bone:15s} MISSING")
            continue
        rows = group[bone]["xformframes"][:]
        k = len(rows)
        p0 = rows[0][:3]
        pm = rows[k // 2][:3]
        p1 = rows[k - 1][:3]
        dp = max(abs(p0[i] - p1[i]) for i in range(3))
        r0 = rows[0][3:7]
        r1 = rows[k - 1][3:7]
        dr = max(abs(r0[i] - r1[i]) for i in range(4))
        print(f"{bone:15s} K={k:4d} pos0={tuple(round(x,4) for x in p0)} pos_end={tuple(round(x,4) for x in p1)} max|dpos|={dp:.4f} max|drot|={dr:.4f}")
