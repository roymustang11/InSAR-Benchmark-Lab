"""Reproducible evaluation framework for the OPERA DISP-S1 displacement product.

The package exposes:

- ``processors``  uniform reader protocol and per-processor adapters.
- ``gnss``        GNSS ingestion and ENU-to-LOS projection with covariance.
- ``errors``      empirical variogram, triple collocation, reference-point bootstrap.
- ``metrics``     pointwise validation metrics.
- ``config``      validated study-area configuration loader.
- ``opera``       OPERA DISP-S1 filename and Zarr-reference parsing.
- ``timeseries``  displacement time-series container and helpers.
"""

from disp_s1_eval.config import StudyAreaConfig, load_study_area_config
from disp_s1_eval.metrics import (
    correlation,
    mae,
    rmse,
    trend_bias,
    uncertainty_coverage,
    velocity_difference,
)
from disp_s1_eval.opera import (
    OPERA_DISP_S1_SHORT_NAME,
    OperaDispS1Product,
    classify_opera_link,
    extract_zarr_reference_variables,
    granule_to_inventory_record,
    links_by_kind,
    parse_opera_disp_s1_filename,
)
from disp_s1_eval.timeseries import (
    DisplacementTimeSeries,
    align_by_date,
    load_csv_timeseries,
)

__version__ = "0.2.0"

__all__ = [
    "DisplacementTimeSeries",
    "OPERA_DISP_S1_SHORT_NAME",
    "OperaDispS1Product",
    "StudyAreaConfig",
    "align_by_date",
    "classify_opera_link",
    "correlation",
    "extract_zarr_reference_variables",
    "granule_to_inventory_record",
    "links_by_kind",
    "load_csv_timeseries",
    "load_study_area_config",
    "mae",
    "parse_opera_disp_s1_filename",
    "rmse",
    "trend_bias",
    "uncertainty_coverage",
    "velocity_difference",
    "__version__",
]
