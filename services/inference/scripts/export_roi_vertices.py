"""Export the real HCP MMP1.0 ROI vertex sets used by the NAA index.

Replicates tribev2.utils.get_hcp_roi_indices via mne directly so it runs
without importing tribev2 (whose onnxruntime dependency is broken on
Windows). Produces:

  services/inference/data/roi_definitions.json   (backend cache)
  apps/web/public/mesh/roi_vertices.json         (frontend renderer)

Vertex indices are into the (20484,) fsaverage5 vector: left hemisphere
0..10241, right hemisphere +10242. The HCP annotation lives on full-res
fsaverage; fsaverage5 is its first 10242 vertices per hemisphere, so we
keep label vertices below that threshold (matching tribev2).
"""

import json
import os
from pathlib import Path

import mne

AFFECTIVE_ROIS = [
    "OFC", "pOFC", "p24", "a24", "TGd", "TE1a", "TE1p", "IFSa", "IFSp", "AAIC",
]
DELIBERATIVE_ROIS = [
    "46", "a9-46v", "p9-46v", "11l", "13l", "d32", "p32", "a10p", "p10p", "10pp",
]

# Modality networks for the multimodal RGB view (paper Fig 7): video -> visual
# cortex, audio -> auditory cortex, text -> language network + prefrontal.
VISUAL_ROIS = [
    "V1", "V2", "V3", "V4", "V3A", "V3B", "V6", "V7", "V8", "VVC", "VMV1",
    "VMV2", "VMV3", "PIT", "FFC", "LO1", "LO2", "LO3", "MT", "MST", "V4t", "PH",
]
AUDITORY_ROIS = [
    "A1", "A4", "A5", "MBelt", "LBelt", "PBelt", "RI", "STGa", "STSdp", "STSvp",
    "TA2",
]
LANGUAGE_ROIS = [
    "44", "45", "47l", "IFSa", "IFSp", "STSva", "STSda", "TPOJ1", "PSL", "SFL",
    "46", "9-46d", "8C", "8Av", "9a", "a9-46v", "p9-46v",
]

FSAVERAGE5_VERTICES = 10242

REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_OUT = REPO_ROOT / "services" / "inference" / "data" / "roi_definitions.json"
FRONTEND_OUT = REPO_ROOT / "apps" / "web" / "public" / "mesh" / "roi_vertices.json"
MODALITY_OUT = REPO_ROOT / "apps" / "web" / "public" / "mesh" / "modality_vertices.json"


def parcel_name(label_name: str) -> str:
    name = label_name
    for suffix in ("-lh", "-rh"):
        if name.endswith(suffix):
            name = name[: -len(suffix)]
    if name.startswith(("L_", "R_")):
        name = name[2:]
    if name.endswith("_ROI"):
        name = name[: -len("_ROI")]
    return name


def collect_vertices(labels, wanted: list[str]) -> list[int]:
    wanted_set = set(wanted)
    vertices: set[int] = set()
    for label in labels:
        if parcel_name(label.name) not in wanted_set:
            continue
        fs5 = label.vertices[label.vertices < FSAVERAGE5_VERTICES]
        offset = FSAVERAGE5_VERTICES if label.hemi == "rh" else 0
        vertices.update((fs5 + offset).tolist())
    return sorted(vertices)


def main() -> None:
    fsaverage_dir = mne.datasets.fetch_fsaverage()
    subjects_dir = os.path.dirname(fsaverage_dir)
    mne.datasets.fetch_hcp_mmp_parcellation(subjects_dir=subjects_dir, accept=True)

    labels = mne.read_labels_from_annot(
        "fsaverage", "HCPMMP1", hemi="both", subjects_dir=subjects_dir
    )

    affective = collect_vertices(labels, AFFECTIVE_ROIS)
    deliberative = collect_vertices(labels, DELIBERATIVE_ROIS)

    print(f"affective: {len(affective)} vertices, deliberative: {len(deliberative)}")
    if not affective or not deliberative:
        raise SystemExit("ROI vertex collection returned empty; check parcel names")

    BACKEND_OUT.parent.mkdir(parents=True, exist_ok=True)
    BACKEND_OUT.write_text(
        json.dumps(
            {
                "affective": affective,
                "deliberative": deliberative,
                "affective_rois": AFFECTIVE_ROIS,
                "deliberative_rois": DELIBERATIVE_ROIS,
            }
        )
    )
    FRONTEND_OUT.parent.mkdir(parents=True, exist_ok=True)
    FRONTEND_OUT.write_text(
        json.dumps({"affective": affective, "deliberative": deliberative})
    )

    visual = collect_vertices(labels, VISUAL_ROIS)
    auditory = collect_vertices(labels, AUDITORY_ROIS)
    language = collect_vertices(labels, LANGUAGE_ROIS)
    print(
        f"visual: {len(visual)}, auditory: {len(auditory)}, language: {len(language)}"
    )
    MODALITY_OUT.write_text(
        json.dumps({"visual": visual, "auditory": auditory, "language": language})
    )

    print(f"wrote {BACKEND_OUT}")
    print(f"wrote {FRONTEND_OUT}")
    print(f"wrote {MODALITY_OUT}")


if __name__ == "__main__":
    main()
