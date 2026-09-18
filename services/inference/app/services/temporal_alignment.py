"""Put a prediction and a recording on the same clock before correlating them.

The released checkpoint emits one prediction per 0.5 s of stimulus: ``TribeModel.predict``
cuts each batch into segments of ``data.TR``, and the checkpoint's ``data.frequency`` is 2 Hz.
It was trained against BOLD shifted back by the ``Fmri`` extractor's ``offset`` of 5 s
(``neuralset.extractors.neuro``, ``start=ta.start - self.offset``), so the prediction for
stimulus time ``t`` estimates the BOLD recorded at ``t + 5``. The Algonauts 2025 recordings
are sampled every 1.49 s from stimulus onset.

Paper 3's first prediction pass truncated both arrays to the shorter length and correlated
them sample by sample, so prediction ``k`` (stimulus time ``0.5 k``) was scored against scan
``k`` (recorded at ``1.49 k``). By the 241st sample the two were four minutes apart. Nothing
failed and the number looked plausible, which is the same shape as the two defects behind the
withdrawn noise ceiling.

This module maps each recorded scan to the stimulus time it responds to and interpolates the
prediction there. Scans whose stimulus time falls outside the predicted window are dropped
rather than extrapolated, and their indices travel with the result so the noise ceiling can
be measured on exactly the same scans.
"""

from __future__ import annotations

import numpy as np

PREDICTION_STEP_S = 0.5
RESPONSE_DELAY_S = 5.0
ALGONAUTS_TR_S = 1.49


def align_to_recording(
    prediction: np.ndarray,
    n_recorded: int,
    recording_tr: float = ALGONAUTS_TR_S,
    prediction_step: float = PREDICTION_STEP_S,
    response_delay: float = RESPONSE_DELAY_S,
) -> dict:
    """Resample a ``(units, prediction_samples)`` prediction onto recorded scan times.

    Returns the prediction at each usable scan, ``(units, n_scans)``, and the indices of
    those scans in the recording.
    """
    if prediction.ndim != 2:
        raise ValueError(f"prediction must be (units, samples), got {prediction.shape}")
    if min(recording_tr, prediction_step) <= 0:
        raise ValueError("sampling intervals must be positive")

    n_predicted = prediction.shape[1]
    scan_times = np.arange(n_recorded) * recording_tr
    stimulus_times = scan_times - response_delay
    prediction_times = np.arange(n_predicted) * prediction_step

    usable = (stimulus_times >= prediction_times[0]) & (stimulus_times <= prediction_times[-1])
    scan_indices = np.flatnonzero(usable)
    if scan_indices.size == 0:
        raise ValueError("no recorded scan falls inside the predicted window")

    aligned = np.empty((prediction.shape[0], scan_indices.size), dtype=np.float64)
    for unit, series in enumerate(prediction):
        aligned[unit] = np.interp(stimulus_times[scan_indices], prediction_times, series)

    return {
        "aligned": aligned,
        "scan_indices": scan_indices,
        "recording_tr": recording_tr,
        "prediction_step": prediction_step,
        "response_delay": response_delay,
    }
