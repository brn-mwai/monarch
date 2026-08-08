"""What the corpus can detect, computed before the corpus decides anything.

Both prior runs point at a null, and a null is only publishable with a power statement
attached: "we found no separation" means nothing until it is paired with "an effect of at
least this size would have been detected". This module supplies the second half for the two
tests the thesis actually runs, RQ II's category ANOVA and RQ I's classifier AUC.

Nothing here reads the scan. It answers what a design of a given size is capable of, which
is a property of the design, so it can be computed and reported before the data land and
cannot be tuned afterwards to flatter whatever arrived.
"""

from __future__ import annotations

import numpy as np
from scipy import stats

DEFAULT_ALPHA = 0.05
DEFAULT_TARGET_POWER = 0.80


def anova_power(
    n_per_group: int,
    n_groups: int,
    eta_squared: float,
    alpha: float = DEFAULT_ALPHA,
) -> float:
    """Power of a one-way ANOVA to reject equal means, at a given effect size.

    Cohen's ``f^2 = eta^2 / (1 - eta^2)`` and the noncentrality is ``f^2 * N``, which is the
    standard fixed-effects form; the test statistic is then noncentral F under the
    alternative.
    """
    if n_per_group < 2:
        raise ValueError(f"need at least 2 per group, got {n_per_group}")
    if n_groups < 2:
        raise ValueError(f"need at least 2 groups, got {n_groups}")
    if not 0.0 <= eta_squared < 1.0:
        raise ValueError(f"eta_squared must be in [0, 1), got {eta_squared}")

    total = n_per_group * n_groups
    df_between = n_groups - 1
    df_within = total - n_groups
    if eta_squared == 0.0:
        return alpha

    noncentrality = (eta_squared / (1.0 - eta_squared)) * total
    critical = stats.f.ppf(1.0 - alpha, df_between, df_within)
    return float(stats.ncf.sf(critical, df_between, df_within, noncentrality))


def anova_minimum_detectable_eta_squared(
    n_per_group: int,
    n_groups: int,
    alpha: float = DEFAULT_ALPHA,
    target_power: float = DEFAULT_TARGET_POWER,
) -> float:
    """Smallest eta^2 the design detects at ``target_power``.

    Found by bisection on ``anova_power``, which is monotone in the effect size, rather than
    by inverting the noncentral F in closed form.
    """
    low, high = 0.0, 0.999
    for _ in range(200):
        mid = 0.5 * (low + high)
        if anova_power(n_per_group, n_groups, mid, alpha) < target_power:
            low = mid
        else:
            high = mid
    return 0.5 * (low + high)


def auc_from_separation(separation: float) -> float:
    """Binormal AUC for two unit-variance populations a distance ``separation`` apart."""
    return float(stats.norm.cdf(separation / np.sqrt(2.0)))


def separation_from_auc(auc: float) -> float:
    """Inverse of :func:`auc_from_separation`."""
    if not 0.0 < auc < 1.0:
        raise ValueError(f"auc must be in (0, 1), got {auc}")
    return float(np.sqrt(2.0) * stats.norm.ppf(auc))


def auc_power(
    n_positive: int,
    n_negative: int,
    auc: float,
    alpha: float = DEFAULT_ALPHA,
    n_simulations: int = 2000,
    seed: int = 0,
) -> float:
    """Power to reject AUC = 0.5, by simulation under a binormal alternative.

    Simulated rather than taken from a closed form because the closed forms differ in their
    variance assumptions at the small sample sizes and unbalanced class ratios this corpus
    has, and a simulation states its assumptions in code where they can be read.

    The test is the two-sided Mann-Whitney U, which is the rank test whose statistic is the
    AUC, so power here is power for the quantity actually reported.
    """
    if n_positive < 2 or n_negative < 2:
        raise ValueError("need at least 2 in each class")

    rng = np.random.default_rng(seed)
    separation = separation_from_auc(auc)

    rejections = 0
    for _ in range(n_simulations):
        positives = rng.normal(loc=separation, size=n_positive)
        negatives = rng.normal(loc=0.0, size=n_negative)
        _, p_value = stats.mannwhitneyu(positives, negatives, alternative="two-sided")
        if p_value < alpha:
            rejections += 1
    return rejections / n_simulations


def auc_minimum_detectable(
    n_positive: int,
    n_negative: int,
    alpha: float = DEFAULT_ALPHA,
    target_power: float = DEFAULT_TARGET_POWER,
    n_simulations: int = 2000,
    seed: int = 0,
    tolerance: float = 0.005,
) -> float:
    """Smallest AUC above 0.5 the design detects at ``target_power``.

    Bisection again, on a simulated power curve that is monotone in AUC up to Monte Carlo
    noise; ``tolerance`` stops the search where further refinement would be reading that
    noise rather than the curve.
    """
    low, high = 0.5 + 1e-6, 0.999
    while high - low > tolerance:
        mid = 0.5 * (low + high)
        if auc_power(n_positive, n_negative, mid, alpha, n_simulations, seed) < target_power:
            low = mid
        else:
            high = mid
    return 0.5 * (low + high)


def statement(
    n_per_group: int,
    n_groups: int,
    n_positive: int,
    n_negative: int,
    alpha: float = DEFAULT_ALPHA,
    target_power: float = DEFAULT_TARGET_POWER,
    seed: int = 0,
) -> dict:
    """Everything a null result in this design has to be reported alongside."""
    mde_eta = anova_minimum_detectable_eta_squared(n_per_group, n_groups, alpha, target_power)
    mde_auc = auc_minimum_detectable(n_positive, n_negative, alpha, target_power, seed=seed)
    return {
        "alpha": alpha,
        "target_power": target_power,
        "anova": {
            "n_per_group": n_per_group,
            "n_groups": n_groups,
            "n_total": n_per_group * n_groups,
            "minimum_detectable_eta_squared": mde_eta,
            "minimum_detectable_cohens_f": float(np.sqrt(mde_eta / (1.0 - mde_eta))),
        },
        "auc": {
            "n_positive": n_positive,
            "n_negative": n_negative,
            "minimum_detectable_auc": mde_auc,
            "minimum_detectable_separation": separation_from_auc(mde_auc),
            "seed": seed,
        },
    }
