"""Landau mean-field theory of collective opinion dynamics.

From the research proposal eq. (7)-(13)::

    Self-consistency:  m  = tanh(beta_J * m + beta * alpha_hat * NAA)
    Free energy:       F(m) = a(T) * m^2 + b * m^4 - h * m
    Susceptibility:    chi  = beta * sech^2(beta_J*m* + beta*alpha_hat*NAA)
                              / (1 - beta_J * sech^2(...))

where:

    beta       = 1 / (k_B * T), with k_B = 1 in natural units
    beta_J     = social coupling constant
    alpha_hat  = heuristic field-scale constant calibrated from NELA-GT
    NAA        = Neural Arousal Asymmetry index
    m          = collective opinion polarisation in [-1, +1]

The Landau layer is a THEORETICAL INTERPRETATION of the measured NAA
observable. It is not direct evidence of real-world opinion shift; it
maps the content-level neural bias into a mean-field model of how a
population of weakly-coupled agents would respond to that bias.

This module is pure numpy / scipy and has zero dependency on TRIBE v2.
"""

from typing import Optional

import numpy as np


def self_consistency_rhs(m: float, beta_j: float, beta_alpha_naa: float) -> float:
    """Right-hand side of eq. (7): tanh(beta_J*m + beta*alpha_hat*NAA)."""
    return float(np.tanh(beta_j * m + beta_alpha_naa))


def find_equilibrium_m(
    beta_j: float,
    alpha_hat: float,
    naa: float,
    beta: float = 1.0,
    max_iter: int = 1000,
    tol: float = 1e-10,
) -> float:
    """Find equilibrium polarisation m* by fixed-point iteration of eq. (7).

    The iteration ``m_{k+1} = tanh(beta_J * m_k + h)`` converges
    monotonically when beta_J < 1 (paramagnetic regime) and bistably
    when beta_J > 1 (ferromagnetic regime, two stable roots).

    In the ferromagnetic regime m = 0 is an UNSTABLE fixed point, so a
    seed of exactly 0 would return the unstable root. We seed away from
    zero to land on the stable +/- root; with no external field the two
    roots are symmetric and the tie is broken toward +m* by convention.
    """
    h = beta * alpha_hat * naa
    if beta_j > 1.0:
        seed = float(np.copysign(0.9, h)) if h != 0.0 else 0.9
    else:
        seed = 0.0
    m = seed
    for _ in range(max_iter):
        m_new = float(np.tanh(beta_j * m + h))
        if abs(m_new - m) < tol:
            return m_new
        m = m_new
    return m


def landau_free_energy(
    m: np.ndarray,
    beta_j: float,
    alpha_hat: float,
    naa: float,
    beta: float = 1.0,
) -> np.ndarray:
    """Landau free energy F(m), the quartic expansion of the mean-field
    free energy whose minimisation reproduces the self-consistency.

    F(m) = a * m^2 + b * m^4 - h * m

    with a = (1 - beta_J) / 2, b = 1 / 12, h = beta * alpha_hat * NAA.

    These coefficients are fixed by requiring dF/dm = 0 to match the
    cubic-order expansion of m = tanh(beta_J*m + h): artanh(m) ~= m + m^3/3
    gives (1 - beta_J)*m + m^3/3 - h = 0, i.e. 2a = 1 - beta_J and 4b = 1/3.
    With these the curve's minimum coincides with find_equilibrium_m near
    criticality (small m). The double-well structure appears when a < 0,
    i.e. beta_J > 1.

    NOTE (paper divergence): the product paper, eq. (5), writes
    a = 1 - beta_J and b = (beta_J)^3 / 3, which do not derive from its own
    self-consistency eq. (4) and leave the plotted minimum off the marked
    m*. The coefficients here supersede the paper; update eq. (5) to match.
    """
    a = (1.0 - beta_j) / 2.0
    b = 1.0 / 12.0
    h = beta * alpha_hat * naa
    return a * m ** 2 + b * m ** 4 - h * m


def susceptibility(
    m_star: float,
    beta_j: float,
    alpha_hat: float,
    naa: float,
    beta: float = 1.0,
) -> Optional[float]:
    """Population susceptibility chi from eq. (9).

    chi = beta * sech^2(beta_J*m* + beta*alpha_hat*NAA)
          / (1 - beta_J * sech^2(beta_J*m* + beta*alpha_hat*NAA))

    Returns ``None`` when the denominator is non-positive: it vanishes at
    the critical point (susceptibility diverges) and goes negative on the
    supercritical branch when evaluated off the stable root, where a
    finite negative chi would be unphysical. At a stable equilibrium the
    denominator is positive and chi is finite.
    """
    arg = beta_j * m_star + beta * alpha_hat * naa
    sech2 = 1.0 / (np.cosh(arg) ** 2)
    numerator = beta * sech2
    denominator = 1.0 - beta_j * sech2
    if denominator <= 1e-12:
        return None
    return float(numerator / denominator)


def compute_landau_analysis(
    naa: float,
    alpha_hat: float,
    beta_j: float = 0.7,
    m_points: int = 200,
) -> dict:
    """Full Landau / Ising analysis for a single NAA value.

    Returns everything needed for the report-page visualisations:

    - Free energy curve F(m) sampled on a uniform m grid
    - Equilibrium polarisation m*
    - Susceptibility chi (or None at the critical point)
    - External field h = alpha_hat * NAA
    - Echo of the input parameters for the chart legend
    """
    m_grid = np.linspace(-1.0, 1.0, m_points)
    f_grid = landau_free_energy(m_grid, beta_j, alpha_hat, naa)

    m_star = find_equilibrium_m(beta_j, alpha_hat, naa)
    chi = susceptibility(m_star, beta_j, alpha_hat, naa)
    h = alpha_hat * naa  # beta = 1

    return {
        "free_energy": {
            "m": m_grid.tolist(),
            "F": f_grid.tolist(),
        },
        "equilibrium_m": float(m_star),
        "susceptibility": chi,
        "external_field_h": float(h),
        "beta_j": float(beta_j),
        "alpha_hat": float(alpha_hat),
        "naa": float(naa),
    }


def compute_susceptibility_curve(
    alpha_hat: float,
    naa_range: tuple[float, float] = (0.0, 5.0),
    naa_points: int = 100,
    beta_j: float = 0.7,
) -> dict:
    """Susceptibility chi(NAA) curve for the susceptibility chart.

    Sweeps NAA along ``naa_range`` and reports chi at each point. Used
    by the population-sensitivity panel of the report.
    """
    naa_grid = np.linspace(naa_range[0], naa_range[1], naa_points)
    chi_values: list[Optional[float]] = []
    for naa in naa_grid:
        m_star = find_equilibrium_m(beta_j, alpha_hat, float(naa))
        chi_values.append(susceptibility(m_star, beta_j, alpha_hat, float(naa)))

    return {
        "naa": naa_grid.tolist(),
        "chi": chi_values,
        "beta_j": float(beta_j),
        "alpha_hat": float(alpha_hat),
    }
