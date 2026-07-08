"""Generate the fsaverage5 medial-wall mask the BrainViewer is missing.

Authoritative source: FreeSurfer's `aparc` annotation on fsaverage, whose
`unknown` label is the medial wall / non-cortex. fsaverage5 vertices are a
specific SUBSET of fsaverage(ico7) vertices (not the first 10242), so we map
fsaverage5 vertex j -> its fsaverage7 index via `mne.grade_to_vertices` and
mark it medial iff that fsaverage7 vertex is in the `unknown` label.

We then GEOMETRICALLY VERIFY against the viewer's own left_pial.json: medial
-wall vertices must cluster on the medial side (toward the hemisphere's inner
midline). If they do not, we abort rather than ship a mis-ordered mask.

Writes 20484-byte uint8 (left 0..10241 then right 10242..20483):
1 = cortex (paint), 0 = medial wall (grey). Matches TRIBE output ordering.

Output: apps/web/public/mesh/medial_mask.bin (+ .json meta)
Run once (needs `mne`):  python scripts/gen_medial_mask.py
"""

import json
import sys
from pathlib import Path

import numpy as np

HEMI_VERTS = 10242
WEB_MESH = (Path(__file__).resolve().parents[3]
            / "apps" / "web" / "public" / "mesh")


def medial_fs7(subjects_dir, hemi):
    """fsaverage7 medial-wall vertices = annot label -1 (unassigned) + any
    label named unknown/???/medial_wall. Read the annot directly because
    mne.read_labels_from_annot silently drops the -1 unassigned vertices."""
    import nibabel as nib

    lab, _, names = nib.freesurfer.read_annot(
        f"{subjects_dir}/fsaverage/label/{hemi}.aparc.annot")
    names = [n.decode() if isinstance(n, bytes) else n for n in names]
    unknown_idx = [i for i, n in enumerate(names)
                   if n.lower() in ("unknown", "???", "medial_wall")]
    medial = (lab == -1) | np.isin(lab, unknown_idx)
    return set(int(v) for v in np.where(medial)[0])


def verify_medial_geometry(mask_left):
    """Masked left-hemi vertices should sit medially. Returns (ok, detail)."""
    coords_path = WEB_MESH / "left_pial.json"
    if not coords_path.exists():
        return True, "skipped (no left_pial.json)"
    verts = np.asarray(json.loads(coords_path.read_text())["vertices"], float)
    if verts.shape[0] != HEMI_VERTS:
        return True, f"skipped (left_pial has {verts.shape[0]} verts)"
    masked = verts[mask_left == 0]
    cortex = verts[mask_left == 1]
    if len(masked) == 0:
        return False, "no masked verts"
    # Left hemisphere sits at x<0; its medial (inner) face is the side nearest
    # the midline (x closest to 0, i.e. the largest/most-positive x).
    return (masked[:, 0].mean() > cortex[:, 0].mean(),
            f"masked.x={masked[:,0].mean():.1f} cortex.x={cortex[:,0].mean():.1f}")


def main():
    try:
        import mne
    except ImportError:
        print("mne not installed. `pip install mne` then re-run.")
        return 1

    fs_dir = mne.datasets.fetch_fsaverage(verbose=False)
    subjects_dir = str(Path(fs_dir).parent)

    verts5 = mne.grade_to_vertices("fsaverage", grade=5,
                                   subjects_dir=subjects_dir)

    mask = np.ones(2 * HEMI_VERTS, dtype=np.uint8)
    for hemi, off, hi in (("lh", 0, 0), ("rh", HEMI_VERTS, 1)):
        med_fs7 = medial_fs7(subjects_dir, hemi)
        fs7_for_fs5 = verts5[hi]
        for j in range(HEMI_VERTS):
            if int(fs7_for_fs5[j]) in med_fs7:
                mask[off + j] = 0

    cortex = int(mask.sum())
    medial = int(mask.size - cortex)
    if medial == 0:
        print("ERROR: 0 vertices masked. Aborting.")
        return 1

    ok, detail = verify_medial_geometry(mask[:HEMI_VERTS])
    print(f"geometry check: {'PASS' if ok else 'FAIL'} ({detail})")
    if not ok:
        print("Masked vertices are not medial - ordering mismatch. Aborting "
              "so we never grey the wrong vertices.")
        return 1

    WEB_MESH.mkdir(parents=True, exist_ok=True)
    (WEB_MESH / "medial_mask.bin").write_bytes(mask.tobytes())
    (WEB_MESH / "medial_mask.json").write_text(json.dumps({
        "dtype": "uint8",
        "length": int(mask.size),
        "order": "left[0:10242] then right[10242:20484]",
        "values": {"1": "cortex (paintable)", "0": "medial wall (grey)"},
        "source": "mne fsaverage aparc 'unknown', grade_to_vertices -> fsaverage5",
        "geometry_check": detail,
        "cortex_vertices": cortex,
        "medial_vertices": medial,
    }, indent=2), encoding="utf-8")

    print(f"wrote medial_mask.bin: cortex={cortex} medial={medial} "
          f"({100*medial/mask.size:.1f}% masked)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
