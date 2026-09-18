"""Lexical and sentiment baselines against the same manipulative label (§5.3).

The index reports AUC 0.6274 on ``naa_signed``. A reader's first question is
whether a bag of words does better for no GPU at all. This script answers it on
the identical 400 rows and the identical label.

The comparison has to be read against how the corpus was built. Every
``source_dataset`` contributes exactly one class, so a lexical model scored over
all four categories can reach its answer through source vocabulary alone, and
leave-one-source-out is not available as a correction: it leaves a single-class
test fold and no computable per-fold AUC. Two readings are reported instead.

    full corpus  400 items, 5-fold stratified CV, source confounded with label
    ISOT only    150 items from one origin corpus with both classes present, so
                 a lexical model cannot win on which corpus a row came from

A source-identity probe is reported alongside them: how well the same features
recover ``source_dataset`` itself. Near ceiling there means the full-corpus
lexical figure measures provenance, not manipulation.

Usage
-----
    python scripts/baselines.py --csv data/final/corpus_naa.csv \
        --out data/final/baselines.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import make_pipeline

SEED = 42
BOOTSTRAP_DRAWS = 2000
ISOT_PREFIX = "ISOT"


def _bootstrap_ci(labels: np.ndarray, scores: np.ndarray) -> tuple[float, float]:
    rng = np.random.default_rng(SEED)
    n = labels.shape[0]
    draws = []
    for _ in range(BOOTSTRAP_DRAWS):
        idx = rng.integers(0, n, n)
        if len(np.unique(labels[idx])) < 2:
            continue
        draws.append(roc_auc_score(labels[idx], scores[idx]))
    return float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))


def _scored(name: str, labels: np.ndarray, scores: np.ndarray, split: str) -> dict:
    auc = float(roc_auc_score(labels, scores))
    low, high = _bootstrap_ci(labels, scores)
    return {
        "model": name,
        "split": split,
        "n": int(labels.shape[0]),
        "auc": auc,
        "ci95": [low, high],
    }


def _tfidf_pipeline():
    return make_pipeline(
        TfidfVectorizer(sublinear_tf=True, min_df=2, ngram_range=(1, 2)),
        LogisticRegression(max_iter=2000, random_state=SEED),
    )


def _out_of_fold(texts: pd.Series, labels: np.ndarray, folds) -> np.ndarray:
    scores = np.full(labels.shape[0], np.nan)
    for train_idx, test_idx in folds:
        model = _tfidf_pipeline()
        model.fit(texts.iloc[train_idx], labels[train_idx])
        scores[test_idx] = model.predict_proba(texts.iloc[test_idx])[:, 1]
    return scores


def _source_identity_probe(texts: pd.Series, groups: np.ndarray) -> dict:
    predicted = cross_val_predict(
        _tfidf_pipeline(),
        texts,
        groups,
        cv=StratifiedKFold(5, shuffle=True, random_state=SEED),
    )
    counts = np.bincount(pd.factorize(groups)[0])
    return {
        "accuracy": float(np.mean(predicted == groups)),
        "n_sources": int(len(np.unique(groups))),
        "chance": float(counts.max() / groups.shape[0]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    frame = pd.read_csv(args.csv)
    labels = frame["manipulative"].astype(int).to_numpy()
    groups = frame["source_dataset"].to_numpy()
    texts = frame["text"]
    analyzer = SentimentIntensityAnalyzer()

    results = [_scored("NAA signed index", labels, frame["naa_signed"].to_numpy(), "none")]

    compound = np.array([analyzer.polarity_scores(t)["compound"] for t in texts])
    results.append(_scored("VADER compound", labels, compound, "none"))
    results.append(_scored("VADER |compound|", labels, np.abs(compound), "none"))

    folds = list(StratifiedKFold(5, shuffle=True, random_state=SEED).split(texts, labels))
    results.append(
        _scored("TF-IDF + logistic", labels, _out_of_fold(texts, labels, folds), "stratified")
    )

    within = frame[frame["source_dataset"].str.startswith(ISOT_PREFIX)].reset_index(drop=True)
    within_labels = within["manipulative"].astype(int).to_numpy()
    within_texts = within["text"]
    within_folds = list(
        StratifiedKFold(5, shuffle=True, random_state=SEED).split(within_texts, within_labels)
    )
    within_compound = np.array([analyzer.polarity_scores(t)["compound"] for t in within_texts])
    results.append(
        _scored(
            "TF-IDF + logistic",
            within_labels,
            _out_of_fold(within_texts, within_labels, within_folds),
            "ISOT only, stratified",
        )
    )
    results.append(_scored("VADER compound", within_labels, within_compound, "ISOT only"))
    results.append(
        _scored("NAA signed index", within_labels, within["naa_signed"].to_numpy(), "ISOT only")
    )

    probe = _source_identity_probe(texts, groups)
    single_class = sorted(
        {str(s) for s in pd.unique(groups) if len(np.unique(labels[groups == s])) < 2}
    )
    payload = {
        "corpus": str(args.csv),
        "n_items": int(frame.shape[0]),
        "seed": SEED,
        "bootstrap_draws": BOOTSTRAP_DRAWS,
        "single_class_sources": single_class,
        "leave_one_source_out": "undefined: every source contributes exactly one class",
        "source_identity_probe": probe,
        "results": results,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    header = f"{'model':<20}{'split':<24}{'n':>5}{'AUC':>9}   95% CI"
    print(header)
    for row in results:
        ci = f"[{row['ci95'][0]:.4f}, {row['ci95'][1]:.4f}]"
        print(f"{row['model']:<20}{row['split']:<24}{row['n']:>5}{row['auc']:>9.4f}   {ci}")
    print("")
    print(
        f"source-identity probe: accuracy {probe['accuracy']:.4f} over "
        f"{probe['n_sources']} sources, chance {probe['chance']:.4f}"
    )
    print(f"single-class sources: {', '.join(single_class)}")
    print("leave-one-source-out is undefined on this corpus for that reason.")
    print(f"written to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
