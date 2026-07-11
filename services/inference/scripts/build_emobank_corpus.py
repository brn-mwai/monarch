"""Build a labeled calibration corpus from EmoBank writer-normalized ratings.

EmoBank (Buechel & Hahn, 2017; CC-BY 4.0) carries per-sentence
valence/arousal/dominance ratings. The writer-normalized CSV columns are
``label1``=valence, ``label2``=arousal, ``label3``=dominance.

Arousal is the outcome ``alpha_hat`` gets calibrated against, so it is the
only label kept. Most EmoBank sentences sit at the neutral midpoint, and a
plain random sample would leave the regression almost no variance in the
outcome; rows are therefore sampled evenly across arousal bins and the
per-bin counts are printed so the sampling is stated, not hidden.

Usage
-----
    python scripts/build_emobank_corpus.py --raw emobank.csv \
        --out data/emobank_corpus.csv --per-bin 8
"""

from __future__ import annotations

import argparse
import csv
import random
import sys
from collections import defaultdict
from pathlib import Path

AROUSAL_COL = "label2"
BIN_EDGES = (0.35, 0.45, 0.55, 0.65)
MIN_WORDS = 8
SEED = 17


def _bin_of(arousal: float) -> int:
    for index, edge in enumerate(BIN_EDGES):
        if arousal < edge:
            return index
    return len(BIN_EDGES)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--per-bin", type=int, default=8)
    args = parser.parse_args()

    buckets: dict[int, list[dict]] = defaultdict(list)
    with open(args.raw, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            text = row["text"].strip()
            if len(text.split()) < MIN_WORDS:
                continue
            arousal = float(row[AROUSAL_COL])
            buckets[_bin_of(arousal)].append({"text": text, "arousal": arousal})

    rng = random.Random(SEED)
    selected: list[dict] = []
    for bin_index in sorted(buckets):
        rows = buckets[bin_index]
        rng.shuffle(rows)
        take = rows[: args.per_bin]
        selected.extend(take)
        print(f"arousal bin {bin_index}: {len(take)} of {len(rows)} available")

    if not selected:
        print("[FAIL] no rows survived filtering", file=sys.stderr)
        return 1

    rng.shuffle(selected)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["text", "arousal"])
        writer.writeheader()
        for row in selected:
            writer.writerow({"text": row["text"], "arousal": f"{row['arousal']:.4f}"})

    arousals = [row["arousal"] for row in selected]
    print(f"\nWrote {args.out} ({len(selected)} rows)")
    print(f"arousal range: [{min(arousals):.3f}, {max(arousals):.3f}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
