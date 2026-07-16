"""Tests for objective (vi), NAA as a manipulation classifier (RQ I).

The load-bearing tests are the ones asserting the module does NOT rescue a bad
result: it must report below-chance AUC as below-chance rather than flipping the
sign, and it must flag a near-perfect AUC as a suspected leak rather than a
finding.
"""

import numpy as np
import pytest

from app.services.validation import evaluate, optimal_threshold, roc_curve_points


def _separable(n: int = 200, gap: float = 4.0, seed: int = 17):
    rng = np.random.default_rng(seed)
    manipulative = rng.normal(gap, 1.0, size=n)
    neutral = rng.normal(0.0, 1.0, size=n)
    scores = np.concatenate([manipulative, neutral])
    labels = np.concatenate([np.ones(n, int), np.zeros(n, int)])
    return scores, labels


def _random(n: int = 400, seed: int = 17):
    rng = np.random.default_rng(seed)
    return rng.normal(0.0, 1.0, size=n), rng.integers(0, 2, size=n)


class TestEvaluate:
    def test_separable_scores_give_high_auc(self):
        result = evaluate(*_separable())
        assert result["auc"] > 0.99
        assert result["discriminates"] is True
        assert result["direction_matches_hypothesis"] is True

    def test_random_scores_give_chance_auc(self):
        result = evaluate(*_random())
        assert result["auc"] == pytest.approx(0.5, abs=0.1)
        assert result["discriminates"] is False
        assert "does not separate" in result["interpretation"]

    def test_below_chance_is_reported_not_flipped(self):
        """The refutation case. Neutral scoring above manipulative must be
        reported as opposite-to-hypothesis, not silently sign-flipped into a
        positive result.

        gap=1.5 gives AUC ~0.85, so the inverted case lands ~0.15: clearly
        below chance but below the leak threshold, which isolates the direction
        path from the leak path.
        """
        scores, labels = _separable(gap=1.5)
        result = evaluate(-scores, labels)
        assert result["auc"] < 0.4
        assert result["leak_suspected"] is False
        assert result["direction_matches_hypothesis"] is False
        assert result["discriminates"] is True
        assert "OPPOSITE" in result["interpretation"]
        assert result["auc_flipped"] == pytest.approx(1.0 - result["auc"])

    def test_inverted_near_perfect_reports_both_leak_and_direction(self):
        """An extreme inverted AUC is both suspicious and inverted. The leak
        warning takes priority but must not swallow the direction."""
        scores, labels = _separable(gap=4.0)
        result = evaluate(-scores, labels)
        assert result["leak_suspected"] is True
        assert result["direction_matches_hypothesis"] is False
        assert "inverted" in result["interpretation"]

    def test_near_perfect_auc_flags_leak(self):
        result = evaluate(*_separable(gap=50.0))
        assert result["leak_suspected"] is True
        assert "leakage" in result["interpretation"]

    def test_leak_flag_is_direction_agnostic(self):
        scores, labels = _separable(gap=50.0)
        assert evaluate(-scores, labels)["leak_suspected"] is True

    def test_moderate_auc_is_not_flagged_as_leak(self):
        result = evaluate(*_separable(gap=1.0))
        assert result["leak_suspected"] is False

    def test_counts_and_confusion_matrix(self):
        result = evaluate(*_separable(n=150))
        assert result["n"] == 300
        assert result["n_manipulative"] == 150
        assert result["n_neutral"] == 150
        assert np.array(result["confusion_matrix"]).sum() == 300

    def test_declares_threshold_is_in_sample(self):
        assert evaluate(*_separable())["threshold_fitted_in_sample"] is True

    def test_perfect_separation_gives_perfect_f1(self):
        scores = np.concatenate([np.full(50, 10.0), np.full(50, -10.0)])
        labels = np.concatenate([np.ones(50, int), np.zeros(50, int)])
        result = evaluate(scores, labels)
        assert result["f1"] == pytest.approx(1.0)
        assert result["precision"] == pytest.approx(1.0)
        assert result["recall"] == pytest.approx(1.0)


class TestInputValidation:
    def test_mismatched_lengths_rejected(self):
        with pytest.raises(ValueError, match="differ in length"):
            evaluate(np.zeros(10), np.ones(5, int))

    def test_non_binary_labels_rejected(self):
        with pytest.raises(ValueError, match="binary"):
            evaluate(np.zeros(10), np.full(10, 2))

    def test_nan_scores_rejected(self):
        scores, labels = _separable(n=10)
        scores[0] = np.nan
        with pytest.raises(ValueError, match="NaN"):
            evaluate(scores, labels)

    def test_single_class_rejected(self):
        with pytest.raises(ValueError, match="class"):
            evaluate(np.arange(10.0), np.ones(10, int))


class TestOptimalThreshold:
    def test_recovers_midpoint_of_separated_classes(self):
        scores = np.concatenate([np.full(50, 10.0), np.full(50, 0.0)])
        labels = np.concatenate([np.ones(50, int), np.zeros(50, int)])
        point = optimal_threshold(scores, labels)
        assert 0.0 < point["threshold"] <= 10.0
        assert point["youden_j"] == pytest.approx(1.0)

    def test_sensitivity_and_specificity_bounded(self):
        point = optimal_threshold(*_separable())
        assert 0.0 <= point["sensitivity"] <= 1.0
        assert 0.0 <= point["specificity"] <= 1.0


class TestRocCurvePoints:
    def test_curve_is_monotonic_and_anchored(self):
        curve = roc_curve_points(*_separable())
        assert curve["fpr"][0] == 0.0
        assert curve["tpr"][0] == 0.0
        assert curve["fpr"][-1] == 1.0
        assert curve["tpr"][-1] == 1.0
        assert all(np.diff(curve["fpr"]) >= 0)
        assert all(np.diff(curve["tpr"]) >= 0)

    def test_auc_matches_evaluate(self):
        scores, labels = _separable()
        assert roc_curve_points(scores, labels)["auc"] == pytest.approx(
            evaluate(scores, labels)["auc"]
        )
