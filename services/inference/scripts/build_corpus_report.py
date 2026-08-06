"""Assemble the corpus-level AMA report -- objective (vii), the primary deliverable.

The proposal (§5.8 iii) requires the apparatus to produce an audit report over a
whole corpus, not one item at a time: a ranked table of every scanned item, the
distribution per category, the free-energy structure at those category means, and
a per-item flag against the operating threshold. ``report_charts.py`` already
draws the single-scan figures; this is the corpus assembly around them.

Everything written here is derived from ``corpus_naa.csv``. There is no fallback
path: a missing input is an error, not a placeholder figure, because a reader
cannot tell a placeholder from a measurement once it is on a page.

Two constraints the outputs must respect, both from the standing rules:

* **No alpha_hat is quoted.** The coupling between NAA and the Ising field is not
  identified by these data -- both prior calibration runs returned an interval
  straddling zero. The free-energy atlas therefore sweeps alpha across a symmetric
  range and says so in the caption. Structure across a range is a legitimate
  physics figure; a single curve at a fitted-but-null alpha is not.
* **The threshold is fitted in sample.** ``validation.evaluate`` picks the Youden
  point on the same data it scores, which inflates F1 while AUC stays honest. The
  flag column is useful for triage and is labelled as such wherever it appears.

Usage
-----
    python scripts/build_corpus_report.py --csv corpus_naa.csv --out-dir data/report
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings  # noqa: E402
from app.services.distribution import characterise  # noqa: E402
from app.services.landau import landau_free_energy  # noqa: E402
from app.services.validation import evaluate  # noqa: E402

DEFAULT_ALPHA_GRID = "-1.0,-0.5,0.0,0.5,1.0"
CARRIED = ("id", "category", "source_dataset", "word_count", "manipulative", "credibility")


def _load(csv_path: Path, naa_col: str, category_col: str, label_col: str) -> dict:
    """Read the scan output, keeping undefined rows so they can be counted."""
    with open(csv_path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"{csv_path} has no header row")
        for column in (naa_col, category_col):
            if column not in reader.fieldnames:
                raise ValueError(
                    f"column '{column}' not in CSV header {reader.fieldnames}"
                )
        rows = list(reader)

    if not rows:
        raise ValueError(f"{csv_path} has a header but no rows")

    scored = [r for r in rows if (r.get(naa_col) or "").strip() != ""]
    ratio_defined = sum(1 for r in rows if (r.get("naa") or "").strip() != "")
    has_labels = label_col in (rows[0].keys())

    return {
        "rows": rows,
        "scored": scored,
        "ratio_defined": ratio_defined,
        "has_labels": has_labels,
    }


def _groups(scored: list[dict], naa_col: str, category_col: str) -> dict[str, np.ndarray]:
    buckets: dict[str, list[float]] = defaultdict(list)
    for row in scored:
        buckets[(row.get(category_col) or "").strip()].append(float(row[naa_col]))
    return {name: np.asarray(values, dtype=float) for name, values in sorted(buckets.items())}


def _ranked_csv(
    scored: list[dict],
    naa_col: str,
    category_col: str,
    threshold: float | None,
    out_path: Path,
) -> list[dict]:
    """Every scanned item, ordered by the index, with its flag."""
    ordered = sorted(scored, key=lambda r: float(r[naa_col]), reverse=True)
    records = []
    for rank, row in enumerate(ordered, start=1):
        record = {"rank": rank, "naa_signed": float(row[naa_col])}
        for column in CARRIED:
            if column in row:
                record[column] = row.get(column, "")
        record["naa_ratio"] = (row.get("naa") or "").strip()
        record["classification"] = row.get("classification", "")
        record["flagged"] = "" if threshold is None else int(float(row[naa_col]) >= threshold)
        records.append(record)

    with open(out_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)
    return records


def _violin_png(groups: dict[str, np.ndarray], out_path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    names = list(groups.keys())
    data = [groups[name] for name in names]

    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    parts = ax.violinplot(data, showmeans=True, showextrema=False)
    for body in parts["bodies"]:
        body.set_alpha(0.45)

    # Overlay the items themselves: a violin is a kernel estimate, and at n=100 a
    # reader should be able to see the sample it was drawn from.
    rng = np.random.default_rng(0)
    for position, values in enumerate(data, start=1):
        jitter = rng.uniform(-0.06, 0.06, size=values.size)
        ax.plot(position + jitter, values, ".", ms=2.5, alpha=0.4, color="black")

    ax.set_xticks(range(1, len(names) + 1))
    ax.set_xticklabels([n.replace("_", "\n") for n in names], fontsize=8)
    ax.set_ylabel("signed NAA  ($A_{aff} - A_{del}$)")
    ax.set_title("Signed NAA by category (predicted cortical proxy)", fontsize=10)
    ax.axhline(0.0, lw=0.8, color="grey", ls="--")
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


def _ranked_png(records: list[dict], threshold: float | None, out_path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    categories = sorted({r.get("category", "") for r in records})
    colours = {name: f"C{i}" for i, name in enumerate(categories)}

    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    for name in categories:
        xs = [r["rank"] for r in records if r.get("category") == name]
        ys = [r["naa_signed"] for r in records if r.get("category") == name]
        ax.plot(xs, ys, ".", ms=4, label=name, color=colours[name])

    if threshold is not None:
        ax.axhline(
            threshold,
            lw=1.0,
            color="crimson",
            label="Youden threshold (fitted in sample)",
        )

    ax.set_xlabel("rank")
    ax.set_ylabel("signed NAA")
    ax.set_title("Corpus ranked by signed NAA", fontsize=10)
    ax.legend(fontsize=7, loc="best")
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


def _atlas_png(
    group_means: dict[str, float],
    alpha_grid: list[float],
    beta_j: float,
    out_path: Path,
) -> None:
    """Free-energy structure at each category's mean NAA, across alpha.

    Alpha is a free parameter here, not an estimate. Each panel is one value of it,
    so the figure shows how the landscape would deform IF the coupling took that
    value -- which is the strongest statement the calibration null permits.
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    m = np.linspace(-1.0, 1.0, 601)
    fig, axes = plt.subplots(
        1, len(alpha_grid), figsize=(3.1 * len(alpha_grid), 3.4), sharey=True
    )
    if len(alpha_grid) == 1:
        axes = [axes]

    for ax, alpha in zip(axes, alpha_grid):
        for name, naa in group_means.items():
            free_energy = landau_free_energy(m, beta_j=beta_j, alpha_hat=alpha, naa=naa)
            ax.plot(m, free_energy, lw=1.3, label=name.replace("_", " "))
        ax.set_title(rf"$\alpha$ = {alpha:g}", fontsize=9)
        ax.set_xlabel("m")
        ax.axvline(0.0, lw=0.6, color="grey", ls=":")
    axes[0].set_ylabel("F(m)")
    axes[-1].legend(fontsize=6.5, loc="upper center")

    fig.suptitle(
        rf"Free-energy atlas at category mean NAA, $\beta J$ = {beta_j:g}. "
        rf"$\alpha$ is swept, not fitted: these data do not constrain it.",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.90))
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--naa-col", default="naa_signed")
    parser.add_argument("--category-col", default="category")
    parser.add_argument("--label-col", default="manipulative")
    parser.add_argument("--baseline", default="neutral_informational")
    parser.add_argument("--beta-j", type=float, default=None)
    parser.add_argument("--alpha-grid", default=DEFAULT_ALPHA_GRID)
    args = parser.parse_args()

    if not args.csv.exists():
        print(
            f"[FAIL] {args.csv} does not exist. The corpus report is built from the "
            "scan output; there is no synthetic substitute.",
            file=sys.stderr,
        )
        return 1

    try:
        loaded = _load(args.csv, args.naa_col, args.category_col, args.label_col)
    except ValueError as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1

    rows, scored = loaded["rows"], loaded["scored"]
    if not scored:
        print(f"[FAIL] no rows carry a usable '{args.naa_col}'", file=sys.stderr)
        return 1

    beta_j = settings.beta_j if args.beta_j is None else args.beta_j
    alpha_grid = [float(a) for a in args.alpha_grid.split(",") if a.strip()]
    args.out_dir.mkdir(parents=True, exist_ok=True)

    groups = _groups(scored, args.naa_col, args.category_col)

    validation = None
    threshold = None
    if loaded["has_labels"]:
        scores, labels = [], []
        for row in scored:
            raw = (row.get(args.label_col) or "").strip()
            if raw:
                scores.append(float(row[args.naa_col]))
                labels.append(int(float(raw)))
        if scores and len(set(labels)) == 2:
            validation = evaluate(np.asarray(scores), np.asarray(labels))
            threshold = validation["threshold"]

    records = _ranked_csv(
        scored, args.naa_col, args.category_col, threshold, args.out_dir / "corpus_ranked.csv"
    )
    _violin_png(groups, args.out_dir / "fig_violin.png")
    _ranked_png(records, threshold, args.out_dir / "fig_ranked.png")

    group_means = {name: float(values.mean()) for name, values in groups.items()}
    _atlas_png(group_means, alpha_grid, beta_j, args.out_dir / "fig_free_energy_atlas.png")

    # characterise compares every category against a named baseline and raises when it
    # is absent; a partial scan can easily not have reached it yet.
    distribution = None
    if len(groups) > 1 and args.baseline in groups:
        distribution = characterise(groups, baseline=args.baseline)
    elif args.baseline not in groups:
        print(
            f"[note] baseline '{args.baseline}' not present in this scan "
            f"({list(groups)}); RQ II comparisons skipped.",
        )

    # Every number a figure shows is written here too, so the thesis cites values
    # rather than reading them off pixels.
    report = {
        "source_csv": str(args.csv),
        "n_rows": len(rows),
        "n_scored": len(scored),
        "n_ratio_defined": loaded["ratio_defined"],
        "n_ratio_undefined": len(rows) - loaded["ratio_defined"],
        "metric": args.naa_col,
        "beta_j": beta_j,
        "alpha_grid": alpha_grid,
        "alpha_is_fitted": False,
        "category_means": group_means,
        "category_n": {name: int(values.size) for name, values in groups.items()},
        "distribution": distribution,
        "validation": validation,
        "threshold_fitted_in_sample": bool(validation is not None),
    }
    (args.out_dir / "corpus_report.json").write_text(
        json.dumps(report, indent=2, default=float), encoding="utf-8"
    )

    print(f"rows in scan      : {len(rows)}")
    print(f"scored on {args.naa_col:<10}: {len(scored)}")
    print(f"ratio NAA defined : {loaded['ratio_defined']}  undefined: {report['n_ratio_undefined']}")
    for name, values in groups.items():
        print(f"  {name:24s} n={values.size:3d}  mean={values.mean():+.4f}  sd={values.std(ddof=1) if values.size > 1 else float('nan'):.4f}")
    if validation:
        print(f"AUC               : {validation['auc']:.4f}  (headline metric)")
        print(f"F1                : {validation['f1']:.4f}  (threshold fitted in sample -- not the headline)")
    else:
        print("validation        : skipped, no two-class label column")
    print(f"\nWrote {args.out_dir}/ : corpus_ranked.csv, corpus_report.json, 3 figures")
    print("alpha is swept, never fitted: no alpha_hat appears in any output.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
