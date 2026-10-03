#!/usr/bin/env python3
"""
tif2xyz - Convert a GeoTIFF raster band to an XYZ point file
Uses GDAL/OGR Python bindings

Each output line holds the map coordinates of a pixel center and its value:
    X Y Z

Usage:
    tif2xyz -i input.tif
    tif2xyz -i input.tif -o output.xyz
    tif2xyz -i input.tif -b 2
    tif2xyz -i input.tif -d ,
    tif2xyz -i input.tif --keep-nodata
    tif2xyz -i input.tif --fmt %.3f
"""

import argparse
import os
import sys

import numpy as np
from osgeo import gdal, gdalconst

gdal.UseExceptions()

# Number of raster rows read and written per block, to bound memory use on
# large DEMs.
BLOCK_ROWS = 256


def tif_to_xyz(input_tif, output_xyz, band=1, delimiter=" ", fmt="%.6g",
               keep_nodata=False):
    """
    Convert a GeoTIFF raster band to an XYZ point file.

    Each line is "X Y Z" where X/Y are the map coordinates of the pixel
    center (computed from the geotransform, rotation terms included) and Z
    is the pixel value. Points are written row by row, top (north) to
    bottom (south), left to right — no header row.

    Args:
        input_tif   (str):  Path to input GeoTIFF file.
        output_xyz  (str):  Path to output XYZ file.
        band        (int):  Raster band to export, 1-indexed (default 1).
        delimiter   (str):  Column separator (default single space).
        fmt         (str):  Numeric format string for the Z value (default "%.6g").
                            X/Y are written with "%.6f".
        keep_nodata (bool): Also write nodata pixels (default False, they are skipped).
    """
    print(f"Input TIF  : {input_tif}")
    print(f"Output XYZ : {output_xyz}")

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
    gt = ds.GetGeoTransform()
    print(f"Grid size  : {cols} cols x {rows} rows")
    if band_count > 1:
        print(f"Band       : {band} of {band_count}")

    rb = ds.GetRasterBand(band)
    nodata = rb.GetNoDataValue()
    if nodata is not None:
        print(f"NoData     : {nodata}" + (" (kept)" if keep_nodata else " (skipped)"))

    line_fmt = delimiter.join(["%.6f", "%.6f", fmt])
    col_centers = np.arange(cols, dtype=np.float64) + 0.5
    written = 0

    with open(output_xyz, "w", newline="\n") as f:
        for row_off in range(0, rows, BLOCK_ROWS):
            n_rows = min(BLOCK_ROWS, rows - row_off)
            data = rb.ReadAsArray(0, row_off, cols, n_rows)
            if data is None:
                print("Error: Could not read pixel data")
                sys.exit(1)

            row_centers = np.arange(row_off, row_off + n_rows, dtype=np.float64) + 0.5
            px, py = np.meshgrid(col_centers, row_centers)
            x = gt[0] + px * gt[1] + py * gt[2]
            y = gt[3] + px * gt[4] + py * gt[5]

            z = data.ravel()
            x = x.ravel()
            y = y.ravel()

            if not keep_nodata:
                valid = np.ones(z.shape, dtype=bool)
                if nodata is not None:
                    if np.isnan(nodata):
                        valid &= ~np.isnan(z)
                    else:
                        valid &= z != nodata
                if np.issubdtype(z.dtype, np.floating):
                    valid &= ~np.isnan(z)
                x, y, z = x[valid], y[valid], z[valid]

            if z.size:
                np.savetxt(f, np.column_stack((x, y, z)), fmt=line_fmt)
                written += z.size

    ds = None

    print(f"Points     : {written} of {cols * rows}")
    print(f"Done -> {output_xyz}")


def main():
    parser = argparse.ArgumentParser(
        prog='tif2xyz',
        description="Convert a GeoTIFF raster band to an XYZ point file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  tif2xyz -i input.tif
  tif2xyz -i input.tif -o output.xyz
  tif2xyz -i input.tif -b 2
  tif2xyz -i input.tif -d ,
  tif2xyz -i input.tif --keep-nodata
  tif2xyz -i input.tif --fmt %.3f
        """
    )
    parser.add_argument(
        "-i", "--input", required=True,
        help="Input GeoTIFF file path"
    )
    parser.add_argument(
        "-o", "--output", default=None,
        help="Output XYZ file path (default: same name as input with .xyz extension)"
    )
    parser.add_argument(
        "-b", "--band", type=int, default=1,
        help="Raster band to export, 1-indexed (default: 1)"
    )
    parser.add_argument(
        "-d", "--delimiter", default=" ",
        help="Column separator (default: single space; use '\\t' for tab)"
    )
    parser.add_argument(
        "--fmt", default="%.6g",
        help="Numeric format string for Z values (default: %%.6g)"
    )
    parser.add_argument(
        "--keep-nodata", action="store_true",
        help="Also write nodata pixels (default: skip them)"
    )

    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)

    output_xyz = args.output
    if output_xyz is None:
        base = os.path.splitext(args.input)[0]
        output_xyz = base + ".xyz"

    delimiter = "\t" if args.delimiter in ("\\t", "tab") else args.delimiter

    tif_to_xyz(
        input_tif=args.input,
        output_xyz=output_xyz,
        band=args.band,
        delimiter=delimiter,
        fmt=args.fmt,
        keep_nodata=args.keep_nodata,
    )


if __name__ == "__main__":
    main()
