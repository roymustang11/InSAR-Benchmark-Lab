# Data Provenance

Datasets consumed by experiments are listed here with source, version,
license, access protocol, and citation. The specific granules and
station identifiers used are recorded in each experiment's
`results/manifest.json`.

## InSAR products

### OPERA Level-3 Surface Displacement (DISP-S1)

- **Source.** NASA JPL OPERA project, distributed by the Alaska Satellite
  Facility DAAC.
- **Short name.** `OPERA_L3_DISP-S1_V1`.
- **Coverage.** CONUS and selected international targets, derived from
  Sentinel-1 SLC stacks; per-frame, time-series displacement.
- **Format.** NetCDF-4 with CF conventions; Kerchunk-style Zarr-reference
  JSON sidecars for cloud-native access.
- **Access.** Earthdata Login required. Searched via the
  [`earthaccess`](https://earthaccess.readthedocs.io) Python client. Direct
  download from ASF DAAC HTTPS endpoints with bearer token.
- **License.** NASA open data; no use restrictions, citation requested.
- **Citation.** OPERA Project (2024). *Surface Displacement from
  Sentinel-1 (DISP-S1) Product*, NASA JPL.
- **Version policy.** `product_version` is recorded per granule;
  experiments pin to a single major version.

### ASF HyP3 SBAS

- **Source.** Alaska Satellite Facility, on-demand HyP3 service.
- **Format.** GeoTIFF stacks of unwrapped phase, coherence, amplitude,
  and metadata sidecars; SBAS time-series via the HyP3-SBAS workflow.
- **Access.** ASF account; submitted programmatically with
  [`hyp3_sdk`](https://hyp3-docs.asf.alaska.edu/using/sdk/).
- **License.** ASF terms of use; cite source missions.
- **Citation.** Hogenson et al. (2020). *Hybrid Pluggable Processing
  Pipeline (HyP3): A cloud-native infrastructure for generic processing
  of SAR data*. ASF.

### MintPy and MiaplPy

- **Software sources.**
  [`insarlab/MintPy`](https://github.com/insarlab/MintPy),
  [`insarlab/MiaplPy`](https://github.com/insarlab/MiaplPy).
- **Inputs.** ISCE3 or PyGMTSAR-prepared SLC stack; produces
  HDF5 time-series in MintPy's `timeseries.h5` and `velocity.h5` schema.
- **Format.** HDF5 with documented MintPy attributes.
- **License.** GPL-3.0 (MintPy), GPL-3.0 (MiaplPy).
- **Citations.**
  - Yunjun, Z., Fattahi, H., & Amelung, F. (2019). *Computers &
    Geosciences*, 133.
  - Mirzaee, S., Amelung, F., & Fattahi, H. (2023). MiaplPy: A
    Python package for phase-linking interferometric time-series.

### PyGMTSAR

- **Source.** [`AlexeyPechnikov/pygmtsar`](https://github.com/AlexeyPechnikov/pygmtsar).
- **Inputs.** Sentinel-1 SLC; orbit and DEM auto-fetched.
- **Outputs.** Interferograms, unwrapped phase, time-series in NetCDF.
- **License.** BSD-3-Clause.
- **Citation.** Pechnikov, A. (2024). *PyGMTSAR: Easy Sentinel-1 SAR
  Interferometry on top of GMTSAR*.

## GNSS products

### Nevada Geodetic Laboratory (NGL)

- **Source.** University of Nevada, Reno; Nevada Geodetic Laboratory.
- **Products used.**
  - Final daily position time series, `tenv3` format, IGS14 frame.
  - Plate-fixed solutions, `tenv3` format, NA12 (and other plates).
  - Station metadata (`DataHoldings.txt`).
- **Access.** HTTPS, no authentication; URLs of the form
  `http://geodesy.unr.edu/gps_timeseries/tenv3/{frame}/{STATION}.tenv3`.
- **License.** Public-domain release; cite Blewitt et al. (2018).
- **Citation.** Blewitt, G., Hammond, W. C., & Kreemer, C. (2018).
  Harnessing the GPS data explosion for interdisciplinary science.
  *EOS*, 99.
- **Quality flags.** Steps file (`steps.txt`) recording offsets;
  experiments may either remove offsets or exclude the affected
  intervals, with the choice recorded in the manifest.

### EarthScope (UNAVCO)

- **Source.** EarthScope Consortium archive.
- **Use.** Cross-check against NGL when available; not the default
  ground truth for this framework.
- **License.** EarthScope data policy; cite the contributing PIs and
  EarthScope.

## Auxiliary datasets

### Coastlines, basins, and administrative boundaries

- Natural Earth (public domain) for cartographic context.
- USGS California Central Valley aquifer system polygons (USGS Open-File
  Report 2009-1257, public domain).

### Digital elevation models

- Copernicus GLO-30 DEM (ESA, free for research, attribution required).
- DEM use in this framework is restricted to display and masking; InSAR
  processors apply their own DEM corrections upstream.

### Land cover and crop masks

- USGS National Land Cover Database (NLCD), public domain.
- USDA Cropland Data Layer (CDL), public domain, used to flag agricultural
  decorrelation regimes.

## Storage and reproducibility

Large products are not committed. Each experiment records:

- granule identifiers, station identifiers, and auxiliary file URLs;
- retrieval timestamp;
- SHA-256 of every input file at analysis time;
- access-client version (`earthaccess`, `hyp3_sdk`, `requests`).

A third party can reproduce any experiment by re-downloading the listed
identifiers from the original archives.
