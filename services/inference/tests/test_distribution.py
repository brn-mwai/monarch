"""Tests for objective (iii), the per-category NAA characterisation (RQ II).

Where a statistic has a known analytic value, the test recovers it rather than
asserting the code merely runs. A KL estimator that returns a plausible number
for every input is worse than none: it would let the thesis report a divergence
between categories that do not differ.
"""

import numpy as np
import pytest

from app.services.distribution import (
    characterise,
    cohens_d,
    describe,
    kl_divergence,
    separation,
    shannon_entropy,
)


def _normal(mean: float, sd: float, n: int = 600, seed: int = 17) -> np.ndarray:
    return np.random.default_rng(seed).normal(mean, sd, size=n)


class TestDescribe:
    def test_recovers_moments(self):
        result = describe(_normal(5.0, 2.0, n=4000))
        assert result["mean"] == pytest.approx(5.0, abs=0.1)
        assert result["sd"] == pytest.approx(2.0, abs=0.1)
        assert result["skewness"] == pytest.approx(0.0, abs=0.15)
        assert result["excess_kurtosis"] == pytest.approx(0.0, abs=0.25)

    def test_reports_n(self):
        assert describe(np.arange(10.0))["n"] == 10

    def test_rejects_singleton(self):
        with pytest.raises(ValueError, match="at least"):
            describe(np.array([1.0]))


class TestCohensD:
    def test_recovers_known_effect(self):
        """Means one SD apart must give d ~= 1."""
        a = _normal(1.0, 1.0, n=4000, seed=1)
        b = _normal(0.0, 1.0, n=4000, seed=2)
        assert cohens_d(a, b) == pytest.approx(1.0, abs=0.1)

    def test_zero_for_identical_distributions(self):
        a = _normal(0.0, 1.0, n=2000, seed=3)
        assert cohens_d(a, a) == pytest.approx(0.0, abs=1e-9)

    def test_sign_marks_direction(self):
        high = _normal(2.0, 1.0, n=800, seed=4)
        low = _normal(0.0, 1.0, n=800, seed=5)
        assert cohens_d(high, low) > 0
        assert cohens_d(low, high) < 0

    def test_identical_constants_give_zero(self):
        constant = np.full(10, 3.0)
        assert cohens_d(constant, constant) == 0.0

    def test_constant_groups_with_offset_raise(self):
        with pytest.raises(ValueError, match="pooled SD is zero"):
            cohens_d(np.full(10, 1.0), np.full(10, 2.0))


class TestShannonEntropy:
    def test_matches_analytic_gaussian_entropy(self):
        """H = 0.5*log(2*pi*e*sigma^2) nats for a Gaussian."""
        sigma = 2.0
        expected = 0.5 * np.log(2 * np.pi * np.e * sigma**2)
        assert shannon_entropy(_normal(0.0, sigma, n=6000)) == pytest.approx(
            expected, abs=0.15
        )

    def test_wider_distribution_has_higher_entropy(self):
        narrow = shannon_entropy(_normal(0.0, 0.5, n=3000, seed=6))
        wide = shannon_entropy(_normal(0.0, 4.0, n=3000, seed=6))
        assert wide > narrow

    def test_constant_sample_rejected(self):
        with pytest.raises(ValueError, match="constant"):
            shannon_entropy(np.full(50, 1.0))


class TestKlDivergence:
    def test_near_zero_for_same_distribution(self):
        a = _normal(0.0, 1.0, n=3000, seed=7)
        assert kl_divergence(a, a) == pytest.approx(0.0, abs=1e-6)

    def test_non_negative_for_different_distributions(self):
        a = _normal(0.0, 1.0, n=2000, seed=8)
        b = _normal(3.0, 1.0, n=2000, seed=9)
        assert kl_divergence(a, b) > 0

    def test_grows_with_separation(self):
        base = _normal(0.0, 1.0, n=2000, seed=10)
        near = _normal(1.0, 1.0, n=2000, seed=11)
        far = _normal(5.0, 1.0, n=2000, seed=12)
        assert kl_divergence(far, base) > kl_divergence(near, base)

    def test_is_asymmetric(self):
        p = _normal(0.0, 1.0, n=2000, seed=13)
        q = _normal(1.0, 3.0, n=2000, seed=14)
        assert kl_divergence(p, q) != pytest.approx(kl_divergence(q, p), abs=1e-3)


class TestSeparation:
    def test_detects_real_separation(self):
        groups = {
            "a": _normal(0.0, 1.0, n=200, seed=15),
            "b": _normal(3.0, 1.0, n=200, seed=16),
        }
        result = separation(groups)
        assert result["significant"] is True
        assert result["usable"] is True
        assert result["eta_squared"] > 0.5

    def test_reports_no_separation_when_groups_identical(self):
        """The Gate 2 kill case: categories drawn from one distribution."""
        rng = np.random.default_rng(21)
        groups = {name: rng.normal(0.0, 1.0, size=200) for name in "abcd"}
        result = separation(groups)
        assert result["usable"] is False
        assert result["eta_squared"] < 0.06

    def test_significant_but_negligible_is_not_usable(self):
        """With large n a trivial effect reaches p < 0.05. eta^2 must veto it.

        This is the guard that stops the thesis reporting a statistically
        significant but physically meaningless category difference.
        """
        groups = {
            "a": _normal(0.0, 1.0, n=8000, seed=18),
            "b": _normal(0.05, 1.0, n=8000, seed=19),
        }
        result = separation(groups)
        assert result["significant"] is True
        assert result["eta_squared"] < 0.06
        assert result["usable"] is False

    def test_variance_decomposition_sums_to_total(self):
        groups = {
            "a": _normal(0.0, 1.0, n=100, seed=22),
            "b": _normal(2.0, 1.0, n=100, seed=23),
        }
        result = separation(groups)
        pooled = np.concatenate(list(groups.values()))
        total = float(np.sum((pooled - pooled.mean()) ** 2))
        assert result["ss_between"] + result["ss_within"] == pytest.approx(total)

    def test_single_category_rejected(self):
        with pytest.raises(ValueError, match="at least two categories"):
            separation({"only": _normal(0.0, 1.0, n=50)})


class TestCharacterise:
    def _groups(self):
        return {
            "high_outrage": _normal(1.0, 1.0, n=300, seed=24),
            "fear_activating": _normal(0.8, 1.0, n=300, seed=25),
            "reward_hook": _normal(0.5, 1.0, n=300, seed=26),
            "neutral_informational": _normal(0.0, 1.0, n=300, seed=27),
        }

    def test_full_rq2_answer_shape(self):
        result = characterise(self._groups(), baseline="neutral_informational")
        assert set(result["per_category"]) == set(self._groups())
        assert result["separation"]["usable"] is True

    def test_baseline_excluded_from_own_comparison(self):
        result = characterise(self._groups(), baseline="neutral_informational")
        baseline = result["per_category"]["neutral_informational"]
        assert "cohens_d_vs_baseline" not in baseline
        assert "kl_vs_baseline" not in baseline

    def test_effect_sizes_ordered_by_true_separation(self):
        result = characterise(self._groups(), baseline="neutral_informational")
        per = result["per_category"]
        assert (
            per["high_outrage"]["cohens_d_vs_baseline"]
            > per["reward_hook"]["cohens_d_vs_baseline"]
        )

    def test_unknown_baseline_rejected(self):
        with pytest.raises(ValueError, match="not among"):
            characterise(self._groups(), baseline="does_not_exist")

    def test_degenerate_category_yields_none_not_a_number(self):
        """A constant category must surface as absent, never as a fabrication."""
        groups = self._groups()
        groups["reward_hook"] = np.full(300, 0.5)
        result = characterise(groups, baseline="neutral_informational")
        assert result["per_category"]["reward_hook"]["entropy"] is None
        assert result["per_category"]["reward_hook"]["kl_vs_baseline"] is None
