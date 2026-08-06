"""Phase boundary map in (beta_J, NAA) space. Proposal objective (v), final piece.

The single-NAA analysis in ``landau.py`` answers "where does this one article
put the population". This sweeps the plane instead, so RQ III can be answered
as a structure rather than as a list of points: for every social coupling
``beta_J`` and every field strength, where does the system sit, and where does
it change character.

Why this is presented as a function of alpha rather than at one calibrated value
--------------------------------------------------------------------------------
The field is ``h = alpha * NAA``. Two independent calibration runs returned an
``alpha_hat`` whose confidence interval straddles zero, so no value is quoted
anywhere in this project. The sweep therefore takes ``alpha`` as a parameter and
the caller varies it across a plausible range. That is the honest form of the
answer: the phase structure is fully determined, the absolute field scale is not
constrained by this corpus.

What the map reports at each grid point
---------------------------------------
- ``m_star``: equilibrium polarisation
- ``chi``: susceptibility, ``None`` where it diverges or is evaluated off the
  stable branch
- ``regime``: ``paramagnetic`` below beta_J = 1, ``ferromagnetic`` above. The
  boundary at beta_J = 1 is where a::= (1 - beta_J)/2 changes sign and the
  free energy develops a double well.
- ``bistable``: whether both signs of seed converge to distinct stable roots.
  Bistability is the physically interesting region: the same media field can
  leave the population in either of two states depending on history.
"""

from __future__ import annotations

from typing import Optional

import numpy as np

from .landau import find_equilibrium_m, susceptibility

CRITICAL_BETA_J = 1.0
BISTABILITY_TOL = 1e-6


def _self_consistency_residual(m: np.ndarray, beta_j: float, field: float) -> np.ndarray:
    return np.tanh(beta_j * m + field) - m


def stable_roots(beta_j: float, field: float, grid_points: int = 2001) -> list[float]:
    """Every stable solution of ``m = tanh(beta_J*m + h)`` on [-1, 1].

    Roots are located by sign changes of the residual on a dense grid and
    refined by bisection, then filtered for stability via the derivative
    condition ``beta_J * sech^2(beta_J*m + h) < 1``.

    Fixed-point iteration is deliberately NOT used here. It suffers critical
    slowing down as beta_J approaches 1: convergence goes as beta_J^n, so at
    beta_J = 0.99 a thousand iterations still leave a residual near 4e-5, and
    two seeds that both genuinely converge to m = 0 look like two distinct
    roots. That produced a false bistable region hugging the phase boundary,
    which is exactly where the map needs to be trustworthy.
    """
    grid = np.linspace(-1.0, 1.0, grid_points)
    residual = _self_consistency_residual(grid, beta_j, field)

    roots: list[float] = []
    for index in range(len(grid) - 1):
        left, right = residual[index], residual[index + 1]
        if left == 0.0:
            roots.append(float(grid[index]))
            continue
        if left * right > 0.0:
            continue
        low, high = float(grid[index]), float(grid[index + 1])
        for _ in range(100):
            mid = 0.5 * (low + high)
            if _self_consistency_residual(np.array([mid]), beta_j, field)[0] * left > 0:
                low = mid
            else:
                high = mid
        roots.append(0.5 * (low + high))

    stable: list[float] = []
    for root in roots:
        slope = beta_j / np.cosh(beta_j * root + field) ** 2
        if slope < 1.0 and all(abs(root - kept) > BISTABILITY_TOL for kept in stable):
            stable.append(root)
    return stable


def is_bistable(beta_j: float, field: float) -> bool:
    """True when the self-consistency equation has two stable solutions.

    Determined by counting roots rather than inferred from ``beta_j > 1``: a
    strong enough field collapses the double well back to a single minimum
    even in the ferromagnetic regime, and that collapse is the interesting
    part of the map, not an edge case to assume away.
    """
    return len(stable_roots(beta_j, field)) >= 2


def sweep(
    naa_values: np.ndarray,
    beta_j_values: np.ndarray,
    alpha: float,
) -> dict:
    """Evaluate the Landau/Ising state on the (beta_J, NAA) grid.

    Arrays are returned grid-major as ``[beta_j_index][naa_index]`` so a
    heatmap can be drawn without transposing.
    """
    if naa_values.ndim != 1 or beta_j_values.ndim != 1:
        raise ValueError("naa_values and beta_j_values must be 1-D")

    m_star: list[list[float]] = []
    chi: list[list[Optional[float]]] = []
    bistable: list[list[bool]] = []

    for beta_j in beta_j_values:
        m_row: list[float] = []
        chi_row: list[Optional[float]] = []
        bistable_row: list[bool] = []
        for naa in naa_values:
            field = alpha * float(naa)
            m = find_equilibrium_m(float(beta_j), alpha, float(naa))
            m_row.append(float(m))
            chi_row.append(susceptibility(m, float(beta_j), alpha, float(naa)))
            bistable_row.append(is_bistable(float(beta_j), field))
        m_star.append(m_row)
        chi.append(chi_row)
        bistable.append(bistable_row)

    return {
        "naa": naa_values.tolist(),
        "beta_j": beta_j_values.tolist(),
        "alpha": float(alpha),
        "m_star": m_star,
        "susceptibility": chi,
        "bistable": bistable,
        "critical_beta_j": CRITICAL_BETA_J,
    }


def critical_field(beta_j: float) -> Optional[float]:
    """Field magnitude at which bistability collapses, for beta_J > 1.

    Above ``beta_J = 1`` the free energy has two minima at zero field. Raising
    the field deepens one and eventually destroys the other; the value where
    the second minimum disappears is the spinodal. It is located by bisection
    on ``is_bistable`` rather than in closed form, which keeps this consistent
    with the solver the rest of the module uses.

    Returns ``None`` in the paramagnetic regime, where there is no second
    minimum to destroy.
    """
    if beta_j <= CRITICAL_BETA_J:
        return None

    low, high = 0.0, 1.0
    while is_bistable(beta_j, high):
        high *= 2.0
        if high > 1e3:
            return None

    for _ in range(200):
        mid = 0.5 * (low + high)
        if is_bistable(beta_j, mid):
            low = mid
        else:
            high = mid
    return 0.5 * (low + high)


def compute_phase_map(
    naa_range: tuple[float, float] = (-1.0, 1.0),
    beta_j_range: tuple[float, float] = (0.1, 1.6),
    alpha: float = 1.0,
    naa_points: int = 81,
    beta_j_points: int = 61,
) -> dict:
    """Objective (v) deliverable: the phase map plus its spinodal boundary."""
    naa_values = np.linspace(*naa_range, naa_points)
    beta_j_values = np.linspace(*beta_j_range, beta_j_points)

    result = sweep(naa_values, beta_j_values, alpha)
    result["spinodal"] = [
        {"beta_j": float(b), "critical_field": critical_field(float(b))}
        for b in beta_j_values
    ]
    return result
