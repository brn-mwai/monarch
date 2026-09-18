"""Ask whether the between-session sign reversals need any explanation beyond the
session noise that was already measured (section 6.5).

51 of 400 items reverse the sign of ``naa_signed`` between the two scanning sessions. The
number is reported in the thesis but not explained, and three mechanisms are available:
speech synthesis, which is re-run per session and can fall back to a different TTS model
entirely; forced alignment over that audio; and GPU nondeterminism in the encoder. Telling
them apart needs a controlled re-run and a GPU.

One question is answerable from the two session files alone, and it is the question that
decides whether a re-run is even looking for something. Under a plain additive-noise model,
where each session measures an item's value with independent error of the size the
test-retest already established, a predictable number of items reverse purely because their
value sits near zero. If the observed count matches that prediction, the reversals are the
scatter already reported acting where the sign is undetermined, not a separate pathology, and
a controlled re-run is a question about the size of sigma rather than about a defect. If the
observed count exceeds it, something is moving items that the paired standard deviation does
not account for.

The noise scale is not assumed. sigma is derived from the paired differences of the two
sessions, and the true per-item spread is estimated by removing that noise variance from the
observed variance of the session means, so no item's own noise is used to predict its own
reversal.

Usage
-----
    python scripts/reversal_diagnosis.py \
        --run-a data/final/corpus_naa.csv \
        --run-b data/final/corpus_naa_run_b.csv \
        --out data/final/reversal_diagnosis.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

COLUMN = "naa_signed"
KEY = "id"
DRAWS = 20000
SEED = 42


def _paired(run_a: Path, run_b: Path) -> pd.DataFrame:
    a = pd.read_csv(run_a)[[KEY, "category", COLUMN]].rename(columns={COLUMN: "a"})
    b = pd.read_csv(run_b)[[KEY, COLUMN]].rename(columns={COLUMN: "b"})
    merged = a.merge(b, on=KEY, how="inner")
    if merged.shape[0] != a.shape[0]:
        raise ValueError(f"{a.shape[0]} items in run A, {merged.shape[0]} matched in run B")
    return merged


def _shrunk_truth(means: np.ndarray, sigma: float) -> tuple[np.ndarray, float]:
    """Empirical-Bayes estimate of each item's session-free value.

    The session means carry error sigma/sqrt(2). Subtracting that variance from their
    observed variance leaves the between-item variance, and the ratio is the shrinkage that
    stops the plug-in estimate from inheriting the noise it is meant to predict.
    """
    mean_error_var = sigma**2 / 2.0
    between_var = max(float(np.var(means, ddof=1)) - mean_error_var, 0.0)
    weight = between_var / (between_var + mean_error_var) if between_var > 0 else 0.0
    grand = float(np.mean(means))
    return grand + weight * (means - grand), float(np.sqrt(between_var))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-a", type=Path, required=True)
    parser.add_argument("--run-b", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    paired = _paired(args.run_a, args.run_b)
    a = paired["a"].to_numpy()
    b = paired["b"].to_numpy()
    n = a.shape[0]

    difference = a - b
    sd_difference = float(np.std(difference, ddof=1))
    sigma = sd_difference / np.sqrt(2.0)
    reversed_mask = np.sign(a) != np.sign(b)
    observed = int(reversed_mask.sum())

    means = (a + b) / 2.0
    truth, between_sd = _shrunk_truth(means, sigma)
    below_zero = stats.norm.cdf(0.0, loc=truth, scale=sigma)
    flip_probability = 2.0 * below_zero * (1.0 - below_zero)
    expected = float(flip_probability.sum())

    rng = np.random.default_rng(SEED)
    simulated = rng.binomial(1, flip_probability, size=(DRAWS, n)).sum(axis=1)
    interval = [float(np.percentile(simulated, 2.5)), float(np.percentile(simulated, 97.5))]
    tail = float(np.mean(simulated >= observed))

    reversed_abs = np.abs(means[reversed_mask])
    stable_abs = np.abs(means[~reversed_mask])
    magnitude = stats.mannwhitneyu(reversed_abs, stable_abs, alternative="less")

    by_category = {
        str(category): {
            "n": int(block.shape[0]),
            "reversed": int((np.sign(block["a"]) != np.sign(block["b"])).sum()),
        }
        for category, block in paired.groupby("category")
    }
    category_table = np.array(
        [[v["reversed"], v["n"] - v["reversed"]] for v in by_category.values()]
    )
    chi2, chi_p = stats.chi2_contingency(category_table)[:2]

    payload = {
        "n_items": n,
        "sd_difference": sd_difference,
        "sigma_per_session": float(sigma),
        "between_item_sd": between_sd,
        "observed_reversals": observed,
        "observed_rate": observed / n,
        "expected_reversals": expected,
        "expected_interval95": interval,
        "tail_probability_at_least_observed": tail,
        "mean_abs_value_reversed": float(reversed_abs.mean()),
        "mean_abs_value_stable": float(stable_abs.mean()),
        "magnitude_test": {"u": float(magnitude.statistic), "p": float(magnitude.pvalue)},
        "by_category": by_category,
        "category_homogeneity": {"chi2": float(chi2), "p": float(chi_p)},
        "seed": SEED,
        "draws": DRAWS,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"items paired                {n}")
    print(f"sd of paired difference     {sd_difference:.5f}")
    print(f"implied per-session sigma   {sigma:.5f}")
    print(f"between-item sd (denoised)  {between_sd:.5f}")
    print("")
    print(f"observed reversals          {observed} ({observed / n:.3%})")
    print(f"expected under noise alone  {expected:.1f}  95% [{interval[0]:.0f}, {interval[1]:.0f}]")
    print(f"P(simulated >= observed)    {tail:.4f}")
    print("")
    print(f"mean |value|, reversed      {reversed_abs.mean():.5f}")
    print(f"mean |value|, stable        {stable_abs.mean():.5f}")
    print(f"reversed items nearer zero  U={magnitude.statistic:.0f}  p={magnitude.pvalue:.3e}")
    print("")
    for category, block in by_category.items():
        print(f"{category:<24}{block['reversed']:>4} of {block['n']}")
    print(f"category homogeneity        chi2={chi2:.3f}  p={chi_p:.4f}")
    print(f"written to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
