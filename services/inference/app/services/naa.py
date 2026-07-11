"""Neural Arousal Asymmetry (NAA) index.

Eq. (4) from the research proposal::

    NAA = A_aff / (A_del + delta)

where ``A_aff`` is the mean predicted activation across affective-
salience ROIs, ``A_del`` is the mean across deliberative-control ROIs,
and ``delta = 1e-3`` prevents division by zero when the deliberative
system has near-zero predicted activation.

NAA is a CONTENT-LEVEL neural bias observable. It is NOT a direct
individual neural measurement -- it characterises the predicted cortical
processing balance for a given media item at the level of TRIBE v2's
population-averaged predictions. The Monarch product copy must reflect
this distinction (see the audit notes on framing risk).
"""

from typing import Optional

import numpy as np

from ..config import settings
from ..models.enums import NAAClassification
from .roi import (
    AFFECTIVE_SALIENCE_ROIS,
    DELIBERATIVE_CONTROL_ROIS,
    HAS_TRIBEV2,
    get_affective_indices,
    get_deliberative_indices,
    get_per_roi_indices,
)

VERTICES = 20484


def compute_naa(
    item_vector: np.ndarray,
    delta: Optional[float] = None,
) -> dict:
    """Compute the NAA index from a (20484,) item-level activation vector.

    Returns
    -------
    dict
        ``naa``: the NAA index value, or ``None`` when undefined
        ``a_aff``: mean affective-salience activation
        ``a_del``: mean deliberative-control activation
        ``classification``: ``"LOW"`` (< 1.0), ``"MOD"`` ([1.0, 2.0]),
            ``"HIGH"`` (> 2.0), or ``"UNDEFINED"``
        ``valid``: ``True`` when the ratio is a meaningful index

    The ratio is a meaningful magnitude-asymmetry only when both network
    means sit at or above baseline. TRIBE outputs are unconstrained, so a
    negative mean would make ``a_aff / (a_del + delta)`` sign-flip or
    explode; in that regime the function returns ``UNDEFINED`` rather than
    a misleading verdict.
    """
    if item_vector.shape != (VERTICES,):
        raise ValueError(f"Expected ({VERTICES},) vector, got {item_vector.shape}")

    aff_indices = get_affective_indices()
    del_indices = get_deliberative_indices()

    a_aff = float(item_vector[aff_indices].mean())
    a_del = float(item_vector[del_indices].mean())

    if not (np.isfinite(a_aff) and np.isfinite(a_del)):
        raise ValueError("ROI mean activation is non-finite (NaN/inf in input)")

    if a_aff < 0.0 or a_del < 0.0:
        return {
            "naa": None,
            "a_aff": a_aff,
            "a_del": a_del,
            "classification": NAAClassification.UNDEFINED.value,
            "valid": False,
        }

    d = settings.naa_delta if delta is None else delta
    naa = a_aff / (a_del + d)

    if naa < 1.0:
        classification = NAAClassification.LOW
    elif naa <= 2.0:
        classification = NAAClassification.MOD
    else:
        classification = NAAClassification.HIGH

    return {
        "naa": float(naa),
        "a_aff": a_aff,
        "a_del": a_del,
        "classification": classification.value,
        "valid": True,
    }


def compute_signed_naa(item_vector: np.ndarray) -> dict:
    """Signed affective-minus-deliberative asymmetry.

    TRIBE predicts standardized activation, so an ROI mean is centered near
    zero and is negative about as often as positive. The ratio form of NAA is
    therefore undefined for most real content (see ``compute_naa``): on a
    40-item EmoBank scan the ratio was undefined for every item. The Landau /
    Ising field ``H = alpha_hat * NAA`` only needs a signed scalar, not a
    dimensionless ratio, so the asymmetry is taken as a difference::

        NAA_signed = A_aff - A_del

    Positive means the affective-salience system is predicted to dominate,
    negative means deliberative control dominates. Units are those of the
    standardized TRIBE output, which is what ``alpha_hat`` is then fitted in.

    The classification is banded on SIGN only -- ``HIGH`` when the affective
    system leads, ``LOW`` when the deliberative system leads. That is the one
    split the metric supports; a MOD band would need a magnitude cut-off, and
    no such threshold has been established from a corpus yet.
    """
    if item_vector.shape != (VERTICES,):
        raise ValueError(f"Expected ({VERTICES},) vector, got {item_vector.shape}")

    a_aff = float(item_vector[get_affective_indices()].mean())
    a_del = float(item_vector[get_deliberative_indices()].mean())

    if not (np.isfinite(a_aff) and np.isfinite(a_del)):
        raise ValueError("ROI mean activation is non-finite (NaN/inf in input)")

    naa = a_aff - a_del
    classification = NAAClassification.HIGH if naa > 0 else NAAClassification.LOW

    return {
        "naa": naa,
        "a_aff": a_aff,
        "a_del": a_del,
        "classification": classification.value,
        "valid": True,
    }


def compute_roi_breakdown(item_vector: np.ndarray) -> dict:
    """Per-ROI mean activation for the report page breakdown chart.

    Walks every ROI in both groups, looks up its bilateral fsaverage5
    indices via tribev2, and averages the activation. Output keys are
    the ROI names; values are dicts with ``activation``, ``system``,
    and ``vertex_count``.
    """
    if not HAS_TRIBEV2:
        raise RuntimeError(
            "tribev2 required for per-ROI breakdown -- the cache only "
            "stores group unions, not per-ROI vertex sets."
        )

    if item_vector.shape != (VERTICES,):
        raise ValueError(f"Expected ({VERTICES},) vector, got {item_vector.shape}")

    breakdown: dict[str, dict] = {}
    for roi_name in AFFECTIVE_SALIENCE_ROIS + DELIBERATIVE_CONTROL_ROIS:
        indices = get_per_roi_indices(roi_name)
        activation = float(item_vector[indices].mean())
        system = (
            "affective"
            if roi_name in AFFECTIVE_SALIENCE_ROIS
            else "deliberative"
        )
        breakdown[roi_name] = {
            "activation": activation,
            "system": system,
            "vertex_count": int(len(indices)),
        }

    return breakdown
