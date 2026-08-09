"""Surface figures that show only what was measured.

Two kinds come out, and the difference between them is the whole point.

**The ROI definition map** paints the affective-salience and deliberative-control vertex
sets on the fsaverage5 surface. It carries no data at all, so it cannot mislead: it answers
what the index compares.

**ROI-mean maps** paint each network with the single mean the scan produced for it, per
category or per item. They are flat by construction and must stay flat. Smooth shading would
draw vertex-level structure from two scalars, which is drawing structure that was never
measured. The scan discards the per-vertex vector after reducing it, so that structure does
not exist on disk and cannot be recovered by rendering.

Every caption states which kind it is. A figure that does not say whether it is a definition
or a measurement is one somebody will read as the wrong one.

Usage
-----
    python scripts/render_brain_figures.py --out-dir data/figures
    python scripts/render_brain_figures.py --out-dir data/figures --scan data/corpus_naa.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.roi import (  # noqa: E402
    get_affective_indices,
    get_deliberative_indices,
)

VERTICES = 20484
HEMI_VERTICES = 10242

AFFECTIVE_CODE = 1.0
DELIBERATIVE_CODE = 2.0


def definition_map() -> np.ndarray:
    """Vertexwise label array: NaN elsewhere, 1 affective-salience, 2 deliberative-control.

    NaN rather than 0 outside the two networks. A zero is a value, and the renderer paints
    it, which turns every unlabelled vertex into a third apparent network and hides the
    sulcal shading that makes the surface readable as anatomy.
    """
    labels = np.full(VERTICES, np.nan, dtype=float)
    labels[get_affective_indices()] = AFFECTIVE_CODE
    labels[get_deliberative_indices()] = DELIBERATIVE_CODE
    return labels


def roi_mean_map(a_aff: float, a_del: float) -> np.ndarray:
    """Each network painted with its own mean, uniform within the network.

    NaN outside the two networks so the renderer leaves that cortex unpainted rather than
    colouring it zero, which would read as a measured value of zero.
    """
    values = np.full(VERTICES, np.nan, dtype=float)
    values[get_affective_indices()] = a_aff
    values[get_deliberative_indices()] = a_del
    return values


def category_means(rows: list[dict]) -> dict[str, dict]:
    """Mean a_aff and a_del per category, with the count they came from."""
    grouped: dict[str, list[tuple[float, float]]] = {}
    for row in rows:
        if not row.get("a_aff") or not row.get("a_del"):
            continue
        grouped.setdefault(row["category"], []).append(
            (float(row["a_aff"]), float(row["a_del"]))
        )

    out = {}
    for category, pairs in sorted(grouped.items()):
        aff = np.array([p[0] for p in pairs])
        dele = np.array([p[1] for p in pairs])
        out[category] = {
            "n": len(pairs),
            "a_aff": float(aff.mean()),
            "a_del": float(dele.mean()),
            "a_aff_sd": float(aff.std(ddof=1)) if len(pairs) > 1 else float("nan"),
            "a_del_sd": float(dele.std(ddof=1)) if len(pairs) > 1 else float("nan"),
        }
    return out


def _two_colour_map():
    """Exactly two colours, so a label map cannot read as a continuous quantity."""
    from matplotlib.colors import ListedColormap

    return ListedColormap(["#e8730c", "#1f6fb4"])


def _load_surface():
    from nilearn import datasets

    return datasets.fetch_surf_fsaverage("fsaverage5")


def _render(values: np.ndarray, surface, title: str, out_dir: Path, stem: str,
            formats: list[str], cmap: str, vmin: float | None, vmax: float | None,
            colorbar: bool) -> None:
    import matplotlib

    matplotlib.use("Agg")
    matplotlib.rcParams["pdf.fonttype"] = 42
    matplotlib.rcParams["svg.fonttype"] = "none"
    import matplotlib.pyplot as plt
    from nilearn import plotting

    fig, axes = plt.subplots(1, 2, figsize=(9.0, 3.6),
                             subplot_kw={"projection": "3d"})
    for ax, hemi, mesh, bg, slice_ in (
        (axes[0], "left", surface.infl_left, surface.sulc_left, slice(0, HEMI_VERTICES)),
        (axes[1], "right", surface.infl_right, surface.sulc_right,
         slice(HEMI_VERTICES, VERTICES)),
    ):
        plotting.plot_surf(
            mesh,
            values[slice_],
            hemi=hemi,
            view="lateral",
            bg_map=bg,
            cmap=cmap,
            vmin=vmin,
            vmax=vmax,
            colorbar=colorbar and hemi == "right",
            avg_method="median",
            axes=ax,
            figure=fig,
        )
        ax.set_title(hemi, fontsize=9)

    fig.suptitle(title, fontsize=10)
    # subplots_adjust rather than tight_layout: 3d axes are not compatible with it and it
    # warns that the result may be wrong.
    fig.subplots_adjust(left=0.02, right=0.98, top=0.88, bottom=0.02, wspace=0.05)
    for fmt in formats:
        fig.savefig(out_dir / f"{stem}.{fmt}", dpi=200 if fmt == "png" else None,
                    format=fmt, bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--scan", type=Path,
                        help="scan CSV; without it only the definition map is drawn")
    parser.add_argument("--category-col", default="category")
    parser.add_argument("--formats", default="png,pdf")
    args = parser.parse_args()

    formats = [f.strip().lower() for f in args.formats.split(",") if f.strip()]
    unknown = [f for f in formats if f not in ("png", "pdf", "svg")]
    if unknown:
        print(f"[FAIL] unsupported format(s): {', '.join(unknown)}", file=sys.stderr)
        return 1

    args.out_dir.mkdir(parents=True, exist_ok=True)
    surface = _load_surface()

    aff_n = len(get_affective_indices())
    del_n = len(get_deliberative_indices())
    _render(
        definition_map(), surface,
        f"ROI definition, not a measurement: affective-salience ({aff_n} vertices, orange) "
        f"and deliberative-control ({del_n}, blue)",
        args.out_dir, "B1_roi_definition", formats,
        cmap=_two_colour_map(), vmin=AFFECTIVE_CODE, vmax=DELIBERATIVE_CODE, colorbar=False,
    )
    print(f"B1_roi_definition: affective {aff_n} vertices, deliberative {del_n} vertices")

    if not args.scan:
        print(f"\nWrote {args.out_dir}/ : definition map only (no --scan given)")
        return 0

    if not args.scan.exists():
        print(f"[FAIL] {args.scan} not found", file=sys.stderr)
        return 1

    with open(args.scan, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    means = category_means(rows)
    if not means:
        print("[FAIL] no usable a_aff / a_del values in the scan", file=sys.stderr)
        return 1

    # One scale across every category, so the panels can be compared by eye. Per-panel
    # scaling would make categories look different when only their colour maps differ.
    all_values = [m[k] for m in means.values() for k in ("a_aff", "a_del")]
    limit = max(abs(min(all_values)), abs(max(all_values)))

    print(f"\nscanned rows: {len(rows)}")
    for category, m in means.items():
        _render(
            roi_mean_map(m["a_aff"], m["a_del"]), surface,
            f"{category} (n={m['n']}): ROI means, uniform within ROI, not vertexwise",
            args.out_dir, f"B2_roi_means_{category}", formats,
            cmap="coolwarm", vmin=-limit, vmax=limit, colorbar=True,
        )
        print(f"  {category:24s} n={m['n']:3d}  a_aff={m['a_aff']:+.4f}  "
              f"a_del={m['a_del']:+.4f}")

    print(f"\nWrote {args.out_dir}/ : 1 definition map and {len(means)} ROI-mean maps "
          f"in {', '.join(formats)}")
    print("ROI-mean maps carry two numbers each. They are not vertexwise activation, and")
    print("their captions say so, because the per-vertex vectors are not retained by the scan.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
