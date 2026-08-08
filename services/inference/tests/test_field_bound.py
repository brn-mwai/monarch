"""Tests for the bridge from a measured spread to the coupling the mechanism would need."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "field_bound.py"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("field_bound", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["field_bound"] = module
    spec.loader.exec_module(module)
    return module


class TestObservedSpread:
    def test_spread_is_max_minus_min(self, mod):
        rows = [{"naa_signed": "-0.05"}, {"naa_signed": "0.02"}, {"naa_signed": "-0.01"}]
        result = mod.observed_spread(rows, "naa_signed")
        assert result["spread"] == pytest.approx(0.07)
        assert result["n_defined"] == 3

    def test_undefined_values_are_excluded_and_counted(self, mod):
        rows = [{"naa_signed": "-0.05"}, {"naa_signed": ""}, {"naa_signed": "0.02"}]
        result = mod.observed_spread(rows, "naa_signed")
        # An empty value treated as 0.0 would report a spread of 0.07 either way here, but
        # would inflate it whenever the real values sit entirely on one side of zero.
        assert result["n_undefined"] == 1
        assert result["n_defined"] == 2
        assert result["min"] == pytest.approx(-0.05)

    def test_undefined_as_zero_would_have_widened_a_one_sided_spread(self, mod):
        rows = [{"naa_signed": "-0.05"}, {"naa_signed": ""}, {"naa_signed": "-0.02"}]
        result = mod.observed_spread(rows, "naa_signed")
        assert result["spread"] == pytest.approx(0.03)

    def test_too_few_defined_values_is_an_error(self, mod):
        with pytest.raises(ValueError, match="at least 2 defined values"):
            mod.observed_spread([{"naa_signed": "0.1"}], "naa_signed")


class TestRequiredCoupling:
    def test_the_bound_is_the_field_over_the_spread(self, mod):
        assert mod.required_coupling(0.5, 0.25) == pytest.approx(0.5)

    def test_a_narrower_observable_demands_a_larger_coupling(self, mod):
        assert mod.required_coupling(0.05, 0.5) > mod.required_coupling(0.5, 0.5)

    def test_doubling_the_spread_halves_the_requirement(self, mod):
        assert mod.required_coupling(0.2, 0.5) == pytest.approx(2 * mod.required_coupling(0.4, 0.5))

    def test_a_non_positive_spread_is_an_error(self, mod):
        with pytest.raises(ValueError, match="spread must be positive"):
            mod.required_coupling(0.0, 0.5)


class TestBoundTable:
    def test_it_uses_the_nearest_sampled_coupling_and_says_so(self, mod):
        beta_j = [1.0, 1.48, 2.01]
        h_c = [0.001, 0.3, 0.53]
        table = mod.bound_table(0.08, beta_j, h_c, targets=(1.5,))
        assert table[0]["beta_j_requested"] == 1.5
        assert table[0]["beta_j_used"] == 1.48

    def test_points_with_no_spinodal_are_skipped(self, mod):
        table = mod.bound_table(0.08, [0.5, 2.0], [float("nan"), 0.53], targets=(0.5, 2.0))
        assert len(table) == 1
        assert table[0]["beta_j_used"] == 2.0

    def test_the_reported_bound_matches_the_definition(self, mod):
        table = mod.bound_table(0.0801, [2.0], [0.53284], targets=(2.0,))
        assert table[0]["alpha_required"] == pytest.approx(0.53284 / 0.0801)
