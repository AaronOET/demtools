#!/usr/bin/env python3
"""
flipbath - Flip the sign of bathymetry in TIF raster or XYZ point files
(depth <-> elevation)
Uses GDAL/OGR Python bindings

Depth (positive down) becomes elevation (positive up) and vice versa:
    z_out = -z_in
Nodata pixels are kept as nodata (e.g. -999 stays -999, it does not become 999).
Georeferencing, projection and metadata are copied from the input.

For *.xyz files only the Z (third) column is flipped; X/Y, delimiters and
any header/comment lines are copied unchanged.

Usage:
    flipbath dem.tif
    flipbath dem.tif -o elev.tif
    flipbath dem1.tif dem2.tif
    flipbath points.xyz
    flipbath "*.tif"
    flipbath -a
    flipbath dem.tif -n -999
"""

import argparse
import glob
import os
import re
import sys

import numpy as np
from osgeo import gdal, gdalconst

gdal.UseExceptions()

FLIP_SUFFIX = "_flip"
XYZ_EXTS = (".xyz",)

# X, Y and Z fields separated by commas and/or whitespace; group 2 is Z.
XYZ_LINE = re.compile(r"^(\s*[^\s,]+(?:\s*,\s*|\s+)[^\s,]+(?:\s*,\s*|\s+))([^\s,]+)(.*)$",
                      re.DOTALL)


def flip_bathymetry(input_tif, output_tif, nodata=None):
    """
    Write a copy of a raster with all valid pixel values multiplied by -1.

    Every band is flipped. Nodata pixels (and NaN, for floating-point
    rasters) are left unchanged. The input file is never modified.

    Args:
        input_tif  (str):   Path to input TIF file.
        output_tif (str):   Path to output TIF file.
        nodata     (float): Nodata value to use when the file does not define
                            one, or to override it (default None = use the
                            file's own nodata value).

    Returns:
        bool: True on success, False on error.
    """
    print(f"Processing: {input_tif}")

    src_ds = gdal.Open(input_tif, gdalconst.GA_ReadOnly)
    if src_ds is None:
        print(f"Error: Could not open {input_tif}")
        return False

    data_type = src_ds.GetRasterBand(1).DataType
    if data_type in (gdal.GDT_Byte, gdal.GDT_UInt16, gdal.GDT_UInt32):
        print(f"  Error: unsigned data type {gdal.GetDataTypeName(data_type)} "
              "cannot hold negated values, skipping...")
        src_ds = None
        return False

    out_ds = gdal.GetDriverByName("GTiff").CreateCopy(output_tif, src_ds)
    src_ds = None
    if out_ds is None:
        print(f"Error: Could not create {output_tif}")
        return False

    out_mins, out_maxs = [], []
    for b in range(1, out_ds.RasterCount + 1):
        band = out_ds.GetRasterBand(b)
        if nodata is not None:
            band.SetNoDataValue(nodata)
        band_nodata = band.GetNoDataValue()

        data = band.ReadAsArray()
        valid = np.ones(data.shape, dtype=bool)
        if band_nodata is not None and not np.isnan(band_nodata):
            valid &= data != band_nodata
        if np.issubdtype(data.dtype, np.floating):
            valid &= ~np.isnan(data)

        # "+ 0" turns -0.0 into 0.0
        data[valid] = -data[valid] + 0
        band.WriteArray(data)
        band.FlushCache()

        if valid.any():
            out_mins.append(data[valid].min())
            out_maxs.append(data[valid].max())

    print(f"  Nodata value: {band_nodata}")
    out_ds.FlushCache()
    out_ds = None

    if out_mins:
        out_min, out_max = min(out_mins), max(out_maxs)
        print(f"  Range: [{-out_max + 0:g}, {-out_min + 0:g}] -> [{out_min:g}, {out_max:g}]")
    else:
        print("  No valid data")
    print(f"  Done -> {output_tif}")
    return True


def negate_token(token):
    """Negate a numeric string textually so its digits are kept exactly."""
    if float(token) == 0:
        return token
    if token[0] == "-":
        return token[1:]
    if token[0] == "+":
        return "-" + token[1:]
    return "-" + token


def flip_xyz(input_xyz, output_xyz, nodata=None):
    """
    Write a copy of an XYZ point file with the Z (third) column multiplied by -1.

    Z is negated textually, so X/Y, delimiters (comma and/or whitespace),
    extra columns and the precision of Z are preserved. Lines that do not
    hold a numeric Z (headers, comments, blank lines) are copied unchanged,
    as are NaN values and Z equal to ``nodata``. The input file is never
    modified.

    Args:
        input_xyz  (str):   Path to input XYZ file.
        output_xyz (str):   Path to output XYZ file.
        nodata     (float): Z value to leave unchanged (default None = none).

    Returns:
        bool: True on success, False on error.
    """
    print(f"Processing: {input_xyz}")

    out_min = out_max = None
    flipped = kept = 0
    try:
        with open(input_xyz, "r", newline="") as fin,                 open(output_xyz, "w", newline="") as fout:
            for line in fin:
                m = XYZ_LINE.match(line)
                if m:
                    try:
                        z = float(m.group(2))
                    except ValueError:
                        m = None
                if not m:
                    fout.write(line)
                    continue
                if np.isnan(z) or (nodata is not None and z == nodata):
                    fout.write(line)
                    kept += 1
                    continue
                fout.write(m.group(1) + negate_token(m.group(2)) + m.group(3))
                z = -z + 0
                out_min = z if out_min is None else min(out_min, z)
                out_max = z if out_max is None else max(out_max, z)
                flipped += 1
    except OSError as e:
        print(f"Error: {e}")
        return False

    print(f"  Points flipped: {flipped}" + (f" (nodata/NaN kept: {kept})" if kept else ""))
    if out_min is not None:
        print(f"  Range: [{-out_max + 0:g}, {-out_min + 0:g}] -> [{out_min:g}, {out_max:g}]")
    else:
        print("  No valid data")
    print(f"  Done -> {output_xyz}")
    return True


def flip_file(input_file, output_file, nodata=None):
    """Flip a TIF raster or, for *.xyz, an XYZ point file."""
    if os.path.splitext(input_file)[1].lower() in XYZ_EXTS:
        return flip_xyz(input_file, output_file, nodata=nodata)
    return flip_bathymetry(input_file, output_file, nodata=nodata)


def flipped_name(input_tif):
    """Default output path: <stem>_flip<ext> next to the input."""
    base, ext = os.path.splitext(input_tif)
    return base + FLIP_SUFFIX + ext


def main():
    parser = argparse.ArgumentParser(
        prog='flipbath',
        description='Flip the sign of bathymetry in TIF raster or XYZ point files (depth <-> elevation)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  flipbath dem.tif                   # -> dem_flip.tif
  flipbath dem.tif -o elev.tif       # -> elev.tif
  flipbath points.xyz                # -> points_flip.xyz (Z column only)
  flipbath dem1.tif dem2.tif         # -> dem1_flip.tif, dem2_flip.tif
  flipbath "*.tif"                   # Wildcards are expanded (skips *_flip.*)
  flipbath -a                        # Process all *.tif and *.xyz in current directory
  flipbath dem.tif -n -999           # Treat -999 as nodata
        """
    )
    parser.add_argument(
        'input',
        nargs='*',
        metavar='FILE',
        help='TIF or XYZ file(s) to process, wildcards allowed'
    )
    parser.add_argument(
        '-a', '--all',
        action='store_true',
        help='Process all *.tif and *.xyz files in the current directory'
    )
    # Deprecated: -i FILE is still accepted for backward compatibility
    parser.add_argument(
        '-i', '--input',
        dest='input_opt',
        metavar='FILE',
        help=argparse.SUPPRESS
    )
    parser.add_argument(
        '-o', '--output', default=None,
        help='Output file path, single input only '
             '(default: same name as input with _flip suffix)'
    )
    parser.add_argument(
        '-n', '--nodata', type=float, default=None,
        help="Nodata value to use if the file does not define one (or to override it); "
             "for XYZ files, Z values equal to it are left unchanged"
    )

    args = parser.parse_args()
    if args.input_opt:
        if args.input:
            parser.error("give the input file either positionally or with -i, not both")
        args.input = [args.input_opt]
    if args.all == bool(args.input):
        parser.error("one of FILE or -a/--all is required (but not both)")

    # Expand wildcards ourselves since the Windows shell does not;
    # skip earlier *_flip.* outputs picked up by a wildcard.
    patterns = ["*.tif", "*.xyz"] if args.all else args.input
    tif_files = []
    for pattern in patterns:
        if glob.has_magic(pattern):
            tif_files.extend(
                f for f in sorted(glob.glob(pattern))
                if not os.path.splitext(f)[0].endswith(FLIP_SUFFIX)
            )
        else:
            tif_files.append(pattern)

    if not tif_files:
        print("No TIF or XYZ files found.")
        sys.exit(0)
    if args.output and len(tif_files) != 1:
        parser.error("-o/--output can only be used with a single input file")

    missing = [f for f in tif_files if not os.path.isfile(f)]
    if missing:
        for f in missing:
            print(f"Error: Input file not found: {f}")
        sys.exit(1)

    success_count = 0
    for tif_file in tif_files:
        output_tif = args.output or flipped_name(tif_file)
        if flip_file(tif_file, output_tif, nodata=args.nodata):
            success_count += 1
        print()

    print(f"Done! {success_count}/{len(tif_files)} file(s) flipped.")
    if success_count != len(tif_files):
        sys.exit(1)


if __name__ == "__main__":
    main()
