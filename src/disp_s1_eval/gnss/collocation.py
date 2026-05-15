"""Temporal collocation strategies for GNSS-vs-InSAR comparison.

Three named strategies are implemented, matching
``docs/validation-protocol.md`` §3:

- :func:`collocate_nearest`            nearest-day rule with a hard window.
- :func:`collocate_weighted_window`    inverse-time-distance weighted mean.
- :func:`collocate_gaussian`           Gaussian temporal kernel.

Every strategy takes a list of GNSS daily epochs and a list of InSAR
target epochs and returns one collocated GNSS value per InSAR epoch, with
``np.nan`` where no admissible GNSS data are available.
"""

from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Callable, Iterable, Sequence

import numpy as np


class CollocationStrategy(str, Enum):
    """Enumeration of supported collocation strategies."""

    NEAREST = "nearest"
    WEIGHTED_WINDOW = "weighted_window"
    GAUSSIAN_SMOOTHING = "gaussian_smoothing"


def collocate_nearest(
    gnss_dates: Sequence[date],
    gnss_values: Sequence[float],
    insar_dates: Sequence[date],
    *,
    max_offset_days: int = 3,
) -> np.ndarray:
    """Return the GNSS value closest to each InSAR epoch within ``max_offset_days``.

    NaN is returned when no GNSS epoch is within the window.
    """
    g_dates = np.asarray(gnss_dates, dtype=object)
    g_values = np.asarray(gnss_values, dtype=float)
    if g_dates.shape != g_values.shape:
        raise ValueError("gnss_dates and gnss_values must have the same length")

    g_ordinals = np.array([d.toordinal() for d in g_dates], dtype=int)
    insar_ordinals = np.array([d.toordinal() for d in insar_dates], dtype=int)

    out = np.full(insar_ordinals.shape, np.nan, dtype=float)
    if g_ordinals.size == 0:
        return out

    for idx, target in enumerate(insar_ordinals):
        offsets = np.abs(g_ordinals - target)
        nearest = int(np.argmin(offsets))
        if int(offsets[nearest]) <= int(max_offset_days) and np.isfinite(g_values[nearest]):
            out[idx] = float(g_values[nearest])
    return out


def collocate_weighted_window(
    gnss_dates: Sequence[date],
    gnss_values: Sequence[float],
    insar_dates: Sequence[date],
    *,
    half_window_days: int = 7,
) -> np.ndarray:
    """Return inverse-time-distance weighted means inside ``±half_window_days``.

    Weights are ``1 / (1 + |Δt|)`` for every GNSS epoch within the window.
    NaN is returned when no admissible GNSS epoch lies inside the window.
    """
    g_ordinals = np.array([d.toordinal() for d in gnss_dates], dtype=int)
    g_values = np.asarray(gnss_values, dtype=float)
    insar_ordinals = np.array([d.toordinal() for d in insar_dates], dtype=int)

    out = np.full(insar_ordinals.shape, np.nan, dtype=float)
    for idx, target in enumerate(insar_ordinals):
        offsets = g_ordinals - target
        mask = (np.abs(offsets) <= int(half_window_days)) & np.isfinite(g_values)
        if not np.any(mask):
            continue
        weights = 1.0 / (1.0 + np.abs(offsets[mask]).astype(float))
        out[idx] = float(np.sum(weights * g_values[mask]) / np.sum(weights))
    return out


def collocate_gaussian(
    gnss_dates: Sequence[date],
    gnss_values: Sequence[float],
    insar_dates: Sequence[date],
    *,
    sigma_days: float = 10.0,
    truncation_sigmas: float = 3.0,
) -> np.ndarray:
    """Return Gaussian-kernel-smoothed GNSS values at the InSAR epochs.

    Contributions beyond ``truncation_sigmas`` standard deviations are
    discarded for efficiency. NaN is returned when no GNSS epoch lies
    within the truncation window.
    """
    if sigma_days <= 0:
        raise ValueError("sigma_days must be positive")
    g_ordinals = np.array([d.toordinal() for d in gnss_dates], dtype=int)
    g_values = np.asarray(gnss_values, dtype=float)
    insar_ordinals = np.array([d.toordinal() for d in insar_dates], dtype=int)

    cutoff = float(truncation_sigmas) * float(sigma_days)
    out = np.full(insar_ordinals.shape, np.nan, dtype=float)

    for idx, target in enumerate(insar_ordinals):
        offsets = (g_ordinals - target).astype(float)
        mask = (np.abs(offsets) <= cutoff) & np.isfinite(g_values)
        if not np.any(mask):
            continue
        weights = np.exp(-0.5 * (offsets[mask] / sigma_days) ** 2)
        out[idx] = float(np.sum(weights * g_values[mask]) / np.sum(weights))
    return out


def resolve_collocation(
    name: str | CollocationStrategy,
) -> Callable[..., np.ndarray]:
    """Return the collocation function for a named strategy."""
    strategy = CollocationStrategy(name) if not isinstance(name, CollocationStrategy) else name
    if strategy is CollocationStrategy.NEAREST:
        return collocate_nearest
    if strategy is CollocationStrategy.WEIGHTED_WINDOW:
        return collocate_weighted_window
    if strategy is CollocationStrategy.GAUSSIAN_SMOOTHING:
        return collocate_gaussian
    raise ValueError(f"unknown collocation strategy: {name}")  # pragma: no cover
