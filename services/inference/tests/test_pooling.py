"""Unit tests for app.services.pooling."""

import numpy as np
import pytest

from app.services.pooling import mean_pool, peak_pool, trimmed_mean_pool


def test_mean_pool_basic():
    preds = np.array(
        [
            [1.0, 2.0, 3.0],
            [3.0, 4.0, 5.0],
        ],
        dtype=np.float32,
    )
    out = mean_pool(preds)
    np.testing.assert_allclose(out, [2.0, 3.0, 4.0])


def test_mean_pool_rejects_1d():
    with pytest.raises(ValueError):
        mean_pool(np.array([1.0, 2.0, 3.0]))


def test_trimmed_mean_zero_trim_matches_mean():
    rng = np.random.default_rng(0)
    preds = rng.normal(size=(10, 5)).astype(np.float32)
    np.testing.assert_allclose(
        trimmed_mean_pool(preds, trim=0.0), mean_pool(preds), rtol=1e-6
    )


def test_trimmed_mean_drops_outliers():
    # 5 rows, all 1.0 except first which is huge.
    preds = np.ones((5, 3), dtype=np.float32)
    preds[0] = 1000.0
    out = trimmed_mean_pool(preds, trim=0.2)  # drop 1 row each tail
    np.testing.assert_allclose(out, [1.0, 1.0, 1.0])


def test_trimmed_mean_invalid_trim():
    preds = np.zeros((4, 2))
    with pytest.raises(ValueError):
        trimmed_mean_pool(preds, trim=0.5)
    with pytest.raises(ValueError):
        trimmed_mean_pool(preds, trim=-0.1)


def test_peak_pool():
    preds = np.array(
        [
            [1.0, 5.0, 2.0],
            [4.0, 3.0, 7.0],
            [2.0, 9.0, 6.0],
        ],
        dtype=np.float32,
    )
    np.testing.assert_allclose(peak_pool(preds), [4.0, 9.0, 7.0])
