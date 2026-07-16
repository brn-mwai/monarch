"""Per-category NAA distribution statistics (proposal objective (iii), RQ II).

Answers RQ II: what is the statistical distribution of the NAA index across
content categories, and what is the KL divergence between them?

Everything here operates on a NAA column plus category labels. It is deliberately
agnostic to how NAA was defined: signed or ratio, cortical or subcortical. That
keeps it valid under any outcome of the observable amendment in
docs/PROPOSAL-AMENDMENT.md, and it is why this module can be written and tested
before the corpus scan exists.

``separation`` is the Gate 2 pilot test. Before spending ~31 GPU-hours on the
full 1,500-item scan, ~1 GPU-hour over 40 items answers the only question that
decides what RQ I and RQ II say: does NAA vary by category at all, or is the
between-category variance indistinguishable from the within-category noise? The
prior is not encouraging. Across both existing runs the signed NAA was negative
for 50/50 items with magnitude variation but no sign variation, which looks more
like a fixed baseline offset between two ROI unions than like a response to
content.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
from scipy import stats

MIN_GROUP = 2
KDE_GRID_POINTS = 512
KDE_GRID_PAD = 0.15
DENSITY_FLOOR = 1e-12


def describe(values: np.ndarray) -> dict:
    """Descriptive statistics for one category (§5.4).

    Skewness and excess kurtosis are reported because the proposal's
    interpretive scheme assumes a distribution that spreads across the balanced
    and affective-dominant regimes. A heavily skewed or near-degenerate
    distribution would mean the index is not discriminating content, and that
    has to be visible in the numbers rather than inferred from a mean.
    """
    x = np.asarray(values, dtype=np.float64)
    if x.size < MIN_GROUP:
        raise ValueError(f"need at least {MIN_GROUP} values, got {x.size}")

    return {
        "n": int(x.size),
        "mean": float(np.mean(x)),
        "sd": float(np.std(x, ddof=1)),
        "median": float(np.median(x)),
        "skewness": float(stats.skew(x)),
        "excess_kurtosis": float(stats.kurtosis(x)),
        "min": float(np.min(x)),
        "max": float(np.max(x)),
    }


def cohens_d(treatment: np.ndarray, baseline: np.ndarray) -> float:
    """Standardized mean difference against the neutral baseline (§5.4).

    Pooled-SD form. Positive means the treatment category sits above baseline.
    Returns 0.0 when both groups are constant and identical, and raises when the
    pooled SD vanishes with a non-zero mean difference, since the effect size is
    undefined rather than infinite there.
    """
    a = np.asarray(treatment, dtype=np.float64)
    b = np.asarray(baseline, dtype=np.float64)
    if a.size < MIN_GROUP or b.size < MIN_GROUP:
        raise ValueError("both groups need at least two values")

    va, vb = np.var(a, ddof=1), np.var(b, ddof=1)
    pooled = np.sqrt(((a.size - 1) * va + (b.size - 1) * vb) / (a.size + b.size - 2))
    difference = float(np.mean(a) - np.mean(b))

    if pooled == 0.0:
        if difference == 0.0:
            return 0.0
        raise ValueError("pooled SD is zero with a non-zero mean difference")
    return difference / float(pooled)


def _kde(values: np.ndarray) -> stats.gaussian_kde:
    """Silverman-bandwidth KDE, as §5.4 specifies."""
    x = np.asarray(values, dtype=np.float64)
    if np.ptp(x) == 0.0:
        raise ValueError("cannot fit a KDE to a constant sample")
    return stats.gaussian_kde(x, bw_method="silverman")


def _shared_grid(*samples: np.ndarray) -> np.ndarray:
    pooled = np.concatenate([np.asarray(s, dtype=np.float64).ravel() for s in samples])
    low, high = float(np.min(pooled)), float(np.max(pooled))
    pad = (high - low) * KDE_GRID_PAD
    return np.linspace(low - pad, high + pad, KDE_GRID_POINTS)


def shannon_entropy(values: np.ndarray) -> float:
    """Differential entropy H(P) of a category's NAA distribution (Eq. 16).

    Estimated by integrating the Silverman KDE over a padded grid. This is a
    DIFFERENTIAL entropy, so it is in nats, is not bounded below by zero, and is
    not scale-invariant: it shifts by log(c) if NAA is rescaled by c. That makes
    it comparable across categories, which is what §5.4 uses it for, but it is
    not comparable against entropies computed on a differently scaled index.
    """
    x = np.asarray(values, dtype=np.float64)
    if x.size < MIN_GROUP:
        raise ValueError(f"need at least {MIN_GROUP} values, got {x.size}")

    grid = _shared_grid(x)
    density = np.clip(_kde(x)(grid), DENSITY_FLOOR, None)
    return float(-np.trapezoid(density * np.log(density), grid))


def kl_divergence(sample_p: np.ndarray, sample_q: np.ndarray) -> float:
    """D_KL(P || Q) between two categories' NAA distributions (Eq. 17).

    Both densities are estimated with Silverman KDEs and integrated on a shared
    grid spanning the pooled support. Q is floored at DENSITY_FLOOR: the
    estimator is otherwise unbounded wherever P has mass and the Q sample does
    not, so a single outlier could dominate the result. The floor makes the
    quantity finite and reportable, at the cost of making large divergences
    dependent on the floor rather than on the data. Treat the ordering of KL
    values across categories as meaningful and the absolute magnitudes as
    bandwidth- and floor-dependent.

    Asymmetric by construction: D_KL(P||Q) != D_KL(Q||P). §5.4 always takes the
    neutral baseline as Q.
    """
    p = np.asarray(sample_p, dtype=np.float64)
    q = np.asarray(sample_q, dtype=np.float64)
    if p.size < MIN_GROUP or q.size < MIN_GROUP:
        raise ValueError("both samples need at least two values")

    grid = _shared_grid(p, q)
    density_p = np.clip(_kde(p)(grid), DENSITY_FLOOR, None)
    density_q = np.clip(_kde(q)(grid), DENSITY_FLOOR, None)
    density_p = density_p / np.trapezoid(density_p, grid)
    density_q = density_q / np.trapezoid(density_q, grid)

    integrand = density_p * np.log(density_p / density_q)
    return float(np.trapezoid(integrand, grid))


def separation(groups: dict[str, np.ndarray]) -> dict:
    """Between- vs within-category variance. The Gate 2 pilot test.

    One-way ANOVA plus eta squared, the share of total NAA variance explained by
    category. eta^2 is reported alongside F because with n=1,500 a trivial effect
    will reach significance: p answers "is there any difference at all", eta^2
    answers "is the difference large enough to matter", and only the second
    speaks to whether NAA is a usable order parameter.

    ``usable`` is deliberately conservative. It requires BOTH p < 0.05 and
    eta^2 >= 0.06 (Cohen's medium threshold). A significant but negligible
    effect is not a basis for claiming NAA discriminates manipulative content,
    and the paper should not present one as though it were.
    """
    usable_groups = {
        name: np.asarray(values, dtype=np.float64)
        for name, values in groups.items()
        if np.asarray(values).size >= MIN_GROUP
    }
    if len(usable_groups) < 2:
        raise ValueError("need at least two categories with two values each")

    arrays = list(usable_groups.values())
    f_statistic, p_value = stats.f_oneway(*arrays)

    pooled = np.concatenate(arrays)
    grand_mean = float(np.mean(pooled))
    ss_between = float(
        sum(a.size * (float(np.mean(a)) - grand_mean) ** 2 for a in arrays)
    )
    ss_total = float(np.sum((pooled - grand_mean) ** 2))
    eta_squared = ss_between / ss_total if ss_total > 0 else 0.0

    significant = bool(np.isfinite(p_value) and p_value < 0.05)
    return {
        "categories": list(usable_groups.keys()),
        "n_total": int(pooled.size),
        "f_statistic": float(f_statistic),
        "p_value": float(p_value),
        "eta_squared": float(eta_squared),
        "ss_between": ss_between,
        "ss_within": ss_total - ss_between,
        "significant": significant,
        "usable": bool(significant and eta_squared >= 0.06),
    }


def characterise(
    groups: dict[str, np.ndarray],
    baseline: str,
) -> dict:
    """Full RQ II answer: per-category stats, effect size, KL, entropy.

    ``baseline`` names the reference category (neutral_informational in §5.4);
    Cohen's d and KL are computed against it, and it is excluded from its own
    comparison.
    """
    if baseline not in groups:
        raise ValueError(f"baseline '{baseline}' not among {list(groups)}")

    reference = np.asarray(groups[baseline], dtype=np.float64)
    per_category: dict[str, dict] = {}

    for name, values in groups.items():
        x = np.asarray(values, dtype=np.float64)
        entry = describe(x)
        entry["entropy"] = _safe(lambda: shannon_entropy(x))
        if name != baseline:
            entry["cohens_d_vs_baseline"] = _safe(lambda: cohens_d(x, reference))
            entry["kl_vs_baseline"] = _safe(lambda: kl_divergence(x, reference))
        per_category[name] = entry

    return {
        "baseline": baseline,
        "per_category": per_category,
        "separation": separation(groups),
    }


def _safe(compute) -> Optional[float]:
    """Return None rather than raising when a sample cannot support a statistic.

    A constant or singleton category defeats the KDE. That is a real property of
    the data and must surface as an absent number in the report, never as a
    fabricated one.
    """
    try:
        return compute()
    except ValueError:
        return None
