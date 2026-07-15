"""Batch-scan a labeled text corpus and write one NAA value per item.

Runs the TRIBE cascade over every row of a CSV, computes the NAA index from
the item-level activation vector, and writes a CSV carrying the original
outcome label alongside the computed NAA. That output is the input to
``calibrate_alpha.py --naa-col naa``, so the expensive GPU pass happens once
and the regression can be re-run for free.

NAA is undefined when either network mean sits below baseline (see
``compute_naa``). Those rows are written with an empty ``naa`` field and
counted in the summary rather than silently dropped, so the paper can state
how much of the corpus produced a usable index.

Usage
-----
    python scripts/batch_naa.py --csv data/corpus.csv \
        --text-col text --outcome-col arousal --out data/corpus_naa.csv
"""

from __future__ import annotations

import argparse
import csv
import statistics
import sys
import time
from pathlib import Path


def _load_rows(csv_path: Path, text_col: str, outcome_col: str) -> list[dict]:
    with open(csv_path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"{csv_path} has no header row")
        for column in (text_col, outcome_col):
            if column not in reader.fieldnames:
                raise ValueError(
                    f"column '{column}' not in CSV header {reader.fieldnames}"
                )
        return [
            row
            for row in reader
            if row[text_col].strip() and row[outcome_col].strip()
        ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--text-col", default="text")
    parser.add_argument("--outcome-col", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    from app.services.inference import TribeInferenceService
    from app.services.naa import compute_naa, compute_signed_naa

    rows = _load_rows(args.csv, args.text_col, args.outcome_col)
    if args.limit:
        rows = rows[: args.limit]
    if not rows:
        print("[FAIL] no usable rows in corpus", file=sys.stderr)
        return 1

    print(f"Scanning {len(rows)} items through TRIBE...")
    service = TribeInferenceService()
    service.load_model()

    scanned: list[dict] = []
    naa_values: list[float] = []
    undefined = 0
    started = time.time()

    for index, row in enumerate(rows, start=1):
        text = row[args.text_col].strip()
        result = service.predict_text(text)
        naa = compute_naa(result["item_vector"])
        signed = compute_signed_naa(result["item_vector"])

        if naa["valid"]:
            naa_values.append(float(naa["naa"]))
        else:
            undefined += 1

        scanned.append(
            {
                "text": text,
                args.outcome_col: row[args.outcome_col],
                "naa": f"{naa['naa']:.6f}" if naa["valid"] else "",
                "naa_signed": f"{signed['naa']:.6f}",
                "a_aff": f"{naa['a_aff']:.6f}",
                "a_del": f"{naa['a_del']:.6f}",
                "classification": naa["classification"],
            }
        )
        elapsed = time.time() - started
        shown = f"{naa['naa']:.4f}" if naa["valid"] else "UNDEFINED"
        print(
            f"[{index}/{len(rows)}] naa={shown} ({elapsed / index:.1f}s/item)",
            flush=True,
        )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["text", args.outcome_col, "naa", "naa_signed", "a_aff", "a_del", "classification"],
        )
        writer.writeheader()
        writer.writerows(scanned)

    print(f"\nWrote {args.out} ({len(scanned)} rows)")
    print(f"NAA defined: {len(naa_values)}/{len(scanned)}  undefined: {undefined}")
    if naa_values:
        print("--- NAA distribution ---")
        print(f"  min    : {min(naa_values):.4f}")
        print(f"  median : {statistics.median(naa_values):.4f}")
        print(f"  mean   : {statistics.fmean(naa_values):.4f}")
        print(f"  max    : {max(naa_values):.4f}")
        if len(naa_values) > 1:
            print(f"  stdev  : {statistics.stdev(naa_values):.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
