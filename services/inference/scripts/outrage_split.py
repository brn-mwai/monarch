"""Split the signed index into its two components by category (§6.2).

Section 6.2 offers a symmetric-response reading of the high-outrage null: both
networks rise together, so the difference stays flat. That reading is testable
from columns already in the corpus. If A_aff and A_del are both elevated for
high outrage relative to neutral while their difference is not, the reading is
supported. If neither is elevated, it is not, and the null has to be explained
by source or by out-of-distribution content instead.

Usage
-----
    python scripts/outrage_split.py --csv data/final/corpus_naa.csv \
        --out data/final/outrage_split.json \
        --figure data/final/report/fig_components.png
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

BASELINE = "neutral_informational"
COMPONENTS = ("a_aff", "a_del", "naa_signed")


def _welch(treated: np.ndarray, control: np.ndarray) -> dict:
    result = stats.ttest_ind(treated, control, equal_var=False)
    pooled = np.sqrt((treated.var(ddof=1) + control.var(ddof=1)) / 2.0)
    return {
        "t": float(result.statistic),
        "p": float(result.pvalue),
        "cohens_d": float((treated.mean() - control.mean()) / pooled),
        "mean_treated": float(treated.mean()),
        "mean_control": float(control.mean()),
    }


def _figure(frame: pd.DataFrame, path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    categories = sorted(frame["category"].unique())
    fig, axes = plt.subplots(1, len(COMPONENTS), figsize=(15, 4.5), sharex=True)
    for axis, column in zip(axes, COMPONENTS):
        data = [frame.loc[frame["category"] == c, column].to_numpy() for c in categories]
        axis.violinplot(data, showmeans=True)
        axis.set_xticks(range(1, len(categories) + 1))
        axis.set_xticklabels([c.replace("_", "\n") for c in categories], fontsize=8)
        axis.axhline(0.0, color="0.6", linewidth=0.8, linestyle="--")
        axis.set_title(column)
    axes[0].set_ylabel("standardised activation")
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=200)
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--figure", type=Path, required=True)
    args = parser.parse_args()

    frame = pd.read_csv(args.csv)
    control = frame[frame["category"] == BASELINE]

    descriptives = {}
    contrasts = {}
    for category in sorted(frame["category"].unique()):
        block = frame[frame["category"] == category]
        descriptives[category] = {
            column: {
                "n": int(block.shape[0]),
                "mean": float(block[column].mean()),
                "sd": float(block[column].std(ddof=1)),
            }
            for column in COMPONENTS
        }
        if category == BASELINE:
            continue
        contrasts[category] = {
            column: _welch(block[column].to_numpy(), control[column].to_numpy())
            for column in COMPONENTS
        }

    anovas = {
        column: dict(
            zip(
                ("F", "p"),
                (
                    float(v)
                    for v in stats.f_oneway(
                        *[
                            frame.loc[frame["category"] == c, column].to_numpy()
                            for c in sorted(frame["category"].unique())
                        ]
                    )
                ),
            )
        )
        for column in COMPONENTS
    }

    _figure(frame, args.figure)
    payload = {
        "corpus": str(args.csv),
        "baseline": BASELINE,
        "descriptives": descriptives,
        "contrasts_vs_baseline": contrasts,
        "one_way_anova": anovas,
        "figure": str(args.figure),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"{'category':<24}{'a_aff mean':>12}{'a_del mean':>12}{'signed mean':>13}")
    for category, block in descriptives.items():
        print(
            f"{category:<24}{block['a_aff']['mean']:>12.5f}"
            f"{block['a_del']['mean']:>12.5f}{block['naa_signed']['mean']:>13.5f}"
        )
    print("")
    print(f"{'contrast vs neutral':<24}{'component':<12}{'t':>9}{'p':>12}{'d':>9}")
    for category, block in contrasts.items():
        for column, stat in block.items():
            print(
                f"{category:<24}{column:<12}{stat['t']:>9.3f}"
                f"{stat['p']:>12.3e}{stat['cohens_d']:>9.3f}"
            )
    print("")
    for column, stat in anovas.items():
        print(f"one-way ANOVA {column:<12} F={stat['F']:.3f}  p={stat['p']:.3e}")
    print(f"written to {args.out} and {args.figure}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
