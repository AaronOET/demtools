#!/usr/bin/env python3
"""
chkdem - Check DEM raster file properties (resolution, projection, extent, nodata)
Uses GDAL/OGR Python bindings
"""

import glob
import argparse
import os
import sys
import numpy as np
from osgeo import gdal, gdalconst, osr

gdal.UseExceptions()

def _describe_projection(wkt):
    """
    Build a short human-readable projection description from a WKT string.

    Args:
        wkt (str): Projection in WKT format (as returned by GetProjection())

    Returns:
        str: Description such as "WGS 84 / UTM zone 48N (EPSG:32648)", or
             "Not defined" if no projection is set.
    """
    if not wkt:
        return "Not defined"

    srs = osr.SpatialReference()
    srs.ImportFromWkt(wkt)

    if srs.IsProjected():
        name = srs.GetAttrValue('PROJCS')
    elif srs.IsGeographic():
        name = srs.GetAttrValue('GEOGCS')
    else:
        name = "Unknown"

    authority = srs.GetAttrValue('AUTHORITY', 0)
    code = srs.GetAttrValue('AUTHORITY', 1)
    if authority and code:
        return f"{name} ({authority}:{code})"
    return name or "Unknown"


def check_dem_info(input_file):
    """
    Report DEM raster properties: dimensions, resolution, projection,
    upper-left coordinates, and per-band nodata statistics.

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

    cols = ds.RasterXSize
    rows = ds.RasterYSize
    band_count = ds.RasterCount

    geotransform = ds.GetGeoTransform()
    origin_x, pixel_width, _, origin_y, _, pixel_height = geotransform
    projection = _describe_projection(ds.GetProjection())

    print(f"  Dimensions: {cols} x {rows} (cols x rows), {band_count} band(s)")
    print(f"  Resolution: {pixel_width} x {abs(pixel_height)}")
    print(f"  Upper-left coordinate: ({origin_x}, {origin_y})")
    print(f"  Projection: {projection}")

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
        is_float = np.issubdtype(data.dtype, np.floating)
        nan_mask = np.isnan(data) if is_float else np.zeros(data.shape, dtype=bool)

        if nodata is not None and not (is_float and np.isnan(nodata)):
            value_mask = data == nodata
        else:
            value_mask = np.zeros(data.shape, dtype=bool)

        nodata_mask = value_mask | nan_mask
        nodata_count = int(np.count_nonzero(nodata_mask))
        valid_data = data[~nodata_mask]

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
        prog='chkdem',
        description='Check DEM raster file properties (resolution, projection, extent, nodata)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  chkdem -a                       # Check all *.tif in current directory
  chkdem -i dem.tif               # Check a single file
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

    print("chkdem: checking DEM raster properties")
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
            if check_dem_info(tif_file):
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
        success = check_dem_info(input_file)
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
