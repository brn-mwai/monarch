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
        ``naa``: the NAA index value
        ``a_aff``: mean affective-salience activation
        ``a_del``: mean deliberative-control activation
        ``classification``: ``"LOW"`` (< 1.0), ``"MOD"`` ([1.0, 2.0]),
            or ``"HIGH"`` (> 2.0)
    """
    if item_vector.shape != (VERTICES,):
        raise ValueError(f"Expected ({VERTICES},) vector, got {item_vector.shape}")

    aff_indices = get_affective_indices()
    del_indices = get_deliberative_indices()

    a_aff = float(item_vector[aff_indices].mean())
    a_del = float(item_vector[del_indices].mean())

    d = settings.naa_delta if delta is None else delta
    naa = a_aff / (a_del + d)

    if naa < 1.0:
        classification = "LOW"
    elif naa <= 2.0:
        classification = "MOD"
    else:
        classification = "HIGH"

    return {
        "naa": float(naa),
        "a_aff": a_aff,
        "a_del": a_del,
        "classification": classification,
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
