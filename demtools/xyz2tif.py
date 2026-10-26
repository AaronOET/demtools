#!/usr/bin/env python3
"""
xyz2tif - Convert an XYZ point file on a regular grid to a GeoTIFF file
Uses GDAL/OGR Python bindings

Each input line holds a point "X Y Z", comma or whitespace delimited, where
X/Y are pixel-center map coordinates (the format tif2xyz writes). The cell
size and raster origin are derived from the point spacing, so no
georeferencing options are needed. Grid cells without a point become nodata.

Usage:
    xyz2tif input.xyz
    xyz2tif input.xyz -o output.tif
    xyz2tif input.xyz -e 3826
    xyz2tif input.xyz -n -9999
    xyz2tif input.xyz --cellsize 5
"""

import argparse
import os
import sys

import numpy as np
from osgeo import gdal, osr

from .xyz2mat import read_xyz

gdal.UseExceptions()

# Max allowed offset of a point from its grid node, as a fraction of the
# cell size, before the input is rejected as not being on a regular grid.
GRID_TOLERANCE = 0.01


def grid_spacing(coords):
    """Smallest spacing between the unique coordinate values (None if only one)."""
    u = np.unique(coords)
    if u.size < 2:
        return None
    return float(np.diff(u).min())


def grid_index(coords, origin, cellsize, axis):
    """Map coordinates to integer grid indices, checking they sit on grid nodes."""
    pos = (coords - origin) / cellsize
    idx = np.rint(pos).astype(np.int64)
    off = np.abs(pos - idx).max()
    if off > GRID_TOLERANCE:
        raise ValueError(
            f"{axis} coordinates are not on a regular grid with cell size "
            f"{cellsize:g} (max offset {off:.3g} cells)"
        )
    return idx


def xyz_to_tif(input_xyz, output_tif, cellsize=None, nodata=-999, epsg=None):
    """
    Convert an XYZ point file on a regular grid to a GeoTIFF.

    X/Y are taken as pixel centers. The cell size is the smallest spacing
    between distinct X (and Y) values unless given; missing rows or columns
    in the input are allowed and are filled with nodata. Rows are written
    north (largest Y) to south.

    Args:
        input_xyz  (str):   Path to input XYZ file (comma or whitespace delimited).
        output_tif (str):   Path to output GeoTIFF file.
        cellsize   (float): Cell size in map units for both axes (default None =
                            derived from the point spacing).
        nodata     (float): NoData value for cells with no point (default -999).
        epsg       (int):   EPSG code for the spatial reference (default None).
    """
    print(f"Input XYZ  : {input_xyz}")
    print(f"Output TIF : {output_tif}")

    try:
        x, y, z = read_xyz(input_xyz)
    except Exception as exc:
        print(f"Error reading XYZ: {exc}")
        sys.exit(1)

    # --- Derive grid ----------------------------------------------------
    dx = cellsize if cellsize is not None else grid_spacing(x)
    dy = cellsize if cellsize is not None else grid_spacing(y)
    if dx is None and dy is None:
        print("Error: cannot derive cell size from a single point, use --cellsize")
        sys.exit(1)
    dx = dx if dx is not None else dy
    dy = dy if dy is not None else dx

    x_min, y_max = x.min(), y.max()
    try:
        col = grid_index(x, x_min, dx, "X")
        row = grid_index(y_max - y, 0.0, dy, "Y")
    except ValueError as exc:
        print(f"Error: {exc}")
        sys.exit(1)

    cols = int(col.max()) + 1
    rows = int(row.max()) + 1
    print(f"Points     : {z.size}")
    print(f"Grid size  : {cols} cols x {rows} rows")
    print(f"Cell size  : {dx:g} x {dy:g}")

    data = np.full((rows, cols), nodata, dtype=np.float32)
    data[row, col] = z

    n_filled = np.unique(row * cols + col).size
    if z.size != n_filled:
        print(f"Warning    : {z.size - n_filled} duplicate (x, y) points, last value kept")
    if data.size != n_filled:
        print(f"Warning    : {data.size - n_filled} grid cells have no point (set to nodata)")

    # --- Build GeoTransform ---------------------------------------------
    # Points are pixel centers, so the upper-left corner is half a cell out.
    geotransform = (x_min - dx / 2, dx, 0.0, y_max + dy / 2, 0.0, -dy)
    print(f"Upper-left : {geotransform[0]}, {geotransform[3]}")

    # --- Create output GeoTIFF -----------------------------------------
    driver = gdal.GetDriverByName("GTiff")
    out_ds = driver.Create(output_tif, cols, rows, 1, gdal.GDT_Float32)
    if out_ds is None:
        print(f"Error: Could not create {output_tif}")
        sys.exit(1)

    out_ds.SetGeoTransform(geotransform)

    if epsg is not None:
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(epsg)
        out_ds.SetProjection(srs.ExportToWkt())
        print(f"Projection : EPSG:{epsg}")
    else:
        print("Projection : none (no EPSG provided)")

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
        prog='xyz2tif',
        description="Convert an XYZ point file on a regular grid to a GeoTIFF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  xyz2tif input.xyz
  xyz2tif input.xyz -o output.tif
  xyz2tif input.csv -e 3826
  xyz2tif input.xyz -n -9999
  xyz2tif input.xyz --cellsize 5
        """
    )
    parser.add_argument(
        "input", nargs="?", metavar="FILE",
        help="Input XYZ file path (comma or whitespace delimited)"
    )
    # Deprecated: -i FILE is still accepted for backward compatibility
    parser.add_argument(
        "-i", "--input", dest="input_opt", metavar="FILE",
        help=argparse.SUPPRESS
    )
    parser.add_argument(
        "-o", "--output", default=None,
        help="Output TIF file path (default: same name as input with .tif extension)"
    )
    parser.add_argument(
        "--cellsize", type=float, default=None,
        help="Cell size in map units (default: derived from the point spacing)"
    )
    parser.add_argument(
        "-n", "--nodata", type=float, default=-999,
        help="NoData value for cells with no point (default: -999)"
    )
    parser.add_argument(
        "-e", "--epsg", type=int, default=None,
        help="EPSG code for spatial reference (optional)"
    )

    args = parser.parse_args()
    if args.input_opt:
        if args.input:
            parser.error("give the input file either positionally or with -i, not both")
        args.input = args.input_opt
    if not args.input:
        parser.error("the input file is required")
    if args.cellsize is not None and args.cellsize <= 0:
        parser.error("--cellsize must be positive")

    if not os.path.isfile(args.input):
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)

    output_tif = args.output
    if output_tif is None:
        base = os.path.splitext(args.input)[0]
        output_tif = base + ".tif"

    xyz_to_tif(
        input_xyz=args.input,
        output_tif=output_tif,
        cellsize=args.cellsize,
        nodata=args.nodata,
        epsg=args.epsg,
    )


if __name__ == "__main__":
    main()
