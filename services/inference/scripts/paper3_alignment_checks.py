"""Two checks on Paper 3's aligned prediction pass, run on CPU from the saved prediction.

**Is the correlation above chance?** Eighty scans of slowly varying BOLD can correlate with an
unrelated series by luck, so a mean ``r`` near 0.03 means nothing without a null. The null
here keeps each series intact and breaks only their alignment: the aligned prediction is
rotated circularly against the recordings by every shift of at least ``MIN_SHIFT`` scans, and
the group mean ``r`` is recomputed at each. The p-value is the share of shifts reaching the
observed value, counting the observed alignment itself.

**How much does the response delay matter?** The primary result uses the 5 s delay the
checkpoint was trained with, fixed before the data were seen. Other delays are reported as
sensitivity only. Choosing the best-scoring delay after the fact would inflate the result, so
nothing here selects one.

Usage
-----
    python scripts/paper3_alignment_checks.py \\
        --prediction data/final/paper3/prediction_s01e01a_first120s.npy \\
        --h5-dir <algonauts fmri dir> --episode s01e01a \\
        --out data/final/paper3/alignment_checks.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.encoder_validation import vertex_correlation  # noqa: E402
from app.services.parcellation import project_to_parcels  # noqa: E402
from app.services.temporal_alignment import RESPONSE_DELAY_S, align_to_recording  # noqa: E402
from scripts.paper3_noise_ceiling import N_PARCELS, load_responses  # noqa: E402

DEFAULT_LABELS = Path(__file__).resolve().parents[1] / "data" / "schaefer1000_fsaverage5.npy"
MIN_SHIFT = 10
SENSITIVITY_DELAYS_S = (3.0, 4.0, 5.0, 6.0, 7.0)


def group_mean_r(predicted: np.ndarray, responses: list[np.ndarray]) -> tuple[float, list[float]]:
    per_subject = [float(vertex_correlation(predicted, observed)["mean_r"])
                   for observed in responses]
    return float(np.mean(per_subject)), per_subject


def aligned_pair(projected: np.ndarray, responses: list[np.ndarray],
                 delay: float) -> tuple[np.ndarray, list[np.ndarray]]:
    n_recorded = min(r.shape[1] for r in responses)
    alignment = align_to_recording(projected, n_recorded, response_delay=delay)
    scans = alignment["scan_indices"]
    return alignment["aligned"], [r[:, scans] for r in responses]


def circular_shift_null(predicted: np.ndarray, responses: list[np.ndarray]) -> dict:
    observed, _ = group_mean_r(predicted, responses)
    n_scans = predicted.shape[1]
    shifts = range(MIN_SHIFT, n_scans - MIN_SHIFT + 1)
    null = np.array([group_mean_r(np.roll(predicted, shift, axis=1), responses)[0]
                     for shift in shifts])
    reached = int(np.sum(null >= observed))
    return {
        "observed": observed,
        "n_shifts": int(null.size),
        "min_shift_scans": MIN_SHIFT,
        "null_mean": float(null.mean()),
        "null_sd": float(null.std(ddof=1)),
        "null_max": float(null.max()),
        "p_one_sided": (reached + 1) / (null.size + 1),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prediction", type=Path, required=True)
    parser.add_argument("--h5-dir", type=Path, required=True)
    parser.add_argument("--episode", required=True)
    parser.add_argument("--labels", type=Path, default=DEFAULT_LABELS)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    prediction = np.load(args.prediction)
    labels = np.load(args.labels)
    projected = project_to_parcels(prediction.T, labels, n_parcels=N_PARCELS)["parcel_timeseries"]
    responses, _ = load_responses(args.h5_dir, args.episode)

    predicted, observed = aligned_pair(projected, responses, RESPONSE_DELAY_S)
    null = circular_shift_null(predicted, observed)
    print(f"primary (delay {RESPONSE_DELAY_S:.0f} s): mean r {null['observed']:+.4f}, "
          f"circular-shift null {null['null_mean']:+.4f} +/- {null['null_sd']:.4f} "
          f"over {null['n_shifts']} shifts, max {null['null_max']:+.4f}, "
          f"p = {null['p_one_sided']:.4f}")

    sensitivity = []
    for delay in SENSITIVITY_DELAYS_S:
        predicted_d, observed_d = aligned_pair(projected, responses, delay)
        mean_r, per_subject = group_mean_r(predicted_d, observed_d)
        sensitivity.append({"delay_s": delay, "n_scans": int(predicted_d.shape[1]),
                            "mean_r": mean_r, "per_subject_mean_r": per_subject})
        print(f"sensitivity delay {delay:.0f} s: mean r {mean_r:+.4f} "
              f"over {predicted_d.shape[1]} scans")

    result = {
        "episode": args.episode,
        "primary_delay_s": RESPONSE_DELAY_S,
        "circular_shift_null": null,
        "delay_sensitivity": sensitivity,
        "note": "primary delay fixed from the checkpoint's training offset; sensitivity rows "
                "are not a selection",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
