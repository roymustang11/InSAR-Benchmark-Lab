"""Backward-compatibility alias for the historical ``insar_benchmark_lab`` import path.

The library has been renamed to :mod:`disp_s1_eval`. This module re-exports the
public API so existing notebooks, tests, and downstream code continue to work.

New code should import from :mod:`disp_s1_eval` directly.
"""

from disp_s1_eval import (
    DisplacementTimeSeries,
    OPERA_DISP_S1_SHORT_NAME,
    OperaDispS1Product,
    StudyAreaConfig,
    align_by_date,
    classify_opera_link,
    correlation,
    extract_zarr_reference_variables,
    granule_to_inventory_record,
    links_by_kind,
    load_csv_timeseries,
    load_study_area_config,
    mae,
    parse_opera_disp_s1_filename,
    rmse,
    trend_bias,
    uncertainty_coverage,
    velocity_difference,
)

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
]
