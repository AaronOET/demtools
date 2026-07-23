#!/usr/bin/env python3
"""
tif2csv - Convert a GeoTIFF raster band to a plain-numeric CSV grid
Uses GDAL/OGR Python bindings

Usage:
    tif2csv -i input.tif
    tif2csv -i input.tif -o output.csv
    tif2csv -i input.tif -b 2
    tif2csv -i input.tif --fmt %.3f
"""

import argparse
import os
import sys

import numpy as np
from osgeo import gdal, gdalconst

gdal.UseExceptions()

def tif_to_csv(input_tif, output_csv, band=1, fmt="%.6g"):
    """
    Convert a GeoTIFF raster band to a plain-numeric CSV grid.

    The CSV is written with rows top (north) to bottom (south), matching
    the row order csv2tif expects — no header row, no georeferencing.

    Args:
        input_tif  (str):   Path to input GeoTIFF file.
        output_csv (str):   Path to output CSV file.
        band       (int):   Raster band to export, 1-indexed (default 1).
        fmt        (str):   Numeric format string passed to np.savetxt (default "%.6g").
    """
    print(f"Input TIF  : {input_tif}")
    print(f"Output CSV : {output_csv}")

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

    np.savetxt(output_csv, data, delimiter=",", fmt=fmt)

    print(f"Done -> {output_csv}")


def main():
    parser = argparse.ArgumentParser(
        prog='tif2csv',
        description="Convert a GeoTIFF raster band to a plain-numeric CSV grid",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  tif2csv -i input.tif
  tif2csv -i input.tif -o output.csv
  tif2csv -i input.tif -b 2
  tif2csv -i input.tif --fmt %.3f
        """
    )
    parser.add_argument(
        "-i", "--input", required=True,
        help="Input GeoTIFF file path"
    )
    parser.add_argument(
        "-o", "--output", default=None,
        help="Output CSV file path (default: same name as input with .csv extension)"
    )
    parser.add_argument(
        "-b", "--band", type=int, default=1,
        help="Raster band to export, 1-indexed (default: 1)"
    )
    parser.add_argument(
        "--fmt", default="%.6g",
        help="Numeric format string for CSV values (default: %%.6g)"
    )

    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)

    output_csv = args.output
    if output_csv is None:
        base = os.path.splitext(args.input)[0]
        output_csv = base + ".csv"

    tif_to_csv(
        input_tif=args.input,
        output_csv=output_csv,
        band=args.band,
        fmt=args.fmt,
    )


if __name__ == "__main__":
    main()
