#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: @spacemany2k38
# 2026-05-03

import curses
import sys
from pathlib import Path

if __name__ == "__main__" and __package__ is None:
    sys.path.append(str(Path(__file__).resolve().parent.parent))
    __package__ = "app"

from app import __version__
from app.core.rain import Rain
from app.core.ui import run_rain
from app.utils.doc_reader import read_app_doc


def print_help():
    doc = read_app_doc('matrix')

    desc = doc.get('description', 'Matrix digital rain in your terminal')
    usage = doc.get('usage', ['matrix [OPTIONS]'])
    options = doc.get('options', [])
    examples = doc.get('examples', [])

    print(f"matrix - {desc}")
    print("\nUSAGE:")
    for u in usage:
        print(f"    {u}")

    if options:
        print("\nOPTIONS:")
        for opt in options:
            print(f"    {opt}")

    if examples:
        print("\nEXAMPLES:")
        for ex in examples:
            print(f"    {ex}")


def print_version():
    doc = read_app_doc('matrix')
    print(doc.get('version', __version__))


def main():
    args = sys.argv[1:]

    if args and args[0] in ("-h", "--help", "help"):
        print_help()
        return 0

    if args and args[0] in ("-v", "--version"):
        print_version()
        return 0

    # Collect message text from arguments
    message = None
    if args:
        text_parts = []
        for arg in args:
            # If it looks like a file, read it
            p = Path(arg)
            if p.is_file():
                try:
                    text_parts.append(p.read_text(errors='replace'))
                except OSError as e:
                    print(f"matrix: cannot read {arg}: {e}", file=sys.stderr)
                    return 1
            else:
                text_parts.append(arg)
        message = " ".join(text_parts)

    try:
        def _run(stdscr):
            rows, cols = stdscr.getmaxyx()
            rain = Rain(rows, cols, message=message)
            run_rain(stdscr, rain)

        curses.wrapper(_run)
    except KeyboardInterrupt:
        pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
