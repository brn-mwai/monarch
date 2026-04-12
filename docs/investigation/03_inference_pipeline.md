# 03 - Inference Pipeline (The Critical-Path Doc)

Every function call from `model.predict_text("...")` to a `(T, 20484)` numpy array. File:line references throughout.

---

## 0. Context

"Monarch predict_text" is the Monarch backend's `TribeInferenceService.predict_text` in `C:\Users\Windows\Downloads\monarch-backend\app\services\inference.py:76-112`. The TRIBE v2 equivalent is:

```python
events_df = model.get_events_dataframe(text_path=Path("foo.txt"))
preds, segments = model.predict(events=events_df)
```

There is **no** direct `predict_text` method in TribeModel. The Monarch wrapper writes the string to a temp file, calls `get_events_dataframe`, then `predict`.

## 1. Model load: `TribeModel.from_pretrained`

`demo_utils.py:150-241`. Pseudocode with shapes and what-happens annotations:

```
# 1.1 Path resolution (demo_utils.py:190-203)
cache_folder.mkdir(exist_ok=True)                                       # creates user-supplied cache dir
device = "cuda" if torch.cuda.is_available() else "cpu"                 # auto
if Path(checkpoint_dir).exists():                                        # local dir
    config_path = checkpoint_dir / "config.yaml"
    ckpt_path   = checkpoint_dir / "best.ckpt"
else:                                                                    # HF hub repo id
    from huggingface_hub import hf_hub_download
    config_path = hf_hub_download(repo_id, "config.yaml")               # -> ~/.cache/huggingface/hub/...
    ckpt_path   = hf_hub_download(repo_id, "best.ckpt")                 # ~1 GB

# 1.2 Config parse (line 204-205)
config = ConfDict(yaml.load(open(config_path), Loader=yaml.UnsafeLoader))
# UnsafeLoader is required because exca.ConfDict emits Python class refs.

# 1.3 Config mutation (lines 206-225; see 02_config_analysis.md for the full field list)
#   - redirect text/audio/video feature infra.folder/cluster to cache_folder
#   - pop infra.workdir, data.study.infra_timelines, data.neuro.infra, data.image_feature.infra
#   - data.study.path = "."
#   - average_subjects = True
#   - checkpoint_path = f"{infra.folder}/best.ckpt"
#   - cache_folder = str(cache_folder) or "./cache"

# 1.4 Instantiate TribeExperiment (line 225)
xp = TribeModel(**config)
# This runs TribeExperiment.model_post_init (main.py:327-376):
#   - infra.tasks_per_node = infra.gpus_per_node
#   - average_subjects branch sets:
#       brain_model_config.subject_layers.average_subjects = True
#       brain_model_config.subject_layers.n_subjects = 0
#       data.neuro.aggregation = "mean"
#       calls set_study_in_average_subject_mode(...) which adds AlignEvents + RemoveDuplicates
#         transforms to the study chain (with trigger_type "Video" or "Audio" depending on study).
#   - resize_subject_layer branch is False, so no SVD reinitialisation.

# 1.5 Checkpoint load (lines 227-237)
logger.info(f"Loading model from {ckpt_path}")
ckpt = torch.load(ckpt_path, map_location="cpu", weights_only=True, mmap=True)
# Checkpoint format is the Lightning dict from BrainModule.on_save_checkpoint:
#   ckpt["state_dict"]       : model.<path> : tensor
#   ckpt["model_build_args"] : {"feature_dims": {...}, "n_outputs": 20484, "n_output_timesteps": 100}

build_args = ckpt["model_build_args"]
state_dict = {k.removeprefix("model."): v for k, v in ckpt["state_dict"].items()}
del ckpt

# 1.6 Build the FmriEncoderModel (line 235)
model = xp.brain_model_config.build(**build_args)
# This hits FmriEncoder.build -> FmriEncoderModel(feature_dims=..., n_outputs=20484,
#                                                 n_output_timesteps=100, config=FmriEncoder(...))
# Which invokes __init__ (model.py:91-157):
#   - For each modality in feature_dims, build an Mlp projector (input_dim = num_layers*feature_dim,
#     output_dim = hidden//n_modalities = 384 for cat aggregation).
#   - combiner = nn.Identity() because config.combiner is None.
#   - low_rank_head = nn.Linear(1152, 2048, bias=False).
#   - predictor = SubjectLayers.build(in_channels=2048, out_channels=20484).
#   - time_pos_embed = nn.Parameter(randn(1, 1024, 1152)).
#   - encoder = TransformerEncoder(dim=1152, depth=8, ...) - x_transformers.

# 1.7 Load weights (line 236)
model.load_state_dict(state_dict, strict=True, assign=True)
del state_dict

# 1.8 Place on device + eval mode (lines 238-240)
model.to(device)
model.eval()
xp._model = model
return xp
```

Note on `feature_dims` in the build args: this is a dict like `{"text": (3, 3072), "audio": (2, 1024), "video": (2, 1408)}` where each tuple is `(num_layers, feature_dim)`. The exact numbers depend on what was actually cached at training time and is written into the checkpoint. Monarch can't hand-compute this without reading `best.ckpt`.

---

## 2. Events DataFrame construction: `get_events_dataframe`

`demo_utils.py:243-320`. Input: exactly one of `text_path`, `audio_path`, `video_path` as a string or Path. Output: standardised pandas DataFrame.

### 2a. Validation
```
# demo_utils.py:277-301
provided = {name: value for (name, value) in [...] if value is not None}
if len(provided) != 1:
    raise ValueError(...)

name, value = next(iter(provided.items()))
path = Path(value)
if path.suffix.lower() not in VALID_SUFFIXES[name]:
    raise ValueError(...)
if not path.is_file():
    raise FileNotFoundError(...)
```

`VALID_SUFFIXES` = `{"text_path": {".txt"}, "audio_path": {".wav",".mp3",".flac",".ogg"}, "video_path": {".mp4",".avi",".mkv",".mov",".webm"}}`.

### 2b. Text path branch (demo_utils.py:303-310)
```
text = path.read_text(encoding="utf-8")
if not text.strip():
    raise ValueError(f"Text file is empty: {path}")
return TextToEvents(
    text=text,
    infra={"folder": self.cache_folder, "mode": "retry"},
).get_events()
```

`TextToEvents.get_events()` (demo_utils.py:112-130):
```
from gtts import gTTS
from langdetect import detect

audio_path = Path(self.infra.uid_folder(create=True)) / "audio.mp3"
lang = detect(self.text)                                # "en"
tts = gTTS(self.text, lang=lang)
tts.save(str(audio_path))                               # requires network for first use

audio_event = {
    "type": "Audio",
    "filepath": str(audio_path),
    "start": 0,
    "timeline": "default",
    "subject": "default",
}
return get_audio_and_text_events(pd.DataFrame([audio_event]))
```

The `@infra.apply()` decorator caches results via exca so repeated same-text calls hit the cache.

### 2c. Audio / video path branch (demo_utils.py:312-320)
```
event_type = "Audio" if audio_path is not None else "Video"
event = {
    "type": event_type,
    "filepath": str(path),
    "start": 0,
    "timeline": "default",
    "subject": "default",
}
return get_audio_and_text_events(pd.DataFrame([event]))
```

### 2d. `get_audio_and_text_events` (demo_utils.py:66-95)

```
transforms = [
    ExtractAudioFromVideo(),                         # video -> emit Audio event
    ChunkEvents("Audio", max_duration=60, min_duration=30),
    ChunkEvents("Video", max_duration=60, min_duration=30),
    ExtractWordsFromAudio(),                         # runs `uvx whisperx ...` subprocess
    AddText(),
    AddSentenceToWords(max_unmatched_ratio=0.05),
    AddContextToWords(sentence_only=False, max_context_len=1024, split_field=""),
    RemoveMissing(),
]
events = standardize_events(events)
for t in transforms:
    events = t(events)
return standardize_events(events)
```

Output columns (evidence from notebook display): at minimum `type`, `start`, `duration`, `filepath`, `text`, `context`. `type` values include `Audio`, `Video`, `Sentence`, `Text`, `Word`. Text events carry the full concatenated transcript string; Word events carry `text`, `start`, `duration`, `context` (up to 1024-token running window), `sentence_id`, `sentence`, `language`. Neuralset's `standardize_events` wraps this into a DataFrame with consistent dtypes and adds a `timeline` column.

Notebook verification: for the 52.21 s Sintel trailer -> 30 Word events + 1 Audio + 1 Video + 1 Text + sentences. For the 23.256 s Shakespeare text -> 1 Audio + 1 Text + N word events (shown in cells 12-15).

### 2e. `ExtractWordsFromAudio` (eventstransforms.py:86-212)

Important detail the Monarch team needs: this transform **shells out**. It runs:

```
uvx whisperx <wav_file> \
  --model large-v3 \
  --language en \
  --device cuda|cpu \
  --compute_type float16 \
  --batch_size 16 \
  --align_model WAV2VEC2_ASR_LARGE_LV60K_960H \   # for english
  --output_dir <tempdir> \
  --output_format json
```

The output JSON is parsed and each word row becomes a pandas row with `text`, `start`, `duration`, `sequence_id`, `sentence`. Transcripts are cached to `<wav>.tsv` next to the audio file. The hard-coded language default is `english`. `_get_transcript_from_audio` raises `RuntimeError` if the whisperx subprocess exits non-zero.

**Blocker for Monarch container**: the container must have `uv` on PATH, and at first use `uvx` will download whisperx + large-v3 + wav2vec2 align model from HuggingFace. Bake those caches into the Docker image or the first request will hang for minutes.

---

## 3. `predict`: `demo_utils.py:322-392`

```python
def predict(self, events, verbose=True):
    if self._model is None:
        raise RuntimeError("TribeModel must be instantiated via .from_pretrained")
    model = self._model

    # 3.1 Build a DataLoader over the events DF for split="all"
    loader = self.data.get_loaders(events=events, split_to_build="all")["all"]
    # -> DataLoader of SegmentDataset.
    # Segments are rolling windows of duration = data.duration_trs * data.TR = 100 * 1 = 100 s,
    # stride = (duration_trs - overlap_trs) * TR = 100 * 1 = 100 s.
    # For events shorter than 100 s, exactly one segment is built covering the full timeline.

    preds, all_segments = [], []
    n_samples, n_kept = 0, 0
    with torch.inference_mode():
        for batch in tqdm(loader, disable=not verbose):
            batch = batch.to(model.device)

            # 3.2 Decompose each 100-TR window into per-TR sub-segments
            batch_segments = []
            for segment in batch.segments:
                for t in np.arange(0, segment.duration - 1e-2, self.data.TR):
                    batch_segments.append(
                        segment.copy(offset=t, duration=self.data.TR)
                    )
            # batch_segments length = batch_size * 100 (for complete windows)

            # 3.3 Filter empty TRs (remove_empty_segments=True by default)
            if self.remove_empty_segments:
                keep = np.array([len(s.ns_events) > 0 for s in batch_segments])
            else:
                keep = np.ones(len(batch_segments), dtype=bool)
            n_kept += keep.sum()
            n_samples += len(batch_segments)
            batch_segments = [s for i, s in enumerate(batch_segments) if keep[i]]

            # 3.4 Forward pass
            y_pred = model(batch).detach().cpu().numpy()
            # Shape: (B, O=20484, T'=100)

            y_pred = rearrange(y_pred, "b d t -> (b t) d")[keep]
            # Shape: (n_kept_in_batch, 20484)

            preds.append(y_pred)
            all_segments.extend(batch_segments)

    preds = np.concatenate(preds)            # (n_kept_total, 20484)
    # Length sanity check
    if len(all_segments) != preds.shape[0]:
        raise ValueError(...)
    logger.info("Predicted %d / %d segments", n_kept, n_samples)
    return preds, all_segments
```

Shapes at each step:

| Step | Shape |
|---|---|
| `batch.data["text"]` | `(B, L_text, D_text, T_feat)` with `L_text=3 layers, D_text=3072, T_feat=100*2=200` (feature_freq=2 Hz, window=100 TR=100s) |
| `batch.data["audio"]` | `(B, L_audio, D_audio, T_feat)` where L_audio is 2 or 3 after subselection, D_audio=1024 |
| `batch.data["video"]` | `(B, L_video, D_video, T_feat)` with D_video=1408 |
| `batch.data["subject_id"]` | `(B,)` int (all zero in average-subject mode) |
| After `FmriEncoderModel.aggregate_features` | `(B, 200, 1152)` (cat'd across layers and modalities) |
| After transformer + low_rank_head + predictor | `(B, 20484, 200)` -> pooled to `(B, 20484, 100)` by `AdaptiveAvgPool1d(100)` |
| `rearrange("b d t -> (b t) d")` | `(B*100, 20484)` |
| `[keep]` | `(n_kept_in_batch, 20484)` |
| Final concat | **`(n_kept_total, 20484)`** |

Notebook observation: Sintel (52.21 s) -> 53 kept of 100 segments = 53%. Shakespeare (23.256 s) -> 24 kept of 100 = 24%. The "100 segments" confirms `duration_trs=100` and the "kept count" confirms 1 TR per second with empty-TR dropping. So **T = ceil(actual_duration_s) - empty_trs**.

---

## 4. `FmriEncoderModel.forward` (model.py:163-178)

```python
def forward(self, batch, pool_outputs=True):
    x = self.aggregate_features(batch)              # (B, T_feat, hidden=1152)
    subject_id = batch.data.get("subject_id", None) # (B,) or None

    if hasattr(self, "temporal_smoothing"):
        x = self.temporal_smoothing(x.transpose(1, 2)).transpose(1, 2)
    if not self.config.linear_baseline:
        x = self.transformer_forward(x, subject_id) # same shape

    x = x.transpose(1, 2)                            # (B, 1152, T_feat)
    if self.config.low_rank_head is not None:
        x = self.low_rank_head(x.transpose(1, 2)).transpose(1, 2)
        # Linear(1152 -> 2048) along the channel dim. Shape: (B, 2048, T_feat)
    x = self.predictor(x, subject_id)                # (B, 20484, T_feat)  via SubjectLayers
    if pool_outputs:
        out = self.pooler(x)                         # (B, 20484, 100)  via AdaptiveAvgPool1d(100)
    else:
        out = x
    return out
```

`transformer_forward` (model.py:227-234):
```python
def transformer_forward(self, x, subject_id=None):
    x = self.combiner(x)                             # Identity(), no shape change
    if hasattr(self, "time_pos_embed"):
        x = x + self.time_pos_embed[:, : x.size(1)] # positional encoding up to max_seq_len=1024
    if hasattr(self, "subject_embed"):               # disabled in release
        x = x + self.subject_embed(subject_id)
    x = self.encoder(x)                              # x_transformers 8-layer TransformerEncoder
    return x
```

## 5. `aggregate_features`: the missing-modality logic (model.py:180-225)

**This is the single most important function for Monarch's multimodal split-view.**

```python
def aggregate_features(self, batch):
    tensors = []
    # Find B, T from the FIRST modality actually present in batch.data (not guaranteed to be text)
    for modality in batch.data.keys():
        if modality in self.feature_dims:
            break
    x = batch.data[modality]
    B, T = x.shape[0], x.shape[-1]

    for modality in self.feature_dims.keys():                 # iterate over EVERY registered modality
        if modality not in self.projectors or modality not in batch.data:
            # MISSING MODALITY -> zero tensor
            data = torch.zeros(
                B, T, self.config.hidden // len(self.feature_dims)     # (B, T, 384)
            ).to(x.device)
        else:
            data = batch.data[modality]                        # (B, L, H, T) or (B, H, T)
            data = data.to(torch.float32)
            if data.ndim == 3:
                data = data.unsqueeze(1)                       # (B, 1, H, T)
            if self.config.layer_aggregation == "mean":
                data = data.mean(dim=1)
            elif self.config.layer_aggregation == "cat":
                data = rearrange(data, "b l d t -> b (l d) t") # (B, L*H, T)
            data = data.transpose(1, 2)                        # (B, T, L*H)
            # Projector: Linear(L*H -> 384) per modality
            if isinstance(self.projectors[modality], SubjectLayersModel):
                data = self.projectors[modality](data.transpose(1,2), batch.data["subject_id"]).transpose(1,2)
            else:
                data = self.projectors[modality](data)          # (B, T, 384)
            if self.config.modality_dropout > 0 and self.training:
                mask = torch.rand(data.shape[0]) < self.config.modality_dropout
                data[mask, :] = torch.zeros_like(data[mask, :])
        tensors.append(data)

    if self.config.extractor_aggregation == "stack":
        out = torch.cat(tensors, dim=1)                         # concat along time (weird; used only if stack)
    elif self.config.extractor_aggregation == "cat":
        out = torch.cat(tensors, dim=-1)                        # concat along feature -> (B, T, 1152)
    elif self.config.extractor_aggregation == "sum":
        out = sum(tensors)

    if self.config.temporal_dropout > 0 and self.training:
        ...                                                     # random time steps zeroed
    return out
```

**Observations the Monarch team must internalise:**

1. **Missing modalities are SILENTLY replaced with zero tensors.** This means you can call `predict` on a text-only events DF (no Video/Audio-from-video branch), and the video projector channels will simply be zero. The output is still a valid `(T, 20484)` vector, but it represents the model's prediction *assuming video was blank*. This is fundamentally different from "what if the subject saw only text" - the model was trained with modality_dropout=0.3 so it has learned to cope with zero channels, but the resulting predictions are NOT physiologically clean per-modality brain responses.
2. **There is no built-in per-modality split.** To get "what would the brain do for just the audio?", you'd need to pass three separate events DataFrames (one with only Audio, one with only Video, one with only Text -> ...wait, text always comes with Audio because of gTTS). Closest clean per-modality call: audio_only events DF, video_only events DF, text-via-gTTS events DF. All three go through the same `predict()`.
3. **The SubjectLayersModel projector branch is only hit if the projector IS a SubjectLayers** - in the release config `projector = Mlp`, so the else branch fires and we do a plain `Mlp(data)` projection.
4. **modality_dropout is gated on `self.training`.** `model.eval()` is set in `from_pretrained`, so at inference the dropout is deterministic / disabled. Inference is reproducible modulo nondeterministic CUDA kernels.

---

## 6. `TribeExperiment` relationships

- `TribeExperiment` (main.py:278-651) is a pydantic BaseModel subclassing `neuraltrain.utils.BaseExperiment`. It contains:
  - `data: Data` - the Data pydantic model (see below).
  - `brain_model_config: BaseModelConfig` - always FmriEncoder in the release.
  - `loss`, `optim`, `metrics`, `wandb_config` - training only.
  - `average_subjects: bool` - toggles the mean-subject head.
  - `_trainer`, `_model`, `_logger` - private runtime state.
  - `infra: TaskInfra` - exca task infra (Slurm cluster config, etc.).
- `TribeModel` (demo_utils.py:133-241) subclasses `TribeExperiment` and only adds:
  - `cache_folder: str = "./cache"` and `remove_empty_segments: bool = True`.
  - `from_pretrained` classmethod.
  - `get_events_dataframe` helper.
  - `predict` method.
- `Data` (main.py:82-275) is a pydantic model with all the extractor configs, `features_to_use`, etc. Key methods:
  - `Data.TR` (property) = `1 / self.neuro.frequency` = **1.0 s** in release.
  - `Data.get_events()` (main.py:149-158) runs the study to produce a training events DataFrame. Not used by Monarch.
  - `Data.get_loaders(events=..., split_to_build="all")` (main.py:160-275): given an events DF, builds a neuralset `SegmentDataset` and returns `{"all": DataLoader}`. This is the critical entry point from `predict()`.
    - For each modality in `features_to_use`, the corresponding extractor's `.prepare(events)` is called, which caches features to `cache_folder`. `_free_extractor_model` is called between extractors to release GPU RAM for the next one.
    - Segments are built via `ns.segments.list_segments(events, triggers=..., stride=100.0, duration=100.0)` (with `TR=1.0`, `duration_trs=100`).
    - `SegmentDataset(extractors=..., segments=..., remove_incomplete_segments=False)` wraps everything and yields `SegmentData` batches.
  - `study_summary()` pulls metadata from each study for subject-id mapping. Disabled by `average_subjects=True`.

---

## 7. `BrainModule` (pl_module.py)

PyTorch Lightning wrapper around `FmriEncoderModel`. Irrelevant for inference EXCEPT for two things:

1. **`on_save_checkpoint`** (pl_module.py:47-52) stashes `model_build_args = {"feature_dims", "n_outputs", "n_output_timesteps"}` into the Lightning dict. This is what `from_pretrained` reads back in step 1.5.
2. **`forward` just delegates to `self.model(batch)`** - no wrapping logic at inference.

The rest (`_run_step`, `training_step`, `configure_optimizers`) is training-only.

---

## 8. Transforms used at inference

Reviewed in `eventstransforms.py`:

| Transform | What it does | Role at inference |
|---|---|---|
| `SplitEvents(val_ratio)` | Deterministic train/val split on `SPLIT_ATTRIBUTES[study]`. | Training only. Dropped from the chain in average-subject mode. |
| `ExtractWordsFromAudio(language="english")` | Shells out to `uvx whisperx`. Returns Word events. | **Hot path** for all inference. Requires `uv` + network for first whisperx download. |
| `CreateVideosFromImages(fps=10)` | moviepy.ImageClip -> mp4, for still-image inputs. | Not used on standard text/audio/video paths. Only relevant if the caller adds Image events manually. |
| `RemoveDuplicates(subset="filepath")` | Drops rows with duplicate filepaths. | Used in average-subject mode via `set_study_in_average_subject_mode` (main.py:168-179). |

---

## 9. ROI helpers in `utils.py`

Exact signatures and return types:

```python
# utils.py:213-256
@lru_cache
def get_hcp_labels(
    mesh: str = "fsaverage5",
    combine: bool = False,
    hemi: Literal["left","right","both"] = "both",
) -> dict[str, np.ndarray]:
    """
    Returns {parcel_name: vertex_indices_into_(20484,)_vector}.
    Right-hemi vertex lists already include the +10242 offset.
    combine=False uses HCPMMP1 (180 parcels/hemi = 360 total).
    combine=True  uses HCPMMP1_combined (22 parcels / hemi = 44 total).
    """
```

Backend: lazily downloads HCP MMP1.0 via `mne.datasets.fetch_hcp_mmp_parcellation(subjects_dir, accept=True)` and reads with `mne.read_labels_from_annot("fsaverage", name, hemi="both", subjects_dir=subjects_dir)`. Strips `L_`/`R_` prefix and `_ROI` suffix. Drops labels that don't match the requested hemi. Clips vertex indices to `FSAVERAGE_SIZES[mesh]=10242` so labels are valid for fsaverage5 (the HCP annotation is for full-res fsaverage=163842). Adds hemi offset. Asserts total vertex count matches `expected_size=10242`.

```python
# utils.py:259-265
def get_hcp_vertex_labels(mesh="fsaverage5", combine=False) -> list[str]:
    """Returns a list of length 20484 with parcel name for each vertex (or '')."""
```

```python
# utils.py:268-284
def get_hcp_roi_indices(
    rois: str | list[str],
    hemi: Literal["left","right","both"] = "both",
    mesh: str = "fsaverage5",
) -> np.ndarray:
    """
    Given parcel names (or glob patterns "TE1*"/"*pole"), return a flat numpy
    int array of vertex indices into a (20484,) activation vector.
    Concatenates across all matching parcels and both hemispheres (if hemi="both").
    """
```

Wildcards: `"TE1*"` matches any parcel starting with `TE1`. `"*pole"` matches any parcel ending with `pole`. Otherwise exact match. Raises `ValueError("ROI X not found in HCP labels")` if no match.

```python
# utils.py:287-306
def summarize_by_roi(
    data: np.ndarray,        # shape (20484,), 1D only (asserts)
    hemi: Literal["left","right","both","both_separate"] = "both",
    mesh: str = "fsaverage5",
) -> np.ndarray:
    """
    For each HCP parcel, compute data[vertex_indices].mean() and stack.
    Returns (180,) or (360,) depending on hemi.
    """
```

```python
# utils.py:309-318
def get_topk_rois(
    data: np.ndarray,        # (20484,)
    hemi: ... = "both",
    mesh: str = "fsaverage5",
    k: int = 10,
) -> np.ndarray:
    """Return top-k parcel names by ROI mean."""
```

### Hemisphere handling subtleties
- `hemi="left"` and `hemi="right"` return parcels for ONE hemisphere with vertex indices already offset (right hemi gets +10242).
- `hemi="both"` calls itself recursively and merges `{name: concat(left[name], right[name])}`. Each parcel name therefore has one entry that spans both hemispheres.
- `hemi="both_separate"` (only in `summarize_by_roi`, not in `get_hcp_labels`) returns 360 means in order `[left_parcels..., right_parcels...]`.

## 10. `FmriTemplateSpace` enum and `TribeSurfaceProjector`

`utils_fmri.py:22-67`. Enum that maps template names to `(id, shape)` tuples.

Relevant entries for Monarch:
- `FSAVERAGE_5 = ('fsaverage5', (10242,))` - the one we want
- `FSAVERAGE_6 = ('fsaverage6', (40962,))` - higher-res variant (not in released model)
- `FSAVERAGE = ('fsaverage', (163842,))` - full-res
- `CIFTI_HCP_FS_LR_32K = ('cifti-hcp-fs_LR_32k', (59412,))`, `CIFTI_HCP_FS_LR_164K = ('cifti-hcp-fs_LR_164k', (170494,))` - not used

`TribeSurfaceProjector` (utils_fmri.py:129-248) subclasses `ns.extractors.neuro.SurfaceProjector`. It is the thing that takes a 4D volume (for training data) and projects to `fsaverage5` via `nilearn.surface.vol_to_surf`. At inference Monarch doesn't touch this - the model output is already on fsaverage5. It IS invoked by `neuro.projection` in the config schema but the release checkpoint never sees volumetric data at inference.

Notes on `apply`:
- Input 4D volume -> calls `vol_to_surf` for each hemisphere with `surf_mesh=pial_{hemi}`, `inner_mesh=white_{hemi}`, `radius=3`, `interpolation="linear"`, `kind="ball"` (from the defaults.py neuro.projection config). Stacks L+R -> (20484, T).
- Input 2D surface data (already `(N_vertices, T)`) -> downsamples by picking `n_vertices_resampled = FSAVERAGE_SIZES[self.mesh]` from each hemisphere. Will raise if asked to upsample.

## 11. Effective TR and timing math

- `data.neuro.frequency = 1` (Hz) in the released config -> `Data.TR = 1.0 s`.
- `data.duration_trs = 100` -> each segment window is 100 s long.
- For a 52.21 s video, exactly one window is built but only 53 of the 100 per-TR rows land on non-empty parts (the remaining 47 are after the video ends).
- For a 23.256 s text-derived audio, 24 of 100 TRs are kept.
- So rule of thumb: **T = round(duration_seconds) = number of 1-second bins that intersect the stimulus**.

---

## 12. Cheat sheet: every shape in one place

```
Input:
  events DataFrame:          pd.DataFrame rows with Audio/Video/Text/Word/Sentence events

DataLoader pass:
  loader batch (batch_size=8): SegmentData with
      batch.data["text"]   : (B, L_text_sel=3, D_text=3072, T_feat=200)
      batch.data["audio"]  : (B, L_audio_sel=2, D_audio=1024, T_feat=200)
      batch.data["video"]  : (B, L_video_sel=2, D_video=1408, T_feat=200)
      batch.data["subject_id"]: (B,) int64 (all zero in avg-subject mode)
      batch.segments       : list[Segment] of length B

FmriEncoderModel.forward:
  aggregate_features(batch) -> (B, 200, 1152)   # projector_each: L*D -> 384, then cat along feat
  transformer_forward       -> (B, 200, 1152)   # + time_pos_embed[:, :200] then encoder
  x.transpose(1,2)          -> (B, 1152, 200)
  low_rank_head             -> (B, 2048, 200)
  predictor(SubjectLayers)  -> (B, 20484, 200)
  pooler(AdaptiveAvgPool1d(100)) -> (B, 20484, 100)

predict post-processing:
  rearrange("b d t -> (b t) d") -> (B*100, 20484)
  [keep]                         -> (n_kept_in_batch, 20484)
  concat across batches          -> (T, 20484)         # T = total non-empty TRs across all windows

Monarch pool:
  mean(preds, axis=0)            -> (20484,)           # the 'item vector' Monarch ships
```
