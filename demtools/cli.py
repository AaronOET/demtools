#!/usr/bin/env python
"""
Top-level `demtools` command. Running `demtools -h` (or with no arguments)
prints the same information shown by `demtools-info`.
"""

import sys
from importlib.metadata import PackageNotFoundError, version

from . import describe


def _print_version():
    try:
        pkg_version = version("demtools")
    except PackageNotFoundError:
        pkg_version = "unknown"
    print(f"demtools {pkg_version}")


def _print_info(tool=None):
    argv_backup = sys.argv
    try:
        sys.argv = ['demtools-info'] + ([tool] if tool else [])
        describe.main()
    finally:
        sys.argv = argv_backup


def main():
    args = sys.argv[1:]

    if not args or args[0] in ('-h', '--help'):
        _print_info()
        return

    if args[0] in ('-v', '--version'):
        _print_version()
        return

    tool = args[0]
    if tool in describe.TOOL_DESCRIPTIONS:
        _print_info(tool)
        return

    print(f"Unknown option or tool: {tool}", file=sys.stderr)
    print("Run 'demtools -h' to see available tools.", file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()
