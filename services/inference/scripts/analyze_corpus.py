"""Answer RQ I and RQ II from a scanned corpus. No GPU.

Consumes the CSV written by ``batch_naa.py`` and emits the objective (iii) and
(vi) results as JSON plus a readable summary.

    RQ II  distribution of NAA across categories, KL vs the neutral baseline
    RQ I   does NAA separate manipulative from neutral content

This is also the **Gate 2 pilot** tool. Run it on a 40-item pilot scan before
committing ~31 GPU-hours to the full 1,500: the ``separation`` block answers
whether NAA varies by category at all, which decides which way RQ I and RQ II
are written. One GPU-hour here buys six weeks of warning.

The exit code is the gate: 0 when the index discriminates, 2 when it does not.
A non-zero exit is a legitimate scientific result, not a failure, and the
distinction matters because a null is the outcome both prior runs point at.

Usage
-----
    python scripts/analyze_corpus.py --csv corpus_naa.csv \
        --naa-col naa_signed --category-col category \
        --out data/rq_answers.json
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

from app.services.distribution import characterise  # noqa: E402
from app.services.validation import evaluate  # noqa: E402

DEFAULT_BASELINE = "neutral_informational"


def _load(
    csv_path: Path,
    naa_col: str,
    category_col: str,
    label_col: str,
) -> tuple[dict[str, list[float]], list[float], list[int]]:
    groups: dict[str, list[float]] = defaultdict(list)
    scores: list[float] = []
    labels: list[int] = []
    skipped = 0

    with open(csv_path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"{csv_path} has no header row")
        for column in (naa_col, category_col):
            if column not in reader.fieldnames:
                raise ValueError(
                    f"column '{column}' not in CSV header {reader.fieldnames}"
                )
        has_labels = label_col in reader.fieldnames

        for row in reader:
            raw = (row.get(naa_col) or "").strip()
            if raw == "":
                skipped += 1
                continue
            value = float(raw)
            groups[(row.get(category_col) or "").strip()].append(value)
            if has_labels and (row.get(label_col) or "").strip() != "":
                scores.append(value)
                labels.append(int(float(row[label_col])))

    if skipped:
        print(
            f"[note] {skipped} rows had an empty '{naa_col}' and were excluded. "
            f"For the ratio NAA this is expected and must be reported: it is "
            f"undefined wherever an ROI mean sits below baseline."
        )
    return dict(groups), scores, labels


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--naa-col", default="naa_signed")
    parser.add_argument("--category-col", default="category")
    parser.add_argument("--label-col", default="manipulative")
    parser.add_argument("--baseline", default=DEFAULT_BASELINE)
    parser.add_argument("--out", type=Path, default=Path("./data/rq_answers.json"))
    args = parser.parse_args()

    groups, scores, labels = _load(
        args.csv, args.naa_col, args.category_col, args.label_col
    )
    if len(groups) < 2:
        print(
            f"[FAIL] need >= 2 categories, found {list(groups)}", file=sys.stderr
        )
        return 1

    arrays = {name: np.array(values) for name, values in groups.items()}
    baseline = args.baseline if args.baseline in arrays else sorted(arrays)[0]
    if baseline != args.baseline:
        print(f"[note] baseline '{args.baseline}' absent; using '{baseline}'")

    answers = {
        "naa_column": args.naa_col,
        "n_items": int(sum(a.size for a in arrays.values())),
        "rq2_distribution": characterise(arrays, baseline=baseline),
    }

    print("\n=== RQ II: NAA distribution across categories ===")
    per_category = answers["rq2_distribution"]["per_category"]
    for name in sorted(per_category):
        entry = per_category[name]
        marker = " (baseline)" if name == baseline else ""
        print(
            f"  {name:<24}{marker}\n"
            f"    n={entry['n']:<5} mean={entry['mean']:+.4f}  "
            f"sd={entry['sd']:.4f}  skew={entry['skewness']:+.2f}  "
            f"kurt={entry['excess_kurtosis']:+.2f}"
        )
        print(f"    entropy={_fmt(entry.get('entropy'))}", end="")
        if name != baseline:
            print(
                f"  d_vs_baseline={_fmt(entry.get('cohens_d_vs_baseline'), '+.3f')}"
                f"  KL_vs_baseline={_fmt(entry.get('kl_vs_baseline'))}"
            )
        else:
            print()

    sep = answers["rq2_distribution"]["separation"]
    print(
        f"\n  separation: F={sep['f_statistic']:.3f}  p={sep['p_value']:.4g}  "
        f"eta^2={sep['eta_squared']:.4f}  "
        f"({'USABLE' if sep['usable'] else 'NOT USABLE'})"
    )
    if not sep["usable"]:
        print(
            "  [NULL] Category membership does not explain a meaningful share "
            "of NAA variance.\n"
            "         RQ II answer: the distributions do not separate. Write "
            "chapters 5-6 from that premise."
        )

    discriminates = None
    if len(set(labels)) == 2:
        answers["rq1_validation"] = evaluate(np.array(scores), np.array(labels))
        result = answers["rq1_validation"]
        discriminates = result["discriminates"]
        print("\n=== RQ I: NAA as a manipulation classifier ===")
        print(
            f"  n={result['n']}  AUC={result['auc']:.4f}  "
            f"F1={result['f1']:.4f}  precision={result['precision']:.4f}  "
            f"recall={result['recall']:.4f}"
        )
        print(f"  {result['interpretation']}")
        if result["leak_suspected"]:
            print(
                "  [CHECK] Verify the ISOT dateline was stripped before "
                "believing this number.",
                file=sys.stderr,
            )
    else:
        print(
            f"\n=== RQ I: skipped, '{args.label_col}' needs both classes ==="
        )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(answers, indent=2), encoding="utf-8")
    print(f"\nWrote {args.out}")

    verdict = sep["usable"] or bool(discriminates)
    return 0 if verdict else 2


def _fmt(value: float | None, spec: str = ".4f") -> str:
    return "n/a" if value is None else format(value, spec)


if __name__ == "__main__":
    sys.exit(main())
