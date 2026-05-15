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
