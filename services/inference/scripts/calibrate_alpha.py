"""Calibrate the Ising coupling ``alpha_hat`` from a labeled CSV.

``alpha_hat`` scales the neural-arousal asymmetry (NAA) into the external
field of the opinion-dynamics model: ``H = alpha_hat * NAA``. It is estimated
empirically by regressing a real-world outcome (the field proxy) on NAA.

Model note (why this is not a plain OLS slope). The equilibrium is
``m = tanh(beta_j * m + alpha_hat * NAA)``. In the low-field regime
``tanh(x) ~= x``, so ``m ~= [alpha_hat / (1 - beta_j)] * NAA``. Therefore the
fitted regression slope ``s`` estimates ``alpha_hat / (1 - beta_j)``, and

    alpha_hat = s * (1 - beta_j)

The slope's 95% CI is propagated through the same factor.

Honesty: ``alpha_hat`` inherits the meaning of the outcome column you choose
(engagement, human arousal rating, ...). The output JSON records that column
name so the paper can state exactly what was calibrated against.

Usage
-----
Regress against a precomputed NAA column (no GPU needed):
    python scripts/calibrate_alpha.py --csv data/corpus.csv \
        --naa-col naa --outcome-col engagement

Compute NAA from text via TRIBE first (needs the model / GPU):
    python scripts/calibrate_alpha.py --csv data/corpus.csv \
        --text-col text --outcome-col arousal_rating

Verify the estimator with no data or model:
    python scripts/calibrate_alpha.py --self-test
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Optional

import numpy as np
from scipy import stats

# Python puts the script's own directory on sys.path, not the working directory, so the
# app package is invisible when this is run as `python scripts/calibrate_alpha.py`.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

DEFAULT_BETA_J = 0.7
DEFAULT_HOLDOUT = 0.2
DEFAULT_SEED = 17
MIN_ROWS = 8
DEFAULT_BOOTSTRAP = 1000
SENSITIVITY_BETA_J = (0.5, 0.6, 0.7, 0.8, 0.9)


def _read_columns(
    csv_path: Path,
    outcome_col: str,
    naa_col: Optional[str],
    text_col: Optional[str],
) -> tuple[list[float], list[Optional[float]], list[Optional[str]]]:
    """Read outcome and either NAA values or text from the CSV."""
    outcomes: list[float] = []
    naa_values: list[Optional[float]] = []
    texts: list[Optional[str]] = []

    with open(csv_path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"{csv_path} has no header row")
        for required in (outcome_col, naa_col, text_col):
            if required and required not in reader.fieldnames:
                raise ValueError(
                    f"column '{required}' not in CSV header {reader.fieldnames}"
                )
        for row in reader:
            outcome_raw = row[outcome_col].strip()
            if outcome_raw == "":
                continue
            outcomes.append(float(outcome_raw))
            naa_values.append(
                float(row[naa_col]) if naa_col and row[naa_col].strip() else None
            )
            texts.append(row[text_col] if text_col else None)

    return outcomes, naa_values, texts


def _naa_from_text(texts: list[Optional[str]]) -> list[float]:
    """Compute NAA per text item via the TRIBE inference service.

    Imported lazily so the regression path (and the self-test) never require
    the model, torch, or a GPU.
    """
    from app.services.inference import TribeInferenceService
    from app.services.naa import compute_naa

    service = TribeInferenceService()
    service.load_model()

    values: list[float] = []
    for text in texts:
        if not text:
            raise ValueError("empty text row; cannot compute NAA")
        result = service.predict_text(text)
        naa = compute_naa(result["item_vector"])
        if not naa["valid"]:
            raise ValueError(f"NAA undefined for text: {text[:60]!r}")
        values.append(float(naa["naa"]))
    return values


def bootstrap_alpha(
    naa: np.ndarray,
    outcome: np.ndarray,
    beta_j: float,
    replicates: int = DEFAULT_BOOTSTRAP,
    seed: int = DEFAULT_SEED,
    normalize_outcome: bool = True,
) -> dict:
    """Percentile bootstrap CI for alpha_hat (proposal §4.4, B = 1,000).

    The analytic t-interval in ``calibrate`` assumes normally distributed
    residuals. At the sample sizes reached so far (n = 10 and n = 40) that
    assumption carries real weight and cannot be checked, which matters
    because the headline result is a NULL: a CI that straddles zero is only
    as credible as the distributional assumption behind it. Resampling
    (NAA, outcome) pairs with replacement makes no normality assumption, so
    a null that survives the bootstrap is the stronger statement.

    Pairs are resampled -- not residuals -- because NAA is observed, not
    fixed by design.

    Returns the percentile CI, the bootstrap median, and ``fraction_negative``:
    the share of replicates placing alpha_hat below zero. At ~0.5 the estimate
    is indistinguishable from noise in sign as well as magnitude.
    """
    if naa.shape != outcome.shape:
        raise ValueError("naa and outcome must have the same length")
    if replicates < 1:
        raise ValueError(f"replicates must be >= 1, got {replicates}")

    x = naa.astype(np.float64)
    y = outcome.astype(np.float64)
    if normalize_outcome:
        span = y.max() - y.min()
        y = (y - y.min()) / span if span > 0 else y - y.min()

    rng = np.random.default_rng(seed)
    factor = 1.0 - beta_j
    estimates: list[float] = []

    for _ in range(replicates):
        idx = rng.integers(0, x.size, size=x.size)
        xs, ys = x[idx], y[idx]
        if np.ptp(xs) == 0.0:
            continue
        slope = float(stats.linregress(xs, ys).slope)
        estimates.append(slope * factor)

    if len(estimates) < 2:
        raise ValueError("bootstrap produced too few usable replicates")

    values = np.array(estimates, dtype=np.float64)
    return {
        "bootstrap_replicates": int(values.size),
        "bootstrap_ci_low": float(np.percentile(values, 2.5)),
        "bootstrap_ci_high": float(np.percentile(values, 97.5)),
        "bootstrap_median": float(np.median(values)),
        "fraction_negative": float(np.mean(values < 0.0)),
    }


def sensitivity_sweep(
    naa: np.ndarray,
    outcome: np.ndarray,
    beta_j_values: tuple[float, ...] = SENSITIVITY_BETA_J,
    normalize_outcome: bool = True,
) -> list[dict]:
    """alpha_hat across the assumed social temperature (proposal §4.4).

    beta_J is an ASSUMPTION -- 0.7, borrowed from Castellano et al. (2009)
    for online political discourse -- not something this data measures. The
    proposal therefore requires the sweep over [0.5, 0.9] to show that no
    downstream conclusion is an artifact of that choice.

    The fitted slope does not depend on beta_J; only the back-out factor
    ``alpha_hat = slope * (1 - beta_j)`` does. So the sweep is an exact
    rescaling rather than a refit, and alpha_hat varies by the full factor
    of 5 spanned by (1 - beta_j) over [0.5, 0.9]. That is worth stating
    plainly in the paper: the magnitude of alpha_hat is driven as much by
    the social-temperature assumption as by the data. Its SIGN and its
    significance are invariant under the sweep, which is why a null is
    robust to beta_J even though a point estimate would not be.
    """
    x = naa.astype(np.float64)
    y = outcome.astype(np.float64)
    if normalize_outcome:
        span = y.max() - y.min()
        y = (y - y.min()) / span if span > 0 else y - y.min()

    fit = stats.linregress(x, y)
    return [
        {
            "beta_j": float(beta_j),
            "alpha_hat": float(fit.slope * (1.0 - beta_j)),
            "p_value": float(fit.pvalue),
        }
        for beta_j in beta_j_values
    ]


def calibrate(
    naa: np.ndarray,
    outcome: np.ndarray,
    beta_j: float,
    holdout: float,
    seed: int,
    normalize_outcome: bool = True,
) -> dict:
    """Fit alpha_hat from (NAA, outcome) pairs.

    NAA is kept in its raw physical units, because ``H = alpha_hat * NAA``
    multiplies the real NAA at inference time; z-scoring it would make
    alpha_hat un-applicable. The outcome is optionally min-max normalized to
    [0, 1] so it reads as a bounded field proxy and alpha_hat lands in a
    sensible range (do NOT z-score it -- that collapses the slope to the
    correlation coefficient and loses the physical scale). alpha_hat is then
    backed out of the fitted slope via the low-field linearization.
    """
    if naa.shape != outcome.shape:
        raise ValueError("naa and outcome must have the same length")
    if naa.size < MIN_ROWS:
        raise ValueError(f"need at least {MIN_ROWS} rows, got {naa.size}")
    if not 0.0 <= holdout < 0.9:
        raise ValueError("holdout must be in [0, 0.9)")

    x = naa.astype(np.float64)
    y = outcome.astype(np.float64)
    if normalize_outcome:
        span = y.max() - y.min()
        y = (y - y.min()) / span if span > 0 else y - y.min()

    rng = np.random.default_rng(seed)
    order = rng.permutation(x.size)
    n_holdout = int(round(x.size * holdout))
    test_idx = order[:n_holdout]
    train_idx = order[n_holdout:]

    fit = stats.linregress(x[train_idx], y[train_idx])
    factor = 1.0 - beta_j

    # 95% CI on the slope, then scaled by (1 - beta_j).
    dof = train_idx.size - 2
    t_crit = float(stats.t.ppf(0.975, dof)) if dof > 0 else float("nan")
    slope_ci = t_crit * fit.stderr
    alpha_hat = fit.slope * factor
    ci_low = (fit.slope - slope_ci) * factor
    ci_high = (fit.slope + slope_ci) * factor
    if factor < 0:
        ci_low, ci_high = ci_high, ci_low

    if test_idx.size >= 2:
        predicted = fit.intercept + fit.slope * x[test_idx]
        ss_res = float(np.sum((y[test_idx] - predicted) ** 2))
        ss_tot = float(np.sum((y[test_idx] - y[test_idx].mean()) ** 2))
        r2_holdout = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    else:
        r2_holdout = None

    return {
        "alpha_hat": float(alpha_hat),
        "ci_low": float(ci_low),
        "ci_high": float(ci_high),
        "slope_standardized": float(fit.slope),
        "beta_j": float(beta_j),
        "n": int(x.size),
        "n_train": int(train_idx.size),
        "n_holdout": int(test_idx.size),
        "r2_train": float(fit.rvalue**2),
        "r2_holdout": r2_holdout,
        "p_value": float(fit.pvalue),
        "outcome_normalized": normalize_outcome,
        "source": "calibrated",
    }


def run_self_test() -> int:
    """Verify the estimator on synthetic data. No CSV, no model.

    Three checks: it recovers a known coupling; the bootstrap CI covers that
    known value; and -- the case that matters for this project -- it reports
    a NULL rather than a spurious estimate when the outcome is independent
    of NAA. A calibrator that cannot detect its own null is not evidence.
    """
    beta_j = 0.7
    true_alpha = 0.6
    slope = true_alpha / (1.0 - beta_j)  # low-field: field ~= slope * naa
    rng = np.random.default_rng(DEFAULT_SEED)
    naa = rng.uniform(0.5, 4.0, size=400)
    field = slope * naa + rng.normal(0, 0.15, size=naa.size)

    # Raw NAA + raw field, no outcome normalization: recovers the true
    # physical coupling exactly.
    result = calibrate(
        naa, field, beta_j, DEFAULT_HOLDOUT, DEFAULT_SEED, normalize_outcome=False
    )
    recovered = result["alpha_hat"]
    recovery_ok = abs(recovered - true_alpha) < 0.05
    print(
        f"[self-test] recovery: true alpha_hat={true_alpha:.3f} "
        f"recovered={recovered:.3f} "
        f"CI=[{result['ci_low']:.3f}, {result['ci_high']:.3f}] "
        f"r2_holdout={result['r2_holdout']:.3f} "
        f"-> {'PASS' if recovery_ok else 'FAIL'}"
    )

    boot = bootstrap_alpha(
        naa, field, beta_j, replicates=200, seed=DEFAULT_SEED, normalize_outcome=False
    )
    covers = boot["bootstrap_ci_low"] <= true_alpha <= boot["bootstrap_ci_high"]
    print(
        f"[self-test] bootstrap: CI=[{boot['bootstrap_ci_low']:.3f}, "
        f"{boot['bootstrap_ci_high']:.3f}] covers {true_alpha:.3f} "
        f"-> {'PASS' if covers else 'FAIL'}"
    )

    sweep = sensitivity_sweep(naa, field, normalize_outcome=False)
    implied_slopes = [row["alpha_hat"] / (1.0 - row["beta_j"]) for row in sweep]
    scaling_ok = max(implied_slopes) - min(implied_slopes) < 1e-9
    spread = max(r["alpha_hat"] for r in sweep) / min(r["alpha_hat"] for r in sweep)
    print(
        f"[self-test] sensitivity: beta_j 0.5->0.9 spans alpha_hat "
        f"{sweep[0]['alpha_hat']:.3f}..{sweep[-1]['alpha_hat']:.3f} "
        f"({spread:.1f}x) -> {'PASS' if scaling_ok else 'FAIL'}"
    )

    null_outcome = rng.normal(0.0, 1.0, size=naa.size)
    null_boot = bootstrap_alpha(
        naa,
        null_outcome,
        beta_j,
        replicates=200,
        seed=DEFAULT_SEED,
        normalize_outcome=False,
    )
    null_ok = null_boot["bootstrap_ci_low"] < 0.0 < null_boot["bootstrap_ci_high"]
    print(
        f"[self-test] null detection: outcome independent of NAA -> "
        f"CI=[{null_boot['bootstrap_ci_low']:.3f}, "
        f"{null_boot['bootstrap_ci_high']:.3f}] straddles zero "
        f"-> {'PASS' if null_ok else 'FAIL'}"
    )

    ok = recovery_ok and covers and scaling_ok and null_ok
    print(f"[self-test] {'ALL PASS' if ok else 'FAILURES PRESENT'}")
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, help="labeled corpus CSV")
    parser.add_argument("--outcome-col", default="outcome", help="field-proxy column")
    parser.add_argument("--naa-col", default=None, help="precomputed NAA column")
    parser.add_argument("--text-col", default=None, help="text column (computes NAA)")
    parser.add_argument("--beta-j", type=float, default=DEFAULT_BETA_J)
    parser.add_argument("--holdout", type=float, default=DEFAULT_HOLDOUT)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument(
        "--bootstrap",
        type=int,
        default=DEFAULT_BOOTSTRAP,
        help="bootstrap replicates for the alpha_hat CI (0 disables)",
    )
    parser.add_argument(
        "--no-normalize-outcome",
        action="store_true",
        help="skip min-max scaling the outcome to [0, 1]",
    )
    parser.add_argument("--out", type=Path, default=Path("./data/alpha_hat.json"))
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return run_self_test()

    if not args.csv:
        parser.error("--csv is required (or use --self-test)")
    if not args.naa_col and not args.text_col:
        parser.error("provide --naa-col (precomputed) or --text-col (computes NAA)")

    outcomes, naa_values, texts = _read_columns(
        args.csv, args.outcome_col, args.naa_col, args.text_col
    )

    if args.naa_col:
        if any(v is None for v in naa_values):
            raise ValueError(f"column '{args.naa_col}' has empty values")
        naa = np.array(naa_values, dtype=np.float64)
    else:
        naa = np.array(_naa_from_text(texts), dtype=np.float64)

    outcome = np.array(outcomes, dtype=np.float64)
    result = calibrate(
        naa,
        outcome,
        args.beta_j,
        args.holdout,
        args.seed,
        normalize_outcome=not args.no_normalize_outcome,
    )
    result["outcome_variable"] = args.outcome_col
    result["csv"] = str(args.csv)

    normalize = not args.no_normalize_outcome
    if args.bootstrap:
        result.update(
            bootstrap_alpha(
                naa, outcome, args.beta_j, args.bootstrap, args.seed, normalize
            )
        )
    result["sensitivity"] = sensitivity_sweep(
        naa, outcome, SENSITIVITY_BETA_J, normalize
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(
        f"alpha_hat = {result['alpha_hat']:.4f} "
        f"(95% CI [{result['ci_low']:.4f}, {result['ci_high']:.4f}], "
        f"n={result['n']}, beta_j={result['beta_j']}, "
        f"outcome='{args.outcome_col}')"
    )
    print(
        f"  train R^2={result['r2_train']:.3f}  "
        f"holdout R^2="
        + (f"{result['r2_holdout']:.3f}" if result["r2_holdout"] is not None else "n/a")
        + f"  p={result['p_value']:.3f}"
    )

    if args.bootstrap:
        print(
            f"  bootstrap ({result['bootstrap_replicates']} reps): "
            f"95% CI [{result['bootstrap_ci_low']:.4f}, "
            f"{result['bootstrap_ci_high']:.4f}]  "
            f"median={result['bootstrap_median']:.4f}  "
            f"frac<0={result['fraction_negative']:.2f}"
        )
        straddles = result["bootstrap_ci_low"] < 0.0 < result["bootstrap_ci_high"]
        if straddles:
            print(
                "  [NULL] bootstrap CI straddles zero: alpha_hat is not "
                "distinguishable from zero. Report the null; do not quote "
                "a point estimate."
            )

    print("  sensitivity over beta_j:")
    for row in result["sensitivity"]:
        print(f"    beta_j={row['beta_j']:.1f} -> alpha_hat={row['alpha_hat']:.4f}")

    print(f"  written to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
