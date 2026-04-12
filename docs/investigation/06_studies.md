# 06 - Studies / Training Data

Each `tribev2/studies/*.py` file. These drive how the model was trained, which determines what the predictions MEAN at inference. Monarch will never train, but must understand these to interpret the `(T, 20484)` outputs correctly.

---

## Summary

| Study | TR | Subjects | Stimuli | fMRI space | Data format | Role in training |
|---|---|---|---|---|---|---|
| `Algonauts2025Bold` | 1.49 s | 4 (sub-01,02,03,05) | Friends sitcom (S1-6 train, S7 test) + movie10 films (bourne, wolf, life, figures) | MNI152NLin2009cAsym | raw BOLD NIfTI via fmriprep, `(76,90,71,592)` | Multimodal video + speech training |
| `Algonauts2025` | 1.49 s | same 4 | same stimuli | Schaefer-1000 parcellation | HDF5 parcellated, `(1000, 592)` | Parcellated variant (not used by released checkpoint) |
| `Lahner2024Bold` | 1.75 s | 10 | BOLD Moments: 3-second video clips, 1000 train / 102 test | MNI152NLin2009cAsym / fsaverage | BIDS / fmriprep `versionB`, plus pre-computed GLM betas on fsaverage | Short-clip video training |
| `Lebel2023Bold` | 2.0 s | 8 (UTS01-08) | Spoken narrative stories (`wheretheressmoke` is the test story, 10 runs) | T1w / MNI152NLin6Asym / fsaverage / fsnative | BIDS / deepprep | Speech / language training |
| `Wen2017` | 2.0 s | 3 | 2.4 hours of YouTube video clips | MNI152NLin6Asym | raw NIfTI (custom naming convention) | Video training |

**All four are combined in the released cortical checkpoint** (see `grids/defaults.py:140-145` where `data.study.names` = `["Algonauts2025Bold","Wen2017","Lahner2024Bold","Lebel2023Bold"]`). After resampling via `TribeSurfaceProjector(mesh="fsaverage5")`, every study's BOLD response lands on 20484 cortical vertices.

**Effective training TR at the brain encoder**: `neuro.frequency = 1` (Hz) in the default config, so the neuro extractor **resamples each study's BOLD from its native TR to 1 Hz** inside neuralset. This is why `Data.TR = 1.0 s` at inference time regardless of the study of origin.

---

## 1. Algonauts2025 / Algonauts2025Bold (algonauts2025.py)

**Source paper**: Gifford et al. 2025, "The Algonauts Project 2025 Challenge: How the Human Brain Makes Sense of Multimodal Movies".

**Dataset origin**: Courtois NeuroMod `friends` + `movie10` sub-projects, released as part of the Algonauts Challenge on `github.com/courtois-neuromod/algonauts_2025.competitors`. Datalad clone required (`pip install datalad`).

**Design** (algonauts2025.py:14-40, 56-97):
- **4 participants**: sub-01, sub-02, sub-03, sub-05 (sub-04 and sub-06 are listed in `RECORDING_DURATIONS` but have zero recording time so are excluded from training).
- **Two stimulus types**:
  1. "Friends" sitcom: 7 seasons, ~175 episodes, segmented into ~5 min chunks `a/b/c/d`. **Seasons 1-6 = train, Season 7 = test.**
  2. "movie10": 4 extractor films (`bourne`, `wolf`, `life`, `figures`) in ~5 min chunks. Some shown twice (runs 1 and 2) for reliability.
- **TR = 1.49 s**, `frequency = 1/1.49 ≈ 0.671 Hz`.
- **Total timelines**: 1588 (`_info.num_timelines`).

**Classes**:
- `Algonauts2025` (base): loads **pre-parcellated** data from HDF5 files (`{subject}_task-friends_{SPACE}_{ATLAS}_desc-s123456_bold.h5`). Schaefer-1000 atlas (1000 parcels, 7 networks). `data_shape=(1000, 592)`.
- `Algonauts2025Bold` (subclass): loads **raw 4D NIfTI** from fmriprep outputs. `data_shape=(76, 90, 71, 592)`. This is the variant used by the released checkpoint.

**Events produced per timeline** (algonauts2025.py:228-275):
- `Fmri` event pointing at the HDF5/nifti file (via `SpecialLoader`).
- `Video` event pointing at the .mkv stimulus.
- `Text` event with concatenated transcript.
- One `Word` event per word in the transcript, with `start`, `duration`, `stop`, `language="english"`, `modality="heard"`.

**Split attribute** (eventstransforms.py:26): `SPLIT_ATTRIBUTES["Algonauts2025Bold"] = "chunk"`. Splits by chunk id.

**What this means for Monarch's interpretation of predictions**: This is the primary source of "video + speech" training data. The brain encoder was conditioned on BOLD responses from people watching ~60 minutes of Friends and movie clips, so predictions are biased toward signals that correspond to temporal-lobe speech processing (STG/MTG) + visual cortex + social/face processing (FFA/STS).

## 2. Lahner2024Bold (lahner2024bold.py)

**Source paper**: Lahner et al., Nature Communications 2024, "Modeling short visual events through the BOLD moments video fMRI dataset and metadata".

**Dataset origin**: BOLD Moments Dataset, boldmomentsdataset.csail.mit.edu. Accessible via `openneuro-py`. License CC0.

**Design** (lahner2024bold.py:14-42, 84-108):
- **10 participants**, sessions 2-5.
- **Two sets**:
  1. Training: **1000 unique 3-second video clips**, 10 runs per session.
  2. Test: **102 unique 3-second video clips**, 3 runs per session, each shown 10 times for reliability.
- **TR = 1.75 s**, `frequency = 0.571 Hz`.
- **Total timelines**: 520.
- **238 volumes per train run, 268 volumes per test run**.
- Includes **LLM-generated captions** for middle frames of each video (`llm_frame_annotations.json`).

**Available in multiple spaces**: MNI152NLin2009cAsym (volumetric), T1w, fsaverage (cortical surface, 163842 verts/hemi), fsnative.

**Preprocessing**: fmriprep `versionB` with additional GLM beta estimation on fsaverage surface. Loaded as either raw BOLD or pre-computed betas from `*_organized_betas_task-{split}_hemi-{left|right}_normalized.pkl` files (shape `(n_trials, n_reps, 163842)`).

**Events per timeline** (lahner2024bold.py:183-244):
- `Fmri` event + N `Video` events per run (one per 3-second clip presented, with LLM caption attached as `middle_frame_captions`).
- No Word events (these are silent video clips).

**Split attribute**: `SPLIT_ATTRIBUTES["Lahner2024Bold"] = "timeline"`. Entire timelines are train or val.

**What this means**: Lahner2024 contributes high-quality short-clip video training signal. Because the clips are **silent**, this is the dataset that trains the model to produce visual-cortex responses without any speech/text input. The LLM captions are used by the text extractor to still produce text features for these clips (via `middle_frame_captions`).

## 3. Lebel2023Bold (lebel2023bold.py)

**Source paper**: LeBel et al., Scientific Data 2023, "A natural language fMRI dataset for voxelwise encoding models". OpenNeuro ds003020.

**Dataset origin**: OpenNeuro ds003020. License CC0.

**Design** (lebel2023bold.py:14-66):
- **8 subjects**: UTS01-UTS08.
  - UTS01/02/03: 82 stories across 20 sessions (extended dataset).
  - UTS04-08: 26-27 stories across 6 sessions.
- **TR = 2.0 s**.
- **432 timelines** (all sessions/runs).
- Subjects listen to **spoken narrative stories** (audio only, no video).
- Test story: `wheretheressmoke` with **10 runs** for reliability.
- Some localizer tasks excluded: `AudioMotorLocalizer`, `AuditoryLocalizer`, `CategoryLocalizer`, `MotorLocalizer`.

**Known issues** (lebel2023bold.py:59-65):
- UTS02: different scan location / protocol, no localizer data.
- UTS04: missing `life.hf5`.
- UTS05: low visual acuity, auditory cues only.
- UTS01/ses-7/treasureisland: corrupted NIfTI, skipped automatically.

**Spaces**: T1w, MNI152NLin6Asym, fsaverage, fsnative.

**Word/phoneme timings**: come from TextGrid files (via `nltk_contrib.textgrid`), NOT from whisperx. The TextGrid files are shipped with the dataset. Both `Word` and `Phoneme` events are produced. Phonemes are currently NOT in `features_to_use` so the model ignores them.

**Events per timeline** (lebel2023bold.py:311-344):
- `Audio` event (the `.wav` file).
- Many `Word` events with text/start/duration.
- Many `Phoneme` events (skipped by the extractor).
- `Fmri` event.
- All non-Fmri events have `start += 10` (10-second pre-story blank period convention).

**Split attribute**: `SPLIT_ATTRIBUTES["Lebel2023Bold"] = "task"`. One story = one task = one split bucket.

**What this means**: Lebel2023 is the pure-language training signal. Because it's audio-only with no video, it trains the Wav2Vec-BERT + LLaMA text branches on clean speech BOLD responses. Key for Monarch because text-only inference ultimately routes through this dataset's learned response patterns.

## 4. Wen2017 (wen2017.py)

**Source paper**: Wen et al., Cerebral Cortex 2018, "Neural Encoding and Decoding with Deep Learning for Dynamic Natural Vision". `academic.oup.com/cercor/article/28/12/4136/4560155`.

**Dataset origin**: `video_fmri_dataset` (custom, not OpenNeuro).

**Design** (wen2017.py):
- **3 subjects**: `subject1`, `subject2`, `subject3`.
- **TR = 2.0 s** (hardcoded, "don't rely on nifti header").
- **Stimuli**: 2.4 hours of YouTube video clips.
- Train segments named `seg*` with 2 fmri runs each.
- Test segments named `test*` with 10 fmri runs each.

**Events per timeline**:
- `Video` event (an `.mp4`).
- `Fmri` event (a masked `.nii.gz`).
- No Word/Audio events emitted directly - if the video has an audio track, the `ExtractAudioFromVideo` + `ExtractWordsFromAudio` transforms would pull it out at load time, otherwise the model sees only video.

**Split attribute**: `SPLIT_ATTRIBUTES["Wen2017"] = "seg"`.

**What this means**: Wen2017 adds more long-form video training signal, complementing Lahner2024's short clips.

---

## 5. Unused studies referenced in code

- `Nastase2020` - split_attr `story`. Defined in `FMRI_SPACES` (`utils.py:31`) and `SPLIT_ATTRIBUTES` (`eventstransforms.py:32`) but no `studies/nastase2020.py` file. Dead code / planned.
- `Wenvtwo2017` - split_attr `run`. Same: referenced, no file. Possibly a Wen2017 v2 that was dropped.
- `Vanessen2023` - split_attr `run`.
- `Aliko2020`, `Li2022` - both split_attr `run` / `task`. These have spaces listed in `FMRI_SPACES` (`MNICOLIN27`).

None of these ship with the repo. The released checkpoint was trained on the four above only.

---

## 6. fMRI spaces table (utils.py:23-32)

```python
FMRI_SPACES = {
    "Algonauts2025Bold": "MNI152NLIN2009C_ASYM_RES_01",
    "Wen2017":           "MNI152NLIN6_ASYM_RES_01",
    "Lahner2024Bold":    "MNI152NLIN2009C_ASYM_RES_01",
    "Lebel2023Bold":     "MNI152NLIN2009C_ASYM_RES_01",
    "Vanessen2023":      "MNI152NLIN6_ASYM_RES_01",
    "Aliko2020":         "MNICOLIN27",
    "Li2022":            "MNICOLIN27",
    "Nastase2020":       "MNI152NLIN2009C_ASYM_RES_01",
}
```

All volumetric MNI spaces. At training time, `TribeSurfaceProjector` (`utils_fmri.py:129-248`) resamples each to fsaverage5 via `nilearn.surface.vol_to_surf(..., kind="ball", radius=3)`. This is why every study ends up on the same 20484-vertex space regardless of its native voxel grid.

## 7. Recording durations table (utils.py:33-61)

```python
RECORDING_DURATIONS = {
    "Algonauts2025Bold/sub-01": 66.4,  # hours
    "Algonauts2025Bold/sub-02": 66.4,
    "Algonauts2025Bold/sub-03": 66.4,
    "Algonauts2025Bold/sub-04": 0,      # skipped
    "Algonauts2025Bold/sub-05": 66.4,
    "Algonauts2025Bold/sub-06": 0,      # skipped
    "Lahner2024Bold/1..10":     6.2 each,
    "Lebel2023Bold/UTS01":      17.9,
    "Lebel2023Bold/UTS02":      18.1,
    "Lebel2023Bold/UTS03":      18.1,
    "Lebel2023Bold/UTS04..08":  6.2-6.4 each,
    "Wen2017/subject1..3":      11.7 each,
}
```

Total training: ~4 * 66.4 (Algonauts) + 10 * 6.2 (Lahner) + 3 * ~18 + 5 * ~6 (Lebel) + 3 * 11.7 (Wen) ≈ ~450 hours of fMRI. Used by `get_subject_weights(weigh_by="recording_time")` (utils.py:182-210) to weight training samples.

## 8. What this means for Monarch's NAA interpretation

The released checkpoint's `(T, 20484)` output is a **weighted ensemble prediction** from all four studies. A prediction of "high activation at vertex 5000" means "under the learned model, the average-subject's BOLD signal at fsaverage5 vertex 5000 would be elevated in response to this stimulus".

Specifically:
- It is NOT raw BOLD.
- It is NOT z-scored (no code normalises the output before it leaves `predict()`).
- The **training target** was each study's native BOLD signal resampled to 1 Hz and projected to fsaverage5 via `vol_to_surf(kind="ball", radius=3)`.
- The **training loss** was `MSELoss(reduction="none")` (grids/defaults.py:233), averaged at the `BrainModule._run_step` level.
- Per-study BOLD data is **not normalised inside the `FmriExtractor`** at training time; each subject's values are on their own arbitrary scale. The `average_subjects=True` toggle at inference sets `data.neuro.aggregation = "mean"` which averages across subjects.

Therefore the output is in **arbitrary model-predicted-BOLD-like units, roughly centered around zero with long tails**. The notebook's use of `robust_normalize(percentile=99)` before plotting is *required* to get consistent visual output.

For Monarch's NAA ratio calculation, this is fine - NAA compares two ROI-mean values of the same output vector, so the arbitrary unit cancels out. But do NOT compare raw values across different stimuli without first normalising (or computing ratios / z-scores).

### Monarch action items from studies analysis

1. **Don't attempt subcortical predictions.** The released checkpoint has no subcortical head. Monarch's spec mention of Nucleus Accumbens / Ventral Striatum cannot be satisfied without training from scratch.
2. **Text-only inference is "valid but degraded".** The training data has lots of text-with-video (Algonauts) and text-with-audio-only (Lebel2023). A pure-text input is out of distribution because in training there was always either video or audio alongside. The gTTS workaround partially closes this gap by synthesising audio from text, but the gTTS voice and the trained Wav2Vec-BERT distribution don't match perfectly.
3. **Expect noisier predictions for short stimuli.** The model's sliding window is 100 TRs = 100 seconds. A 10-second headline produces 10 kept TRs of 100, so **10% of the segment has valid signal and 90% is zero-padded / empty-dropped**. The averaged-pooled item vector for a 10s headline is therefore much noisier than for a 60s monologue.
4. **The fsaverage5 surface is the native output space**. No subcortical. No volumetric. No parcellation. If Monarch wants a Schaefer-1000 parcel view, it needs to pre-compute a `vertex -> parcel` mapping and average client-side.
