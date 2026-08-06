"""Tests for the (beta_J, NAA) phase map, proposal objective (v).

The physics these assert is textbook mean-field Ising, which is the point: if
the sweep does not reproduce the known behaviour of the model it implements,
no result computed on top of it can be trusted.
"""

import numpy as np
import pytest

from app.services.phase_map import (
    CRITICAL_BETA_J,
    compute_phase_map,
    critical_field,
    is_bistable,
    sweep,
)


class TestBistability:
    def test_paramagnetic_regime_is_never_bistable(self):
        for beta_j in (0.1, 0.5, 0.9, 0.99):
            assert is_bistable(beta_j, 0.0) is False

    def test_ferromagnetic_regime_is_bistable_at_zero_field(self):
        for beta_j in (1.1, 1.3, 1.6):
            assert is_bistable(beta_j, 0.0) is True

    def test_strong_field_collapses_bistability(self):
        """A large enough field destroys the second minimum even above
        beta_J = 1. This is the spinodal, not an edge case."""
        assert is_bistable(1.5, 0.0) is True
        assert is_bistable(1.5, 5.0) is False


class TestCriticalField:
    def test_none_below_critical_coupling(self):
        assert critical_field(0.8) is None
        assert critical_field(CRITICAL_BETA_J) is None

    def test_positive_above_critical_coupling(self):
        h_c = critical_field(1.3)
        assert h_c is not None and h_c > 0.0

    def test_grows_with_coupling(self):
        """Deeper wells need a stronger field to collapse."""
        assert critical_field(1.5) > critical_field(1.2)

    def test_brackets_the_bistable_boundary(self):
        beta_j = 1.4
        h_c = critical_field(beta_j)
        assert is_bistable(beta_j, h_c * 0.9) is True
        assert is_bistable(beta_j, h_c * 1.1) is False


class TestSweep:
    def test_grid_is_beta_major(self):
        naa = np.linspace(-1.0, 1.0, 5)
        beta = np.linspace(0.2, 1.4, 3)
        result = sweep(naa, beta, alpha=1.0)

        assert len(result["m_star"]) == 3
        assert len(result["m_star"][0]) == 5

    def test_zero_field_gives_zero_polarisation_below_critical(self):
        result = sweep(np.array([0.0]), np.array([0.5]), alpha=1.0)
        assert result["m_star"][0][0] == pytest.approx(0.0, abs=1e-8)

    def test_polarisation_follows_field_sign(self):
        result = sweep(np.array([-0.5, 0.5]), np.array([0.5]), alpha=1.0)
        negative, positive = result["m_star"][0]

        assert negative < 0.0 < positive
        assert negative == pytest.approx(-positive, abs=1e-9)

    def test_polarisation_stays_inside_physical_bounds(self):
        result = sweep(
            np.linspace(-3.0, 3.0, 9), np.linspace(0.1, 1.8, 7), alpha=1.0
        )
        flat = [m for row in result["m_star"] for m in row]

        assert all(-1.0 <= m <= 1.0 for m in flat)

    def test_rejects_non_1d_input(self):
        with pytest.raises(ValueError, match="1-D"):
            sweep(np.zeros((2, 2)), np.array([0.5]), alpha=1.0)


class TestComputePhaseMap:
    def test_shape_matches_requested_resolution(self):
        result = compute_phase_map(naa_points=11, beta_j_points=7)

        assert len(result["naa"]) == 11
        assert len(result["beta_j"]) == 7
        assert len(result["m_star"]) == 7
        assert len(result["susceptibility"][0]) == 11

    def test_spinodal_is_none_below_critical_and_set_above(self):
        result = compute_phase_map(
            beta_j_range=(0.5, 1.5), beta_j_points=11, naa_points=5
        )
        entries = {round(e["beta_j"], 4): e["critical_field"] for e in result["spinodal"]}

        assert all(v is None for k, v in entries.items() if k <= CRITICAL_BETA_J)
        assert any(v is not None for k, v in entries.items() if k > CRITICAL_BETA_J)

    def test_alpha_is_echoed_not_assumed(self):
        """No alpha_hat is quoted in this project, so the caller supplies it
        and the map records which value produced it."""
        assert compute_phase_map(alpha=0.25, naa_points=5, beta_j_points=5)["alpha"] == 0.25
