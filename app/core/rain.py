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
HEX_CHARSET = list("0123456789abcdef")
BIN_CHARSET = list("01")
DEC_CHARSET = list("0123456789")
ZED_CHARSET = list("abcdefghijklmnopqrstuvwxyz")


def random_char(charset=None):
    """Pick a random character from the given charset (default: CHARSET)."""
    return random.choice(charset or CHARSET)


class Stream:
    """A single falling stream (column of characters)."""

    __slots__ = (
        "col", "speed", "head", "length", "chars", "age",
        "depth", "mutate_rate", "_tick_acc", "direction", "charset",
    )

    def __init__(self, col, rows, depth=1.0, direction=1, charset=None):
        self.col = col
        self.charset = charset
        self.depth = depth                    # 0.3-1.0, affects brightness
        self.speed = random.uniform(0.4, 1.6) * depth
        self.length = random.randint(4, rows)
        self.direction = direction            # 1 = down, -1 = up
        if direction == 1:
            self.head = random.randint(-rows, -1)   # start above screen
        else:
            self.head = random.randint(rows, 2 * rows)  # start below
        self.chars = [random_char(charset) for _ in range(self.length)]
        self.age = 0
        self.mutate_rate = random.uniform(0.02, 0.12)
        self._tick_acc = 0.0

    def tick(self, rows):
        """Advance the stream; returns True while alive."""
        self._tick_acc += self.speed
        while self._tick_acc >= 1.0:
            self._tick_acc -= 1.0
            self.head += self.direction
            self.age += 1

        # Randomly mutate some characters (they flicker in the movie)
        for i in range(self.length):
            if random.random() < self.mutate_rate:
                self.chars[i] = random_char(self.charset)

        # Stream is dead once fully off-screen
        if self.direction == 1:
            tail = self.head - self.length
            return tail < rows
        else:
            tail = self.head + self.length
            return tail >= 0

    def visible_cells(self, rows):
        """Yield (row, char, brightness) for on-screen cells.

        brightness: 0.0–1.0 where 1.0 is the bright head.
        """
        for i in range(self.length):
            row = self.head - i * self.direction
            if 0 <= row < rows:
                # Brightness fades from head (1.0) to tail (0.0)
                bright = 1.0 - (i / self.length)
                yield row, self.chars[i], bright


class MessageInjector:
    """Injects words from a message into the rain.

    Each character drips down its column to land at the target row,
    shimmers while visible (mutating between the real char and random glyphs),
    then washes away downward. Letters arrive at staggered, irregular intervals
    so the word resolves organically from the cascade.
    """

    def __init__(self, text, charset=None):
        self.charset = charset
        self.words = [w for w in text.split() if w]
        self.word_idx = 0
        self._cooldown = random.randint(20, 50)
        # Each cell: {row, col, target_row, char, state, timer, shimmer}
        self._cells = []

    def tick(self, rows, cols):
        """Advance one frame. Returns list of (row, col, char, phase)."""
        # Advance existing cells
        new_cells = []
        for cell in self._cells:
            self._advance_cell(cell, rows)
            if cell['state'] != 'dead':
                new_cells.append(cell)
        self._cells = new_cells

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
            target_row = random.randint(4, max(4, rows - 5))

            for i, ch in enumerate(word):
                start_delay = i * random.randint(3, 7) + random.randint(0, 5)
                cell = {
                    'row': random.randint(-8, -1),
                    'col': col + i,
                    'target_row': target_row,
                    'char': ch,
                    'state': 'falling',
                    'timer': 0,
                    'delay': start_delay,
                    'hold_time': random.randint(55, 85),
                    'fall_speed': random.uniform(0.6, 1.4),
                    'fall_acc': 0.0,
                    'shimmer_rate': random.uniform(0.08, 0.2),
                }
                self._cells.append(cell)

            self._cooldown = random.randint(40, 100)

        return self._get_cells()

    def _advance_cell(self, cell, rows):
        """Advance a single character cell through its lifecycle."""
        if cell['delay'] > 0:
            cell['delay'] -= 1
            return

        state = cell['state']

        if state == 'falling':
            # Drip down toward target row
            cell['fall_acc'] += cell['fall_speed']
            while cell['fall_acc'] >= 1.0:
                cell['fall_acc'] -= 1.0
                cell['row'] += 1
            if cell['row'] >= cell['target_row']:
                cell['row'] = cell['target_row']
                cell['state'] = 'lock'
                cell['timer'] = cell['hold_time']

        elif state == 'lock':
            # Character is in place — shimmer occasionally
            cell['timer'] -= 1
            if cell['timer'] <= 0:
                cell['state'] = 'wash'
                cell['timer'] = 0

        elif state == 'wash':
            # Wash away downward
            cell['timer'] += 1
            cell['row'] += 1
            if cell['row'] >= rows:
                cell['state'] = 'dead'

    def _get_cells(self):
        """Return renderable cells with phase info."""
        cells = []
        for cell in self._cells:
            if cell['delay'] > 0:
                continue
            if cell['state'] == 'dead':
                continue

            row = cell['row']
            col = cell['col']
            ch = cell['char']

            if cell['state'] == 'falling':
                # While falling, show random chars (it's still in the rain)
                if random.random() < 0.6:
                    ch = random_char(self.charset)
                phase = "glow"
            elif cell['state'] == 'lock':
                # Shimmer: occasionally show a random char then snap back
                if random.random() < cell['shimmer_rate']:
                    ch = random_char(self.charset)
                # Phase based on timer
                if cell['timer'] > cell['hold_time'] * 0.6:
                    phase = "glow"
                else:
                    phase = "hold"
            else:  # wash
                # Fading out, show random chars more often
                if random.random() < 0.4 + cell['timer'] * 0.05:
                    ch = random_char(self.charset)
                phase = "fade"

            cells.append((row, col, ch, phase))
        return cells


class Rain:
    """The full Matrix rain simulation across the terminal."""

    def __init__(self, rows, cols, message=None, charset=None):
        self.rows = rows
        self.cols = cols
        self.charset = charset
        self.streams = []
        self._spawn_cooldowns = {}  # col -> ticks until next spawn allowed
        self.injector = MessageInjector(message, charset) if message else None
        self.direction = 1  # 1 = down, -1 = up

    def toggle_direction(self):
        """Flip rain direction. Existing streams keep their direction
        and die out naturally."""
        self.direction *= -1

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
                s = Stream(col, self.rows, depth, self.direction, self.charset)
                self.streams.append(s)
                self._spawn_cooldowns[col] = random.randint(5, 25)

    def tick_messages(self):
        """Advance message injector; returns cell list or empty."""
        if self.injector:
            return self.injector.tick(self.rows, self.cols)
        return []
