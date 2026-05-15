"""Statistical error diagnostics for InSAR validation.

Tools follow ``docs/methodology.md`` §5 and ``docs/validation-protocol.md`` §7:

- :func:`empirical_variogram`, :func:`fit_exponential_variogram` —
  spatial decorrelation of residuals.
- :func:`triple_collocation` — per-product error variance from three
  pairwise-independent products (McColl et al. 2014).
- :func:`reference_point_bootstrap` — reference-frame nuisance.
- :func:`closure_phase_residual` — interferogram triangle closure.
- :func:`paired_bootstrap_mean` — CI on residual means.
"""

from disp_s1_eval.errors.bootstrap import (
    paired_bootstrap_mean,
    reference_point_bootstrap,
)
from disp_s1_eval.errors.closure import closure_phase_residual
from disp_s1_eval.errors.triple_collocation import (
    TripleCollocationResult,
    triple_collocation,
)
from disp_s1_eval.errors.variogram import (
    ExponentialVariogram,
    VariogramBin,
    empirical_variogram,
    fit_exponential_variogram,
)

__all__ = [
    "ExponentialVariogram",
    "TripleCollocationResult",
    "VariogramBin",
    "closure_phase_residual",
    "empirical_variogram",
    "fit_exponential_variogram",
    "paired_bootstrap_mean",
    "reference_point_bootstrap",
    "triple_collocation",
]
