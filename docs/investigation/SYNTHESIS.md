# SYNTHESIS - The Nine Questions

**Everything you need to wire the Monarch frontend to live TRIBE v2 inference, in one file.**

Cross-references to the deep-dive docs in this directory use bracket links like `[03 §2a]`.

---

## Q1. Exact code path from `model.predict_text("some headline")` to a `(T, 20484)` activation array

There is NO `predict_text` method in TRIBE v2 itself. The Monarch backend wraps it. Full call chain:

```
monarch-backend/app/services/inference.py:76-112
    TribeInferenceService.predict_text(text: str)
        (writes text to a tmp .txt file)
 │
 └──> tribev2/demo_utils.py:243-320
      TribeModel.get_events_dataframe(text_path=Path(tmp.txt))
          line 304: path.read_text(encoding="utf-8")
          line 307-310: TextToEvents(text=..., infra={"folder": cache_folder, "mode": "retry"}).get_events()
      │
      └──> tribev2/demo_utils.py:98-130
           TextToEvents.get_events()  (decorated with @infra.apply())
               line 114: from gtts import gTTS
               line 115: from langdetect import detect
               line 117: audio_path = Path(self.infra.uid_folder(create=True)) / "audio.mp3"
               line 118: lang = detect(self.text)
               line 119-120: gTTS(self.text, lang=lang).save(str(audio_path))
               line 123-129: audio_event = {"type": "Audio", "filepath": audio_path, ...}
               line 130: return get_audio_and_text_events(pd.DataFrame([audio_event]))
           │
           └──> tribev2/demo_utils.py:66-95
                get_audio_and_text_events(events_df, audio_only=False)
                    transforms = [
                        ExtractAudioFromVideo(),                       # no-op for audio input
                        ChunkEvents("Audio", max_duration=60, min_duration=30),
                        ChunkEvents("Video", max_duration=60, min_duration=30),  # no video
                        ExtractWordsFromAudio(),                        # runs uvx whisperx subprocess
                        AddText(),
                        AddSentenceToWords(max_unmatched_ratio=0.05),
                        AddContextToWords(sentence_only=False, max_context_len=1024, split_field=""),
                        RemoveMissing(),
                    ]
                    events = standardize_events(events_df)
                    for t in transforms: events = t(events)
                    return standardize_events(events)
                │
                └──> tribev2/eventstransforms.py:86-212
                     ExtractWordsFromAudio._run(events_df)
                         line 135: subprocess.run(["uvx", "whisperx", wav, ...], ...)
                         returns pd.DataFrame of Word events

(Back in TribeInferenceService.predict_text)
 │
 └──> tribev2/demo_utils.py:322-392
      TribeModel.predict(events=events_df, verbose=True)
          line 357: loader = self.data.get_loaders(events=events, split_to_build="all")["all"]
          │
          └──> tribev2/main.py:160-275
               Data.get_loaders(events=events, split_to_build="all")
                   line 214-217: for each modality -> extractor.prepare(events) -> _free_extractor_model
                       (caches HuggingFaceText (LLaMA 3.2-3B), Wav2VecBert, HuggingFaceVideo features to disk)
                   line 245-251: segments = ns.segments.list_segments(events, triggers=..., stride=100s, duration=100s)
                   line 263-267: dataset = ns.dataloader.SegmentDataset(extractors=..., segments=..., remove_incomplete_segments=False)
                   line 268-272: dataloader = dataset.build_dataloader(shuffle=False, num_workers=..., batch_size=8)
                   returns {"all": dataloader}
          │
          line 359-381: prediction loop:
              for batch in tqdm(loader):
                  batch = batch.to(model.device)
                  # decompose each 100-TR window into per-TR sub-segments (line 364-369)
                  batch_segments = [segment.copy(offset=t, duration=TR) for segment in batch.segments for t in np.arange(0, duration, TR)]
                  # drop empty TRs (line 370-376)
                  keep = np.array([len(s.ns_events) > 0 for s in batch_segments])
                  # forward pass (line 377)
                  y_pred = model(batch).detach().cpu().numpy()    # (B, 20484, 100)
                  # flatten + filter (line 378)
                  y_pred = rearrange(y_pred, "b d t -> (b t) d")[keep]   # (n_kept_in_batch, 20484)
                  preds.append(y_pred)
          │
          └──> tribev2/model.py:163-178
               FmriEncoderModel.forward(batch, pool_outputs=True)
                   line 164: x = self.aggregate_features(batch)                           # (B, 200, 1152)
                   │
                   └──> tribev2/model.py:180-225
                        aggregate_features(batch)
                            for modality in self.feature_dims.keys():
                                if modality not in batch.data: data = torch.zeros(B, T, 384)
                                else: project + optional layer-cat/mean + optional dropout
                            out = torch.cat(tensors, dim=-1)          # concat to (B, 200, 1152)
                            return out
                   line 168-169: x = self.transformer_forward(x, subject_id)              # (B, 200, 1152)
                   │
                   └──> tribev2/model.py:227-234
                        transformer_forward(x, subject_id=None)
                            line 228: x = self.combiner(x)                                # Identity
                            line 229-230: x = x + self.time_pos_embed[:, :x.size(1)]      # learned pos emb
                            line 232-233: x = self.encoder(x)                             # x_transformers 8-layer
                            return x
                   line 170: x = x.transpose(1, 2)                                        # (B, 1152, 200)
                   line 171-172: x = self.low_rank_head(x.transpose(1,2)).transpose(1,2)  # (B, 2048, 200)
                   line 173: x = self.predictor(x, subject_id)                            # (B, 20484, 200)  via SubjectLayers
                   line 174-175: out = self.pooler(x)                                     # (B, 20484, 100)
                   return out

          line 381: preds = np.concatenate(preds)                                         # (T_total, 20484)
          return (preds, all_segments)
```

**Return shape**: `preds` is `np.ndarray` of shape `(T, 20484)` where `T` = number of non-empty 1-second TRs across all 100-TR windows. For a 23.256s Shakespeare input the notebook observed `T=24`. For a 52.21s Sintel trailer it observed `T=53`.

See `[03 §§1-6]` for the full line-by-line trace with shape annotations.

---

## Q2. Data format: what does the `(T, 20484)` output represent?

**Physical interpretation**: Predicted fMRI BOLD response at each of the 20484 fsaverage5 cortical vertices, per 1-second time bin. Not raw BOLD, not z-scored, not Pearson correlations. These are the **direct model outputs** from `self.predictor(x, subject_id)` followed by `AdaptiveAvgPool1d(100)`, with no post-processing.

**Unit**: arbitrary. The training loss was `MSELoss(reduction="none")` (`grids/defaults.py:233`) against the native BOLD signal of each study, resampled to 1 Hz and projected to fsaverage5 via `nilearn.surface.vol_to_surf(kind="ball", radius=3)`. No per-subject standardisation was applied to the targets inside the `FmriExtractor`. With `average_subjects=True`, the subject dimension is averaged out. So the output lives on roughly the scale of "average-subject BOLD values at 1Hz", which is close to z-score magnitudes but without guaranteed mean-zero or unit-variance.

**Range**: unconstrained. Both positive and negative. Long-tailed. The notebook uses `robust_normalize(percentile=99)` (clips to [p1, p99] then rescales to [0,1]) before display, which is what TRIBE's own visualisation code does by default.

**Ordering**: first 10242 vertices = left hemisphere, last 10242 vertices = right hemisphere. Within a hemisphere, the indices follow the fsaverage5 vertex order from nilearn's GIFTI files (same order as FreeSurfer's standard fsaverage5). See `utils.py:242-246` which offsets right-hemi HCP ROI indices by 10242 before concatenation.

**Normalisation for visualisation** (see `[04 §Colormap pipeline]` and `[05 §4]`):

```python
# What TRIBE v2 does internally before rendering:
normalized = robust_normalize(data, percentile=99, two_sided=True, clip=True)
# lo = np.percentile(data, 1); hi = np.percentile(data, 99)
# out = clip((data - lo) / (hi - lo), 0, 1)
```

This is the single most important function for Monarch's frontend port. Re-implement in JS verbatim.

**For NAA computation**: the unit doesn't matter because NAA compares two ROI-mean values from the same output vector (the ratio cancels units). Monarch can compute NAA on the raw `(20484,)` values. For cross-stimulus comparisons (e.g., "does this headline produce higher arousal than that one?"), normalise per-batch or use the calibrated alpha-hat.

---

## Q3. Colormap pipeline: `(20484,)` float -> per-vertex colours

The reference implementation is `PlotBrainPyvista.plot_surf` in `cortical_pv.py:80-167`, driven by `plot_timesteps` in `base.py:235-365`. Combined, the notebook call:

```python
plotter.plot_timesteps(preds[:15], segments=..., cmap="fire", norm_percentile=99, vmin=.5, alpha_cmap=(0, .2))
```

produces this pipeline:

1. **Robust normalize** with percentile=99 applied **once to all 15 TRs at once** (so all frames share a normalisation range):
   ```python
   data = robust_normalize(data, percentile=99)
   # lo = p1(data.flatten()), hi = p99(data.flatten())
   # normalized = clip((data - lo) / (hi - lo), 0, 1)
   ```

2. **Get cmap** via `get_cmap("fire", alpha_cmap=(0, 0.2))`:
   - Start with `colorcet.cm.fire` (fallback chain: matplotlib -> seaborn -> colorcet).
   - Wrap in `get_alpha_cmap(cmap, threshold=0, scale=0.2)`:
     - For 1024 sample points across [0, 1]
     - `alpha[i<204] = ramp(0..1)` over the first 0.2 of the range
     - `alpha[i>=204] = 1.0`
     - Result: fully transparent at value 0, fully opaque by value 0.2, linear between.

3. **Get ScalarMappable** via `get_scalar_mappable(data, cmap, vmin=0.5, vmax=None)`:
   - `Normalize(vmin=0.5, vmax=1.0)` maps the top half of the normalized range to the cmap.
   - Values < 0.5 lookup at cmap index 0 (the "off" colour); combined with the alpha ramp from step 2, anything below 0.5 is invisible because the alpha at cmap index 0 is near zero.

4. **Split by hemisphere** with `get_stat_map(data)` (`base.py:178-215`):
   ```python
   left = data[:10242]
   right = data[10242:]
   return dict(left=left, right=right, both=np.r_[left, right])
   ```

5. **For each view / hemisphere**:
   ```python
   rgba = sm.to_rgba(stat_map)                              # (N, 4)
   bg_map = mesh["bg_map"]                                  # sulcal depth, (N,)
   bg_norm = (bg_map - bg_map.min()) / (bg_map.max() - bg_map.min() + 1e-8)
   bg_rgb = 1 - np.column_stack([bg_norm] * 3)              # (N, 3), bg_darkness=0 default
   # Alpha-blend activation over sulcal gray:
   colors = rgba[:, 3:4] * rgba[:, :3] + (1 - rgba[:, 3:4]) * bg_rgb
   ```

6. **Render**: pyvista `PolyData(vertices, pv_faces)` + `point_data["colors"]=colors`, add_mesh with `smooth_shading=True, ambient=0.3`, off-screen screenshot to PNG.

**For Monarch JS port**: every step is straight-forward:
- `robust_normalize` in JS: sort once, look up p1 and p99 indices.
- LUT: embed `colorcet.cm.fire(linspace(0,1,256))` as a 256-RGBA texture baked at build time.
- Alpha ramp: piecewise-linear function in shader or in the LUT alpha channel.
- `vmin=0.5`: apply as `clamp((norm - 0.5) / 0.5, 0, 1)` before LUT lookup.
- Sulcal gray: the `monarch-meshes/*_pial.json` files already ship `sulcalDepth` arrays; pre-normalise with metadata's min/max (`-1.494..1.841`).
- Blend: `finalRgb = alpha * lutRgb + (1 - alpha) * sulcalRgb`.
- Lighting: `ambient=0.3, diffuse=0.7` Phong over `smooth_shading=True` means per-vertex normals via `BufferGeometry.computeVertexNormals()`.

See `[05 §3]` for the line-by-line Python and `[05 §14]` for a GLSL shader sketch.

**Important gotcha**: `robust_normalize` must be applied to the whole `(T, 20484)` time series at once if animating, otherwise each TR will flicker to full brightness. For a single static snapshot (Monarch MVP), apply to the `(20484,)` item vector. For the A/B compare, apply to the concatenation of both vectors so they share a scale.

---

## Q4. Multimodal: can encoders run separately?

**Short answer**: Yes and no.

**Yes** - you can pass a text-only events DataFrame, or an audio-only DF, and `predict()` will return a valid `(T, 20484)` output. The `aggregate_features` method (`model.py:180-225`) silently replaces missing modalities with zero tensors, then concatenates everything and feeds the result through the transformer. So:
- `predict_text("hello")` (via TextToEvents -> gTTS -> audio -> whisperx -> text+audio features) actually runs with `text + audio + zeros_for_video`.
- `predict_audio(path)` runs with `text + audio + zeros_for_video` (text comes from whisperx'd transcription of the audio).
- `predict_video(path)` runs with `text + audio + video`.

There is no API for "text only with zero audio zero video". Text always reaches the model via the audio pipeline (gTTS or whisperx transcription).

**No** - you cannot cleanly decompose the output. The transformer's 8 layers mix the modalities non-linearly. Setting the audio channels to zero does not produce "the brain response if only text was present" - it produces "the brain response if the audio were silent" under the trained model, which includes whatever spurious correlations the model learned between silent-audio and resting-state BOLD.

**`aggregate_features` accepting a single modality**: Yes, in the sense that missing modalities are zero-filled, so calling `model.forward(batch)` with `batch.data` containing only `text` will return an output. The output's quality is sensitive to the training-time `modality_dropout=0.3` - the model was regularised to cope with missing channels, so the predictions are not nonsense, but they aren't physiologically clean either.

**How per-modality vectors relate to combined**: Not cleanly. The Monarch backend's `predict_multimodal` (inference.py:142-176) runs three separate `predict()` calls (text -> audio -> video) and takes a simple numpy mean of the three item vectors. This is NOT "what the combined model would predict" - it's a post-hoc average that lets the frontend show separate "text channel", "audio channel", "video channel" maps. For the real combined prediction you'd need one `predict()` call with all three modalities present in the events DF.

**Recommendation for Monarch**:
1. **For the primary brain render**: call `predict()` with the full multimodal events DF (the natural output of `get_events_dataframe(text_path=...)`). That's a single `(T, 20484)` from one forward pass.
2. **For the "RGB multimodal" stretch visualisation** (like TRIBE's `plot_surf_rgb`): run three separate `predict()` calls with artificial text-only / audio-only / video-only events DFs, get three `(20484,)` vectors, map each to an RGB channel in the shader. This is what `predict_multimodal` in the backend already does.
3. **Do NOT claim** that the three separate predictions "decompose" the combined prediction. They don't. Communicate this clearly in the UI.

---

## Q5. Temporal: what is TR and how many TRs for 30 seconds?

**Inference TR = 1.0 s**. Confirmed at:
- `grids/defaults.py:73` - `"neuro": {"frequency": 1, ...}`
- `main.py:146-147` - `@property\ndef TR(self): return 1 / self.neuro.frequency` -> 1.0 s
- Notebook markdown: "1 TR = 1 second"
- Notebook output: 52.21s video -> 53 kept TRs, 23.256s text -> 24 kept TRs (roughly 1:1 TR-to-seconds).

**Segment window = 100 TRs = 100 s** (`grids/defaults.py:132` - `"duration_trs": 100`).

**For a 30-second headline**: the sliding window is 100 s, so only ONE window is built. Each of the 100 per-second rows is checked for emptiness, and roughly 30 of them will contain events (the headline spans 30s of TRs). So **T ≈ 30** non-empty rows, shape `(30, 20484)`.

**For a 60-second scan**: T ≈ 60.

**For a 200-second monologue**: T ≈ 100, because one 100-TR window is built per 100s of stride, but the predict loop rearranges all 200 rows into the final output. Actually, looking more carefully at `get_loaders` + `list_segments`:
```python
segments = ns.segments.list_segments(
    events[sel],
    triggers=events[sel].type == "CategoricalEvent",
    stride=(self.duration_trs - overlap_trs) * self.TR,      # (100 - 0) * 1 = 100s stride
    duration=self.duration_trs * self.TR,                    # 100s duration
    ...
)
```
For a 200s stimulus with stride=100 and duration=100, two windows are built: `[0..100]` and `[100..200]`. Each produces 100 per-TR rows, 100 of which are non-empty. So `T ≈ 200`.

**Can the frontend animate at TR rate?** Yes. At 1 Hz the animation is slow, but the TRIBE web demo uses ffmpeg `minterpolate` to generate in-between frames (`base.py:474-478`). The Monarch frontend can do client-side linear interpolation: `lerp(frame[t], frame[t+1], alpha)` where `alpha = (video_currentTime - t) / TR`.

**For the Monarch MVP static snapshot**: ignore time entirely. Compute `preds.mean(axis=0)` -> `(20484,)` and ship once per scan. That's what `monarch-backend/app/services/inference.py:predict_text` already does via `mean_pool(preds_np)`.

---

## Q6. Video / image input

**`get_events_dataframe(video_path=...)`** (`demo_utils.py:312-320`):
```python
event = {"type": "Video", "filepath": str(path), "start": 0, "timeline": "default", "subject": "default"}
return get_audio_and_text_events(pd.DataFrame([event]))
```

Then `get_audio_and_text_events` applies:
1. `ExtractAudioFromVideo()` - uses `neuralset.events.transforms.ExtractAudioFromVideo` (external package). Internally calls `moviepy.VideoFileClip(...).audio.write_audiofile(...)` to write a `.wav` next to the video. Emits an `Audio` event.
2. `ChunkEvents("Video", max_duration=60, min_duration=30)` - splits long videos into 30-60s chunks.
3. `ExtractWordsFromAudio()` - runs `uvx whisperx` on the extracted audio track (see Q1 for details).
4. `AddText()`, `AddSentenceToWords`, `AddContextToWords`, `RemoveMissing` - same as audio path.

So a video input produces **Video + Audio + Text + Word + Sentence** events in the DF. All three modalities (text, audio, video) are active in the forward pass.

**`get_events_dataframe(image_path=...)`**: **NOT SUPPORTED**. `VALID_SUFFIXES` (`demo_utils.py:42-46`) only has entries for `text_path`, `audio_path`, `video_path`. There is no `image_path` kwarg in `get_events_dataframe`. To feed a still image you'd need to either:
- Construct your own events DataFrame with `type="Image"` events and pass it directly to `model.predict(events=...)` (the `CreateVideosFromImages` transform could turn them into videos). But `get_audio_and_text_events` doesn't call `CreateVideosFromImages` so you'd need to call it yourself or add it to your own transform chain.
- Or use a workaround: convert the image to a 5-second video with ffmpeg, then pass `video_path`.

**`CreateVideosFromImages`** (`eventstransforms.py:215-265`):
```python
class CreateVideosFromImages(EventsTransform):
    fps: int = 10
    remove_images: bool = True
    infra: exca.MapInfra = ...

    @infra.apply(item_uid=lambda e: f"{e.filepath}_{e.duration}")
    def create_video(self, image_events):
        for image_event in image_events:
            video_filepath = Path(...) / f"{stem}_{duration}.mp4"
            clip = moviepy.ImageClip(str(image_filepath), duration=image_event.duration)
            clip.write_videofile(video_filepath, codec="libx264", audio=False, fps=10)
            yield Video.from_dict(image_event.to_dict() | {"type": "Video", ...})
```

So it replicates the image at 10 FPS for `image_event.duration` seconds, writes an mp4, and emits a Video event. The image duration has to be set on the input event (it's not auto-inferred). Adds `remove_images=True` to drop the original Image event after replacement.

**V-JEPA 2 frame sampling parameters**: The model repo name is `facebook/vjepa2-vitg-fpc64-256`, where `fpc64` = 64 frames per clip, `256` = 256-pixel input. `clip_duration=4` (`grids/defaults.py:52`) means each 4-second video segment is sampled as 64 frames (at 16 FPS). The `HuggingFaceVideo` outer wrapper in neuralset is responsible for slicing the video into non-overlapping 4-second chunks. At the training feature frequency of 2 Hz, each 0.5 s produces one feature vector that summarises a 4-second sliding context.

**DINOv2 still-image branch**: configured in `grids/defaults.py:42-50` but NOT in `features_to_use = ["text", "audio", "video"]`, so the released model does NOT use it. If a future Monarch wants to wire DINOv2 separately, they'd need to either re-train or hack the extractor chain.

---

## Q7. Dual brain view (Monarch A/B compare mode)

**What Monarch must send to the frontend**: Two separate predict() calls, each producing one `(20484,)` mean-pooled vector.

```python
# Backend pseudocode (Monarch already has the singleton model)
result_a = inference_service.predict_text(text_a)["item_vector"]   # (20484,) np.float32
result_b = inference_service.predict_text(text_b)["item_vector"]   # (20484,) np.float32

# Serialisation to the frontend:
{
  "a": {"vector": result_a.tolist(), "naa": 0.42, "label": "Headline A"},
  "b": {"vector": result_b.tolist(), "naa": 0.38, "label": "Headline B"}
}
# ~165 KB per vector as JSON. Compressed gzip ~30 KB. Consider binary float32 + base64 for bandwidth.
```

**Frontend renders two instances of `<BrainViewer>` side-by-side**, each consuming one vector. Important subtleties:

1. **Share normalisation range across both brains.** Don't let each brain independently compute its own `robust_normalize(percentile=99)` because that would wipe out relative-magnitude differences. Instead:
   ```js
   const combined = new Float32Array([...vecA, ...vecB]);
   const {lo, hi} = computePercentiles(combined, 1, 99);
   const normA = vecA.map(v => clamp((v - lo) / (hi - lo), 0, 1));
   const normB = vecB.map(v => clamp((v - lo) / (hi - lo), 0, 1));
   ```
   Now `normA` and `normB` are on the same scale, so the visually brighter brain really is more active.

2. **Use the same cmap + alpha ramp for both.** Don't let the user pick different colours per side, or the comparison becomes meaningless.

3. **Synchronise camera controls.** When the user orbits one brain, the other should orbit to match. In Three.js this is one `OrbitControls` instance driving both cameras via a shared target, or two controls that sync via an event bus.

4. **Show a difference map as a third brain (optional stretch).** `diff = vecA - vecB`, then render with a **diverging** colormap (`"seismic"` or `"bwr"`) and `symmetric_cbar=True`. TRIBE's `get_thresholded_sm` already supports `symmetric_cbar`. The Monarch shader would use a diverging LUT (256 stops from blue through white to red) and normalise on `max(|diff.min()|, |diff.max()|)`.

5. **NAA gets computed per brain, independently.** The NAA ratio is per-scan. Show `naa_a=0.42` and `naa_b=0.38` in the UI without mixing.

6. **Don't average the two vectors.** That's meaningless for A/B comparison.

---

## Q8. What Monarch must do differently from the TRIBE v2 demo

| Aspect | TRIBE v2 demo | Monarch |
|---|---|---|
| Inference timing | Pre-baked, static | **Live per scan** via FastAPI + TribeModel singleton |
| Physics layer | None | **NAA + Landau / Ising mean-field** free energy, susceptibility, crackling noise |
| Calibration | N/A | **Alpha-hat** OLS on NELA-GT-2021 labels |
| Batch mode | Single demo clip | **Corpus-scale** (1500+ items), memmap-backed resume journal |
| A/B compare | None | **Two scans side-by-side** with shared normalisation and optional diff map |
| Frontend | Three.js with pre-baked texture atlas, 5 GLB meshes, per-face colour interpolation | Three.js + R3F with a **single shader** that reads live `(20484,)` per vertex, mirror-ports `robust_normalize` + alpha blend |
| Animation | Video-timeline driven, pre-baked frames | Static snapshot at MVP; stretch goal = live animation with `(T, 20484)` payloads |
| Output surface | fsaverage5 cortical | fsaverage5 cortical (identical) |
| Subcortical | None | None (impossible without re-training, see `[06 §NAA interpretation]`) |
| Colour stretch | `fire` cmap (presumably, matching the notebook) | `fire` cmap (identical) |
| Mesh assets | 5 GLB files with embedded PyVista-style normals | 4 JSON files + 1 combined binary in `monarch-meshes/` (already committed, see `01_file_map.md`) |
| Input modalities | Pre-selected demo videos only | **User uploads**: text, audio (wav/mp3/flac/ogg), video (mp4/avi/mkv/mov/webm) |

**Per-diff breakdown**:

### Live inference
- Load `TribeModel.from_pretrained("facebook/tribev2")` ONCE at FastAPI app startup (done, see `inference_service.load_model`).
- Handle per-request text/audio/video via `get_events_dataframe`.
- **Shared singleton**: make sure FastAPI uses only one worker process or handle the multi-worker case with a distributed lock. LLaMA 3.2-3B alone is ~6 GB of VRAM; you don't want four workers loading it four times.
- **First-request cold start**: the extractors (LLaMA, V-JEPA2, w2v-BERT) are only loaded when `extractor.prepare(events)` is called, not at app startup. So the first `/scan` is ~60 s slow while each extractor downloads from HF. Pre-warm by running one dummy scan at startup.

### NAA + Landau / Ising
- Nowhere in TRIBE v2. Build as a separate module `monarch.naa` and `monarch.landau`.
- NAA: `compute_naa(preds_20484, affective_indices, deliberative_indices)` returns a single scalar. ~30 lines of numpy.
- Landau: `F(m, beta, h) = -0.5 * m^2 * beta + log(cosh(beta * (m + h)))` + gradient descent to find `m_star(beta, h)`. `chi = d m_star / d h` for susceptibility. Pure numpy.

### Alpha-hat calibration
- Train on NELA-GT-2021 labels (`1=reliable, 0=unreliable`). OLS with sklearn `LinearRegression` against NAA values. Save intercept and slope.
- At inference, `alpha_hat = intercept + slope * naa`.
- NELA-GT-2021 is ~1.8M articles and needs to be downloaded from `https://doi.org/10.7910/DVN/RBKVBM` (Harvard Dataverse). ~10 GB.

### Batch corpus mode
- Iterate over a CSV/JSONL of items.
- Write each item's `(20484,)` item vector into `np.memmap("corpus.f32", dtype="f4", shape=(N, 20484), mode="w+")`.
- Journal completed item ids to `corpus.journal.jsonl` after each successful write.
- On resume, read the journal, skip completed items.
- Bottleneck: 1500 items x ~10s/item on MI300X = ~4 hours. Use a single background worker, not parallel, to avoid stepping on the TRIBE model's GPU memory.

### A/B compare
- See Q7.

---

## Q9. Blocking issues

Tagged P0 (blocks MVP), P1 (blocks nice-to-have), P2 (operational).

### P0 - model availability
1. **`neuralset==0.0.2` and `neuraltrain==0.0.2` are Meta-internal and not visible on public PyPI** (`pyproject.toml:15-16`). `TribeExperiment` subclasses `neuraltrain.utils.BaseExperiment` and imports dozens of symbols from both. Without these packages, `from tribev2.demo_utils import TribeModel` crashes on the first import. **Verify this works on a clean venv before writing any other Monarch code.** If not reachable, Monarch cannot proceed at all. Already flagged in the audit (`[audit §10.1]`).
2. **LLaMA 3.2-3B is gated** (`meta-llama/Llama-3.2-3B`). Requires `huggingface-cli login` with an approved account. In production this means a service account with the access grant baked into the container. Already flagged in the audit.
3. **License is CC-BY-NC-4.0** (`LICENSE`). Non-commercial only. **If Monarch is a commercial product, shipping the weights or derived predictions is a legal blocker.** Already flagged.

### P0 - Windows dev box broken imports
4. **The `tribev2.demo_utils` import chain crashes on this machine.** The chain is `tribev2 -> demo_utils -> main -> pl_module -> neuraltrain -> torchmetrics -> onnxruntime`, and `onnxruntime` has a broken DLL here. This is why `scripts/export_brain_mesh.py` deliberately avoids `import tribev2` and replicates `BasePlotBrain.get_mesh()` inline. **The Monarch backend on the dev box can't test any TRIBE code path that involves the encoder**. On the AMD MI300X production box, `onnxruntime` should work under ROCm but `torchmetrics` + `onnxruntime` compatibility needs to be verified.

### P0 - WhisperX runtime requirement
5. **`ExtractWordsFromAudio` shells out to `uvx whisperx`** (`eventstransforms.py:111-132`). Requires:
   - `uv` installed on the container's PATH
   - Network access on first call to download whisperx + `large-v3` + `WAV2VEC2_ASR_LARGE_LV60K_960H` align model from HuggingFace
   - Significant disk space for the cached whisperx models
   - Blocks until the subprocess finishes (no timeout in the wrapper)
   
   **Bake the whisperx cache into the Docker image** by running a dummy scan at container build time, so the first production request doesn't hang. Or stand up an air-gap proxy that serves the cached files.

### P0 - subcortical gap
6. **No subcortical checkpoint is published on `facebook/tribev2`.** The Monarch spec mentions Nucleus Accumbens / Ventral Striatum ROI integration; these are subcortical only. The HCP MMP1.0 parcellation is cortical only, so `get_hcp_roi_indices("Accumbens")` will raise `ValueError`. **Monarch must drop subcortical ROIs from the NAA computation, or train a subcortical head from scratch (infeasible).** Already flagged in the audit (`[audit §10.6]`).
7. **Monarch spec's `8,802 subcortical voxels` is not present anywhere in the repo.** Whatever subcortical voxel count Monarch quotes needs to be re-derived from Harvard-Oxford 2mm at inference time. Already flagged.
8. **Monarch spec's `hidden=384`, `8-head transformer` disagree with reality** (`hidden=1152, low_rank_head=2048`, heads unknown because neuraltrain doesn't override x_transformers defaults). Update the Monarch design doc. Already flagged.

### P0 - implicit deps
9. **`mne` is not in `pyproject.toml` but is imported by `tribev2/utils.py:13`** (for HCP ROI helpers). Add `mne` to Monarch's own requirements. Already flagged.
10. **`requests`, `tqdm`, `exca`, `pydantic`, `whisperx` are similarly implicit.** `whisperx` is invoked as a subprocess but `uv` must be installed. The others are transitive via neuralset.

### P0 - ROI naming
11. **The Monarch spec uses EEG-style ROI labels (`Fp1`, `Fp2`)** that are NOT HCP MMP1.0 parcel names. Will crash `get_hcp_roi_indices("Fp1")` with `ValueError: ROI Fp1 not found in HCP labels`. Lock down the intended ROI mapping with the product owner before any NAA wiring. Already flagged.
12. **`MI` ambiguity**: "MI" in HCP means mid-insula, not primary motor (which is `4`). The Monarch spec is ambiguous.

### P1 - frontend mesh / normalisation
13. **`monarch-meshes/*_inflated.json` were exported with `inflate=True`, not `inflate="half"`** (`scripts/export_brain_mesh.py:83-84`). The notebook default is `"half"`. For visual fidelity to the notebook output, the Monarch frontend should either (a) lerp the pial and inflated coords 50/50 in JS at mesh load time, or (b) re-run `export_brain_mesh.py` with an `inflate="half"` option added. **Minor visual difference**, not a functional blocker.
14. **`robust_normalize` must run over the full (T, 20484) slab**, not per-TR, if animating. For the MVP static snapshot, run on the `(20484,)` item vector.
15. **`colorcet.cm.fire` LUT must be pre-sampled at build time.** There is no Python runtime in the frontend to call colorcet directly. Bake to a 256-stop RGBA array and embed.

### P2 - operational
16. **First scan cold start**: extractors are lazy-loaded on first `.prepare(events)` call. ~60-90 s of HF downloads + model-to-VRAM for LLaMA + V-JEPA + w2v-BERT. Pre-warm with a dummy scan at app startup.
17. **Multi-worker FastAPI**: avoid. One model instance, one worker. For throughput, serve from a queue instead of parallel workers.
18. **Cache folder growth**: `TribeModel.from_pretrained(cache_folder=...)` - all extracted features get cached here. For batch corpus mode (1500 items) the cache can grow to 10s of GB. Mount on a persistent volume with > 100 GB.
19. **`torch.load(..., weights_only=True, mmap=True)`** (`demo_utils.py:228`) - the `mmap=True` kwarg has had ROCm-specific edge cases in the past. Sanity check on MI300X torch 2.5/2.6.
20. **No tests in the repo.** Monarch must write its own integration test: load the model, run one known fixture, assert shape and rough numerical range (e.g. `preds.shape == (30, 20484)`, `abs(preds).max() < 100`).
21. **`fast_dev_run` and `test_run.py` are training-mode**, not useful for inference smoke tests. Monarch needs its own inference smoke test.

---

## Appendix - file reference cheat sheet

| Need | Location |
|---|---|
| Top-level API | `C:\Users\Windows\Downloads\tribev2\tribev2\__init__.py` (just re-exports TribeModel) |
| Model load logic | `C:\Users\Windows\Downloads\tribev2\tribev2\demo_utils.py:150-241` |
| Events DF builder | `C:\Users\Windows\Downloads\tribev2\tribev2\demo_utils.py:243-320` |
| Predict loop | `C:\Users\Windows\Downloads\tribev2\tribev2\demo_utils.py:322-392` |
| gTTS text->events | `C:\Users\Windows\Downloads\tribev2\tribev2\demo_utils.py:98-130` |
| WhisperX subprocess | `C:\Users\Windows\Downloads\tribev2\tribev2\eventstransforms.py:94-212` |
| FmriEncoder config | `C:\Users\Windows\Downloads\tribev2\tribev2\model.py:49-87` |
| FmriEncoder forward | `C:\Users\Windows\Downloads\tribev2\tribev2\model.py:89-234` |
| `aggregate_features` (missing-modality logic) | `C:\Users\Windows\Downloads\tribev2\tribev2\model.py:180-225` |
| Default training config | `C:\Users\Windows\Downloads\tribev2\tribev2\grids\defaults.py:114-258` |
| Data / Experiment pydantic | `C:\Users\Windows\Downloads\tribev2\tribev2\main.py:82-275` (`Data`) + `278-651` (`TribeExperiment`) |
| HCP ROI helpers | `C:\Users\Windows\Downloads\tribev2\tribev2\utils.py:213-318` |
| Mesh loading | `C:\Users\Windows\Downloads\tribev2\tribev2\plotting\base.py:127-172` |
| Colour pipeline | `C:\Users\Windows\Downloads\tribev2\tribev2\plotting\cortical_pv.py:80-167` |
| Robust normalize | `C:\Users\Windows\Downloads\tribev2\tribev2\plotting\utils.py:19-35` |
| Alpha cmap | `C:\Users\Windows\Downloads\tribev2\tribev2\plotting\utils.py:114-136` |
| Pre-exported mesh JSONs | `C:\Users\Windows\Downloads\tribev2\monarch-meshes\*.json` |
| Pre-exported mesh binary | `C:\Users\Windows\Downloads\tribev2\monarch-meshes\fsaverage5_combined.bin` + `.layout.json` |
| Mesh exporter script | `C:\Users\Windows\Downloads\tribev2\scripts\export_brain_mesh.py` |
| Monarch backend reference | `C:\Users\Windows\Downloads\monarch-backend\app\services\inference.py` |
| Prior audit | `C:\Users\Windows\monarch-audit\AUDIT_REPORT.md` |
