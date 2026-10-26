#!/usr/bin/env python3
"""
tif2mat - Convert a GeoTIFF raster band to a plain-numeric matrix (grid) file
Uses GDAL/OGR Python bindings

Usage:
    tif2mat input.tif
    tif2mat input.tif -o output.csv
    tif2mat input.tif -o output.txt
    tif2mat input.tif -b 2
    tif2mat input.tif --fmt %.3f
"""

import argparse
import os
import sys

import numpy as np
from osgeo import gdal, gdalconst

gdal.UseExceptions()

def tif_to_mat(input_tif, output_mat, band=1, fmt="%.6g"):
    """
    Convert a GeoTIFF raster band to a plain-numeric matrix (grid) file.

    The matrix is written with rows top (north) to bottom (south), matching
    the row order mat2tif expects — no header row, no georeferencing.
    A .txt output is tab delimited; any other extension (e.g. .csv) is
    comma delimited.

    Args:
        input_tif  (str):   Path to input GeoTIFF file.
        output_mat (str):   Path to output matrix file (.csv or .txt).
        band       (int):   Raster band to export, 1-indexed (default 1).
        fmt        (str):   Numeric format string passed to np.savetxt (default "%.6g").
    """
    print(f"Input TIF  : {input_tif}")
    print(f"Output MAT : {output_mat}")

    ds = gdal.Open(input_tif, gdalconst.GA_ReadOnly)
    if ds is None:
        print(f"Error: Could not open {input_tif}")
        sys.exit(1)

    band_count = ds.RasterCount
    if band < 1 or band > band_count:
        print(f"Error: Band {band} out of range (file has {band_count} band(s))")
        sys.exit(1)

    cols = ds.RasterXSize
    rows = ds.RasterYSize
    print(f"Grid size  : {cols} cols x {rows} rows")
    if band_count > 1:
        print(f"Band       : {band} of {band_count}")

    data = ds.GetRasterBand(band).ReadAsArray()
    ds = None

    if data is None:
        print("Error: Could not read pixel data")
        sys.exit(1)

    delimiter = "	" if os.path.splitext(output_mat)[1].lower() == ".txt" else ","
    np.savetxt(output_mat, data, delimiter=delimiter, fmt=fmt)

    print(f"Done -> {output_mat}")


def main():
    parser = argparse.ArgumentParser(
        prog='tif2mat',
        description="Convert a GeoTIFF raster band to a plain-numeric matrix (grid) file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  tif2mat input.tif
  tif2mat input.tif -o output.csv
  tif2mat input.tif -o output.txt
  tif2mat input.tif -b 2
  tif2mat input.tif --fmt %.3f
        """
    )
    parser.add_argument(
        "input", nargs="?", metavar="FILE",
        help="Input GeoTIFF file path"
    )
    # Deprecated: -i FILE is still accepted for backward compatibility
    parser.add_argument(
        "-i", "--input", dest="input_opt", metavar="FILE",
        help=argparse.SUPPRESS
    )
    parser.add_argument(
        "-o", "--output", default=None,
        help="Output matrix file path; .txt is tab delimited, otherwise comma "
             "(default: same name as input with .csv extension)"
    )
    parser.add_argument(
        "-b", "--band", type=int, default=1,
        help="Raster band to export, 1-indexed (default: 1)"
    )
    parser.add_argument(
        "--fmt", default="%.6g",
        help="Numeric format string for matrix values (default: %%.6g)"
    )

    args = parser.parse_args()
    if args.input_opt:
        if args.input:
            parser.error("give the input file either positionally or with -i, not both")
        args.input = args.input_opt
    if not args.input:
        parser.error("the input file is required")

    if not os.path.isfile(args.input):
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)

    output_mat = args.output
    if output_mat is None:
        base = os.path.splitext(args.input)[0]
        output_mat = base + ".csv"

    tif_to_mat(
        input_tif=args.input,
        output_mat=output_mat,
        band=args.band,
        fmt=args.fmt,
    )


if __name__ == "__main__":
    main()
