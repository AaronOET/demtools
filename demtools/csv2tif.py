#!/usr/bin/env python3
"""
csv2tif - Convert a CSV raster grid to a GeoTIFF file
Uses GDAL/OGR Python bindings

Usage:
    csv2tif -i input.csv
    csv2tif -i input.csv -o output.tif
    csv2tif -i input.csv -o output.tif --xll 0.0 --yll 0.0 --cellsize 1.0
    csv2tif -i input.csv --epsg 32648
"""

import argparse
import os
import sys

import numpy as np
from osgeo import gdal, osr

gdal.UseExceptions()

def csv_to_tif(input_csv, output_tif, xll=0.0, yll=0.0, cellsize=1.0,
               nodata=-999, epsg=None):
    """
    Convert a CSV raster grid to a GeoTIFF.

    The CSV is expected to be a plain numeric grid (no headers) where rows
    correspond to raster rows from top (north) to bottom (south).

    Args:
        input_csv  (str):   Path to input CSV file.
        output_tif (str):   Path to output GeoTIFF file.
        xll        (float): X coordinate of the lower-left corner (default 0.0).
        yll        (float): Y coordinate of the lower-left corner (default 0.0).
        cellsize   (float): Cell/pixel size in map units (default 1.0).
        nodata     (float): NoData value to assign (default -999).
        epsg       (int):   EPSG code for the spatial reference (optional).
    """
    print(f"Input CSV  : {input_csv}")
    print(f"Output TIF : {output_tif}")

    # --- Read CSV -------------------------------------------------------
    try:
        data = np.genfromtxt(input_csv, delimiter=",", dtype=np.float32)
    except Exception as exc:
        print(f"Error reading CSV: {exc}")
        sys.exit(1)

    if data.ndim == 1:
        # Single-row CSV — treat as one-row raster
        data = data.reshape(1, -1)

    rows, cols = data.shape
    print(f"Grid size  : {cols} cols x {rows} rows")

    # --- Build GeoTransform ---------------------------------------------
    # GDAL geotransform: (x_top_left, pixel_width, 0, y_top_left, 0, -pixel_height)
    x_top_left = xll
    y_top_left = yll + rows * cellsize
    geotransform = (x_top_left, cellsize, 0.0, y_top_left, 0.0, -cellsize)

    # --- Create output GeoTIFF -----------------------------------------
    driver = gdal.GetDriverByName("GTiff")
    out_ds = driver.Create(output_tif, cols, rows, 1, gdal.GDT_Float32)
    if out_ds is None:
        print(f"Error: Could not create {output_tif}")
        sys.exit(1)

    out_ds.SetGeoTransform(geotransform)

    # Spatial reference
    srs = osr.SpatialReference()
    if epsg is not None:
        srs.ImportFromEPSG(epsg)
        out_ds.SetProjection(srs.ExportToWkt())
        print(f"Projection : EPSG:{epsg}")
    else:
        print("Projection : none (no EPSG provided)")

    # Write band
    out_band = out_ds.GetRasterBand(1)
    out_band.SetNoDataValue(nodata)
    out_band.WriteArray(data)
    out_band.FlushCache()

    out_ds.FlushCache()
    out_ds = None

    print(f"NoData     : {nodata}")
    print(f"Done -> {output_tif}")


def main():
    parser = argparse.ArgumentParser(
        prog='csv2tif',
        description="Convert a CSV raster grid to a GeoTIFF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  csv2tif -i input.csv
  csv2tif -i input.csv -o output.tif
  csv2tif -i input.csv -o output.tif --xll 250000 --yll 2500000 --cellsize 5
  csv2tif -i input.csv --epsg 32648
        """
    )
    parser.add_argument(
        "-i", "--input", required=True,
        help="Input CSV file path"
    )
    parser.add_argument(
        "-o", "--output", default=None,
        help="Output TIF file path (default: same name as input with .tif extension)"
    )
    parser.add_argument(
        "--xll", type=float, default=0.0,
        help="X coordinate of lower-left corner (default: 0.0)"
    )
    parser.add_argument(
        "--yll", type=float, default=0.0,
        help="Y coordinate of lower-left corner (default: 0.0)"
    )
    parser.add_argument(
        "--cellsize", type=float, default=1.0,
        help="Cell size in map units (default: 1.0)"
    )
    parser.add_argument(
        "-n", "--nodata", type=float, default=-999,
        help="NoData value to assign (default: -999)"
    )
    parser.add_argument(
        "--epsg", type=int, default=None,
        help="EPSG code for spatial reference (optional)"
    )

    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)

    output_tif = args.output
    if output_tif is None:
        base = os.path.splitext(args.input)[0]
        output_tif = base + ".tif"

    csv_to_tif(
        input_csv=args.input,
        output_tif=output_tif,
        xll=args.xll,
        yll=args.yll,
        cellsize=args.cellsize,
        nodata=args.nodata,
        epsg=args.epsg,
    )


if __name__ == "__main__":
    main()
