"""Verify the final .anims: compile CR2W and check the slide really moves."""

import base64
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))
import anims_write_simd as sw

root = r"C:\Users\kluse\Projects\cyberpunk-2077\mods\DesertEagle"
fin = os.path.join(root, "assets", "work", "anims_final")
bin_dir = os.path.join(fin, "bin")
os.makedirs(bin_dir, exist_ok=True)

wk = r"C:\Users\kluse\Tools\WolvenKit\9.1.0\wolvenkit-cli.cmd"
for name in ("base1", "mag_std"):
    src = os.path.join(fin, f"w_handgun__tsunami_nue__{name}.anims.json")
    res = subprocess.run([wk, "convert", "deserialize", src, "-o", bin_dir, "-v", "Detailed"],
                         capture_output=True, text=True)
    ok = "Success" in (res.stdout + res.stderr)
    print(f"[{'OK' if ok else 'FAIL'}] CR2W {name}.anims")
    if not ok:
        for line in (res.stdout + res.stderr).splitlines():
            if "Exception" in line:
                print("   ", line.strip()[:160])
        raise SystemExit(1)

# movement sanity: decode base1 recoil_shoulder, slide (index 5) translation varies
doc = json.load(open(os.path.join(fin, "w_handgun__tsunami_nue__base1.anims.json"), encoding="utf-8"))
for entry in doc["Data"]["RootChunk"]["animations"]:
    anim = entry["Data"]["animation"]["Data"]
    if anim["name"]["$value"] != "recoil_shoulder":
        continue
    buf = anim["animBuffer"]["Data"]
    hdr = {k: buf[k] for k in (
        "numFrames", "numJoints", "numExtraJoints", "duration", "isScaleConstant",
        "isTrackConstant", "numTranslationsToCopy", "numTranslationsToEvalAlignedToSimd",
        "quantizationBits", "numTracks")}
    dec = sw.decode_simd(base64.b64decode(buf["inplaceCompressedBuffer"]["Bytes"]), hdr)
    slide = [f[5]["t"] for f in dec["frames"]]
    dp = max(max(abs(a[i] - b[i]) for i in range(3)) for a, b in zip(slide, slide[1:]))
    rot = [f[5]["r"] for f in dec["frames"]]
    dr = max(max(abs(a[i] - b[i]) for i in range(4)) for a, b in zip(rot, rot[1:]))
    print(f"slide translation range: max frame delta = {dp:.4f} m")
    print(f"slide rotation    range: max frame delta = {dr:.4f}")
    ok = dp > 1e-3 or dr > 1e-3
    print(f"[{'OK' if ok else 'FAIL'}] slide (bone 5) animates across frames")
    print("ANIMS_FINAL_VERIFY_OK" if ok else "ANIMS_FINAL_VERIFY_FAIL")
