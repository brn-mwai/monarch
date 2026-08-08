"""Tests for the power statement, against properties power calculations must satisfy.

Checked against behaviour that follows from the definitions rather than against numbers
copied from another tool, so a passing suite means the module is internally coherent, not
that it agrees with a table nobody re-derived.
"""

from __future__ import annotations

import pytest

from app.services.power import (
    anova_minimum_detectable_eta_squared,
    anova_power,
    auc_from_separation,
    auc_minimum_detectable,
    auc_power,
    separation_from_auc,
    statement,
)


class TestAnovaPower:
    def test_zero_effect_gives_power_equal_to_alpha(self):
        assert anova_power(100, 4, 0.0, alpha=0.05) == pytest.approx(0.05)

    def test_power_rises_with_sample_size(self):
        small = anova_power(10, 4, 0.06)
        large = anova_power(100, 4, 0.06)
        assert large > small

    def test_power_rises_with_effect_size(self):
        assert anova_power(100, 4, 0.10) > anova_power(100, 4, 0.02)

    def test_a_large_effect_in_a_large_sample_is_near_certain(self):
        assert anova_power(100, 4, 0.25) > 0.99

    def test_too_few_per_group_is_an_error(self):
        with pytest.raises(ValueError, match="at least 2 per group"):
            anova_power(1, 4, 0.1)

    def test_effect_size_out_of_range_is_an_error(self):
        with pytest.raises(ValueError, match=r"eta_squared must be in \[0, 1\)"):
            anova_power(50, 4, 1.0)


class TestAnovaMinimumDetectable:
    def test_the_returned_effect_reaches_the_target_power(self):
        mde = anova_minimum_detectable_eta_squared(100, 4, target_power=0.80)
        assert anova_power(100, 4, mde) == pytest.approx(0.80, abs=0.01)

    def test_anything_smaller_falls_short_of_the_target(self):
        mde = anova_minimum_detectable_eta_squared(100, 4)
        assert anova_power(100, 4, mde * 0.5) < 0.80

    def test_bigger_samples_detect_smaller_effects(self):
        assert (anova_minimum_detectable_eta_squared(400, 4)
                < anova_minimum_detectable_eta_squared(25, 4))

    def test_demanding_more_power_demands_a_bigger_effect(self):
        assert (anova_minimum_detectable_eta_squared(100, 4, target_power=0.95)
                > anova_minimum_detectable_eta_squared(100, 4, target_power=0.80))


class TestBinormalMapping:
    def test_no_separation_is_chance(self):
        assert auc_from_separation(0.0) == pytest.approx(0.5)

    def test_the_mapping_round_trips(self):
        for auc in (0.55, 0.7, 0.9):
            assert auc_from_separation(separation_from_auc(auc)) == pytest.approx(auc)

    def test_auc_outside_the_open_unit_interval_is_an_error(self):
        with pytest.raises(ValueError, match=r"auc must be in \(0, 1\)"):
            separation_from_auc(1.0)


class TestAucPower:
    def test_chance_level_rejects_at_about_alpha(self):
        power = auc_power(50, 50, 0.5 + 1e-9, alpha=0.05, n_simulations=2000, seed=1)
        assert power == pytest.approx(0.05, abs=0.03)

    def test_power_rises_with_the_effect(self):
        assert (auc_power(50, 50, 0.80, n_simulations=600, seed=2)
                > auc_power(50, 50, 0.60, n_simulations=600, seed=2))

    def test_power_rises_with_sample_size(self):
        assert (auc_power(150, 150, 0.65, n_simulations=600, seed=3)
                > auc_power(15, 15, 0.65, n_simulations=600, seed=3))

    def test_same_seed_reproduces_the_estimate(self):
        first = auc_power(40, 40, 0.7, n_simulations=400, seed=9)
        second = auc_power(40, 40, 0.7, n_simulations=400, seed=9)
        assert first == second

    def test_a_single_case_class_is_an_error(self):
        with pytest.raises(ValueError, match="at least 2 in each class"):
            auc_power(1, 50, 0.7)


class TestAucMinimumDetectable:
    def test_the_returned_auc_reaches_roughly_the_target_power(self):
        mde = auc_minimum_detectable(100, 100, n_simulations=600, seed=4, tolerance=0.01)
        assert auc_power(100, 100, mde, n_simulations=600, seed=4) >= 0.75

    def test_bigger_samples_detect_smaller_aucs(self):
        big = auc_minimum_detectable(200, 200, n_simulations=400, seed=5, tolerance=0.02)
        small = auc_minimum_detectable(20, 20, n_simulations=400, seed=5, tolerance=0.02)
        assert big < small

    def test_the_result_stays_above_chance(self):
        mde = auc_minimum_detectable(100, 100, n_simulations=400, seed=6, tolerance=0.02)
        assert 0.5 < mde < 1.0


class TestStatement:
    def test_it_reports_both_tests_and_the_settings_used(self):
        result = statement(100, 4, 300, 100, seed=0)
        assert result["anova"]["n_total"] == 400
        assert result["auc"]["n_positive"] == 300
        assert 0.0 < result["anova"]["minimum_detectable_eta_squared"] < 1.0
        assert 0.5 < result["auc"]["minimum_detectable_auc"] < 1.0
        assert result["alpha"] == 0.05
        assert result["target_power"] == 0.80

    def test_cohens_f_agrees_with_the_eta_squared_it_reports(self):
        result = statement(100, 4, 300, 100, seed=0)
        eta = result["anova"]["minimum_detectable_eta_squared"]
        f = result["anova"]["minimum_detectable_cohens_f"]
        assert f ** 2 == pytest.approx(eta / (1 - eta))
