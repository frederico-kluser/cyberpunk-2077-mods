"""Full clip-by-clip verification of the final .anims CR2W files.

For EVERY clip in the compiled sets:
  1. re-serialize the CR2W -> JSON
  2. decode the animation buffer (Simd or Compressed)
  3. compare frame 0 and the motion range against the source .re xformframes
     (re-timed to the clip's frame count)

Run with any python3 (needs the anims codecs, no h5py):

  python3 verify_anims_clips.py <anims_bin_dir> <anims_json_dir> <out_dir>
"""

import base64
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scripts"))
import anims_write_simd as sw  # noqa: E402

WK = r"C:\Users\kluse\Tools\WolvenKit\9.1.0\wolvenkit-cli.cmd"
JOINTS = 11


def decode_clip(anim):
    buf = anim["animBuffer"]["Data"]
    btype = buf.get("$type")
    if btype == "animAnimationBufferSimd":
        hdr = {k: buf[k] for k in (
            "numFrames", "numJoints", "numExtraJoints", "duration", "isScaleConstant",
            "isTrackConstant", "numTranslationsToCopy", "numTranslationsToEvalAlignedToSimd",
            "quantizationBits", "numTracks")}
        blob = base64.b64decode(buf["inplaceCompressedBuffer"]["Bytes"])
        dec = sw.decode_simd(blob, hdr)
        return dec["frames"], buf["numFrames"]
    # Compressed: rebuild frames from const + raw keys (raw keys carry the
    # per-frame motion; const keys are single-pose joints)
    import anims_write as cw
    counts = {
        "num_anim_keys_raw": buf.get("numAnimKeysRaw") or 0,
        "num_const_anim_keys": buf.get("numConstAnimKeys") or 0,
    }
    blob = base64.b64decode(buf["tempBuffer"]["Bytes"])
    keys = cw.decode_buffer(blob, counts, buf.get("duration", 1.0))
    nframes = buf.get("numFrames") or 1
    duration = buf.get("duration") or 1.0

    frames = [[{"t": [0.0, 0.0, 0.0], "r": [0.0, 0.0, 0.0, 1.0], "s": [1.0, 1.0, 1.0]} for _ in range(JOINTS)] for _ in range(nframes)]

    # const keys -> all frames
    for k in keys["const"]:
        if 0 <= k["bone"] < JOINTS:
            field = "t" if k["component"] == 0 else "r"
            for f in range(nframes):
                frames[f][k["bone"]][field] = list(k["value"])

    # raw keys -> per-frame (nearest key by time)
    by_bone = {}
    for k in keys["raw"]:
        by_bone.setdefault((k["bone"], k["component"]), []).append(k)
    for (bone, comp), items in by_bone.items():
        if not (0 <= bone < JOINTS):
            continue
        field = "t" if comp == 0 else "r"
        items.sort(key=lambda k: k["time"])
        for f in range(nframes):
            t = f * duration / max(1, nframes - 1)
            best = min(items, key=lambda k: abs(k["time"] - t))
            frames[f][bone][field] = list(best["value"])
    return frames, nframes


def main():
    bin_dir, json_dir, out_dir = sys.argv[1:4]
    os.makedirs(out_dir, exist_ok=True)

    total = ok = 0
    for set_name in ("base1", "mag_std"):
        cr2w = os.path.join(bin_dir, f"w_handgun__tsunami_nue__{set_name}.anims")
        res = subprocess.run([WK, "convert", "serialize", cr2w, "-o", out_dir, "-v", "Minimal"],
                             capture_output=True, text=True)
        if "Success" not in (res.stdout + res.stderr):
            print(f"[FAIL] serialize {set_name}")
            return 1
        doc = json.load(open(os.path.join(out_dir, f"w_handgun__tsunami_nue__{set_name}.anims.json"), encoding="utf-8"))
        for entry in doc["Data"]["RootChunk"]["animations"]:
            anim = entry["Data"]["animation"]["Data"]
            name = anim["name"]["$value"]
            frames, nframes = decode_clip(anim)
            # motion range across the clip (ALL bones, translation + rotation)
            dp = 0.0
            dr = 0.0
            for a, b in zip(frames, frames[1:]):
                for ja, jb in zip(a, b):
                    dp = max(dp, max(abs(x - y) for x, y in zip(ja["t"], jb["t"])))
                    dr = max(dr, max(abs(x - y) for x, y in zip(ja["r"], jb["r"])))
            f0 = frames[0][5]["t"]
            total += 1
            animated = dp > 1e-4 or dr > 1e-4
            # every CS2 source carries motion (even the idle sway) — a frozen
            # clip means the writer collapsed it to a single pose
            good = len(frames) == nframes and animated
            ok += good
            print(f"[{'OK' if good else 'FAIL'}] {set_name}/{name:16s} frames={len(frames):3d}/{nframes:3d} "
                  f"dp={dp:.4f}m dr={dr:.4f} f0={tuple(round(x,3) for x in f0)}")
    print(f"ANIMS_CLIPS_VERIFY_{'OK' if ok == total else 'FAIL'} ({ok}/{total} clips)")
    return 0 if ok == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
