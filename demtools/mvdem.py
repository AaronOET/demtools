#!/usr/bin/env python3
"""
mvdem - Relocate TIF raster files by setting a new upper-left coordinate, without modifying pixel data
Uses GDAL/OGR Python bindings
"""

import glob
import argparse
import os
import sys
from osgeo import gdal, gdalconst

gdal.UseExceptions()

def relocate_dem(input_file, x, y):
    """
    Relocate a raster file by setting a new upper-left coordinate.
    Pixel size/rotation and pixel data are left unchanged; only the
    geotransform origin is updated.

    Args:
        input_file (str): Path to input TIF file
        x (float): New upper-left X coordinate
        y (float): New upper-left Y coordinate

    Returns:
        bool: True on success, False otherwise
    """
    print(f"Processing: {input_file}")

    # Open the input dataset in read-only to inspect current state
    src_ds = gdal.Open(input_file, gdalconst.GA_ReadOnly)
    if src_ds is None:
        print(f"Error: Could not open {input_file}")
        return False

    current_gt = src_ds.GetGeoTransform()
    current_x, pixel_width, rotation_x, current_y, rotation_y, pixel_height = current_gt
    print(f"  Current upper-left coordinate: ({current_x}, {current_y})")

    new_gt = (x, pixel_width, rotation_x, y, rotation_y, pixel_height)

    if current_gt == new_gt:
        print(f"  Upper-left coordinate already set to ({x}, {y}), skipping...")
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

    # Re-open in update mode to set the geotransform origin only (no pixel data changed)
    ds = gdal.Open(input_file, gdalconst.GA_Update)
    if ds is None:
        print(f"Error: Could not open {input_file} for update")
        return False

    ds.SetGeoTransform(new_gt)
    ds.FlushCache()
    ds = None

    print(f"  Successfully relocated to upper-left coordinate ({x}, {y})")
    return True


def main():
    parser = argparse.ArgumentParser(
        prog='mvdem',
        description='Relocate TIF raster files by setting a new upper-left coordinate',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  mvdem -i dem.tif -x 500000 -y 2500000      # Process a single file
  mvdem -a -x 500000 -y 2500000              # Process all *.tif in current directory
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
        '-x',
        dest='x',
        type=float,
        required=True,
        metavar='X',
        help='New upper-left X coordinate'
    )
    parser.add_argument(
        '-y',
        dest='y',
        type=float,
        required=True,
        metavar='Y',
        help='New upper-left Y coordinate'
    )

    args = parser.parse_args()
    x, y = args.x, args.y

    print(f"mvdem: relocating to upper-left coordinate ({x}, {y})")
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
            if relocate_dem(tif_file, x, y):
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
        success = relocate_dem(input_file, x, y)
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
