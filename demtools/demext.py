#!/usr/bin/env python3
"""
demext - Extract the bounding-box extent of DEM raster files as rectangle shapefiles
Uses GDAL/OGR Python bindings
"""

import argparse
import glob
import os
import sys
from osgeo import gdal, gdalconst, ogr, osr

gdal.UseExceptions()


def compute_extent(input_file):
    """
    Compute the full bounding-box extent of a raster file from its
    geotransform and raster dimensions.

    Args:
        input_file (str): Path to input TIF file

    Returns:
        tuple: (minx, maxx, miny, maxy, srs_wkt), or None if the file could
        not be opened. srs_wkt is an empty string if undefined.
    """
    ds = gdal.Open(input_file, gdalconst.GA_ReadOnly)
    if ds is None:
        return None

    cols = ds.RasterXSize
    rows = ds.RasterYSize
    origin_x, pixel_width, _, origin_y, _, pixel_height = ds.GetGeoTransform()
    srs_wkt = ds.GetProjection()
    ds = None

    x1 = origin_x
    x2 = origin_x + cols * pixel_width
    y1 = origin_y
    y2 = origin_y + rows * pixel_height

    minx, maxx = min(x1, x2), max(x1, x2)
    miny, maxy = min(y1, y2), max(y1, y2)
    return minx, maxx, miny, maxy, srs_wkt


def save_dem_extent(input_file, output_dir="SHP_EXT"):
    """
    Extract the bounding-box extent of a DEM raster file as a single
    rectangle polygon, and save it as a new shapefile in output_dir.

    Args:
        input_file (str): Path to input TIF file
        output_dir (str): Directory to save the extent shapefile into

    Returns:
        bool: True on success, False otherwise
    """
    print(f"Processing: {input_file}")

    extent = compute_extent(input_file)
    if extent is None:
        print(f"Error: Could not open {input_file}")
        return False

    minx, maxx, miny, maxy, srs_wkt = extent
    print(f"  Extent: X [{minx}, {maxx}], Y [{miny}, {maxy}]")

    os.makedirs(output_dir, exist_ok=True)
    stem = os.path.splitext(os.path.basename(input_file))[0]
    out_path = os.path.join(output_dir, f"{stem}.shp")

    driver = ogr.GetDriverByName("ESRI Shapefile")
    if os.path.exists(out_path):
        driver.DeleteDataSource(out_path)

    out_ds = driver.CreateDataSource(out_path)
    srs = osr.SpatialReference()
    if srs_wkt:
        srs.ImportFromWkt(srs_wkt)
    out_layer = out_ds.CreateLayer(stem, srs=srs if srs_wkt else None, geom_type=ogr.wkbPolygon)

    for field_name in ("minx", "miny", "maxx", "maxy"):
        out_layer.CreateField(ogr.FieldDefn(field_name, ogr.OFTReal))
    field_defn = ogr.FieldDefn("tif_name", ogr.OFTString)
    field_defn.SetWidth(254)
    out_layer.CreateField(field_defn)

    ring = ogr.Geometry(ogr.wkbLinearRing)
    ring.AddPoint_2D(minx, miny)
    ring.AddPoint_2D(maxx, miny)
    ring.AddPoint_2D(maxx, maxy)
    ring.AddPoint_2D(minx, maxy)
    ring.AddPoint_2D(minx, miny)

    polygon = ogr.Geometry(ogr.wkbPolygon)
    polygon.AddGeometry(ring)

    feature = ogr.Feature(out_layer.GetLayerDefn())
    feature.SetGeometry(polygon)
    feature.SetField("minx", minx)
    feature.SetField("miny", miny)
    feature.SetField("maxx", maxx)
    feature.SetField("maxy", maxy)
    feature.SetField("tif_name", stem)
    out_layer.CreateFeature(feature)

    feature = None
    out_ds = None

    print(f"  Successfully saved extent to: {out_path}")
    return True


def main():
    parser = argparse.ArgumentParser(
        prog='demext',
        description='Extract the bounding-box extent of DEM raster files as rectangle shapefiles',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  demext -a                        # Process all *.tif in current directory
  demext -i dem.tif                # Process a single file
  demext -a -o SHP_EXT             # Process all *.tif, write shapefiles to SHP_EXT/
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
        '-o', '--output',
        default='SHP_EXT',
        metavar='DIR',
        help='Output directory for shapefiles (default: SHP_EXT)'
    )

    args = parser.parse_args()

    print("demext: extracting DEM extents")
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
            if save_dem_extent(tif_file, args.output):
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
        success = save_dem_extent(input_file, args.output)
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
