"""Check a scan's output against the corpus it claims to have scanned.

Runbook step A2. The scan is the one step that cannot be repeated cheaply, so the moment its
output lands the question is whether those rows are really the corpus's rows, computed, in
order. Doing that by eye once is fine; doing it three times across three runs is how a
mismatch gets waved through.

The tolerance matters. Output columns are written to six decimals, so recomputing
``a_aff - a_del`` and comparing against a separately rounded ``naa_signed`` disagrees by up to
1e-6 on perfectly good rows. Comparing at 1e-9 reports false failures, which is exactly what
happened the first time this was checked by hand.

Usage
-----
    python scripts/verify_scan_output.py --corpus data/corpus.csv --scan data/corpus_naa.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

# Three separately rounded six-decimal columns: a_aff and a_del each carry up to 5e-7, so
# their difference carries up to 1e-6, and naa_signed is rounded independently for another
# 5e-7. Worst case is 1.5e-6. A tolerance of exactly 1e-6 rejected 4 of the 50 rows in the
# first completed run, all of them sound.
ROUNDING_TOLERANCE = 2e-6


def _read(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def check(corpus: list[dict], scan: list[dict]) -> tuple[list[str], dict]:
    """Return the failures found and the facts worth reporting either way."""
    failures: list[str] = []
    n = len(scan)

    if n == 0:
        return ["scan output is empty"], {"n_scanned": 0}
    if n > len(corpus):
        failures.append(f"scan has {n} rows, corpus only has {len(corpus)}")
        return failures, {"n_scanned": n}

    # The scan consumes the first N corpus rows in order, so row i must be corpus row i.
    for field in ("text", "category", "id"):
        if field not in scan[0]:
            failures.append(f"scan output has no {field} column")
            continue
        wrong = [i for i in range(n) if scan[i][field] != corpus[i][field]]
        if wrong:
            failures.append(
                f"{len(wrong)} rows differ from the corpus on {field} "
                f"(first at index {wrong[0]})"
            )

    distinct_text = len({r["text"] for r in scan})
    if distinct_text != n:
        failures.append(f"{n - distinct_text} duplicate texts in the scan output")

    signed = [r for r in scan if r.get("naa_signed")]
    distinct_signed = len({r["naa_signed"] for r in signed})
    # Needs at least two rows to mean anything: one row is trivially all-identical.
    if len(signed) > 1 and distinct_signed == 1:
        failures.append("every naa_signed value is identical, which is not a measurement")

    inconsistent = 0
    for row in scan:
        if row.get("a_aff") and row.get("a_del") and row.get("naa_signed"):
            recomputed = float(row["a_aff"]) - float(row["a_del"])
            if abs(recomputed - float(row["naa_signed"])) > ROUNDING_TOLERANCE:
                inconsistent += 1
    if inconsistent:
        failures.append(
            f"{inconsistent} rows where naa_signed does not equal a_aff - a_del "
            f"beyond {ROUNDING_TOLERANCE:g}"
        )

    categories: dict[str, int] = {}
    for row in scan:
        categories[row["category"]] = categories.get(row["category"], 0) + 1

    undefined = sum(1 for r in scan if not r.get("naa"))
    return failures, {
        "n_scanned": n,
        "n_corpus": len(corpus),
        "distinct_texts": distinct_text,
        "distinct_naa_signed": distinct_signed,
        "ratio_undefined": undefined,
        "ratio_defined": n - undefined,
        "by_category": categories,
        "complete": n == len(corpus),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--scan", type=Path, required=True)
    args = parser.parse_args()

    for path in (args.corpus, args.scan):
        if not path.exists():
            print(f"[FAIL] {path} not found", file=sys.stderr)
            return 1

    failures, facts = check(_read(args.corpus), _read(args.scan))

    print(f"scanned {facts['n_scanned']} of {facts.get('n_corpus', '?')} corpus rows")
    if facts.get("by_category"):
        for category, count in sorted(facts["by_category"].items()):
            print(f"  {category:24s} {count}")
    print(f"ratio NAA defined: {facts.get('ratio_defined')}  "
          f"undefined: {facts.get('ratio_undefined')}")
    print(f"distinct texts: {facts.get('distinct_texts')}  "
          f"distinct naa_signed: {facts.get('distinct_naa_signed')}")

    if failures:
        print("\n[FAIL] this output does not match the corpus:", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1

    if facts.get("complete"):
        print("\n[OK] every corpus row is scanned and matches. Ready for analysis.")
    else:
        remaining = facts["n_corpus"] - facts["n_scanned"]
        print(f"\n[OK] rows match the corpus. Partial: {remaining} still to scan.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
