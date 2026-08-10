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
TOTAL_VERTS = 20484
SCALE_PERCENTILES = (1.0, 99.0)


def vector_scale(vectors_dir: Path, mask_path: Path | None) -> dict | None:
    """Pool every shipped map and take one colour range for the whole corpus.

    Normalising each map by its own percentiles makes every item render identically
    saturated, so a weakly activated item and a strongly activated one look the same and a
    comparison between two brains means nothing. The range is therefore measured once across
    all maps, over cortex only: the medial wall carries no signal and its values would drag
    the percentiles toward zero.
    """
    import numpy as np

    files = sorted(vectors_dir.glob("*.f32"))
    if not files:
        return None

    mask = None
    if mask_path is not None and mask_path.exists():
        raw = np.frombuffer(mask_path.read_bytes(), dtype=np.uint8)
        if raw.size == TOTAL_VERTS:
            mask = raw.astype(bool)

    pooled = []
    for path in files:
        values = np.fromfile(path, dtype=np.float32)
        if values.size != TOTAL_VERTS:
            raise ValueError(f"{path.name}: {values.size} vertices, expected {TOTAL_VERTS}")
        pooled.append(values[mask] if mask is not None else values)

    stacked = np.concatenate(pooled)
    low, high = (float(np.percentile(stacked, q)) for q in SCALE_PERCENTILES)
    return {
        "lo": low,
        "hi": high,
        "nVectors": len(files),
        "percentiles": list(SCALE_PERCENTILES),
        "cortexOnly": mask is not None,
    }



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


def items(rows: list[dict], vectors_dir: Path | None) -> list[dict]:
    out = []
    for row in rows:
        text = row.get("text", "")
        item_id = row.get("id", "")
        out.append({
            "id": item_id,
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
            # Derived from what is on disk, never hand-set. The site loads {id}.f32 only
            # when this is true, and a stale true draws a flat fill as though it were a
            # per-vertex prediction.
            "hasVector": bool(vectors_dir and (vectors_dir / f"{item_id}.f32").exists()),
        })
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scan", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--vectors-dir", type=Path, default=None)
    parser.add_argument("--medial-mask", type=Path, default=None)
    parser.add_argument("--corpus-target", type=int, default=400)
    args = parser.parse_args()

    if args.vectors_dir is not None and not args.vectors_dir.is_dir():
        print(f"[FAIL] {args.vectors_dir} is not a directory", file=sys.stderr)
        return 1

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
        "items": items(rows, args.vectors_dir),
    }
    if args.vectors_dir is not None:
        scale = vector_scale(args.vectors_dir, args.medial_mask)
        if scale is not None:
            payload["vectorScale"] = scale

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")

    with_vector = sum(1 for item in payload["items"] if item["hasVector"])
    print(f"rows exported : {len(rows)} of {args.corpus_target}")
    print(f"complete      : {payload['complete']}")
    print(f"per-vertex map: {with_vector} of {len(rows)}")
    if "vectorScale" in payload:
        vs = payload["vectorScale"]
        print(f"vertex scale  : [{vs['lo']:+.5f}, {vs['hi']:+.5f}] "
              f"from {vs['nVectors']} maps, cortexOnly={vs['cortexOnly']}")
    print(f"ratio defined : {summary['nRatioDefined']}  undefined: {summary['nRatioUndefined']}")
    for category in summary["categories"]:
        print(f"  {category['category']:24s} n={category['n']:3d} "
              f"mean={category['mean']:+.4f}")
    print(f"\nWrote {args.out} ({args.out.stat().st_size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
