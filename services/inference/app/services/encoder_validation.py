"""Vertex-level validation of a predicted-fMRI encoder against held-out subjects.

Paper 3 asks whether the released average-subject checkpoint predicts any real cortex. The
claim under test is a published audit reporting vertex ``r = -0.0145`` against a measured
inter-subject ceiling of ``+0.0508``. Magnitudes that small make the reporting conventions
decisive: whether undefined vertices are dropped or silently zeroed changes the third
decimal place, and the third decimal place is the entire claim.

Three rules this module keeps
-----------------------------
**An undefined correlation stays undefined.** A vertex with no variance over time, which is
what the medial wall looks like after masking, has no Pearson correlation. Returning 0.0
there would pull a mean toward zero with fabricated values, so those vertices are NaN and
counted, and the count travels with the result.

**The ceiling is measured, not assumed.** The comparison is meaningless without knowing how
much signal is there to predict. The leave-one-subject-out ceiling correlates each subject
against the mean of the others, which is a lower bound on what any encoder could achieve.

**Sign is preserved.** Anti-correlation is the finding under test, so nothing here takes an
absolute value or flips a sign to make a number look better.
"""

from __future__ import annotations

import numpy as np

MIN_TIMEPOINTS = 3
MIN_SUBJECTS_FOR_CEILING = 2


def _pearson_rows(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Pearson r between matching rows of two (vertices, timepoints) arrays.

    Rows with zero variance yield NaN rather than a number, because the correlation is not
    defined there and any substitute value is invented.
    """
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if a.shape != b.shape:
        raise ValueError(f"shape mismatch: {a.shape} vs {b.shape}")
    if a.ndim != 2:
        raise ValueError(f"expected (vertices, timepoints), got {a.ndim}d")
    if a.shape[1] < MIN_TIMEPOINTS:
        raise ValueError(f"need at least {MIN_TIMEPOINTS} timepoints, got {a.shape[1]}")

    a_centred = a - a.mean(axis=1, keepdims=True)
    b_centred = b - b.mean(axis=1, keepdims=True)
    numerator = (a_centred * b_centred).sum(axis=1)

    live = _has_variance(a, a_centred) & _has_variance(b, b_centred)
    denominator = np.sqrt((a_centred ** 2).sum(axis=1) * (b_centred ** 2).sum(axis=1))

    with np.errstate(invalid="ignore", divide="ignore"):
        r = np.where(live, numerator / denominator, np.nan)
    return r


def _has_variance(raw: np.ndarray, centred: np.ndarray) -> np.ndarray:
    """Whether each row varies, judged against its own scale rather than against zero.

    Centring a constant row leaves rounding residue near 1e-17 instead of exact zero, so a
    ``> 0`` test admits it and returns a correlation of order 1e-17. That is not a small
    effect, it is noise wearing the costume of one, and at the magnitudes this module exists
    to adjudicate it is indistinguishable from the claim under test.
    """
    residual = (centred ** 2).sum(axis=1)
    scale = (raw ** 2).sum(axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        relative = np.where(scale > 0, residual / scale, 0.0)
    return relative > 1e-12


def vertex_correlation(predicted: np.ndarray, observed: np.ndarray) -> dict:
    """Per-vertex Pearson r between predicted and observed responses.

    Both arrays are (vertices, timepoints) on the same surface and the same time base.
    """
    r = _pearson_rows(predicted, observed)
    defined = ~np.isnan(r)
    return {
        "r_per_vertex": r,
        "n_vertices": int(r.size),
        "n_defined": int(defined.sum()),
        "n_undefined": int((~defined).sum()),
        "mean_r": float(np.nanmean(r)) if defined.any() else float("nan"),
        "median_r": float(np.nanmedian(r)) if defined.any() else float("nan"),
    }


def noise_ceiling(subject_responses: list[np.ndarray]) -> dict:
    """Leave-one-subject-out inter-subject correlation, per vertex.

    Each subject is correlated against the mean of the remaining subjects, and the per-vertex
    ceiling is the average of those correlations. This is a lower bound on achievable
    performance: an encoder cannot be expected to beat the agreement between real brains.
    """
    if len(subject_responses) < MIN_SUBJECTS_FOR_CEILING:
        raise ValueError(
            f"need at least {MIN_SUBJECTS_FOR_CEILING} subjects, got {len(subject_responses)}"
        )
    stacked = np.stack([np.asarray(s, dtype=float) for s in subject_responses])

    per_subject = []
    for index in range(stacked.shape[0]):
        held_out = stacked[index]
        others = np.delete(stacked, index, axis=0).mean(axis=0)
        per_subject.append(_pearson_rows(held_out, others))

    per_subject_array = np.stack(per_subject)
    with np.errstate(invalid="ignore"):
        ceiling = np.nanmean(per_subject_array, axis=0)
    all_nan = np.isnan(per_subject_array).all(axis=0)
    ceiling = np.where(all_nan, np.nan, ceiling)

    defined = ~np.isnan(ceiling)
    return {
        "ceiling_per_vertex": ceiling,
        "per_subject_r": per_subject_array,
        "n_subjects": int(stacked.shape[0]),
        "n_defined": int(defined.sum()),
        "mean_ceiling": float(np.nanmean(ceiling)) if defined.any() else float("nan"),
    }


def bootstrap_ci(
    values: np.ndarray,
    n_resamples: int = 10000,
    confidence: float = 0.95,
    seed: int = 0,
) -> dict:
    """Percentile bootstrap interval for the mean, over the sampling unit given.

    Resample subjects when the question is whether the result generalises to new people, and
    vertices when it is whether it generalises across cortex. The caller decides which by
    what it passes; the seed is explicit so a reported interval can be reproduced exactly.
    """
    finite = np.asarray(values, dtype=float)
    finite = finite[np.isfinite(finite)]
    if finite.size == 0:
        return {"point": float("nan"), "low": float("nan"), "high": float("nan"), "n": 0}

    rng = np.random.default_rng(seed)
    draws = rng.integers(0, finite.size, size=(n_resamples, finite.size))
    means = finite[draws].mean(axis=1)
    tail = (1.0 - confidence) / 2.0

    return {
        "point": float(finite.mean()),
        "low": float(np.quantile(means, tail)),
        "high": float(np.quantile(means, 1.0 - tail)),
        "n": int(finite.size),
        "n_resamples": int(n_resamples),
        "confidence": confidence,
        "seed": seed,
    }


def evaluate(
    predicted: np.ndarray,
    subject_responses: list[np.ndarray],
    seed: int = 0,
) -> dict:
    """Encoder performance against held-out subjects, with its ceiling and intervals.

    ``predicted`` is one set of predictions evaluated against every subject in turn, which is
    what an average-subject checkpoint licenses: it emits no per-subject output, so the same
    prediction is scored against each brain.
    """
    per_subject = [vertex_correlation(predicted, observed) for observed in subject_responses]
    subject_means = np.array([result["mean_r"] for result in per_subject])
    ceiling = noise_ceiling(subject_responses)

    encoder_ci = bootstrap_ci(subject_means, seed=seed)
    ceiling_means = np.nanmean(ceiling["per_subject_r"], axis=1)
    ceiling_ci = bootstrap_ci(ceiling_means, seed=seed)

    return {
        "per_subject": per_subject,
        "encoder_mean_r": encoder_ci,
        "noise_ceiling": ceiling_ci,
        "n_subjects": len(subject_responses),
        "beats_zero": bool(encoder_ci["low"] > 0.0),
        "reaches_ceiling": bool(encoder_ci["low"] >= ceiling_ci["point"]),
    }
