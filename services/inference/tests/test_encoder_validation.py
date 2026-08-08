"""Tests for Paper 3's evaluation core, against cases whose answer is known in advance.

The claim under test lives near r = 0.015, so a convention that quietly turns an undefined
vertex into a zero would move the result by more than the effect. These tests pin the
conventions, not just the arithmetic.
"""

from __future__ import annotations

import numpy as np
import pytest

from app.services.encoder_validation import (
    bootstrap_ci,
    evaluate,
    noise_ceiling,
    vertex_correlation,
)


@pytest.fixture
def rng() -> np.random.Generator:
    return np.random.default_rng(20260808)


class TestVertexCorrelation:
    def test_identical_signals_give_one(self, rng):
        signal = rng.normal(size=(50, 200))
        result = vertex_correlation(signal, signal)
        assert np.allclose(result["r_per_vertex"], 1.0)
        assert result["n_undefined"] == 0

    def test_negated_signals_give_minus_one_and_the_sign_is_kept(self, rng):
        signal = rng.normal(size=(50, 200))
        result = vertex_correlation(signal, -signal)
        assert np.allclose(result["r_per_vertex"], -1.0)
        assert result["mean_r"] == pytest.approx(-1.0)

    def test_flat_vertices_are_undefined_not_zero(self, rng):
        predicted = rng.normal(size=(10, 100))
        observed = rng.normal(size=(10, 100))
        observed[3] = 0.7
        result = vertex_correlation(predicted, observed)
        assert np.isnan(result["r_per_vertex"][3])
        assert result["n_undefined"] == 1
        assert result["n_defined"] == 9

    def test_a_flat_vertex_does_not_drag_the_mean_toward_zero(self, rng):
        predicted = rng.normal(size=(4, 300))
        observed = predicted.copy()
        observed[0] = 1.0
        result = vertex_correlation(predicted, observed)
        # Three perfectly correlated vertices and one undefined: the mean is 1.0, not 0.75.
        assert result["mean_r"] == pytest.approx(1.0)

    def test_an_all_zero_vertex_is_undefined(self, rng):
        predicted = rng.normal(size=(5, 100))
        observed = rng.normal(size=(5, 100))
        observed[2] = 0.0
        assert np.isnan(vertex_correlation(predicted, observed)["r_per_vertex"][2])

    @pytest.mark.parametrize("level", [1e-8, 0.7, 1.0, 1e6])
    def test_constant_vertices_are_undefined_at_every_scale(self, rng, level):
        # Regression: centring a constant row leaves residue near 1e-17, which a ">0" test
        # admits and turns into a correlation of order 1e-17 rather than a NaN.
        predicted = rng.normal(size=(3, 100))
        observed = rng.normal(size=(3, 100))
        observed[1] = level
        assert np.isnan(vertex_correlation(predicted, observed)["r_per_vertex"][1])

    def test_shape_mismatch_is_an_error(self, rng):
        with pytest.raises(ValueError, match="shape mismatch"):
            vertex_correlation(rng.normal(size=(5, 100)), rng.normal(size=(6, 100)))

    def test_too_few_timepoints_is_an_error(self, rng):
        with pytest.raises(ValueError, match="at least 3 timepoints"):
            vertex_correlation(rng.normal(size=(5, 2)), rng.normal(size=(5, 2)))


class TestNoiseCeiling:
    def test_identical_subjects_ceiling_is_one(self, rng):
        shared = rng.normal(size=(20, 150))
        result = noise_ceiling([shared.copy() for _ in range(4)])
        assert result["mean_ceiling"] == pytest.approx(1.0)
        assert result["n_subjects"] == 4

    def test_independent_subjects_ceiling_sits_near_zero(self, rng):
        subjects = [rng.normal(size=(200, 150)) for _ in range(5)]
        result = noise_ceiling(subjects)
        assert abs(result["mean_ceiling"]) < 0.1

    def test_shared_signal_under_noise_lifts_the_ceiling(self, rng):
        shared = rng.normal(size=(100, 200))
        subjects = [shared + rng.normal(scale=0.5, size=(100, 200)) for _ in range(4)]
        result = noise_ceiling(subjects)
        assert result["mean_ceiling"] > 0.5

    def test_one_subject_is_an_error(self, rng):
        with pytest.raises(ValueError, match="at least 2 subjects"):
            noise_ceiling([rng.normal(size=(10, 50))])


class TestBootstrapCi:
    def test_interval_brackets_the_point_estimate(self, rng):
        values = rng.normal(loc=0.3, scale=0.05, size=40)
        ci = bootstrap_ci(values, n_resamples=2000, seed=1)
        assert ci["low"] < ci["point"] < ci["high"]

    def test_same_seed_reproduces_the_interval(self, rng):
        values = rng.normal(size=30)
        first = bootstrap_ci(values, n_resamples=1000, seed=7)
        second = bootstrap_ci(values, n_resamples=1000, seed=7)
        assert first == second

    def test_non_finite_values_are_excluded_from_n(self):
        ci = bootstrap_ci(np.array([0.1, 0.2, np.nan, np.inf]), n_resamples=500, seed=0)
        assert ci["n"] == 2

    def test_all_undefined_gives_nan_rather_than_a_number(self):
        ci = bootstrap_ci(np.array([np.nan, np.nan]), n_resamples=100, seed=0)
        assert np.isnan(ci["point"])
        assert ci["n"] == 0


class TestEvaluate:
    def test_a_predictor_of_the_shared_signal_beats_zero(self, rng):
        shared = rng.normal(size=(60, 200))
        subjects = [shared + rng.normal(scale=0.4, size=(60, 200)) for _ in range(5)]
        result = evaluate(shared, subjects, seed=3)
        assert result["beats_zero"]
        assert result["n_subjects"] == 5

    def test_an_anticorrelated_predictor_is_reported_negative(self, rng):
        shared = rng.normal(size=(60, 200))
        subjects = [shared + rng.normal(scale=0.3, size=(60, 200)) for _ in range(4)]
        result = evaluate(-shared, subjects, seed=3)
        assert result["encoder_mean_r"]["point"] < 0
        assert not result["beats_zero"]

    def test_unrelated_predictions_do_not_reach_the_ceiling(self, rng):
        shared = rng.normal(size=(80, 200))
        subjects = [shared + rng.normal(scale=0.3, size=(80, 200)) for _ in range(4)]
        result = evaluate(rng.normal(size=(80, 200)), subjects, seed=5)
        assert not result["reaches_ceiling"]
        assert result["noise_ceiling"]["point"] > result["encoder_mean_r"]["point"]
