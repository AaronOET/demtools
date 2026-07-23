#!/usr/bin/env python
"""
Top-level `demtools` command. Running `demtools -h` (or with no arguments)
prints the same information shown by `demtools-info`. Running `demtools -v`
prints the installed demtools version. Running `demtools -cl` (or
`--change-log`) prints the changelog.
"""

import sys

from . import __version__, describe
from .changelog import CHANGELOG


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
        print(f"demtools {__version__}")
        return

    if args[0] in ('-cl', '--change-log'):
        print(CHANGELOG.strip())
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
