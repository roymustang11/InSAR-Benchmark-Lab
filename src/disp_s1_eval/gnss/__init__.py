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
    StationHolding,
    download_ngl_station,
    download_station_holdings,
    ngl_tenv3_url,
    parse_tenv3,
    parse_station_holdings,
    read_tenv3_file,
    select_stations_for_aoi,
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
    "StationHolding",
    "collocate_gaussian",
    "collocate_nearest",
    "collocate_weighted_window",
    "download_ngl_station",
    "download_station_holdings",
    "ngl_tenv3_url",
    "parse_tenv3",
    "parse_station_holdings",
    "project_enu_covariance_to_los",
    "project_enu_to_los",
    "read_tenv3_file",
    "resolve_collocation",
    "select_stations_for_aoi",
]
