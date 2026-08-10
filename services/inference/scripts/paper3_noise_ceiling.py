"""Measure the inter-subject noise ceiling for one Friends episode, in parcel space.

This replaces the pass-1 notebook cell that produced `noise_ceiling.json`. That cell had two
defects and both of them changed the number rather than crashing, which is why this is a
script with assertions instead of a cell with a comment.

**The episode was never chosen.** The cell carried `STIMULUS = None  # set from the printed
keys` and fell back to `list(f.keys())[0]`. The first key in these files is
`ses-001_task-s01e02a`, so the ceiling was measured on a different episode from the one pass
2 predicts. Here the episode is an argument, the key is matched by name, and a file missing
that episode is an error.

**The array was transposed.** `encoder_validation` takes `(units, timepoints)`. The
recordings are stored `(timepoints, parcels)`, and the cell's `if data.shape[0] >
data.shape[1]` guard cannot fire on `(482, 1000)`, so every correlation ran across the parcel
axis and the result was an inter-subject spatial similarity per timepoint reported as a
per-parcel ceiling. Orientation is asserted against the atlas parcel count here rather than
inferred from which axis is longer.

Usage
-----
    python scripts/paper3_noise_ceiling.py --h5-dir <dir> --episode s01e01a \
        --out data/paper3/noise_ceiling.json
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from pathlib import Path

import h5py
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.encoder_validation import bootstrap_ci, noise_ceiling  # noqa: E402

N_PARCELS = 1000


def _episode_key(handle: h5py.File, episode: str) -> str:
    matches = [k for k in handle.keys() if k.endswith(f"task-{episode}")]
    if not matches:
        raise KeyError(
            f"{os.path.basename(handle.filename)} has no key for episode {episode}; "
            f"first keys are {list(handle.keys())[:3]}"
        )
    if len(matches) > 1:
        raise KeyError(f"episode {episode} is ambiguous in {handle.filename}: {matches}")
    return matches[0]


def _as_parcels_by_time(data: np.ndarray, path: str) -> np.ndarray:
    """Return the recording as (parcels, timepoints), refusing to guess.

    The orientation is decided by which axis holds the atlas parcel count, not by which axis
    is longer: an episode with more TRs than parcels would invert a length-based rule and
    still produce a plausible correlation.
    """
    if data.ndim != 2:
        raise ValueError(f"{path}: expected 2d, got {data.ndim}d")
    if data.shape[1] == N_PARCELS:
        return data.T
    if data.shape[0] == N_PARCELS:
        return data
    raise ValueError(f"{path}: neither axis is {N_PARCELS} parcels, shape {data.shape}")


def load_responses(h5_dir: Path, episode: str) -> tuple[list[np.ndarray], list[str]]:
    paths = sorted(glob.glob(str(h5_dir / "*task-friends*.h5")))
    if not paths:
        raise FileNotFoundError(f"no friends h5 files under {h5_dir}")

    responses: list[np.ndarray] = []
    for path in paths:
        with h5py.File(path, "r") as handle:
            key = _episode_key(handle, episode)
            node = handle[key]
            raw = node[list(node.keys())[0]][:] if isinstance(node, h5py.Group) else node[:]
        responses.append(_as_parcels_by_time(np.asarray(raw, dtype=float), path))
        print(f"  {os.path.basename(path)[:24]}  {key}  {responses[-1].shape}")

    shortest = min(r.shape[1] for r in responses)
    return [r[:, :shortest] for r in responses], paths


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--h5-dir", type=Path, required=True)
    parser.add_argument("--episode", default="s01e01a")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    print(f"episode {args.episode}, oriented (parcels, timepoints):")
    responses, paths = load_responses(args.h5_dir, args.episode)

    ceiling = noise_ceiling(responses)
    per_subject = np.nanmean(ceiling["per_subject_r"], axis=1)
    interval = bootstrap_ci(per_subject, n_resamples=10000, seed=0)

    print()
    print("Leave-one-subject-out noise ceiling, parcel level")
    print(f"  subjects        : {ceiling['n_subjects']}")
    print(f"  parcels defined : {ceiling['n_defined']} of {responses[0].shape[0]}")
    print(f"  timepoints      : {responses[0].shape[1]}")
    print(f"  mean ceiling    : {ceiling['mean_ceiling']:+.4f}")
    print(f"  95% CI          : [{interval['low']:+.4f}, {interval['high']:+.4f}]")
    print()
    for index, value in enumerate(per_subject):
        print(f"  subject {index + 1}: {value:+.4f}")

    result = {
        "episode": args.episode,
        "n_subjects": ceiling["n_subjects"],
        "n_parcels_total": int(responses[0].shape[0]),
        "n_parcels_defined": ceiling["n_defined"],
        "n_timepoints": int(responses[0].shape[1]),
        "mean_ceiling": ceiling["mean_ceiling"],
        "ci_low": interval["low"],
        "ci_high": interval["high"],
        "per_subject": per_subject.tolist(),
        "space": "Schaefer 1000 parcels, MNI152NLin2009cAsym",
        "orientation": "(parcels, timepoints); correlation is over time within each parcel",
        "sources": [os.path.basename(p) for p in paths],
        "note": "parcel level, not vertex level; averaging within a parcel raises r",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"\nWrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
