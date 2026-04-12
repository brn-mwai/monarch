"""alpha_hat calibration via OLS on NELA-GT-2021.

The Landau / Ising layer needs a single scalar ``alpha_hat`` that scales
the Neural Arousal Asymmetry index into the external-field term of the
Ising model. ``alpha_hat`` is calibrated ONCE on the NELA-GT-2021 corpus
by regressing observed share-rate proxies against TRIBE v2 NAA values.

This module is a thin loader over the cached calibration result. The
actual fit is done offline in ``scripts/calibrate_alpha.py``; the API
server only needs to read the JSON it produced.

Default fallback: 0.5. The /api/scan endpoint will log a warning when
the calibration file is missing.
"""

import json
from pathlib import Path
from typing import Optional

DEFAULT_ALPHA_HAT = 0.5


def load_alpha_hat(
    path: Path,
    fallback: float = DEFAULT_ALPHA_HAT,
) -> dict:
    """Read the calibrated alpha_hat from disk.

    Returns
    -------
    dict
        ``alpha_hat``: float -- point estimate
        ``ci_low``: optional float -- lower 95% CI
        ``ci_high``: optional float -- upper 95% CI
        ``source``: str -- "calibrated" or "fallback"
    """
    if not path.exists():
        return {
            "alpha_hat": fallback,
            "ci_low": None,
            "ci_high": None,
            "source": "fallback",
        }

    with open(path) as f:
        data = json.load(f)

    return {
        "alpha_hat": float(data.get("alpha_hat", fallback)),
        "ci_low": _maybe_float(data.get("ci_low")),
        "ci_high": _maybe_float(data.get("ci_high")),
        "source": "calibrated",
    }


def _maybe_float(value) -> Optional[float]:
    return float(value) if value is not None else None
