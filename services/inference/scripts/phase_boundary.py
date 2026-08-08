"""Paper 1's figure set: phase structure, critical exponents, and the field bound.

No GPU, no corpus, no measurement. Everything here follows from the mean-field Ising
solver already in ``landau.py`` and ``phase_map.py``, so it can be produced before the
scan finishes and stands whatever the scan returns.

Three things come out:

**The solver checked against exact results.** Mean-field theory fixes three exponents,
``beta = 1/2``, ``gamma = 1``, ``delta = 3``. Recovering them numerically is what
licenses every later figure drawn with the same solver. They are fitted here, printed
with their residuals, and the run fails if any is off by more than ``--exponent-tol``.

**The phase diagram.** Where in ``(beta_J, h)`` two stable opinions coexist, bounded by
the spinodal field ``h_c(beta_J)`` at which the second minimum disappears.

**The bound, which is the contribution.** For an observable ``X`` used as a field,
``h = alpha X``, no media-driven transition is possible unless

    alpha  >=  h_c(beta_J) / dX

so measuring the spread ``dX`` of any candidate observable bounds the coupling from
below without fitting anything. That inverts the usual procedure: rather than fitting
``alpha`` and hoping it clears zero, it states what ``alpha`` would have to be for the
mechanism to work at all, and it applies to any proposed field observable.

Usage
-----
    python scripts/phase_boundary.py --out-dir data/paper1
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.landau import (  # noqa: E402
    find_equilibrium_m,
    landau_free_energy,
    susceptibility,
)
from app.services.phase_map import (  # noqa: E402
    CRITICAL_BETA_J,
    critical_field,
    is_bistable,
)

# A field enters the solver as alpha * naa, so any (alpha, naa) pair with that product
# gives the same physics. Fixing naa = 1 makes alpha the field itself and keeps the
# exponent fits reading in the variable the theory is written in.
UNIT_NAA = 1.0


def solve_m(beta_j: float, h: float) -> float:
    """Stable root of m = tanh(beta_J m + h), by bracketing rather than iteration.

    ``find_equilibrium_m`` iterates the map directly, which is the right thing for the
    application but converges as a power of the step count at the critical point, where
    the map's derivative reaches one. The exponents are defined exactly there, so fitting
    them off iterated values reads the truncation error rather than the physics: the
    critical isotherm came out as delta = 1.35 against an exact 3.

    Bracketing has no such problem, so the exponents are fitted from this and the shipped
    solver is then checked against it away from criticality (``solver_agreement``).
    """
    from scipy.optimize import brentq

    def f(m: float) -> float:
        return np.tanh(beta_j * m + h) - m

    if h == 0.0 and beta_j <= CRITICAL_BETA_J:
        return 0.0
    lo = 1e-14 if h == 0.0 else 0.0
    if f(lo) <= 0.0:
        return 0.0
    return float(brentq(f, lo, 1.0, xtol=1e-15, rtol=1e-15, maxiter=500))


def solver_agreement(points: int = 40) -> dict:
    """Largest gap between the shipped solver and the bracketed root, off criticality."""
    worst = 0.0
    where = None
    for beta_j in np.linspace(0.3, 2.0, points):
        if abs(beta_j - CRITICAL_BETA_J) < 0.02:
            continue
        for h in (0.0, 0.01, 0.1, 0.5):
            a = find_equilibrium_m(float(beta_j), h, UNIT_NAA)
            b = solve_m(float(beta_j), h)
            if abs(a - b) > worst:
                worst, where = abs(a - b), (float(beta_j), h)
    return {"max_abs_difference": worst, "at_beta_j_h": where}


def _fit_loglog(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    """Slope and intercept of log y against log x, positive entries only."""
    keep = (x > 0) & (y > 0) & np.isfinite(x) & np.isfinite(y)
    slope, intercept = np.polyfit(np.log(x[keep]), np.log(y[keep]), 1)
    return float(slope), float(intercept)


def exponents(points: int = 60, window: float = 0.05) -> dict:
    """Fit the three mean-field exponents close to the critical point.

    Each is fitted inside a small window of the critical point, because the power laws
    are asymptotic: fit them too far out and the quartic term contaminates the slope.
    """
    # beta: m* ~ (beta_J - 1)^beta at zero field, approached from above.
    t = np.linspace(window / points, window, points)
    m_vals = np.array([solve_m(CRITICAL_BETA_J + ti, 0.0) for ti in t])
    beta_exp, _ = _fit_loglog(t, np.abs(m_vals))

    # gamma: chi ~ |beta_J - 1|^(-gamma), approached from below where the single root is
    # stable and the solver returns a finite susceptibility.
    chi_vals = []
    t_chi = []
    for ti in t:
        beta_j = CRITICAL_BETA_J - ti
        m = solve_m(beta_j, 0.0)
        chi = susceptibility(m, beta_j, 0.0, UNIT_NAA)
        if chi is not None and chi > 0:
            chi_vals.append(chi)
            t_chi.append(ti)
    gamma_slope, _ = _fit_loglog(np.array(t_chi), np.array(chi_vals))
    gamma_exp = -gamma_slope

    # delta: at criticality, m ~ h^(1/delta).
    h = np.logspace(-6, -3, points)
    m_h = np.array([solve_m(CRITICAL_BETA_J, hi) for hi in h])
    inv_delta, _ = _fit_loglog(h, m_h)
    delta_exp = 1.0 / inv_delta if inv_delta else float("inf")

    return {
        "beta": {"fitted": beta_exp, "exact": 0.5, "error": abs(beta_exp - 0.5)},
        "gamma": {"fitted": gamma_exp, "exact": 1.0, "error": abs(gamma_exp - 1.0)},
        "delta": {"fitted": delta_exp, "exact": 3.0, "error": abs(delta_exp - 3.0)},
        "window": window,
        "points": points,
    }


def boundary(beta_j_values: np.ndarray) -> dict:
    """Spinodal field against coupling, defined only above the critical point."""
    fields = []
    for beta_j in beta_j_values:
        h_c = critical_field(float(beta_j))
        fields.append(float("nan") if h_c is None else h_c)
    return {"beta_j": beta_j_values.tolist(), "h_c": fields}


def alpha_required(h_c: np.ndarray, spreads: list[float]) -> dict:
    """Coupling a candidate observable must exceed, per unit of its spread."""
    return {f"{s:g}": (h_c / s).tolist() for s in spreads}


def _save(fig, out_dir: Path, stem: str, formats: list[str]) -> None:
    """Write one figure in every requested format.

    Journals want vector; the repo and the site want a raster to look at. Both come off
    the same figure object so they cannot drift apart.
    """
    for fmt in formats:
        fig.savefig(out_dir / f"{stem}.{fmt}", dpi=200 if fmt == "png" else None,
                    format=fmt, bbox_inches="tight")


def _figures(out_dir: Path, exps: dict, bnd: dict, spreads: list[float],
             formats: list[str]) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # Type 42 keeps text as text in the PDF, which is what production desks require;
    # the default Type 3 subsets glyphs and fails preflight at several journals.
    matplotlib.rcParams["pdf.fonttype"] = 42
    matplotlib.rcParams["ps.fonttype"] = 42
    matplotlib.rcParams["svg.fonttype"] = "none"

    beta_j = np.asarray(bnd["beta_j"])
    h_c = np.asarray(bnd["h_c"])

    # F1: the free energy splitting.
    m = np.linspace(-1.0, 1.0, 601)
    fig, ax = plt.subplots(figsize=(5.5, 3.8))
    for bj, style in ((0.8, "-"), (1.0, "--"), (1.4, "-.")):
        ax.plot(m, landau_free_energy(m, beta_j=bj, alpha_hat=0.0, naa=UNIT_NAA),
                style, lw=1.4, label=rf"$\beta J$ = {bj}")
    ax.set_xlabel("m"); ax.set_ylabel("F(m)")
    ax.set_title("Free energy at zero field", fontsize=10)
    ax.legend(fontsize=8)
    fig.tight_layout(); _save(fig, out_dir, "F1_free_energy", formats); plt.close(fig)

    # F2: order parameter, with the fitted exponent stated on the figure.
    t = np.linspace(1e-4, 0.4, 200)
    m_star = [solve_m(CRITICAL_BETA_J + ti, 0.0) for ti in t]
    fig, ax = plt.subplots(figsize=(5.5, 3.8))
    ax.plot(CRITICAL_BETA_J + t, m_star, lw=1.5)
    ax.plot(CRITICAL_BETA_J - t, np.zeros_like(t), lw=1.5, color="C0")
    ax.axvline(CRITICAL_BETA_J, lw=0.8, ls=":", color="grey")
    ax.set_xlabel(r"$\beta J$"); ax.set_ylabel(r"$m^*$")
    ax.set_title(rf"Order parameter, fitted $\beta$ = {exps['beta']['fitted']:.3f} (exact 1/2)",
                 fontsize=10)
    fig.tight_layout(); _save(fig, out_dir, "F2_order_parameter", formats); plt.close(fig)

    # F3: susceptibility divergence.
    t3 = np.logspace(-4, -1, 120)
    chi = []
    for ti in t3:
        bj = CRITICAL_BETA_J - ti
        chi.append(susceptibility(solve_m(bj, 0.0), bj, 0.0, UNIT_NAA))
    fig, ax = plt.subplots(figsize=(5.5, 3.8))
    ax.loglog(t3, chi, lw=1.5)
    ax.set_xlabel(r"$1 - \beta J$"); ax.set_ylabel(r"$\chi$")
    ax.set_title(rf"Susceptibility, fitted $\gamma$ = {exps['gamma']['fitted']:.3f} (exact 1)",
                 fontsize=10)
    fig.tight_layout(); _save(fig, out_dir, "F3_susceptibility", formats); plt.close(fig)

    # F4: critical isotherm.
    h = np.logspace(-6, -2, 120)
    m_h = [solve_m(CRITICAL_BETA_J, hi) for hi in h]
    fig, ax = plt.subplots(figsize=(5.5, 3.8))
    ax.loglog(h, m_h, lw=1.5)
    ax.set_xlabel("h"); ax.set_ylabel("m")
    ax.set_title(rf"Critical isotherm, fitted $\delta$ = {exps['delta']['fitted']:.3f} (exact 3)",
                 fontsize=10)
    fig.tight_layout(); _save(fig, out_dir, "F4_critical_isotherm", formats); plt.close(fig)

    # F5: the phase diagram.
    fig, ax = plt.subplots(figsize=(5.8, 4.0))
    ax.plot(beta_j, h_c, lw=1.6, color="C3", label=r"spinodal $h_c(\beta J)$")
    ax.fill_between(beta_j, 0, h_c, alpha=0.18, color="C3", label="bistable")
    ax.set_xlabel(r"$\beta J$"); ax.set_ylabel("h")
    ax.set_title("Phase diagram: where two opinions coexist", fontsize=10)
    ax.legend(fontsize=8)
    fig.tight_layout(); _save(fig, out_dir, "F5_phase_diagram", formats); plt.close(fig)

    # F6: the bound.
    fig, ax = plt.subplots(figsize=(5.8, 4.0))
    for s in spreads:
        ax.plot(beta_j, h_c / s, lw=1.4, label=rf"$\Delta X$ = {s:g}")
    ax.set_xlabel(r"$\beta J$"); ax.set_ylabel(r"$\alpha$ required")
    ax.set_title(r"Coupling needed before media can drive a transition", fontsize=10)
    ax.legend(fontsize=8, title="observable spread", title_fontsize=8)
    fig.tight_layout(); _save(fig, out_dir, "F6_alpha_required", formats); plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--beta-j-max", type=float, default=2.0)
    parser.add_argument("--points", type=int, default=120)
    parser.add_argument("--spreads", default="0.1,0.5,1.0,2.0")
    parser.add_argument("--exponent-tol", type=float, default=0.05)
    parser.add_argument("--formats", default="png,pdf",
                        help="comma-separated figure formats; pdf and svg are vector")
    args = parser.parse_args()

    spreads = [float(s) for s in args.spreads.split(",") if s.strip()]
    formats = [f.strip().lower() for f in args.formats.split(",") if f.strip()]
    unknown = [f for f in formats if f not in ("png", "pdf", "svg", "eps")]
    if unknown:
        print(f"[FAIL] unsupported format(s): {', '.join(unknown)}", file=sys.stderr)
        return 1
    args.out_dir.mkdir(parents=True, exist_ok=True)

    exps = exponents()
    beta_j_values = np.linspace(CRITICAL_BETA_J + 1e-3, args.beta_j_max, args.points)
    bnd = boundary(beta_j_values)
    h_c = np.asarray(bnd["h_c"])

    _figures(args.out_dir, exps, bnd, spreads, formats)

    result = {
        "exponents": exps,
        "solver_agreement": solver_agreement(),
        "critical_beta_j": CRITICAL_BETA_J,
        "phase_boundary": bnd,
        "alpha_required_per_spread": alpha_required(h_c, spreads),
        "bistable_at_zero_field_above_critical": bool(is_bistable(1.5, 0.0)),
    }
    (args.out_dir / "phase_boundary.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )

    print("mean-field exponents, fitted against exact values:")
    worst = 0.0
    for name, d in exps.items():
        if name in ("window", "points"):
            continue
        print(f"  {name:6s} fitted={d['fitted']:.4f}  exact={d['exact']:.1f}  error={d['error']:.4f}")
        worst = max(worst, d["error"])

    print(f"\nspinodal field: h_c({beta_j_values[0]:.3f}) = {h_c[0]:.5f}"
          f"  ..  h_c({beta_j_values[-1]:.2f}) = {h_c[-1]:.5f}")
    for s in spreads:
        print(f"  observable spread {s:>4g}: alpha must exceed {h_c[-1] / s:.4f} "
              f"at beta_J = {args.beta_j_max:g}")

    print(f"\nWrote {args.out_dir}/ : phase_boundary.json and 6 figures "
          f"in {', '.join(formats)}")

    # The exponents are the check that licenses every other figure here, so a solver that
    # misses them fails the run rather than publishing curves nobody verified.
    if worst > args.exponent_tol:
        print(f"\n[FAIL] exponent error {worst:.4f} exceeds tolerance {args.exponent_tol}",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
