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
- **flipbath**: Flip the sign of bathymetry in GeoTIFF files (depth <-> elevation), writing `<name>_flip.tif`
- **mvdem**: Relocate GeoTIFF files by setting a new upper-left coordinate, without modifying pixel data
- **mat2tif**: Convert a plain-numeric matrix (grid) file (.csv or .txt) to a GeoTIFF file
- **tif2mat**: Convert a GeoTIFF raster band to a plain-numeric matrix (grid) file, .csv or .txt (the reverse of `mat2tif`)
- **tif2xyz**: Convert a GeoTIFF raster band to an XYZ point file (pixel-center X, Y, value)
- **xyz2mat**: Convert an XYZ point file to a matrix (grid) file (.csv and .txt), ready for `mat2tif`
- **xyz2tif**: Convert an XYZ point file on a regular grid to a GeoTIFF, deriving cell size and origin from the points (the reverse of `tif2xyz`)
- **demmask**: Extract the valid-data boundary of GeoTIFF files and save as shapefiles
- **demext**: Extract the bounding-box extent of GeoTIFF files and save as rectangle shapefiles

## Usage

### Command-line

```bash
# List all available commands
demtools -h

# Show details for a specific command
demtools-info mat2tif

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

# Flip bathymetry sign (depth <-> elevation), nodata kept as-is
flipbath dem.tif                  # -> dem_flip.tif
flipbath dem.tif -o elev.tif
flipbath -a

# Relocate a GeoTIFF by setting a new upper-left coordinate
mvdem dem.tif -x 500000 -y 2500000

# Convert a matrix grid (.csv or .txt) to GeoTIFF (origin as lower-left or upper-left corner)
mat2tif grid.csv -o dem.tif --xll 250000 --yll 2500000 --cellsize 5 -e 32648
mat2tif grid.txt -o dem.tif --xul 250000 --yul 2500100 --cellsize 5 -e 32648

# Convert a GeoTIFF raster band back to a matrix grid (.txt is tab delimited)
tif2mat dem.tif -o grid.csv
tif2mat dem.tif -o grid.txt

# Convert a GeoTIFF raster band to an XYZ point file (nodata skipped)
tif2xyz dem.tif -o points.xyz
tif2xyz dem.tif -d , --keep-nodata

# Convert an XYZ point file to a matrix grid (-> depths_mat.csv, depths_mat.txt)
xyz2mat depths.xyz
xyz2mat depths.xyz -o grid --south-up -n -9999

# Convert a gridded XYZ point file straight to GeoTIFF (cell size/origin from the points)
xyz2tif points.xyz -o dem.tif -e 3826

# Extract the valid-data boundary of all TIF files and save as shapefiles
demmask -a
demmask dem.tif -o SHP_MSK

# Extract the bounding-box extent of all TIF files and save as shapefiles
demext -a
demext dem.tif -o SHP_EXT
```

### Python API

```python
from demtools import asproj, chgnodata, defnodata, chkdem, flipbath, mvdem, mat2tif, tif2mat, tif2xyz, xyz2mat, xyz2tif, demmask, demext

# Assign a projection without touching pixel data
asproj.assign_projection("dem.tif", epsg=3826)

# Convert nodata value in a raster file
chgnodata.convert_nodata_value("dem.tif", output_nodata=-9999)

# Assign nodata metadata without touching pixel values
defnodata.define_nodata_value("dem.tif", nodata_value=-9999)

# Check DEM raster properties (read-only)
chkdem.check_dem_info("dem.tif")

# Flip bathymetry sign (depth <-> elevation) into a new file
flipbath.flip_bathymetry("dem.tif", "dem_flip.tif")

# Relocate a raster by setting a new upper-left coordinate
mvdem.relocate_dem("dem.tif", x=500000, y=2500000)

# Convert a matrix grid to GeoTIFF
mat2tif.mat_to_tif(
    input_mat="grid.csv",
    output_tif="dem.tif",
    xll=250000,
    yll=2500000,
    cellsize=5,
    nodata=-999,
    epsg=32648,
)

# Convert a GeoTIFF raster band back to a matrix grid
tif2mat.tif_to_mat(
    input_tif="dem.tif",
    output_mat="grid.csv",
)

# Convert a GeoTIFF raster band to an XYZ point file
tif2xyz.tif_to_xyz(
    input_tif="dem.tif",
    output_xyz="points.xyz",
)

# Convert an XYZ point file to a matrix grid (writes grid.csv and grid.txt)
xyz2mat.xyz_to_mat(
    input_xyz="depths.xyz",
    output_stem="grid",
)

# Convert a gridded XYZ point file to GeoTIFF
xyz2tif.xyz_to_tif(
    input_xyz="points.xyz",
    output_tif="dem.tif",
    epsg=3826,
)

# Extract the valid-data boundary and save as a shapefile
demmask.save_mask_boundary("dem.tif", output_dir="SHP_MSK")

# Extract the bounding-box extent and save as a shapefile
demext.save_dem_extent("dem.tif", output_dir="SHP_EXT")
```

## Notes

- `asproj`, `chgnodata`, `defnodata`, and `mvdem` automatically create a `RAS_BAK/` directory with backup copies before modifying files.
- `flipbath` never modifies the input; it writes a new `<name>_flip.tif` (or the `-o` path). Nodata pixels keep their value (e.g. `-999` does not become `999`). Unsigned integer rasters are rejected since they cannot hold negated values.
- `chkdem` (and its `deminfo` alias), `tif2mat`, `tif2xyz`, `demmask`, and `demext` are read-only and never modify the input file.
- `demmask` writes shapefiles to an output directory (default `SHP_MSK/`), one shapefile per input TIF, each holding a single polygon covering all of that file's valid-data pixels.
- `demext` writes shapefiles to an output directory (default `SHP_EXT/`), one shapefile per input TIF, each holding a single rectangle polygon covering that file's full raster extent.
- `mat2tif` expects a plain numeric matrix (no headers, comma or whitespace delimited), with rows ordered from north to south; `tif2mat` and `xyz2mat` write matrices in the same row order.
- `xyz2mat` builds the grid from the unique X/Y values in the input; cells with no point are filled with the nodata value (default `-999`, matching `mat2tif`), and `--south-up` reverses the row order.
- `xyz2tif` treats X/Y as pixel centers (as written by `tif2xyz`). The cell size is the smallest spacing between distinct X (and Y) values unless `--cellsize` is given; interior gaps become nodata, but rows/columns missing at the edges shrink the extent. Points off the regular grid are rejected.
- `tif2xyz` writes one `X Y Z` line per pixel using pixel-center coordinates from the geotransform; nodata (and NaN) pixels are skipped unless `--keep-nodata` is given.
- The input file is given positionally (`chkdem dem.tif`); the older `-i dem.tif` form still works for backward compatibility.
- GDAL must be installed separately via conda or a pre-built wheel; it is not listed in `requirements.txt` as it cannot be reliably installed via pip on all platforms.
