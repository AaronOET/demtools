#!/usr/bin/env python
"""
Command-line utility to display descriptions of demtools functionality.
"""

import argparse
import sys
from textwrap import dedent

TOOL_DESCRIPTIONS = {
    'asproj': """
        Assign a projection to TIF raster files without modifying pixel data.

        This tool updates only the projection *metadata* of one or more GeoTIFF
        files based on an EPSG code, without touching the actual pixel values.
        A backup is saved in RAS_BAK/.

        Examples:
            asproj -a --epsg 3826         # Process all *.tif, assign EPSG:3826
            asproj -i dem.tif --epsg 3826 # Process a single file
    """,
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
    'chkdem': """
        Check DEM raster file properties (resolution, projection, extent, nodata).

        This tool reads one or more GeoTIFF files (read-only, no modification)
        and reports dimensions, pixel resolution, projection, and upper-left
        coordinates, plus per-band nodata value, nodata pixel count/percentage,
        and the valid-data min/max range.

        Examples:
            chkdem -a                  # Check all *.tif in current directory
            chkdem -i dem.tif          # Check a single file
    """,
    'deminfo': """
        Check DEM raster file properties (resolution, projection, extent, nodata).

        Alias for chkdem — reads one or more GeoTIFF files (read-only, no
        modification) and reports dimensions, pixel resolution, projection,
        and upper-left coordinates, plus per-band nodata value, nodata pixel
        count/percentage, and the valid-data min/max range.

        Examples:
            deminfo -a                  # Check all *.tif in current directory
            deminfo -i dem.tif          # Check a single file
    """,
    'defnodata': """
        Define the nodata value for TIF raster files without modifying pixel data.

        This tool updates only the nodata *metadata* of one or more GeoTIFF files
        without touching the actual pixel values. A backup is saved in RAS_BAK/.

        Examples:
            defnodata -a                  # Process all *.tif (nodata=-999)
            defnodata -a -v -9999         # Process all *.tif, define nodata as -9999
            defnodata -i dem.tif          # Process a single file (nodata=-999)
            defnodata -i dem.tif -v -9999 # Process a single file, define nodata as -9999
    """,
    'csv2tif': """
        Convert a plain-numeric CSV raster grid to a GeoTIFF file.

        The CSV must contain only numeric values arranged in rows (top→bottom) and
        columns (left→right), with no header row. Georeferencing parameters
        (origin coordinates, cell size, EPSG) can be provided via options. The
        origin can be given as the lower-left corner (--xll/--yll) or directly
        as the upper-left corner (--xul/--yul, which take precedence).

        Examples:
            csv2tif -i grid.csv
            csv2tif -i grid.csv -o dem.tif
            csv2tif -i grid.csv --xll 250000 --yll 2500000 --cellsize 5 --epsg 32648
            csv2tif -i grid.csv --xul 250000 --yul 2500100 --cellsize 5 --epsg 32648
            csv2tif -i grid.csv -n -9999
    """,
    'tif2csv': """
        Convert a GeoTIFF raster band to a plain-numeric CSV grid.

        Reverse of csv2tif. Reads a single band from a GeoTIFF (read-only, no
        modification) and writes it as a plain-numeric CSV grid, rows
        top→bottom and columns left→right, with no header row and no
        georeferencing.

        Examples:
            tif2csv -i dem.tif
            tif2csv -i dem.tif -o grid.csv
            tif2csv -i dem.tif -b 2
            tif2csv -i dem.tif --fmt %.3f
    """,
    'mvdem': """
        Relocate TIF raster files by setting a new upper-left coordinate.

        This tool updates only the geotransform origin of one or more GeoTIFF
        files, leaving pixel size/rotation and pixel data unchanged. A backup
        is saved in RAS_BAK/.

        Examples:
            mvdem -i dem.tif -x 500000 -y 2500000   # Process a single file
            mvdem -a -x 500000 -y 2500000           # Process all *.tif
    """,
    'getmask': """
        Extract the valid-data boundary of TIF raster files and save as shapefiles.

        This tool reads one or more GeoTIFF files (read-only, no modification),
        derives the valid-data mask (from nodata unless the file carries an
        explicit mask), merges the valid-data regions into a single boundary
        polygon, and saves it as an ESRI Shapefile in the output directory
        (default: SHP_MSK/).

        Examples:
            getmask -a                  # Process all *.tif in current directory
            getmask -i dem.tif          # Process a single file
            getmask -a -o SHP_MSK       # Process all *.tif, write shapefiles to SHP_MSK/
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
