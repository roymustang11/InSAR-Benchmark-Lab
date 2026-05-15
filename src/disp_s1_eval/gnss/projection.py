"""ENU-to-LOS projection with covariance propagation.

Convention follows ``docs/methodology.md`` §2: the LOS unit vector points
from the ground toward the satellite, expressed in the local east-north-up
frame, so positive LOS displacement corresponds to range decrease (motion
toward the satellite).
"""

from __future__ import annotations

import numpy as np


def project_enu_to_los(
    enu: np.ndarray,
    los_unit: np.ndarray,
) -> np.ndarray:
    """Project an ENU displacement vector onto the LOS unit vector.

    Parameters:
        enu:        Array of shape ``(3,)`` or ``(3, ...)`` with east, north,
                    up components.
        los_unit:   Array of shape ``(3,)`` or ``(3, ...)`` with the LOS
                    unit vector expressed in ENU. Must broadcast against ``enu``.

    Returns:
        LOS displacement of shape ``enu.shape[1:]`` (or scalar for 1-D inputs).
    """
    enu_arr = np.asarray(enu, dtype=float)
    los_arr = np.asarray(los_unit, dtype=float)
    if enu_arr.shape[0] != 3 or los_arr.shape[0] != 3:
        raise ValueError("first axis of enu and los_unit must have length 3")
    return np.einsum("i...,i...->...", los_arr, enu_arr)


def project_enu_covariance_to_los(
    covariance_enu: np.ndarray,
    los_unit: np.ndarray,
) -> np.ndarray:
    """Propagate a 3x3 ENU covariance into LOS variance.

    Parameters:
        covariance_enu: Array of shape ``(3, 3)`` or ``(..., 3, 3)``. Must be
                        symmetric positive semi-definite per epoch (not
                        enforced).
        los_unit:       Array of shape ``(3,)`` or ``(..., 3)`` with the LOS
                        unit vector expressed in ENU.

    Returns:
        LOS variance with shape ``covariance_enu.shape[:-2]`` (or scalar for
        a single 3x3 input).
    """
    cov = np.asarray(covariance_enu, dtype=float)
    los = np.asarray(los_unit, dtype=float)

    if cov.ndim == 2:
        if cov.shape != (3, 3):
            raise ValueError("covariance_enu must be 3x3")
        if los.shape != (3,):
            raise ValueError("los_unit must have shape (3,) when covariance is 3x3")
        return float(los @ cov @ los)

    if cov.shape[-2:] != (3, 3):
        raise ValueError("covariance_enu trailing axes must be (3, 3)")
    if los.shape[-1] != 3:
        raise ValueError("los_unit trailing axis must be 3")

    return np.einsum("...i,...ij,...j->...", los, cov, los)
