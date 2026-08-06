"""Build the four-category manipulation corpus (proposal objective (i), §5.2).

Emits 375 items per category by default (1,500 total) across:

    high_outrage           partisan political content   (NELA-GT-2021)
    fear_activating        fabricated crisis / health    (ISOT Fake.csv)
    reward_hook            clickbait                     (Webis-Clickbait-17)
    neutral_informational  wire service + abstracts      (ISOT True.csv, PubMed)

Text only. The audio and video modalities in the proposal's Table 1 are out of
scope per docs/PROPOSAL-AMENDMENT.md; the released TRIBE v2 checkpoint and the
remaining project time do not support them.

Three properties this builder exists to guarantee
-------------------------------------------------
**Matched passage length across categories.** §5.2 specifies 50-200 word
passages, but three of the four sources are headline corpora and a headline is
~10 words. Feeding 150-word outrage articles against 12-word clickbait
headlines would confound category with sequence length: TRIBE consumes a 2 Hz
stimulus grid, so a longer passage is a longer time series and a different
number of TRs. Any NAA difference would then be a length artifact rather than a
content effect, and RQ II would be measuring the wrong thing. Every item is
therefore built into a passage over the SAME word budget by ``_to_passage``,
and ``_report`` prints the per-category length distribution so the balance is
auditable rather than assumed.

**ISOT dateline removal.** ISOT ``True.csv`` articles open with a wire dateline
("WASHINGTON (Reuters) - "). It is absent from ``Fake.csv``. A classifier can
score near-perfect AUC by detecting the literal string "(Reuters)", which is a
well-known artifact of this dataset and would silently invalidate objective
(vi). ``_strip_dateline`` removes it before the passage is built.

**No guessed schemas.** Every adapter declares the columns it requires and
validates them against the real file header, failing with actual-vs-expected
rather than a KeyError or, worse, a silently wrong corpus. Run ``--inspect``
first to print the true schema of each source you downloaded.

Sources are NOT auto-downloaded: NELA-GT-2021 is on Harvard Dataverse, ISOT on
the University of Victoria site, Webis-Clickbait-17 on Zenodo. Download them,
then point this script at the files.

Downstream note
---------------
Scan with ``--outcome-col category`` for objectives (iii)/(vi) and name every
other column the analysis needs in ``--carry-cols``, since the GPU pass is the
one step that cannot be repeated cheaply:

    python scripts/batch_naa.py --csv corpus.csv \
        --outcome-col category \
        --carry-cols id,manipulative,credibility,source_dataset,word_count \
        --out corpus_naa.csv

``word_count`` and ``source_dataset`` are carried so the length confound and
the dataset-leak check can be run against the scanned rows themselves rather
than re-joined on text.

Usage
-----
    python scripts/build_corpus.py --inspect \
        --nela-db nela-gt-2021.db --isot-fake Fake.csv

    python scripts/build_corpus.py \
        --nela-db nela-gt-2021.db --nela-labels labels.csv \
        --isot-fake Fake.csv --isot-true True.csv \
        --clickbait-instances instances.jsonl --clickbait-truth truth.jsonl \
        --pubmed pubmed_abstracts.csv \
        --out /kaggle/working/corpus.csv --per-category 375
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
import sqlite3
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Iterator, Optional

SEED = 17

# --min-words is the TARGET, not a floor: _to_passage stops at the first
# sentence boundary past it, so passages land just above this value and
# --max-words only caps the overshoot. 150 is chosen over §5.2's lower bound of
# 50 because out-of-distribution stimuli are the leading suspected confound
# behind the calibration null (TRIBE v2 was trained on naturalistic movie
# watching, and the null was produced by TTS'd single sentences at T~9 TRs).
# 150-200 words stays inside the §5.2 range while sitting far closer to that
# training distribution. The cost is pool size: sources too short to reach the
# target are dropped rather than admitted at a different length, which would
# reintroduce the length confound.
DEFAULT_MIN_WORDS = 150
DEFAULT_MAX_WORDS = 200
DEFAULT_PER_CATEGORY = 375
LENGTH_IMBALANCE_TOLERANCE = 0.15

# Resolved at call time by _to_passage, so --min-words/--max-words reach every
# reader without threading the budget through each one.
MIN_WORDS = DEFAULT_MIN_WORDS
MAX_WORDS = DEFAULT_MAX_WORDS

CATEGORIES = (
    "high_outrage",
    "fear_activating",
    "reward_hook",
    "neutral_informational",
)

NELA_TABLE = "newsdata"
NELA_COLUMNS = ("source", "title", "content")
NELA_LABEL_COLUMNS = ("source", "aggregated_label")
NELA_UNRELIABLE = 2

ISOT_COLUMNS = ("title", "text", "subject")
ISOT_FEAR_KEYWORDS = (
    "virus", "outbreak", "pandemic", "vaccine", "cancer", "disease",
    "death", "dead", "kill", "attack", "terror", "war", "crisis",
    "collapse", "warning", "danger", "threat", "emergency", "toxic",
    "poison", "radiation", "invasion", "shooting", "bomb",
)

CLICKBAIT_INSTANCE_KEYS = ("id", "targetParagraphs")
CLICKBAIT_TRUTH_KEYS = ("id", "truthClass")
CLICKBAIT_POSITIVE = "clickbait"

PUBMED_COLUMN = "abstract"

HYPERPARTISAN_COLUMNS = ("text", "partisan_intensity")

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
_DATELINE = re.compile(
    r"^\s*[A-Z][A-Za-z.\-/' ]{0,40}\s*\(\s*Reuters\s*\)\s*[-–—]\s*"
)
_AGENCY_MENTION = re.compile(r"\(\s*Reuters\s*\)", re.IGNORECASE)
_AGENCY_TOKEN = re.compile(r"\breuters\b", re.IGNORECASE)
_WHITESPACE = re.compile(r"\s+")


def _strip_dateline(text: str) -> str:
    """Remove the wire dateline that leaks the ISOT True/Fake split.

    ISOT ``True.csv`` is Reuters copy and opens with "WASHINGTON (Reuters) - ".
    ``Fake.csv`` never does. Left in, the string "(Reuters)" alone separates the
    classes almost perfectly, so any AUC computed against these labels measures
    dateline detection rather than the NAA index. Residual mid-body mentions are
    dropped too, since one surviving "(Reuters)" restores the leak.
    """
    cleaned = _DATELINE.sub("", text)
    cleaned = _AGENCY_MENTION.sub("", cleaned)
    return _WHITESPACE.sub(" ", cleaned).strip()


def _to_passage(
    text: str,
    min_words: Optional[int] = None,
    max_words: Optional[int] = None,
) -> Optional[str]:
    """Build a whole-sentence passage inside [min_words, max_words].

    Accumulates complete sentences until the budget is reached, so passages end
    on a sentence boundary. Truncating mid-sentence would hand TRIBE an
    unnatural token stream, and out-of-distribution stimuli are already the
    leading suspected confound behind the calibration null.

    Returns ``None`` when the source is too short to reach ``min_words``: a
    headline padded to length would be a fabrication, and a short item admitted
    unpadded would reintroduce the length confound this function prevents.
    """
    min_words = MIN_WORDS if min_words is None else min_words
    max_words = MAX_WORDS if max_words is None else max_words
    normalized = _WHITESPACE.sub(" ", text or "").strip()
    if not normalized:
        return None

    kept: list[str] = []
    count = 0
    for sentence in _SENTENCE_SPLIT.split(normalized):
        sentence = sentence.strip()
        if not sentence:
            continue
        length = len(sentence.split())
        if count + length > max_words:
            break
        kept.append(sentence)
        count += length
        if count >= min_words:
            break

    if count < min_words:
        return None
    return " ".join(kept)


def _require_columns(found: list[str], required: tuple[str, ...], label: str) -> None:
    missing = [column for column in required if column not in found]
    if missing:
        raise ValueError(
            f"{label}: missing column(s) {missing}.\n"
            f"  expected: {list(required)}\n"
            f"  found:    {found}\n"
            f"Run --inspect to print the real schema, then map the columns."
        )


def _csv_header(path: Path) -> list[str]:
    with open(path, newline="", encoding="utf-8", errors="replace") as handle:
        reader = csv.reader(handle)
        try:
            return next(reader)
        except StopIteration:
            raise ValueError(f"{path} is empty") from None


def read_nela(db_path: Path, labels_path: Path) -> Iterator[dict]:
    """High-outrage: articles from sources NELA-GT labels unreliable.

    ``aggregated_label`` is 0 reliable / 1 mixed / 2 unreliable at SOURCE level,
    not article level. ``credibility`` rescales it to [-1, +1] as §4.4 requires
    for the alpha_hat calibration, where +1 is reliable and -1 unreliable.
    """
    labels_header = _csv_header(labels_path)
    _require_columns(labels_header, NELA_LABEL_COLUMNS, f"NELA labels {labels_path}")

    credibility: dict[str, float] = {}
    with open(labels_path, newline="", encoding="utf-8", errors="replace") as handle:
        for row in csv.DictReader(handle):
            raw = (row.get("aggregated_label") or "").strip()
            if raw == "":
                continue
            try:
                label = int(float(raw))
            except ValueError:
                continue
            credibility[row["source"].strip()] = 1.0 - label

    if not credibility:
        raise ValueError(f"{labels_path}: no usable aggregated_label values")

    connection = sqlite3.connect(str(db_path))
    try:
        available = [
            row[1] for row in connection.execute(f"PRAGMA table_info({NELA_TABLE})")
        ]
        if not available:
            raise ValueError(
                f"{db_path}: table '{NELA_TABLE}' not found. "
                f"Run --inspect to list the real tables."
            )
        _require_columns(available, NELA_COLUMNS, f"NELA db {db_path}:{NELA_TABLE}")

        query = f"SELECT source, title, content FROM {NELA_TABLE}"
        for source, title, content in connection.execute(query):
            source = (source or "").strip()
            score = credibility.get(source)
            if score is None or score > -1.0:
                continue
            passage = _to_passage(content or "")
            if passage is None:
                continue
            yield {
                "text": passage,
                "source_dataset": "NELA-GT-2021",
                "source_name": source,
                "credibility": f"{score:.1f}",
                "title": (title or "").strip(),
            }
    finally:
        connection.close()


def read_isot(path: Path, fear_only: bool, dataset: str) -> Iterator[dict]:
    """ISOT Fake.csv (fear-activating) or True.csv (neutral wire service).

    ``fear_only`` keeps items whose title or body carries crisis/health threat
    language, which is what §5.2 asks of this category. Without it the category
    would be "any fabricated news" rather than "fear-activating".
    """
    header = _csv_header(path)
    _require_columns(header, ISOT_COLUMNS, f"ISOT {path}")

    with open(path, newline="", encoding="utf-8", errors="replace") as handle:
        for row in csv.DictReader(handle):
            title = (row.get("title") or "").strip()
            body = row.get("text") or ""
            if fear_only:
                haystack = f"{title} {body[:400]}".lower()
                if not any(word in haystack for word in ISOT_FEAR_KEYWORDS):
                    continue
            passage = _to_passage(_strip_dateline(body))
            if passage is None:
                continue
            yield {
                "text": passage,
                "source_dataset": dataset,
                "source_name": (row.get("subject") or "").strip(),
                "credibility": "",
                "title": title,
            }


def read_clickbait(instances_path: Path, truth_path: Path) -> Iterator[dict]:
    """Reward-hook: Webis-Clickbait-17 items judged clickbait.

    ``targetParagraphs`` (the linked article body) is used rather than
    ``postText`` (the teaser). The teaser is the clickbait, but it is ~10 words
    and cannot meet the §5.2 length spec without reintroducing the length
    confound. The body is the content the hook delivers the reader to, and it is
    length-comparable with the other three categories.
    """
    for path, keys in (
        (instances_path, CLICKBAIT_INSTANCE_KEYS),
        (truth_path, CLICKBAIT_TRUTH_KEYS),
    ):
        with open(path, encoding="utf-8", errors="replace") as handle:
            first = handle.readline().strip()
        if not first:
            raise ValueError(f"{path} is empty")
        _require_columns(list(json.loads(first).keys()), keys, f"clickbait {path}")

    truth: dict[str, str] = {}
    with open(truth_path, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            truth[str(record["id"])] = str(record.get("truthClass", "")).strip()

    with open(instances_path, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            if truth.get(str(record["id"])) != CLICKBAIT_POSITIVE:
                continue
            paragraphs = record.get("targetParagraphs") or []
            passage = _to_passage(" ".join(paragraphs))
            if passage is None:
                continue
            yield {
                "text": passage,
                "source_dataset": "Webis-Clickbait-17",
                "source_name": "clickbait",
                "credibility": "",
                "title": " ".join(record.get("postText") or []).strip(),
            }


def read_hyperpartisan(path: Path) -> Iterator[dict]:
    """High-outrage: SemEval-2019 Task 4 articles labelled hyperpartisan.

    Stands in for NELA-GT-2021, which the proposal named but whose authors
    deaccessioned it on 1 January 2024. Produced by ``fetch_hyperpartisan.py``,
    which has already applied the label filter and stripped the source markup.

    ``credibility`` is left empty on purpose. This dataset carries a political
    lean, not a reliability rating, and writing lean into a credibility column
    would silently change what objective (iv) regresses against. The lean is
    carried separately as ``partisan_intensity``.
    """
    header = _csv_header(path)
    _require_columns(header, HYPERPARTISAN_COLUMNS, f"hyperpartisan {path}")

    with open(path, newline="", encoding="utf-8", errors="replace") as handle:
        for row in csv.DictReader(handle):
            passage = _to_passage(row.get("text") or "")
            if passage is None:
                continue
            yield {
                "text": passage,
                "source_dataset": "SemEval-2019-Task4",
                "source_name": "hyperpartisan",
                "credibility": "",
                "partisan_intensity": (row.get("partisan_intensity") or "").strip(),
                "title": (row.get("title") or "").strip(),
            }


def read_pubmed(path: Path, column: str = PUBMED_COLUMN) -> Iterator[dict]:
    """Neutral-informational: scientific abstracts."""
    header = _csv_header(path)
    _require_columns(header, (column,), f"PubMed {path}")

    with open(path, newline="", encoding="utf-8", errors="replace") as handle:
        for row in csv.DictReader(handle):
            passage = _to_passage(row.get(column) or "")
            if passage is None:
                continue
            yield {
                "text": passage,
                "source_dataset": "PubMed",
                "source_name": "pubmed",
                "credibility": "1.0",
                "title": "",
            }


def _sample(pool: list[dict], count: int, category: str) -> list[dict]:
    """Draw ``count`` items, balanced across the category's source datasets.

    A flat random draw is proportional to pool size, which quietly destroys
    the point of using more than one source. ``neutral_informational`` pools
    ~13.7k ISOT wire articles against 150 PubMed abstracts, so a flat draw of
    100 returned 99 wire and 1 abstract: the neutral category became a single
    publisher's house style, while the other three categories came from
    elsewhere. Any separation could then be publisher detection rather than
    the NAA index, which is the same failure the dateline strip exists to
    prevent.

    Sources are therefore drawn round-robin. A source that runs out yields its
    remaining share to the others, so the count is still met.
    """
    rng = random.Random(f"{SEED}:{category}")
    if len(pool) < count:
        print(
            f"[WARN] {category}: only {len(pool)} items available, "
            f"{count} requested. Category will be short, and unequal category "
            f"sizes weaken the Cohen's d and KL estimates in objective (iii).",
            file=sys.stderr,
        )
        rng.shuffle(pool)
        return pool

    by_source: dict[str, list[dict]] = {}
    for item in pool:
        by_source.setdefault(item["source_dataset"], []).append(item)
    for items in by_source.values():
        rng.shuffle(items)

    if len(by_source) > 1:
        shares = {name: len(items) for name, items in by_source.items()}
        print(f"  {category}: balancing across {shares}")

    drawn: list[dict] = []
    queues = sorted(by_source.items())
    while len(drawn) < count:
        progressed = False
        for _, items in queues:
            if len(drawn) >= count:
                break
            if items:
                drawn.append(items.pop())
                progressed = True
        if not progressed:
            break
    return drawn


def _report(rows: list[dict]) -> bool:
    """Print per-category length stats. Returns False if lengths are imbalanced.

    The length check is the whole point: if categories differ materially in word
    count, a category contrast in NAA cannot be attributed to content.
    """
    by_category: dict[str, list[int]] = defaultdict(list)
    for row in rows:
        by_category[row["category"]].append(int(row["word_count"]))

    print("\nper-category word count:")
    means: list[float] = []
    for category in CATEGORIES:
        counts = by_category.get(category, [])
        if not counts:
            print(f"  {category:<24} EMPTY")
            continue
        mean = statistics.fmean(counts)
        means.append(mean)
        print(
            f"  {category:<24} n={len(counts):<5} "
            f"mean={mean:6.1f}  median={statistics.median(counts):6.1f}  "
            f"min={min(counts):3d}  max={max(counts):3d}"
        )

    if len(means) < 2:
        return False

    spread = (max(means) - min(means)) / max(means)
    balanced = spread <= LENGTH_IMBALANCE_TOLERANCE
    verdict = "OK" if balanced else "IMBALANCED"
    print(
        f"\nlength balance: {spread:.1%} spread across category means "
        f"({verdict}, tolerance {LENGTH_IMBALANCE_TOLERANCE:.0%})"
    )
    if not balanced:
        print(
            "[WARN] Category means differ by more than the tolerance. An NAA "
            "difference between categories may be a passage-length artifact "
            "rather than a content effect. Narrow the word budget "
            "(--min-words/--max-words) until this is within tolerance before "
            "running the GPU pass.",
            file=sys.stderr,
        )
    return balanced


def _inspect(args: argparse.Namespace) -> int:
    """Print the real schema of every source provided. Guesses nothing."""
    if args.nela_db:
        print(f"\n=== NELA db: {args.nela_db} ===")
        connection = sqlite3.connect(str(args.nela_db))
        try:
            tables = [
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            ]
            print(f"tables: {tables}")
            for table in tables:
                columns = [
                    row[1] for row in connection.execute(f"PRAGMA table_info({table})")
                ]
                count = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
                print(f"  {table}: rows={count[0]} columns={columns}")
        finally:
            connection.close()

    for label, path in (
        ("NELA labels", args.nela_labels),
        ("hyperpartisan", args.hyperpartisan),
        ("ISOT fake", args.isot_fake),
        ("ISOT true", args.isot_true),
        ("PubMed", args.pubmed),
    ):
        if path:
            print(f"\n=== {label}: {path} ===")
            print(f"columns: {_csv_header(path)}")

    for label, path in (
        ("clickbait instances", args.clickbait_instances),
        ("clickbait truth", args.clickbait_truth),
    ):
        if path:
            print(f"\n=== {label}: {path} ===")
            with open(path, encoding="utf-8", errors="replace") as handle:
                first = handle.readline().strip()
            print(f"keys: {list(json.loads(first).keys()) if first else 'EMPTY'}")

    return 0


def _drop_agency_mentions(pool: list[dict], label: str) -> list[dict]:
    """Remove any item still naming the wire agency, in any form.

    ``_strip_dateline`` removes the leading "CITY (Reuters) - " and the
    parenthesised form, but it only runs on the ISOT readers, and neither form
    catches a bare "told Reuters" mid-sentence. Either survivor restores the
    leak that lets a classifier score on publisher detection instead of on the
    NAA index, so the item is dropped rather than edited: excising the token
    in place leaves a grammatical scar that is itself a tell, and the pools
    are large enough that dropping costs nothing.
    """
    kept = [item for item in pool if not _AGENCY_TOKEN.search(item["text"])]
    dropped = len(pool) - len(kept)
    if dropped:
        print(f"  {label}: dropped {dropped} items naming the wire agency")
    return kept


def _collect(args: argparse.Namespace) -> dict[str, list[dict]]:
    pools: dict[str, list[dict]] = {category: [] for category in CATEGORIES}

    if args.hyperpartisan:
        pools["high_outrage"] = list(read_hyperpartisan(args.hyperpartisan))
    elif args.nela_db and args.nela_labels:
        pools["high_outrage"] = list(read_nela(args.nela_db, args.nela_labels))
    if args.isot_fake:
        pools["fear_activating"] = list(
            read_isot(args.isot_fake, fear_only=True, dataset="ISOT-fake")
        )
    if args.clickbait_instances and args.clickbait_truth:
        pools["reward_hook"] = list(
            read_clickbait(args.clickbait_instances, args.clickbait_truth)
        )

    neutral: list[dict] = []
    if args.isot_true:
        neutral.extend(read_isot(args.isot_true, fear_only=False, dataset="ISOT-true"))
    if args.pubmed:
        neutral.extend(read_pubmed(args.pubmed))
    pools["neutral_informational"] = neutral

    return {
        category: _drop_agency_mentions(pool, category)
        for category, pool in pools.items()
    }


def main() -> int:
    global MIN_WORDS, MAX_WORDS

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nela-db", type=Path, help="nela-gt-2021.db (sqlite)")
    parser.add_argument("--nela-labels", type=Path, help="NELA labels.csv")
    parser.add_argument(
        "--hyperpartisan",
        type=Path,
        help="hyperpartisan.csv from fetch_hyperpartisan.py; supersedes --nela-db",
    )
    parser.add_argument("--isot-fake", type=Path, help="ISOT Fake.csv")
    parser.add_argument("--isot-true", type=Path, help="ISOT True.csv")
    parser.add_argument("--clickbait-instances", type=Path, help="instances.jsonl")
    parser.add_argument("--clickbait-truth", type=Path, help="truth.jsonl")
    parser.add_argument("--pubmed", type=Path, help="PubMed abstracts CSV")
    parser.add_argument("--pubmed-col", default=PUBMED_COLUMN)
    parser.add_argument("--out", type=Path, default=Path("/kaggle/working/corpus.csv"))
    parser.add_argument("--per-category", type=int, default=DEFAULT_PER_CATEGORY)
    parser.add_argument("--min-words", type=int, default=DEFAULT_MIN_WORDS)
    parser.add_argument("--max-words", type=int, default=DEFAULT_MAX_WORDS)
    parser.add_argument("--inspect", action="store_true", help="print schemas, exit")
    args = parser.parse_args()

    if args.inspect:
        return _inspect(args)

    if args.min_words >= args.max_words:
        parser.error("--min-words must be below --max-words")

    MIN_WORDS, MAX_WORDS = args.min_words, args.max_words

    pools = _collect(args)
    if not any(pools.values()):
        parser.error("no sources provided; pass at least one dataset path")

    rows: list[dict] = []
    for category in CATEGORIES:
        pool = pools[category]
        print(f"{category:<24} pool={len(pool)}")
        for index, item in enumerate(_sample(pool, args.per_category, category)):
            rows.append(
                {
                    "id": f"{category}-{index:04d}",
                    "text": item["text"],
                    "category": category,
                    "manipulative": "0" if category == "neutral_informational" else "1",
                    "credibility": item["credibility"],
                    "partisan_intensity": item.get("partisan_intensity", ""),
                    "source_dataset": item["source_dataset"],
                    "source_name": item["source_name"],
                    "word_count": str(len(item["text"].split())),
                }
            )

    if not rows:
        print("[FAIL] no rows survived filtering", file=sys.stderr)
        return 1

    random.Random(SEED).shuffle(rows)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "id", "text", "category", "manipulative", "credibility",
        "partisan_intensity", "source_dataset", "source_name", "word_count",
    ]
    with open(args.out, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nWrote {args.out} ({len(rows)} rows)")
    balanced = _report(rows)

    leaked = sum(1 for row in rows if "reuters" in row["text"].lower())
    print(f"dateline leak check: {leaked} rows still mention Reuters")
    if leaked:
        print(
            "[WARN] Residual agency mentions survive. Any AUC against the ISOT "
            "labels may be detecting the wire source, not the NAA index.",
            file=sys.stderr,
        )

    short = {
        category: sum(1 for row in rows if row["category"] == category)
        for category in CATEGORIES
    }
    missing = {c: n for c, n in short.items() if n < args.per_category}
    if missing:
        print(
            f"[FAIL] categories under --per-category {args.per_category}: "
            f"{missing}. A corpus short of a whole category cannot support the "
            "objective (iii) contrast it exists to measure.",
            file=sys.stderr,
        )

    return 0 if balanced and not leaked and not missing else 1


if __name__ == "__main__":
    sys.exit(main())
