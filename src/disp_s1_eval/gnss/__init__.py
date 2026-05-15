"""GNSS ingestion, projection, and temporal collocation for InSAR validation.

Three layers:

- :mod:`disp_s1_eval.gnss.ngl` reads NGL ``tenv3`` daily-position series
  with full ENU covariance.
- :mod:`disp_s1_eval.gnss.projection` projects ENU and its covariance into
  the per-pixel InSAR line of sight (``docs/methodology.md`` §2).
- :mod:`disp_s1_eval.gnss.collocation` implements the temporal collocation
  strategies of ``docs/validation-protocol.md`` §3.
"""

from disp_s1_eval.gnss.collocation import (
    CollocationStrategy,
    collocate_gaussian,
    collocate_nearest,
    collocate_weighted_window,
    resolve_collocation,
)
from disp_s1_eval.gnss.ngl import (
    GnssStation,
    GnssTimeSeries,
    NGL_TENV3_BASE_URL,
    download_ngl_station,
    parse_tenv3,
    read_tenv3_file,
)
from disp_s1_eval.gnss.projection import (
    project_enu_to_los,
    project_enu_covariance_to_los,
)

__all__ = [
    "CollocationStrategy",
    "GnssStation",
    "GnssTimeSeries",
    "NGL_TENV3_BASE_URL",
    "collocate_gaussian",
    "collocate_nearest",
    "collocate_weighted_window",
    "download_ngl_station",
    "parse_tenv3",
    "project_enu_covariance_to_los",
    "project_enu_to_los",
    "read_tenv3_file",
    "resolve_collocation",
]
