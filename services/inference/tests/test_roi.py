"""Unit tests for app.services.roi.

Tests the disk-cache fallback path. The live tribev2 lookup path is
covered by an integration test that runs only on machines with tribev2
installed (skipped here).
"""

import pytest

from app.services import roi


def test_roi_loads_from_cache(stub_roi_cache):
    aff = roi.get_affective_indices()
    delib = roi.get_deliberative_indices()
    assert len(aff) == 200
    assert len(delib) == 200
    assert set(aff).isdisjoint(set(delib))


def test_roi_indices_are_int(stub_roi_cache):
    aff = roi.get_affective_indices()
    assert aff.dtype.kind == "i"


def test_per_roi_requires_tribev2():
    if roi.HAS_TRIBEV2:
        pytest.skip("tribev2 is installed; live path covered separately")
    with pytest.raises(RuntimeError):
        roi.get_per_roi_indices("OFC")
