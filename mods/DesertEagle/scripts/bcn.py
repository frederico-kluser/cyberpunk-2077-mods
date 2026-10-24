"""BCn block texture compression (BC1 / BC4 / BC5) in numpy.

The REDengine `.mesh`-style texture container (`.xbm`) stores pixels as BCn
blocks (see docs/PIPELINE.md "Formato das texturas"). This module encodes and
decodes:

  BC1  8 B/block   RGB (2x RGB565 endpoints + 2-bit indices)
  BC4  8 B/block   single channel (2 endpoints + 3-bit indices)
  BC5 16 B/block   two BC4 blocks -> normal XY (Z reconstructed by the engine)

Encoding is a solid baseline (endpoint min/max + nearest palette index) —
correct and fast; quality is fine for game textures. decode_* lets callers
verify round-trips numerically.
"""

from __future__ import annotations

import numpy as np


def _bc4_block(values: np.ndarray) -> bytes:
    """Encode one 4x4 single-channel block (values 0..255) as BC4."""
    flat = values.reshape(16)
    lo = int(flat.min())
    hi = int(flat.max())
    if lo == hi:
        return bytes([lo, hi]) + b"\x00" * 6

    # 8-value palette: a0 > a1 -> 6 interpolated + 0 + 255
    palette = np.empty(8, dtype=np.int32)
    palette[0] = hi
    palette[1] = lo
    for i in range(1, 7):
        palette[1 + i] = ((7 - i) * hi + i * lo) // 7
    palette[7] = 255 if hi > lo else 0

    diffs = np.abs(flat.astype(np.int32)[:, None] - palette[None, :])
    idx = diffs.argmin(axis=1).astype(np.uint8)

    bits = np.zeros(16, dtype=np.uint64)
    for t in range(16):
        bits[t] = int(idx[t]) & 0x7
    packed = 0
    for t in range(16):
        packed |= int(bits[t]) << (3 * t)
    out = bytes([hi, lo]) + packed.to_bytes(6, "little")
    return out


def _bc4_decode(block: bytes) -> np.ndarray:
    hi, lo = block[0], block[1]
    palette = np.empty(8, dtype=np.int32)
    palette[0] = hi
    palette[1] = lo
    if hi > lo:
        for i in range(1, 7):
            palette[1 + i] = ((7 - i) * hi + i * lo) // 7
        palette[7] = 255
    else:
        for i in range(1, 5):
            palette[1 + i] = ((5 - i) * hi + i * lo) // 5
        palette[5] = 0
        palette[6] = 255
        palette[7] = 0 if hi <= lo else 255
    packed = int.from_bytes(block[2:8], "little")
    out = np.empty(16, dtype=np.uint8)
    for t in range(16):
        out[t] = palette[(packed >> (3 * t)) & 0x7]
    return out.reshape(4, 4)


def _bc1_block(rgb: np.ndarray) -> bytes:
    """Encode one 4x4 RGB block (values 0..255) as BC1."""
    flat = rgb.reshape(16, 3).astype(np.int32)
    lum = flat @ np.array([2, 5, 1])  # rough luminance
    lo_i = int(lum.argmin())
    hi_i = int(lum.argmax())
    c0 = flat[hi_i]
    c1 = flat[lo_i]

    def pack565(c):
        return ((int(c[0]) >> 3) << 11) | ((int(c[1]) >> 2) << 5) | (int(c[2]) >> 3)

    p0, p1 = pack565(c0), pack565(c1)
    if p0 < p1:
        p0, p1 = p1, p0
        c0, c1 = c1, c0

    def unpack565(p):
        return np.array([((p >> 11) & 31) * 255 // 31, ((p >> 5) & 63) * 255 // 63, (p & 31) * 255 // 31], dtype=np.int32)

    e0, e1 = unpack565(p0), unpack565(p1)
    pal = np.array([e0, e1, (2 * e0 + e1) // 3, (e0 + 2 * e1) // 3], dtype=np.int32)
    diffs = ((flat[:, None, :] - pal[None, :, :]) ** 2).sum(axis=2)
    idx = diffs.argmin(axis=1)

    bits = 0
    for t in range(16):
        bits |= int(idx[t]) << (2 * t)
    return p0.to_bytes(2, "little") + p1.to_bytes(2, "little") + bits.to_bytes(4, "little")


def _bc1_decode(block: bytes) -> np.ndarray:
    p0 = int.from_bytes(block[0:2], "little")
    p1 = int.from_bytes(block[2:4], "little")
    bits = int.from_bytes(block[4:8], "little")

    def unpack565(p):
        return np.array([((p >> 11) & 31) * 255 // 31, ((p >> 5) & 63) * 255 // 63, (p & 31) * 255 // 31], dtype=np.int32)

    e0, e1 = unpack565(p0), unpack565(p1)
    if p0 > p1:
        pal = np.array([e0, e1, (2 * e0 + e1) // 3, (e0 + 2 * e1) // 3], dtype=np.int32)
    else:
        pal = np.array([e0, e1, (e0 + e1) // 2, np.zeros(3, dtype=np.int32)], dtype=np.int32)
    pal = np.clip(pal, 0, 255).astype(np.uint8)
    out = np.empty((16, 3), dtype=np.uint8)
    for t in range(16):
        out[t] = pal[(bits >> (2 * t)) & 0x3]
    return out.reshape(4, 4, 3)


def encode_bc4(gray: np.ndarray) -> bytes:
    """Encode an HxW uint8 single channel image as BC4 blocks."""
    h, w = gray.shape
    out = bytearray()
    for y in range(0, h, 4):
        for x in range(0, w, 4):
            out += _bc4_block(gray[y:y + 4, x:x + 4])
    return bytes(out)


def decode_bc4(data: bytes, h: int, w: int) -> np.ndarray:
    out = np.zeros((h, w), dtype=np.uint8)
    pos = 0
    for y in range(0, h, 4):
        for x in range(0, w, 4):
            out[y:y + 4, x:x + 4] = _bc4_decode(data[pos:pos + 8])
            pos += 8
    return out


def encode_bc5(rg: np.ndarray) -> bytes:
    """Encode an HxWx2 uint8 image (two channels) as BC5 blocks."""
    r = encode_bc4(np.ascontiguousarray(rg[:, :, 0]))
    g = encode_bc4(np.ascontiguousarray(rg[:, :, 1]))
    out = bytearray()
    blocks = len(r) // 8
    for b in range(blocks):
        out += r[b * 8:(b + 1) * 8]
        out += g[b * 8:(b + 1) * 8]
    return bytes(out)


def decode_bc5(data: bytes, h: int, w: int) -> np.ndarray:
    n_blocks_y = (h + 3) // 4
    n_blocks_x = (w + 3) // 4
    r = bytearray()
    g = bytearray()
    for b in range(n_blocks_y * n_blocks_x):
        r += data[b * 16:b * 16 + 8]
        g += data[b * 16 + 8:b * 16 + 16]
    out = np.zeros((h, w, 2), dtype=np.uint8)
    out[:, :, 0] = decode_bc4(bytes(r), h, w)
    out[:, :, 1] = decode_bc4(bytes(g), h, w)
    return out


def encode_bc1(rgb: np.ndarray) -> bytes:
    """Encode an HxWx3 uint8 image as BC1 blocks."""
    h, w = rgb.shape[:2]
    out = bytearray()
    for y in range(0, h, 4):
        for x in range(0, w, 4):
            out += _bc1_block(rgb[y:y + 4, x:x + 4])
    return bytes(out)


def decode_bc1(data: bytes, h: int, w: int) -> np.ndarray:
    out = np.zeros((h, w, 3), dtype=np.uint8)
    pos = 0
    for y in range(0, h, 4):
        for x in range(0, w, 4):
            out[y:y + 4, x:x + 4] = _bc1_decode(data[pos:pos + 8])
            pos += 8
    return out
