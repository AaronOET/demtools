#!/usr/bin/env python3
"""
chgnodata - Convert nodata values for TIF raster files
Uses GDAL/OGR Python bindings
"""

import glob
import argparse
import os
import sys
from osgeo import gdal, gdalconst

def convert_nodata_value(input_file, output_nodata=-999):
    """
    Convert nodata value of a raster file to specified value

    Args:
        input_file (str): Path to input TIF file
        output_nodata (float): New nodata value (default: -999)
    """
    print(f"Processing: {input_file}")

    # Open the input dataset
    src_ds = gdal.Open(input_file, gdalconst.GA_ReadOnly)
    if src_ds is None:
        print(f"Error: Could not open {input_file}")
        return False

    # Get raster band (assuming single band, modify if multi-band)
    src_band = src_ds.GetRasterBand(1)

    # Get current nodata value
    current_nodata = src_band.GetNoDataValue()
    print(f"  Current nodata value: {current_nodata}")

    if current_nodata == output_nodata:
        print(f"  Nodata value already set to {output_nodata}, skipping...")
        src_ds = None
        return True

    # Read the data
    data = src_band.ReadAsArray()

    # Get raster properties
    rows, cols = data.shape
    geotransform = src_ds.GetGeoTransform()
    projection = src_ds.GetProjection()
    data_type = src_band.DataType

    # Create backup directory
    backup_dir = "RAS_BAK"
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        print(f"  Created backup directory: {backup_dir}")

    backup_filename = os.path.basename(input_file)
    backup_file = os.path.join(backup_dir, backup_filename)

    # Create backup
    print(f"  Creating backup: {backup_file}")
    gdal.GetDriverByName('GTiff').CreateCopy(backup_file, src_ds)

    # Close source dataset
    src_ds = None

    # Create new dataset (overwrite original)
    driver = gdal.GetDriverByName('GTiff')
    out_ds = driver.Create(input_file, cols, rows, 1, data_type)

    # Set geotransform and projection
    out_ds.SetGeoTransform(geotransform)
    out_ds.SetProjection(projection)

    # Get output band
    out_band = out_ds.GetRasterBand(1)

    # Replace current nodata values with new nodata value
    if current_nodata is not None:
        data[data == current_nodata] = output_nodata

    # Write the data
    out_band.WriteArray(data)

    # Set the new nodata value
    out_band.SetNoDataValue(output_nodata)

    # Flush data to disk
    out_band.FlushCache()
    out_ds = None

    print(f"  Successfully converted nodata value to {output_nodata}")
    return True


def main():
    parser = argparse.ArgumentParser(
        prog='chgnodata',
        description='Convert nodata values for TIF raster files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  chgnodata -a                       # Process all *.tif in current directory (nodata=-999)
  chgnodata -a -v -9999              # Process all *.tif, set nodata to -9999
  chgnodata -i dem.tif               # Process a single file (nodata=-999)
  chgnodata -i dem.tif -v -9999      # Process a single file, set nodata to -9999
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
        help='New nodata value to set (default: -999)'
    )

    args = parser.parse_args()
    new_nodata = args.nodata_value

    print(f"chgnodata: converting nodata values to {new_nodata}")
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
            if convert_nodata_value(tif_file, new_nodata):
                success_count += 1
            print()

        print("Conversion complete!")
        print(f"Successfully processed: {success_count}/{len(tif_files)} files")
        if success_count < len(tif_files):
            print("Some files failed to process. Check error messages above.")

    elif args.input:
        input_file = args.input
        if not os.path.isfile(input_file):
            print(f"Error: File not found: {input_file}")
            sys.exit(1)

        print("-" * 40)
        success = convert_nodata_value(input_file, new_nodata)
        print()
        if success:
            print("Conversion complete!")
        else:
            print("Conversion failed.")
            sys.exit(1)


if __name__ == "__main__":
    gdal.UseExceptions()

    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
