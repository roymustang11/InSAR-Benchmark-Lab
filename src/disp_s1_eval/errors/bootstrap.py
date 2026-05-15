"""Bootstrap utilities for InSAR validation.

Two estimators are exposed:

- :func:`paired_bootstrap_mean` resamples station-level residuals with
  replacement and returns a percentile confidence interval on the mean.
- :func:`reference_point_bootstrap` repeats a velocity-or-displacement
  estimator under randomly drawn reference pixels and returns the
  per-pixel inter-quantile range, used as a reference-uncertainty map by
  the validation protocol.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

import numpy as np


@dataclass(frozen=True)
class BootstrapInterval:
    """Bootstrap point estimate with a percentile confidence interval."""

    estimate: float
    lower: float
    upper: float
    n_resamples: int
    confidence: float


def paired_bootstrap_mean(
    residuals: Sequence[float] | np.ndarray,
    *,
    n_resamples: int = 5000,
    confidence: float = 0.95,
    seed: int | None = None,
) -> BootstrapInterval:
    """Return a percentile bootstrap CI for the mean of ``residuals``.

    NaN entries are dropped before resampling. Confidence is two-sided.
    """
    arr = np.asarray(residuals, dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size < 2:
        raise ValueError("paired_bootstrap_mean requires at least 2 finite samples")
    if not (0.0 < confidence < 1.0):
        raise ValueError("confidence must lie in (0, 1)")

    rng = np.random.default_rng(seed)
    indices = rng.integers(0, arr.size, size=(int(n_resamples), arr.size))
    resampled_means = arr[indices].mean(axis=1)

    alpha = (1.0 - confidence) / 2.0
    lower, upper = np.quantile(resampled_means, [alpha, 1.0 - alpha])

    return BootstrapInterval(
        estimate=float(np.mean(arr)),
        lower=float(lower),
        upper=float(upper),
        n_resamples=int(n_resamples),
        confidence=float(confidence),
    )


def reference_point_bootstrap(
    displacement: np.ndarray,
    candidate_indices: np.ndarray,
    *,
    estimator: Callable[[np.ndarray], np.ndarray] | None = None,
    n_draws: int = 200,
    quantile_low: float = 0.025,
    quantile_high: float = 0.975,
    seed: int | None = None,
) -> dict[str, np.ndarray]:
    """Re-estimate a per-pixel field under randomly drawn reference pixels.

    Parameters:
        displacement:       Array of shape ``(T, Y, X)`` (or ``(Y, X)``) of
                            measurements that are reference-pixel relative.
        candidate_indices:  Array of shape ``(M, 2)`` with ``(y_idx, x_idx)``
                            of admissible reference pixels.
        estimator:          Optional callable applied to the rereferenced
                            displacement to produce the field of interest
                            (e.g. a velocity map). When ``None``, the
                            displacement at the last time step is used.
        n_draws:            Number of reference draws.
        quantile_low,
        quantile_high:      Percentile-interval bounds reported per pixel.
        seed:               Random seed for reproducibility.

    Returns:
        Mapping with keys ``"central"``, ``"lower"``, ``"upper"``, and
        ``"width"``, each a 2-D array of shape ``(Y, X)``.
    """
    if displacement.ndim not in (2, 3):
        raise ValueError("displacement must be 2-D (Y, X) or 3-D (T, Y, X)")
    if candidate_indices.ndim != 2 or candidate_indices.shape[1] != 2:
        raise ValueError("candidate_indices must have shape (M, 2)")
    if candidate_indices.shape[0] == 0:
        raise ValueError("candidate_indices must not be empty")
    if not (0.0 <= quantile_low < quantile_high <= 1.0):
        raise ValueError("quantile bounds must satisfy 0 <= low < high <= 1")

    rng = np.random.default_rng(seed)
    draws = rng.integers(0, candidate_indices.shape[0], size=int(n_draws))

    realisations: list[np.ndarray] = []
    for j in draws:
        y_idx, x_idx = candidate_indices[j]
        if displacement.ndim == 2:
            rereferenced = displacement - displacement[y_idx, x_idx]
            field = estimator(rereferenced) if estimator is not None else rereferenced
        else:
            ref_series = displacement[:, y_idx, x_idx]
            rereferenced = displacement - ref_series[:, None, None]
            field = estimator(rereferenced) if estimator is not None else rereferenced[-1]
        realisations.append(np.asarray(field, dtype=float))

    stacked = np.stack(realisations, axis=0)
    central = np.median(stacked, axis=0)
    lower = np.quantile(stacked, quantile_low, axis=0)
    upper = np.quantile(stacked, quantile_high, axis=0)

    return {
        "central": central,
        "lower": lower,
        "upper": upper,
        "width": upper - lower,
    }
