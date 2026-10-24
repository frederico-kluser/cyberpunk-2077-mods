"""Full CR2W round-trip check: serialize the compiled .anims back and decode
the Simd buffer — the transforms must match the ones written."""

import base64
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))
import anims_write_simd as sw

out = r"C:\Users\kluse\Projects\cyberpunk-2077\mods\DesertEagle\assets\work\anims_test"
anims = os.path.join(out, "w_handgun__tsunami_nue__base1.anims")
verify = os.path.join(out, "verify")
os.makedirs(verify, exist_ok=True)

res = subprocess.run(
    [r"C:\Users\kluse\Tools\WolvenKit\9.1.0\wolvenkit-cli.cmd",
     "convert", "serialize", anims, "-o", verify, "-v", "Minimal"],
    capture_output=True, text=True)
if "Success" not in (res.stdout + res.stderr):
    print("SERIALIZE_FAIL")
    print((res.stdout + res.stderr)[-400:])
    raise SystemExit(1)

rt = json.load(open(os.path.join(verify, "w_handgun__tsunami_nue__base1.anims.json"), encoding="utf-8"))
for entry in rt["Data"]["RootChunk"]["animations"]:
    anim = entry["Data"]["animation"]["Data"]
    if anim["name"]["$value"] != "recoil_shoulder":
        continue
    buf = anim["animBuffer"]["Data"]
    print("buffer type:", buf.get("$type"))
    hdr = {
        "numFrames": buf["numFrames"], "numJoints": buf["numJoints"],
        "numExtraJoints": buf["numExtraJoints"], "duration": buf["duration"],
        "isScaleConstant": buf["isScaleConstant"], "isTrackConstant": buf["isTrackConstant"],
        "numTranslationsToCopy": buf["numTranslationsToCopy"],
        "numTranslationsToEvalAlignedToSimd": buf["numTranslationsToEvalAlignedToSimd"],
        "quantizationBits": buf["quantizationBits"], "numTracks": buf["numTracks"],
    }
    blob = base64.b64decode(buf["inplaceCompressedBuffer"]["Bytes"])
    dec = sw.decode_simd(blob, hdr)
    print(f"frames={hdr['numFrames']} joints={hdr['numJoints']} blob={len(blob)}B")

    # compare with the source transforms (re-decode the pristine file)
    src = json.load(open(r"C:\Users\kluse\Projects\cyberpunk-2077\mods\DesertEagle\assets\_inventory\anims_json\w_handgun__tsunami_nue__base1.anims.json", encoding="utf-8"))
    for e2 in src["Data"]["RootChunk"]["animations"]:
        a2 = e2["Data"]["animation"]["Data"]
        if a2["name"]["$value"] != "recoil_shoulder":
            continue
        b2 = a2["animBuffer"]["Data"]
        h2 = {k: b2[k] for k in hdr}
        s_dec = sw.decode_simd(base64.b64decode(b2["inplaceCompressedBuffer"]["Bytes"]), h2)

    t_err = 0.0
    r_bad = 0
    n = 0
    for f in range(len(dec["frames"])):
        for j in range(len(dec["frames"][f])):
            a, b = s_dec["frames"][f][j], dec["frames"][f][j]
            t_err += max(abs(x - y) for x, y in zip(a["t"], b["t"]))
            d = sum(x * y for x, y in zip(a["r"], b["r"]))
            if not (all(abs(x - y) < 3e-3 for x, y in zip(a["r"], b["r"])) or
                    all(abs(x + y) < 3e-3 for x, y in zip(a["r"], b["r"]))):
                r_bad += 1
            n += 1
    t_err /= n
    ok = t_err < 2e-3 and r_bad == 0
    print(f"CR2W roundtrip vs vanilla source: mean|t|={t_err:.2e} rot_mismatch={r_bad}/{n}")
    print("CR2W_ANIMS_ROUNDTRIP_OK" if ok else "CR2W_ANIMS_ROUNDTRIP_FAIL")
