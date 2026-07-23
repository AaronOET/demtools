#!/usr/bin/env python3
"""
asproj - Assign a projection (spatial reference) to TIF raster files without modifying pixel data
Uses GDAL/OGR Python bindings
"""

import glob
import argparse
import os
import sys
from osgeo import gdal, gdalconst, osr

gdal.UseExceptions()

def assign_projection(input_file, epsg):
    """
    Assign a projection to a raster file without changing any pixel data.
    Only the projection metadata is updated in the file.

    Args:
        input_file (str): Path to input TIF file
        epsg (int): EPSG code of the spatial reference to assign

    Returns:
        bool: True on success, False otherwise
    """
    print(f"Processing: {input_file}")

    srs = osr.SpatialReference()
    try:
        srs.ImportFromEPSG(epsg)
    except RuntimeError:
        print(f"Error: Invalid or unknown EPSG code: {epsg}")
        return False

    # Open the input dataset in read-only to inspect current state
    src_ds = gdal.Open(input_file, gdalconst.GA_ReadOnly)
    if src_ds is None:
        print(f"Error: Could not open {input_file}")
        return False

    current_wkt = src_ds.GetProjection()
    new_wkt = srs.ExportToWkt()
    print(f"  Current projection: {current_wkt if current_wkt else 'Not defined'}")

    if current_wkt == new_wkt:
        print(f"  Projection already set to EPSG:{epsg}, skipping...")
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

    # Re-open in update mode to set projection metadata only (no pixel data changed)
    ds = gdal.Open(input_file, gdalconst.GA_Update)
    if ds is None:
        print(f"Error: Could not open {input_file} for update")
        return False

    ds.SetProjection(new_wkt)
    ds.FlushCache()
    ds = None

    print(f"  Successfully assigned projection EPSG:{epsg}")
    return True


def main():
    parser = argparse.ArgumentParser(
        prog='asproj',
        description='Assign a projection to TIF raster files without modifying pixel data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  asproj -a --epsg 3826              # Process all *.tif in current directory
  asproj -i dem.tif --epsg 3826      # Process a single file
  asproj -i dem.tif -e 3826          # Same as above, using the -e alias
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
        '-e', '--epsg',
        type=int,
        required=True,
        metavar='CODE',
        help='EPSG code of the projection to assign'
    )

    args = parser.parse_args()
    epsg = args.epsg

    print(f"asproj: assigning projection EPSG:{epsg}")
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
            if assign_projection(tif_file, epsg):
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
        success = assign_projection(input_file, epsg)
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
