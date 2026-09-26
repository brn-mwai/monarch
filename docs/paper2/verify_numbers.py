"""Check every number quoted in paper2.tex against the committed artifacts. CPU only.

Most numbers are read from JSON written by the scripts in services/inference/scripts. Four
quantities had no committed script and are computed here from the scan CSVs: the scan-order
check, the paired bootstrap of the between-session difference in eta^2, the second session's
spread, and the closed-form spinodal field used to cross-check field_bound.json.

    python verify_numbers.py

Exits non-zero if any quoted value disagrees with its source at the printed precision.
"""

from __future__ import annotations

import json
import sys
from math import atanh, sqrt
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

DATA = Path(__file__).resolve().parents[2] / "services" / "inference" / "data"
FINAL = DATA / "final"
SEED = 42
DRAWS = 5000

failures: list[str] = []


def load(name: str) -> dict:
    return json.loads((FINAL / name).read_text(encoding="utf-8"))


def check(label: str, quoted: float, value: float, digits: int, source: str) -> None:
    ok = round(value, digits) == round(quoted, digits)
    print(f"{'OK ' if ok else 'BAD'} {label:<44} paper={quoted:<12} source={value:<.6g}  [{source}]")
    if not ok:
        failures.append(label)


def eta_squared(values: np.ndarray, groups: np.ndarray) -> float:
    grand = values.mean()
    between = sum((groups == g).sum() * (values[groups == g].mean() - grand) ** 2 for g in np.unique(groups))
    return float(between / ((values - grand) ** 2).sum())


def spinodal_field(beta_j: float) -> float:
    """h_c for m = tanh(beta_j m + h): the field at which the metastable branch vanishes."""
    m_s = sqrt(1.0 - 1.0 / beta_j)
    return sqrt(beta_j * (beta_j - 1.0)) - atanh(m_s)


def main() -> int:
    rq = load("rq_answers.json")
    sep = rq["rq2_distribution"]["separation"]
    cats = rq["rq2_distribution"]["per_category"]
    check("eta^2 session A", 0.1068, sep["eta_squared"], 4, "rq_answers.json")
    check("F session A", 15.779, sep["f_statistic"], 3, "rq_answers.json")
    check("p session A (x1e-9)", 1.035, sep["p_value"] * 1e9, 3, "rq_answers.json")
    check("d fear vs neutral", 0.9389, cats["fear_activating"]["cohens_d_vs_baseline"], 4, "rq_answers.json")
    check("d reward vs neutral", 0.3188, cats["reward_hook"]["cohens_d_vs_baseline"], 4, "rq_answers.json")
    check("d outrage vs neutral", 0.0300, cats["high_outrage"]["cohens_d_vs_baseline"], 4, "rq_answers.json")
    check("AUC index", 0.6274, rq["rq1_validation"]["auc"], 4, "rq_answers.json")
    check("F1 (in-sample threshold)", 0.6680, rq["rq1_validation"]["f1"], 4, "rq_answers.json")

    power = json.loads((DATA / "power_statement.json").read_text(encoding="utf-8"))
    check("min detectable eta^2", 0.0268, power["anova"]["minimum_detectable_eta_squared"], 4, "power_statement.json")
    check("min detectable AUC", 0.5916, power["auc"]["minimum_detectable_auc"], 4, "power_statement.json")

    split = load("outrage_split.json")["contrasts_vs_baseline"]
    for cat, comp, d in [("high_outrage", "a_aff", 0.507), ("high_outrage", "a_del", 0.491),
                         ("fear_activating", "a_aff", 0.613), ("fear_activating", "a_del", -0.098),
                         ("reward_hook", "a_aff", 0.261), ("reward_hook", "a_del", -0.009)]:
        check(f"d {cat} {comp}", d, split[cat][comp]["cohens_d"], 3, "outrage_split.json")
    check("p outrage naa_signed", 0.832, split["high_outrage"]["naa_signed"]["p"], 3, "outrage_split.json")

    base = {(r["model"], r["split"]): r for r in load("baselines.json")["results"]}
    check("AUC TF-IDF", 0.9758, base[("TF-IDF + logistic", "stratified")]["auc"], 4, "baselines.json")
    check("AUC VADER", 0.5392, base[("VADER compound", "none")]["auc"], 4, "baselines.json")
    check("AUC TF-IDF ISOT only", 0.9724, base[("TF-IDF + logistic", "ISOT only, stratified")]["auc"], 4, "baselines.json")
    check("AUC index ISOT only", 0.7290, base[("NAA signed index", "ISOT only")]["auc"], 4, "baselines.json")
    check("source probe accuracy", 0.6625, load("baselines.json")["source_identity_probe"]["accuracy"], 4, "baselines.json")

    rt = load("test_retest.json")
    check("ICC(2,1) signed", 0.8725, rt["agreement"]["naa_signed"]["icc_2_1"], 4, "test_retest.json")
    check("eta^2 session B", 0.0888, rt["separation_run_b_shared_items"]["eta_squared"], 4, "test_retest.json")
    check("F session B", 12.861, rt["separation_run_b_shared_items"]["f_statistic"], 3, "test_retest.json")
    check("p session B (x1e-8)", 4.918, rt["separation_run_b_shared_items"]["p_value"] * 1e8, 3, "test_retest.json")
    check("sign reversals", 51, rt["direction_flips"], 0, "test_retest.json")

    rev = load("reversal_diagnosis.json")
    check("expected reversals", 55.3, rev["expected_reversals"], 1, "reversal_diagnosis.json")
    check("sigma per session", 0.00728, rev["sigma_per_session"], 5, "reversal_diagnosis.json")

    calibration = load("calibration.json")
    check("held-out R^2 of calibration", -0.031, calibration["r2_holdout"], 3, "calibration.json")
    check("calibration fit rows", 320, calibration["n_train"], 0, "calibration.json")
    check("calibration held-out rows", 80, calibration["n_holdout"], 0, "calibration.json")

    bound = load("field_bound.json")
    check("min X", -0.0698, bound["observable"]["min"], 4, "field_bound.json")
    check("max X", 0.0543, bound["observable"]["max"], 4, "field_bound.json")
    check("Delta X session A", 0.1241, bound["observable"]["spread"], 4, "field_bound.json")
    check("alpha required, beta J = 2", 4.2938, bound["bound"][2]["alpha_required"], 4, "field_bound.json")
    for row in bound["bound"]:
        check(f"h_c closed form, beta J={row['beta_j_used']:.3f}", round(row["critical_field"], 5),
              spinodal_field(row["beta_j_used"]), 5, "closed form vs field_bound.json")

    run_a = pd.read_csv(FINAL / "corpus_naa.csv")
    run_b = pd.read_csv(FINAL / "corpus_naa_run_b.csv")
    check("ratio undefined (of 400)", 69, int(run_a["naa"].isna().sum()), 0, "corpus_naa.csv")
    for cat, mean in [("fear_activating", 167.4), ("high_outrage", 163.5),
                      ("neutral_informational", 163.7), ("reward_hook", 162.2)]:
        check(f"mean words {cat}", mean, run_a.loc[run_a.category == cat, "word_count"].mean(), 1, "corpus_naa.csv")

    # Scan order. Rows are appended in scan order by batch_naa.py; thirds by np.array_split.
    values = run_a["naa_signed"].to_numpy()
    categories = run_a["category"].to_numpy()
    thirds = np.concatenate([np.full(len(c), i) for i, c in enumerate(np.array_split(np.arange(len(run_a)), 3))])
    chi2, p_chi, _, _ = stats.chi2_contingency(pd.crosstab(thirds, categories))
    check("scan-third balance chi^2", 2.773, chi2, 3, "computed here")
    check("scan-third balance p", 0.8368, p_chi, 4, "computed here")
    _, p_drift = stats.f_oneway(*[values[thirds == t] for t in range(3)])
    check("drift eta^2", 0.0167, eta_squared(values, thirds), 4, "computed here")
    check("drift p", 0.0353, p_drift, 4, "computed here")
    residual = values - pd.Series(values).groupby(thirds).transform("mean").to_numpy() + values.mean()
    _, p_res = stats.f_oneway(*[residual[categories == c] for c in np.unique(categories)])
    check("eta^2 after removing scan-third means", 0.1048, eta_squared(residual, categories), 4, "computed here")
    check("p after removing scan-third means (x1e-9)", 1.588, p_res * 1e9, 3, "computed here")

    # Session B spread and the paired bootstrap of eta^2(A) - eta^2(B), resampling items within category.
    paired = run_a[["id", "category", "naa_signed"]].merge(run_b[["id", "naa_signed"]], on="id", suffixes=("_a", "_b"))
    a, b, c = paired["naa_signed_a"].to_numpy(), paired["naa_signed_b"].to_numpy(), paired["category"].to_numpy()
    check("Delta X session B", 0.1176, b.max() - b.min(), 4, "computed here")
    check("alpha required at beta J = 2, session B spread", 4.530, spinodal_field(2.0) / (b.max() - b.min()), 3, "computed here")
    rng = np.random.default_rng(SEED)
    index_by_cat = [np.where(c == k)[0] for k in np.unique(c)]
    diffs = []
    for _ in range(DRAWS):
        idx = np.concatenate([rng.choice(ix, ix.size) for ix in index_by_cat])
        diffs.append(eta_squared(a[idx], c[idx]) - eta_squared(b[idx], c[idx]))
    low, high = np.percentile(diffs, [2.5, 97.5])
    check("eta^2 difference A - B", 0.018, eta_squared(a, c) - eta_squared(b, c), 3, "computed here")
    check("eta^2 difference 95% CI low", -0.014, low, 3, "computed here, seed 42")
    check("eta^2 difference 95% CI high", 0.052, high, 3, "computed here, seed 42")

    print(f"\n{len(failures)} mismatches" + (f": {failures}" if failures else ""))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
