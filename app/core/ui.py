#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: @spacemany2k38
# 2026-05-03

"""Curses-based renderer for the Matrix rain."""

import curses
import subprocess
import time

from app.core.effects import EFFECT_KEYS, create_effect


def _init_colors():
    """Set up color pairs for depth-based green shading."""
    curses.start_color()
    curses.use_default_colors()

    if curses.can_change_color() and curses.COLORS >= 256:
        # Use 256-color palette for rich greens
        # Pair 1: bright head (white-green glow)
        curses.init_pair(1, 15, -1)       # bright white head
        # Pair 2: bright green (near head)
        curses.init_pair(2, 46, -1)       # vivid green
        # Pair 3: medium green
        curses.init_pair(3, 40, -1)       # green
        # Pair 4: dim green
        curses.init_pair(4, 34, -1)       # darker green
        # Pair 5: very dim green (tail)
        curses.init_pair(5, 22, -1)       # very dark green
        # Pair 6: near-black (fading out)
        curses.init_pair(6, 236, -1)      # almost gone

        # Dim depth variants (background columns)
        # Pair 7: dim bright
        curses.init_pair(7, 28, -1)
        # Pair 8: dim medium
        curses.init_pair(8, 22, -1)
        # Pair 9: dim dark
        curses.init_pair(9, 236, -1)

        # Message injection colors
        # Pair 10: message glow (bright white)
        curses.init_pair(10, 15, -1)
        # Pair 11: message hold (vivid green, readable)
        curses.init_pair(11, 46, -1)
        # Pair 12: message fade (dimming out)
        curses.init_pair(12, 34, -1)
    else:
        # Fallback: basic 8-color
        curses.init_pair(1, curses.COLOR_WHITE, -1)
        curses.init_pair(2, curses.COLOR_GREEN, -1)
        curses.init_pair(3, curses.COLOR_GREEN, -1)
        curses.init_pair(4, curses.COLOR_GREEN, -1)
        curses.init_pair(5, curses.COLOR_GREEN, -1)
        curses.init_pair(6, curses.COLOR_GREEN, -1)
        curses.init_pair(7, curses.COLOR_GREEN, -1)
        curses.init_pair(8, curses.COLOR_GREEN, -1)
        curses.init_pair(9, curses.COLOR_GREEN, -1)
        curses.init_pair(10, curses.COLOR_WHITE, -1)
        curses.init_pair(11, curses.COLOR_GREEN, -1)
        curses.init_pair(12, curses.COLOR_GREEN, -1)


def _pick_msg_color(phase):
    """Choose color for injected message characters."""
    if phase == "glow":
        return curses.color_pair(10) | curses.A_BOLD
    elif phase == "hold":
        return curses.color_pair(11) | curses.A_BOLD
    else:  # fade
        return curses.color_pair(12)


def _pick_color(brightness, depth, is_head):
    """Choose color pair + attributes based on brightness and depth."""
    if is_head:
        # Leading character: bright white glow
        if depth > 0.6:
            return curses.color_pair(1) | curses.A_BOLD
        else:
            return curses.color_pair(2) | curses.A_BOLD

    if depth >= 0.7:
        # Foreground stream — full brightness range
        if brightness > 0.85:
            return curses.color_pair(2) | curses.A_BOLD
        elif brightness > 0.65:
            return curses.color_pair(2)
        elif brightness > 0.45:
            return curses.color_pair(3)
        elif brightness > 0.25:
            return curses.color_pair(4)
        elif brightness > 0.10:
            return curses.color_pair(5)
        else:
            return curses.color_pair(6)
    else:
        # Background stream — dim, adds depth
        if brightness > 0.6:
            return curses.color_pair(7)
        elif brightness > 0.3:
            return curses.color_pair(8)
        else:
            return curses.color_pair(9)


def _hide_titlebar():
    """Hide the Terminal window title bar text on launch."""
    script = (
        'tell application "Terminal"\n'
        '  set myWindow to front window\n'
        '  set myTab to selected tab of myWindow\n'
        '  set custom title of myTab to " "\n'
        '  set title displays device name of myWindow to false\n'
        '  set title displays shell path of myWindow to false\n'
        '  set title displays window size of myWindow to false\n'
        '  set title displays file name of myWindow to false\n'
        '  set title displays custom title of myWindow to false\n'
        'end tell'
    )
    try:
        subprocess.run(
            ['osascript', '-e', script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=3,
        )
    except (OSError, subprocess.TimeoutExpired):
        pass


def _restore_titlebar():
    """Restore the Terminal window title bar on exit."""
    script = (
        'tell application "Terminal"\n'
        '  set myWindow to front window\n'
        '  set myTab to selected tab of myWindow\n'
        '  set title displays device name of myWindow to true\n'
        '  set title displays shell path of myWindow to true\n'
        '  set title displays window size of myWindow to true\n'
        '  set title displays custom title of myWindow to true\n'
        'end tell'
    )
    try:
        subprocess.run(
            ['osascript', '-e', script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=3,
        )
    except (OSError, subprocess.TimeoutExpired):
        pass


def _toggle_fullscreen():
    """Toggle macOS native fullscreen."""
    try:
        subprocess.Popen(
            ['osascript', '-e',
             'tell application "System Events" to '
             'keystroke "f" using {control down, command down}'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError:
        pass


def run_rain(stdscr, rain):
    """Main render loop."""
    curses.curs_set(0)         # hide cursor
    stdscr.nodelay(True)       # non-blocking getch
    stdscr.timeout(33)         # ~30 fps

    _init_colors()
    stdscr.bkgd(' ', curses.color_pair(0))

    # Hide title bar clutter on launch
    _hide_titlebar()

    target_fps = 30
    frame_time = 1.0 / target_fps
    effects = []  # active effects list
    is_fullscreen = False

    while True:
        t0 = time.monotonic()

        key = stdscr.getch()
        if key in (ord('q'), ord('Q'), 27):  # q, Q, Esc
            if is_fullscreen:
                _toggle_fullscreen()
            _restore_titlebar()
            break

        # Trigger effects from keypresses
        if key != -1:
            ch = chr(key) if 0 <= key < 256 else ''
            if ch == 'f':
                _toggle_fullscreen()
                is_fullscreen = not is_fullscreen
            elif ch == 'r':
                rain.toggle_direction()
            elif ch in EFFECT_KEYS:
                rows, cols = stdscr.getmaxyx()
                eff = create_effect(EFFECT_KEYS[ch], rows, cols)
                if eff:
                    effects.append(eff)

        # Prune dead effects
        effects = [e for e in effects if e.alive]

        # Handle resize
        rows, cols = stdscr.getmaxyx()
        rain.resize(rows, cols)

        # Advance simulation
        rain.tick()
        msg_cells = rain.tick_messages()

        # Render
        stdscr.erase()

        # Build a set of message cell positions so rain doesn't overwrite them
        msg_positions = set()
        for row, col, ch, phase in msg_cells:
            if 0 <= row < rows and 0 <= col < cols:
                msg_positions.add((row, col))

        for stream in rain.streams:
            for idx, (row, ch, brightness) in enumerate(
                stream.visible_cells(rows)
            ):
                if stream.col >= cols:
                    continue
                if (row, stream.col) in msg_positions:
                    continue  # message takes priority

                # Apply effects to position
                draw_row, draw_col = row, stream.col
                bright_mod = 1.0
                for eff in effects:
                    result = eff.transform(draw_row, draw_col, rows, cols)
                    if result is None:
                        draw_row = -1  # skip this cell
                        break
                    draw_row, draw_col = result
                    bright_mod *= eff.brightness_mod(row, stream.col, rows, cols)

                if draw_row < 0 or draw_row >= rows or draw_col < 0 or draw_col >= cols:
                    continue

                is_head = (idx == 0)
                eff_brightness = min(1.0, brightness * bright_mod)
                attr = _pick_color(eff_brightness, stream.depth, is_head)
                try:
                    stdscr.addstr(draw_row, draw_col, ch, attr)
                except curses.error:
                    pass

        # Render message cells on top
        for row, col, ch, phase in msg_cells:
            if 0 <= row < rows and 0 <= col < cols:
                attr = _pick_msg_color(phase)
                try:
                    stdscr.addstr(row, col, ch, attr)
                except curses.error:
                    pass

        stdscr.refresh()

        # Frame rate limiting
        elapsed = time.monotonic() - t0
        sleep_time = frame_time - elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)
