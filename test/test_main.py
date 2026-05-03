#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: @spacemany2k38
# 2026-05-03

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.rain import Rain, Stream, random_char, CHARSET


class TestRandomChar(unittest.TestCase):
    def test_returns_string(self):
        ch = random_char()
        self.assertIsInstance(ch, str)
        self.assertEqual(len(ch), 1)

    def test_in_charset(self):
        for _ in range(100):
            self.assertIn(random_char(), CHARSET)


class TestStream(unittest.TestCase):
    def test_init(self):
        s = Stream(col=5, rows=24, depth=1.0)
        self.assertEqual(s.col, 5)
        self.assertEqual(len(s.chars), s.length)
        self.assertTrue(s.head < 0)

    def test_tick_advances(self):
        s = Stream(col=0, rows=24, depth=1.0)
        s.speed = 1.0
        initial_head = s.head
        s.tick(24)
        self.assertGreaterEqual(s.head, initial_head)

    def test_dies_when_off_screen(self):
        s = Stream(col=0, rows=10, depth=1.0)
        s.head = 100
        s.length = 3
        alive = s.tick(10)
        self.assertFalse(alive)

    def test_visible_cells_in_range(self):
        s = Stream(col=0, rows=24, depth=1.0)
        s.head = 10
        s.length = 5
        s.chars = ['a', 'b', 'c', 'd', 'e']
        cells = list(s.visible_cells(24))
        for row, ch, bright in cells:
            self.assertGreaterEqual(row, 0)
            self.assertLess(row, 24)
            self.assertGreaterEqual(bright, 0.0)
            self.assertLessEqual(bright, 1.0)

    def test_visible_cells_head_is_brightest(self):
        s = Stream(col=0, rows=24, depth=1.0)
        s.head = 10
        s.length = 5
        s.chars = ['a', 'b', 'c', 'd', 'e']
        cells = list(s.visible_cells(24))
        if cells:
            self.assertEqual(cells[0][2], 1.0)


class TestRain(unittest.TestCase):
    def test_init(self):
        r = Rain(24, 80)
        self.assertEqual(r.rows, 24)
        self.assertEqual(r.cols, 80)
        self.assertEqual(len(r.streams), 0)

    def test_resize(self):
        r = Rain(24, 80)
        r.resize(50, 120)
        self.assertEqual(r.rows, 50)
        self.assertEqual(r.cols, 120)

    def test_tick_spawns_streams(self):
        r = Rain(24, 80)
        # Run many ticks — some streams should spawn
        for _ in range(200):
            r.tick()
        self.assertGreater(len(r.streams), 0)

    def test_tick_removes_dead_streams(self):
        r = Rain(24, 80)
        s = Stream(col=0, rows=24, depth=1.0)
        s.head = 100
        s.length = 3
        r.streams.append(s)
        r.tick()
        # Dead stream should have been removed (or new ones spawned)
        dead = [st for st in r.streams if st is s]
        self.assertEqual(len(dead), 0)


if __name__ == "__main__":
    unittest.main()
