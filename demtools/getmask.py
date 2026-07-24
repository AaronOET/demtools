#!/usr/bin/env python3
"""
getmask - Extract the valid-data boundary of TIF raster files and save as shapefiles
Uses GDAL/OGR Python bindings
"""

import argparse
import glob
import os
import sys
from osgeo import gdal, gdalconst, ogr, osr

gdal.UseExceptions()

def extract_boundary(input_file):
    """
    Extract the valid-data boundary of a raster file as a single OGR polygon
    geometry, merging all contiguous valid-data regions from the raster's
    mask band (nodata-derived unless the file carries an explicit mask).

    Args:
        input_file (str): Path to input TIF file

    Returns:
        tuple: (ogr.Geometry or None, str) — the boundary geometry (None if
        the file could not be opened or has no valid data) and the raster's
        projection WKT (empty string if undefined).
    """
    ds = gdal.Open(input_file, gdalconst.GA_ReadOnly)
    if ds is None:
        return None, ""

    band = ds.GetRasterBand(1)
    mask_band = band.GetMaskBand()
    srs_wkt = ds.GetProjection()

    # Reclassify to a binary valid-data raster before polygonizing, the same
    # way prototype/rasmask.py reclassifies the DEM to a single value before
    # RasterToPolygon. GDALPolygonize groups pixels by *equal source value*,
    # so polygonizing the raw elevation band (as this function used to do,
    # passing the mask band along only as a mask) makes it emit one polygon
    # per contiguous run of pixels sharing the exact same elevation — for a
    # continuous DEM surface that's close to one polygon per pixel, and the
    # resulting flood-fill and union work dominates runtime. Copying the mask
    # band into a real in-memory raster (so it has its own geotransform) and
    # polygonizing that instead collapses every valid pixel to one value, so
    # only the actual valid/nodata boundary gets vectorized — a handful of
    # polygons instead of potentially millions.
    mem_raster_ds = gdal.GetDriverByName("MEM").Create(
        "", ds.RasterXSize, ds.RasterYSize, 1, gdalconst.GDT_Byte
    )
    mem_raster_ds.SetGeoTransform(ds.GetGeoTransform())
    mem_raster_ds.SetProjection(srs_wkt)
    mem_band = mem_raster_ds.GetRasterBand(1)
    mem_band.WriteArray(mask_band.ReadAsArray())

    # "MEM" is the unified in-memory vector driver name from GDAL 3.11+;
    # older GDAL only knows the vector driver as "Memory".
    mem_driver_name = "MEM" if ogr.GetDriverByName("MEM") else "Memory"
    mem_ds = ogr.GetDriverByName(mem_driver_name).CreateDataSource("mask")
    srs = osr.SpatialReference()
    if srs_wkt:
        srs.ImportFromWkt(srs_wkt)
    layer = mem_ds.CreateLayer("mask", srs=srs if srs_wkt else None, geom_type=ogr.wkbPolygon)
    layer.CreateField(ogr.FieldDefn("value", ogr.OFTInteger))

    gdal.Polygonize(mem_band, mem_band, layer, 0)

    # mem_band doubles as its own mask, so pixels with mask value 0 (nodata)
    # never get vectorized in the first place; every feature produced is a
    # valid-data region.
    #
    # Union all polygons in one cascaded/unary pass rather than folding them
    # together one at a time: a naive `boundary = boundary.Union(geom)` loop
    # re-unions the whole accumulated boundary against each new polygon, which
    # is O(n^2) in the polygon count.
    multi = ogr.Geometry(ogr.wkbMultiPolygon)
    for feature in layer:
        geom = feature.GetGeometryRef()
        if geom is not None:
            multi.AddGeometry(geom)

    if multi.GetGeometryCount() == 0:
        boundary = None
    elif hasattr(multi, "UnaryUnion"):
        boundary = multi.UnaryUnion()
    else:
        boundary = multi.UnionCascaded()

    mem_raster_ds = None
    ds = None
    return boundary, srs_wkt


def save_mask_boundary(input_file, output_dir):
    """
    Extract the valid-data boundary of a raster file and save it as an ESRI
    Shapefile in output_dir, named after the input file.

    Args:
        input_file (str): Path to input TIF file
        output_dir (str): Directory to write the output shapefile into

    Returns:
        bool: True on success, False otherwise
    """
    print(f"Processing: {input_file}")

    boundary, srs_wkt = extract_boundary(input_file)
    if boundary is None:
        print(f"Error: Could not open {input_file} or no valid data found")
        return False

    os.makedirs(output_dir, exist_ok=True)
    stem = os.path.splitext(os.path.basename(input_file))[0]
    out_path = os.path.join(output_dir, f"{stem}.shp")

    shp_driver = ogr.GetDriverByName("ESRI Shapefile")
    if os.path.exists(out_path):
        shp_driver.DeleteDataSource(out_path)

    out_ds = shp_driver.CreateDataSource(out_path)
    srs = osr.SpatialReference()
    if srs_wkt:
        srs.ImportFromWkt(srs_wkt)
    out_layer = out_ds.CreateLayer(stem, srs=srs if srs_wkt else None, geom_type=ogr.wkbPolygon)

    field_defn = ogr.FieldDefn("tif_name", ogr.OFTString)
    field_defn.SetWidth(254)
    out_layer.CreateField(field_defn)

    feature = ogr.Feature(out_layer.GetLayerDefn())
    feature.SetGeometry(boundary)
    feature.SetField("tif_name", stem)
    out_layer.CreateFeature(feature)

    feature = None
    out_ds = None

    print(f"  Saved boundary: {out_path}")
    return True


def main():
    parser = argparse.ArgumentParser(
        prog='getmask',
        description='Extract the valid-data boundary of TIF raster files and save as shapefiles',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  getmask -a                       # Process all *.tif in current directory
  getmask -i dem.tif                # Process a single file
  getmask -a -o SHP_MSK             # Process all *.tif, write shapefiles to SHP_MSK/
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
        default='SHP_MSK',
        metavar='DIR',
        help='Output directory for shapefiles (default: SHP_MSK)'
    )

    args = parser.parse_args()

    print("getmask: extracting valid-data boundary")
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
            if save_mask_boundary(tif_file, args.output):
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
        success = save_mask_boundary(input_file, args.output)
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
