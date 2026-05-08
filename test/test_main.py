#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: @spacemany2k38
# 2026-05-03

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import re

from app import __version__
from app.core.rain import Rain, Stream, random_char, CHARSET, MessageInjector
from app.core.sources import (
    HAMLET, LOREM, get_source, read_binary_as_hex,
)
from app.utils.doc_reader import read_app_doc

REPO_ROOT = Path(__file__).resolve().parent.parent


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

    def test_message_rain(self):
        r = Rain(24, 80, message="hello world")
        self.assertIsNotNone(r.injector)

    def test_tick_messages_empty(self):
        r = Rain(24, 80)
        self.assertEqual(r.tick_messages(), [])

    def test_tick_messages_with_text(self):
        r = Rain(24, 80, message="neo")
        # Run enough ticks for the cooldown to expire and a word to appear
        cells = []
        for _ in range(100):
            r.tick()
            cells = r.tick_messages()
            if cells:
                break
        self.assertGreater(len(cells), 0)


class TestMessageInjector(unittest.TestCase):
    def test_init(self):
        inj = MessageInjector("follow the white rabbit")
        self.assertEqual(len(inj.words), 4)

    def test_empty_text(self):
        inj = MessageInjector("")
        self.assertEqual(inj.words, [])
        cells = inj.tick(24, 80)
        self.assertEqual(cells, [])

    def test_produces_cells(self):
        inj = MessageInjector("wake up")
        inj._cooldown = 0
        # Run enough ticks for chars to fall into view
        cells = []
        for _ in range(50):
            cells = inj.tick(24, 80)
            if cells:
                break
        self.assertGreater(len(cells), 0)

    def test_cells_have_phases(self):
        inj = MessageInjector("test")
        inj._cooldown = 0
        cells = []
        for _ in range(50):
            cells = inj.tick(24, 80)
            if cells:
                break
        for row, col, ch, phase in cells:
            self.assertIn(phase, ("glow", "hold", "fade"))


class TestSources(unittest.TestCase):
    def test_hamlet_is_string(self):
        self.assertIsInstance(HAMLET, str)
        self.assertIn("To be, or not to be", HAMLET)

    def test_lorem_is_string(self):
        self.assertIsInstance(LOREM, str)
        self.assertIn("Lorem ipsum", LOREM)

    def test_get_source_hamlet(self):
        text = get_source('hamlet')
        self.assertIn("To be", text)

    def test_get_source_lorem(self):
        text = get_source('lorem')
        self.assertIn("dolor sit amet", text)

    def test_get_source_matrix_returns_hex(self):
        text = get_source('matrix')
        self.assertIsInstance(text, str)
        # Hex output is pairs of hex digits separated by spaces
        parts = text.split()
        for part in parts[:20]:
            self.assertEqual(len(part), 2)
            int(part, 16)  # raises ValueError if not valid hex

    def test_get_source_unknown(self):
        with self.assertRaises(ValueError):
            get_source('unknown')

    def test_get_source_matrix_with_file(self):
        # Read this test file itself as binary hex
        text = get_source('matrix', path=__file__)
        parts = text.split()
        self.assertGreater(len(parts), 10)
        for part in parts[:20]:
            self.assertEqual(len(part), 2)
            int(part, 16)

    def test_get_source_matrix_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            get_source('matrix', path='/nonexistent/file.bin')

    def test_read_binary_as_hex(self):
        result = read_binary_as_hex(Path(__file__), max_bytes=16)
        parts = result.split()
        self.assertEqual(len(parts), 16)


class TestVersionConsistency(unittest.TestCase):
    """All version references must match. CI catches drift."""

    def _read_program_version(self):
        text = (REPO_ROOT / ".program").read_text()
        for line in text.splitlines():
            if line.startswith("version:"):
                return line.split(":", 1)[1].strip()
        self.fail(".program has no version field")

    def _read_doc_version(self):
        doc = read_app_doc('matrix')
        version = doc.get('version')
        self.assertIsNotNone(version, "doc/matrix.yaml has no VERSION")
        return version

    def _read_readme_version(self):
        text = (REPO_ROOT / "README.md").read_text()
        match = re.search(r'^Version:\s*(.+)$', text, re.MULTILINE)
        self.assertIsNotNone(match, "README.md has no Version: line")
        return match.group(1).strip()

    def test_all_versions_match(self):
        program_v = self._read_program_version()
        doc_v = self._read_doc_version()
        readme_v = self._read_readme_version()
        init_v = __version__

        self.assertEqual(
            init_v, program_v,
            f"__init__.py ({init_v}) != .program ({program_v})",
        )
        self.assertEqual(
            init_v, doc_v,
            f"__init__.py ({init_v}) != doc/matrix.yaml ({doc_v})",
        )
        self.assertEqual(
            init_v, readme_v,
            f"__init__.py ({init_v}) != README.md ({readme_v})",
        )


if __name__ == "__main__":
    unittest.main()
