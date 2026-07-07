#!/usr/bin/env python3
"""
chknodata - Check the nodata value for TIF raster files
Uses GDAL/OGR Python bindings
"""

import glob
import argparse
import os
import sys
import numpy as np
from osgeo import gdal, gdalconst

gdal.UseExceptions()

def check_nodata_value(input_file):
    """
    Report the nodata value and basic pixel statistics for a raster file.

    Args:
        input_file (str): Path to input TIF file

    Returns:
        bool: True if the file was read successfully, False otherwise
    """
    print(f"Processing: {input_file}")

    ds = gdal.Open(input_file, gdalconst.GA_ReadOnly)
    if ds is None:
        print(f"Error: Could not open {input_file}")
        return False

    band_count = ds.RasterCount
    for band_idx in range(1, band_count + 1):
        band = ds.GetRasterBand(band_idx)
        nodata = band.GetNoDataValue()

        label = f"Band {band_idx}" if band_count > 1 else "Band"
        if nodata is None:
            print(f"  {label}: no nodata value defined")
        else:
            print(f"  {label}: nodata value = {nodata}")

        data = band.ReadAsArray()
        if data is None:
            print("    Warning: could not read pixel data")
            continue

        total_pixels = data.size
        if nodata is not None:
            nodata_mask = data == nodata
            nodata_count = int(np.count_nonzero(nodata_mask))
            valid_data = data[~nodata_mask]
        else:
            nodata_count = 0
            valid_data = data

        print(f"    Total pixels: {total_pixels}")
        print(f"    Nodata pixels: {nodata_count} ({nodata_count / total_pixels:.2%})")

        if valid_data.size > 0:
            print(f"    Valid data range: {valid_data.min()} to {valid_data.max()}")
        else:
            print("    Valid data range: N/A (all pixels are nodata)")

    ds = None
    return True


def main():
    parser = argparse.ArgumentParser(
        prog='chknodata',
        description='Check the nodata value for TIF raster files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  chknodata -a                       # Check all *.tif in current directory
  chknodata -i dem.tif               # Check a single file
        """
    )

    # Mutually exclusive group: -a or -i
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '-a', '--all',
        action='store_true',
        help='Check all *.tif files in the current directory'
    )
    group.add_argument(
        '-i', '--input',
        metavar='FILE',
        help='Check a single TIF file'
    )

    args = parser.parse_args()

    print("chknodata: checking nodata values")
    print("=" * 60)

    if args.all:
        tif_files = glob.glob("*.tif")
        if not tif_files:
            print("No TIF files found in current directory.")
            sys.exit(0)

        print(f"Found {len(tif_files)} TIF file(s):")
        for f in tif_files:
            print(f"  - {f}")
        print("\nProcessing files...")
        print("-" * 40)

        success_count = 0
        for tif_file in tif_files:
            if check_nodata_value(tif_file):
                success_count += 1
            print()

        print("Done!")
        print(f"Successfully processed: {success_count}/{len(tif_files)} files")
        if success_count < len(tif_files):
            print("Some files failed to process. Check error messages above.")

    elif args.input:
        input_file = args.input
        if not os.path.isfile(input_file):
            print(f"Error: File not found: {input_file}")
            sys.exit(1)

        print("-" * 40)
        success = check_nodata_value(input_file)
        print()
        if success:
            print("Done!")
        else:
            print("Failed.")
            sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
