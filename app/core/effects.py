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
    """Horizontal wave — propagates from one side, displaces rows smoothly."""

    def __init__(self):
        super().__init__(duration=3.0)
        self.amplitude = random.uniform(1.5, 3.0)
        self.wavelength = random.uniform(8, 16)
        self.speed = random.uniform(40, 70)
        self.direction = random.choice([-1, 1])

    def transform(self, row, col, rows, cols):
        t = self.progress
        # Wave front position (travels across screen)
        front = self.direction * self.speed * t
        # Distance from wave front determines if this col is affected
        dist_from_front = col - front if self.direction > 0 else (cols - col) - front
        # Only affect columns the wave has reached
        if dist_from_front < 0 or dist_from_front > self.wavelength * 2:
            return row, col
        # Smooth envelope: wave builds up, passes, then settles
        envelope = math.sin(math.pi * dist_from_front / (self.wavelength * 2))
        offset = self.amplitude * envelope * math.sin(dist_from_front / self.wavelength * math.pi * 2)
        new_row = row + int(offset)
        if 0 <= new_row < rows:
            return new_row, col
        return row, col


class BurstEffect(Effect):
    """Shockwave ring — expands outward from center, displacing chars it passes."""

    def __init__(self, rows, cols):
        super().__init__(duration=2.0)
        self.cy = rows // 2
        self.cx = cols // 2
        # Max radius is the diagonal
        self.max_radius = math.sqrt(rows**2 + cols**2) * 0.6
        self.ring_width = random.uniform(4, 8)

    def transform(self, row, col, rows, cols):
        t = self.progress
        # Ring radius expands over time
        radius = t * self.max_radius
        # Distance from center (account for char aspect ratio)
        dx = (col - self.cx) * 0.5  # chars are ~2x taller than wide
        dy = row - self.cy
        dist = math.sqrt(dx * dx + dy * dy)

        # Only displace chars near the ring edge
        ring_dist = abs(dist - radius)
        if ring_dist > self.ring_width:
            return row, col

        # Push outward proportional to closeness to ring center
        strength = (1.0 - ring_dist / self.ring_width) * 2.0
        # Decay strength over time
        strength *= (1.0 - t * 0.5)

        if dist < 0.1:
            return row, col

        push_r = int((dy / dist) * strength)
        push_c = int(((col - self.cx) / (dist * 2 + 0.1)) * strength)
        new_row = row + push_r
        new_col = col + push_c

        if 0 <= new_row < rows and 0 <= new_col < cols:
            return new_row, new_col
        return row, col


class FlashEffect(Effect):
    """Screen flash — everything goes bright white then fades back."""

    def __init__(self):
        super().__init__(duration=0.8)

    def brightness_mod(self, row, col, rows, cols):
        t = self.progress
        # Sharp spike at start, quick decay
        return 1.0 + 3.0 * (1.0 - t) ** 4


class ReverseEffect(Effect):
    """Reverses gravity — all characters drift upward."""

    def __init__(self):
        super().__init__(duration=3.0)

    def transform(self, row, col, rows, cols):
        t = self.progress
        # Smooth ease in/out for the upward push
        strength = math.sin(t * math.pi)
        # Shift everything up — further from top = more shift
        shift = int(row * strength * 0.4)
        new_row = row - shift
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
