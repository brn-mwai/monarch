"""Tests for putting a prediction and a recording on one clock.

The defect these guard against produced a plausible correlation from series sampled at
different rates, so each test builds a case where the right answer is known and a
sample-by-sample comparison would get it wrong.
"""

from __future__ import annotations

import numpy as np
import pytest

from app.services.temporal_alignment import align_to_recording


def _signal(t: np.ndarray) -> np.ndarray:
    return np.sin(2 * np.pi * t / 37.0) + 0.5 * np.cos(2 * np.pi * t / 11.0)


def test_recovers_the_recording_when_both_sample_one_signal() -> None:
    stimulus_t = np.arange(241) * 0.5
    prediction = _signal(stimulus_t)[None, :]
    scan_t = np.arange(300) * 1.49
    recording = _signal(scan_t - 5.0)

    result = align_to_recording(prediction, n_recorded=300)
    idx = result["scan_indices"]

    assert np.corrcoef(result["aligned"][0], recording[idx])[0, 1] > 0.999


def test_sample_by_sample_truncation_would_have_failed_the_same_case() -> None:
    prediction = _signal(np.arange(241) * 0.5)
    recording = _signal(np.arange(300) * 1.49 - 5.0)

    naive = np.corrcoef(prediction, recording[:241])[0, 1]

    assert naive < 0.5


def test_keeps_only_scans_whose_stimulus_time_was_predicted() -> None:
    result = align_to_recording(np.zeros((3, 241)), n_recorded=300)
    idx = result["scan_indices"]
    stimulus_t = idx * 1.49 - 5.0

    assert stimulus_t.min() >= 0.0
    assert stimulus_t.max() <= 120.0
    assert idx[0] == 4
    assert idx[-1] == 83
    assert result["aligned"].shape == (3, idx.size)


def test_rejects_a_recording_that_ends_before_the_delay() -> None:
    with pytest.raises(ValueError, match="no recorded scan"):
        align_to_recording(np.zeros((1, 241)), n_recorded=3)


def test_rejects_a_prediction_in_the_wrong_orientation() -> None:
    with pytest.raises(ValueError, match="units, samples"):
        align_to_recording(np.zeros(241), n_recorded=300)
