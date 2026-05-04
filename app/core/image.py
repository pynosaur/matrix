#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: @spacemany2k38
# 2026-05-03

"""Convert images to ASCII art for Matrix rain overlay.

Supports: PNG, JPEG, GIF, BMP, PPM/PGM via platform tools.
Falls back to Pillow if available, otherwise uses macOS `sips` + raw bitmap,
or Linux `convert` (ImageMagick).
"""

import os
import struct
import subprocess
import tempfile
from pathlib import Path

from app.core.rain import random_char, CHARSET

# ASCII brightness ramp (dark to bright)
_RAMP = " .:-=+*#%@"


def image_to_grid(filepath, target_rows, target_cols):
    """Load an image and convert to a grid of (char, brightness) tuples.

    Returns a 2D list: grid[row][col] = (char, brightness)
    where brightness is 0.0 (black) to 1.0 (white).
    Returns None if the image can't be loaded.
    """
    filepath = str(filepath)
    pixels = _load_pixels(filepath, target_cols, target_rows)
    if pixels is None:
        return None

    height = len(pixels)
    width = len(pixels[0]) if height > 0 else 0

    grid = []
    for y in range(height):
        row = []
        for x in range(width):
            brightness = pixels[y][x]
            # Pick a character based on brightness
            idx = int(brightness * (len(_RAMP) - 1))
            idx = max(0, min(len(_RAMP) - 1, idx))
            ch = _RAMP[idx]
            # For very dark areas, use space (invisible in the rain)
            # For brighter areas, use the ramp character
            row.append((ch, brightness))
        grid.append(row)

    return grid


def _load_pixels(filepath, width, height):
    """Load image as grayscale pixel array (0.0–1.0), resized to width x height.

    Uses macOS sips (built-in), ImageMagick, or direct PPM/PGM parsing.
    Pure Python — no external libraries.
    """
    # Try macOS sips
    pixels = _try_sips(filepath, width, height)
    if pixels is not None:
        return pixels

    # Try ImageMagick convert
    pixels = _try_imagemagick(filepath, width, height)
    if pixels is not None:
        return pixels

    # Try reading PPM/PGM directly
    if filepath.lower().endswith(('.ppm', '.pgm', '.pnm')):
        return _read_pnm(filepath, width, height)

    return None


def _try_sips(filepath, width, height):
    """Load via macOS sips (converts to JPEG then reads raw)."""
    try:
        # Check if sips exists
        result = subprocess.run(
            ['which', 'sips'], capture_output=True, timeout=5,
        )
        if result.returncode != 0:
            return None

        with tempfile.TemporaryDirectory() as tmpdir:
            # Convert to bitmap format we can parse
            ppm_path = os.path.join(tmpdir, 'img.ppm')

            # Use sips to resize and export as bitmap
            # First resize
            subprocess.run(
                ['sips', '-z', str(height * 2), str(width),
                 filepath, '--out', os.path.join(tmpdir, 'resized.png')],
                capture_output=True, timeout=10,
            )

            # Then use python to read with the imageio approach
            # Actually, use `sips -s format bmp` and parse BMP
            bmp_path = os.path.join(tmpdir, 'img.bmp')
            result = subprocess.run(
                ['sips', '-s', 'format', 'bmp',
                 '-z', str(height), str(width),
                 filepath, '--out', bmp_path],
                capture_output=True, timeout=10,
            )
            if result.returncode != 0:
                return None

            return _read_bmp_grayscale(bmp_path, width, height)
    except (subprocess.TimeoutExpired, OSError, Exception):
        return None


def _try_imagemagick(filepath, width, height):
    """Load via ImageMagick convert."""
    try:
        result = subprocess.run(
            ['which', 'convert'], capture_output=True, timeout=5,
        )
        if result.returncode != 0:
            return None

        with tempfile.TemporaryDirectory() as tmpdir:
            pgm_path = os.path.join(tmpdir, 'img.pgm')
            subprocess.run(
                ['convert', filepath, '-resize', f'{width}x{height}!',
                 '-colorspace', 'Gray', '-depth', '8', pgm_path],
                capture_output=True, timeout=10,
            )
            if os.path.exists(pgm_path):
                return _read_pnm(pgm_path, width, height)
    except (subprocess.TimeoutExpired, OSError, Exception):
        return None
    return None


def _read_bmp_grayscale(filepath, target_w, target_h):
    """Read a BMP file and extract grayscale pixels."""
    try:
        with open(filepath, 'rb') as f:
            # BMP header
            header = f.read(54)
            if len(header) < 54 or header[:2] != b'BM':
                return None

            data_offset = struct.unpack_from('<I', header, 10)[0]
            width = struct.unpack_from('<i', header, 18)[0]
            height = struct.unpack_from('<i', header, 22)[0]
            bpp = struct.unpack_from('<H', header, 28)[0]

            bottom_up = height > 0
            height = abs(height)

            f.seek(data_offset)
            row_size = ((width * (bpp // 8) + 3) // 4) * 4

            rows = []
            for _ in range(height):
                row_data = f.read(row_size)
                row = []
                bytes_per_pixel = bpp // 8
                for x in range(min(width, target_w)):
                    offset = x * bytes_per_pixel
                    if bytes_per_pixel >= 3:
                        b = row_data[offset]
                        g = row_data[offset + 1]
                        r = row_data[offset + 2]
                        # Luminance
                        gray = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
                    elif bytes_per_pixel == 1:
                        gray = row_data[offset] / 255.0
                    else:
                        gray = 0.5
                    row.append(gray)
                rows.append(row)

            if bottom_up:
                rows.reverse()

            # Truncate or pad to target dimensions
            rows = rows[:target_h]
            return rows
    except (OSError, struct.error, IndexError):
        return None


def _read_pnm(filepath, target_w, target_h):
    """Read PPM/PGM (P5/P6 binary or P2/P3 text)."""
    try:
        with open(filepath, 'rb') as f:
            magic = f.readline().strip()

            # Skip comments
            line = f.readline()
            while line.startswith(b'#'):
                line = f.readline()

            dims = line.split()
            width, height = int(dims[0]), int(dims[1])
            maxval = int(f.readline().strip())

            if magic == b'P5':  # Binary PGM
                pixels = []
                for y in range(min(height, target_h)):
                    row = []
                    data = f.read(width)
                    for x in range(min(width, target_w)):
                        row.append(data[x] / maxval)
                    pixels.append(row)
                return pixels

            elif magic == b'P6':  # Binary PPM
                pixels = []
                for y in range(min(height, target_h)):
                    row = []
                    data = f.read(width * 3)
                    for x in range(min(width, target_w)):
                        r = data[x * 3]
                        g = data[x * 3 + 1]
                        b = data[x * 3 + 2]
                        gray = (0.299 * r + 0.587 * g + 0.114 * b) / maxval
                        row.append(gray)
                    pixels.append(row)
                return pixels

    except (OSError, ValueError, IndexError):
        return None
    return None
