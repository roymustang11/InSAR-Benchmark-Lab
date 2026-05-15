# InSAR Benchmark Lab Design

## Purpose

This repository will become a professional research portfolio for hands-on InSAR work. Its first flagship direction is land subsidence and groundwater-related deformation because that problem has high public value, repeatable time-series behavior, strong validation opportunities, and direct relevance to Sentinel-1, OPERA, HyP3, MintPy, and future NISAR workflows.

The repository will not try to replace mature processors such as MintPy, MiaplPy, ISCE3, PyGMTSAR, or HyP3. Instead, it will sit above them as a reproducible benchmark and validation lab: ingest open InSAR products, compare workflows, quantify uncertainty, validate against independent geodetic data, and communicate results through polished notebooks.

## Research Thesis

Open InSAR processing has become powerful, but researchers and applied users still need transparent, reproducible ways to answer whether a deformation product is trustworthy for a given scientific question. This project will focus on uncertainty-aware validation and workflow comparison for ground deformation monitoring.

Initial thesis statement:

> Reproducible benchmarking, uncertainty analysis, and GNSS validation can make open InSAR deformation products more interpretable, comparable, and scientifically defensible across subsidence, volcano, and landslide applications.

## Initial Application Focus

The first application will be land subsidence caused by groundwater extraction. Candidate first regions are California Central Valley and the Houston/Gulf Coast region. The preferred first region is California Central Valley because it has strong Sentinel-1 coverage, extensive prior InSAR literature, clear deformation signals, and accessible GNSS stations for validation.

The later application modules will reuse the same framework:

- Volcano deformation: nonlinear deformation, event detection, and phase-linking comparison.
- Landslide deformation: coherence loss, slope-localized time series, and alert-style monitoring plots.

## Positioning Relative To Existing Projects

MintPy provides mature time-series analysis and visualization. This project will use MintPy outputs and focus on validation metrics, uncertainty checks, reference-point sensitivity, and notebook-driven case studies.

MiaplPy and phase-linking tools improve time-series quality. This project will compare phase-linking outputs against conventional workflows where practical, especially for decorrelating surfaces.

FanInSAR is useful for algorithm experimentation. This project may use it later for prototype methods, while keeping the first deliverables focused on reproducible applied science.

PyGMTSAR demonstrates an excellent Colab-first communication style. This project will adopt the public notebook experience but add stronger validation, uncertainty, and benchmark framing.

ISCE3, Dolphin, OPERA, ARIA, and HyP3 provide modern open processing ecosystems. This project will treat them as data and workflow sources rather than competitors.

## Repository Architecture

The repository should be organized around reproducible research products:

- `README.md`: professional research pitch, quickstart, notebooks, study areas, and roadmap.
- `notebooks/`: Colab-ready notebooks for data access, time-series analysis, validation, and comparison.
- `src/insar_benchmark_lab/`: lightweight Python utilities for loading outputs, computing metrics, and plotting.
- `data/README.md`: instructions for external datasets; large data should not be committed.
- `configs/`: study-area configuration files for reproducible runs.
- `docs/`: research notes, methods, design specs, and manuscript-style writeups.
- `tests/`: focused tests for metrics, loaders, and configuration parsing.

## Initial Notebook Set

The first notebook sequence should be:

1. `01_project_orientation.ipynb`: explain the study area, data sources, scientific question, and workflow map.
2. `02_hyp3_or_opera_to_timeseries.ipynb`: load open InSAR products and organize them into an analysis-ready structure.
3. `03_mintpy_timeseries_validation.ipynb`: ingest MintPy-style outputs and compare displacement time series to GNSS.
4. `04_uncertainty_and_reference_sensitivity.ipynb`: test how reference point choice, coherence thresholds, and masking affect deformation estimates.
5. `05_deformation_story_map.ipynb`: produce final maps, time-series plots, residuals, and interpretation figures.

The notebooks should be runnable locally first, then prepared for Colab where external dependencies and data access permit it.

## Python Package Scope

The first package should stay small and defensible. It should include:

- Product loaders for CSV, GeoTIFF, HDF5, and MintPy-style time-series data as needed.
- Validation metrics: RMSE, MAE, trend bias, correlation, velocity difference, residual distribution, and uncertainty calibration checks.
- Time-series utilities: date alignment, LOS displacement normalization, detrending, and station extraction.
- Plot helpers: displacement maps, GNSS-vs-InSAR time-series panels, residual maps, and benchmark tables.
- Configuration loading for study areas and dataset paths.

It should avoid reimplementing full InSAR processing, phase unwrapping, atmospheric correction, or orbital correction in the first phase.

## Data Flow

The intended first workflow is:

1. Select study area and time window.
2. Obtain open InSAR products from HyP3, OPERA, ARIA, or MintPy-compatible processing.
3. Convert product outputs into common local analysis structures.
4. Load GNSS station positions and time series where available.
5. Align InSAR and GNSS dates, reference frames, and units.
6. Compute validation and uncertainty metrics.
7. Produce publication-quality maps, time-series figures, and benchmark tables.

## Error Handling

The tools should fail clearly when required files, CRS metadata, dates, units, or reference information are missing. Errors should explain what is missing and which notebook or config field should be corrected. Silent assumptions about units, coordinate reference systems, or reference frames are not acceptable.

## Testing Strategy

Tests should start with small synthetic and fixture-based cases:

- Metric functions return expected values for known arrays.
- Date alignment handles missing dates and irregular sampling.
- Config validation catches missing required fields.
- Loaders identify unsupported or malformed inputs with clear errors.

Notebook execution tests can be added later after the first stable notebook sequence exists.

## First Milestone

The first public milestone is a professional GitHub repository that contains:

- A polished README with the research pitch and roadmap.
- A clear folder structure.
- A minimal tested Python package.
- One complete local notebook showing the subsidence validation workflow on a small sample or documented external dataset.
- A roadmap showing how the same framework extends to volcano and landslide monitoring.

## Out Of Scope For Phase One

The first phase will not build a new SAR processor, replace MintPy, automate large-scale cloud processing, or claim a novel deformation algorithm before validation infrastructure exists. Those are possible later research directions after the benchmark lab is credible.

