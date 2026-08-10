"""Measure how much of the observable survives a second pass over the same corpus.

Two GPU sessions scanned the same items with the same code and the same ROI definitions.
That pair is a test-retest measurement, and it was never taken: every reported effect rests
on one session, so the question of how much of an item's score is the item and how much is
the session had no answer.

What it answers, in order of consequence
----------------------------------------
**Does the headline separation replicate?** The four-category ANOVA is recomputed on the
second session over the items both sessions share, and against the first session restricted
to the same items so the comparison is not confounded by sample size.

**How large is session noise against the signal it has to be read through?** The standard
deviation of the paired differences is reported beside the between-item standard deviation.
A ratio near one means an item's score is as much session as item.

**How often does the direction flip?** ``naa_signed`` is read as a direction, affective
leads or deliberative leads, so a sign flip between sessions is a qualitative disagreement
about that item, not a rounding difference.

Nothing here is corrected, shrunk or averaged across sessions. Averaging two runs would
report a precision neither run has.

Usage
-----
    python scripts/test_retest.py --run-a data/final/corpus_naa.csv \
        --run-b data/final/corpus_naa_run_b.csv --out data/final/test_retest.json
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np
from scipy import stats

COLUMNS = ("naa_signed", "a_aff", "a_del")


def _load(path: Path) -> dict[str, dict]:
    with open(path, newline="", encoding="utf-8") as handle:
        return {row["id"]: row for row in csv.DictReader(handle)}


def _anova(values: np.ndarray, categories: np.ndarray) -> dict:
    groups = [values[categories == c] for c in sorted(set(categories.tolist()))]
    f_stat, p_value = stats.f_oneway(*groups)
    grand = values.mean()
    ss_between = sum(len(g) * (g.mean() - grand) ** 2 for g in groups)
    ss_total = ((values - grand) ** 2).sum()
    return {
        "f_statistic": float(f_stat),
        "p_value": float(p_value),
        "eta_squared": float(ss_between / ss_total) if ss_total > 0 else float("nan"),
        "n": int(values.size),
    }


def _agreement(a: np.ndarray, b: np.ndarray) -> dict:
    diff = b - a
    # ICC(2,1): absolute agreement, two-way random effects. Pearson r would count a session
    # that shifted every score by a constant as perfect agreement, and a shift is exactly the
    # failure mode a second GPU session can have.
    stacked = np.stack([a, b])
    n, k = a.size, 2
    grand = stacked.mean()
    ms_rows = k * ((stacked.mean(axis=0) - grand) ** 2).sum() / (n - 1)
    ms_cols = n * ((stacked.mean(axis=1) - grand) ** 2).sum() / (k - 1)
    residual = stacked - stacked.mean(axis=0) - stacked.mean(axis=1, keepdims=True) + grand
    ms_error = (residual ** 2).sum() / ((n - 1) * (k - 1))
    icc = (ms_rows - ms_error) / (ms_rows + (k - 1) * ms_error + k * (ms_cols - ms_error) / n)

    return {
        "pearson_r": float(np.corrcoef(a, b)[0, 1]),
        "icc_2_1": float(icc),
        "mean_difference": float(diff.mean()),
        "sd_difference": float(diff.std(ddof=1)),
        "loa_low": float(diff.mean() - 1.96 * diff.std(ddof=1)),
        "loa_high": float(diff.mean() + 1.96 * diff.std(ddof=1)),
        "max_abs_difference": float(np.abs(diff).max()),
        "between_item_sd_run_a": float(a.std(ddof=1)),
        "noise_to_signal": float(diff.std(ddof=1) / a.std(ddof=1)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-a", type=Path, required=True)
    parser.add_argument("--run-b", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    run_a, run_b = _load(args.run_a), _load(args.run_b)
    shared = sorted(set(run_a) & set(run_b))
    if not shared:
        print("[FAIL] the two runs share no item ids", file=sys.stderr)
        return 1

    mismatched = [i for i in shared if run_a[i]["text"] != run_b[i]["text"]]
    if mismatched:
        print(f"[FAIL] {len(mismatched)} ids carry different text between runs", file=sys.stderr)
        return 1

    categories = np.array([run_a[i]["category"] for i in shared])
    agreement = {}
    for column in COLUMNS:
        a = np.array([float(run_a[i][column]) for i in shared])
        b = np.array([float(run_b[i][column]) for i in shared])
        agreement[column] = _agreement(a, b)

    signed_a = np.array([float(run_a[i]["naa_signed"]) for i in shared])
    signed_b = np.array([float(run_b[i]["naa_signed"]) for i in shared])
    flips = int((np.sign(signed_a) != np.sign(signed_b)).sum())

    result = {
        "n_paired": len(shared),
        "n_run_a_total": len(run_a),
        "n_run_b_total": len(run_b),
        "agreement": agreement,
        "direction_flips": flips,
        "direction_flip_rate": flips / len(shared),
        "separation_run_a_shared_items": _anova(signed_a, categories),
        "separation_run_b_shared_items": _anova(signed_b, categories),
        "note": (
            "Two GPU sessions over identical text with identical code and ROI definitions. "
            "Neither run is corrected or averaged into the other."
        ),
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(f"paired items      : {len(shared)}")
    for column in COLUMNS:
        stat = agreement[column]
        print(f"{column:11s} r={stat['pearson_r']:.4f}  ICC={stat['icc_2_1']:.4f}  "
              f"sd(diff)={stat['sd_difference']:.5f}  "
              f"noise/signal={stat['noise_to_signal']:.3f}")
    print(f"direction flips   : {flips} of {len(shared)} "
          f"({100 * flips / len(shared):.1f}%)")
    for label in ("separation_run_a_shared_items", "separation_run_b_shared_items"):
        sep = result[label]
        print(f"{label:31s} eta^2={sep['eta_squared']:.4f}  "
              f"F={sep['f_statistic']:.3f}  p={sep['p_value']:.3e}")
    print(f"\nWrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
