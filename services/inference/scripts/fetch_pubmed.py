"""Fetch PubMed abstracts for the neutral-informational corpus category.

Writes a CSV with an ``abstract`` column, which is what ``build_corpus.py``'s
``read_pubmed`` adapter expects. Sources the neutral baseline from a second
register (scientific writing) so it is not drawn entirely from the ISOT wire
service, which would confound the neutral category with a single publisher's
house style.

Sampling is deliberately broad rather than topic-selected. Hand-picking
subject terms would let the operator tune the neutral category's emotional
content after seeing results, and disease-heavy terms in particular would
leak threat vocabulary into the baseline and blur it against
``fear_activating``. The query below filters only on having an abstract, being
English, and being a journal article in a fixed date window, then takes a
seeded random sample of the returned PMIDs. Both the query and the seed are
recorded in the output so the draw is reproducible.

NCBI E-utilities allows 3 requests/second unencrypted. ``--api-key`` raises
that to 10/s but is not required.

Usage
-----
    python scripts/fetch_pubmed.py --n 200 --out pubmed_abstracts.csv
"""

from __future__ import annotations

import argparse
import csv
import random
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
DEFAULT_QUERY = (
    'hasabstract[text] AND english[lang] AND journal article[pt] '
    'AND ("2019/01/01"[dp] : "2021/12/31"[dp])'
)
SEED = 20260716
SEARCH_POOL = 5000
BATCH = 100
MIN_WORDS = 150
REQUEST_PAUSE = 0.4


def _get(url: str, retries: int = 3) -> bytes:
    last: Exception | None = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=60) as response:
                return response.read()
        except Exception as exc:
            last = exc
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"E-utilities request failed after {retries} tries: {last}")


def search_pmids(query: str, pool: int, api_key: str) -> list[str]:
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": str(pool),
        "retmode": "json",
        "sort": "pub_date",
    }
    if api_key:
        params["api_key"] = api_key
    payload = _get(f"{EUTILS}/esearch.fcgi?{urllib.parse.urlencode(params)}")

    import json

    result = json.loads(payload)["esearchresult"]
    return list(result.get("idlist", []))


def fetch_abstracts(pmids: list[str], api_key: str) -> list[dict]:
    records: list[dict] = []
    for start in range(0, len(pmids), BATCH):
        chunk = pmids[start : start + BATCH]
        params = {"db": "pubmed", "id": ",".join(chunk), "retmode": "xml"}
        if api_key:
            params["api_key"] = api_key
        payload = _get(f"{EUTILS}/efetch.fcgi?{urllib.parse.urlencode(params)}")
        root = ET.fromstring(payload)

        for article in root.iter("PubmedArticle"):
            pmid_node = article.find(".//PMID")
            texts = [
                "".join(node.itertext()).strip()
                for node in article.iter("AbstractText")
            ]
            abstract = " ".join(t for t in texts if t).strip()
            if not abstract or len(abstract.split()) < MIN_WORDS:
                continue
            records.append(
                {
                    "pmid": pmid_node.text if pmid_node is not None else "",
                    "abstract": abstract,
                }
            )

        print(
            f"  fetched {min(start + BATCH, len(pmids))}/{len(pmids)} PMIDs, "
            f"{len(records)} usable",
            flush=True,
        )
        time.sleep(REQUEST_PAUSE)
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=200)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--query", default=DEFAULT_QUERY)
    parser.add_argument("--pool", type=int, default=SEARCH_POOL)
    parser.add_argument("--api-key", default="")
    args = parser.parse_args()

    print(f"Query: {args.query}")
    pmids = search_pmids(args.query, args.pool, args.api_key)
    if not pmids:
        print("[FAIL] search returned no PMIDs", file=sys.stderr)
        return 1
    print(f"Search returned {len(pmids)} PMIDs")

    random.Random(SEED).shuffle(pmids)
    # Over-draw: many abstracts fall under MIN_WORDS and are discarded.
    draw = pmids[: min(len(pmids), args.n * 4)]

    records = fetch_abstracts(draw, args.api_key)
    if len(records) < args.n:
        print(
            f"[WARN] only {len(records)} abstracts reached {MIN_WORDS} words, "
            f"{args.n} requested. Raise --pool or lower --n.",
            file=sys.stderr,
        )
    records = records[: args.n]

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["pmid", "abstract", "query", "seed"])
        writer.writeheader()
        for record in records:
            writer.writerow({**record, "query": args.query, "seed": SEED})

    words = sorted(len(r["abstract"].split()) for r in records)
    print(f"\nWrote {args.out} ({len(records)} abstracts)")
    if words:
        print(f"  words min/median/max: {words[0]}/{words[len(words) // 2]}/{words[-1]}")
    return 0 if len(records) >= args.n else 2


if __name__ == "__main__":
    sys.exit(main())
