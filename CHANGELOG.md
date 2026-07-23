# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).


## [0.12.0] - 2026-07-23

### Added
- `getmask` was writing shapefile boundaries in raw pixel/line coordinates
  instead of georeferenced map coordinates, because `gdal.Polygonize` was
  called with the mask band as its own source band (which has no dataset to
  pull a geotransform from). It now polygonizes the real raster band, using
  the mask band only to filter valid-data pixels. Also removed a stale
  `value == 0` filter that would have incorrectly dropped valid pixels whose
  data value is legitimately `0`.
- `getmask` tool to extract the valid-data boundary of GeoTIFF files and save
  it as an ESRI Shapefile, ported from `prototype/getmask.py` onto GDAL/OGR
  (no new dependencies) instead of the prototype's geopandas/rasterio/shapely stack.

## [0.11.1] - 2026-07-23

### Changed
- Updated README.md to document all current tools (`asproj`, `chkdem`/`deminfo`,
  `mvdem`, `tif2csv`) and current CLI flags (`-e`, `--xul`/`--yul`).

## [0.11.0] - 2026-07-23

### Added
- `-e` as a short alias for `--epsg` in `csv2tif`.
- `--xul` and `--yul` options in `csv2tif` to set the raster origin as the
  upper-left corner directly, as an alternative to `--xll`/`--yll`.
- `tif2csv` tool to convert a GeoTIFF raster band to a plain-numeric CSV grid
  (the reverse of `csv2tif`).

## [0.10.5] - 2026-07-23

### Added
- `-e` as a short alias for `--epsg` in `asproj`.

## [0.10.2] - 2026-07-23

### Fixed
- Registered the `deminfo` alias (packaged as an entry point pointing at
  `chkdem`) in `demtools-info`'s tool descriptions so it now appears in
  `demtools -h` and has its own `demtools-info deminfo` detail page.

## [0.10.1] - 2026-07-11

### Changed
- Updated project metadata in `pyproject.toml`.

## [0.10.0] - 2026-07-07

### Changed
- Updated nodata handling in the `chkdem` tool.

## [0.9.0] - 2026-07-07

### Added
- `asproj` tool for assigning a projection to TIF files without modifying pixel data.
- `chkdem` tool for reporting DEM raster properties (resolution, projection, extent, nodata).

### Removed
- `chknodata` tool, superseded by `chkdem`.

## [0.8.0] - 2026-07-07

### Added
- `chknodata` tool to check nodata values in TIF files.

## [0.7.3] - 2026-07-07

### Changed
- Version bump; no functional changes.

## [0.7.2] - 2026-07-07

### Changed
- Version bump; no functional changes.

## [0.7.1] - 2026-07-07

### Added
- `demtools` script entry point.

### Changed
- CLI now displays version via `demtools -v`.

## [0.7.0] - 2026-07-07

### Changed
- Renamed `setnodata` to `defnodata` and updated related documentation.

## [0.5.1] - 2026-05-24

### Changed
- Version bump; no functional changes.

## [0.5.0] - 2026-05-24

### Added
- CLI entry point with core command functionality.

## [0.4.1] - 2026-05-11

### Fixed
- Added `gdal.UseExceptions()` to `chgnodata.py`, `csv2tif.py`, and `setnodata.py`.

## [0.3.0] - 2026-05-11

### Changed
- Removed `setup.py` as part of project restructuring in favor of `pyproject.toml`.

### Fixed
- CI/CD publishing pipeline (PyPI/TestPyPI GitHub Actions workflow).

## [0.2.0] - 2026-05-11

### Added
- Initial GitHub Actions workflow for publishing to PyPI and TestPyPI.

## [0.1.0] - 2026-05-11

### Added
- Initial release.
