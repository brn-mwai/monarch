"""Project fsaverage5 vertex predictions into parcels, so they can meet the public data.

The released checkpoint emits 20484 fsaverage5 vertices (``tribe-ckpt/config.yaml``,
``mesh: fsaverage5``). The Algonauts 2025 public release, which is the CC0 data anyone can
obtain, is 1000 Schaefer parcels rather than a surface. Comparing the two therefore needs the
prediction reduced to parcels, which is also the space TRIBE was scored in.

The reduction is not free of consequence and the consequence runs one way: averaging vertices
within a parcel cancels independent noise, so parcel correlations are systematically higher
than vertex correlations on the same data. A parcel-level r is therefore **not** comparable to
the vertex-level r = -0.0145 reported by the audit under test. Both numbers are worth having;
conflating them would manufacture a disagreement or a rescue that is really just a change of
spatial unit.
"""

from __future__ import annotations

import numpy as np

MEDIAL_WALL_LABEL = 0


def project_to_parcels(
    vertex_timeseries: np.ndarray,
    labels: np.ndarray,
    n_parcels: int | None = None,
) -> dict:
    """Average vertex time series within each parcel.

    ``vertex_timeseries`` is (vertices, timepoints). ``labels`` is one integer per vertex,
    with :data:`MEDIAL_WALL_LABEL` marking vertices belonging to no parcel; those are dropped
    rather than pooled into a parcel they are not part of.

    NaN vertices are excluded from their parcel's mean instead of poisoning it, and a parcel
    left with no usable vertex is NaN and counted rather than reported as zero.
    """
    data = np.asarray(vertex_timeseries, dtype=float)
    label_array = np.asarray(labels)

    if data.ndim != 2:
        raise ValueError(f"expected (vertices, timepoints), got {data.ndim}d")
    if label_array.ndim != 1:
        raise ValueError(f"labels must be one per vertex, got {label_array.ndim}d")
    if label_array.shape[0] != data.shape[0]:
        raise ValueError(
            f"labels cover {label_array.shape[0]} vertices, data has {data.shape[0]}"
        )

    present = [int(v) for v in np.unique(label_array) if int(v) != MEDIAL_WALL_LABEL]
    total = n_parcels if n_parcels is not None else (max(present) if present else 0)
    if total < 1:
        raise ValueError("no parcels found outside the medial wall")

    out = np.full((total, data.shape[1]), np.nan, dtype=float)
    vertices_used = np.zeros(total, dtype=int)

    for parcel in range(1, total + 1):
        rows = data[label_array == parcel]
        if rows.size == 0:
            continue
        usable = rows[~np.isnan(rows).all(axis=1)]
        if usable.size == 0:
            continue
        with np.errstate(invalid="ignore"):
            out[parcel - 1] = np.nanmean(usable, axis=0)
        vertices_used[parcel - 1] = usable.shape[0]

    empty = int((vertices_used == 0).sum())
    return {
        "parcel_timeseries": out,
        "n_parcels": total,
        "vertices_per_parcel": vertices_used,
        "n_empty_parcels": empty,
        "n_medial_wall_vertices": int((label_array == MEDIAL_WALL_LABEL).sum()),
    }
