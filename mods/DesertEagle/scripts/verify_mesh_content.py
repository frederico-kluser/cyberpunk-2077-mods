"""Content verification of the PACKED .mesh against the source geometry.

The renders were made from de_geometry.json — this proves the data that
actually ships (after PT_Short4N/Float16_2/Dec4/UByte4N quantization through
mesh_write.py -> CR2W) matches it. Catches quantization or packing bugs that
would only show as a distorted gun in-game.

python3 verify_mesh_content.py <shipped.mesh> <de_geometry.json>
"""

import json
import os
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mesh_buffer as mb  # noqa: E402

WK = r"C:\Users\kluse\Tools\WolvenKit\9.1.0\wolvenkit-cli.cmd"


def main():
    mesh_path, geo_path = sys.argv[1], sys.argv[2]
    # mesh_buffer reads the serialized JSON form — serialize the CR2W first
    out_dir = os.path.join(os.path.dirname(os.path.abspath(mesh_path)), "_content_verify")
    os.makedirs(out_dir, exist_ok=True)
    res = subprocess.run([WK, "convert", "serialize", mesh_path, "-o", out_dir, "-v", "Minimal"],
                         capture_output=True, text=True)
    if "Success" not in (res.stdout + res.stderr):
        print("MESH_CONTENT_VERIFY_FAIL serialize")
        return 1
    mesh_json = os.path.join(out_dir, os.path.basename(mesh_path) + ".json")
    rc = mb.load_mesh(mesh_json)
    packed = mb.decode_geometry(rc)
    source = json.load(open(geo_path, encoding="utf-8"))["chunks"]

    fails = []
    print(f"chunks: packed={len(packed)} source={len(source)}")
    if len(packed) != len(source):
        fails.append("chunk count")

    for ci, (p, s) in enumerate(zip(packed, source)):
        np_, ns = len(p["positions"]), len(s["positions"])
        print(f"\nchunk {ci}: verts packed={np_} source={ns} | indices packed={len(p['indices'])} source={len(s['indices'])}")
        if np_ != ns or len(p["indices"]) != len(s["indices"]):
            fails.append(f"chunk{ci} counts")
            continue

        pos_err = max(
            max(abs(a - b) for a, b in zip(pa, pb))
            for pa, pb in zip(p["positions"], s["positions"])
        )
        uv_err = max(
            max(abs(a - b) for a, b in zip(ua, ub))
            for ua, ub in zip(p["uvs"], s["uvs"])
        )
        w_err = max(
            max(abs(a - b) for a, b in zip(wa, wb))
            for wa, wb in zip(p["skin_weights"], s["skin_weights"])
        )
        idx_bad = sum(1 for a, b in zip(p["skin_indices"], s["skin_indices"]) if sorted(a) != sorted(b) and [x for x in a if x] != [x for x in b])
        idx_ok = p["indices"] == s["indices"]
        print(f"  max|position err| = {pos_err:.6f} m (quantization bound ~ {0.253 / 65534:.6f} m)")
        print(f"  max|uv err|       = {uv_err:.6f} (half-float bound ~ 0.001)")
        print(f"  max|weight err|   = {w_err:.6f} (ubyte bound ~ {1/255:.6f})")
        print(f"  index list exact: {idx_ok} | skin-index rows differing: {idx_bad}")

        if pos_err > 0.001:
            fails.append(f"chunk{ci} positions")
        if uv_err > 0.002:
            fails.append(f"chunk{ci} uvs")
        if w_err > 0.005:
            fails.append(f"chunk{ci} weights")
        if not idx_ok:
            fails.append(f"chunk{ci} indices")

    if not fails:
        print("\nMESH_CONTENT_VERIFY_OK")
        return 0
    print(f"\nMESH_CONTENT_VERIFY_FAIL {fails}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
