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

Each item is appended to ``--out`` and flushed the moment it is scanned, so a
killed session (Colab disconnect, OOM) keeps every item computed so far.
Re-running with the same ``--out`` resumes: items whose text is already in the
file are skipped, and only the remainder is scanned.

``--carry-cols`` copies further columns through the GPU pass unchanged. The
scan is the only expensive step and it cannot be repeated cheaply, so any
column a later analysis needs must be named here: scanning the four-category
corpus with ``--outcome-col category`` alone would drop ``credibility`` and
force a second scan to calibrate against it.

Usage
-----
    python scripts/batch_naa.py --csv data/corpus.csv \
        --text-col text --outcome-col arousal --out data/corpus_naa.csv

    python scripts/batch_naa.py --csv corpus.csv \
        --outcome-col category --carry-cols credibility,source \
        --out corpus_naa.csv
"""

from __future__ import annotations

import argparse
import csv
import statistics
import sys
import time
from pathlib import Path

# Python puts the script's own directory on sys.path, not the working directory, so the
# app package is invisible when this is run as `python scripts/batch_naa.py`.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


COMPUTED_COLUMNS = ("naa", "naa_signed", "a_aff", "a_del", "classification")


def free_gpu_memory() -> None:
    """Return this item's allocations to the driver before the next one starts.

    The cascade holds several models resident and each item adds a (T, 20484) prediction
    plus the intermediates behind it. Without this the run reaches an allocator failure
    within a handful of items on a 16 GB card, having already paid for the model load.
    Safe on CPU-only machines, where it does nothing.
    """
    import gc

    gc.collect()
    try:
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except ImportError:
        pass


def _load_rows(
    csv_path: Path,
    text_col: str,
    outcome_col: str,
    carry_cols: tuple[str, ...] = (),
) -> list[dict]:
    with open(csv_path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"{csv_path} has no header row")
        for column in (text_col, outcome_col, *carry_cols):
            if column not in reader.fieldnames:
                raise ValueError(
                    f"column '{column}' not in CSV header {reader.fieldnames}"
                )
        return [
            row
            for row in reader
            if row[text_col].strip() and row[outcome_col].strip()
        ]


def _output_fieldnames(outcome_col: str, carry_cols: tuple[str, ...]) -> list[str]:
    fieldnames = ["text", outcome_col]
    for column in carry_cols:
        if column not in fieldnames:
            fieldnames.append(column)
    return fieldnames + list(COMPUTED_COLUMNS)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--text-col", default="text")
    parser.add_argument("--outcome-col", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument(
        "--carry-cols",
        default="",
        help="comma-separated extra source columns to copy into --out unchanged",
    )
    args = parser.parse_args()

    carry_cols = tuple(c.strip() for c in args.carry_cols.split(",") if c.strip())
    reserved = {"text", *COMPUTED_COLUMNS}
    clashing = [c for c in carry_cols if c in reserved]
    if clashing:
        print(
            f"[FAIL] --carry-cols may not name output columns: {clashing}",
            file=sys.stderr,
        )
        return 1

    rows = _load_rows(args.csv, args.text_col, args.outcome_col, carry_cols)
    if args.limit:
        rows = rows[: args.limit]
    if not rows:
        print("[FAIL] no usable rows in corpus", file=sys.stderr)
        return 1

    fieldnames = _output_fieldnames(args.outcome_col, carry_cols)

    done_texts: set[str] = set()
    if args.out.exists():
        with open(args.out, newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            existing = reader.fieldnames or []
            if existing and existing != fieldnames:
                print(
                    f"[FAIL] {args.out} has header {existing}, this run writes "
                    f"{fieldnames}. Appending would misalign every resumed row. "
                    "Use a different --out or match the original flags.",
                    file=sys.stderr,
                )
                return 1
            done_texts = {r["text"] for r in reader if r.get("text")}

    pending = [row for row in rows if row[args.text_col].strip() not in done_texts]
    if done_texts:
        print(f"Resuming: {len(done_texts)} items already in {args.out}, {len(pending)} remaining")
    if not pending:
        print(f"All {len(rows)} items already scanned in {args.out}; nothing to do.")
        return 0

    print(f"Scanning {len(pending)} items through TRIBE...")
    from app.services.inference import TribeInferenceService
    from app.services.naa import compute_naa, compute_signed_naa

    service = TribeInferenceService()
    service.load_model()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    started = time.time()
    completed = 0
    with open(args.out, "a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if not done_texts:
            writer.writeheader()
            handle.flush()

        for index, row in enumerate(pending, start=1):
            text = row[args.text_col].strip()
            result = service.predict_text(text)
            naa = compute_naa(result["item_vector"])
            signed = compute_signed_naa(result["item_vector"])

            record = {
                "text": text,
                args.outcome_col: row[args.outcome_col],
                "naa": f"{naa['naa']:.6f}" if naa["valid"] else "",
                "naa_signed": f"{signed['naa']:.6f}",
                "a_aff": f"{naa['a_aff']:.6f}",
                "a_del": f"{naa['a_del']:.6f}",
                "classification": naa["classification"],
            }
            for column in carry_cols:
                record.setdefault(column, row.get(column, ""))
            writer.writerow(record)
            handle.flush()
            completed += 1

            # Each item's (T, 20484) predictions and the cascade's intermediates stay
            # referenced until the next assignment, so on a 16 GB card the run died of an
            # allocator failure after three items. Releasing here bounds memory to one item.
            del result, naa, signed
            free_gpu_memory()

            elapsed = time.time() - started
            shown = f"{record['naa'] or 'UNDEFINED'}"
            print(
                f"[{index}/{len(pending)}] naa={shown} ({elapsed / index:.1f}s/item)",
                flush=True,
            )

    naa_values: list[float] = []
    undefined = 0
    with open(args.out, newline="", encoding="utf-8") as handle:
        for r in csv.DictReader(handle):
            if r.get("naa"):
                naa_values.append(float(r["naa"]))
            else:
                undefined += 1

    total = len(naa_values) + undefined
    print(f"\nWrote {args.out} ({total} rows, {completed} new this run)")
    print(f"NAA defined: {len(naa_values)}/{total}  undefined: {undefined}")
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
