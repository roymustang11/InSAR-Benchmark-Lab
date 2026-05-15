"""Triple collocation for unbiased per-product error variance.

Given three pairwise-independent measurements ``x``, ``y``, ``z`` of the
same underlying signal with additive zero-mean errors, the symmetric
triple-collocation estimator for the error variance of ``x`` is

.. math::

    \\sigma_x^2 = \\langle (x - y)(x - z) \\rangle.

We use the symmetric form valid when all three series share a common scale
(the framework rescales each product to a common stable-window mean before
applying the estimator). For a derivation and assumptions see McColl
et al. (2014, *GRL*).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class TripleCollocationResult:
    """Per-product error standard deviations (mm) and the sample size."""

    name_x: str
    name_y: str
    name_z: str
    sigma_x: float
    sigma_y: float
    sigma_z: float
    n_samples: int


def triple_collocation(
    x: np.ndarray,
    y: np.ndarray,
    z: np.ndarray,
    *,
    name_x: str = "X",
    name_y: str = "Y",
    name_z: str = "Z",
) -> TripleCollocationResult:
    """Estimate per-product error standard deviations from three series.

    Pairs containing any non-finite value are dropped. A negative covariance
    product (which would imply a negative variance under the assumptions of
    the estimator) is reported as ``nan`` rather than silently squared,
    flagging the assumption violation explicitly.
    """
    arr_x = np.asarray(x, dtype=float)
    arr_y = np.asarray(y, dtype=float)
    arr_z = np.asarray(z, dtype=float)
    if not (arr_x.shape == arr_y.shape == arr_z.shape):
        raise ValueError("x, y, and z must have the same shape")

    mask = np.isfinite(arr_x) & np.isfinite(arr_y) & np.isfinite(arr_z)
    if int(np.sum(mask)) < 3:
        raise ValueError("triple collocation requires at least 3 collocated samples")

    xv = arr_x[mask] - np.mean(arr_x[mask])
    yv = arr_y[mask] - np.mean(arr_y[mask])
    zv = arr_z[mask] - np.mean(arr_z[mask])

    var_x = float(np.mean((xv - yv) * (xv - zv)))
    var_y = float(np.mean((yv - xv) * (yv - zv)))
    var_z = float(np.mean((zv - xv) * (zv - yv)))

    return TripleCollocationResult(
        name_x=name_x,
        name_y=name_y,
        name_z=name_z,
        sigma_x=float(np.sqrt(var_x)) if var_x >= 0 else float("nan"),
        sigma_y=float(np.sqrt(var_y)) if var_y >= 0 else float("nan"),
        sigma_z=float(np.sqrt(var_z)) if var_z >= 0 else float("nan"),
        n_samples=int(np.sum(mask)),
    )
