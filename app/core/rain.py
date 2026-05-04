#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: @spacemany2k38
# 2026-05-03

"""Matrix digital rain engine — the core simulation."""

import random
import math

# Half-width katakana (authentic Matrix feel) + digits + latin fragments
_KATAKANA = list(
    "ｦｧｨｩｪｫｬｭｮｯｰｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝ"
)
_DIGITS = list("0123456789")
_SYMBOLS = list(":<>{}[]|/\\=+*^~!?@#$%&")
_LATIN = list("abcdefghijklmnopqrstuvwxyz")

CHARSET = _KATAKANA + _DIGITS + _SYMBOLS + _LATIN


def random_char():
    """Pick a random character from the Matrix charset."""
    return random.choice(CHARSET)


class Stream:
    """A single falling stream (column of characters).

    Organic: speed drifts over time, mutation rate varies per-character,
    brightness has slight jitter to simulate CRT phosphor irregularity.
    """

    __slots__ = (
        "col", "speed", "head", "length", "chars", "age",
        "depth", "mutate_rates", "_tick_acc", "_base_speed",
        "_speed_phase",
    )

    def __init__(self, col, rows, depth=1.0):
        self.col = col
        self.depth = depth
        self._base_speed = random.uniform(0.3, 1.8) * depth
        self.speed = self._base_speed
        self._speed_phase = random.uniform(0, math.pi * 2)

        # Length varies widely — some are tiny bursts, some long cascades
        self.length = self._pick_length(rows)
        self.head = random.randint(-rows, -1)
        self.chars = [random_char() for _ in range(self.length)]
        self.age = 0
        # Per-character mutation rates (irregular shimmer)
        self.mutate_rates = [
            random.uniform(0.01, 0.18) for _ in range(self.length)
        ]
        self._tick_acc = 0.0

    @staticmethod
    def _pick_length(rows):
        """Biased length: many short, some medium, few very long."""
        half = max(7, rows // 2)
        r = random.random()
        if r < 0.3:
            return random.randint(3, 6)       # short drips
        elif r < 0.7:
            return random.randint(6, half)
        else:
            return random.randint(half, max(half, rows))

    def tick(self, rows):
        """Advance the stream; returns True while alive."""
        # Speed drifts sinusoidally (organic pulsing)
        self._speed_phase += 0.05
        drift = math.sin(self._speed_phase) * 0.15
        self.speed = max(0.15, self._base_speed + drift)

        self._tick_acc += self.speed
        while self._tick_acc >= 1.0:
            self._tick_acc -= 1.0
            self.head += 1
            self.age += 1

        # Per-character mutation (irregular flicker)
        for i in range(self.length):
            if random.random() < self.mutate_rates[i]:
                self.chars[i] = random_char()
                # Occasionally shift the mutation rate itself
                if random.random() < 0.05:
                    self.mutate_rates[i] = random.uniform(0.01, 0.18)

        tail = self.head - self.length
        return tail < rows

    def visible_cells(self, rows):
        """Yield (row, char, brightness) for on-screen cells.

        Brightness fades nonlinearly and has subtle jitter.
        """
        for i in range(self.length):
            row = self.head - i
            if 0 <= row < rows:
                if i == 0:
                    yield row, self.chars[i], 1.0
                    continue
                # Nonlinear fade — holds brightness longer near head, drops faster at tail
                t = i / self.length
                bright = max(0.0, 1.0 - (t ** 0.6))
                # Subtle phosphor jitter
                bright += random.uniform(-0.04, 0.04)
                bright = max(0.0, min(1.0, bright))
                yield row, self.chars[i], bright


class MessageInjector:
    """Injects words from a message into the rain.

    Words materialize character by character — each letter emerges from
    the rain at its position, glows bright, holds, then dissolves back.
    The timing is staggered and irregular, like someone reading them out
    of the cascade.
    """

    def __init__(self, text):
        self.words = [w for w in text.split() if w]
        self.word_idx = 0
        self._cooldown = random.randint(20, 50)
        self._active = []  # (row, col, char, ttl, appear_delay)

    def tick(self, rows, cols):
        """Advance one frame. Returns list of (row, col, char, phase)."""
        # Age active cells
        new_active = []
        for row, col, ch, ttl, delay in self._active:
            if delay > 0:
                new_active.append((row, col, ch, ttl, delay - 1))
            elif ttl > 0:
                new_active.append((row, col, ch, ttl - 1, 0))
        self._active = new_active

        # Cool down between words
        if self._cooldown > 0:
            self._cooldown -= 1
            return self._get_cells()

        # Place next word
        if self.words:
            word = self.words[self.word_idx % len(self.words)]
            self.word_idx += 1

            max_col = cols - len(word)
            if max_col < 0:
                word = word[:cols]
                max_col = 0

            col = random.randint(0, max(0, max_col))
            row = random.randint(3, max(3, rows - 4))

            # Stagger each character with irregular delays
            for i, ch in enumerate(word):
                # Each char appears with a slightly random delay
                delay = i * random.randint(2, 5) + random.randint(0, 3)
                ttl = random.randint(50, 75)
                self._active.append((row, col + i, ch, ttl, delay))

            self._cooldown = random.randint(35, 90)

        return self._get_cells()

    def _get_cells(self):
        """Return renderable cells with phase info."""
        cells = []
        for row, col, ch, ttl, delay in self._active:
            if delay > 0:
                continue  # not yet visible
            if ttl > 40:
                phase = "glow"
            elif ttl > 12:
                phase = "hold"
            else:
                phase = "fade"
            cells.append((row, col, ch, phase))
        return cells


class Rain:
    """The full Matrix rain simulation across the terminal.

    Organic spawning: density oscillates over time (the rain breathes),
    columns spawn in clusters with gaps, and occasional solitary drips
    appear and vanish quickly.
    """

    def __init__(self, rows, cols, message=None):
        self.rows = rows
        self.cols = cols
        self.streams = []
        self._spawn_cooldowns = {}
        self.injector = MessageInjector(message) if message else None
        self._frame = 0
        self._density_phase = random.uniform(0, math.pi * 2)
        # Hot zones: columns that tend to spawn more
        self._hot_zones = self._gen_hot_zones(cols)

    def _gen_hot_zones(self, cols):
        """Create clusters of 'active' columns — some areas rain heavy, others sparse."""
        zones = [0.3] * cols  # base probability weight per column
        # Create 3-6 hot clusters
        num_clusters = random.randint(3, min(6, cols // 10 + 1))
        for _ in range(num_clusters):
            center = random.randint(0, cols - 1)
            width = random.randint(3, min(12, cols // 4))
            for c in range(max(0, center - width), min(cols, center + width)):
                dist = abs(c - center) / width
                zones[c] += (1.0 - dist) * 0.7
        return zones

    def resize(self, rows, cols):
        self.rows = rows
        if cols != self.cols:
            self.cols = cols
            self._hot_zones = self._gen_hot_zones(cols)
        self.rows = rows

    def tick(self):
        """Advance one frame."""
        self._frame += 1

        # Update existing streams, remove dead ones
        alive = []
        for s in self.streams:
            if s.tick(self.rows):
                alive.append(s)
        self.streams = alive

        # Breathing density — oscillates slowly
        self._density_phase += 0.008
        breath = 0.5 + 0.5 * math.sin(self._density_phase)
        # Base spawn probability modulated by breath
        base_prob = 0.008 + 0.014 * breath

        # Spawn new streams
        for col in range(self.cols):
            if col in self._spawn_cooldowns:
                self._spawn_cooldowns[col] -= 1
                if self._spawn_cooldowns[col] > 0:
                    continue
                del self._spawn_cooldowns[col]

            # Probability weighted by hot zone and breathing
            prob = base_prob * self._hot_zones[col]

            if random.random() < prob:
                depth = self._pick_depth()
                s = Stream(col, self.rows, depth)
                self.streams.append(s)
                # Cooldown varies — sometimes quick succession, sometimes long gap
                self._spawn_cooldowns[col] = self._pick_cooldown()

        # Occasional solitary drips (single chars that flash and vanish)
        if random.random() < 0.06:
            col = random.randint(0, max(0, self.cols - 1))
            s = Stream(col, self.rows, depth=random.uniform(0.4, 0.8))
            s.length = random.randint(1, 3)
            s.chars = [random_char() for _ in range(s.length)]
            s.mutate_rates = [0.3] * s.length  # flicker fast
            s.head = random.randint(0, self.rows - 1)
            self.streams.append(s)

        # Slowly drift hot zones (the rain pattern shifts over time)
        if self._frame % 120 == 0:
            self._shift_hot_zones()

    @staticmethod
    def _pick_depth():
        """Weighted depth — mostly foreground, some background."""
        r = random.random()
        if r < 0.15:
            return random.uniform(0.2, 0.4)
        elif r < 0.35:
            return random.uniform(0.4, 0.7)
        else:
            return random.uniform(0.7, 1.0)

    @staticmethod
    def _pick_cooldown():
        """Variable cooldown — sometimes bursts, sometimes gaps."""
        r = random.random()
        if r < 0.2:
            return random.randint(2, 5)   # quick burst
        elif r < 0.7:
            return random.randint(8, 20)
        else:
            return random.randint(20, 50)  # long pause

    def _shift_hot_zones(self):
        """Slightly drift the hot zones so the pattern evolves."""
        cols = self.cols
        new_zones = self._hot_zones[:]
        shift = random.choice([-2, -1, 1, 2])
        if shift > 0:
            new_zones = [0.3] * shift + new_zones[:cols - shift]
        else:
            new_zones = new_zones[-shift:] + [0.3] * (-shift)
        # Blend old and new for smooth transition
        self._hot_zones = [
            0.7 * old + 0.3 * new
            for old, new in zip(self._hot_zones, new_zones[:cols])
        ]

    def tick_messages(self):
        """Advance message injector; returns cell list or empty."""
        if self.injector:
            return self.injector.tick(self.rows, self.cols)
        return []
