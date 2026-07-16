"""NAA as a binary manipulation classifier (proposal objective (vi), RQ I).

Answers RQ I: can predicted activation serve as a quantitative signature of
emotionally manipulative media content? Operationally, does the NAA index
separate labelled manipulative content from labelled neutral content?

The scores are NAA values and the labels are ground truth (1 manipulative,
0 neutral). Like ``distribution``, this is agnostic to how NAA was defined, so
it holds under any outcome of the observable amendment.

Two properties this module refuses to paper over
------------------------------------------------
**Direction is not assumed.** The proposal predicts NAA >> 1 for manipulative
content, so higher should mean more manipulative. Both existing runs found the
signed NAA negative for every item, so the sign of any real relationship is an
open question. ``evaluate`` reports the AUC as measured and flags AUC < 0.5,
which means the index runs OPPOSITE to the proposal's hypothesis. Silently
flipping the scores to force AUC > 0.5 would convert a refutation into a
result; ``auc_flipped`` reports what a direction-agnostic reading would give,
separately and labelled.

**A suspiciously good result is a leak, not a triumph.** ``evaluate`` flags
AUC >= LEAK_SUSPICION. The ISOT True/Fake split leaks through the Reuters wire
dateline, and near-perfect separation on a construct that produced a null
calibration is far more likely to be an artifact than a discovery. The corpus
builder strips the dateline and verifies it, but the check belongs on both ends.
"""

from __future__ import annotations

import numpy as np
from sklearn import metrics

MIN_PER_CLASS = 2
LEAK_SUSPICION = 0.95


def _validate(scores: np.ndarray, labels: np.ndarray) -> tuple:
    x = np.asarray(scores, dtype=np.float64)
    y = np.asarray(labels).astype(int)

    if x.shape != y.shape:
        raise ValueError(f"scores {x.shape} and labels {y.shape} differ in length")
    if not np.all(np.isin(y, (0, 1))):
        raise ValueError("labels must be binary 0/1")
    if not np.all(np.isfinite(x)):
        raise ValueError("scores contain NaN or inf")
    for value in (0, 1):
        if int(np.sum(y == value)) < MIN_PER_CLASS:
            raise ValueError(f"need >= {MIN_PER_CLASS} items of class {value}")
    return x, y


def optimal_threshold(scores: np.ndarray, labels: np.ndarray) -> dict:
    """Youden-J optimal operating point on the ROC curve.

    J = sensitivity + specificity - 1, maximised over thresholds. Used because
    §5.8 flags per-item content against a single decision threshold and the
    corpus is balanced by construction, so there is no cost asymmetry to justify
    anything more elaborate.

    The threshold is fitted on the SAME data it is evaluated on, which is
    optimistic. §5.7 does not ask for a split, but the paper must say so: the
    reported F1 is an upper bound, not a held-out estimate.
    """
    x, y = _validate(scores, labels)
    fpr, tpr, thresholds = metrics.roc_curve(y, x)
    youden = tpr - fpr
    best = int(np.argmax(youden))
    return {
        "threshold": float(thresholds[best]),
        "sensitivity": float(tpr[best]),
        "specificity": float(1.0 - fpr[best]),
        "youden_j": float(youden[best]),
    }


def evaluate(scores: np.ndarray, labels: np.ndarray) -> dict:
    """ROC/AUC/F1/precision/recall at the Youden-optimal threshold (§5.7)."""
    x, y = _validate(scores, labels)

    auc = float(metrics.roc_auc_score(y, x))
    point = optimal_threshold(x, y)
    predicted = (x >= point["threshold"]).astype(int)

    result = {
        "n": int(x.size),
        "n_manipulative": int(np.sum(y == 1)),
        "n_neutral": int(np.sum(y == 0)),
        "auc": auc,
        "auc_flipped": float(1.0 - auc),
        "threshold": point["threshold"],
        "precision": float(metrics.precision_score(y, predicted, zero_division=0)),
        "recall": float(metrics.recall_score(y, predicted, zero_division=0)),
        "f1": float(metrics.f1_score(y, predicted, zero_division=0)),
        "sensitivity": point["sensitivity"],
        "specificity": point["specificity"],
        "confusion_matrix": metrics.confusion_matrix(y, predicted).tolist(),
        "threshold_fitted_in_sample": True,
    }

    result["direction_matches_hypothesis"] = bool(auc >= 0.5)
    result["discriminates"] = bool(auc >= 0.6 or auc <= 0.4)
    result["leak_suspected"] = bool(max(auc, 1.0 - auc) >= LEAK_SUSPICION)
    result["interpretation"] = _interpret(result)
    return result


def _interpret(result: dict) -> str:
    """One sentence the paper can quote, chosen by the numbers not by hope."""
    auc = result["auc"]

    if result["leak_suspected"]:
        inverted = "" if auc >= 0.5 else ", and inverted relative to the hypothesis"
        return (
            f"AUC {auc:.3f} is near-perfect{inverted}. Suspect label leakage "
            f"(e.g. the ISOT Reuters dateline) before reporting this as "
            f"discrimination."
        )
    if not result["discriminates"]:
        return (
            f"AUC {auc:.3f} is close to chance. The NAA index does not separate "
            f"manipulative from neutral content in this corpus."
        )
    if auc < 0.5:
        return (
            f"AUC {auc:.3f} is below chance: the index runs OPPOSITE to the "
            f"proposal's hypothesis, with neutral content scoring higher than "
            f"manipulative content. Report the direction; do not flip the sign."
        )
    return (
        f"AUC {auc:.3f} separates manipulative from neutral content in the "
        f"direction the proposal predicts."
    )


def roc_curve_points(scores: np.ndarray, labels: np.ndarray) -> dict:
    """FPR/TPR series for the report's ROC figure."""
    x, y = _validate(scores, labels)
    fpr, tpr, thresholds = metrics.roc_curve(y, x)
    return {
        "fpr": fpr.tolist(),
        "tpr": tpr.tolist(),
        "thresholds": [float(t) for t in thresholds],
        "auc": float(metrics.roc_auc_score(y, x)),
    }
