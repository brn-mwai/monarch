# 01 - TRIBE v2 File Map

Every Python file, notebook, and data artefact in `C:\Users\Windows\Downloads\tribev2\`.
Subdirectories `.git/`, `__pycache__/`, `*.pyc`, `*.egg-info/` are skipped.

Grand total: **26 Python source files + 1 notebook + 7 mesh artefacts + 4 docs**.

---

## Root

| Path | Purpose |
|---|---|
| `LICENSE` | CC-BY-NC-4.0 (non-commercial). **Blocker for a paid SaaS Monarch.** |
| `README.md` | Top-level doc. Lists the HF model id `facebook/tribev2`, claims `(n_timesteps, n_vertices)` output on fsaverage5. |
| `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md` | Standard Meta OSS boilerplate. Not used. |
| `pyproject.toml` | Hard deps `neuralset==0.0.2`, `neuraltrain==0.0.2` (Meta internal, unknown if on any public index), `torch>=2.5.1,<2.7`, `numpy==2.2.6`, `x_transformers==1.27.20`, `moviepy>=2.2.1`, `gtts`, `langdetect`, `spacy`, `soundfile`, `Levenshtein`, `julius`, `transformers`, `huggingface_hub`, `einops`, `pyyaml`. Optional: `plotting` (nilearn, pyvista, colorcet, nibabel, matplotlib, seaborn, scipy, scikit-image), `training` (torchmetrics, wandb, lightning), `test` (pytest). **Implicit deps not listed**: `mne` (utils.py), `requests`/`tqdm` (demo_utils.py), `whisperx` (invoked via `uvx` subprocess), `exca`, `pydantic`. |
| `tribe_demo.ipynb` | 17-cell Colab walkthrough. Loads `facebook/tribev2`, predicts on Sintel trailer (53 TRs) and Shakespeare text (24 TRs), visualises with `PlotBrain.plot_timesteps(cmap="fire", norm_percentile=99, vmin=.5, alpha_cmap=(0,.2))`. This is the ONLY code sample in the repo. |

## `scripts/`

| Path | Purpose |
|---|---|
| `scripts/export_brain_mesh.py` | **Standalone** fsaverage5 mesh exporter that deliberately does NOT import `tribev2` (because the tribev2 import chain fails on this Windows box via neuraltrain -> torchmetrics -> onnxruntime DLL). Reproduces `BasePlotBrain.get_mesh()` inline with nilearn+nibabel and writes to `monarch-meshes/`. The recipe the Monarch build team should copy for any offline mesh step. |

## `monarch-meshes/` (pre-generated output)

These are ready for the Monarch frontend. Already checked in.

| Path | Shape | Notes |
|---|---|---|
| `left_pial.json` / `right_pial.json` | 10242 verts, 20480 faces, sulc 10242 | JSON for web. ~1.2 MB each. |
| `left_inflated.json` / `right_inflated.json` | same | "inflate=True" geometry (not the "half" variant). |
| `fsaverage5_combined.bin` | ~1.04 MB | Compact binary of both hemispheres, pial+inflated. |
| `fsaverage5_combined.layout.json` | 8 sections | Byte offsets into the .bin. |
| `metadata.json` | | `verticesPerHemisphere=10242`, `totalVertices=20484`, `facesPerHemisphere=20480`, sulc range `-1.494..1.841`, per-hemisphere bounding boxes. |

## `tribev2/` (the Python package)

### Top-level modules

| File | 1-line summary | Key exports |
|---|---|---|
| `tribev2/__init__.py` | Single line `from tribev2.demo_utils import TribeModel`. | `TribeModel` |
| `tribev2/demo_utils.py` | High-level inference wrapper (`TribeModel`, `TextToEvents`, `get_audio_and_text_events`, `download_file`). This is the **only public API** Monarch needs. | `TribeModel.from_pretrained`, `TribeModel.get_events_dataframe`, `TribeModel.predict`, `VALID_SUFFIXES` |
| `tribev2/eventstransforms.py` | Custom events transforms registered into neuralset: `SplitEvents` (deterministic train/val split), `ExtractWordsFromAudio` (runs `uvx whisperx` subprocess), `CreateVideosFromImages` (moviepy `ImageClip`), `RemoveDuplicates`, `assign_splits`, `SPLIT_ATTRIBUTES` dict for each study. | All four transforms as classes. |
| `tribev2/main.py` | `Data` (pydantic config for DataLoaders) and `TribeExperiment` (pydantic Lightning-based pipeline). `TribeModel` inherits from `TribeExperiment`. Contains `_free_extractor_model` to release GPU memory between sequential extractors. | `Data`, `TribeExperiment` |
| `tribev2/model.py` | The brain encoder. `FmriEncoder` (BaseModelConfig) is the config, `FmriEncoderModel` (nn.Module) is the runtime object. Also `TemporalSmoothing` (unused in released weights). | `FmriEncoder`, `FmriEncoderModel`, `TemporalSmoothing` |
| `tribev2/pl_module.py` | `BrainModule` - pytorch_lightning wrapper. `on_save_checkpoint` stashes `model_build_args` (feature_dims, n_outputs, n_output_timesteps) that `from_pretrained` later reads. | `BrainModule` |
| `tribev2/utils.py` | `MultiStudyLoader`, `split_segments_by_time`, `assign_fmri_space`, `set_study_in_average_subject_mode`, `get_subject_weights`, **HCP helpers**: `get_hcp_labels` (lru_cached; calls mne), `get_hcp_vertex_labels`, `get_hcp_roi_indices`, `summarize_by_roi`, `get_topk_rois`. Also `FMRI_SPACES` and `RECORDING_DURATIONS` dicts. | The HCP helpers are the backbone of Monarch's NAA computation. |
| `tribev2/utils_fmri.py` | `FmriTemplateSpace` enum (all MNI + fsaverage + CIFTI variants with voxel shapes), `is_mni_space`, `load_mni_mesh`, `TribeSurfaceProjector` (subclasses `ns.extractors.neuro.SurfaceProjector`, uses `nilearn.surface.vol_to_surf` or downsampling). | `FmriTemplateSpace.FSAVERAGE_5 = (id='fsaverage5', shape=(10242,))` - this is WHERE the 10242 number lives in code. |

### `tribev2/plotting/`

| File | 1-line summary |
|---|---|
| `plotting/__init__.py` | Re-exports `BasePlotBrain`, `PlotBrainNilearn`, `PlotBrainPyvista`, `plot_subcortical`, `get_subcortical_roi_indices`, and all the utils helpers. **`PlotBrain = PlotBrainPyvista`** is the default. |
| `plotting/base.py` | `BasePlotBrain` (pydantic): loads the fsaverage mesh via `cached_fetch_surf_fsaverage`, `get_mesh()` splits left+right with `inflate=bool|"half"` logic, `get_stat_map()` splits a (N,) array by hemisphere (with upsampling via cKDTree for cross-resolution), `get_hemis()` combines geometry + data, `plot_timesteps()` builds a matplotlib mosaic, `plot_timesteps_mp4()` calls ffmpeg, `plot_stimuli()` overlays audio waveform and transcript text. |
| `plotting/cortical.py` | `PlotBrainNilearn` - matplotlib 3D backend via `nilearn.plotting.plot_surf_stat_map`. 12 views in `VIEW_DICT`. Also has `plot_surf_rgb` for multi-modal RGB mixing. |
| `plotting/cortical_pv.py` | `PlotBrainPyvista` - the default backend. `dpi=3000`, off-screen PyVista screenshots rasterised into matplotlib axes. Has `annotate_rois` (labels HCP ROIs by center-of-mass) and `plot_surf_rgb` (3-modality RGB visualisation). |
| `plotting/subcortical.py` | Harvard-Oxford subcortical atlas rendering with marching cubes meshes. `get_subcortical_mask`, `get_subcortical_labels`, `cached_ho_atlas`, `get_subcortical_roi_indices`, `voxel_to_mesh`, `plot_subcortical`. **Not connected to the released checkpoint** (the released `facebook/tribev2` is cortical only). |
| `plotting/utils.py` | Heavy utility module. **Key functions**: `robust_normalize(array, percentile=99)` - the backbone of value normalisation; `get_cmap` (matplotlib -> seaborn -> colorcet fallback chain); `get_scalar_mappable`; `get_thresholded_sm`; `get_alpha_cmap`; `saturate_colors`; `tight_crop`; `get_rainbow_brain` (hue-by-longitude demo helper); `combine_mosaics`; `plot_rgb_colorbar`; segment helpers `has_video`, `has_audio`, `get_clip`, `get_audio`, `get_words`, `get_text`. |

### `tribev2/studies/`

| File | 1-line summary | TR | Subjects |
|---|---|---|---|
| `studies/__init__.py` | Re-exports the four study classes. | - | - |
| `studies/algonauts2025.py` | `Algonauts2025` (Schaefer-1000 parcellated HDF5) and `Algonauts2025Bold` (raw nifti via fmriprep). Friends + movie10 films. | **1.49 s** | 4 (sub-01,02,03,05) |
| `studies/lahner2024bold.py` | `Lahner2024Bold` - BOLD Moments 3s video clips. 1000 train, 102 test. Subjects watch in 4 sessions. | **1.75 s** | 10 |
| `studies/lebel2023bold.py` | `Lebel2023Bold` - 8 subjects listening to spoken narratives (UTS01..UTS08). Uses `nltk_contrib.textgrid` for word/phoneme timings. | **2.0 s** | 8 |
| `studies/wen2017.py` | `Wen2017` - 3 subjects watching video clips from cerebral cortex paper. | **2.0 s** | 3 |

### `tribev2/grids/`

| File | 1-line summary |
|---|---|
| `grids/__init__.py` | Empty (1 line). |
| `grids/defaults.py` | **`default_config`** - the canonical training config dict that the released model was trained with. ~260 lines. Defines text/audio/video/image/neuro extractor configs, brain model hyperparameters (`hidden=1152`, `low_rank_head=2048`, `depth=8`, `extractor_aggregation="cat"`, `layer_aggregation="cat"`, `combiner=None`, `modality_dropout=0.3`), data config (`duration_trs=100`, `layers_to_use=[0.5, 0.75, 1.0]`, `layer_aggregation="group_mean"`), and Slurm infra. |
| `grids/run_cortical.py` | Grid over `data.study.names` (single study OR all-four ensemble). Calls `neuraltrain.utils.run_grid` with `combinatorial=True`, `infra_mode="force"`. |
| `grids/run_subcortical.py` | Same grid but swaps `data.neuro.projection` to `MaskProjector(mask="subcortical", fwhm=6.0)`. **No checkpoint is published for this.** |
| `grids/test_run.py` | Local debugging entry point. Strips cluster, shortens to 3 epochs, narrows to `Algonauts2025Bold / subject_timeline_index<3`. |

## `tribev2.egg-info/`

Standard setuptools metadata, auto-generated at install time. Safe to ignore - `PKG-INFO`, `SOURCES.txt`, `dependency_links.txt`, `requires.txt`, `top_level.txt`.

---

## Quick triage - which file to open for which question

| Question | Open |
|---|---|
| How do I call predict()? | `demo_utils.py:322-392` |
| What shape comes out? | `demo_utils.py:382` + `model.py:163-178` (pooler) |
| What config fields does from_pretrained read? | `demo_utils.py:204-225` |
| What model architecture? | `model.py:89-234` + `grids/defaults.py:201-214` |
| How does text get turned into audio? | `demo_utils.py:98-130` (`TextToEvents` via `gTTS`) |
| How does audio get turned into words? | `eventstransforms.py:86-212` (`uvx whisperx` subprocess) |
| What ROIs exist? | `utils.py:213-256` (`get_hcp_labels` via `mne.datasets.fetch_hcp_mmp_parcellation`) |
| How is a (20484,) vector normalised for display? | `plotting/utils.py:19-35` (`robust_normalize`) |
| How does the mesh get loaded? | `plotting/base.py:127-172` (`BasePlotBrain.get_mesh`) |
| How is the sulcal background blended? | `plotting/cortical_pv.py:123-128` (`rgba*a + bg*(1-a)`) |
| Is there a subcortical checkpoint? | **No.** `grids/run_subcortical.py` exists, but no published weights. |
