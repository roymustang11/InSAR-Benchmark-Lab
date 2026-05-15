"""Empirical variogram and exponential-model fit for spatial residuals.

The empirical (semi)variogram at lag ``h`` is

.. math::

    \\hat{\\gamma}(h) = \\frac{1}{2 |N(h)|}
        \\sum_{(i,j) \\in N(h)} (z_i - z_j)^2,

where ``N(h)`` is the set of pairs with separation in a bin around ``h``
(Cressie 1993). The exponential model is

.. math::

    \\gamma(h) = c_0 + c \\, \\bigl(1 - e^{-h / a}\\bigr),

with nugget ``c_0``, partial sill ``c`` (so that ``c_0 + c`` is the sill),
and range ``a``. ``c_0`` is interpreted as the point error variance under
the Gaussian model.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class VariogramBin:
    """One distance bin of an empirical variogram."""

    distance: float
    semivariance: float
    n_pairs: int


@dataclass(frozen=True)
class ExponentialVariogram:
    """Fitted exponential variogram parameters."""

    nugget: float
    partial_sill: float
    range: float

    @property
    def sill(self) -> float:
        return self.nugget + self.partial_sill

    def evaluate(self, distance: float | np.ndarray) -> np.ndarray:
        """Return the model semivariance at the requested distances."""
        h = np.asarray(distance, dtype=float)
        return self.nugget + self.partial_sill * (1.0 - np.exp(-h / self.range))


def empirical_variogram(
    coordinates: np.ndarray,
    values: np.ndarray,
    *,
    n_bins: int = 15,
    max_distance: float | None = None,
) -> list[VariogramBin]:
    """Compute the binned empirical semivariogram.

    Parameters:
        coordinates:    Array of shape ``(N, 2)`` with planar coordinates
                        (e.g. metres in a local projection or degrees if
                        small-angle approximations suffice).
        values:         Array of shape ``(N,)`` of scalar residuals.
        n_bins:         Number of distance bins.
        max_distance:   Optional cap on the largest lag considered. Defaults
                        to half the maximum pairwise distance, which is the
                        usual rule of thumb (Cressie 1993).
    """
    coords = np.asarray(coordinates, dtype=float)
    vals = np.asarray(values, dtype=float)
    if coords.ndim != 2 or coords.shape[1] != 2:
        raise ValueError("coordinates must have shape (N, 2)")
    if vals.shape != (coords.shape[0],):
        raise ValueError("values must have shape (N,)")

    finite = np.isfinite(vals)
    coords = coords[finite]
    vals = vals[finite]
    n = coords.shape[0]
    if n < 2:
        raise ValueError("variogram requires at least two finite samples")

    diff = coords[:, None, :] - coords[None, :, :]
    distance = np.sqrt(np.sum(diff * diff, axis=-1))
    sq_diff = (vals[:, None] - vals[None, :]) ** 2
    iu = np.triu_indices(n, k=1)
    d = distance[iu]
    s = sq_diff[iu]

    if max_distance is None:
        max_distance = float(np.max(d) / 2.0) if d.size > 0 else 0.0
    if max_distance <= 0:
        raise ValueError("max_distance must be positive")

    edges = np.linspace(0.0, max_distance, int(n_bins) + 1)
    bins: list[VariogramBin] = []
    for lo, hi in zip(edges[:-1], edges[1:], strict=True):
        mask = (d >= lo) & (d < hi)
        count = int(np.sum(mask))
        if count == 0:
            continue
        bins.append(
            VariogramBin(
                distance=float(0.5 * (lo + hi)),
                semivariance=float(0.5 * np.mean(s[mask])),
                n_pairs=count,
            )
        )
    return bins


def fit_exponential_variogram(bins: list[VariogramBin]) -> ExponentialVariogram:
    """Fit an exponential model to a binned empirical variogram.

    The fit minimizes pair-count-weighted squared residuals using
    ``scipy.optimize.curve_fit`` when available, and otherwise falls back to
    a NumPy-only Gauss-Newton iteration. Initial guesses use the smallest
    bin as the nugget, the largest bin as the sill, and one third of the
    maximum lag as the range.
    """
    if len(bins) < 3:
        raise ValueError("fit_exponential_variogram requires at least 3 bins")

    h = np.array([b.distance for b in bins], dtype=float)
    g = np.array([b.semivariance for b in bins], dtype=float)
    w = np.array([b.n_pairs for b in bins], dtype=float)

    nugget0 = float(np.min(g))
    sill0 = float(np.max(g))
    range0 = float(np.max(h) / 3.0)
    p0 = np.array([nugget0, max(sill0 - nugget0, 1e-9), range0], dtype=float)

    try:
        from scipy.optimize import curve_fit  # type: ignore[import-not-found]

        def model(h_, c0, c, a):
            return c0 + c * (1.0 - np.exp(-h_ / a))

        popt, _ = curve_fit(
            model,
            h,
            g,
            p0=p0,
            sigma=1.0 / np.sqrt(w),
            absolute_sigma=False,
            bounds=([0.0, 0.0, 1e-9], [np.inf, np.inf, np.inf]),
            maxfev=5000,
        )
        c0, c, a = (float(v) for v in popt)
    except ImportError:
        c0, c, a = _gauss_newton(h, g, w, p0)

    return ExponentialVariogram(nugget=c0, partial_sill=c, range=a)


def _gauss_newton(
    h: np.ndarray,
    g: np.ndarray,
    w: np.ndarray,
    p0: np.ndarray,
    *,
    max_iter: int = 200,
    tolerance: float = 1e-10,
) -> tuple[float, float, float]:
    p = p0.astype(float).copy()
    sqrt_w = np.sqrt(w)
    for _ in range(max_iter):
        c0, c, a = p
        a_safe = max(a, 1e-9)
        e = np.exp(-h / a_safe)
        residual = (c0 + c * (1.0 - e)) - g
        d_c0 = np.ones_like(h)
        d_c = 1.0 - e
        d_a = -c * (h / (a_safe * a_safe)) * e
        J = np.stack([d_c0 * sqrt_w, d_c * sqrt_w, d_a * sqrt_w], axis=1)
        r = residual * sqrt_w
        try:
            step, *_ = np.linalg.lstsq(J, r, rcond=None)
        except np.linalg.LinAlgError:  # pragma: no cover
            break
        p_new = p - step
        p_new[0] = max(p_new[0], 0.0)
        p_new[1] = max(p_new[1], 0.0)
        p_new[2] = max(p_new[2], 1e-9)
        if np.linalg.norm(p_new - p) < tolerance:
            p = p_new
            break
        p = p_new
    return float(p[0]), float(p[1]), float(p[2])
