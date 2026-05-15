# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [Semantic Versioning](https://semver.org/).

## [0.2.0] — 2026-05-15

### Added

- Methodology, validation protocol, and data-provenance documents under
  `docs/`.
- Documentation figures under `docs/figures/` with a reproducible
  generator script.
- `disp_s1_eval.processors` package: `DeformationProductReader` protocol
  with adapters for OPERA DISP-S1 (full implementation), MintPy (full
  implementation), and registered stubs for MiaplPy, HyP3-SBAS, and
  PyGMTSAR.
- `disp_s1_eval.gnss` package: NGL `tenv3` ingestion, ENU-to-LOS
  projection with covariance propagation, and three temporal collocation
  strategies (`nearest`, `weighted_window`, `gaussian_smoothing`).
- `disp_s1_eval.errors` package: empirical variogram with exponential
  fit, triple collocation (McColl 2014), paired bootstrap, reference-point
  bootstrap, and closure-phase residual diagnostic.
- `experiments/E01_central_valley_disp_s1_vs_gnss/` with config, CLI
  runner (`--dry-run` mode included), README, and a `results/` directory
  layout that produces `manifest.json` and `summary.md`.
- `CITATION.cff`, `AUTHORS.md`, and this changelog.

### Changed

- Package renamed from `insar_benchmark_lab` to `disp_s1_eval`. The old
  import path is preserved as an alias for backward compatibility.
- `pyproject.toml` updated: new project name, version, keywords, and an
  `[io]` extras group covering `xarray`, `h5py`, `netCDF4`, `zarr`,
  `pandas`, and `requests`.
- README rewritten with a project hero figure, badges, scope statement,
  pipeline diagrams, install and usage sections, and module reference.

### Tests

- 63 tests across 9 files, all passing.

## [0.1.0] — 2026-05-14

### Added

- Initial scaffolding: validation metrics, OPERA filename and Zarr
  reference helpers, study-area config loader, displacement
  time-series container, and five orientation notebooks.
