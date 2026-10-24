"""Round-trip test for the BCn codec: encode -> decode -> measure error."""

import numpy as np

import bcn

# realistic (smooth) content: clipped gradients + mild noise, like game textures
yy, xx = np.mgrid[0:64, 0:64]
base = np.clip((xx + yy) * 2, 0, 255).astype(np.uint8)
rng = np.random.default_rng(42)

gray = np.clip(base.astype(np.int32) + rng.integers(-10, 11, (64, 64)), 0, 255).astype(np.uint8)
enc = bcn.encode_bc4(gray)
dec = bcn.decode_bc4(enc, 64, 64)
err4 = np.abs(dec.astype(np.int32) - gray.astype(np.int32)).mean()
print(f"BC4 bytes={len(enc)} (expect 2048) mean_abs_err={err4:.2f}")

rg = np.stack([gray, np.clip(255 - base, 0, 255).astype(np.uint8)], axis=2)
enc5 = bcn.encode_bc5(rg)
dec5 = bcn.decode_bc5(enc5, 64, 64)
err5 = np.abs(dec5.astype(np.int32) - rg.astype(np.int32)).mean()
print(f"BC5 bytes={len(enc5)} (expect 4096) mean_abs_err={err5:.2f}")

rgb = np.stack([gray, np.clip(base // 2, 0, 255).astype(np.uint8), np.full((64, 64), 200, np.uint8)], axis=2)
enc1 = bcn.encode_bc1(rgb)
dec1 = bcn.decode_bc1(enc1, 64, 64)
err1 = np.abs(dec1.astype(np.int32) - rgb.astype(np.int32)).mean()
print(f"BC1 bytes={len(enc1)} (expect 2048) mean_abs_err={err1:.2f}")

ok = len(enc) == 2048 and len(enc5) == 4096 and len(enc1) == 2048
ok = ok and err4 < 6 and err5 < 6 and err1 < 12
print("BCN_TEST_OK" if ok else "BCN_TEST_FAIL")
