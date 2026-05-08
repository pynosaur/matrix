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
from app.core.rain import BIN_CHARSET, DEC_CHARSET, HEX_CHARSET, ZED_CHARSET, Rain
from app.core.sources import get_source
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

    source_flags = {'--hamlet': 'hamlet', '--lorem': 'lorem'}
    charset_flags = {
        '--hex': HEX_CHARSET,
        '--bin': BIN_CHARSET,
        '--dec': DEC_CHARSET,
        '--zed': ZED_CHARSET,
    }

    charset = None
    if args and args[0] in charset_flags:
        charset = charset_flags[args[0]]
        args = args[1:]
    elif args and args[0] == '--rain':
        if len(args) < 2:
            print("matrix: --rain requires a file path", file=sys.stderr)
            return 1
        rain_path = Path(args[1])
        if not rain_path.is_file():
            print(
                f"matrix: {args[1]}: No such file", file=sys.stderr,
            )
            return 1
        try:
            raw = rain_path.read_text(errors='replace')
            raw = raw.replace('\x00', '')
            chars = sorted(set(ch for ch in raw if not ch.isspace()))
            if not chars:
                print(
                    "matrix: --rain file has no usable characters",
                    file=sys.stderr,
                )
                return 1
            charset = chars
        except OSError as e:
            print(f"matrix: {args[1]}: {e}", file=sys.stderr)
            return 1
        args = args[2:]
        if args and args[0] == '--':
            args = args[1:]

    if args and args[0] == "--self":
        base = Path(__file__).resolve().parent
        src_dir = base / "_src"  # Nuitka bundled source
        if not src_dir.is_dir():
            src_dir = base / "core"
        src_file = src_dir / "rain.py"
        try:
            message = src_file.read_text(errors='replace')
            message = message.replace('\x00', '')
        except OSError as e:
            print(f"matrix: {e}", file=sys.stderr)
            return 1
        args = args[1:]

    elif args and args[0] in source_flags:
        source_name = source_flags[args[0]]
        args = args[1:]
        try:
            message = get_source(source_name)
        except (FileNotFoundError, OSError) as e:
            print(f"matrix: {e}", file=sys.stderr)
            return 1

    else:
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
            elif args[0] == "-x":
                if len(args) < 2:
                    print("matrix: -x requires a file path", file=sys.stderr)
                    return 1
                try:
                    hex_text = get_source('matrix', path=args[1])
                    message = (message + " " + hex_text) if message else hex_text
                except (FileNotFoundError, OSError) as e:
                    print(f"matrix: {args[1]}: {e}", file=sys.stderr)
                    return 1
                args = args[2:]
            else:
                break

        if args:
            text = " ".join(args)
            message = (message + " " + text) if message else text

    try:
        def _run(stdscr):
            rows, cols = stdscr.getmaxyx()
            rain = Rain(rows, cols, message=message, charset=charset)
            run_rain(stdscr, rain)

        curses.wrapper(_run)
    except KeyboardInterrupt:
        pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
