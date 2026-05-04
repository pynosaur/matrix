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
    """Reverse gravity — rain decelerates to a stop, then drifts upward."""

    def __init__(self):
        super().__init__(duration=4.0)

    def transform(self, row, col, rows, cols):
        t = self.progress
        # Phase 1 (0–0.35): decelerate — chars slow down, barely move
        # Phase 2 (0.35–1.0): reverse — chars drift upward, accelerating
        if t < 0.35:
            # Slow-down phase: slight upward resistance, gets stronger
            strength = (t / 0.35) ** 2  # ease-in
            shift = int(row * strength * 0.08)
            new_row = row - shift
        else:
            # Reverse phase: accelerate upward
            rev_t = (t - 0.35) / 0.65  # 0→1 within reverse phase
            strength = rev_t ** 1.5  # accelerating
            shift = int(row * strength * 0.6)
            new_row = row - shift

        if 0 <= new_row < rows:
            return new_row, col
        return None


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
    'b': 'burst',
    'f': 'flash',
    'r': 'reverse',
    'x': 'scatter',
}


def create_effect(name, rows, cols):
    """Create an effect by name."""
    if name == 'burst':
        return BurstEffect(rows, cols)
    elif name == 'flash':
        return FlashEffect()
    elif name == 'reverse':
        return ReverseEffect()
    elif name == 'scatter':
        return ScatterEffect()
    return None
