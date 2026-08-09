"""Turn the scan CSV into the compact JSON the site reads.

The site has no inference backend and is not getting one, so everything it shows about the
corpus has to be baked in at build time. This writes that file: per-item values and
per-category summaries, and nothing the scan did not produce.

Item text ships in full. A truncated preview is enough for a table row but not for reading
an item, and the page offers the whole text behind a control; the corpus is public data
already cited in the thesis.

Usage
-----
    python scripts/export_corpus_web.py --scan data/corpus_naa.csv \
        --out ../../apps/web/public/data/corpus.json
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from pathlib import Path

PREVIEW_CHARS = 180



def _float_or_none(value: str | None) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def summarise(rows: list[dict]) -> dict:
    by_category: dict[str, list[float]] = {}
    aff_by_category: dict[str, list[float]] = {}
    del_by_category: dict[str, list[float]] = {}

    for row in rows:
        signed = _float_or_none(row.get("naa_signed"))
        if signed is None:
            continue
        category = row["category"]
        by_category.setdefault(category, []).append(signed)
        aff_by_category.setdefault(category, []).append(float(row["a_aff"]))
        del_by_category.setdefault(category, []).append(float(row["a_del"]))

    categories = []
    for category in sorted(by_category):
        values = by_category[category]
        categories.append({
            "category": category,
            "n": len(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "sd": statistics.stdev(values) if len(values) > 1 else None,
            "min": min(values),
            "max": max(values),
            "aAffMean": statistics.mean(aff_by_category[category]),
            "aDelMean": statistics.mean(del_by_category[category]),
        })

    all_values = [v for values in by_category.values() for v in values]
    undefined = sum(1 for r in rows if not r.get("naa"))

    return {
        "categories": categories,
        "nScanned": len(rows),
        "nRatioUndefined": undefined,
        "nRatioDefined": len(rows) - undefined,
        "spread": (max(all_values) - min(all_values)) if all_values else None,
        "min": min(all_values) if all_values else None,
        "max": max(all_values) if all_values else None,
    }


def items(rows: list[dict]) -> list[dict]:
    out = []
    for row in rows:
        text = row.get("text", "")
        out.append({
            "id": row.get("id", ""),
            "category": row["category"],
            "preview": text[:PREVIEW_CHARS] + ("..." if len(text) > PREVIEW_CHARS else ""),
            "text": text,
            "wordCount": int(row["word_count"]) if row.get("word_count") else None,
            "source": row.get("source_dataset", ""),
            # The labels the item carried before it was ever scanned. They are the only
            # ground truth in this dataset: the activation values have none.
            "labelManipulative": row.get("manipulative", ""),
            "labelCredibility": row.get("credibility", ""),
            "labelPartisan": row.get("partisan_intensity", ""),
            "naaSigned": _float_or_none(row.get("naa_signed")),
            "naaRatio": _float_or_none(row.get("naa")),
            "aAff": _float_or_none(row.get("a_aff")),
            "aDel": _float_or_none(row.get("a_del")),
        })
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scan", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--corpus-target", type=int, default=400)
    args = parser.parse_args()

    if not args.scan.exists():
        print(f"[FAIL] {args.scan} not found", file=sys.stderr)
        return 1

    with open(args.scan, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        print("[FAIL] scan CSV has no rows", file=sys.stderr)
        return 1

    summary = summarise(rows)
    payload = {
        "corpusTarget": args.corpus_target,
        "complete": len(rows) >= args.corpus_target,
        "summary": summary,
        "items": items(rows),
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")

    print(f"rows exported : {len(rows)} of {args.corpus_target}")
    print(f"complete      : {payload['complete']}")
    print(f"ratio defined : {summary['nRatioDefined']}  undefined: {summary['nRatioUndefined']}")
    for category in summary["categories"]:
        print(f"  {category['category']:24s} n={category['n']:3d} "
              f"mean={category['mean']:+.4f}")
    print(f"\nWrote {args.out} ({args.out.stat().st_size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
