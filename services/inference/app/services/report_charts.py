"""Matplotlib chart renderers for the PDF report.

Each function returns PNG bytes so the reportlab layer can embed them without
touching matplotlib. Uses the non-interactive Agg backend and a shared
monochrome-plus-fire style so every figure reads as one system.
"""

from __future__ import annotations

import io
import math

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Wedge  # noqa: E402

INK = "#111111"
GREY = "#8a8a8a"
LIGHT = "#dddddd"
FIRE = "#f0642c"
AMBER = "#f2b705"
GREEN = "#5aa469"
AFFECTIVE = "#f0642c"
DELIBERATIVE = "#5b6472"


def _figure_to_png(fig, dpi: int = 200) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight", transparent=True)
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def _base_axes(ax) -> None:
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(LIGHT)
    ax.tick_params(colors=GREY, labelsize=8, length=3)
    ax.set_facecolor("none")


def naa_gauge_png(naa: float) -> bytes:
    """Semicircular gauge, 0..5, with green/amber/red zones and a needle."""
    fig, ax = plt.subplots(figsize=(4.6, 2.6), subplot_kw={"aspect": "equal"})
    ax.axis("off")
    zones = [(0.0, 1.0, GREEN), (1.0, 2.0, AMBER), (2.0, 5.0, FIRE)]
    for lo, hi, color in zones:
        ax.add_patch(
            Wedge((0, 0), 1.0, 180 - hi / 5 * 180, 180 - lo / 5 * 180, width=0.32, facecolor=color)
        )
    for tick in range(6):
        angle = math.radians(180 - tick / 5 * 180)
        ax.text(1.16 * math.cos(angle), 1.16 * math.sin(angle), str(tick),
                ha="center", va="center", fontsize=8, color=GREY)
    naa_clamped = max(0.0, min(5.0, naa))
    needle = math.radians(180 - naa_clamped / 5 * 180)
    ax.plot([0, 0.86 * math.cos(needle)], [0, 0.86 * math.sin(needle)],
            color=INK, linewidth=2.4, solid_capstyle="round")
    ax.add_patch(plt.Circle((0, 0), 0.045, color=INK))
    ax.text(0, -0.28, f"{naa:.2f}", ha="center", va="center", fontsize=26,
            fontweight="bold", color=INK)
    ax.text(0, -0.5, "NAA", ha="center", va="center", fontsize=9, color=GREY,
            fontfamily="monospace")
    ax.set_xlim(-1.3, 1.3)
    ax.set_ylim(-0.6, 1.3)
    return _figure_to_png(fig)


def landau_curve_png(landau: dict) -> bytes:
    """Landau free-energy F(m) with the equilibrium m* marked."""
    m = np.array(landau.get("free_energy_m") or landau.get("free_energy", {}).get("m") or [])
    f = np.array(landau.get("free_energy_F") or landau.get("free_energy", {}).get("F") or [])
    fig, ax = plt.subplots(figsize=(4.8, 2.7))
    _base_axes(ax)
    if m.size and f.size:
        ax.plot(m, f, color=INK, linewidth=2)
        eq = landau.get("equilibrium_m")
        if eq is not None:
            fi = float(np.interp(eq, m, f))
            ax.plot([eq], [fi], "o", color=FIRE, markersize=7, zorder=5)
            ax.annotate(f"m* = {eq:.3f}", (eq, fi), textcoords="offset points",
                        xytext=(8, 8), fontsize=8, color=FIRE)
    ax.set_xlabel(r"polarisation $m$", fontsize=9, color=INK)
    ax.set_ylabel(r"free energy $F(m)$", fontsize=9, color=INK)
    return _figure_to_png(fig)


def susceptibility_curve_png(naa: float, beta_j: float, alpha_hat: float) -> bytes:
    """chi(NAA) with the scanned item marked."""
    x = np.linspace(0.01, 5.0, 240)
    # low-field susceptibility of the mean-field Ising model
    denom = np.maximum(1e-6, 1.0 - beta_j * (1.0 - np.tanh(alpha_hat * x) ** 2))
    chi = (1.0 - np.tanh(alpha_hat * x) ** 2) / denom
    fig, ax = plt.subplots(figsize=(4.8, 2.7))
    _base_axes(ax)
    ax.plot(x, chi, color=INK, linewidth=2)
    yi = float(np.interp(max(0.01, naa), x, chi))
    ax.axvline(naa, color=FIRE, linestyle="--", linewidth=1.2)
    ax.plot([naa], [yi], "o", color=FIRE, markersize=7, zorder=5)
    ax.annotate(f"this item\nNAA = {naa:.2f}", (naa, yi), textcoords="offset points",
                xytext=(8, 4), fontsize=8, color=FIRE)
    ax.set_xlabel("NAA", fontsize=9, color=INK)
    ax.set_ylabel(r"susceptibility $\chi$", fontsize=9, color=INK)
    return _figure_to_png(fig)


def methodology_png() -> bytes:
    """The key equations (LaTeX via mathtext) each with a plain-language gloss."""
    # (equation, plain gloss, y-centre). The NAA fraction is tall, so it gets
    # extra vertical room above the next row.
    rows = [
        (r"$\mathrm{NAA} = \dfrac{A_{\mathrm{emotion}}}{A_{\mathrm{reasoning}} + \delta}$",
         "how much the content leans on emotion vs reasoning", 0.86),
        (r"$H = \hat{\alpha}\,\cdot\,\mathrm{NAA}$",
         "the pull this content exerts on opinion", 0.58),
        (r"$m = \tanh(\beta_J\, m + \hat{\alpha}\,\mathrm{NAA})$",
         "where collective opinion settles", 0.36),
        (r"$F(m) = a\,m^{2} + b\,m^{4} - h\,m$",
         "the opinion energy landscape it tilts", 0.14),
    ]
    fig, ax = plt.subplots(figsize=(6.8, 2.9))
    ax.axis("off")
    for eq, gloss, y in rows:
        ax.text(0.02, y, eq, fontsize=13, color=INK, va="center", ha="left")
        ax.text(0.60, y, gloss, fontsize=8.5, color=GREY, va="center", ha="left")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    return _figure_to_png(fig)


def roi_bars_png(roi_breakdown: dict, top_k: int = 6) -> bytes:
    """Horizontal bars of the most-engaged affective vs deliberative ROIs."""
    rows = sorted(roi_breakdown.items(), key=lambda kv: kv[1]["activation"], reverse=True)
    rows = rows[: top_k * 2]
    names = [r[0] for r in rows][::-1]
    vals = [r[1]["activation"] for r in rows][::-1]
    colors = [AFFECTIVE if r[1]["system"] == "affective" else DELIBERATIVE for r in rows][::-1]
    fig, ax = plt.subplots(figsize=(4.8, 3.0))
    _base_axes(ax)
    ax.barh(range(len(names)), vals, color=colors, height=0.66)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=8, fontfamily="monospace", color=INK)
    ax.set_xlabel("mean predicted activation", fontsize=9, color=INK)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=AFFECTIVE, label="affective"),
                       Patch(color=DELIBERATIVE, label="deliberative")],
              loc="lower right", fontsize=8, frameon=False)
    return _figure_to_png(fig)
