"""Closure-phase residual diagnostic.

For an interferogram triangle on epochs ``(t_i, t_j, t_k)`` (with
``i < j < k``), the closure phase is

.. math::

    \\Phi_{ijk} = \\varphi_{ij} + \\varphi_{jk} - \\varphi_{ik},

which is identically zero in the absence of phase-unwrapping errors,
non-linear scattering, or other systematic effects. A non-zero closure is
a quantitative diagnostic of those error sources (De Zan et al. 2015;
Ansari et al. 2021).

This module operates on already-unwrapped phase (or displacement, which
differs only by a known multiplicative factor) and returns the closure
residual for every requested triangle.
"""

from __future__ import annotations

from itertools import combinations
from typing import Iterable, Sequence

import numpy as np


def closure_phase_residual(
    interferograms: dict[tuple[int, int], np.ndarray],
    *,
    triangles: Iterable[tuple[int, int, int]] | None = None,
) -> dict[tuple[int, int, int], np.ndarray]:
    """Return the closure residual for every requested triangle.

    Parameters:
        interferograms:  Mapping of ``(reference_index, secondary_index)`` to
                         the unwrapped pairwise field (any shape).
        triangles:       Optional iterable of ``(i, j, k)`` triples with
                         ``i < j < k``. When ``None``, every triangle whose
                         three constituent pairs are present in
                         ``interferograms`` is evaluated.
    """
    if not interferograms:
        raise ValueError("interferograms mapping must be non-empty")

    pair_keys = set(interferograms)
    if triangles is None:
        all_indices: set[int] = set()
        for i, j in pair_keys:
            all_indices.add(i)
            all_indices.add(j)
        candidate_triangles: list[tuple[int, int, int]] = []
        for i, j, k in combinations(sorted(all_indices), 3):
            if (i, j) in pair_keys and (j, k) in pair_keys and (i, k) in pair_keys:
                candidate_triangles.append((i, j, k))
        triangles_iter: Sequence[tuple[int, int, int]] = candidate_triangles
    else:
        triangles_iter = list(triangles)

    out: dict[tuple[int, int, int], np.ndarray] = {}
    for i, j, k in triangles_iter:
        if not (i < j < k):
            raise ValueError(f"triangle indices must satisfy i < j < k: {(i, j, k)}")
        for pair in ((i, j), (j, k), (i, k)):
            if pair not in interferograms:
                raise KeyError(f"missing interferogram for pair {pair}")
        phi_ij = np.asarray(interferograms[(i, j)], dtype=float)
        phi_jk = np.asarray(interferograms[(j, k)], dtype=float)
        phi_ik = np.asarray(interferograms[(i, k)], dtype=float)
        if not (phi_ij.shape == phi_jk.shape == phi_ik.shape):
            raise ValueError(
                f"interferograms for triangle {(i, j, k)} have mismatched shapes"
            )
        out[(i, j, k)] = phi_ij + phi_jk - phi_ik
    return out
