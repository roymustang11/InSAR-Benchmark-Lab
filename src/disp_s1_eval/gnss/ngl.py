"""Nevada Geodetic Laboratory ``tenv3`` ingestion.

The Nevada Geodetic Laboratory at the University of Nevada, Reno publishes
daily-position GNSS time series in a fixed-format ASCII layout commonly
referred to as ``tenv3``. Each row is one daily solution.

The columns used by this framework are:

==========  ============================================================
Column      Meaning
==========  ============================================================
site        4-character station identifier
YYMMMDD     Date code (e.g. ``20JAN01``)
yyyy.yyyy   Decimal year
MJD         Modified Julian day
week        GPS week
d           Day of week
reflon      Reference longitude (deg)
e0          Integer-meter east component (m)
east        East offset within tile (m)
n0          Integer-meter north component (m)
north       North offset within tile (m)
u0          Integer-meter up component (m)
up          Up offset within tile (m)
ant         Antenna offset (m)
sig_e       East 1-sigma (m)
sig_n       North 1-sigma (m)
sig_u       Up 1-sigma (m)
corr_en     East-north correlation
corr_eu     East-up correlation
corr_nu     North-up correlation
==========  ============================================================

Reference:
    Blewitt, G., Hammond, W. C., & Kreemer, C. (2018). Harnessing the GPS
    data explosion for interdisciplinary science. EOS, 99.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Iterable

import numpy as np


NGL_TENV3_BASE_URL = "https://geodesy.unr.edu/gps_timeseries/IGS20/tenv3"
NGL_DATAHOLDINGS_URL = "https://geodesy.unr.edu/NGLStationPages/DataHoldings.txt"


_MONTH_MAP = {
    "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
    "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12,
}


@dataclass(frozen=True)
class GnssStation:
    """Static metadata for a GNSS station."""

    station_id: str
    longitude: float
    latitude: float
    elevation_m: float | None = None


@dataclass(frozen=True)
class StationHolding:
    """NGL station availability metadata used for AOI filtering."""

    station_id: str
    latitude: float
    longitude: float
    start: date
    end: date
    n_epochs: int


@dataclass(frozen=True)
class GnssTimeSeries:
    """Daily ENU displacement time series for a single GNSS station.

    All fields are NumPy arrays of equal length ``N`` (one entry per daily
    solution). ENU components are reported in **millimeters** relative to the
    series mean; the original NGL meter-tile baseline is subtracted on read.
    The full ENU covariance per epoch is constructed from per-component
    sigmas and pairwise correlations.

    Attributes:
        station:    :class:`GnssStation` metadata.
        dates:      Tuple of ``date`` objects of length ``N``.
        east_mm, north_mm, up_mm:  Detrended ENU displacement, mm.
        sigma_e_mm, sigma_n_mm, sigma_u_mm:  Per-epoch 1-sigma, mm.
        corr_en, corr_eu, corr_nu: Per-epoch correlations, dimensionless.
        reference_frame: NGL solution frame name (e.g. ``"IGS14"``).
    """

    station: GnssStation
    dates: tuple[date, ...]
    east_mm: np.ndarray
    north_mm: np.ndarray
    up_mm: np.ndarray
    sigma_e_mm: np.ndarray
    sigma_n_mm: np.ndarray
    sigma_u_mm: np.ndarray
    corr_en: np.ndarray
    corr_eu: np.ndarray
    corr_nu: np.ndarray
    reference_frame: str = "IGS14"

    def __post_init__(self) -> None:
        N = len(self.dates)
        for name in (
            "east_mm", "north_mm", "up_mm",
            "sigma_e_mm", "sigma_n_mm", "sigma_u_mm",
            "corr_en", "corr_eu", "corr_nu",
        ):
            if getattr(self, name).shape != (N,):
                raise ValueError(f"{name} must have shape ({N},)")

    def covariance(self, index: int) -> np.ndarray:
        """Return the 3x3 ENU covariance matrix at epoch ``index`` (mm^2)."""
        se = float(self.sigma_e_mm[index])
        sn = float(self.sigma_n_mm[index])
        su = float(self.sigma_u_mm[index])
        ren = float(self.corr_en[index])
        reu = float(self.corr_eu[index])
        rnu = float(self.corr_nu[index])
        return np.array(
            [
                [se * se, ren * se * sn, reu * se * su],
                [ren * se * sn, sn * sn, rnu * sn * su],
                [reu * se * su, rnu * sn * su, su * su],
            ],
            dtype=float,
        )


def parse_tenv3(
    lines: Iterable[str],
    *,
    station_id: str | None = None,
    reference_frame: str = "IGS14",
    longitude: float | None = None,
    latitude: float | None = None,
) -> GnssTimeSeries:
    """Parse NGL tenv3-format text into a :class:`GnssTimeSeries`.

    The ``lines`` iterable yields raw strings (with or without trailing
    newlines). A header row, if present, is detected and skipped.
    """
    rows: list[list[str]] = []
    site_from_file: str | None = None
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#") or line.lower().startswith("site"):
            continue
        parts = line.split()
        if len(parts) < 14:
            continue
        rows.append(parts)
        if site_from_file is None:
            site_from_file = parts[0]

    if not rows:
        raise ValueError("no data rows found in tenv3 input")

    site = (station_id or site_from_file or "UNKN").upper()
    dates: list[date] = []
    east_m: list[float] = []
    north_m: list[float] = []
    up_m: list[float] = []
    sig_e_m: list[float] = []
    sig_n_m: list[float] = []
    sig_u_m: list[float] = []
    corr_en: list[float] = []
    corr_eu: list[float] = []
    corr_nu: list[float] = []

    for parts in rows:
        try:
            dates.append(_parse_yymmmdd(parts[1]))
            east_m.append(float(parts[7]) + float(parts[8]))
            north_m.append(float(parts[9]) + float(parts[10]))
            up_m.append(float(parts[11]) + float(parts[12]))
            sig_e_m.append(float(parts[14]))
            sig_n_m.append(float(parts[15]))
            sig_u_m.append(float(parts[16]))
            corr_en.append(float(parts[17]))
            corr_eu.append(float(parts[18]))
            corr_nu.append(float(parts[19]))
        except (IndexError, ValueError):
            continue

    if not dates:
        raise ValueError("tenv3 rows present but none were parseable")

    east_arr = np.asarray(east_m, dtype=float) * 1000.0
    north_arr = np.asarray(north_m, dtype=float) * 1000.0
    up_arr = np.asarray(up_m, dtype=float) * 1000.0
    east_arr -= float(np.mean(east_arr))
    north_arr -= float(np.mean(north_arr))
    up_arr -= float(np.mean(up_arr))

    station = GnssStation(
        station_id=site,
        longitude=float(longitude) if longitude is not None else float("nan"),
        latitude=float(latitude) if latitude is not None else float("nan"),
    )

    return GnssTimeSeries(
        station=station,
        dates=tuple(dates),
        east_mm=east_arr,
        north_mm=north_arr,
        up_mm=up_arr,
        sigma_e_mm=np.asarray(sig_e_m, dtype=float) * 1000.0,
        sigma_n_mm=np.asarray(sig_n_m, dtype=float) * 1000.0,
        sigma_u_mm=np.asarray(sig_u_m, dtype=float) * 1000.0,
        corr_en=np.asarray(corr_en, dtype=float),
        corr_eu=np.asarray(corr_eu, dtype=float),
        corr_nu=np.asarray(corr_nu, dtype=float),
        reference_frame=reference_frame,
    )


def read_tenv3_file(
    path: str | Path,
    *,
    station_id: str | None = None,
    reference_frame: str = "IGS14",
    longitude: float | None = None,
    latitude: float | None = None,
) -> GnssTimeSeries:
    """Read a tenv3 file from disk into a :class:`GnssTimeSeries`."""
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(file_path)
    with file_path.open("r", encoding="utf-8") as stream:
        return parse_tenv3(
            stream,
            station_id=station_id or file_path.stem.upper(),
            reference_frame=reference_frame,
            longitude=longitude,
            latitude=latitude,
        )


def download_ngl_station(
    station_id: str,
    destination: str | Path,
    *,
    reference_frame: str = "IGS14",
    timeout_seconds: float = 30.0,
) -> Path:
    """Download a station's tenv3 file from NGL and return its local path.

    The function only retrieves the file; parsing is performed by
    :func:`read_tenv3_file`. The destination directory is created if it
    does not exist.
    """
    try:
        import requests  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "download_ngl_station requires the requests package; "
            "install with `pip install -e .[io]`"
        ) from exc

    site = station_id.upper()
    url = ngl_tenv3_url(site, reference_frame=reference_frame)
    out_dir = Path(destination)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{site}.tenv3"
    response = requests.get(url, timeout=timeout_seconds)
    response.raise_for_status()
    out_path.write_bytes(response.content)
    return out_path


def ngl_tenv3_url(station_id: str, *, reference_frame: str = "IGS20") -> str:
    """Return the current NGL final-solution tenv3 URL for a station."""
    site = station_id.upper()
    frame = reference_frame.upper()
    if frame in {"IGS20", "IGS14"}:
        return f"{NGL_TENV3_BASE_URL}/IGS20/{site}.tenv3"
    return f"{NGL_TENV3_BASE_URL}/{frame}/{site}.{frame}.tenv3"


def download_station_holdings(
    destination: str | Path,
    *,
    url: str = NGL_DATAHOLDINGS_URL,
    fetcher: object | None = None,
) -> Path:
    """Download NGL DataHoldings.txt to ``destination``."""
    out_path = Path(destination)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if fetcher is None:
        try:
            import requests  # type: ignore[import-not-found]
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "download_station_holdings requires requests; "
                "install with `pip install -e .[io]`"
            ) from exc
        content = requests.get(url, timeout=60).content
    else:
        content = fetcher(url)  # type: ignore[operator]
    out_path.write_bytes(content)
    return out_path


def parse_station_holdings(lines: Iterable[str]) -> list[StationHolding]:
    """Parse a compact station-holdings table.

    Accepted formats:

    - Compact: ``station latitude longitude start end epochs``.
    - Native NGL DataHoldings: ``Sta Lat Long Hgt X Y Z Dtbeg Dtend Dtmod NumSol ...``.
    """
    holdings: list[StationHolding] = []
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#") or line.lower().startswith("station"):
            continue
        parts = line.split()
        if len(parts) < 6:
            continue
        try:
            station_id, latitude, longitude, start, end, n_epochs = _parse_holding_parts(parts)
            holdings.append(
                StationHolding(
                    station_id=station_id,
                    latitude=latitude,
                    longitude=longitude,
                    start=start,
                    end=end,
                    n_epochs=n_epochs,
                )
            )
        except ValueError:
            continue
    return holdings


def _parse_holding_parts(parts: list[str]) -> tuple[str, float, float, date, date, int]:
    station_id = parts[0].upper()
    latitude = float(parts[1])
    longitude = _normalize_longitude(float(parts[2]))

    if len(parts) >= 11:
        try:
            return (
                station_id,
                latitude,
                longitude,
                date.fromisoformat(parts[7]),
                date.fromisoformat(parts[8]),
                int(parts[10]),
            )
        except ValueError:
            pass

    return (
        station_id,
        latitude,
        longitude,
        date.fromisoformat(parts[3]),
        date.fromisoformat(parts[4]),
        int(parts[5]),
    )


def _normalize_longitude(value: float) -> float:
    return value - 360.0 if value > 180.0 else value


def select_stations_for_aoi(
    holdings: Iterable[StationHolding],
    bbox: object,
    *,
    start: date,
    end: date,
    min_epochs: int = 200,
) -> list[StationHolding]:
    """Filter station holdings by AOI, temporal coverage, and epoch count."""
    selected = []
    for station in holdings:
        inside = bool(bbox.contains(station.longitude, station.latitude))  # type: ignore[attr-defined]
        covers_window = station.start <= start and station.end >= end
        enough_epochs = station.n_epochs >= int(min_epochs)
        if inside and covers_window and enough_epochs:
            selected.append(station)
    return sorted(selected, key=lambda item: item.station_id)


def _parse_yymmmdd(token: str) -> date:
    if len(token) != 7:
        raise ValueError(f"unexpected NGL date token: {token!r}")
    year_two = int(token[:2])
    month_token = token[2:5].upper()
    day = int(token[5:7])
    if month_token not in _MONTH_MAP:
        raise ValueError(f"unknown month abbreviation in {token!r}")
    year = 2000 + year_two if year_two < 80 else 1900 + year_two
    return date(year, _MONTH_MAP[month_token], day)


def epochs_within(series: GnssTimeSeries, start: date, end: date) -> int:
    """Return the count of ``series`` epochs in ``[start, end]``."""
    return sum(1 for d in series.dates if start <= d <= end)


def days_between(a: date, b: date) -> int:
    """Return ``(b - a).days``, exposed as a helper for collocation modules."""
    return (b - a).days


def shift_dates(series: GnssTimeSeries, days: int) -> tuple[date, ...]:
    """Return the series dates shifted by ``days`` calendar days."""
    delta = timedelta(days=days)
    return tuple(d + delta for d in series.dates)
