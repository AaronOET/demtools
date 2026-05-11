#!/usr/bin/env python
"""
Command-line utility to display descriptions of demtools functionality.
"""

import argparse
import sys
from textwrap import dedent

TOOL_DESCRIPTIONS = {
    'chgnodata': """
        Convert nodata values for TIF raster files.

        This tool reads one or more GeoTIFF files, replaces the existing nodata
        value with a new one (re-writing pixel data), and saves a backup of the
        original file in the RAS_BAK/ directory.

        Examples:
            chgnodata -a                  # Process all *.tif (nodata=-999)
            chgnodata -a -v -9999         # Process all *.tif, set nodata to -9999
            chgnodata -i dem.tif          # Process a single file (nodata=-999)
            chgnodata -i dem.tif -v -9999 # Process a single file, set nodata to -9999
    """,
    'setnodata': """
        Define a nodata value for TIF raster files without modifying pixel data.

        This tool updates only the nodata *metadata* of one or more GeoTIFF files
        without touching the actual pixel values. A backup is saved in RAS_BAK/.

        Examples:
            setnodata -a                  # Process all *.tif (nodata=-999)
            setnodata -a -v -9999         # Process all *.tif, define nodata as -9999
            setnodata -i dem.tif          # Process a single file (nodata=-999)
            setnodata -i dem.tif -v -9999 # Process a single file, define nodata as -9999
    """,
    'csv2tif': """
        Convert a plain-numeric CSV raster grid to a GeoTIFF file.

        The CSV must contain only numeric values arranged in rows (top→bottom) and
        columns (left→right), with no header row. Georeferencing parameters
        (lower-left corner coordinates, cell size, EPSG) can be provided via options.

        Examples:
            csv2tif -i grid.csv
            csv2tif -i grid.csv -o dem.tif
            csv2tif -i grid.csv --xll 250000 --yll 2500000 --cellsize 5 --epsg 32648
            csv2tif -i grid.csv -n -9999
    """,
}


def main():
    parser = argparse.ArgumentParser(
        prog='demtools-info',
        description='Display descriptions of demtools commands',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        'tool',
        nargs='?',
        choices=list(TOOL_DESCRIPTIONS.keys()),
        help='Tool name to describe (omit to list all tools)',
    )
    args = parser.parse_args()

    if args.tool:
        print(f"\n--- {args.tool} ---")
        print(dedent(TOOL_DESCRIPTIONS[args.tool]))
    else:
        print("\nDEMTOOLS — DEM raster utility commands\n")
        for tool, desc in TOOL_DESCRIPTIONS.items():
            first_line = dedent(desc).strip().splitlines()[0]
            print(f"  {tool:<14} {first_line}")
        print("\nRun 'demtools-info <tool>' for details on a specific command.")


if __name__ == "__main__":
    main()
