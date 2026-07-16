# Monarch, Roadmap to Submission

**Student:** Brian Mwai (1050555) | **Supervisor:** Dr. Songa Mutambi
**Baseline date:** 2026-07-16
**Companion documents:** `PROPOSAL-AMENDMENT.md` (the three decisions this plan depends on)

Weeks are relative to the baseline. **The absolute submission deadline is not yet
fixed in this document and must be confirmed with the supervisor at Gate 0**, as
it determines whether W6-W8 is a writing phase or a compression phase.

---

## How to read this

Every week ends in a **gate**: a binary, checkable artifact. Not "worked on the
corpus" but "corpus.csv exists, 1,500 rows, length balance under 15%". A gate
either passed or it did not. This is what makes progress followable, and it is
what lets a slip be seen in week 2 rather than week 6.

Two gates are **kill gates** (G0, G2). If they fail, the plan changes rather
than the schedule slipping. They are marked.

---

## The critical path

```
G0 sign-off ──> G1 corpus ──> G2 pilot ──> G3 full scan ──> G4 analysis ──> G5 writing
   (blocking)      (no GPU)     (1 GPU-h)     (31 GPU-h)      (no GPU)
                                   ^
                                   └── kill gate: decides what RQ I and II say
```

Only G3 needs meaningful GPU. Everything downstream of it is free, which is why
G3 must not slip: it is the only step that cannot be compressed.

---

## W0 (this week), Gate 0: supervisor sign-off. BLOCKING, KILL GATE

Nothing downstream is worth doing until this closes. Send
`PROPOSAL-AMENDMENT.md` and get a decision on three points:

1. **Amend the observable** to the cortical affective-salience vs
   deliberative-control asymmetry, signed. The released TRIBE v2 checkpoint
   predicts 20,484 cortical vertices only; there is no amygdala and no nucleus
   accumbens, so proposal Eq. (4) cannot be executed as written.
2. **Drop audio and video.** Text only. Not reachable in the time remaining.
3. **The null is the calibration result.** No `alpha_hat` is quoted.

4. **Narrow RQ IV** to text features only. §5.6 specifies a per-modality
   comparison of `I(x; NAA)` across text, audio and video; dropping two
   modalities makes that sub-question unanswerable. See "What each research
   question can actually be answered with" below.

Also confirm at this gate:
- The absolute submission deadline.
- Target venue for the journal version.
- Whether the article requirement can be met as **submitted with a preprint
  posted**, since acceptance depends on reviewers rather than on the work.

**Gate 0 passes when:** written sign-off on all four, in email, on file.

**If Gate 0 fails** (supervisor rejects the amendment and requires the
amygdala): the project cannot proceed as designed, because no subcortical
checkpoint exists and training one needs the raw fMRI corpora plus industrial
compute. The fallback is to make the instrument limitation the *entire* thesis:
RQ I answered in the negative, at length, with the evidence already in hand and
no further computation required. Decide this at G0, not in week 5.

---

## W1, Gate 1: corpus built. No GPU

- Download NELA-GT-2021 (Harvard Dataverse), ISOT (UVic), Webis-Clickbait-17
  (Zenodo), PubMed abstracts. Upload as one Kaggle Dataset.
- Run `python scripts/build_corpus.py --inspect ...` FIRST against every file
  and fix any adapter whose declared columns do not match the real schema.
- Build: `--per-category 375 --out /kaggle/working/corpus.csv`
- Set up the Kaggle notebook (30 GPU-h/week, 12h sessions, persistent
  `/kaggle/working/`). Port from `notebooks/monarch_colab.ipynb`.

**Gate 1 passes when:** `corpus.csv` has 1,500 rows, 375 per category, length
balance reported under the 15% tolerance, and the dateline leak check reports 0.
The script exits non-zero if any of these fail, so the gate is the exit code.

**Risk:** if a category pool comes in under 375 after the 150-word filter, lower
`--per-category` for all four. Unequal n weakens the Cohen's d and KL estimates.

---

## W2, Gate 2: pilot scan. ~1 GPU-h. KILL GATE

**Do not run the full 1,500 before this.** Scan 40 items, 10 per category, and
answer one question: does NAA vary by category at all?

Compute the between-category vs within-category variance (one-way ANOVA, plus
Cohen's d against the neutral baseline). The prior is not encouraging: across
both existing runs, `NAA_signed` was negative for 50/50 items with magnitude
variation but no sign variation, which is more consistent with a fixed baseline
offset between the two ROI unions than with content-driven variation.

This pilot is the cheapest decisive test in the project. It costs ~1 GPU-hour
and it determines which way RQ I and RQ II are answered.

**Gate 2 passes when:** the pilot result is recorded either way. It does not
require a positive effect.

- **Separation present** (d > 0.3, between > within): proceed to G3. RQ I and II
  are answered as the proposal anticipated.
- **No separation**: still proceed to G3 (n=1,500 is what makes a null
  publishable rather than underpowered), but RQ I is now answered in the
  negative and chapters 5-6 are written from that premise in W3 rather than
  discovered in W7. **This is the single most valuable thing this gate buys:
  six weeks of warning.**

---

## W2-W3, Gate 3: full scan. ~31 GPU-h, the only real GPU cost

- `batch_naa.py --csv corpus.csv --text-col text --outcome-col category
  --out /kaggle/working/corpus_naa.csv`
- ~75 s/item x 1,500 = ~31 GPU-h = roughly one week of Kaggle quota.
- Per-item append/flush/resume already works, so a killed session loses nothing.
  Re-running the same `--out` resumes.
- **Known gap:** `batch_naa.py` carries one outcome column and drops the rest.
  Either scan with `--outcome-col category` and re-join on `text` for the
  credibility calibration, or add a `--carry-cols` flag first. Decide in W1.

**Gate 3 passes when:** `corpus_naa.csv` has one row per corpus item with
`naa_signed`, `a_aff`, `a_del` populated, and the undefined-ratio count is
recorded for the paper.

---

## W3-W4, Gate 4: analysis. No GPU, all of it

Everything here runs on the CSV from G3. This is objectives (iii), (iv), (vi)
and the remainder of (v), none of which currently exists in code apart from the
calibration estimator.

- **(iii)** Per-category distribution: mean, sd, skew, kurtosis, Cohen's d vs
  neutral, KL divergence (KDE, Silverman bandwidth), Shannon entropy. **Built
  and tested** in `app/services/distribution.py`.
- **(iv)** Calibration on the NELA subset against `credibility`. Bootstrap CI
  and beta_J sweep are in `calibrate_alpha.py` and self-tested.
- **(vi)** ROC/AUC/F1/precision/recall against `manipulative`. **Built and
  tested** in `app/services/validation.py`. SemEval-2020 Task 11 needs a loader
  and is still outstanding.
- **(v)** Phase boundary map in (beta_J, NAA) space. The solver, free energy and
  susceptibility are done and tested; only the 2D sweep is missing.
- **§5.6** Kraskov k-NN mutual information for RQ IV. **Zero lines exist.**
- **(vii)** Corpus-level report. Currently the report generator emits a
  single-item PDF; the AMA needs the ranked table, per-category violins, and the
  free-energy atlas.

**Read AUC, not F1.** A synthetic null corpus run through
`analyze_corpus.py` returned `AUC=0.451` with `F1=0.735`: the F1 looks
respectable purely because the Youden threshold is fitted in-sample on a
balanced corpus. Quoting F1 alone would present a chance-level classifier as a
working one. `discriminates` keys off AUC for exactly this reason, and the
report records `threshold_fitted_in_sample: true`.

**Gate 4 passes when:** every number and figure that appears in either paper
exists as a file on disk, generated by a script that can be re-run.

**Do not skip the ROC leak check.** If AUC against the ISOT labels comes back
above ~0.95, suspect the wire dateline before believing the result. The corpus
builder strips it and verifies, but check the number, not the intention.

---

## W5-W8, Gate 5: writing

The thesis first, the journal version derived from it. Do not write them in
parallel: the journal version is a compression of a finished argument, and
compressing an argument that is still moving wastes both.

- **W5-W6:** thesis chapters 1-4 (intro, lit review, theory, methodology).
  Largely a rewrite of the proposal against the amendment, so this is the
  cheapest writing in the project and can start the moment Gate 0 closes,
  in parallel with the scan. **Chapters 1-4 do not depend on any result.**
- **W7:** thesis chapters 5-6 (results, discussion), structured as the four RQ
  answers in order. Full draft to supervisor.
- **W8:** revisions, final submission, code and data release.
- **W8+:** journal version compressed from the finished thesis, preprint posted
  at submission.

**Write chapters 1-4 during W2-W4 while the GPU runs.** The scan is wall-clock,
not effort. Leaving all writing to W5 wastes the three weeks in which the only
bottleneck is Kaggle's queue.

**Corrections that must land before submission** (tracked in
`PROPOSAL-AMENDMENT.md` §7):
- Proposal Eq. (10) is mathematically wrong. It writes `a = 1-betaJ`,
  `b = (betaJ)^3/3`, which do not derive from its own Eq. (7). Correct is
  `a = (1-betaJ)/2`, `b = 1/12`, which is what `landau.py:95` implements.
- The abstract's "dimensionless scalar" language is wrong for the signed NAA.
- `data/alpha_hat.json` ships `source: "fallback"`. Never present it as an
  estimate.
- `ScientificDisclaimer.tsx` was corrected on 2026-07-16 but is **not
  redeployed**.

---

## The deliverables

**One body of work, two write-ups.** Accomplish what the proposal set out,
answer RQ I-IV, then render the same science twice for two audiences:

1. **Project document (thesis).** CUEA format, full chapters, complete
   derivations, full methodology, negative results and confounds stated at
   length. The reader is an examiner checking rigour.
2. **Journal version.** The same result compressed to venue length. Lit review
   collapses to a paragraph, derivations to their results, methodology to
   reproducibility. The reader is a referee asking whether the claim is new and
   supported.

Same findings, same figures, same numbers. Different register. The journal
version is written *from* the thesis, after it, not in parallel.

*Venue:* the proposal names Physical Review E and Physica A. Physica A is the
realistic target for a text-corpus sociophysics result, and more so if the
result is null. Confirm at Gate 0.

*On "published":* peer review runs 3 to 9 months from submission, which no
undergraduate timeline can guarantee. What is controllable is **submitted, with
a preprint posted at submission**. A preprint is a real, citable, dated output
the day it goes up. Raise this at Gate 0 rather than miss it at week 8.

---

## What each research question can actually be answered with

This is the spine of both write-ups. Every gate above exists to service a cell
in this table.

| RQ | Question | Answerable? | Needs |
|---|---|---|---|
| I | Can TRIBE v2 activation serve as a physically grounded signature of manipulative content? | **Yes, and the answer is the thesis's main finding** | G3. Objective (vi) is built and tested |
| II | NAA distribution across categories, and the KL divergence between them? | **Yes** | G1 + G3. Objective (iii) is built and tested |
| III | How does the NAA field alter the Ising phase structure? | **Yes, in full, even under the null** | Objective (v), built and tested. Phase boundary map outstanding |
| IV | Mutual information between stimulus features and NAA? | **Partially, and RQ IV must be narrowed** | §5.6 Kraskov MI, **still zero code** |

**Only the scan stands between here and RQ I and RQ II.** As of 2026-07-16 the
analysis for both is implemented, tested, and driven by one command:

```
python scripts/analyze_corpus.py --csv corpus_naa.csv --naa-col naa_signed
```

It emits the objective (iii) and (vi) results as JSON and exits 2 when the index
does not discriminate. A non-zero exit there is a legitimate scientific result,
not a build failure.

### RQ I: the honest answer is the contribution

The answer cannot be a clean yes, because the instrument does not measure what
§4.1 says it measures: the released checkpoint is cortical-only, so the
amygdala-based construct is not computable. The answer is therefore about the
cortical affective-salience vs deliberative-control proxy, and it carries the
limitation with it.

That is not a failure to answer RQ I. It IS the answer to RQ I, and it is the
most novel thing in the project: this is the first independent research
application of TRIBE v2, and no published work states that the released weights
cannot support the subcortical claims the technical report describes. It belongs
in the results, not buried in limitations.

### RQ III: answerable in full regardless of the null

RQ III is a **theory** question. The mean-field derivation, the
self-consistency solution `m*(NAA)`, the susceptibility divergence at `T -> Tc`,
and the Landau free-energy landscape all stand on their own; they are already
implemented and covered by 16 tests.

The `alpha_hat` null limits one thing only: pinning the absolute field scale. So
rather than substituting a single calibrated `alpha_hat`, present the phase
structure **as a function of `alpha` across a plausible range**, and state
plainly that the data does not constrain it. The `beta_J` sweep already does
exactly this for social temperature. RQ III is answered completely; the honest
qualifier is that the coupling remains unconstrained by this corpus.

### RQ IV: must be narrowed, and the supervisor should be told

As written, RQ IV asks how much of the signature is accounted for by low-level
physical properties, and §5.6 specifies a **per-modality** comparison of
`I(x; NAA)` across text, audio and video. Dropping audio and video makes the
per-modality comparison unanswerable.

RQ IV survives in narrowed form: Kraskov k-NN mutual information between the
NAA index and **text** features only (NRC valence, Flesch-Kincaid grade), with
k=5 and B=1,000 bootstrap replicates as Table 2 specifies. The per-modality
sub-question is dropped. **This is a fourth decision for Gate 0**, alongside the
three in `PROPOSAL-AMENDMENT.md`.

---

## Standing rules for this project

1. **Report the null.** Do not quote an `alpha_hat` the data does not support.
2. **No fabricated data, ever.** No synthetic heatmaps, no padded passages, no
   claims in the UI or the paper that the code does not support.
3. **Kaggle, not Colab.** The proposal specified Kaggle for a reason; the drift
   to free Colab is what killed the 40-item run twice.
4. **Every number in either paper comes from a re-runnable script.**
