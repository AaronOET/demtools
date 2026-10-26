#!/usr/bin/env python3
"""
xyz2mat - Convert an XYZ point file to a matrix (grid) file

Each input line holds a point "X Y Z", comma or whitespace delimited. The
unique X values become the matrix columns (west -> east) and the unique Y
values become the rows, north up by default (first row = largest Y).
Both a comma-delimited .csv and a tab-delimited .txt matrix are written.

Usage:
    xyz2mat input.xyz
    xyz2mat input.csv -o output
    xyz2mat input.xyz --south-up
    xyz2mat input.xyz -n -9999
    xyz2mat input.xyz --fmt %.3f
"""

import argparse
import os
import sys

import numpy as np


def read_xyz(input_xyz):
    """Read a 3-column XYZ file, auto-detecting comma or whitespace delimiter."""
    with open(input_xyz) as f:
        sample = f.read(4096)
    delimiter = "," if "," in sample else None
    data = np.loadtxt(input_xyz, delimiter=delimiter, ndmin=2)
    if data.shape[1] < 3:
        raise ValueError(f"expected at least 3 columns, found {data.shape[1]}")
    return data[:, 0], data[:, 1], data[:, 2]


def xyz_to_matrix(x, y, z, nodata=-999, south_up=False):
    """
    Place Z values on the grid defined by the unique X and Y coordinates.

    Returns (xs, ys, mat) where xs/ys are the sorted unique coordinates and
    mat has one row per Y and one column per X. Rows run north to south
    (largest Y first) unless south_up is True. Cells with no point are
    filled with nodata; for duplicate (X, Y) points the last value is kept.
    """
    xs, ix = np.unique(x, return_inverse=True)
    ys, iy = np.unique(y, return_inverse=True)
    mat = np.full((ys.size, xs.size), nodata, dtype=float)
    mat[iy, ix] = z

    n_filled = np.unique(iy * xs.size + ix).size
    if z.size != n_filled:
        print(f"Warning    : {z.size - n_filled} duplicate (x, y) points, last value kept")
    if mat.size != n_filled:
        print(f"Warning    : {mat.size - n_filled} grid cells have no point (filled with {nodata})")

    if not south_up:
        mat = np.flipud(mat)
    return xs, ys, mat


def xyz_to_mat(input_xyz, output_stem, south_up=False, nodata=-999, fmt="%g"):
    """
    Convert an XYZ point file to a matrix (grid) file.

    Writes <output_stem>.csv (comma delimited) and <output_stem>.txt (tab
    delimited), no header row. Columns follow X ascending (west -> east);
    rows follow Y descending (north -> south, the row order mat2tif
    expects) unless south_up is True.

    Args:
        input_xyz   (str):   Path to input XYZ file (comma or whitespace delimited).
        output_stem (str):   Output path without extension.
        south_up    (bool):  Put the smallest Y in the first row (default False).
        nodata      (float): Value for grid cells with no point (default -999).
        fmt         (str):   Numeric format string passed to np.savetxt (default "%g").
    """
    output_csv = output_stem + ".csv"
    output_txt = output_stem + ".txt"
    print(f"Input XYZ  : {input_xyz}")
    print(f"Output MAT : {output_csv}")
    print(f"             {output_txt}")

    try:
        x, y, z = read_xyz(input_xyz)
    except Exception as exc:
        print(f"Error reading XYZ: {exc}")
        sys.exit(1)

    xs, ys, mat = xyz_to_matrix(x, y, z, nodata=nodata, south_up=south_up)

    np.savetxt(output_csv, mat, delimiter=",", fmt=fmt)
    np.savetxt(output_txt, mat, delimiter="\t", fmt=fmt)

    valid = mat[(mat != nodata) & ~np.isnan(mat)]
    print(f"Points     : {z.size}")
    print(f"Grid size  : {xs.size} cols (x) x {ys.size} rows (y), "
          f"{'south' if south_up else 'north'} up")
    print(f"X range    : {xs.min():g} - {xs.max():g}")
    print(f"Y range    : {ys.min():g} - {ys.max():g}")
    if valid.size:
        print(f"Z range    : {valid.min():g} - {valid.max():g}")
    print(f"Done -> {output_csv}, {output_txt}")


def main():
    parser = argparse.ArgumentParser(
        prog='xyz2mat',
        description="Convert an XYZ point file to a matrix (grid) file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  xyz2mat depths.txt                 -> depths_mat.csv, depths_mat.txt
  xyz2mat depths.csv -o out/depths   -> out/depths.csv, out/depths.txt
  xyz2mat depths.txt --south-up      -> first row = smallest y
  xyz2mat depths.txt -n -9999        -> fill empty cells with -9999
  xyz2mat depths.txt --fmt %%.3f      -> 3 decimals
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
        help="Output path stem; .csv and .txt are appended "
             "(default: <input name>_mat)"
    )
    parser.add_argument(
        "--south-up", action="store_true",
        help="Put the smallest Y in the first row (default: north up)"
    )
    parser.add_argument(
        "-n", "--nodata", type=float, default=-999,
        help="Value for grid cells with no point (default: -999)"
    )
    parser.add_argument(
        "--fmt", default="%g",
        help="Numeric format string (default: %%g)"
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

    if args.output is None:
        output_stem = os.path.splitext(args.input)[0] + "_mat"
    else:
        output_stem = args.output
        if os.path.splitext(output_stem)[1].lower() in (".csv", ".txt"):
            output_stem = os.path.splitext(output_stem)[0]

    xyz_to_mat(
        input_xyz=args.input,
        output_stem=output_stem,
        south_up=args.south_up,
        nodata=args.nodata,
        fmt=args.fmt,
    )


if __name__ == "__main__":
    main()
