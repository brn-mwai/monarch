# 02 - Config Analysis

**Where the config lives at runtime**: `facebook/tribev2` on HuggingFace, pulled via `hf_hub_download(repo_id, "config.yaml")` (`demo_utils.py:202`) into `~/.cache/huggingface/hub/models--facebook--tribev2/snapshots/<hash>/config.yaml`. Confirmed by the notebook's own log line: `Loading model from /private/home/sdascoli/.cache/huggingface/hub/models--facebook--tribev2/snapshots/d09bb3a0c156fab565cd1e513bc087692dacbd43/best.ckpt`.

**Is the file cached on THIS machine?** No. I searched `C:/Users/Windows/.cache/huggingface/**`, `C:/Users/Windows/Downloads/tribev2/cache/**`, and `C:/Users/Windows/Downloads/monarch-backend/cache/**`. None produced a `config.yaml`. The Monarch dev box has never downloaded the model (makes sense - no GPU, broken onnxruntime, broken tribev2 imports).

**Therefore** everything below is re-derived from the training `default_config` dict in `tribev2/grids/defaults.py` and from the loading code in `tribev2/demo_utils.py::from_pretrained`. The released `config.yaml` on HF should be numerically identical to this dict (that's what `TribeExperiment.setup_run` in `main.py:612-621` dumps into `infra.folder/config.yaml` at training time, via `yaml.dump(self.model_dump())`).

---

## 1. Config loading flow (demo_utils.py:190-225, line by line)

```python
# demo_utils.py:190
if cache_folder is not None:
    Path(cache_folder).mkdir(parents=True, exist_ok=True)

# demo_utils.py:192-193
if device == "auto":
    device = "cuda" if torch.cuda.is_available() else "cpu"

# demo_utils.py:194-203
checkpoint_dir = Path(checkpoint_dir)
if checkpoint_dir.exists():
    config_path = checkpoint_dir / "config.yaml"
    ckpt_path = checkpoint_dir / checkpoint_name
else:
    from huggingface_hub import hf_hub_download
    repo_id = str(checkpoint_dir)
    config_path = hf_hub_download(repo_id, "config.yaml")
    ckpt_path = hf_hub_download(repo_id, checkpoint_name)

# demo_utils.py:204-205  --- parsed with UnsafeLoader because the YAML
# contains pickled Python class references emitted by exca.ConfDict.
with open(config_path, "r") as f:
    config = ConfDict(yaml.load(f, Loader=yaml.UnsafeLoader))

# demo_utils.py:206-208  --- redirect extractor caches to user-chosen folder
for modality in ["text", "audio", "video"]:
    config[f"data.{modality}_feature.infra.folder"] = cache_folder
    config[f"data.{modality}_feature.infra.cluster"] = cluster

# demo_utils.py:210-216  --- strip training-time infra
for param in [
    "infra.workdir",
    "data.study.infra_timelines",
    "data.neuro.infra",
    "data.image_feature.infra",
]:
    config.pop(param)

# demo_utils.py:217-222
config["data.study.path"] = "."                               # prevent dataset loader from hunting for DATAPATH
config["average_subjects"] = True                             # use the mean-subject head
config["checkpoint_path"] = str(config["infra.folder"]) + f"/{checkpoint_name}"
config["cache_folder"] = str(cache_folder) if cache_folder is not None else "./cache"

# demo_utils.py:223-224  --- optional user overrides
if config_update is not None:
    config.update(config_update)

# demo_utils.py:225  --- finally instantiate
xp = cls(**config)
```

Important: the config parse uses `yaml.UnsafeLoader`, which means the YAML file contains Python class references produced by `exca.ConfDict`. It is **not** safe-loadable. Monarch should not try to pre-parse it with `yaml.safe_load` - the SDK assumes `UnsafeLoader`.

## 2. Fields the loader reads (enumerated from demo_utils and main.py/model.py)

Listed in the order the code touches them. Inferred types come from the pydantic `Data` and `TribeExperiment` classes in `main.py` and `FmriEncoder` in `model.py`.

### 2a. `infra.*` (general experiment infra, mostly stripped at load time)

| Field | Type | Inference-time behaviour |
|---|---|---|
| `infra.folder` | str | Used to construct `checkpoint_path`. Must exist at load time (line 219). |
| `infra.workdir` | dict | **Popped** (line 211). |
| `infra.cluster` | str | TaskInfra. Monarch sets to `None` or override. |
| `infra.gpus_per_node` | int | Sets `tasks_per_node`, affects strategy. |

### 2b. `data.*` - the `Data` pydantic class

Defined in `main.py:82-117`.

| Field | Type | Default in `grids/defaults.py` | Role at inference |
|---|---|---|---|
| `data.study` | `MultiStudyLoader` | Algonauts2025Bold + Wen2017 + Lahner2024Bold + Lebel2023Bold | Ignored at inference because `average_subjects=True` switches to mean-subject mode and a single dummy timeline. Still instantiated. |
| `data.study.path` | str | `DATADIR` env var | **Rewritten to `"."` by from_pretrained** so it doesn't attempt to read training datasets. |
| `data.study.names` | str or list | 4 studies | Used only to build subject layer shape (disabled by average_subjects). |
| `data.neuro` | `ns.extractors.BaseExtractor` | `FmriExtractor` with `frequency=1`, `offset=5`, `projection={name: SurfaceProjector, mesh: fsaverage5, kind: ball, radius: 3}` | Not queried at inference (there's no Fmri event in the user's events DF). BUT `self.data.TR = 1 / self.neuro.frequency = 1.0 s` is the sliding window. |
| `data.text_feature` | `ns.extractors.BaseExtractor` | `HuggingFaceText` with `model_name=meta-llama/Llama-3.2-3B`, `event_types=Word`, `aggregation=sum`, `frequency=2`, `contextualized=True`, `layers=[0, 0.2, 0.4, 0.6, 0.8, 1.0]`, `batch_size=4`, `cache_n_layers=20` | **Reloaded** with LLaMA 3.2-3B HF weights. Extracts contextualised word-level embeddings from the context text column. |
| `data.audio_feature` | `ns.extractors.BaseExtractor` | `Wav2VecBert` (facebook/w2v-bert-2.0) with `frequency=2`, `layers=[0.75, 1.0]`, `event_types=Audio`, `aggregation=sum`, `cache_n_layers=20` | Loaded at inference. |
| `data.video_feature` | `ns.extractors.BaseExtractor` | `HuggingFaceVideo` with `frequency=2`, `event_types=Video`, `aggregation=sum`, `clip_duration=4`, nested `image` sub-extractor pointing at `facebook/vjepa2-vitg-fpc64-256`, `layers=[0.75, 1.0]` | Loaded at inference. **NB**: the outer extractor is `HuggingFaceVideo` but the actual model weights are V-JEPA 2 ViT-g via the nested `image` field. |
| `data.image_feature` | `ns.extractors.BaseExtractor` | `HuggingFaceVideo` wrapping `facebook/dinov2-large` at `layers=2/3`, `batch_size=4`, `frequency=2` | **Popped (`data.image_feature.infra`) at load time. The image branch is configured but `features_to_use` does not include `"image"`, so at inference DINOv2 is NOT used.** |
| `data.subject_id` | `ns.extractors.LabelEncoder` | default | Used for the SubjectLayers head (average-subject after from_pretrained rewrite). |
| `data.frequency` | float \| None | `2` | Target feature-extractor frequency. Applied to each extractor's `frequency` attr in `Data.model_post_init`. |
| `data.features_to_use` | list[Literal...] | **`["text", "audio", "video"]`** | Which modalities the brain encoder consumes. Drives `feature_dims` dict on first batch. |
| `data.features_to_mask` | list[Literal...] | `[]` | Nothing masked at inference. |
| `data.n_layers_to_use` | int \| None | `None` | Exclusive with `layers_to_use`. |
| `data.layers_to_use` | list[float] \| None | **`[0.5, 0.75, 1.0]`** | Sub-selects a 3-tuple of relative-depth layers from each extractor at inference. |
| `data.layer_aggregation` | `"group_mean"` or `"mean"` | **`"group_mean"`** | Per-extractor aggregation mode. |
| `data.duration_trs` | int | **`100`** | Segment window length. The sliding loader builds 100-TR windows; `FmriEncoderModel` also sets `n_output_timesteps=100`. |
| `data.overlap_trs_train` | int | `0` | Training only. |
| `data.overlap_trs_val` | int \| None | `0` | Val only. |
| `data.batch_size` | int | `8` (defaults.py) | Sliding-window batch. |
| `data.num_workers` | int \| None | `20` in defaults, `0` in test_run | Torch DataLoader workers. |
| `data.shuffle_train` / `data.shuffle_val` | bool | | Training only. |
| `data.stride_drop_incomplete` | bool | `False` | Inference wants `False`. |
| `data.split_segments_by_time` | bool | `False` | Training only. |

### 2c. `brain_model_config.*` - the `FmriEncoder` config

Defined in `model.py:49-86`.

| Field | Type | Default in `grids/defaults.py` | Purpose |
|---|---|---|---|
| `name` | str | `"FmriEncoder"` | Class key for BaseModelConfig registry. |
| `hidden` | int | **`1152`** | Transformer hidden size. **Differs from the Monarch spec's claimed 384.** With `extractor_aggregation=cat` and 3 modalities, each modality projects to `1152/3 = 384`, which is likely the origin of the 384 number in the spec. |
| `low_rank_head` | int \| None | **`2048`** | Linear(1152 -> 2048) applied before the per-vertex head. **Not in the Monarch spec at all.** |
| `extractor_aggregation` | `"stack"`/`"sum"`/`"cat"` | **`"cat"`** | How to combine the per-modality projections. |
| `layer_aggregation` | `"mean"`/`"cat"` | **`"cat"`** | How to combine multiple layer embeddings per modality. With `layers_to_use=[0.5,0.75,1.0]` this multiplies input_dim by 3. |
| `combiner` | `Mlp \| None` | **`None`** | When None, `self.combiner = nn.Identity()` and the code asserts `hidden % n_modalities == 0`. |
| `encoder` | `TransformerEncoder` | `{"depth": 8}` (all other attention/head fields inherited from `neuraltrain.models.transformer.TransformerEncoder` defaults) | **8-layer x_transformers encoder**. Head count is not explicit in defaults.py - it falls through to whatever `neuraltrain.models.transformer.TransformerEncoder` sets. |
| `projector` | `Mlp` | `Mlp(norm_layer="layer", activation_layer="gelu")` | Per-modality input MLP. Built once per modality in `FmriEncoderModel.__init__`. |
| `subject_layers` | `SubjectLayers` | `{"subject_dropout": 0.1}`, plus `average_subjects=True` and `n_subjects=0` forced by from_pretrained | Output head. |
| `subject_embedding` | bool | `False` | |
| `time_pos_embedding` | bool | `True` | Learned positional embedding `nn.Parameter(1, max_seq_len, hidden)`. |
| `max_seq_len` | int | `1024` | Positional embedding size. |
| `dropout` | float | `0.0` | |
| `linear_baseline` | bool | `False` | When True, skips the transformer entirely. |
| `modality_dropout` | float | `0.3` | **Training-only** (gated on `self.training`). Eval = deterministic. |
| `temporal_dropout` | float | `0.0` | Training-only. |
| `temporal_smoothing` | `TemporalSmoothing \| None` | `None` | Optional per-channel gaussian conv. Disabled in released config. |

Internal fields computed in `FmriEncoderModel.__init__`:
- `self.pooler = nn.AdaptiveAvgPool1d(n_output_timesteps=100)` - pools the per-sample 100-TR window into exactly 100 output TRs (so inference stays 1 TR per 1 s).
- `self.low_rank_head = nn.Linear(1152, 2048, bias=False)` if `low_rank_head is not None`.
- `self.predictor = SubjectLayers.build(in_channels=2048, out_channels=20484)` via `SubjectLayers` in `neuraltrain.models.common`. **This is where the 20484-vertex-per-brain output width is produced.**
- `self.time_pos_embed = nn.Parameter(randn(1, 1024, 1152))`.
- `self.encoder = TransformerEncoder(dim=1152, depth=8, ...)` via x_transformers.

### 2d. Other top-level `TribeExperiment` fields (`main.py:278-325`)

| Field | Default | Role |
|---|---|---|
| `seed` | 33 | Ignored at inference. |
| `loss` | `MSELoss(reduction="none")` | Training only. |
| `optim` | `LightningOptimizer{Adam, OneCycleLR, lr=1e-4}` | Training only. |
| `metrics` | `[OnlinePearsonCorr, GroupedMetric(OnlinePearsonCorr), TopkAcc{topk=1}]` | Training only. |
| `wandb_config` | `WandbLoggerConfig` | Training only. |
| `n_epochs` | 15 | Training only. |
| `monitor` | `"val/pearson"` | Training only. |
| `average_subjects` | **forced True at load time** | Activates the mean-subject head. |
| `checkpoint_path` | rewritten at load time | Points at `best.ckpt`. |
| `load_checkpoint` | True (default) | |
| `test_only` | False | |
| `resize_subject_layer` | False | Skips the SVD-based re-init in `_init_module`. |
| `freeze_backbone` | False | |
| `accumulate_grad_batches` | 1 | Halves `data.batch_size` at >1 (training). |
| `patience` | None | |

## 3. Inferred shapes from config to output

### 3a. Text modality
`HuggingFaceText` at LLaMA 3.2-3B hidden=3072. `layers=[0, 0.2, 0.4, 0.6, 0.8, 1.0]` is the **extraction** list. `layers_to_use=[0.5, 0.75, 1.0]` is the **sub-selection** applied by `Data.model_post_init`. With `layer_aggregation="cat"`, each timestep is `3 * 3072 = 9216`. That's the `feature_dim * num_layers` inside `FmriEncoderModel.__init__`. Output of the per-modality projector: `hidden // 3 = 384`. (This is the 384 the Monarch spec thinks is the "shared space" width.)

### 3b. Audio modality
`Wav2VecBert` at w2v-BERT 2.0 hidden=1024. `layers=[0.75, 1.0]` extracted, `layers_to_use=[0.5, 0.75, 1.0]` sub-selection - **but w2v-BERT only has two layers in the default extraction list**, so the sub-selection is clamped by the available layers (check against `neuralset` source for exact behaviour; conservatively assume 2 layers at inference). `num_layers * feature_dim = 2 * 1024 = 2048`. Projector output: 384.

### 3c. Video modality
V-JEPA 2 ViT-g (`facebook/vjepa2-vitg-fpc64-256`) hidden=1408. `layers=[0.75, 1.0]`, 2 layers * 1408 = 2816. Projector output: 384. `clip_duration=4` means each feature covers 4s of video.

### 3d. Concatenation and fusion
`extractor_aggregation="cat"` -> `[text(384), audio(384), video(384)]` concatenated = 1152 hidden. `combiner=None` -> `nn.Identity()`. `+ time_pos_embed[:, :T]` (learned, max 1024 positions). 8-layer transformer. `low_rank_head = Linear(1152, 2048)`. `SubjectLayers.build(in_channels=2048, out_channels=20484)` projects to vertices. `AdaptiveAvgPool1d(100)` on the time axis.

### 3e. Output
**`(B, 20484, 100)`** inside the model. `predict()` then rearranges to `(B*100, 20484)`, drops empty segments, and concatenates batches -> `(T, 20484)` where `T` is the number of **non-empty** TRs (the notebook shows 53 for a 52-second video and 24 for a 23-second text, so roughly 1 TR per second with empty-TR dropping).

## 4. Feature extractor identities (confirmed)

| Modality | HF repo id | Source |
|---|---|---|
| Text | `meta-llama/Llama-3.2-3B` | `grids/defaults.py:29` |
| Audio | `facebook/w2v-bert-2.0` | Class name `Wav2VecBert` in `grids/defaults.py:62`; the concrete HF id comes from the neuralset extractor's class default. |
| Video | `facebook/vjepa2-vitg-fpc64-256` | `grids/defaults.py:55` |
| Image (disabled) | `facebook/dinov2-large` | `grids/defaults.py:44` |

The `Wav2VecBert` extractor is a neuralset class name, not a HF id. `facebook/w2v-bert-2.0` is what the paper and README claim, and the Monarch backend already uses that identity. Confirm once you can actually load the config.yaml.

## 5. Data pipeline transforms (demo_utils.py:66-95)

Applied by `get_audio_and_text_events` for audio or video input:

1. `ExtractAudioFromVideo()` - from `neuralset.events.transforms`. Strips the audio track of a video event into an Audio event with the same timeline.
2. `ChunkEvents(event_type_to_chunk="Audio", max_duration=60, min_duration=30)` - splits audio into 30-60s chunks.
3. `ChunkEvents(event_type_to_chunk="Video", max_duration=60, min_duration=30)` - same for video.
4. `ExtractWordsFromAudio()` (from `tribev2.eventstransforms`) - runs `uvx whisperx <wav> --model large-v3 --align_model WAV2VEC2_ASR_LARGE_LV60K_960H --device <cuda|cpu> --compute_type float16 --batch_size 16 --output_format json` in a subprocess. Parses the JSON to extract `text`, `start`, `duration=end-start`, `sequence_id`, `sentence`. Also writes `<wav>.tsv` for cache.
5. `AddText()` - adds a full-clip Text event.
6. `AddSentenceToWords(max_unmatched_ratio=0.05)` - sentence boundary annotation.
7. `AddContextToWords(sentence_only=False, max_context_len=1024, split_field="")` - attaches a running context window (up to 1024 tokens) to each Word. This is what the LLaMA text extractor actually encodes.
8. `RemoveMissing()` - drops rows missing required fields.

For text input (`TextToEvents`):
1. `detect(text)` via `langdetect`.
2. `gTTS(text, lang=detected).save(audio.mp3)` - synthesizes MP3.
3. Feed an Audio event at `start=0` through `get_audio_and_text_events`.

## 6. Output format
Released checkpoint: **cortical only, fsaverage5, 10242 verts per hemisphere, 20484 total**. Left hemisphere is indices `[0..10241]`, right hemisphere is `[10242..20483]`. Confirmed by:
- `utils_fmri.py:50` - `FSAVERAGE_5 = ('fsaverage5', (10242,))`
- `utils.py:243-246` - `index_offset = expected_size if hemi == "right" else 0` for HCP ROI indices, so right-hemi indices are already offset.
- `monarch-meshes/metadata.json` (ground truth from exported mesh): `totalVertices: 20484`.
- Notebook: `Predictions shape: (53, 20484)` and `(24, 20484)`.

**Subcortical is NOT in the released checkpoint**. `grids/run_subcortical.py` exists but no `config.yaml`/`best.ckpt` for it on HuggingFace. The `plotting/subcortical.py` code can render predictions from a hypothetical subcortical model but has no weights to feed it.
