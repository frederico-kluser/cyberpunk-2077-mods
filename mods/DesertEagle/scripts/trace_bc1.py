"""Trace the BC1 decoder internals for a known two-color block."""

import numpy as np

enc = bytes.fromhex("00f81f0000005555")
p0 = int.from_bytes(enc[0:2], "little")
p1 = int.from_bytes(enc[2:4], "little")
bits = int.from_bytes(enc[4:8], "little")
print(f"p0={p0:#06x} p1={p1:#06x} bits={bits:#010x}")


def unpack565(p):
    return np.array([((p >> 11) & 31) * 255 // 31, ((p >> 5) & 63) * 255 // 63, (p & 31) * 255 // 63], dtype=np.int32)


e0, e1 = unpack565(p0), unpack565(p1)
print("e0:", e0.tolist(), "e1:", e1.tolist())
print("p0 > p1:", p0 > p1)
if p0 > p1:
    pal = np.array([e0, e1, (2 * e0 + e1) // 3, (e0 + 2 * e1) // 3], dtype=np.int32)
else:
    pal = np.array([e0, e1, (e0 + e1) // 2, np.zeros(3, dtype=np.int32)], dtype=np.int32)
print("pal shape:", pal.shape)
print("pal:", pal.tolist())
for t in range(8):
    print(f"  t={t} idx={(bits >> (2*t)) & 3}")
