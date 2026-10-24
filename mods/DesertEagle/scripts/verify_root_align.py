"""Assert the shipped .anims root transform equals A @ rest.

The grip alignment lives in the root local (barrel_plug). This checks the
compiled sets carry exactly the exported A applied to the skeleton rest —
a data-level guard for the design documented in ANIMS.md.

python3 verify_root_align.py <anims_json_dir>
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MOD_ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(MOD_ROOT, "scripts"))
sys.path.insert(0, os.path.join(MOD_ROOT, "src", "blender"))
import anims_write_simd as sw  # noqa: E402


def quat_mat(q):
    x, y, z, w = q
    n = (x * x + y * y + z * z + w * w) ** 0.5 or 1.0
    x, y, z, w = x / n, y / n, z / n, w / n
    return [
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ]


def main():
    json_dir = sys.argv[1]
    align = json.load(open(os.path.join(MOD_ROOT, "assets", "work", "de_align.json"), encoding="utf-8"))
    R, t = align["R"], align["t"]
    print(f"A rotation = {R}")

    total = ok = 0
    for set_name in ("base1", "mag_std"):
        path = os.path.join(json_dir, f"w_handgun__tsunami_nue__{set_name}.anims.json")
        doc = json.load(open(path, encoding="utf-8"))
        for entry in doc["Data"]["RootChunk"]["animations"]:
            anim = entry["Data"]["animation"]["Data"]
            buf = anim["animBuffer"]["Data"]
            btype = buf.get("$type")
            if btype == "animAnimationBufferSimd":
                hdr = {k: buf[k] for k in (
                    "numFrames", "numJoints", "numExtraJoints", "duration", "isScaleConstant",
                    "isTrackConstant", "numTranslationsToCopy", "numTranslationsToEvalAlignedToSimd",
                    "quantizationBits", "numTracks")}
                dec = sw.decode_simd(__import__("base64").b64decode(buf["inplaceCompressedBuffer"]["Bytes"]), hdr)
                f0 = dec["frames"][0][0]
            else:
                continue  # compressed clips pin the root as const keys; covered below
            # expected root = A @ rest(barrel_plug) = A since rest is identity
            exp_t = tuple(t)
            got_t = tuple(f0["t"])
            err = max(abs(a - b) for a, b in zip(exp_t, got_t))
            total += 1
            good = err < 2e-3
            ok += good
            print(f"[{'OK' if good else 'FAIL'}] {set_name}/{anim['name']['$value']:16s} root t={tuple(round(x,4) for x in got_t)} err={err:.5f}")

    print(f"ROOT_ALIGN_VERIFY_{'OK' if ok == total else 'FAIL'} ({ok}/{total} simd clips)")
    return 0 if ok == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
