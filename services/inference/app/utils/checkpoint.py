"""Checkpoint-resume batch inference using ``numpy.memmap``.

Because AMD Kaggle GPU sessions have a finite duration, the batch
pipeline writes activation vectors to a memory-mapped array that is
flushed to disk after every item. A small JSON progress file records
which item indices have completed. On restart, inference resumes from
the checkpoint without reprocessing completed items.

Modalities are processed in cost order: text -> audio -> video.
"""

import json
from pathlib import Path

import numpy as np


class BatchCheckpoint:
    """Memory-mapped checkpoint-resume manager for batch inference."""

    VERTICES = 20484

    def __init__(self, output_dir: Path, total_items: int) -> None:
        self.output_dir = output_dir
        self.total_items = total_items
        output_dir.mkdir(parents=True, exist_ok=True)

        self.memmap_path = output_dir / "activations.mmap"
        self.progress_path = output_dir / "progress.json"

        if self.memmap_path.exists() and self.progress_path.exists():
            # Resume mode
            self.activations = np.memmap(
                self.memmap_path,
                dtype=np.float32,
                mode="r+",
                shape=(total_items, self.VERTICES),
            )
            with open(self.progress_path) as f:
                self.progress = json.load(f)
        else:
            # Fresh start
            self.activations = np.memmap(
                self.memmap_path,
                dtype=np.float32,
                mode="w+",
                shape=(total_items, self.VERTICES),
            )
            self.progress = {"completed": [], "last_index": -1}
            self._flush_progress()

    @property
    def last_completed_index(self) -> int:
        return int(self.progress["last_index"])

    def is_completed(self, index: int) -> bool:
        return index in self.progress["completed"]

    def save_item(self, index: int, vector: np.ndarray) -> None:
        """Write one activation vector and update the checkpoint."""
        if vector.shape != (self.VERTICES,):
            raise ValueError(
                f"Expected ({self.VERTICES},) vector, got {vector.shape}"
            )
        self.activations[index] = vector.astype(np.float32)
        self.activations.flush()

        if index not in self.progress["completed"]:
            self.progress["completed"].append(index)
        self.progress["last_index"] = max(self.progress["last_index"], index)
        self._flush_progress()

    def get_remaining_indices(self) -> list[int]:
        completed = set(self.progress["completed"])
        return [i for i in range(self.total_items) if i not in completed]

    def get_all_activations(self) -> np.ndarray:
        """Return the full (N, 20484) array as a regular ndarray."""
        return np.array(self.activations)

    def _flush_progress(self) -> None:
        with open(self.progress_path, "w") as f:
            json.dump(self.progress, f)
