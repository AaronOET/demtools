# DEMTOOLS

A collection of Python tools for working with DEM (Digital Elevation Model) raster files.

> **GDAL Installation**: GDAL is required for this package. For conda environments, use `conda install gdal` to install GDAL. For non-conda environments, download the appropriate wheel file from [https://github.com/cgohlke/geospatial-wheels/releases](https://github.com/cgohlke/geospatial-wheels/releases) to install GDAL.

## Installation

```bash
pip install -e .
```

## Features

- **chgnodata**: Convert (replace) the nodata value of GeoTIFF files, updating pixel data accordingly
- **defnodata**: Assign a nodata value to GeoTIFF files without modifying pixel data (metadata only)
- **csv2tif**: Convert a plain-numeric CSV raster grid to a GeoTIFF file

## Usage

### Command-line

```bash
# List all available commands
demtools-info

# Convert nodata values for all TIF files in the current directory
chgnodata -a

# Convert nodata of a single file to -9999
chgnodata -i dem.tif -v -9999

# Set nodata metadata for all TIF files (no pixel data change)
defnodata -a -v -9999

# Convert a CSV grid to GeoTIFF
csv2tif -i grid.csv -o dem.tif --xll 250000 --yll 2500000 --cellsize 5 --epsg 32648
```

### Python API

```python
from demtools import chgnodata, defnodata, csv2tif

# Convert nodata value in a raster file
chgnodata.convert_nodata_value("dem.tif", output_nodata=-9999)

# Assign nodata metadata without touching pixel values
defnodata.define_nodata_value("dem.tif", nodata_value=-9999)

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
```

## Notes

- `chgnodata` and `defnodata` automatically create a `RAS_BAK/` directory with backup copies before modifying files.
- `csv2tif` expects a plain numeric CSV (no headers), with rows ordered from north to south.
- GDAL must be installed separately via conda or a pre-built wheel; it is not listed in `requirements.txt` as it cannot be reliably installed via pip on all platforms.
