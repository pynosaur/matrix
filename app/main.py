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

    if args and args[0] == "--self":
        # Read core/rain.py source — the rain engine
        base = Path(__file__).resolve().parent
        src_dir = base / "_src"  # Nuitka bundled source
        if not src_dir.is_dir():
            src_dir = base / "core"  # dev fallback
        src_file = src_dir / "rain.py"
        if not src_file.is_file():
            # flat Nuitka layout
            src_file = src_dir / "rain.py"
        try:
            message = src_file.read_text(errors='replace')
            message = message.replace('\x00', '')
        except OSError as e:
            print(f"matrix: {e}", file=sys.stderr)
            return 1
        args = args[1:]

    else:
        # Parse flags
        message = None

        while args and args[0].startswith('-') and args[0] not in ('-',):
            if args[0] == "-f":
                if len(args) < 2:
                    print("matrix: -f requires a file path", file=sys.stderr)
                    return 1
                fpath = Path(args[1])
                if not fpath.is_file():
                    print(f"matrix: {args[1]}: No such file", file=sys.stderr)
                    return 1
                try:
                    file_text = fpath.read_text(errors='replace')
                    file_text = file_text.replace('\x00', '')
                    message = (message + " " + file_text) if message else file_text
                except OSError as e:
                    print(f"matrix: {args[1]}: {e}", file=sys.stderr)
                    return 1
                args = args[2:]
            else:
                break

        # Remaining args are message text
        if args:
            text = " ".join(args)
            message = (message + " " + text) if message else text

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
