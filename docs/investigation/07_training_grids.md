# 07 - Training Grids

`tribev2/grids/*`. These files define the experiment configurations that produced the released checkpoints. Monarch will never re-train, but the team needs to read these because `defaults.py` IS the config schema that `from_pretrained` loads.

---

## 1. `grids/__init__.py`

Single-line empty file (well, a copyright header). Nothing re-exported.

## 2. `grids/defaults.py` - the canonical training config

**This is the most important file in the `grids/` directory.** The released `facebook/tribev2/config.yaml` is almost certainly a serialised version of this dict (with environment-resolved paths).

### Top of file (lines 1-25)
```python
PROJECT_NAME = "tribe_release"

SLURM_PARTITION = os.getenv("SLURM_PARTITION", "")
SLURM_CONSTRAINT = os.getenv("SLURM_CONSTRAINT", "")
WANDB_ENTITY = os.getenv("WANDB_ENTITY", "")
DATADIR = os.getenv("DATAPATH")
BASEDIR = os.getenv("SAVEPATH")
CACHEDIR = os.path.join(BASEDIR, "cache", PROJECT_NAME)
SAVEDIR = os.path.join(BASEDIR, "results", PROJECT_NAME)
N_CPUS = 20
CACHE_N_LAYERS = 20

for path in [CACHEDIR, SAVEDIR, DATADIR]:
    Path(path).mkdir(parents=True, exist_ok=True)
```

**Hard requirement**: importing this module at runtime requires `SAVEPATH` and `DATAPATH` env vars to be set. `os.path.join(None, ...)` would crash at import. This blocks any "from tribev2.grids import defaults" without env setup.

### Feature extractor configs (lines 26-112)

```python
text_feature = {
    "name": "HuggingFaceText",
    "event_types": "Word",
    "model_name": "meta-llama/Llama-3.2-3B",
    "aggregation": "sum",
    "frequency": 2,                              # 2 Hz feature rate
    "contextualized": True,                      # use AddContextToWords context window
    "layers": [0, 0.2, 0.4, 0.6, 0.8, 1.0],      # extract 6 relative-depth layers
    "batch_size": 4,
    "cache_n_layers": 20,                        # cache all 20 layers for potential swap
}

image_feature = {
    "name": "HuggingFaceVideo",                  # outer wrapper
    "frequency": 2,
    "event_types": "Video",
    "aggregation": "sum",
    "image": {                                    # nested image-model descriptor
        "name": "HuggingFaceImage",
        "model_name": "facebook/dinov2-large",
        "layers": 2/3,                           # single-layer scalar
        "infra": {"keep_in_ram": False},
        "batch_size": 4,
        "cache_n_layers": 20,
    },
}

video_feature = image_feature | {
    "clip_duration": 4,                          # 4 second video clip window
    "image": {
        "name": "HuggingFaceImage",
        "model_name": "facebook/vjepa2-vitg-fpc64-256",   # V-JEPA 2 ViT-g
        "infra": {"keep_in_ram": False},
        "layers": [0.75, 1.0],                    # 2 layers
        "cache_n_layers": 20,
    },
}

audio_feature = {
    "name": "Wav2VecBert",                        # neuralset class name
    "frequency": 2,
    "layers": [0.75, 1.0],
    "event_types": "Audio",
    "aggregation": "sum",
    "cache_n_layers": 20,
}

neuro_extractor = {
    "name": "FmriExtractor",
    "allow_missing": True,
    "offset": 5,                                  # 5-second HRF offset
    "frequency": 1,                               # 1 Hz = 1s TR
    "projection": {
        "name": "SurfaceProjector",
        "mesh": "fsaverage5",
        "kind": "ball",
        "radius": 3,
    },
}

for extractor in [text_feature, image_feature, video_feature, audio_feature, neuro_extractor]:
    extractor["infra"] = {
        "cluster": "slurm",
        "cpus_per_task": 10,
        "folder": CACHEDIR,
        "keep_in_ram": True,
        "mode": "cached",
        "min_samples_per_job": 1,
        "max_jobs": 256,
        "timeout_min": 60 * 12,
        "slurm_partition": SLURM_PARTITION,
    }
    extractor["infra"]["version"] = "release"
    if extractor["name"] == "FmriExtractor":
        extractor["infra"]["max_jobs"] = 1024
    else:
        extractor["infra"]["gpus_per_node"] = 1
        extractor["infra"]["slurm_constraint"] = SLURM_CONSTRAINT
    if extractor["name"] == "HuggingFaceVideo":
        extractor["infra"]["min_samples_per_job"] = 1
        extractor["infra"]["max_jobs"] = 1024
        extractor["infra"]["timeout_min"] = 60 * 24
    if extractor["name"] == "HuggingFaceText":
        extractor["infra"]["min_samples_per_job"] = 32
    extractor["allow_missing"] = True
    extractor["=replace="] = True
```

**Key takeaways**:
1. **Feature frequency is 2 Hz** for text/audio/video (every 0.5 s produce one feature frame), while the neuro target is 1 Hz. The sliding window inside neuralset handles the alignment.
2. **HRF offset is 5 seconds** (`neuro.offset=5`). The BOLD signal at time T is targeted against features from time T-5. This is a standard canonical HRF peak approximation.
3. **Projection**: `SurfaceProjector(mesh="fsaverage5", kind="ball", radius=3)`. `kind="ball"` means sample voxels within a 3 mm ball around each surface vertex, then average. `radius=3` is the ball radius.
4. **`cache_n_layers=20` for all extractors** - training caches up to 20 hidden-state layers per extractor but only the sub-set in `layers` gets used. Allows re-runs to swap `layers_to_use` without re-extracting.
5. **`aggregation="sum"` on neuro_extractor** - wait, the top of the loop mutates every extractor. Actually `aggregation` is only set on the feature extractors (text/audio/video), not on neuro. The `set_study_in_average_subject_mode` code path sets `neuro.aggregation = "mean"` at inference time to average subjects.
6. **`=replace=` is an exca marker** that tells the config merger to replace the entire sub-dict rather than deep-merging. It's not a value, it's a merge directive.
7. **All `infra` is stripped at inference time** by `TribeModel.from_pretrained` - the `neuro.infra` and `image_feature.infra` are popped, and the text/audio/video feature `infra.folder` is rewritten to the user's `cache_folder`.

### The `default_config` top-level dict (lines 114-258)

```python
default_config = {
    "infra": {
        "cluster": "slurm",
        "slurm_partition": SLURM_PARTITION,
        "folder": SAVEDIR,
        "gpus_per_node": 1,
        "cpus_per_task": N_CPUS,
        "mem_gb": 128,
        "timeout_min": 60 * 24 * 3,
        "mode": "retry",
        "slurm_constraint": SLURM_CONSTRAINT,
        "workdir": {
            "copied": ["neuralset", "neuraltrain", "tribev2"],
            "includes": ["*.py", "*.txt"],
        },
    },
    "data": {
        "frequency": 2,                                        # overrides feature extractors' freq
        "duration_trs": 100,                                   # 100-TR segment window
        "overlap_trs_train": 0,
        "overlap_trs_val": 0,
        "shuffle_val": True,
        "num_workers": 20,
        "layers_to_use": [0.5, 0.75, 1.0],                     # 3 sub-selected layers
        "layer_aggregation": "group_mean",
        "study": {
            "names": [
                "Algonauts2025Bold",
                "Wen2017",
                "Lahner2024Bold",
                "Lebel2023Bold",
            ],
            "path": DATADIR,
            "query": None,
            "infra_timelines": {...},
            "transforms": {
                "extractaudio":    {"name": "ExtractAudioFromVideo"},
                "extractwords":    {"name": "ExtractWordsFromAudio"},
                "addtext":         {"name": "AddText"},
                "addsentence":     {"name": "AddSentenceToWords", "max_unmatched_ratio": 0.05},
                "addcontext":      {"name": "AddContextToWords",
                                    "sentence_only": False,
                                    "max_context_len": 1024,
                                    "split_field": ""},
                "removemissing":   {"name": "RemoveMissing"},
                "chunksounds":     {"name": "ChunkEvents",
                                    "event_type_to_chunk": "Audio",
                                    "max_duration": 60, "min_duration": 30},
                "chunkvideos":     {"name": "ChunkEvents",
                                    "event_type_to_chunk": "Video",
                                    "max_duration": 60, "min_duration": 30,
                                    "infra": {"backend": "Cached", "folder": CACHEDIR}},
                "query":           {"name": "QueryEvents", "query": None},
                "split":           {"name": "SplitEvents", "val_ratio": 0.1},
            },
        },
        "neuro": neuro_extractor,
        "features_to_use": ["text", "audio", "video"],
        "text_feature":   text_feature,
        "video_feature":  video_feature,
        "audio_feature":  audio_feature,
        "image_feature":  image_feature,                        # configured but NOT in features_to_use
        "batch_size": 8,
    },
    "wandb_config": {
        "log_model": False,
        "entity": WANDB_ENTITY,
        "project": "tribe_release",
        "group": "default",
    },
    "brain_model_config": {
        "name": "FmriEncoder",
        "low_rank_head": 2048,
        "hidden": 1152,
        "extractor_aggregation": "cat",
        "layer_aggregation": "cat",
        "combiner": None,
        "encoder": {"depth": 8},
        "subject_layers": {"subject_dropout": 0.1},
        "subject_embedding": False,
        "modality_dropout": 0.3,
    },
    "metrics": [
        {"log_name": "pearson",        "name": "OnlinePearsonCorr", "dim": 0},
        {"log_name": "subj_pearson",   "name": "GroupedMetric",
         "metric_name": "OnlinePearsonCorr", "kwargs": {"dim": 0}},
        {"log_name": "retrieval_top1", "name": "TopkAcc", "topk": 1},
    ],
    "loss": {"name": "MSELoss", "kwargs": {"reduction": "none"}},
    "optim": {
        "name": "LightningOptimizer",
        "optimizer": {"name": "Adam", "lr": 1e-4, "kwargs": {"weight_decay": 0.0}},
        "scheduler": {"name": "OneCycleLR", "kwargs": {"max_lr": 1e-4, "pct_start": 0.1}},
    },
    "n_epochs": 15,
    "limit_train_batches": None,
    "patience": None,
    "enable_progress_bar": True,
    "log_every_n_steps": 5,
    "fast_dev_run": False,
    "seed": 33,
}
```

**Important confirmations for Monarch**:
- `features_to_use = ["text", "audio", "video"]`. `image` is configured but not in the list - so DINOv2-large is **loaded into the experiment but the projector for "image" is not built and its output is not fed to the transformer**. Confirmed by reading `FmriEncoderModel.__init__` which iterates over `feature_dims` keys (which comes from the `model_build_args` in the checkpoint), and `feature_dims` is driven by `features_to_use` at training time.
- The pipeline of transforms above is the training-time pipeline. Inference uses a stripped-down version (`get_audio_and_text_events` in demo_utils.py).
- `duration_trs = 100` is the segment window. Confirmed at inference: `Predicted 53 / 100 segments` in the notebook.
- `modality_dropout = 0.3` is the training-only dropout that makes the model robust to missing modalities at inference.
- `encoder.depth = 8` is the only transformer parameter set explicitly. Everything else (heads, ff_mult, attn_dropout defaults, etc.) is inherited from `neuraltrain.models.transformer.TransformerEncoder` defaults (which themselves are x_transformers defaults).

### `__main__` block (lines 261-272)

```python
if __name__ == "__main__":
    from ..main import TribeExperiment
    exp = TribeExperiment(**default_config)
    exp.infra.clear_job()
    out = exp.run()
    print(out)
```

Running `python -m tribev2.grids.defaults` directly would submit a Slurm training job with the exact default config. Monarch will never do this.

## 3. `grids/run_cortical.py` - cortical grid search

```python
from exca import ConfDict
from neuraltrain.utils import run_grid
from ..main import TribeExperiment
from .defaults import default_config

GRID_NAME = "cortical"

update = {"wandb_config.group": GRID_NAME}

grid = {
    "data.study.names": [
        "Algonauts2025Bold",
        "Lahner2024Bold",
        "Lebel2023Bold",
        "Wen2017",
        ["Algonauts2025Bold", "Lahner2024Bold", "Lebel2023Bold", "Wen2017"],
    ],
}

if __name__ == "__main__":
    updated_config = ConfDict(default_config)
    updated_config.update(update)
    out = run_grid(
        TribeExperiment,
        GRID_NAME,
        updated_config,
        grid,
        job_name_keys=["wandb_config.name", "infra.job_name"],
        combinatorial=True,
        overwrite=False,
        dry_run=False,
        infra_mode="force",
    )
```

**5 runs total**:
1. `Algonauts2025Bold` alone
2. `Lahner2024Bold` alone
3. `Lebel2023Bold` alone
4. `Wen2017` alone
5. All four combined -> this is the **released checkpoint**

The `combinatorial=True` flag means it takes the Cartesian product of all grid entries. Since only `data.study.names` is gridded here, it's just 5 runs.

## 4. `grids/run_subcortical.py` - subcortical grid search

Same structure as `run_cortical.py` but with a config override that swaps the projection from `SurfaceProjector(mesh="fsaverage5")` to:

```python
"data.neuro": {
    "projection": {
        "name": "MaskProjector",
        "mask": "subcortical",
        "=replace=": True,
    },
    "fwhm": 6.0,
}
```

`MaskProjector` is a neuralset class (not in this repo). `mask="subcortical"` is presumably a string key that resolves to the Harvard-Oxford subcortical mask. `fwhm=6.0` is 6 mm Gaussian smoothing. `=replace=` tells exca to replace the entire `projection` sub-dict.

**No subcortical checkpoint is published on HuggingFace**. The `facebook/tribev2` HF repo only has `best.ckpt` for the cortical model. If Monarch wants subcortical predictions, it must train one itself. This requires:
- A GPU cluster (the grid is designed for Slurm).
- The `neuralset`/`neuraltrain` packages (unknown availability).
- ~450 hours of fMRI data (see `06_studies.md`).
- Multi-day training on multiple GPUs.

**Verdict**: subcortical is out of reach for the Monarch MVP.

## 5. `grids/test_run.py` - local CI test entry point

```python
import os
from exca import ConfDict
from ..main import TribeExperiment
from .defaults import default_config

update = {
    "data.num_workers": 0,
    "infra.cluster": None,
    "infra.workdir": None,
    "wandb_config": None,
    "save_checkpoints": False,
    "n_epochs": 3,
    "infra.gpus_per_node": 1,
    "infra.mode": "force",
    "data.study.names": "Algonauts2025Bold",
    "data.study.transforms.query.query": "subject_timeline_index<3",
}

updated_config = ConfDict(default_config)
updated_config.update(update)

def test_run(config):
    task = TribeExperiment(**config)
    task.infra.clear_job()
    task.run()

if __name__ == "__main__":
    folder = os.path.join(updated_config["infra"]["folder"], "test")
    updated_config["infra"]["folder"] = folder
    if os.path.exists(folder):
        import shutil
        shutil.rmtree(folder)
    test_run(updated_config)
```

This is the local "does everything import correctly" smoke test. Runs 3 epochs on a narrow slice of Algonauts (first 3 timelines per subject), single GPU, no wandb, no checkpoint saving, no slurm. Monarch's integration test should be a similar 5-minute smoke run that just asserts shapes.

**BUT** this still requires:
- `DATAPATH` and `SAVEPATH` env vars.
- The actual Algonauts dataset on disk (multi-GB datalad clone).
- A GPU (3 epochs even on 3 timelines is probably too slow on CPU).
- All the extractor weights (LLaMA 3.2-3B, Wav2Vec-BERT 2.0, V-JEPA 2 ViT-g) that get loaded sequentially and each take a few GB of VRAM.

**So `test_run.py` is not usable as a Monarch smoke test.** It tests training. Monarch needs an inference-only smoke test - load the released checkpoint and run predict on a fixed fixture.

## 6. Global observations for the Monarch team

1. **`defaults.py` is read-through documentation for the `config.yaml` in the HF checkpoint.** Monarch can treat it as the schema reference when inspecting the downloaded YAML.
2. **`run_cortical.py` is the training command for the released checkpoint.** If Monarch ever wants to re-train (to remove the CC-BY-NC-4.0 license restriction by training on their own data), this is the recipe.
3. **`run_subcortical.py` exists but produces no published weights.** Subcortical ROI requests in the Monarch spec are architecturally unreachable.
4. **None of these files are needed at Monarch inference time.** The only tribev2 import at inference is `from tribev2.demo_utils import TribeModel`, which transitively loads `main.py`, `model.py`, `pl_module.py`, `eventstransforms.py`, `studies/*`, `utils.py`, `utils_fmri.py` via the `from .studies import *` and `from .model import *` wildcards in `main.py:39-47`. The `grids/` directory is NOT pulled in.
5. The **feature extractor HF model ids are pinned right here** (`meta-llama/Llama-3.2-3B`, `facebook/dinov2-large`, `facebook/vjepa2-vitg-fpc64-256`). The `Wav2VecBert` class name resolves to `facebook/w2v-bert-2.0` inside neuralset (confirm once you have neuralset source).
