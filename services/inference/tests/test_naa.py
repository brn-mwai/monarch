"""Unit tests for app.services.naa.

Uses the ``stub_roi_cache`` fixture so the test runs without tribev2.
"""

import numpy as np
import pytest

from app.services.naa import compute_naa, compute_signed_naa


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


def test_compute_naa_valid_flag_true_on_normal(stub_roi_cache, synthetic_item_vector):
    result = compute_naa(synthetic_item_vector)
    assert result["valid"] is True
    assert result["naa"] is not None


def test_compute_naa_zero_affective_is_valid_low(stub_roi_cache):
    """Zero (at-baseline) affective activation is a valid regime, NAA = 0 -> LOW."""
    v = np.zeros(20484, dtype=np.float32)
    v[200:400] = 1.0  # deliberative only

    result = compute_naa(v)
    assert result["valid"] is True
    assert result["naa"] == pytest.approx(0.0, abs=1e-3)
    assert result["classification"] == "LOW"


def test_compute_naa_negative_deliberative_is_undefined(stub_roi_cache):
    """Below-baseline deliberative mean must NOT be silently reported as LOW."""
    v = np.zeros(20484, dtype=np.float32)
    v[0:200] = 1.5       # affective above baseline
    v[200:400] = -0.5    # deliberative below baseline

    result = compute_naa(v)
    assert result["valid"] is False
    assert result["naa"] is None
    assert result["classification"] == "UNDEFINED"
    assert result["a_aff"] == pytest.approx(1.5)
    assert result["a_del"] == pytest.approx(-0.5)


def test_compute_naa_negative_deliberative_near_minus_delta_is_undefined(stub_roi_cache):
    """The exact explosion case: a_del ~= -delta would blow up the ratio."""
    v = np.zeros(20484, dtype=np.float32)
    v[0:200] = 1.0
    v[200:400] = -1e-3   # near -delta -> old code: NAA ~ +/-1e6

    result = compute_naa(v)
    assert result["valid"] is False
    assert result["naa"] is None
    assert result["classification"] == "UNDEFINED"


def test_compute_naa_negative_affective_is_undefined(stub_roi_cache):
    v = np.zeros(20484, dtype=np.float32)
    v[0:200] = -0.8      # affective below baseline
    v[200:400] = 1.0

    result = compute_naa(v)
    assert result["valid"] is False
    assert result["classification"] == "UNDEFINED"


def test_compute_naa_both_negative_is_undefined(stub_roi_cache):
    v = np.zeros(20484, dtype=np.float32)
    v[0:200] = -0.3
    v[200:400] = -0.9

    result = compute_naa(v)
    assert result["valid"] is False
    assert result["classification"] == "UNDEFINED"


def test_compute_naa_nan_raises(stub_roi_cache):
    v = np.zeros(20484, dtype=np.float32)
    v[0:200] = np.nan

    with pytest.raises(ValueError):
        compute_naa(v)


def test_compute_naa_inf_raises(stub_roi_cache):
    v = np.zeros(20484, dtype=np.float32)
    v[200:400] = np.inf

    with pytest.raises(ValueError):
        compute_naa(v)


def test_compute_naa_boundary_one_is_moderate(stub_roi_cache):
    """NAA == 1.0 falls in MOD (LOW is strictly < 1.0). delta=0 for exactness."""
    v = np.zeros(20484, dtype=np.float32)
    v[0:200] = 1.0
    v[200:400] = 1.0

    result = compute_naa(v, delta=0.0)
    assert result["naa"] == pytest.approx(1.0)
    assert result["classification"] == "MOD"


def test_compute_naa_boundary_two_is_moderate(stub_roi_cache):
    """NAA == 2.0 falls in MOD (HIGH is strictly > 2.0). delta=0 for exactness."""
    v = np.zeros(20484, dtype=np.float32)
    v[0:200] = 2.0
    v[200:400] = 1.0

    result = compute_naa(v, delta=0.0)
    assert result["naa"] == pytest.approx(2.0)
    assert result["classification"] == "MOD"


def test_compute_naa_just_above_two_is_high(stub_roi_cache):
    v = np.zeros(20484, dtype=np.float32)
    v[0:200] = 2.5
    v[200:400] = 1.0

    result = compute_naa(v, delta=0.0)
    assert result["naa"] == pytest.approx(2.5)
    assert result["classification"] == "HIGH"


def test_compute_signed_naa_positive_when_affective_dominates(stub_roi_cache):
    v = np.zeros(20484, dtype=np.float32)
    v[0:200] = 0.4
    v[200:400] = 0.1

    result = compute_signed_naa(v)
    assert result["valid"] is True
    assert result["naa"] == pytest.approx(0.3, abs=1e-6)


def test_compute_signed_naa_defined_where_ratio_is_undefined(stub_roi_cache):
    """The case that killed the ratio: a below-baseline deliberative mean."""
    v = np.zeros(20484, dtype=np.float32)
    v[0:200] = -0.2
    v[200:400] = -0.5

    assert compute_naa(v)["valid"] is False
    signed = compute_signed_naa(v)
    assert signed["valid"] is True
    assert signed["naa"] == pytest.approx(0.3, abs=1e-6)


def test_compute_signed_naa_negative_when_deliberative_dominates(stub_roi_cache):
    v = np.zeros(20484, dtype=np.float32)
    v[0:200] = -0.3
    v[200:400] = 0.2

    assert compute_signed_naa(v)["naa"] == pytest.approx(-0.5, abs=1e-6)


def test_compute_signed_naa_rejects_wrong_shape(stub_roi_cache):
    with pytest.raises(ValueError):
        compute_signed_naa(np.zeros(100, dtype=np.float32))
