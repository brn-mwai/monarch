"""Pytest fixtures shared across the suite.

The most important fixture is ``stub_roi_cache``, which writes a tiny
JSON ROI cache to a temp dir and monkeypatches the module-level cache
path. This lets ``test_naa.py`` run without tribev2 installed (the
naa module would otherwise fall back to a tribev2 lookup).
"""

import json
from pathlib import Path

import numpy as np
import pytest


@pytest.fixture
def stub_roi_cache(tmp_path: Path, monkeypatch) -> Path:
    """Drop a fake roi_definitions.json with two disjoint index sets and
    point app.services.roi at it for the duration of the test."""
    cache_path = tmp_path / "roi_definitions.json"
    affective = list(range(0, 200))           # 200 vertices in [0, 200)
    deliberative = list(range(200, 400))      # 200 vertices in [200, 400)
    cache_path.write_text(
        json.dumps(
            {
                "affective": affective,
                "deliberative": deliberative,
                "affective_rois": ["TEST_AFF"],
                "deliberative_rois": ["TEST_DEL"],
            }
        )
    )

    from app.services import roi

    # Reset lru_cache so a fresh lookup runs against our stub path.
    roi.get_affective_indices.cache_clear()
    roi.get_deliberative_indices.cache_clear()
    monkeypatch.setattr(roi, "DEFAULT_CACHE_PATH", cache_path)

    yield cache_path

    roi.get_affective_indices.cache_clear()
    roi.get_deliberative_indices.cache_clear()


@pytest.fixture
def synthetic_item_vector() -> np.ndarray:
    """A deterministic (20484,) vector with predictable per-region means.

    - Affective indices [0, 200): all 1.5
    - Deliberative indices [200, 400): all 0.5
    - Everything else: zero
    """
    v = np.zeros(20484, dtype=np.float32)
    v[0:200] = 1.5
    v[200:400] = 0.5
    return v
