"""Temporal pooling: collapse (T, 20484) TRIBE v2 predictions to a single
(20484,) item-level activation vector.

Eq. (1) from the Monarch paper:

    v = (1 / T) * sum_{t=1}^{T} P_{t, :}

Mean-pooling is the primary statistic. The trimmed mean and peak helpers
are kept for secondary robustness checks (and for the calibration
notebook).
"""

import numpy as np


def mean_pool(preds: np.ndarray) -> np.ndarray:
    """Reduce (T, V) to (V,) by averaging over the time axis."""
    if preds.ndim != 2:
        raise ValueError(f"Expected (T, V) array, got shape {preds.shape}")
    return preds.mean(axis=0)


def trimmed_mean_pool(preds: np.ndarray, trim: float = 0.1) -> np.ndarray:
    """Symmetric trimmed mean across TRs.

    Drops the extreme `trim` fraction at each tail per vertex before
    averaging. trim=0 reduces to mean_pool.
    """
    if not 0 <= trim < 0.5:
        raise ValueError("trim must be in [0, 0.5)")
    if preds.ndim != 2:
        raise ValueError(f"Expected (T, V) array, got shape {preds.shape}")
    sorted_preds = np.sort(preds, axis=0)
    n = sorted_preds.shape[0]
    k = int(n * trim)
    if k == 0:
        return sorted_preds.mean(axis=0)
    return sorted_preds[k : n - k].mean(axis=0)


def peak_pool(preds: np.ndarray) -> np.ndarray:
    """Max across TRs per vertex (secondary statistic)."""
    if preds.ndim != 2:
        raise ValueError(f"Expected (T, V) array, got shape {preds.shape}")
    return preds.max(axis=0)
