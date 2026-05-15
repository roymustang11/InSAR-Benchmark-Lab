import math

import numpy as np
import pytest

from insar_benchmark_lab.metrics import (
    correlation,
    mae,
    rmse,
    trend_bias,
    uncertainty_coverage,
    velocity_difference,
)


def test_rmse_ignores_nan_pairs():
    observed = np.array([1.0, 2.0, np.nan, 4.0])
    predicted = np.array([1.0, 4.0, 3.0, 1.0])

    assert rmse(observed, predicted) == pytest.approx(math.sqrt(13.0 / 3.0))


def test_mae_ignores_nan_pairs():
    observed = np.array([1.0, 2.0, np.nan, 4.0])
    predicted = np.array([2.0, 1.0, 3.0, 0.0])

    assert mae(observed, predicted) == pytest.approx(2.0)


def test_correlation_requires_two_valid_pairs():
    assert correlation([1.0, np.nan], [2.0, 3.0]) is None


def test_correlation_returns_pearson_value():
    assert correlation([1.0, 2.0, 3.0], [2.0, 4.0, 6.0]) == pytest.approx(1.0)


def test_velocity_difference_uses_first_and_last_valid_samples():
    dates = ["2020-01-01", "2021-01-01", "2022-01-01"]
    insar_mm = [0.0, 10.0, 20.0]
    gnss_mm = [0.0, 8.0, 16.0]

    assert velocity_difference(dates, insar_mm, gnss_mm) == pytest.approx(2.0)


def test_trend_bias_is_mean_residual():
    assert trend_bias([10.0, 20.0, 30.0], [8.0, 22.0, 25.0]) == pytest.approx(5.0 / 3.0)


def test_uncertainty_coverage_counts_residuals_inside_interval():
    observed = [0.0, 10.0, 20.0, 30.0]
    predicted = [1.0, 9.0, 25.0, 20.0]
    sigma = [2.0, 2.0, 2.0, 5.0]

    assert uncertainty_coverage(observed, predicted, sigma, sigma_multiplier=1.0) == pytest.approx(0.5)


def test_metrics_raise_for_no_valid_pairs():
    with pytest.raises(ValueError, match="at least one valid pair"):
        rmse([np.nan], [1.0])
