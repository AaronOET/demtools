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
            asproj dem.tif --epsg 3826    # Process a single file
    """,
    'chgnodata': """
        Convert nodata values for TIF raster files.

        This tool reads one or more GeoTIFF files, replaces the existing nodata
        value with a new one (re-writing pixel data), and saves a backup of the
        original file in the RAS_BAK/ directory.

        Examples:
            chgnodata -a                  # Process all *.tif (nodata=-999)
            chgnodata -a -v -9999         # Process all *.tif, set nodata to -9999
            chgnodata dem.tif             # Process a single file (nodata=-999)
            chgnodata dem.tif -v -9999    # Process a single file, set nodata to -9999
    """,
    'chkdem': """
        Check DEM raster file properties (resolution, projection, extent, nodata).

        This tool reads one or more GeoTIFF files (read-only, no modification)
        and reports dimensions, pixel resolution, projection, and upper-left
        coordinates, plus per-band nodata value, nodata pixel count/percentage,
        and the valid-data min/max range.

        Examples:
            chkdem -a                  # Check all *.tif in current directory
            chkdem dem.tif             # Check a single file
    """,
    'deminfo': """
        Check DEM raster file properties (resolution, projection, extent, nodata).

        Alias for chkdem — reads one or more GeoTIFF files (read-only, no
        modification) and reports dimensions, pixel resolution, projection,
        and upper-left coordinates, plus per-band nodata value, nodata pixel
        count/percentage, and the valid-data min/max range.

        Examples:
            deminfo -a                  # Check all *.tif in current directory
            deminfo dem.tif             # Check a single file
    """,
    'defnodata': """
        Define the nodata value for TIF raster files without modifying pixel data.

        This tool updates only the nodata *metadata* of one or more GeoTIFF files
        without touching the actual pixel values. A backup is saved in RAS_BAK/.

        Examples:
            defnodata -a                  # Process all *.tif (nodata=-999)
            defnodata -a -v -9999         # Process all *.tif, define nodata as -9999
            defnodata dem.tif             # Process a single file (nodata=-999)
            defnodata dem.tif -v -9999    # Process a single file, define nodata as -9999
    """,
    'mat2tif': """
        Convert a plain-numeric matrix (grid) file to a GeoTIFF file.

        The matrix must contain only numeric values arranged in rows
        (top→bottom) and columns (left→right), with no header row. Values may
        be comma delimited (.csv) or whitespace/tab delimited (.txt). Georeferencing parameters
        (origin coordinates, cell size, EPSG) can be provided via options. The
        origin can be given as the lower-left corner (--xll/--yll) or directly
        as the upper-left corner (--xul/--yul, which take precedence).

        Examples:
            mat2tif grid.csv
            mat2tif grid.txt -o dem.tif
            mat2tif grid.csv --xll 250000 --yll 2500000 --cellsize 5 --epsg 32648
            mat2tif grid.csv --xul 250000 --yul 2500100 --cellsize 5 --epsg 32648
            mat2tif grid.csv -n -9999
    """,
    'tif2mat': """
        Convert a GeoTIFF raster band to a plain-numeric matrix (grid) file.

        Reverse of mat2tif. Reads a single band from a GeoTIFF (read-only, no
        modification) and writes it as a plain-numeric matrix grid, rows
        top→bottom and columns left→right, with no header row and no
        georeferencing.

        Examples:
            tif2mat dem.tif                 # -> dem.csv
            tif2mat dem.tif -o grid.csv
            tif2mat dem.tif -o grid.txt     # tab delimited
            tif2mat dem.tif -b 2
            tif2mat dem.tif --fmt %.3f
    """,
    'tif2xyz': """
        Convert a GeoTIFF raster band to an XYZ point file.

        Reads a single band from a GeoTIFF (read-only, no modification) and
        writes one "X Y Z" line per pixel, where X/Y are the map coordinates
        of the pixel center and Z is the pixel value. Points are ordered row
        by row (top→bottom, left→right), with no header row. Nodata pixels
        are skipped unless --keep-nodata is given.

        Examples:
            tif2xyz dem.tif
            tif2xyz dem.tif -o points.xyz
            tif2xyz dem.tif -b 2
            tif2xyz dem.tif -d ,
            tif2xyz dem.tif --keep-nodata
            tif2xyz dem.tif --fmt %.3f
    """,
    'xyz2mat': """
        Convert an XYZ point file to a matrix (grid) file.

        Reads "X Y Z" points (comma or whitespace delimited) and places each
        Z on the grid formed by the unique X (columns, west→east) and Y
        (rows, north→south by default) values. Writes both a comma-delimited
        <stem>.csv and a tab-delimited <stem>.txt with no header row, ready
        for mat2tif. Cells without a point are filled with the nodata value.

        Examples:
            xyz2mat depths.xyz                 # -> depths_mat.csv, depths_mat.txt
            xyz2mat depths.csv -o grid         # -> grid.csv, grid.txt
            xyz2mat depths.xyz --south-up      # first row = smallest Y
            xyz2mat depths.xyz -n -9999        # fill empty cells with -9999
            xyz2mat depths.xyz --fmt %.3f
    """,
    'xyz2tif': """
        Convert an XYZ point file on a regular grid to a GeoTIFF file.

        Reverse of tif2xyz. Reads "X Y Z" points (comma or whitespace
        delimited) where X/Y are pixel-center coordinates, derives the cell
        size and origin from the point spacing, and writes a single-band
        Float32 GeoTIFF. Grid cells without a point are set to nodata.
        Points that are not on a regular grid are rejected.

        Examples:
            xyz2tif points.xyz                 # -> points.tif
            xyz2tif points.xyz -o dem.tif -e 3826
            xyz2tif points.xyz -n -9999        # nodata for empty cells
            xyz2tif points.xyz --cellsize 5    # set cell size explicitly
    """,
    'flipbath': """
        Flip the sign of bathymetry in TIF raster files (depth <-> elevation).

        This tool writes a copy of each input GeoTIFF with every valid pixel
        multiplied by -1 (depth positive down <-> elevation positive up).
        Nodata pixels stay nodata, and georeferencing, projection and
        metadata are copied. The input file is not modified; output goes to
        <name>_flip.tif unless -o is given (single input only).

        Examples:
            flipbath dem.tif                # -> dem_flip.tif
            flipbath dem.tif -o elev.tif    # -> elev.tif
            flipbath "*.tif"                # Wildcards (skips *_flip.tif)
            flipbath -a                     # Process all *.tif
            flipbath dem.tif -n -999        # Treat -999 as nodata
    """,
    'mvdem': """
        Relocate TIF raster files by setting a new upper-left coordinate.

        This tool updates only the geotransform origin of one or more GeoTIFF
        files, leaving pixel size/rotation and pixel data unchanged. A backup
        is saved in RAS_BAK/.

        Examples:
            mvdem dem.tif -x 500000 -y 2500000      # Process a single file
            mvdem -a -x 500000 -y 2500000           # Process all *.tif
    """,
    'demmask': """
        Extract the valid-data boundary of TIF raster files and save as shapefiles.

        This tool reads one or more GeoTIFF files (read-only, no modification),
        derives the valid-data mask (from nodata unless the file carries an
        explicit mask), merges the valid-data regions into a single boundary
        polygon, and saves it as an ESRI Shapefile in the output directory
        (default: SHP_MSK/).

        Examples:
            demmask -a                  # Process all *.tif in current directory
            demmask dem.tif             # Process a single file
            demmask -a -o SHP_MSK       # Process all *.tif, write shapefiles to SHP_MSK/
    """,
    'demext': """
        Extract the bounding-box extent of DEM raster files as rectangle shapefiles.

        This tool reads one or more GeoTIFF files (read-only, no modification),
        computes the full raster bounding box from its geotransform and
        dimensions, and saves it as a rectangle polygon ESRI Shapefile in the
        output directory (default: SHP_EXT/).

        Examples:
            demext -a                  # Process all *.tif in current directory
            demext dem.tif             # Process a single file
            demext -a -o SHP_EXT       # Process all *.tif, write shapefiles to SHP_EXT/
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
