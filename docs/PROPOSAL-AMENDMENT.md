# Proposal Amendment, Monarch

**To:** Dr. Songa Mutambi
**From:** Brian Mwai (1050555)
**Re:** *Measuring the Invisible*, instrument limitation, reformulated observable, and revised scope
**Date:** 2026-07-16
**Status:** DRAFT, requires supervisor sign-off before the paper is written

---

## Summary

Three things have changed since the April proposal. All three are empirical, all three are documented below, and two of them change what the thesis can claim.

1. **The released TRIBE v2 checkpoint cannot measure the amygdala.** It is cortical-only. The proposal's central observable, Eq. (4), is defined on a structure the instrument does not predict.
2. **The ratio form of NAA is undefined on real content** and has been replaced by a signed difference.
3. **The one calibration run to date returned a null result, twice, independently.**

None of these is a bug. They are properties of the instrument and of the data, and the honest response is to amend the proposal rather than to report numbers the instrument cannot support.

---

## 1. The instrument does not measure the amygdala

### What the proposal assumes

The proposal states that TRIBE v2 "outputs a predicted fMRI activation pattern across 29,286 neural targets," including "the amygdala and nucleus accumbens as explicit prediction targets." Eq. (4) defines the central observable as

```
NAA = A_amyg / (A_PFC + delta)
```

and the ROI table (§4.1) sources `A_amyg` and `A_NAcc` from the Harvard-Oxford *subcortical* atlas.

### What the released checkpoint actually does

The released `facebook/tribev2` checkpoint predicts **20,484 cortical surface vertices on fsaverage5, and nothing else.** There is no subcortical head. The amygdala and the nucleus accumbens are not among its outputs.

Evidence:

| Source | Finding |
|---|---|
| `services/inference/tribe-ckpt/config.yaml:145,154` | `mesh: fsaverage5`, `name: TribeSurfaceProjector`, a surface projector. No `MaskProjector`, no Harvard-Oxford reference, no subcortical mask. |
| Checkpoint payload (`model_build_args`) | `"n_outputs": 20484` |
| `services/inference/scripts/smoke_test.py:121` | Runtime assertion `if preds.shape[1] != 20484` |
| Upstream `tribe_demo.ipynb:309,571` | Recorded real outputs: `Predictions shape: (53, 20484)`, `(24, 20484)` |
| Two independent runs (AMD MI300X, Colab T4) | Both produced `(T, 20484)` |

The figures **29,286 and 8,802 appear nowhere in the model, the checkpoint, or the upstream code.** They describe the architecture as characterised in the FAIR technical report; they do not describe the weights that were released. The proposal inherited them from the paper and assumed they were available.

A subcortical *training grid* exists upstream (`tribev2/grids/run_subcortical.py`, which would use `MaskProjector(mask="subcortical")` and the Harvard-Oxford atlas), but **no subcortical checkpoint has been published.** Training one would require the four source fMRI datasets (Algonauts2025, Lahner2024, Lebel2023, Wen2017) and a compute budget far outside a B.Sc. project on free-tier GPU.

### Consequence

Objectives (ii)–(vi) cannot be executed on the amygdala. This is not recoverable by better engineering. Two options exist:

- **(a) Train the subcortical grid.** Not feasible: requires the raw fMRI corpora and industrial compute.
- **(b) Amend the observable to what the instrument actually measures.** Feasible, and already what the code does.

**Recommendation: (b).**

### The amended observable

The implementation already computes an asymmetry between two *cortical* ROI unions (`app/services/roi.py:51-75`), resolved via the HCP MMP1.0 (Glasser) parcellation:

- **Affective-salience (cortical proxy):** OFC, pOFC, p24, a24, TGd, TE1a, TE1p, IFSa, IFSp, AAIC
- **Deliberative-control:** 46, a9-46v, p9-46v, 11l, 13l, d32, p32, a10p, p10p, 10pp

This is a defensible construct, orbitofrontal and anterior cingulate cortex, temporal pole and agranular insula are genuinely affective-salience regions, and the DLPFC/frontopolar set is genuinely deliberative, but **it is not the amygdala, and the thesis must not call it that.** The nucleus accumbens and DMN ROIs from the proposal's §4.1 table are dropped: NAcc is subcortical and unavailable; DMN was never used in any computation.

The proposal's framing must change from *"we measure the amygdala hijack"* to *"we measure a cortical affective-salience vs deliberative-control asymmetry, as a proxy for the amygdala hijack, because the released instrument is cortical-only."* This is a weaker claim. It is also a true one, and the limitation is itself a reportable finding: **the first independent research application of TRIBE v2 establishes that the released checkpoint cannot support subcortical affective claims.** No published work states this.

---

## 2. The ratio form of NAA is undefined on real content

Eq. (4) presumes `A_amyg` and `A_PFC` are positive activations, so that `NAA ~ 1` means balance and `NAA >> 1` means affective dominance.

TRIBE v2 predicts **standardized** activation. ROI means therefore sit near zero and are negative roughly as often as positive. The ratio sign-flips or explodes, and is meaningless.

Measured, on real scans:

| Run | Ratio NAA defined |
|---|---|
| MI300X, n=40 | **4 / 40.** `a_aff` negative for 36/40 (mean −0.0563); `a_del` positive for 40/40 (mean +0.0958) |
| Colab T4, n=10 | **1 / 10** |

`compute_naa` correctly returns `UNDEFINED` in this regime rather than a misleading verdict (`app/services/naa.py:71-78`). The six demo presets never exposed this because they never went through the model.

**Amendment.** The observable becomes the signed difference (`compute_signed_naa`, `naa.py:99`):

```
NAA_signed = A_aff - A_del
```

This is always defined. The Landau field `H = alpha * NAA` requires only a signed scalar, not a dimensionless ratio, so the physics is unaffected, but `NAA_signed` carries the units of TRIBE's standardized output, so it is **not dimensionless**, and the proposal's "dimensionless scalar" language in the abstract and §4.1 must be corrected. `alpha` is then fitted in those units.

**A caution that must appear in the paper.** `NAA_signed` was negative for *every item in both runs* (n=50 total; range −0.2260 to −0.0220). The deliberative union sits above the affective union for all real content tested. There is magnitude variation but **no sign variation**, so the interpretive scheme in §4.1 ("NAA ≈ 1 balanced, NAA >> 1 amygdala dominance") has no empirical counterpart, and the classification bands in the code are sign-only for that reason (`naa.py:114-118`). A systematic offset of this kind across 50/50 items is more consistent with a fixed baseline difference between the two ROI unions than with content-driven variation, and the paper should say so.

---

## 3. The calibration returned a null result, twice

Both runs regressed `NAA_signed` against EmoBank writer-normalized arousal:

| Run | n | alpha_hat | 95% CI | train R² | holdout R² | p |
|---|---|---|---|---|---|---|
| MI300X | 40 | −0.1321 | [−0.9199, 0.6557] | 0.004 | −0.162 | n/r |
| Colab T4 | 10 | −0.4562 | [−2.8425, 1.9300] | 0.035 | −6.007 | 0.656 |

Both CIs straddle zero. Both holdout R² are negative, worse than predicting the mean. **`alpha_hat` is not distinguishable from zero, and the paper must not quote a value for it.** `data/alpha_hat.json` currently ships `alpha_hat: 0.5, source: "fallback"`, an uncalibrated default that must never be presented as an estimate.

### What the null does and does not establish

**It does not test the proposal's hypothesis.** The proposal calibrates against **NELA-GT-2021 source-level credibility** (§4.4, Eq. 15) and characterises NAA across **four manipulation categories** (§5.2). EmoBank arousal was a substitute of convenience, a small, freely available, per-sentence arousal rating set. It is not in the proposal at all.

So the honest statement is: *a proxy calibration against text arousal ratings returned a null; the proposal's actual calibration and category-contrast experiments have not yet been run.*

### Confounds, in order of suspicion

1. **Out-of-distribution stimuli.** TRIBE v2 was trained on naturalistic movie watching. We fed it single short sentences rendered by synthetic TTS (T ≈ 9 TRs). This is the largest confound and is fixable, the proposal's own design specifies 50–200 word passages, which are markedly closer to the training distribution.
2. **ROI specification.** `a_aff` sitting below baseline for 36/40 items is systematic, not noise. The cortical proxy union or the mean-pooling may be washing out the signal.
3. **Outcome mismatch.** EmoBank arousal is a human *text rating*, not a neural measure. Regressing a predicted neural asymmetry on a text rating tests a chain of two weak links.

---

## 4. Revised scope

### Where the work actually stands

Against the seven specific objectives (§2.3), audited against the code on 2026-07-16:

| # | Objective | Status |
|---|---|---|
| i | 1,500-item multimodal corpus, 4×375 | **MISSING**, the only builder is EmoBank (~40 items, no categories, text-only) |
| ii | Deploy TRIBE v2, NAA per item | **PARTIAL**, pipeline works end-to-end, zero errors; run on ~50 items, cortical-only, text-only |
| iii | NAA distribution, Cohen's d, KL, entropy | **MISSING**, zero lines of code |
| iv | alpha_hat via OLS on NELA-GT-2021, bootstrap, sensitivity | **PARTIAL**, competent OLS estimator with a passing self-test, but pointed at EmoBank not NELA; CI is analytic-t, not bootstrap; no beta_J sweep |
| v | Landau/Ising: m*, chi, F(m), phase boundary | **PARTIAL, closest to done.** Solver, free energy and susceptibility implemented and well tested (16 tests). Phase boundary map absent. |
| vi | Classifier validation: ROC/AUC/F1 | **MISSING**, zero lines of code; sklearn is a declared-but-unused dependency |
| vii | Ship the AMA | **PARTIAL**, batch CLI and checkpoint-resume work; report is a single-item PDF, not a corpus HTML report |

The physics core is real and tested. **The empirical spine, corpus, distributions, validation, does not exist.**

### Time remaining

The proposal's five-month timeline began in April. Month 5 is final writing. It is now mid-July: roughly **six to eight weeks of build time remain.** The 1,500-item *multimodal* corpus is not reachable in that window, VoxPopuli, FakeSV, C-SPAN, TED and LibriSpeech each need download, preprocessing and per-modality pipelines that do not exist, and the proposal's own estimate for video alone is ~14 GPU-hours per 375 items on top of that engineering.

### Proposed revision

**Drop the audio and video modalities. Keep everything else.**

| Proposal | Revised | Why |
|---|---|---|
| 1,500 items, text + audio + video | 1,500 items, **text only**, 4×375 | Preserves N, the four categories, and every statistical objective. Multimodal is unreachable in the time remaining. |
| NAA = A_amyg / A_PFC, dimensionless | **NAA_signed = A_aff − A_del**, cortical proxies, in standardized-output units | The instrument is cortical-only and standardized. |
| RQ IV: MI per modality | MI on text features only (NRC valence, Flesch-Kincaid) | Follows from text-only. |
| Compute: Kaggle, 30 GPU-h/week | **Kaggle, as originally specified** | See below. |

At ~75 s/item, 1,500 text items is **~31 GPU-hours**, about one week of Kaggle's 30 GPU-h/week free tier, with 12-hour sessions and persistent `/kaggle/working/`. This is feasible.

**Note that the proposal specified Kaggle and the work drifted to free Colab**, whose quota is far tighter and whose sessions cap at ~1.5 hours, which is what the 40-item run died against, twice. Returning to Kaggle, as originally designed, removes the blocker that currently stalls the project. `batch_naa.py` already has per-item append/flush/resume, which is exactly what a 12-hour Kaggle session needs.

### What this thesis can honestly deliver

1. **A negative methodological finding of genuine value:** the released TRIBE v2 checkpoint is cortical-only and cannot support the subcortical affective claims that its own technical report describes. First independent application; nobody has published this.
2. **A reformulated, always-defined observable** and the empirical demonstration of why the ratio form fails on standardized encoder output.
3. **The proposal's actual experiment, run:** the four-category NAA contrast with KL divergence, Cohen's d and entropy, which has never been run and is the test most likely to show signal, because outrage-vs-abstract is a far larger contrast than per-sentence arousal, and 50–200 word passages sit much closer to TRIBE's training distribution than the TTS'd single sentences that produced the null.
4. **An honest calibration section** reporting the null, with confounds enumerated.
5. **The AMA**, shipped.

If the four-category contrast also comes back null, that is still a complete and publishable thesis: *a physically-grounded order parameter for media manipulation is not recoverable from the released TRIBE v2 checkpoint, and here is precisely why.* A null result rigorously obtained and honestly reported is a legitimate B.Sc. Physics contribution. A quoted `alpha_hat` that the data does not support is not.

---

## 5. Decisions required from the supervisor

1. **Approve the amended observable** (cortical affective-salience vs deliberative-control, signed) and the corresponding rewrite of the abstract, §4.1 and Eq. (4)., *blocking*
2. **Approve dropping audio and video**, and the corresponding rewrite of §5.2, §5.6 and RQ IV., *blocking*
3. **Confirm the null is reported as the calibration result**, with no `alpha_hat` quoted., *blocking*
4. Confirm the four-category contrast (§5.2) is the priority experiment for the remaining GPU budget.

---

## 6. Corrections already applied

- **`apps/web/src/components/explainers/ScientificDisclaimer.tsx`** (public site, monarch-4iy.pages.dev) claimed *"Validation is convergent (SemEval-2020 Task 11)"* and *"alpha-hat is a heuristic field-scale estimate calibrated on NELA-GT-2021 source-level credibility scores."* **Neither is true**, no validation code exists, and `alpha_hat` is the 0.5 fallback. Corrected on 2026-07-16 to state the cortical-only limitation, the uncalibrated `alpha_hat`, and the null. **Not yet redeployed.**

## 7. Outstanding corrections

- **`app/services/landau.py:90-93`** records that the product paper's Eq. (5) coefficients (`a = 1−beta_J`, `b = beta_J³/3`) do not derive from its own self-consistency Eq. (4) and leave the plotted minimum off the marked `m*`. The code supersedes the paper with `a = (1−beta_J)/2`, `b = 1/12`. **The thesis Eq. (10) has the same defect and must be corrected to match the code.**
- `data/alpha_hat.json` ships `source: "fallback"`. It must never be presented as calibrated.
- `app/utils/checkpoint.py` (`BatchCheckpoint`) is dead code, imported nowhere.
