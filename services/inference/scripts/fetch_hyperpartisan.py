"""Fetch hyperpartisan news articles for the high_outrage corpus category.

Replaces NELA-GT-2021, which the proposal named but whose authors deaccessioned
it on 1 January 2024; it is now behind manual per-application review and was
unreachable with a valid Harvard Dataverse token (403 on every file, empty
version listing).

Source is SemEval-2019 Task 4 (PAN @ Webis), CC-BY-4.0, read through the
HuggingFace rows API so a few hundred articles cost a few MB instead of the
3.2 GB parquet export.

Two properties of this source that matter for the corpus
--------------------------------------------------------
**The label is article-level, not publisher-level.** NELA's ``aggregated_label``
rates a source's credibility, so using it to select outraged *articles* was
always a proxy. ``hyperpartisan`` here is assigned per article. Since
``high_outrage`` is defined by content, the article-level label matches the
construct more closely than the one it replaces.

**``bias`` is an ordinal lean, not a credibility score.** Its classes are
right, right-center, least, left-center, left, so index 2 is the least-biased
centre and ``|bias - 2|`` is a partisan-extremity score on 0 to 2. That is
emitted as ``partisan_intensity`` and is NOT written to ``credibility``:
political lean and factual reliability are different quantities, and NELA's
credibility outcome for objective (iv) has no equivalent in this dataset.

Usage
-----
    python scripts/fetch_hyperpartisan.py --n 200 --out hyperpartisan.csv
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import random
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROWS_API = "https://datasets-server.huggingface.co/rows"
DATASET = "pietrolesci/hyperpartisan_news_detection"
CONFIG = "default"
SPLIT = "train"
SEED = 20260716
BATCH = 100
MIN_WORDS = 150
CENTRE_BIAS = 2
REQUEST_PAUSE = 0.3

_TAG = re.compile(r"<[^>]+>")
_WHITESPACE = re.compile(r"\s+")


def _clean(raw: str) -> str:
    """Strip the markup the raw field carries.

    Rows arrive as "Headline <p>body</p><p>more</p>" with HTML entities left
    encoded. Both would reach the TTS stage verbatim and be read aloud as
    literal tag text, so they are removed before any length check.
    """
    text = _TAG.sub(" ", raw or "")
    text = html.unescape(text)
    return _WHITESPACE.sub(" ", text).strip()


def _get(url: str, retries: int = 3) -> dict:
    last: Exception | None = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=60) as response:
                return json.loads(response.read())
        except Exception as exc:
            last = exc
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"rows API failed after {retries} tries: {last}")


def fetch_rows(offset: int, length: int) -> list[dict]:
    params = {
        "dataset": DATASET,
        "config": CONFIG,
        "split": SPLIT,
        "offset": str(offset),
        "length": str(length),
    }
    payload = _get(f"{ROWS_API}?{urllib.parse.urlencode(params)}")
    if "rows" not in payload:
        raise RuntimeError(f"unexpected rows API response: {str(payload)[:200]}")
    return [r["row"] for r in payload["rows"]]


def collect(target: int, max_offset: int) -> list[dict]:
    """Walk randomly-placed windows until ``target`` usable articles are found.

    Sequential reads from offset 0 would draw one contiguous slice of the
    publisher ordering, so the sample would be a handful of outlets rather than
    the corpus. Windows are drawn from a seeded shuffle instead, which keeps
    the draw reproducible without being one block.
    """
    windows = list(range(0, max_offset, BATCH))
    random.Random(SEED).shuffle(windows)

    kept: list[dict] = []
    seen: set[int] = set()
    for offset in windows:
        if len(kept) >= target:
            break
        for row in fetch_rows(offset, BATCH):
            if not row.get("hyperpartisan"):
                continue
            uid = row.get("uid")
            if uid in seen:
                continue
            text = _clean(row.get("text") or row.get("news_text") or "")
            if len(text.split()) < MIN_WORDS:
                continue
            seen.add(uid)
            bias = row.get("bias")
            kept.append(
                {
                    "uid": uid,
                    "text": text,
                    "title": (row.get("title") or "").strip(),
                    "bias": bias,
                    "partisan_intensity": (
                        "" if bias is None else f"{abs(int(bias) - CENTRE_BIAS)}"
                    ),
                }
            )
        print(f"  offset {offset}: {len(kept)}/{target} usable", flush=True)
        time.sleep(REQUEST_PAUSE)
    return kept


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=200)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--max-offset", type=int, default=100_000)
    args = parser.parse_args()

    print(f"Source: {DATASET} [{CONFIG}/{SPLIT}], CC-BY-4.0")
    rows = collect(args.n, args.max_offset)
    if len(rows) < args.n:
        print(
            f"[WARN] only {len(rows)} articles reached {MIN_WORDS} words, "
            f"{args.n} requested. Raise --max-offset.",
            file=sys.stderr,
        )
    rows = rows[: args.n]
    if not rows:
        print("[FAIL] no usable articles", file=sys.stderr)
        return 1

    args.out.parent.mkdir(parents=True, exist_ok=True)
    fields = ["uid", "text", "title", "bias", "partisan_intensity"]
    with open(args.out, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    words = sorted(len(r["text"].split()) for r in rows)
    print(f"\nWrote {args.out} ({len(rows)} articles)")
    print(f"  words min/median/max: {words[0]}/{words[len(words) // 2]}/{words[-1]}")
    return 0 if len(rows) >= args.n else 2


if __name__ == "__main__":
    sys.exit(main())
