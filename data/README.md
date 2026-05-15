# Data Directory

This repository does not commit large InSAR or geospatial products.

Use these local subdirectories when running notebooks:

```text
data/raw/        Downloaded archives and untouched source products.
data/interim/    Converted files and extracted subsets.
data/processed/  Analysis-ready small tables or products.
data/external/   Data managed by external tools or cloud clients.
```

The `.gitignore` file excludes those directories and common large formats such as HDF5, NetCDF, GeoTIFF, VRT, and ZIP archives.

## Candidate Open Sources

- ASF HyP3 products for on-demand InSAR processing.
- OPERA DISP-S1 products for displacement time series.
- ARIA standard products where available.
- MintPy-compatible time-series outputs generated locally or from open workflows.
- Nevada Geodetic Laboratory or EarthScope GNSS time series for validation.

Each notebook should document the exact data source, access date, product version, geographic bounds, and processing assumptions used for a result.
