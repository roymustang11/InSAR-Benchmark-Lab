# InSAR Benchmark Lab Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first professional, testable repository foundation for an uncertainty-aware InSAR benchmark lab focused on groundwater-related land subsidence.

**Architecture:** Keep the repository lightweight and research-oriented: public docs and notebooks at the top level, a small installable package under `src/insar_benchmark_lab`, and focused tests under `tests`. The package starts with validation metrics and config loading because those are stable foundations for later InSAR product loaders and notebook workflows.

**Tech Stack:** Python 3.10+, NumPy, PyYAML, pytest, Jupyter notebooks, Markdown documentation, Git.

---

## File Structure

- Create `README.md`: public GitHub landing page with research thesis, quickstart, notebook roadmap, and source projects.
- Create `LICENSE`: MIT license for original code and docs.
- Create `.gitignore`: Python, notebook, cache, environment, and geospatial-data ignore rules.
- Create `pyproject.toml`: package metadata, runtime dependencies, dev dependencies, pytest configuration.
- Create `src/insar_benchmark_lab/__init__.py`: public package exports.
- Create `src/insar_benchmark_lab/metrics.py`: validation metrics for InSAR-vs-GNSS comparisons.
- Create `src/insar_benchmark_lab/config.py`: YAML study-area config loader and validator.
- Create `src/insar_benchmark_lab/timeseries.py`: lightweight CSV time-series loader and date alignment utility.
- Create `tests/test_metrics.py`: focused tests for validation metrics.
- Create `tests/test_config.py`: focused tests for config validation.
- Create `tests/test_timeseries.py`: focused tests for CSV loading and date alignment.
- Create `configs/central_valley_subsidence.yml`: first study-area configuration.
- Create `data/README.md`: external data policy and suggested data sources.
- Create `docs/research-roadmap.md`: staged research roadmap across subsidence, volcanoes, and landslides.
- Create `notebooks/README.md`: notebook sequence and execution expectations.
- Create five notebook stubs in `notebooks/`: valid `.ipynb` files with clear objectives and no false outputs.

## Task 1: Project Metadata And Public README

**Files:**
- Create: `.gitignore`
- Create: `LICENSE`
- Create: `pyproject.toml`
- Create: `README.md`

- [ ] **Step 1: Create `.gitignore`**

Add this file:

```gitignore
# Python
__pycache__/
*.py[cod]
*.egg-info/
.pytest_cache/
.ruff_cache/
.mypy_cache/
.coverage
htmlcov/

# Environments
.venv/
venv/
env/
.env

# Jupyter
.ipynb_checkpoints/

# Local data and generated products
data/raw/
data/interim/
data/processed/
data/external/
outputs/
*.h5
*.hdf5
*.nc
*.tif
*.tiff
*.vrt
*.zip

# OS/editor
.DS_Store
.idea/
.vscode/
```

- [ ] **Step 2: Create `LICENSE`**

Use MIT license text with copyright holder:

```text
MIT License

Copyright (c) 2026 Shubham Singh

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 3: Create `pyproject.toml`**

Add this file:

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "insar-benchmark-lab"
version = "0.1.0"
description = "Reproducible InSAR benchmarking and validation tools for ground deformation studies."
readme = "README.md"
requires-python = ">=3.10"
license = { text = "MIT" }
authors = [
  { name = "Shubham Singh" }
]
keywords = ["InSAR", "remote-sensing", "geodesy", "subsidence", "GNSS"]
dependencies = [
  "numpy>=1.24",
  "PyYAML>=6.0"
]

[project.optional-dependencies]
dev = [
  "pytest>=8.0"
]
notebooks = [
  "jupyter>=1.0",
  "matplotlib>=3.8",
  "pandas>=2.0"
]

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
addopts = "-q"
```

- [ ] **Step 4: Create `README.md`**

Add this file:

```markdown
# InSAR Benchmark Lab

Reproducible research tools and notebooks for validating open InSAR deformation products.

The first research theme is groundwater-related land subsidence. The repository focuses on a practical question that matters for scientific and operational InSAR work:

> When should an open InSAR deformation product be trusted for a specific ground-deformation problem?

This project does not replace mature processors such as MintPy, MiaplPy, ISCE3, PyGMTSAR, OPERA, ARIA, or HyP3. It sits above them as a benchmark and validation layer: ingest outputs, compare workflows, quantify uncertainty, validate against independent geodetic observations, and communicate results through reproducible notebooks.

## Research Direction

The initial flagship case study is land subsidence in California's Central Valley. This is a strong first target because it has clear deformation signals, public relevance, Sentinel-1 coverage, prior literature, and GNSS stations that can support validation.

Later modules will extend the same framework to volcano deformation and landslide monitoring.

## Planned Notebook Track

| Notebook | Purpose |
| --- | --- |
| `01_project_orientation.ipynb` | Study area, scientific question, data sources, workflow map. |
| `02_hyp3_or_opera_to_timeseries.ipynb` | Organize open InSAR products into analysis-ready structures. |
| `03_mintpy_timeseries_validation.ipynb` | Compare InSAR displacement time series against GNSS. |
| `04_uncertainty_and_reference_sensitivity.ipynb` | Test reference-point, coherence, and masking sensitivity. |
| `05_deformation_story_map.ipynb` | Produce final maps, time-series plots, residuals, and interpretation figures. |

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
```

- [ ] **Step 5: Commit metadata**

Run:

```bash
git add .gitignore LICENSE pyproject.toml README.md
git commit -m "chore: add project metadata and README"
```

Expected: commit succeeds.

## Task 2: Validation Metrics Package

**Files:**
- Create: `src/insar_benchmark_lab/__init__.py`
- Create: `src/insar_benchmark_lab/metrics.py`
- Create: `tests/test_metrics.py`

- [ ] **Step 1: Write failing metric tests**

Create `tests/test_metrics.py`:

```python
import math

import numpy as np
import pytest

from insar_benchmark_lab.metrics import (
    correlation,
    mae,
    rmse,
    trend_bias,
    uncertainty_coverage,
    velocity_difference,
)


def test_rmse_ignores_nan_pairs():
    observed = np.array([1.0, 2.0, np.nan, 4.0])
    predicted = np.array([1.0, 4.0, 3.0, 1.0])

    assert rmse(observed, predicted) == pytest.approx(math.sqrt(13.0 / 3.0))


def test_mae_ignores_nan_pairs():
    observed = np.array([1.0, 2.0, np.nan, 4.0])
    predicted = np.array([2.0, 1.0, 3.0, 0.0])

    assert mae(observed, predicted) == pytest.approx(2.0)


def test_correlation_requires_two_valid_pairs():
    assert correlation([1.0, np.nan], [2.0, 3.0]) is None


def test_correlation_returns_pearson_value():
    assert correlation([1.0, 2.0, 3.0], [2.0, 4.0, 6.0]) == pytest.approx(1.0)


def test_velocity_difference_uses_first_and_last_valid_samples():
    dates = ["2020-01-01", "2021-01-01", "2022-01-01"]
    insar_mm = [0.0, 10.0, 20.0]
    gnss_mm = [0.0, 8.0, 16.0]

    assert velocity_difference(dates, insar_mm, gnss_mm) == pytest.approx(2.0)


def test_trend_bias_is_mean_residual():
    assert trend_bias([10.0, 20.0, 30.0], [8.0, 22.0, 25.0]) == pytest.approx(5.0 / 3.0)


def test_uncertainty_coverage_counts_residuals_inside_interval():
    observed = [0.0, 10.0, 20.0, 30.0]
    predicted = [1.0, 9.0, 25.0, 20.0]
    sigma = [2.0, 2.0, 2.0, 5.0]

    assert uncertainty_coverage(observed, predicted, sigma, sigma_multiplier=1.0) == pytest.approx(0.5)


def test_metrics_raise_for_no_valid_pairs():
    with pytest.raises(ValueError, match="at least one valid pair"):
        rmse([np.nan], [1.0])
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
pytest tests/test_metrics.py -q
```

Expected: FAIL because `insar_benchmark_lab.metrics` does not exist yet.

- [ ] **Step 3: Implement package exports**

Create `src/insar_benchmark_lab/__init__.py`:

```python
"""Utilities for reproducible InSAR benchmarking and validation."""

from insar_benchmark_lab.metrics import (
    correlation,
    mae,
    rmse,
    trend_bias,
    uncertainty_coverage,
    velocity_difference,
)

__all__ = [
    "correlation",
    "mae",
    "rmse",
    "trend_bias",
    "uncertainty_coverage",
    "velocity_difference",
]
```

- [ ] **Step 4: Implement metric functions**

Create `src/insar_benchmark_lab/metrics.py`:

```python
from __future__ import annotations

from datetime import date
from typing import Iterable

import numpy as np


ArrayLike = Iterable[float] | np.ndarray


def _valid_pairs(observed: ArrayLike, predicted: ArrayLike) -> tuple[np.ndarray, np.ndarray]:
    obs = np.asarray(list(observed), dtype=float)
    pred = np.asarray(list(predicted), dtype=float)
    if obs.shape != pred.shape:
        raise ValueError("observed and predicted must have the same shape")

    mask = np.isfinite(obs) & np.isfinite(pred)
    if not np.any(mask):
        raise ValueError("metrics require at least one valid pair")
    return obs[mask], pred[mask]


def rmse(observed: ArrayLike, predicted: ArrayLike) -> float:
    """Return root-mean-square error after dropping NaN pairs."""
    obs, pred = _valid_pairs(observed, predicted)
    return float(np.sqrt(np.mean((pred - obs) ** 2)))


def mae(observed: ArrayLike, predicted: ArrayLike) -> float:
    """Return mean absolute error after dropping NaN pairs."""
    obs, pred = _valid_pairs(observed, predicted)
    return float(np.mean(np.abs(pred - obs)))


def correlation(observed: ArrayLike, predicted: ArrayLike) -> float | None:
    """Return Pearson correlation, or None when fewer than two valid pairs exist."""
    obs, pred = _valid_pairs(observed, predicted)
    if obs.size < 2:
        return None
    return float(np.corrcoef(obs, pred)[0, 1])


def trend_bias(observed: ArrayLike, predicted: ArrayLike) -> float:
    """Return mean predicted-minus-observed residual."""
    obs, pred = _valid_pairs(observed, predicted)
    return float(np.mean(pred - obs))


def uncertainty_coverage(
    observed: ArrayLike,
    predicted: ArrayLike,
    sigma: ArrayLike,
    *,
    sigma_multiplier: float = 1.0,
) -> float:
    """Return the fraction of residuals within sigma_multiplier times sigma."""
    obs = np.asarray(list(observed), dtype=float)
    pred = np.asarray(list(predicted), dtype=float)
    sig = np.asarray(list(sigma), dtype=float)
    if obs.shape != pred.shape or obs.shape != sig.shape:
        raise ValueError("observed, predicted, and sigma must have the same shape")
    if sigma_multiplier <= 0:
        raise ValueError("sigma_multiplier must be positive")

    mask = np.isfinite(obs) & np.isfinite(pred) & np.isfinite(sig) & (sig > 0)
    if not np.any(mask):
        raise ValueError("uncertainty coverage requires at least one valid pair")

    residual = np.abs(pred[mask] - obs[mask])
    limit = sigma_multiplier * sig[mask]
    return float(np.mean(residual <= limit))


def velocity_difference(dates: Iterable[str], insar_mm: ArrayLike, gnss_mm: ArrayLike) -> float:
    """Return InSAR-minus-GNSS endpoint velocity difference in mm/year."""
    parsed_dates = np.asarray([date.fromisoformat(value) for value in dates])
    insar = np.asarray(list(insar_mm), dtype=float)
    gnss = np.asarray(list(gnss_mm), dtype=float)
    if parsed_dates.shape != insar.shape or parsed_dates.shape != gnss.shape:
        raise ValueError("dates, insar_mm, and gnss_mm must have the same length")

    mask = np.isfinite(insar) & np.isfinite(gnss)
    if np.count_nonzero(mask) < 2:
        raise ValueError("velocity difference requires at least two valid samples")

    valid_dates = parsed_dates[mask]
    valid_insar = insar[mask]
    valid_gnss = gnss[mask]
    order = np.argsort(valid_dates)
    valid_dates = valid_dates[order]
    valid_insar = valid_insar[order]
    valid_gnss = valid_gnss[order]

    elapsed_days = (valid_dates[-1] - valid_dates[0]).days
    if elapsed_days <= 0:
        raise ValueError("velocity difference requires dates spanning more than zero days")

    years = elapsed_days / 365.25
    insar_velocity = (valid_insar[-1] - valid_insar[0]) / years
    gnss_velocity = (valid_gnss[-1] - valid_gnss[0]) / years
    return float(insar_velocity - gnss_velocity)
```

- [ ] **Step 5: Run metric tests**

Run:

```bash
pytest tests/test_metrics.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit metrics**

Run:

```bash
git add src/insar_benchmark_lab/__init__.py src/insar_benchmark_lab/metrics.py tests/test_metrics.py
git commit -m "feat: add validation metrics"
```

Expected: commit succeeds.

## Task 3: Study-Area Configuration Loader

**Files:**
- Create: `src/insar_benchmark_lab/config.py`
- Create: `tests/test_config.py`
- Create: `configs/central_valley_subsidence.yml`

- [ ] **Step 1: Write failing config tests**

Create `tests/test_config.py`:

```python
from pathlib import Path

import pytest

from insar_benchmark_lab.config import StudyAreaConfig, load_study_area_config


def test_load_study_area_config(tmp_path):
    config_path = tmp_path / "study.yml"
    config_path.write_text(
        """
name: Central Valley Subsidence
slug: central-valley-subsidence
application: subsidence
region:
  west: -121.0
  south: 35.0
  east: -119.0
  north: 37.0
time_window:
  start: "2018-01-01"
  end: "2023-12-31"
reference:
  method: stable-area
  notes: Use a documented low-deformation area outside the main bowl.
data_sources:
  insar:
    - OPERA DISP-S1
    - ASF HyP3
  gnss:
    - Nevada Geodetic Laboratory
""",
        encoding="utf-8",
    )

    config = load_study_area_config(config_path)

    assert isinstance(config, StudyAreaConfig)
    assert config.slug == "central-valley-subsidence"
    assert config.region["west"] == pytest.approx(-121.0)
    assert config.time_window["start"] == "2018-01-01"
    assert "OPERA DISP-S1" in config.data_sources["insar"]


def test_config_rejects_missing_required_field(tmp_path):
    config_path = tmp_path / "bad.yml"
    config_path.write_text("name: Missing Slug\n", encoding="utf-8")

    with pytest.raises(ValueError, match="missing required field: slug"):
        load_study_area_config(config_path)


def test_config_rejects_invalid_bbox_order(tmp_path):
    config_path = tmp_path / "bad_bbox.yml"
    config_path.write_text(
        """
name: Bad Box
slug: bad-box
application: subsidence
region:
  west: -119.0
  south: 35.0
  east: -121.0
  north: 37.0
time_window:
  start: "2018-01-01"
  end: "2023-12-31"
reference:
  method: stable-area
  notes: invalid
data_sources:
  insar: []
  gnss: []
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="region west must be less than east"):
        load_study_area_config(config_path)


def test_config_rejects_missing_file():
    with pytest.raises(FileNotFoundError):
        load_study_area_config(Path("does-not-exist.yml"))
```

- [ ] **Step 2: Run config tests to verify failure**

Run:

```bash
pytest tests/test_config.py -q
```

Expected: FAIL because `insar_benchmark_lab.config` does not exist yet.

- [ ] **Step 3: Implement config loader**

Create `src/insar_benchmark_lab/config.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


REQUIRED_FIELDS = (
    "name",
    "slug",
    "application",
    "region",
    "time_window",
    "reference",
    "data_sources",
)


@dataclass(frozen=True)
class StudyAreaConfig:
    name: str
    slug: str
    application: str
    region: dict[str, float]
    time_window: dict[str, str]
    reference: dict[str, str]
    data_sources: dict[str, list[str]]


def load_study_area_config(path: str | Path) -> StudyAreaConfig:
    """Load and validate a study-area YAML configuration."""
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(config_path)

    with config_path.open("r", encoding="utf-8") as stream:
        raw = yaml.safe_load(stream) or {}

    if not isinstance(raw, dict):
        raise ValueError("study-area config must be a YAML mapping")

    for field in REQUIRED_FIELDS:
        if field not in raw:
            raise ValueError(f"missing required field: {field}")

    region = _validate_region(raw["region"])
    time_window = _validate_string_mapping(raw["time_window"], "time_window", ("start", "end"))
    reference = _validate_string_mapping(raw["reference"], "reference", ("method", "notes"))
    data_sources = _validate_data_sources(raw["data_sources"])

    return StudyAreaConfig(
        name=str(raw["name"]),
        slug=str(raw["slug"]),
        application=str(raw["application"]),
        region=region,
        time_window=time_window,
        reference=reference,
        data_sources=data_sources,
    )


def _validate_region(value: Any) -> dict[str, float]:
    if not isinstance(value, dict):
        raise ValueError("region must be a mapping")
    required = ("west", "south", "east", "north")
    for key in required:
        if key not in value:
            raise ValueError(f"region missing required field: {key}")
    region = {key: float(value[key]) for key in required}
    if region["west"] >= region["east"]:
        raise ValueError("region west must be less than east")
    if region["south"] >= region["north"]:
        raise ValueError("region south must be less than north")
    return region


def _validate_string_mapping(value: Any, field_name: str, required: tuple[str, ...]) -> dict[str, str]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a mapping")
    for key in required:
        if key not in value:
            raise ValueError(f"{field_name} missing required field: {key}")
    return {key: str(value[key]) for key in value}


def _validate_data_sources(value: Any) -> dict[str, list[str]]:
    if not isinstance(value, dict):
        raise ValueError("data_sources must be a mapping")
    sources: dict[str, list[str]] = {}
    for key, entries in value.items():
        if not isinstance(entries, list):
            raise ValueError(f"data_sources.{key} must be a list")
        sources[str(key)] = [str(entry) for entry in entries]
    return sources
```

- [ ] **Step 4: Export config API**

Modify `src/insar_benchmark_lab/__init__.py` so it contains:

```python
"""Utilities for reproducible InSAR benchmarking and validation."""

from insar_benchmark_lab.config import StudyAreaConfig, load_study_area_config
from insar_benchmark_lab.metrics import (
    correlation,
    mae,
    rmse,
    trend_bias,
    uncertainty_coverage,
    velocity_difference,
)

__all__ = [
    "StudyAreaConfig",
    "correlation",
    "load_study_area_config",
    "mae",
    "rmse",
    "trend_bias",
    "uncertainty_coverage",
    "velocity_difference",
]
```

- [ ] **Step 5: Add Central Valley config**

Create `configs/central_valley_subsidence.yml`:

```yaml
name: Central Valley Subsidence
slug: central-valley-subsidence
application: subsidence
region:
  west: -121.0
  south: 35.0
  east: -119.0
  north: 37.0
time_window:
  start: "2018-01-01"
  end: "2023-12-31"
reference:
  method: stable-area
  notes: Select a documented low-deformation area outside the main subsidence bowl before final analysis.
data_sources:
  insar:
    - OPERA DISP-S1
    - ASF HyP3
    - MintPy-compatible time-series products
  gnss:
    - Nevada Geodetic Laboratory
    - UNAVCO/EarthScope GNSS station products
```

- [ ] **Step 6: Run config tests**

Run:

```bash
pytest tests/test_config.py -q
```

Expected: PASS.

- [ ] **Step 7: Run full tests**

Run:

```bash
pytest
```

Expected: all tests PASS.

- [ ] **Step 8: Commit config loader**

Run:

```bash
git add src/insar_benchmark_lab/__init__.py src/insar_benchmark_lab/config.py tests/test_config.py configs/central_valley_subsidence.yml
git commit -m "feat: add study area config loader"
```

Expected: commit succeeds.

## Task 4: Time-Series Loader And Date Alignment

**Files:**
- Create: `src/insar_benchmark_lab/timeseries.py`
- Create: `tests/test_timeseries.py`
- Modify: `src/insar_benchmark_lab/__init__.py`

- [ ] **Step 1: Write failing time-series tests**

Create `tests/test_timeseries.py`:

```python
from datetime import date

import numpy as np
import pytest

from insar_benchmark_lab.timeseries import align_by_date, load_csv_timeseries


def test_load_csv_timeseries_reads_required_columns(tmp_path):
    csv_path = tmp_path / "station.csv"
    csv_path.write_text(
        "date,displacement_mm,sigma_mm\n"
        "2020-01-01,0.0,1.5\n"
        "2020-01-13,2.0,1.8\n",
        encoding="utf-8",
    )

    series = load_csv_timeseries(csv_path, uncertainty_column="sigma_mm", station_id="P123")

    assert series.station_id == "P123"
    assert series.dates == (date(2020, 1, 1), date(2020, 1, 13))
    assert np.allclose(series.displacement_mm, [0.0, 2.0])
    assert np.allclose(series.sigma_mm, [1.5, 1.8])


def test_load_csv_timeseries_rejects_missing_column(tmp_path):
    csv_path = tmp_path / "station.csv"
    csv_path.write_text("date,value\n2020-01-01,1.0\n", encoding="utf-8")

    with pytest.raises(ValueError, match="missing required column: displacement_mm"):
        load_csv_timeseries(csv_path)


def test_align_by_date_returns_common_dates_in_order():
    left_dates = [date(2020, 1, 1), date(2020, 1, 13), date(2020, 1, 25)]
    right_dates = [date(2020, 1, 13), date(2020, 1, 25), date(2020, 2, 6)]

    common_dates, left_values, right_values = align_by_date(
        left_dates,
        [0.0, 2.0, 4.0],
        right_dates,
        [10.0, 20.0, 30.0],
    )

    assert common_dates == (date(2020, 1, 13), date(2020, 1, 25))
    assert np.allclose(left_values, [2.0, 4.0])
    assert np.allclose(right_values, [10.0, 20.0])


def test_align_by_date_rejects_no_overlap():
    with pytest.raises(ValueError, match="no overlapping dates"):
        align_by_date(
            [date(2020, 1, 1)],
            [1.0],
            [date(2021, 1, 1)],
            [2.0],
        )
```

- [ ] **Step 2: Run time-series tests to verify failure**

Run:

```bash
pytest tests/test_timeseries.py -q
```

Expected: FAIL because `insar_benchmark_lab.timeseries` does not exist yet.

- [ ] **Step 3: Implement time-series utilities**

Create `src/insar_benchmark_lab/timeseries.py`:

```python
from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable

import numpy as np


@dataclass(frozen=True)
class DisplacementTimeSeries:
    station_id: str | None
    dates: tuple[date, ...]
    displacement_mm: np.ndarray
    sigma_mm: np.ndarray | None = None

    def __post_init__(self) -> None:
        if len(self.dates) != len(self.displacement_mm):
            raise ValueError("dates and displacement_mm must have the same length")
        if self.sigma_mm is not None and len(self.dates) != len(self.sigma_mm):
            raise ValueError("dates and sigma_mm must have the same length")


def load_csv_timeseries(
    path: str | Path,
    *,
    date_column: str = "date",
    displacement_column: str = "displacement_mm",
    uncertainty_column: str | None = None,
    station_id: str | None = None,
) -> DisplacementTimeSeries:
    """Load a simple displacement time series from a CSV file."""
    csv_path = Path(path)
    if not csv_path.exists():
        raise FileNotFoundError(csv_path)

    with csv_path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        fieldnames = set(reader.fieldnames or [])
        _require_column(fieldnames, date_column)
        _require_column(fieldnames, displacement_column)
        if uncertainty_column is not None:
            _require_column(fieldnames, uncertainty_column)

        dates: list[date] = []
        displacement: list[float] = []
        sigma: list[float] = []
        for row in reader:
            dates.append(date.fromisoformat(row[date_column]))
            displacement.append(float(row[displacement_column]))
            if uncertainty_column is not None:
                sigma.append(float(row[uncertainty_column]))

    sigma_array = np.asarray(sigma, dtype=float) if uncertainty_column is not None else None
    return DisplacementTimeSeries(
        station_id=station_id,
        dates=tuple(dates),
        displacement_mm=np.asarray(displacement, dtype=float),
        sigma_mm=sigma_array,
    )


def align_by_date(
    left_dates: Iterable[date],
    left_values: Iterable[float],
    right_dates: Iterable[date],
    right_values: Iterable[float],
) -> tuple[tuple[date, ...], np.ndarray, np.ndarray]:
    """Align two value series by exact common dates."""
    left_date_tuple = tuple(left_dates)
    right_date_tuple = tuple(right_dates)
    left_array = np.asarray(list(left_values), dtype=float)
    right_array = np.asarray(list(right_values), dtype=float)
    if len(left_date_tuple) != len(left_array):
        raise ValueError("left_dates and left_values must have the same length")
    if len(right_date_tuple) != len(right_array):
        raise ValueError("right_dates and right_values must have the same length")

    left_lookup = dict(zip(left_date_tuple, left_array, strict=True))
    right_lookup = dict(zip(right_date_tuple, right_array, strict=True))
    common = tuple(sorted(set(left_lookup) & set(right_lookup)))
    if not common:
        raise ValueError("no overlapping dates")

    return (
        common,
        np.asarray([left_lookup[item] for item in common], dtype=float),
        np.asarray([right_lookup[item] for item in common], dtype=float),
    )


def _require_column(fieldnames: set[str], column: str) -> None:
    if column not in fieldnames:
        raise ValueError(f"missing required column: {column}")
```

- [ ] **Step 4: Export time-series API**

Modify `src/insar_benchmark_lab/__init__.py` so it contains:

```python
"""Utilities for reproducible InSAR benchmarking and validation."""

from insar_benchmark_lab.config import StudyAreaConfig, load_study_area_config
from insar_benchmark_lab.metrics import (
    correlation,
    mae,
    rmse,
    trend_bias,
    uncertainty_coverage,
    velocity_difference,
)
from insar_benchmark_lab.timeseries import DisplacementTimeSeries, align_by_date, load_csv_timeseries

__all__ = [
    "DisplacementTimeSeries",
    "StudyAreaConfig",
    "align_by_date",
    "correlation",
    "load_csv_timeseries",
    "load_study_area_config",
    "mae",
    "rmse",
    "trend_bias",
    "uncertainty_coverage",
    "velocity_difference",
]
```

- [ ] **Step 5: Run time-series tests**

Run:

```bash
pytest tests/test_timeseries.py -q
```

Expected: PASS.

- [ ] **Step 6: Run full tests**

Run:

```bash
pytest
```

Expected: all tests PASS.

- [ ] **Step 7: Commit time-series utilities**

Run:

```bash
git add src/insar_benchmark_lab/__init__.py src/insar_benchmark_lab/timeseries.py tests/test_timeseries.py
git commit -m "feat: add time series loading utilities"
```

Expected: commit succeeds.

## Task 5: Data Policy, Roadmap, And Notebook Stubs

**Files:**
- Create: `data/README.md`
- Create: `docs/research-roadmap.md`
- Create: `notebooks/README.md`
- Create: `notebooks/01_project_orientation.ipynb`
- Create: `notebooks/02_hyp3_or_opera_to_timeseries.ipynb`
- Create: `notebooks/03_mintpy_timeseries_validation.ipynb`
- Create: `notebooks/04_uncertainty_and_reference_sensitivity.ipynb`
- Create: `notebooks/05_deformation_story_map.ipynb`

- [ ] **Step 1: Create data policy**

Create `data/README.md`:

```markdown
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
```

- [ ] **Step 2: Create research roadmap**

Create `docs/research-roadmap.md`:

```markdown
# Research Roadmap

## Phase 1: Subsidence Validation Foundation

Scientific question: how reliably do open InSAR products measure groundwater-related land subsidence in California's Central Valley?

Deliverables:

- Study-area configuration for the Central Valley.
- Validation metrics for InSAR-vs-GNSS time series.
- Notebook sequence for product organization, validation, uncertainty checks, and final figures.
- Clear documentation of data provenance and reference-frame assumptions.

## Phase 2: Workflow Comparison

Scientific question: how do OPERA, HyP3/ARIA, MintPy-compatible, and phase-linking workflows differ in velocity, residuals, uncertainty, and spatial coverage?

Deliverables:

- Common product-loading interfaces.
- Benchmark tables for multiple workflows.
- Reference-point sensitivity analysis.
- Coherence and masking sensitivity analysis.

## Phase 3: Volcano Extension

Scientific question: can the same validation framework characterize nonlinear volcanic deformation and event-like signals?

Deliverables:

- Volcano study-area config.
- Event-window time-series diagnostics.
- Phase-linking comparison on decorrelating surfaces.

## Phase 4: Landslide Extension

Scientific question: can the same framework support localized slope-deformation monitoring under coherence loss?

Deliverables:

- Landslide study-area config.
- Local time-series extraction utilities.
- Masking and coherence-loss diagnostics.
- Alert-style summary plots.
```

- [ ] **Step 3: Create notebook README**

Create `notebooks/README.md`:

```markdown
# Notebooks

The notebook track is designed to be readable as a research narrative and runnable as the codebase matures.

| Notebook | Status | Purpose |
| --- | --- | --- |
| `01_project_orientation.ipynb` | Stub | Study area, scientific question, data sources, workflow map. |
| `02_hyp3_or_opera_to_timeseries.ipynb` | Stub | Organize open InSAR products into analysis-ready structures. |
| `03_mintpy_timeseries_validation.ipynb` | Stub | Compare InSAR displacement time series against GNSS. |
| `04_uncertainty_and_reference_sensitivity.ipynb` | Stub | Test reference-point, coherence, and masking sensitivity. |
| `05_deformation_story_map.ipynb` | Stub | Produce maps, time-series plots, residuals, and interpretation figures. |

The stubs contain objectives and setup cells only. They should not contain fabricated outputs.
```

- [ ] **Step 4: Create notebook stubs**

For each notebook, create a valid minimal notebook JSON with matching title and objective. Use this template and change the title/objective for each file:

```json
{
  "cells": [
    {
      "cell_type": "markdown",
      "metadata": {},
      "source": [
        "# 01 Project Orientation\n",
        "\n",
        "Objective: define the Central Valley subsidence study area, scientific question, data sources, and workflow map.\n"
      ]
    },
    {
      "cell_type": "code",
      "execution_count": null,
      "metadata": {},
      "outputs": [],
      "source": [
        "from insar_benchmark_lab.config import load_study_area_config\n",
        "\n",
        "config = load_study_area_config('../configs/central_valley_subsidence.yml')\n",
        "config\n"
      ]
    }
  ],
  "metadata": {
    "kernelspec": {
      "display_name": "Python 3",
      "language": "python",
      "name": "python3"
    },
    "language_info": {
      "name": "python",
      "pygments_lexer": "ipython3"
    }
  },
  "nbformat": 4,
  "nbformat_minor": 5
}
```

Use these titles and objectives:

```text
01_project_orientation.ipynb
Title: 01 Project Orientation
Objective: define the Central Valley subsidence study area, scientific question, data sources, and workflow map.

02_hyp3_or_opera_to_timeseries.ipynb
Title: 02 HyP3 Or OPERA To Time Series
Objective: organize open InSAR products into an analysis-ready structure without committing large source files.

03_mintpy_timeseries_validation.ipynb
Title: 03 MintPy Time Series Validation
Objective: compare InSAR displacement time series against independent GNSS observations.

04_uncertainty_and_reference_sensitivity.ipynb
Title: 04 Uncertainty And Reference Sensitivity
Objective: quantify how reference point choice, masking, and uncertainty assumptions affect deformation estimates.

05_deformation_story_map.ipynb
Title: 05 Deformation Story Map
Objective: produce final maps, time-series panels, residual plots, and interpretation figures for the case study.
```

- [ ] **Step 5: Verify notebooks are valid JSON**

Run:

```bash
python -m json.tool notebooks/01_project_orientation.ipynb >/dev/null
python -m json.tool notebooks/02_hyp3_or_opera_to_timeseries.ipynb >/dev/null
python -m json.tool notebooks/03_mintpy_timeseries_validation.ipynb >/dev/null
python -m json.tool notebooks/04_uncertainty_and_reference_sensitivity.ipynb >/dev/null
python -m json.tool notebooks/05_deformation_story_map.ipynb >/dev/null
```

Expected: all commands exit with code 0.

- [ ] **Step 6: Commit docs and notebook stubs**

Run:

```bash
git add data/README.md docs/research-roadmap.md notebooks/README.md notebooks/*.ipynb
git commit -m "docs: add research roadmap and notebook track"
```

Expected: commit succeeds.

## Task 6: Final Verification

**Files:**
- Modify if needed: files created in Tasks 1-4

- [ ] **Step 1: Install package in editable mode**

Run:

```bash
python -m pip install -e ".[dev,notebooks]"
```

Expected: package installs successfully.

- [ ] **Step 2: Run full test suite**

Run:

```bash
pytest
```

Expected: all tests PASS.

- [ ] **Step 3: Validate config loads from repository path**

Run:

```bash
python -c "from insar_benchmark_lab.config import load_study_area_config; print(load_study_area_config('configs/central_valley_subsidence.yml').slug)"
```

Expected output:

```text
central-valley-subsidence
```

- [ ] **Step 4: Check repository status**

Run:

```bash
git status --short
```

Expected: no uncommitted changes.

If verification requires a small fix, make the smallest correction, rerun the relevant command, and commit it with:

```bash
git add README.md pyproject.toml src/insar_benchmark_lab tests configs data docs notebooks
git commit -m "fix: complete initial repository verification"
```
