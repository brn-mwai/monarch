# 04 - Demo Notebook Cell-by-Cell

`tribev2/tribe_demo.ipynb`. The notebook has 17 cells total (markdown + code + outputs). Code cells are numbered here as C1..C7 for clarity; markdown cells are summarised as M1..M10.

**Key takeaway**: the whole notebook is effectively a 5-step demo: load -> fetch sample video -> predict -> render timesteps -> repeat with Shakespeare text. It produces only one shape of output (`(T, 20484)`) and uses only `plot_timesteps` for rendering. There is no `plot_surf_rgb`, no subcortical plotting, no ROI overlay, no `get_hcp_roi_indices` call.

---

## Cell breakdown

### M1. Title + intro
"TRIBE v2 Demo: Predicting Brain Responses to Naturalistic Stimuli". Describes the paper and announces the four steps of the notebook. No code.

### M2. Colab setup instructions
"1. Activate GPU. 2. Run command below. 3. Restart." Prompts the reader to install tribev2.

### C1. (cell id `f2cc3200`) Install command
```bash
!uv pip install "tribev2[plotting] @ git+https://github.com/facebookresearch/tribev2.git"
```
Shell command. Outputs not captured. Monarch doesn't need this - the backend dependency is pinned in its own pyproject.toml.

### M3. "Loading the model"
Explains that the first run downloads ~1 GB from HuggingFace. Mentions `PlotBrain(mesh="fsaverage5")`.

### C2. (cell id `0`) Load model + plotter
```python
from tribev2.demo_utils import TribeModel, download_file
from tribev2.plotting import PlotBrain
from pathlib import Path

CACHE_FOLDER = Path("./cache")
model = TribeModel.from_pretrained("facebook/tribev2", cache_folder=CACHE_FOLDER)
plotter = PlotBrain(mesh="fsaverage5")
```
**Arguments**: `checkpoint_dir="facebook/tribev2"`, `cache_folder=Path("./cache")`, other kwargs default (checkpoint_name="best.ckpt", cluster=None, device="auto", config_update=None).

**Outputs** (captured in the cell's output block):
- `TqdmWarning: IProgress not found...` (cosmetic).
- Two `LabelEncoder: event_types has not been set` warnings from neuralset (cosmetic).
- Two `Missing events will be encoded using the default all-zero value` warnings.
- **`INFO - Loading model from /private/home/sdascoli/.cache/huggingface/hub/models--facebook--tribev2/snapshots/d09bb3a0c156fab565cd1e513bc087692dacbd43/best.ckpt`** - this tells us the commit hash of the released checkpoint at the time of Sdascoli's run (d09bb3a...).
- Two `FutureWarning` about `torch.cuda.amp.autocast(args...)` from x_transformers. **Shows x_transformers is the transformer backend**, confirming grids/defaults.py.

No explicit return-shape print. The `plotter` is the default `PlotBrainPyvista` with `inflate="half"`, `bg_map="sulcal"`, `dpi=3000`, `bg_darkness=0`, `ambient=0.3`, `hemisphere_gap=0`.

### M4. "Predict brain responses to a video"
Enumerated pipeline: audio extract -> whisperx transcription -> DINOv2 + V-JEPA2 + Wav2Vec-BERT + LLaMA3.2 -> `fMRI at each time step (1 TR = 1 second)`. The **1 TR = 1 second** line is direct confirmation from the author that `Data.TR = 1.0 s`.

### C3. (cell id `3`) Build events DF for Sintel trailer
```python
video_path = CACHE_FOLDER / "sample_video.mp4"
url = "https://download.blender.org/durian/trailer/sintel_trailer-480p.mp4"
download_file(url, video_path)
df = model.get_events_dataframe(video_path=video_path)
display(df.head(8)[["type", "start", "duration", "filepath", "text", "context"]])
```

**Output (captured)**:
```
INFO - Downloaded https://download.blender.org/durian/trailer/sintel_trailer-480p.mp4 -> cache/sample_video.mp4
Extract audio from video events: 100%|██████████| 1/1 [00:00<00:00, 655.46it/s]
Extracting words from audio: 100%|██████████| 1/1 [00:00<00:00, 662.61it/s]
Add context to words: 100%|██████████| 30/30 [00:00<00:00, 63775.53it/s]
```
Only 30 words extracted from the trailer (sparse dialogue in the Sintel trailer). The DF `head(8)` shows columns `type, start, duration, filepath, text, context` with rows:

| idx | type | start | duration | filepath | text | context |
|---|---|---|---|---|---|---|
| 0 | Audio | 0.0 | 52.21 | cache/sample_video.wav | NaN | |
| 1 | Video | 0.0 | 52.21 | cache/sample_video.mp4 | NaN | |
| 2 | Sentence | 12.213 | 2.042 | NaN | "What brings you to the land of the gatekeepers?." | |
| 3 | Text | 12.213 | 31.47 | NaN | "What brings you to the land..." (truncated) | |
| 4 | Word | 12.213 | 0.120 | NaN | "What" | "What" |
| 5 | Word | 12.393 | 0.280 | NaN | "brings" | "What brings" |
| 6 | Word | 12.713 | 0.101 | NaN | "you" | "What brings you" |
| 7 | Word | 12.854 | 0.100 | NaN | "to" | "What brings you to" |

**This confirms**:
- `AddContextToWords` accumulates a running prefix (not a sentence-bounded window). The `context` column grows monotonically through the clip.
- `AddText` produces a single `Text` row spanning all dialogue.
- Sentences are tagged with a `?.` at the end (transcription artefact from whisperx).
- `filepath` is only populated for Audio/Video rows.

### M5. "Run the model"
Notes that LLaMA 3.2 is gated. States `preds` shape is `(n_timesteps, n_vertices)`, with "one prediction per second of stimulus".

### C4. (cell id `4`) Run predict() on video
```python
preds, segments = model.predict(events=df)
print(f"Predictions shape: {preds.shape}  (n_timesteps, n_vertices)")
```

**Output (captured)**:
```
[10:14:05 INFO] Preparing extractor: text
[10:14:05 INFO] Preparing extractor: audio
[10:14:05 INFO] Preparing extractor: video
[10:14:06 INFO] Preparing extractor: subject_id
[10:14:06 WARNING] LabelEncoder has only found one label: {'default'}. This was probably not intended.
[10:14:06 INFO] Building dataloader for split all
100%|██████████| 1/1 [00:00<00:00,  1.19it/s]
INFO - Predicted 53 / 100 segments (53.0% kept)

Predictions shape: (53, 20484)  (n_timesteps, n_vertices)
```

**This is the ONLY captured output in the whole repo that confirms the numerical shape.** 53 kept out of 100 for a 52.21 s video = one TR per second, empty TRs dropped (the 47 "empty" TRs are where the rolling window extended past the end of the clip).

The extractors are prepared in order: text -> audio -> video -> subject_id. The whole pipeline ran on 1 batch in 1 second because extractors cache to disk between calls (and for a 52 s video the transformer forward pass is trivial).

### M6. Markdown explaining visualisation parameters
"fire colormap", "norm_percentile=99 normalizes values within the 99th percentile". No code.

### C5. (cell id `5`) Render timesteps for video
```python
n_timesteps = 15
fig = plotter.plot_timesteps(
    preds[:n_timesteps],
    segments=segments[:n_timesteps],
    cmap="fire",
    norm_percentile=99,
    vmin=.5,
    alpha_cmap=(0, .2),
    show_stimuli=True,
)
```

**Arguments**:
- `neuro=preds[:15]` - shape `(15, 20484)`.
- `segments=segments[:15]` - first 15 segments matching those TRs.
- `cmap="fire"` - colorcet `fire` palette (imported via `get_cmap`'s fallback chain: matplotlib -> seaborn -> colorcet). Fire is a warm perceptually-uniform cmap (black -> dark red -> orange -> yellow -> white).
- `norm_percentile=99` - `robust_normalize(data, percentile=99, two_sided=True, clip=True)` - clips to [p1, p99], scales to [0,1], two-sided means lower bound is the p1, not the array min. **Most important for Monarch**.
- `vmin=0.5` - applied to the ScalarMappable AFTER normalisation. Effectively: start showing colour only for vertices whose normalised value is >= 0.5. Visually clips the bottom half of the range.
- `alpha_cmap=(0, 0.2)` - `get_alpha_cmap(cmap, threshold=0, scale=0.2)`: sets alpha=0 below threshold, ramps 0->1 linearly between threshold and threshold+scale, alpha=1 above. Here this means "fully transparent at value 0, fully opaque by value 0.2". In combination with `vmin=0.5` above, you get transparency across the low half and full opacity above the midpoint - the sulcal background shows through the low-activation regions.
- `show_stimuli=True` - adds audio waveform + transcript text (+ video frame) rows below the brain row.

**Output shape note**: `plot_timesteps` returns a matplotlib `Figure`. The notebook cell's output block is `"Outputs are too large to include. Use Bash with: cat <notebook_path> | jq '.cells[10].outputs'"`. The image is a PNG grid with one row per `neuro` entry (here just one row called `"Brain reponse"` - the typo is in base.py:256) plus stimuli rows. Per timestep, plot_timesteps calls `plot_surf(value[i], ...)` which produces one off-screen PyVista PNG per frame.

**Inside `plot_timesteps`** (base.py:235-365):
1. Wraps `neuro` in `{"Brain reponse": neuro}` if it's a plain ndarray.
2. Applies `robust_normalize(v, percentile=99)` for each key in `neuro` if `norm_percentile is not None`.
3. Builds a matplotlib mosaic with subplots per `(key, timestep)` pair, adding stimulus rows if `show_stimuli`.
4. Calls `plot_surf(value[i], axes=..., views=views[key], **kwargs)` for each timestep.
5. Optionally calls `plot_stimuli(segments, axes, ...)` to render the audio waveform and words below.
6. Returns the `Figure` object.

Critical: **`robust_normalize` is applied INSIDE `plot_timesteps`, not inside the individual `plot_surf` calls.** This means the per-timestep plots all share a common normalisation window (the p1..p99 across all 15 timesteps). If you render TRs one at a time by calling `plot_surf` directly, you get per-frame normalisation unless you pre-normalise yourself.

### M7. Markdown - "Predict brain responses to text (via text-to-speech)"
Explains gTTS + transcribe-back flow.

### C6. (cell id `12`) Build events DF for Shakespeare text
```python
text = """
To be or not to be, that is the question.
...
"""
text_path = CACHE_FOLDER / "shakespeare.txt"
text_path.write_text(text)
df = model.get_events_dataframe(text_path=text_path)
display(df.head(8)[...])
```

**Output (captured)**:
```
       type     start   duration  filepath  text  context
0     Audio  0.000000  23.256000  cache/tribev2.demo_utils.TextToEvents.get_events...
1  Sentence  0.090999   1.261002  NaN        "To be or not to be."
2     Text   0.091000  22.590000  NaN        "To be or not to be. That is the question. ..."
3     Word   0.091000   0.100000  NaN        "To"           "To"
4     Word   0.271000   0.200000  NaN        "be"           "To be"
5     Word   0.551000   0.060000  NaN        "or"           "To be or"
6     Word   0.691000   0.200000  NaN        "not"          "To be or not"
7     Word   0.931000   0.100000  NaN        "to"           "To be or not to"
```

**Confirms**: Text path goes through `TextToEvents.get_events()`, the synthesised audio lands in `cache/tribev2.demo_utils.TextToEvents.get_events_...` (exca creates a uid folder), and the same `get_audio_and_text_events` pipeline runs. **The resulting DF has no Video rows** - text-only input never creates a video event.

### C7. (cell id `c935b95f`) Run predict() on Shakespeare
```python
preds, segments = model.predict(events=df)
print(f"Predictions shape: {preds.shape}  (n_timesteps, n_vertices)")
```

**Output (captured)**:
```
[17:00:42 WARNING] Removing extractor video as there are no corresponding events
[17:00:42 INFO] Preparing extractor: text
[17:00:42 INFO] Preparing extractor: audio
[17:00:42 INFO] Preparing extractor: subject_id
[17:00:42 WARNING] LabelEncoder has only found one label: {'bar'}. This was probably not intended.
[17:00:43 INFO] Building dataloader for split all
100%|██████████| 1/1 [00:00<00:00,  1.16it/s]
INFO - Predicted 24 / 100 segments (24.0% kept)

Predictions shape: (24, 20484)  (n_timesteps, n_vertices)
```

**Critical confirmation**: the `Removing extractor video` warning shows that when no Video events are present, `Data.get_loaders` silently removes the video extractor. But the `FmriEncoderModel.aggregate_features` code still has `video` in `feature_dims` (because that's part of the loaded checkpoint's `model_build_args`), and the corresponding branch fills the video channels with **zero tensors**. So the prediction is "as if the subject saw a blank video".

The warning about `LabelEncoder has only found one label: {'bar'}` is strange - it's finding "bar" as the only subject label. Not important for inference (average-subject mode takes all labels to zero).

24 / 100 segments for 23.256 s audio = again 1 TR per second with empty drops.

### C8. (cell id `d2dcaa65`) Render timesteps for Shakespeare
```python
n_timesteps = 15
fig = plotter.plot_timesteps(
    preds[:n_timesteps],
    segments=segments[:n_timesteps],
    cmap="fire",
    norm_percentile=99,
    vmin=.5,
    alpha_cmap=(0, .2),
    show_stimuli=True,
)
```

Same call as C5. For audio-only input, `plot_stimuli` will render the audio waveform and the transcript word spans but no video frames (because `has_video(segment)=False`).

### M8. End of notebook
No further cells. No ROI overlay, no `plot_surf_rgb`, no subcortical, no `get_hcp_roi_indices`. The notebook is pure predict-and-render.

---

## Colormap / normalisation pipeline distilled

```
data: (20484,) float in whatever "BOLD-like" units TRIBE produces (see 05_plotting_system.md)
  |
  v
robust_normalize(data, percentile=99, two_sided=True, clip=True)
    lo = p1, hi = p99
    (data - lo) / (hi - lo), clipped to [0,1]
  |
  v
get_cmap("fire", alpha_cmap=(0, 0.2))
    base = colorcet.cm.fire           # 256-color warm ramp
    alpha_cmap wraps it in a ListedColormap where alpha=0 below value 0 and
    ramps to 1 by value 0.2
  |
  v
get_scalar_mappable(data, cmap, vmin=0.5, vmax=None)
    vmax = data.max() after normalisation (so effectively 1.0)
    vmin is hardcoded 0.5
    returns matplotlib.cm.ScalarMappable with a Normalize(0.5, 1.0) transform
  |
  v
sm.to_rgba(stat_map)     # (N_vertices, 4) per hemisphere
  |
  v
For each vertex: rgba[:, 3:4] * rgba[:, :3] + (1 - rgba[:, 3:4]) * bg_rgb
  where bg_rgb is derived from the sulcal depth map:
      bg_norm = (bg_map - min) / (max - min + 1e-8)
      bg_rgb = 1 - [bg_darkness + bg_norm * (1 - bg_darkness)] stacked x3
      (bg_darkness=0 -> sulci darker, gyri lighter; inverted gray)
```

So the final vertex colour is `alpha * warm_cmap(norm_val) + (1-alpha) * sulcal_gray`.

For Monarch's JS renderer to mirror this exactly, it needs:
1. A 256-stop ramp of `colorcet.cm.fire` (sample at N=256 points and embed as a lookup texture).
2. The `robust_normalize(percentile=99)` logic in JS (two calls to numpy-equivalent `percentile` with interpolation).
3. The `alpha_cmap(threshold=0, scale=0.2)` ramp (zero below 0, linear 0..1 from 0 to 0.2, one above 0.2).
4. A per-vertex `vmin=0.5` cutoff (linear from 0.5..1.0 mapped to 0..255 in the cmap LUT).
5. The sulcal background baked into the mesh (already in `monarch-meshes/*.json` as `sulcalDepth`).
6. The blend equation above.

See `05_plotting_system.md` for the exact matplotlib calls.

---

## Animation / time-axis behaviour

The notebook **does not animate**. It builds a static matplotlib figure with a grid of 15 subplots, each showing one TR. If Monarch wants to animate the `(T, 20484)` array through time, there's one reference implementation: `BasePlotBrain.plot_timesteps_mp4` (base.py:431-490), which calls `plot_surf` once per TR into a temporary figure, saves PNGs, and stitches them together with `ffmpeg -framerate 1 -vf minterpolate=fps=<interpolated_fps>`. **The ffmpeg `minterpolate` step is the "temporal smoothing" for the output video.** No in-model temporal interpolation - the encoder just produces 1 TR per 1 s.

## Dual-view / RGB-channel mode

Not in the notebook. To see it, open `plotting/cortical_pv.py:169-280` (`plot_surf_rgb`). It accepts a list of 2 or 3 signals, maps each to a colour channel, renders a single mesh where the vertex colour is the RGB mix. This is how TRIBE's paper shows "this vertex is mostly audio-driven" (green-dominant vertices mean the audio-only model has high activity there).

## Colormap choices in evidence

| Where | Cmap |
|---|---|
| `PlotBrainPyvista.plot_surf` default (cortical_pv.py:90) | `"hot"` (matplotlib built-in) |
| `PlotBrainNilearn.plot_surf` default (cortical.py:73) | `"hot"` |
| `plot_timesteps_mp4` default kwargs | inherits from `plot_surf` so `"hot"` |
| `plotting/utils.py:278` default in `plot_colorbar` | `colorcet.cm.fire` |
| `plotting/subcortical.py:200` default | `"hot"` |
| **The notebook actually uses** (C5 + C8) | `"fire"` (colorcet) |
| RGB visualisation default | `"rgb"` literal (not a cmap; uses the RGB channel mixing branch) |

**Verdict**: the notebook's `fire` is the reference. Build Monarch's LUT from `colorcet.cm.fire`. The class default `hot` is a reasonable fallback but the notebook (and, presumably, the actual TRIBE web demo) uses `fire`.
