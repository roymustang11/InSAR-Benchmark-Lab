# InSAR Benchmark Lab

Reproducible research tools and notebooks for validating open InSAR deformation products.

The first research theme is groundwater-related land subsidence. The repository focuses on a practical question that matters for scientific and operational InSAR work:

> When should an open InSAR deformation product be trusted for a specific ground-deformation problem?

This project does not replace mature processors such as MintPy, MiaplPy, ISCE3, PyGMTSAR, OPERA, ARIA, or HyP3. It sits above them as a benchmark and validation layer: ingest outputs, compare workflows, quantify uncertainty, validate against independent geodetic observations, and communicate results through reproducible notebooks.

## Research Direction

The initial flagship case study is land subsidence in California's Central Valley. This is a strong first target because it has clear deformation signals, public relevance, Sentinel-1 coverage, prior literature, and GNSS stations that can support validation.

Later modules will extend the same framework to volcano deformation and landslide monitoring.

## Planned Notebook Track

| Notebook | Status | Purpose |
| --- | --- | --- |
| [01 Project Orientation](notebooks/01_project_orientation.ipynb) [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/roymustang11/InSAR-Benchmark-Lab/blob/main/notebooks/01_project_orientation.ipynb) | Runnable orientation | Study area, scientific question, data sources, workflow map. |
| [02 OPERA DISP-S1 Product Search](notebooks/02_hyp3_or_opera_to_timeseries.ipynb) [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/roymustang11/InSAR-Benchmark-Lab/blob/main/notebooks/02_hyp3_or_opera_to_timeseries.ipynb) | Runnable metadata search | Search OPERA DISP-S1 products, build an inventory table, and inspect product metadata links. |
| [03 MintPy Time Series Validation](notebooks/03_mintpy_timeseries_validation.ipynb) | Stub | Compare InSAR displacement time series against GNSS. |
| [04 Uncertainty And Reference Sensitivity](notebooks/04_uncertainty_and_reference_sensitivity.ipynb) | Stub | Test reference-point, coherence, and masking sensitivity. |
| [05 Deformation Story Map](notebooks/05_deformation_story_map.ipynb) | Stub | Produce final maps, time-series plots, residuals, and interpretation figures. |

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev,notebooks]"
pytest
```

## Repository Layout

```text
configs/                  Study-area configuration files.
data/                     External data instructions; large data is not committed.
docs/                     Research notes, roadmap, and planning documents.
notebooks/                Colab-ready notebook sequence.
src/insar_benchmark_lab/  Lightweight validation and benchmarking utilities.
tests/                    Unit tests for metrics, config loading, and future loaders.
```

## First Milestone

- Build a small tested Python package for metrics and study-area configuration.
- Document a Central Valley subsidence case study.
- Prepare a Colab-style notebook sequence.
- Validate deformation time series against independent GNSS data.
- Quantify sensitivity to reference-point choice and masking decisions.

## Data Policy

Large geospatial products, HDF5 files, GeoTIFFs, and downloaded archives are intentionally excluded from Git. The repository will document how to obtain data from open sources such as ASF HyP3, OPERA, ARIA, MintPy-compatible outputs, and GNSS archives.

## Status

This repository is in its initial research-foundation phase. The first implemented code focuses on validation metrics and reproducible study-area configuration.
