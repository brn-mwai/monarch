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

Two things this script learned from a run that spent twelve GPU-hours and reported nothing.

**Every stage announces itself, with elapsed seconds.** The encoder pass is dataloader-bound:
``TribeModel.predict`` batches 60-second chunks, and the cost is video feature extraction
inside the loader, not the forward pass. A run that cannot say which chunk it is on is a run
whose remaining time cannot be estimated, and the only honest thing to do with it is kill it.

**``--max-seconds`` trims the stimulus.** The comparison needs the same timepoints on both
sides, not all of them: ``shortest`` already truncates the recordings to the prediction. A
window that finishes and reports its own ``n_timepoints`` is worth more than a full episode
that hits the session cap and reports nothing.

Usage
-----
    python -u scripts/paper3_prediction.py \
        --stimulus /kaggle/input/.../friends_s01e01a.mkv \
        --h5-dir /kaggle/input/.../fmri \
        --out /kaggle/working/paper3_validation.json \
        --prediction-out /kaggle/working/prediction.npy \
        --max-seconds 120

``python -u`` is not decoration. tqdm writes to stderr and the subprocess is not a tty, so
without it the progress bar sits in a buffer that a killed process never flushes.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.encoder_validation import bootstrap_ci, noise_ceiling, vertex_correlation  # noqa: E402
from app.services.inference import TribeInferenceService  # noqa: E402
from app.services.parcellation import project_to_parcels  # noqa: E402
from scripts.paper3_noise_ceiling import N_PARCELS, load_responses  # noqa: E402

DEFAULT_LABELS = Path(__file__).resolve().parents[1] / "data" / "schaefer1000_fsaverage5.npy"

_STARTED = time.monotonic()


def say(message: str) -> None:
    """Print with elapsed seconds, so a stalled stage is visible as a stalled stage."""
    print(f"[{time.monotonic() - _STARTED:7.1f}s] {message}", flush=True)


def episode_of(stimulus: Path) -> str:
    """``friends_s01e01a.mkv`` -> ``s01e01a``, the token the h5 keys end with."""
    return stimulus.stem.split("_")[-1]


def stage(stimulus: Path, work_dir: Path) -> Path:
    """Return a copy of the stimulus somewhere writable, or the original if it already is.

    tribev2 extracts the audio track by writing a ``.wav`` beside the video, so a stimulus on
    a read-only mount fails inside moviepy with a broken pipe and an ffmpeg message about the
    filesystem. Kaggle mounts every dataset read-only, which is where this was found.
    """
    if os.access(stimulus.parent, os.W_OK):
        return stimulus

    work_dir.mkdir(parents=True, exist_ok=True)
    staged = work_dir / stimulus.name
    if not staged.exists() or staged.stat().st_size != stimulus.stat().st_size:
        say(f"staging {stimulus.name} ({stimulus.stat().st_size / 1e6:.0f} MB) to {work_dir}")
        shutil.copy2(stimulus, staged)
        say("staged")
    return staged


def trim(stimulus: Path, seconds: float, work_dir: Path) -> Path:
    """Cut the first ``seconds`` of the stimulus, re-encoding nothing.

    Stream copy keeps this to a few seconds on a 580 MB file. The cut lands on the nearest
    preceding keyframe, so the trimmed duration is approximate and the reported
    ``n_timepoints`` comes from the prediction rather than from this number.
    """
    work_dir.mkdir(parents=True, exist_ok=True)
    trimmed = work_dir / f"{stimulus.stem}_first{int(seconds)}s{stimulus.suffix}"
    if trimmed.exists():
        say(f"trimmed stimulus already present: {trimmed.name}")
        return trimmed

    say(f"trimming {stimulus.name} to {seconds:.0f}s")
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(stimulus),
         "-t", str(seconds), "-c", "copy", str(trimmed)],
        check=True,
    )
    say(f"trimmed to {trimmed.stat().st_size / 1e6:.0f} MB")
    return trimmed


def predict(stimulus: Path, prediction_out: Path | None) -> np.ndarray:
    service = TribeInferenceService()
    say("loading checkpoint")
    service.load_model()
    say("checkpoint loaded, starting the encoder pass")
    say("this is dataloader-bound: video features are extracted per 60s chunk")
    result = service.predict_video(stimulus)
    prediction = np.asarray(result["raw_preds"], dtype=np.float32)
    say(f"prediction: {prediction.shape} over {result['n_trs']} TRs")

    # Written before anything downstream can fail: this is the only part that needs a GPU,
    # and a later error must not cost the hours it took.
    if prediction_out is not None:
        prediction_out.parent.mkdir(parents=True, exist_ok=True)
        np.save(prediction_out, prediction)
        say(f"wrote {prediction_out}")
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
    parser.add_argument("--work-dir", type=Path,
                        default=Path(tempfile.gettempdir()) / "monarch-stimulus",
                        help="where to stage the stimulus when its own directory is read-only")
    parser.add_argument("--max-seconds", type=float, default=None,
                        help="predict only the first N seconds; the recordings are truncated "
                             "to match, so the comparison stays on the same timepoints")
    args = parser.parse_args()

    episode = args.episode or episode_of(args.stimulus)
    say(f"stimulus {args.stimulus.name}, episode {episode}")

    staged = stage(args.stimulus, args.work_dir)
    if args.max_seconds is not None:
        staged = trim(staged, args.max_seconds, args.work_dir)
    prediction = predict(staged, args.prediction_out)

    say("projecting to parcels")
    labels = np.load(args.labels)
    # The checkpoint emits fsaverage5 vertices and the recordings are parcels. The prediction
    # is projected down rather than the recordings upsampled, which would invent within-parcel
    # structure the data does not have.
    projected = project_to_parcels(prediction.T, labels, n_parcels=N_PARCELS)["parcel_timeseries"]
    say(f"projected to parcels: {projected.shape}")

    say(f"loading recordings for {episode}, oriented (parcels, timepoints)")
    responses, paths = load_responses(args.h5_dir, episode)

    shortest = min([projected.shape[1]] + [r.shape[1] for r in responses])
    projected = projected[:, :shortest]
    responses = [r[:, :shortest] for r in responses]
    say(f"subjects {len(responses)}, parcels {responses[0].shape[0]}, timepoints {shortest}")

    say("correlating and bootstrapping")
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
        "max_seconds": args.max_seconds,
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
    say(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
