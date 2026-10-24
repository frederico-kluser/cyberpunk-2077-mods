"""Golden test for the Simd codec: REAL vanilla data round-trip.

1. decode the pristine Nue `recoil_shoulder` Simd buffer (real game data)
2. re-encode it with anims_write_simd
3. decode the re-encoded blob and compare every transform
4. patch the clip in the .anims JSON -> CR2W deserialize

python3 test_anims_simd.py <base1.anims.json> <out_dir>
"""

import base64
import json
import os
import struct
import sys

import anims_write_simd as sw


def q_close(a, b, eps=2e-3):
    # quaternions: compare up to sign
    d = sum(x * y for x, y in zip(a, b))
    return all(abs(x - y) <= eps for x, y in zip(a, b)) or all(abs(x + y) <= eps for x, y in zip(a, b))


def main():
    src_json, out_dir = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)

    doc = json.load(open(src_json, encoding="utf-8"))
    target = None
    for entry in doc["Data"]["RootChunk"]["animations"]:
        anim = entry["Data"]["animation"]["Data"]
        if anim["name"]["$value"] == "recoil_shoulder":
            target = anim
    assert target is not None

    buf = target["animBuffer"]["Data"]
    hdr = {
        "numFrames": buf["numFrames"],
        "numJoints": buf["numJoints"],
        "numExtraJoints": buf["numExtraJoints"],
        "duration": buf["duration"],
        "isScaleConstant": buf["isScaleConstant"],
        "isTrackConstant": buf["isTrackConstant"],
        "numTranslationsToCopy": buf["numTranslationsToCopy"],
        "numTranslationsToEvalAlignedToSimd": buf["numTranslationsToEvalAlignedToSimd"],
        "quantizationBits": buf["quantizationBits"],
        "numTracks": buf["numTracks"],
    }
    blob = base64.b64decode(buf["inplaceCompressedBuffer"]["Bytes"])
    print(f"source: frames={hdr['numFrames']} joints={hdr['numJoints']} "
          f"copy={hdr['numTranslationsToCopy']} eval={hdr['numTranslationsToEvalAlignedToSimd']} "
          f"bits={hdr['quantizationBits']} blob={len(blob)}B")

    # 1. decode real data
    dec1 = sw.decode_simd(blob, hdr)

    # 2. re-encode from the decoded transforms
    built = sw.encode_simd(dec1["frames"], dec1["duration"], hdr["quantizationBits"])
    print(f"re-encoded: blob={len(built['blob'])}B copy={built['header']['numTranslationsToCopy']} "
          f"eval={built['header']['numTranslationsToEvalAlignedToSimd']}")
    same_size = len(built["blob"]) == len(blob)
    print(f"[{'OK' if same_size else 'WARN'}] blob size {'matches' if same_size else 'differs'} "
          f"({len(built['blob'])} vs {len(blob)})")

    # 3. decode again and compare
    hdr2 = dict(hdr)
    hdr2.update(built["header"])
    dec2 = sw.decode_simd(built["blob"], hdr2)

    t_err = r_err = 0.0
    n = 0
    for f in range(len(dec1["frames"])):
        for j in range(len(dec1["frames"][f])):
            a, b = dec1["frames"][f][j], dec2["frames"][f][j]
            t_err += max(abs(x - y) for x, y in zip(a["t"], b["t"]))
            if not q_close(a["r"], b["r"]):
                r_err += 1
            n += 1
    t_err /= n
    print(f"roundtrip: mean|t| err={t_err:.2e} m, rotation mismatches={r_err}/{n}")

    ok_rt = t_err < 2e-3 and r_err == 0
    print(f"[{'OK' if ok_rt else 'FAIL'}] decode->encode->decode on REAL game data")
    if not ok_rt:
        print("SIMD_CODEC_TEST_FAIL")
        return 1

    # 4. patch the clip -> CR2W test target
    result = sw.write_clip(doc, "recoil_shoulder", dec1["frames"], dec1["duration"], hdr["quantizationBits"])
    patched = os.path.join(out_dir, "w_handgun__tsunami_nue__base1.anims.json")
    json.dump(doc, open(patched, "w", encoding="utf-8"), indent=1)
    print(f"[OK] patched clip -> {result}")
    print("SIMD_CODEC_TEST_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
