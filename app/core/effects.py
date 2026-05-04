#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: @spacemany2k38
# 2026-05-03

"""Interactive effects — triggered by keypresses during the rain."""

import math
import random
import time


class Effect:
    """Base class for transient visual effects."""

    def __init__(self, duration=1.0):
        self.start = time.monotonic()
        self.duration = duration

    @property
    def progress(self):
        """0.0 at start, 1.0 at end."""
        elapsed = time.monotonic() - self.start
        return min(1.0, elapsed / self.duration)

    @property
    def alive(self):
        return self.progress < 1.0

    def transform(self, row, col, rows, cols):
        """Transform a cell position. Returns (new_row, new_col) or None to hide."""
        return row, col

    def brightness_mod(self, row, col, rows, cols):
        """Return brightness multiplier for a cell (0.0–2.0)."""
        return 1.0


class WaveEffect(Effect):
    """Ripple wave — distorts columns like a sine wave passing through."""

    def __init__(self):
        super().__init__(duration=2.5)
        self.amplitude = random.uniform(2.0, 4.0)
        self.frequency = random.uniform(0.15, 0.3)
        self.direction = random.choice([-1, 1])

    def transform(self, row, col, rows, cols):
        t = self.progress
        # Wave travels across columns
        phase = self.direction * (col * self.frequency - t * 8)
        # Amplitude fades in and out
        amp = self.amplitude * math.sin(t * math.pi)
        offset = int(amp * math.sin(phase))
        new_row = row + offset
        if 0 <= new_row < rows:
            return new_row, col
        return None


class BurstEffect(Effect):
    """Explosion from center — pushes characters outward briefly."""

    def __init__(self, rows, cols):
        super().__init__(duration=1.5)
        self.cy = rows // 2
        self.cx = cols // 2
        self.force = random.uniform(8, 14)

    def transform(self, row, col, rows, cols):
        t = self.progress
        # Force peaks at start, decays
        strength = self.force * (1.0 - t) ** 2
        dx = col - self.cx
        dy = row - self.cy
        dist = math.sqrt(dx * dx + dy * dy) + 0.1
        # Push outward, strongest near center
        push = strength / (dist * 0.3 + 1)
        new_row = int(row + (dy / dist) * push)
        new_col = int(col + (dx / dist) * push)
        if 0 <= new_row < rows and 0 <= new_col < cols:
            return new_row, new_col
        return None


class FlashEffect(Effect):
    """Screen flash — everything goes bright white then fades back."""

    def __init__(self):
        super().__init__(duration=0.8)

    def brightness_mod(self, row, col, rows, cols):
        t = self.progress
        # Sharp spike at start, quick decay
        return 1.0 + 3.0 * (1.0 - t) ** 4


class ReverseEffect(Effect):
    """Briefly reverses gravity — streams appear to fall upward."""

    def __init__(self):
        super().__init__(duration=2.0)

    def transform(self, row, col, rows, cols):
        t = self.progress
        # Mirror vertically, blend in/out
        blend = math.sin(t * math.pi)  # 0 -> 1 -> 0
        mirror_row = rows - 1 - row
        new_row = int(row + (mirror_row - row) * blend)
        if 0 <= new_row < rows:
            return new_row, col
        return None


class DenseEffect(Effect):
    """Sudden downpour — massively increases density temporarily."""

    def __init__(self):
        super().__init__(duration=3.0)

    @property
    def density_multiplier(self):
        t = self.progress
        # Ramps up, holds, fades
        return 1.0 + 4.0 * math.sin(t * math.pi)


class SlowMoEffect(Effect):
    """Slow motion — everything crawls for a moment."""

    def __init__(self):
        super().__init__(duration=3.0)

    @property
    def speed_multiplier(self):
        t = self.progress
        # Dips to 0.15x at peak, eases in/out
        return 1.0 - 0.85 * math.sin(t * math.pi)


class ScatterEffect(Effect):
    """Characters scatter randomly from their positions then reform."""

    def __init__(self):
        super().__init__(duration=2.0)

    def transform(self, row, col, rows, cols):
        t = self.progress
        # Scatter peaks in the middle, reforms at end
        intensity = math.sin(t * math.pi) * 3
        if intensity < 0.1:
            return row, col
        dr = int(random.gauss(0, intensity))
        dc = int(random.gauss(0, intensity))
        new_row = max(0, min(rows - 1, row + dr))
        new_col = max(0, min(cols - 1, col + dc))
        return new_row, new_col


# Map of key -> effect factory
EFFECT_KEYS = {
    'w': 'wave',
    'b': 'burst',
    'f': 'flash',
    'r': 'reverse',
    'd': 'dense',
    's': 'slow',
    'x': 'scatter',
}


def create_effect(name, rows, cols):
    """Create an effect by name."""
    if name == 'wave':
        return WaveEffect()
    elif name == 'burst':
        return BurstEffect(rows, cols)
    elif name == 'flash':
        return FlashEffect()
    elif name == 'reverse':
        return ReverseEffect()
    elif name == 'dense':
        return DenseEffect()
    elif name == 'slow':
        return SlowMoEffect()
    elif name == 'scatter':
        return ScatterEffect()
    return None
