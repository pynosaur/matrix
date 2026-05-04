#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: @spacemany2k38
# 2026-05-03

"""Matrix digital rain engine — the core simulation."""

import random

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
    """A single falling stream (column of characters)."""

    __slots__ = (
        "col", "speed", "head", "length", "chars", "age",
        "depth", "mutate_rate", "_tick_acc",
    )

    def __init__(self, col, rows, depth=1.0):
        self.col = col
        self.depth = depth                    # 0.3–1.0, affects brightness
        self.speed = random.uniform(0.4, 1.6) * depth
        self.length = random.randint(4, rows)
        self.head = random.randint(-rows, -1)  # start off-screen
        self.chars = [random_char() for _ in range(self.length)]
        self.age = 0
        self.mutate_rate = random.uniform(0.02, 0.12)
        self._tick_acc = 0.0

    def tick(self, rows):
        """Advance the stream; returns True while alive."""
        self._tick_acc += self.speed
        while self._tick_acc >= 1.0:
            self._tick_acc -= 1.0
            self.head += 1
            self.age += 1

        # Randomly mutate some characters (they flicker in the movie)
        for i in range(self.length):
            if random.random() < self.mutate_rate:
                self.chars[i] = random_char()

        # Stream is dead once fully off-screen below
        tail = self.head - self.length
        return tail < rows

    def visible_cells(self, rows):
        """Yield (row, char, brightness) for on-screen cells.

        brightness: 0.0–1.0 where 1.0 is the bright head.
        """
        for i in range(self.length):
            row = self.head - i
            if 0 <= row < rows:
                # Brightness fades from head (1.0) to tail (0.0)
                bright = 1.0 - (i / self.length)
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
    """The full Matrix rain simulation across the terminal."""

    def __init__(self, rows, cols, message=None):
        self.rows = rows
        self.cols = cols
        self.streams = []
        self._spawn_cooldowns = {}  # col -> ticks until next spawn allowed
        self.injector = MessageInjector(message) if message else None

    def resize(self, rows, cols):
        self.rows = rows
        self.cols = cols

    def tick(self):
        """Advance one frame."""
        # Update existing streams, remove dead ones
        alive = []
        for s in self.streams:
            if s.tick(self.rows):
                alive.append(s)
        self.streams = alive

        # Spawn new streams
        for col in range(self.cols):
            # Cool down per column to avoid overlap
            if col in self._spawn_cooldowns:
                self._spawn_cooldowns[col] -= 1
                if self._spawn_cooldowns[col] > 0:
                    continue
                del self._spawn_cooldowns[col]

            # Probability of spawning
            if random.random() < 0.015:
                depth = random.choice([0.3, 0.5, 0.7, 1.0, 1.0, 1.0])
                s = Stream(col, self.rows, depth)
                self.streams.append(s)
                self._spawn_cooldowns[col] = random.randint(5, 25)

    def tick_messages(self):
        """Advance message injector; returns cell list or empty."""
        if self.injector:
            return self.injector.tick(self.rows, self.cols)
        return []
