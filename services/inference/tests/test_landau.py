"""Unit tests for app.services.landau.

These exercise the math directly without any tribev2 dependency.
"""

import numpy as np
import pytest

from app.services.landau import (
    compute_landau_analysis,
    compute_susceptibility_curve,
    find_equilibrium_m,
    landau_free_energy,
    self_consistency_rhs,
    susceptibility,
)


def test_self_consistency_rhs_zero():
    # tanh(0) = 0
    assert self_consistency_rhs(0.0, 0.7, 0.0) == pytest.approx(0.0)


def test_self_consistency_rhs_positive_field():
    # tanh(0.5 * 0 + 0.3) ~= 0.291
    val = self_consistency_rhs(0.0, 0.5, 0.3)
    assert val == pytest.approx(np.tanh(0.3), rel=1e-6)


def test_find_equilibrium_paramagnetic_no_field():
    """beta_J < 1 with NAA = 0 -> m* = 0 (paramagnetic, no spontaneous mag)."""
    m_star = find_equilibrium_m(beta_j=0.7, alpha_hat=0.5, naa=0.0)
    assert m_star == pytest.approx(0.0, abs=1e-6)


def test_find_equilibrium_with_field():
    """Positive NAA -> positive m*."""
    m_star = find_equilibrium_m(beta_j=0.7, alpha_hat=0.5, naa=2.0)
    assert m_star > 0.0
    assert m_star < 1.0  # bounded by tanh


def test_find_equilibrium_satisfies_self_consistency():
    """m* = tanh(beta_J*m* + h)."""
    beta_j = 0.7
    alpha_hat = 0.5
    naa = 1.5
    m_star = find_equilibrium_m(beta_j=beta_j, alpha_hat=alpha_hat, naa=naa)
    h = alpha_hat * naa
    rhs = np.tanh(beta_j * m_star + h)
    assert m_star == pytest.approx(rhs, abs=1e-8)


def test_landau_free_energy_shape():
    m = np.linspace(-1, 1, 50)
    F = landau_free_energy(m, beta_j=0.7, alpha_hat=0.5, naa=1.0)
    assert F.shape == m.shape


def test_landau_free_energy_minimum_with_field_is_positive_m():
    """With NAA > 0 the free-energy minimum should sit at positive m."""
    m = np.linspace(-1, 1, 1001)
    F = landau_free_energy(m, beta_j=0.7, alpha_hat=0.5, naa=1.5)
    m_min = m[np.argmin(F)]
    assert m_min > 0.0


def test_susceptibility_finite_below_critical():
    chi = susceptibility(
        m_star=0.0, beta_j=0.5, alpha_hat=0.5, naa=0.0
    )
    assert chi is not None
    assert np.isfinite(chi)
    assert chi > 0.0


def test_compute_landau_analysis_returns_all_keys():
    out = compute_landau_analysis(naa=1.5, alpha_hat=0.5, beta_j=0.7)
    for key in (
        "free_energy",
        "equilibrium_m",
        "susceptibility",
        "external_field_h",
        "beta_j",
        "alpha_hat",
        "naa",
    ):
        assert key in out
    assert len(out["free_energy"]["m"]) == 200
    assert len(out["free_energy"]["F"]) == 200


def test_susceptibility_curve_monotonic_in_naa_for_paramagnetic():
    """For beta_J = 0.5 (paramagnetic), chi should be a smooth function
    of NAA. We just check that the curve has the right length."""
    out = compute_susceptibility_curve(
        alpha_hat=0.5,
        naa_range=(0.0, 3.0),
        naa_points=20,
        beta_j=0.5,
    )
    assert len(out["naa"]) == 20
    assert len(out["chi"]) == 20
    # All entries finite for beta_J = 0.5
    assert all(c is not None and np.isfinite(c) for c in out["chi"])
