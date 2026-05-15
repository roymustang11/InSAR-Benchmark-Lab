import numpy as np
import pytest

from disp_s1_eval.errors import (
    closure_phase_residual,
    empirical_variogram,
    fit_exponential_variogram,
    paired_bootstrap_mean,
    reference_point_bootstrap,
    triple_collocation,
)


def test_empirical_variogram_increases_with_distance_for_linear_field():
    rng = np.random.default_rng(0)
    n = 60
    coords = rng.uniform(0.0, 10.0, size=(n, 2))
    values = 0.5 * coords[:, 0]
    bins = empirical_variogram(coords, values, n_bins=8)
    assert len(bins) >= 4
    semis = [b.semivariance for b in bins[:4]]
    assert semis[-1] > semis[0]


def test_fit_exponential_variogram_recovers_known_parameters():
    rng = np.random.default_rng(1)
    n = 200
    coords = rng.uniform(0.0, 50.0, size=(n, 2))
    distances = np.sqrt(((coords[:, None, :] - coords[None, :, :]) ** 2).sum(axis=-1))
    nugget, partial_sill, range_ = 0.2, 1.5, 12.0
    cov = nugget * np.eye(n) + partial_sill * np.exp(-distances / range_)
    L = np.linalg.cholesky(cov + 1e-9 * np.eye(n))
    field = L @ rng.standard_normal(n)
    bins = empirical_variogram(coords, field, n_bins=15)
    fit = fit_exponential_variogram(bins)
    assert fit.range == pytest.approx(range_, rel=0.6)
    assert fit.sill == pytest.approx(nugget + partial_sill, rel=0.6)


def test_triple_collocation_recovers_known_error_variances():
    rng = np.random.default_rng(2)
    truth = rng.standard_normal(2000)
    sigma_x, sigma_y, sigma_z = 0.5, 0.8, 0.3
    x = truth + rng.standard_normal(2000) * sigma_x
    y = truth + rng.standard_normal(2000) * sigma_y
    z = truth + rng.standard_normal(2000) * sigma_z
    out = triple_collocation(x, y, z)
    assert out.sigma_x == pytest.approx(sigma_x, rel=0.15)
    assert out.sigma_y == pytest.approx(sigma_y, rel=0.15)
    assert out.sigma_z == pytest.approx(sigma_z, rel=0.15)
    assert out.n_samples == 2000


def test_triple_collocation_drops_non_finite_pairs():
    x = np.array([1.0, 2.0, np.nan, 4.0])
    y = np.array([1.1, 2.1, 3.1, 4.1])
    z = np.array([0.9, 2.0, 3.2, np.inf])
    with pytest.raises(ValueError):
        triple_collocation(x, y, z)


def test_paired_bootstrap_mean_brackets_zero_for_zero_mean_data():
    rng = np.random.default_rng(3)
    sample = rng.normal(0.0, 1.0, size=500)
    out = paired_bootstrap_mean(sample, n_resamples=2000, seed=4)
    assert out.lower < 0.0 < out.upper


def test_paired_bootstrap_mean_rejects_short_series():
    with pytest.raises(ValueError):
        paired_bootstrap_mean([np.nan, 1.0])


def test_reference_point_bootstrap_returns_expected_keys():
    rng = np.random.default_rng(5)
    field = rng.standard_normal((4, 5, 6))
    candidates = np.array([[1, 1], [2, 3], [3, 4]])
    out = reference_point_bootstrap(field, candidates, n_draws=20, seed=6)
    assert set(out) == {"central", "lower", "upper", "width"}
    for arr in out.values():
        assert arr.shape == (5, 6)
    assert np.all(out["width"] >= 0)


def test_closure_phase_residual_is_zero_when_phases_consistent():
    rng = np.random.default_rng(7)
    a = rng.standard_normal((3, 3))
    b = rng.standard_normal((3, 3))
    c = rng.standard_normal((3, 3))
    interferograms = {
        (0, 1): a,
        (1, 2): b,
        (0, 2): a + b,
    }
    closure = closure_phase_residual(interferograms)
    assert (0, 1, 2) in closure
    assert np.allclose(closure[(0, 1, 2)], 0.0)


def test_closure_phase_residual_detects_unwrapping_error():
    a = np.zeros((2, 2))
    b = np.zeros((2, 2))
    c = np.full((2, 2), 2.0 * np.pi)
    interferograms = {(0, 1): a, (1, 2): b, (0, 2): c}
    closure = closure_phase_residual(interferograms)
    assert np.allclose(closure[(0, 1, 2)], -2.0 * np.pi)
