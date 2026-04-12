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
    when beta_J > 1 (ferromagnetic regime, two stable roots). Starting
    from m_0 = 0 with no external field selects the m=0 root for
    paramagnetic systems and the m > 0 root for ferromagnetic systems
    with positive h.
    """
    h = beta * alpha_hat * naa
    m = 0.0
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
    """Landau free energy F(m) from eq. (10).

    F(m) = a(T) * m^2 + b * m^4 - h * m

    with a(T) = 1 - beta_J, b = (beta_J)^3 / 3, h = beta * alpha_hat * NAA.

    The double-well structure appears when a(T) < 0, i.e. beta_J > 1.
    """
    a = 1.0 - beta_j
    b = (beta_j ** 3) / 3.0
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

    Returns ``None`` when the denominator is within machine epsilon of
    zero (the susceptibility diverges at the critical point and there
    is no finite numerical answer to report).
    """
    arg = beta_j * m_star + beta * alpha_hat * naa
    sech2 = 1.0 / (np.cosh(arg) ** 2)
    numerator = beta * sech2
    denominator = 1.0 - beta_j * sech2
    if abs(denominator) < 1e-12:
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
