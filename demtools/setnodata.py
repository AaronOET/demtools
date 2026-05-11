#!/usr/bin/env python3
"""
setnodata - Define (assign) a nodata value for TIF raster files without modifying pixel data
Uses GDAL/OGR Python bindings
"""

import glob
import argparse
import os
import sys
from osgeo import gdal, gdalconst

gdal.UseExceptions()

def define_nodata_value(input_file, nodata_value=-999):
    """
    Define a nodata value for a raster file without changing any pixel data.
    Only the nodata metadata is updated in the file.

    Args:
        input_file (str): Path to input TIF file
        nodata_value (float): Nodata value to assign (default: -999)
    """
    print(f"Processing: {input_file}")

    # Open the input dataset in read-only to inspect current state
    src_ds = gdal.Open(input_file, gdalconst.GA_ReadOnly)
    if src_ds is None:
        print(f"Error: Could not open {input_file}")
        return False

    # Get raster band (assuming single band, modify if multi-band)
    src_band = src_ds.GetRasterBand(1)

    # Get current nodata value
    current_nodata = src_band.GetNoDataValue()
    print(f"  Current nodata value: {current_nodata}")

    if current_nodata == nodata_value:
        print(f"  Nodata value already set to {nodata_value}, skipping...")
        src_ds = None
        return True

    # Close read-only handle before backup/update
    src_ds = None

    # Create backup directory
    backup_dir = "RAS_BAK"
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        print(f"  Created backup directory: {backup_dir}")

    backup_filename = os.path.basename(input_file)
    backup_file = os.path.join(backup_dir, backup_filename)

    # Create backup before modifying
    print(f"  Creating backup: {backup_file}")
    src_ds = gdal.Open(input_file, gdalconst.GA_ReadOnly)
    gdal.GetDriverByName('GTiff').CreateCopy(backup_file, src_ds)
    src_ds = None

    # Re-open in update mode to set nodata metadata only (no pixel data changed)
    ds = gdal.Open(input_file, gdalconst.GA_Update)
    if ds is None:
        print(f"Error: Could not open {input_file} for update")
        return False

    band = ds.GetRasterBand(1)
    band.SetNoDataValue(nodata_value)
    band.FlushCache()
    ds = None

    print(f"  Successfully defined nodata value as {nodata_value}")
    return True


def main():
    parser = argparse.ArgumentParser(
        prog='setnodata',
        description='Define a nodata value for TIF raster files without modifying pixel data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  setnodata -a                       # Process all *.tif in current directory (nodata=-999)
  setnodata -a -v -9999              # Process all *.tif, define nodata as -9999
  setnodata -i dem.tif               # Process a single file (nodata=-999)
  setnodata -i dem.tif -v -9999      # Process a single file, define nodata as -9999
        """
    )

    # Mutually exclusive group: -a or -i
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '-a', '--all',
        action='store_true',
        help='Process all *.tif files in the current directory'
    )
    group.add_argument(
        '-i', '--input',
        metavar='FILE',
        help='Process a single TIF file'
    )

    parser.add_argument(
        '-v', '--value',
        dest='nodata_value',
        type=float,
        default=-999,
        metavar='NODATA',
        help='Nodata value to assign (default: -999)'
    )

    args = parser.parse_args()
    new_nodata = args.nodata_value

    print(f"setnodata: defining nodata value as {new_nodata}")
    print("=" * 60)

    if args.all:
        tif_files = glob.glob("*.tif")
        if not tif_files:
            print("No TIF files found in current directory.")
            sys.exit(0)

        print(f"Found {len(tif_files)} TIF file(s):")
        for f in tif_files:
            print(f"  - {f}")
        print(f"\nProcessing files...")
        print("-" * 40)

        success_count = 0
        for tif_file in tif_files:
            if define_nodata_value(tif_file, new_nodata):
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
        success = define_nodata_value(input_file, new_nodata)
        print()
        if success:
            print("Done!")
        else:
            print("Failed.")
            sys.exit(1)


if __name__ == "__main__":
    gdal.UseExceptions()

    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
