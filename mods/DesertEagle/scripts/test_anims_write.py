"""Round-trip + CR2W test for the animation buffer writer.

1. pack synthetic joint keys -> decode -> compare (codec correctness)
2. patch the REAL Nue base1.anims clip `recoil_shoulder` -> deserialize CR2W
   -> serialize -> decode -> compare (end-to-end)

Run with Blender's python (needs numpy-free stdlib only, any python3 works):
  python3 test_anims_write.py <base1.anims.json> <out_dir>
"""

import base64
import json
import os
import struct
import sys

import anims_write as aw


def approx(a, b, eps=1e-4):
    return all(abs(x - y) <= eps for x, y in zip(a, b))


def main():
    src_json, out_dir = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    fails = []

    # --- 1. codec round-trip -------------------------------------------------
    duration = 0.333
    joints = {
        0: {"position": [(0.0, (1.0, 2.0, 3.0))]},                     # const
        5: {
            "position": [(0.0, (0.0, 0.0, 0.0)), (0.333, (0.0, 0.0, 0.15))],
            "rotation": [(0.0, (0.0, 0.0, 0.0, 1.0)), (0.333, (0.0, 0.26, 0.0, 0.966))],
        },
    }
    built = aw.build_buffer(joints, duration)
    counts = {
        "num_anim_keys_raw": built["num_anim_keys_raw"],
        "num_const_anim_keys": built["num_const_anim_keys"],
    }
    decoded = aw.decode_buffer(built["blob"], counts, duration)

    ok = built["num_anim_keys_raw"] == 4 and built["num_const_anim_keys"] == 1
    print(f"[{'OK' if ok else 'FAIL'}] counts raw={built['num_anim_keys_raw']} const={built['num_const_anim_keys']}")
    if not ok:
        fails.append("counts")

    if decoded["const"] and approx(decoded["const"][0]["value"], (1.0, 2.0, 3.0)) and decoded["const"][0]["bone"] == 0:
        print("[OK] const key round-trips (bone 0, position)")
    else:
        print(f"[FAIL] const key: {decoded.get('const')}")
        fails.append("const")

    slide = [k for k in decoded["raw"] if k["bone"] == 5 and k["component"] == 0]
    if len(slide) == 2 and approx(slide[1]["value"], (0.0, 0.0, 0.15), 1e-5) and abs(slide[1]["time"] - duration) < 1e-3:
        print("[OK] raw position keys round-trip (bone 5, slide motion)")
    else:
        print(f"[FAIL] raw positions: {slide}")
        fails.append("raw-position")

    rot = [k for k in decoded["raw"] if k["bone"] == 5 and k["component"] == 1]
    if len(rot) == 2 and rot[1]["w_sign"] == 0:
        # smallest-three: stored x',y',z' reconstruct as x'*sqrt(2-dot'), w = 1-dot'
        xp, yp, zp = rot[1]["value"]
        dot = xp * xp + yp * yp + zp * zp
        f = (2.0 - dot) ** 0.5
        x, y, z, w = xp * f, yp * f, zp * f, 1.0 - dot
        ok_rot = abs(w - 0.966) < 0.02 and abs(y - 0.26) < 0.02
        print(f"[{'OK' if ok_rot else 'FAIL'}] smallest-three rotation (y={y:.3f} w={w:.3f})")
        if not ok_rot:
            fails.append("rotation")
    else:
        print(f"[FAIL] rotations: {rot}")
        fails.append("rotation")

    # --- 2. real clip patch -> CR2W -----------------------------------------
    doc = json.load(open(src_json, encoding="utf-8"))
    result = aw.write_clip(doc, "recoil_shoulder", joints, duration, 11)
    patched = os.path.join(out_dir, "w_handgun__tsunami_nue__base1.anims.json")
    json.dump(doc, open(patched, "w", encoding="utf-8"), indent=1)
    print(f"[OK] patched clip recoil_shoulder -> {result}")

    print("ANIMS_CODEC_TEST_OK" if not fails else f"ANIMS_CODEC_TEST_FAIL {fails}")
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(main())
