"""Debug BC1 with minimal blocks: constant, two-color, gradient."""

import numpy as np

import bcn

# 1. constant color block
blk = np.full((4, 4, 3), (200, 100, 50), dtype=np.uint8)
enc = bcn.encode_bc1(blk)
dec = bcn.decode_bc1(enc, 4, 4)
print("constant err:", np.abs(dec.astype(int) - blk.astype(int)).mean())
print("  enc:", enc.hex())

# 2. two-color block (half and half)
blk2 = np.zeros((4, 4, 3), dtype=np.uint8)
blk2[:2] = (255, 0, 0)
blk2[2:] = (0, 0, 255)
enc2 = bcn.encode_bc1(blk2)
dec2 = bcn.decode_bc1(enc2, 4, 4)
print("two-color err:", np.abs(dec2.astype(int) - blk2.astype(int)).mean())
print("  enc:", enc2.hex())
print("  dec row0:", dec2[0].tolist(), "row2:", dec2[2].tolist())
