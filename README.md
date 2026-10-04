# DEMTOOLS

A collection of Python tools for working with DEM (Digital Elevation Model) raster files.

> **GDAL Installation**: GDAL is required for this package. For conda environments, use `conda install gdal` to install GDAL. For non-conda environments, download the GDAL wheel file from [https://github.com/cgohlke/geospatial-wheels/releases](https://github.com/cgohlke/geospatial-wheels/releases) that matches your Python version and platform (e.g., `cp312` for Python 3.12, `win_amd64` for 64-bit Windows), then install it with `pip install <wheel-file>.whl`.

## Installation

```bash
pip install -e .
```

## Features

- **asproj**: Assign a projection to GeoTIFF files without modifying pixel data (metadata only)
- **chgnodata**: Convert (replace) the nodata value of GeoTIFF files, updating pixel data accordingly
- **defnodata**: Assign a nodata value to GeoTIFF files without modifying pixel data (metadata only)
- **chkdem** (alias: **deminfo**): Check DEM raster file properties (resolution, projection, extent, nodata) — read-only
- **mvdem**: Relocate GeoTIFF files by setting a new upper-left coordinate, without modifying pixel data
- **csv2tif**: Convert a plain-numeric CSV raster grid to a GeoTIFF file
- **tif2csv**: Convert a GeoTIFF raster band to a plain-numeric CSV grid (the reverse of `csv2tif`)
- **tif2xyz**: Convert a GeoTIFF raster band to an XYZ point file (pixel-center X, Y, value)
- **demmask**: Extract the valid-data boundary of GeoTIFF files and save as shapefiles
- **demext**: Extract the bounding-box extent of GeoTIFF files and save as rectangle shapefiles

## Usage

### Command-line

```bash
# List all available commands
demtools -h

# Show details for a specific command
demtools-info csv2tif

# Assign a projection to all TIF files in the current directory
asproj -a --epsg 3826
asproj dem.tif -e 3826

# Convert nodata values for all TIF files in the current directory
chgnodata -a

# Convert nodata of a single file to -9999
chgnodata dem.tif -v -9999

# Set nodata metadata for all TIF files (no pixel data change)
defnodata -a -v -9999

# Check DEM raster properties (read-only)
chkdem -a
chkdem dem.tif
deminfo dem.tif

# Relocate a GeoTIFF by setting a new upper-left coordinate
mvdem dem.tif -x 500000 -y 2500000

# Convert a CSV grid to GeoTIFF (origin as lower-left or upper-left corner)
csv2tif grid.csv -o dem.tif --xll 250000 --yll 2500000 --cellsize 5 -e 32648
csv2tif grid.csv -o dem.tif --xul 250000 --yul 2500100 --cellsize 5 -e 32648

# Convert a GeoTIFF raster band back to a CSV grid
tif2csv dem.tif -o grid.csv

# Convert a GeoTIFF raster band to an XYZ point file (nodata skipped)
tif2xyz dem.tif -o points.xyz
tif2xyz dem.tif -d , --keep-nodata

# Extract the valid-data boundary of all TIF files and save as shapefiles
demmask -a
demmask dem.tif -o SHP_MSK

# Extract the bounding-box extent of all TIF files and save as shapefiles
demext -a
demext dem.tif -o SHP_EXT
```

### Python API

```python
from demtools import asproj, chgnodata, defnodata, chkdem, mvdem, csv2tif, tif2csv, tif2xyz, demmask, demext

# Assign a projection without touching pixel data
asproj.assign_projection("dem.tif", epsg=3826)

# Convert nodata value in a raster file
chgnodata.convert_nodata_value("dem.tif", output_nodata=-9999)

# Assign nodata metadata without touching pixel values
defnodata.define_nodata_value("dem.tif", nodata_value=-9999)

# Check DEM raster properties (read-only)
chkdem.check_dem_info("dem.tif")

# Relocate a raster by setting a new upper-left coordinate
mvdem.relocate_dem("dem.tif", x=500000, y=2500000)

# Convert CSV grid to GeoTIFF
csv2tif.csv_to_tif(
    input_csv="grid.csv",
    output_tif="dem.tif",
    xll=250000,
    yll=2500000,
    cellsize=5,
    nodata=-999,
    epsg=32648,
)

# Convert a GeoTIFF raster band back to a CSV grid
tif2csv.tif_to_csv(
    input_tif="dem.tif",
    output_csv="grid.csv",
)

# Convert a GeoTIFF raster band to an XYZ point file
tif2xyz.tif_to_xyz(
    input_tif="dem.tif",
    output_xyz="points.xyz",
)

# Extract the valid-data boundary and save as a shapefile
demmask.save_mask_boundary("dem.tif", output_dir="SHP_MSK")

# Extract the bounding-box extent and save as a shapefile
demext.save_dem_extent("dem.tif", output_dir="SHP_EXT")
```

## Notes

- `asproj`, `chgnodata`, `defnodata`, and `mvdem` automatically create a `RAS_BAK/` directory with backup copies before modifying files.
- `chkdem` (and its `deminfo` alias), `tif2csv`, `tif2xyz`, `demmask`, and `demext` are read-only and never modify the input file.
- `demmask` writes shapefiles to an output directory (default `SHP_MSK/`), one shapefile per input TIF, each holding a single polygon covering all of that file's valid-data pixels.
- `demext` writes shapefiles to an output directory (default `SHP_EXT/`), one shapefile per input TIF, each holding a single rectangle polygon covering that file's full raster extent.
- `csv2tif` expects a plain numeric CSV (no headers), with rows ordered from north to south; `tif2csv` writes CSVs in the same row order.
- `tif2xyz` writes one `X Y Z` line per pixel using pixel-center coordinates from the geotransform; nodata (and NaN) pixels are skipped unless `--keep-nodata` is given.
- The input file is given positionally (`chkdem dem.tif`); the older `-i dem.tif` form still works for backward compatibility.
- GDAL must be installed separately via conda or a pre-built wheel; it is not listed in `requirements.txt` as it cannot be reliably installed via pip on all platforms.
