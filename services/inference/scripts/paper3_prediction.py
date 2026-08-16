"""Run the released checkpoint over one Friends episode and correlate it against the
recordings, in the parcel space the pass-1 ceiling was measured in.

This is pass 2 of Paper 3. It was a notebook cell, and the cell failed twice on Kaggle for
the same environment reason: installing the pinned stack upgrades numpy on disk while the
kernel process already holds the image's numpy in memory, so the first in-kernel import of
scipy reads a new ``numpy/_core/strings.py`` against an old compiled ``umath`` and dies on
``cannot import name '_center'``. The corpus scan never hit this because every heavy step
there runs in a ``%%bash`` subprocess, which starts after the installs and sees one numpy.
So the logic lives here and the notebook shells out to it.

Orientation and episode matching are inherited from the pass-1 script rather than restated:
selecting a record by position and inferring orientation from axis length are the two defects
that produced the withdrawn ceiling.

Usage
-----
    python scripts/paper3_prediction.py \
        --stimulus /kaggle/input/.../friends_s01e01a.mkv \
        --h5-dir /kaggle/input/.../fmri \
        --out /kaggle/working/paper3_validation.json \
        --prediction-out /kaggle/working/prediction.npy
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.encoder_validation import bootstrap_ci, noise_ceiling, vertex_correlation  # noqa: E402
from app.services.inference import TribeInferenceService  # noqa: E402
from app.services.parcellation import project_to_parcels  # noqa: E402
from scripts.paper3_noise_ceiling import N_PARCELS, load_responses  # noqa: E402

DEFAULT_LABELS = Path(__file__).resolve().parents[1] / "data" / "schaefer1000_fsaverage5.npy"


def episode_of(stimulus: Path) -> str:
    """``friends_s01e01a.mkv`` -> ``s01e01a``, the token the h5 keys end with."""
    return stimulus.stem.split("_")[-1]


def predict(stimulus: Path, prediction_out: Path | None) -> np.ndarray:
    service = TribeInferenceService()
    service.load_model()
    result = service.predict_video(stimulus)
    prediction = np.asarray(result["raw_preds"], dtype=np.float32)
    print(f"prediction: {prediction.shape} over {result['n_trs']} TRs")

    # Written before anything downstream can fail: this is the only part that needs a GPU,
    # and a later error must not cost the hours it took.
    if prediction_out is not None:
        prediction_out.parent.mkdir(parents=True, exist_ok=True)
        np.save(prediction_out, prediction)
        print(f"wrote {prediction_out}")
    return prediction


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stimulus", type=Path, required=True)
    parser.add_argument("--h5-dir", type=Path, required=True)
    parser.add_argument("--episode", default=None,
                        help="defaults to the trailing token of the stimulus filename")
    parser.add_argument("--labels", type=Path, default=DEFAULT_LABELS,
                        help="one Schaefer parcel label per fsaverage5 vertex")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--prediction-out", type=Path, default=None)
    args = parser.parse_args()

    episode = args.episode or episode_of(args.stimulus)
    print(f"stimulus {args.stimulus.name}, episode {episode}")

    prediction = predict(args.stimulus, args.prediction_out)

    labels = np.load(args.labels)
    # The checkpoint emits fsaverage5 vertices and the recordings are parcels. The prediction
    # is projected down rather than the recordings upsampled, which would invent within-parcel
    # structure the data does not have.
    projected = project_to_parcels(prediction.T, labels, n_parcels=N_PARCELS)["parcel_timeseries"]
    print(f"projected to parcels: {projected.shape}")

    print(f"recordings for {episode}, oriented (parcels, timepoints):")
    responses, paths = load_responses(args.h5_dir, episode)

    shortest = min([projected.shape[1]] + [r.shape[1] for r in responses])
    projected = projected[:, :shortest]
    responses = [r[:, :shortest] for r in responses]
    print(f"subjects {len(responses)}, parcels {responses[0].shape[0]}, timepoints {shortest}")

    per_subject = [vertex_correlation(projected, observed) for observed in responses]
    means = np.array([r["mean_r"] for r in per_subject])
    encoder = bootstrap_ci(means, n_resamples=10000, seed=0)

    ceiling = noise_ceiling(responses)
    ceiling_ci = bootstrap_ci(np.nanmean(ceiling["per_subject_r"], axis=1),
                              n_resamples=10000, seed=0)

    print()
    print("Checkpoint against held-out subjects, parcel level")
    print(f"  encoder mean r : {encoder['point']:+.4f}  "
          f"95% CI [{encoder['low']:+.4f}, {encoder['high']:+.4f}]")
    print(f"  noise ceiling  : {ceiling_ci['point']:+.4f}  "
          f"95% CI [{ceiling_ci['low']:+.4f}, {ceiling_ci['high']:+.4f}]")
    print(f"  beats zero     : {encoder['low'] > 0}")
    print(f"  reaches ceiling: {encoder['low'] >= ceiling_ci['point']}")
    print()
    for index, value in enumerate(means):
        print(f"  subject {index + 1}: {value:+.4f}")

    result = {
        "stimulus": args.stimulus.name,
        "episode": episode,
        "encoder": encoder,
        "ceiling": ceiling_ci,
        "per_subject_mean_r": means.tolist(),
        "n_parcels_defined": [int(r["n_defined"]) for r in per_subject],
        "n_timepoints": int(shortest),
        "sources": [Path(p).name for p in paths],
        "space": "Schaefer 1000 parcels",
        "note": "parcel level; not comparable with the audit's vertex-level r",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"\nWrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
