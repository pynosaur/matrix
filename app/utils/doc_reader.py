#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: @spacemany2k38
# 2026-05-03

"""Reads YAML doc files shipped alongside the binary."""

import os
from pathlib import Path


def read_app_doc(app_name):
    """Read the YAML doc for an app, returning a dict of fields."""
    doc_file = _find_doc(app_name)
    if doc_file is None or not doc_file.exists():
        return {}
    return _parse_simple_yaml(doc_file.read_text())


def _find_doc(app_name):
    candidates = [
        Path(__file__).resolve().parent.parent.parent / "doc" / f"{app_name}.yaml",
        Path(os.getcwd()) / "doc" / f"{app_name}.yaml",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def _parse_simple_yaml(text):
    result = {}
    current_key = None
    current_list = None

    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if not raw_line[0].isspace() and ":" in stripped:
            if current_key and current_list is not None:
                result[current_key] = current_list

            key, _, value = stripped.partition(":")
            key = key.strip().lower()
            value = value.strip()

            if value == ">":
                current_key = key
                current_list = None
                result[key] = ""
            elif value == "":
                result[key] = ""
                current_key = key
                current_list = []
            elif value.startswith('"') and value.endswith('"'):
                result[key] = value[1:-1]
                current_key = key
                current_list = None
            else:
                result[key] = value
                current_key = key
                current_list = None
        elif raw_line[0].isspace():
            if stripped.startswith("- "):
                item = stripped[2:].strip()
                if item.startswith('"') and item.endswith('"'):
                    item = item[1:-1]
                if current_list is None:
                    current_list = []
                current_list.append(item)
            else:
                if current_key and current_key in result and isinstance(
                    result[current_key], str,
                ):
                    result[current_key] += (
                        (" " if result[current_key] else "") + stripped
                    )

    if current_key and current_list is not None:
        result[current_key] = current_list

    return result
