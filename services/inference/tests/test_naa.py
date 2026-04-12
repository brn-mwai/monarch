"""Unit tests for app.services.naa.

Uses the ``stub_roi_cache`` fixture so the test runs without tribev2.
"""

import numpy as np
import pytest

from app.services.naa import compute_naa


def test_compute_naa_basic(stub_roi_cache, synthetic_item_vector):
    result = compute_naa(synthetic_item_vector)

    # Affective average is 1.5, deliberative is 0.5, delta = 1e-3.
    # NAA = 1.5 / 0.501 = ~2.994 -> HIGH classification (above the 2.0 threshold).
    expected_naa = 1.5 / (0.5 + 1e-3)
    assert result["a_aff"] == pytest.approx(1.5)
    assert result["a_del"] == pytest.approx(0.5)
    assert result["naa"] == pytest.approx(expected_naa, rel=1e-4)
    assert result["classification"] == "HIGH"


def test_compute_naa_moderate_classification(stub_roi_cache):
    """A_aff just above A_del puts NAA in the (1.0, 2.0] MOD range."""
    v = np.zeros(20484, dtype=np.float32)
    v[0:200] = 0.7      # affective
    v[200:400] = 0.5    # deliberative -> NAA ~1.397

    result = compute_naa(v)
    assert 1.0 < result["naa"] <= 2.0
    assert result["classification"] == "MOD"


def test_compute_naa_low_classification(stub_roi_cache):
    """A_aff < A_del gives NAA < 1 -> LOW classification."""
    v = np.zeros(20484, dtype=np.float32)
    v[0:200] = 0.2          # affective
    v[200:400] = 1.0        # deliberative

    result = compute_naa(v)
    assert result["classification"] == "LOW"
    assert result["naa"] < 1.0


def test_compute_naa_high_classification(stub_roi_cache):
    v = np.zeros(20484, dtype=np.float32)
    v[0:200] = 5.0
    v[200:400] = 1.0

    result = compute_naa(v)
    assert result["classification"] == "HIGH"
    assert result["naa"] > 2.0


def test_compute_naa_zero_deliberative_uses_delta(stub_roi_cache):
    """A_del = 0 should not divide by zero -- delta protects."""
    v = np.zeros(20484, dtype=np.float32)
    v[0:200] = 1.0
    # deliberative left at zero

    result = compute_naa(v)
    assert np.isfinite(result["naa"])
    # NAA = 1.0 / (0.0 + 1e-3) = 1000
    assert result["naa"] == pytest.approx(1000.0, rel=1e-3)
    assert result["classification"] == "HIGH"


def test_compute_naa_rejects_wrong_shape(stub_roi_cache):
    with pytest.raises(ValueError):
        compute_naa(np.zeros(100))
