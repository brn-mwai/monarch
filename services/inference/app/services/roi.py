"""HCP MMP1.0 ROI definitions for the Monarch NAA computation.

ROI names are from the Glasser et al. (2016) parcellation, accessed via
``tribev2.utils.get_hcp_roi_indices``. The audit confirmed every parcel
listed below exists in the HCP MMP1.0 atlas.

IMPORTANT CORRECTIONS from the audit (see monarch-audit/AUDIT_REPORT.md):

  - "IFS" in the original spec -> use "IFSa" and "IFSp" (anterior /
    posterior inferior frontal sulcus).
  - "MI" (mid-insula) -> use "AAIC" (agranular insular complex). Mid-
    insula is a subdivision of insular cortex; AAIC is the closest
    cortical proxy in HCP MMP1.0.
  - "Fp1" / "Fp2" are EEG labels -> use "10p" and "10pp" (frontopolar
    cortex). EEG electrode names do not exist as parcels.
  - Nucleus accumbens / ventral striatum are SUBCORTICAL -- not
    available in the released cortical-only TRIBE v2 checkpoint. The
    audit notes this. They are intentionally omitted from NAA.

The lookup is cached on disk in ``data/roi_definitions.json`` so the
server can boot without paying the cost of importing tribev2 just to
resolve indices.
"""

import json
from functools import lru_cache
from pathlib import Path
from typing import Optional

import numpy as np

# Try TRIBE v2 utils first; fall back to the cached JSON file.
try:
    from tribev2.utils import get_hcp_roi_indices  # type: ignore
    HAS_TRIBEV2 = True
except ImportError:
    HAS_TRIBEV2 = False

    def get_hcp_roi_indices(*args, **kwargs):  # type: ignore
        raise RuntimeError(
            "tribev2 is not installed. Either install it (pip install -e "
            "/path/to/tribev2) or pre-generate data/roi_definitions.json "
            "via app.services.roi.cache_roi_indices."
        )


# === ROI group definitions ===

AFFECTIVE_SALIENCE_ROIS: list[str] = [
    "OFC",    # orbitofrontal cortex
    "pOFC",   # posterior OFC
    "p24",    # posterior area 24 (anterior cingulate)
    "a24",    # anterior area 24 (anterior cingulate)
    "TGd",    # temporal pole, dorsal
    "TE1a",   # anterior temporal area 1
    "TE1p",   # posterior temporal area 1
    "IFSa",   # anterior inferior frontal sulcus
    "IFSp",   # posterior inferior frontal sulcus
    "AAIC",   # agranular insular complex (cortical insula proxy)
]

DELIBERATIVE_CONTROL_ROIS: list[str] = [
    "46",     # mid-DLPFC
    "9-46v",  # ventral area 9-46
    "11l",    # lateral area 11
    "13l",    # lateral area 13
    "d32",    # dorsal area 32
    "p32",    # pregenual area 32
    "10p",    # frontopolar area 10p
    "10pp",   # frontopolar area 10pp
]


# Module-level path so tests can monkeypatch it without touching settings.
DEFAULT_CACHE_PATH = Path("./data/roi_definitions.json")


@lru_cache(maxsize=1)
def get_affective_indices(cache_path: Optional[Path] = None) -> np.ndarray:
    """Return fsaverage5 vertex indices for affective-salience ROIs (bilateral)."""
    return _get_indices("affective", AFFECTIVE_SALIENCE_ROIS, cache_path)


@lru_cache(maxsize=1)
def get_deliberative_indices(cache_path: Optional[Path] = None) -> np.ndarray:
    """Return fsaverage5 vertex indices for deliberative-control ROIs (bilateral)."""
    return _get_indices("deliberative", DELIBERATIVE_CONTROL_ROIS, cache_path)


def _get_indices(
    group: str,
    roi_names: list[str],
    cache_path: Optional[Path],
) -> np.ndarray:
    """Resolve ROI indices: prefer the on-disk cache, fall back to live
    tribev2 lookup. Either path returns a 1-D int64 numpy array."""
    path = cache_path or DEFAULT_CACHE_PATH
    if path.exists():
        with open(path) as f:
            data = json.load(f)
        if group in data:
            return np.array(data[group], dtype=np.int64)

    if not HAS_TRIBEV2:
        raise FileNotFoundError(
            f"ROI cache not found at {path} and tribev2 is not installed. "
            "Run scripts/cache_roi.py on a machine that has tribev2."
        )

    return get_hcp_roi_indices(roi_names, hemi="both", mesh="fsaverage5")


def get_per_roi_indices(roi_name: str) -> np.ndarray:
    """Indices for a single ROI (bilateral). Used by the per-ROI breakdown.

    Always goes through tribev2 -- the cache only stores the union of
    each group, not per-ROI vertex sets.
    """
    if not HAS_TRIBEV2:
        raise RuntimeError("tribev2 required for per-ROI breakdown")
    return get_hcp_roi_indices([roi_name], hemi="both", mesh="fsaverage5")


def cache_roi_indices(output_path: Path) -> dict:
    """Pre-compute and save ROI indices to JSON.

    Run this once on a machine with tribev2 installed to bootstrap the
    cache file. The server can then start without tribev2 in its import
    path (which is useful for the unit test process).
    """
    if not HAS_TRIBEV2:
        raise RuntimeError("tribev2 must be installed to cache ROI indices")

    affective = get_hcp_roi_indices(AFFECTIVE_SALIENCE_ROIS, hemi="both", mesh="fsaverage5")
    deliberative = get_hcp_roi_indices(DELIBERATIVE_CONTROL_ROIS, hemi="both", mesh="fsaverage5")

    data = {
        "affective": np.asarray(affective).tolist(),
        "deliberative": np.asarray(deliberative).tolist(),
        "affective_rois": AFFECTIVE_SALIENCE_ROIS,
        "deliberative_rois": DELIBERATIVE_CONTROL_ROIS,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(data, f)

    print(f"Cached ROI indices to {output_path}")
    print(f"  Affective:    {len(data['affective'])} vertices")
    print(f"  Deliberative: {len(data['deliberative'])} vertices")
    return data
