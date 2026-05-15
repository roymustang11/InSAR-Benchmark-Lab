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
    """Return mean observed-minus-predicted residual."""
    obs, pred = _valid_pairs(observed, predicted)
    return float(np.mean(obs - pred))


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

    years = _decimal_year(valid_dates[-1]) - _decimal_year(valid_dates[0])
    insar_velocity = (valid_insar[-1] - valid_insar[0]) / years
    gnss_velocity = (valid_gnss[-1] - valid_gnss[0]) / years
    return float(insar_velocity - gnss_velocity)


def _decimal_year(value: date) -> float:
    year_start = date(value.year, 1, 1)
    next_year_start = date(value.year + 1, 1, 1)
    year_length = (next_year_start - year_start).days
    return value.year + ((value - year_start).days / year_length)
