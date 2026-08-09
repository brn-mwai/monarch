# Publication plan

Dr. Mutambi's standing requirement from the proposal defence: two published journal articles
besides the project document. This maps four candidates, of which two satisfy that
requirement and the third is the one most likely to be cited.

Physics sits in every one of them. The neural encoder is the thermometer; the physics is the
statistical mechanics of a coupled population under an external field, and what a measured
field value implies for it. A paper that is mostly about the encoder is not a physics paper.

**On timing, stated plainly:** what is controllable is *submitted plus a dated preprint*.
Review at Physica A runs three to six months, so no date below promises publication.

---

## The dissertation

> **Measuring the Invisible: a sociophysics framework for quantifying emotionally
> manipulative media content using predictive neural encoding — instrument, constraint,
> and a source-confounded separation**

The approved title, with the amendment carried in the subtitle rather than discovered in
Chapter 5. Requires supervisor sign-off on `docs/amendment/PROPOSAL-AMENDMENT.pdf` first.

**The subtitle changed on 2026-08-09.** It read "and null" while both prior partial runs
pointed that way. The completed 400-item corpus separates at `eta^2 = 0.1068`, so the null
wording would have been false. It is replaced by what the corpus actually supports, confound
included. The amendment PDF still carries the old wording and needs this correction before it
is sent.

---

## Paper 1 — theory

> **Bounding the external field in mean-field opinion dynamics: what any content observable
> must satisfy to drive a transition**

**Independent of the scan.** Every result is analytic or CPU-computed, so this can be drafted
while the GPU run is still queued, and it stands whatever the scan returns.

**The gap.** Social Ising studies carry an external field `h` that is assigned by hand and
never measured. The literature can therefore show a population tipping without establishing
that any real influence is strong enough to tip it.

**The contribution.** For any observable `X` used as a field, `h = αX`, no media-driven
transition is possible unless

```
α  ≥  h_c(βJ) / ΔX
```

This inverts the usual procedure. Rather than fitting `α` and hoping it clears zero, it
states what `α` would have to be for the mechanism to work at all, and it applies to any
candidate field observable, not only to this project's index.

**Contents.** Mean-field Ising and the self-consistency condition; the Landau expansion with
coefficients derived rather than asserted; the second-order transition and the spinodal;
numerical recovery of the exact exponents `β = 1/2`, `γ = 1`, `δ = 3` as a check on the
solver; the bound; a screening criterion others can apply before collecting data.

**Status.** Drafted at `docs/paper1/paper1.tex`, compiling to 11 pages with no undefined
references. Figures are vector, and every number is generated from `phase_boundary.json`
rather than typed. Unaffected by the scan. Remaining: a deeper novelty search than the four
papers already checked.

**Venue.** Physica A, European Physical Journal B, or Journal of Physics: Complexity.
Preprint to arXiv physics.soc-ph on submission day.

---

## Paper 2 — the instrument and the corpus

> **A cortical-proxy observable for emotionally manipulative media: an instrument, a
> 400-item corpus, and a source-confounded separation**

**The scan is done, and it changed this paper.** The old subtitle said "a null result". The
corpus does not give a null. It gives a separation the design was powered to detect, carried
almost entirely by one category, inside a design where category cannot be told apart from
source dataset.

**What the corpus says.** All 400 items scanned and verified. RQ II separates at
`F = 15.779`, `p = 1.035e-09`, `eta^2 = 0.1068`, against the `0.0268` the design was powered
to detect; power at the observed value is 1.0. RQ I gives `AUC = 0.6274` against the label
`manipulative`, clearing the detectable `0.5916`, with power 0.961.

**Where the separation comes from.** Welch tests against the neutral baseline:
fear-activating `d = +0.939` at `p = 3.283e-10`, reward-hook `d = +0.319` at `p = 0.025`,
high outrage `d = +0.030` at `p = 0.832`. Outrage does not separate at all, which is the
category the proposal expected to separate most.

**The confound, stated first rather than buried.** Each category is drawn from exactly one
source: fear-activating from ISOT-fake, high outrage from SemEval-2019-Task4, reward-hook
from Webis-Clickbait-17, neutral from PubMed and ISOT-true. So the separation is between
corpora and cannot be distinguished from a separation between framing styles. Length is
controlled and is not the confound: category word counts are 167.4, 163.5, 163.7 and 162.2
with standard deviations near 11. Provenance is the uncontrolled variable.

The one piece of evidence against a pure source artifact is internal: high outrage comes from
its own distinct source and does not separate. A separation driven only by provenance would
be expected to move every category.

**What the paper can therefore claim.** That the index separates these four corpora at a
measured effect size, with the power statement attached; that the separation is concentrated
in one category; and that the design cannot attribute it to framing. Not that the index
detects manipulation.

**The physics still works, and now on measured numbers.** The spread over the full corpus is
`dX = 0.1241`, giving `alpha >= 0.1693` at `beta_J = 1.102`, `1.6553` at `1.496` and `4.2938`
at `2.000`. The bound no longer rescues a null; it states what the coupling would have to be
for a spread of this size to move a population at all.

**Every category mean is still negative.** The deliberative network leads throughout. The
categories differ in how far below zero they sit, not in which side wins. No item set shows
emotional dominance in absolute terms.

**The ratio form fails on 69 of 400 items, 17.25%.** That is the methods note's number.

**Status.** Corpus complete and verified, analysis run, figures produced. Needs writing.

**Venue.** Physica A or Entropy.

---

## Paper 3 — the validation

> **Does an average brain predict any brain? Held-out validation of the released TRIBE v2
> average-subject checkpoint**

**The one most likely to be cited, and the one nobody has published openly. The completed
corpus made it more load-bearing, not less:** Paper 2 now reports a detected separation, and a
detected separation in predicted activity means nothing about brains until someone shows the
encoder tracks cortex at all.

**Why it exists.** Monarch runs the released checkpoint in its average-subject configuration,
because `tribev2/demo_utils.py:218` forces `average_subjects = True` at load. A commercial
lab has since published a zero-shot audit reporting that this configuration is anti-correlated
with real cortex: vertex `r = −0.0145` against a measured inter-subject ceiling of `+0.0508`,
negative in all seven Yeo networks and all four subjects. A companion paper reports that
averaged read-outs carry no more signal than deleting the subject term entirely.

That work is self-published by a company selling the per-subject alternative, uses four
subjects and one stimulus, and reports magnitudes near `r = 0.015` either way. It is a sign
claim, not an effect-size claim, and it has not been independently replicated.

**The contribution.** Replicate it. Compute vertex-level Pearson `r` for the checkpoint
against held-out subjects on public naturalistic fMRI, with a measured noise ceiling and
bootstrap intervals. Either the sign holds or it does not; both outcomes are publishable, and
either constrains every study built on this checkpoint.

**Feasibility.** No large GPU: the work is data preparation and evaluation discipline, not
compute. But the earlier claim here, that the checkpoint outputs "fsaverage5, the same surface
CNeuroMod and Algonauts publish", was half wrong and is corrected in `docs/paper3/PLAN.md`.
The checkpoint does emit fsaverage5, confirmed by `tribe-ckpt/config.yaml` (`mesh: fsaverage5`)
and the smoke test's `(T, 20484)` = 2 x 10242. The Algonauts 2025 public release is not a
surface: it is MNI-normalised and reduced to 1000 Schaefer parcels, CC0 via CONP. A projection
step is therefore required, and parcel-level results may not be compared directly with the
audit's vertex-level `r`, because averaging within a parcel cancels independent noise and
raises correlations on identical data.

**Status.** Evaluation core built and tested (`app/services/encoder_validation.py`,
`app/services/parcellation.py`); data acquisition not started. Estimated three to five days,
most of it alignment and preprocessing.

**Venue.** Imaging Neuroscience, or NeuroImage as a brief communication.

---

## Optional short note

> **Ratio observables over standardised encoder output are undefined on real content**

A methods note. Encoder output is z-scored, so a denominator built from an ROI mean sits below
zero for a large fraction of items and the ratio sign-flips or explodes. Evidenced at 40/40 on
the EmoBank run and again in the corpus scan. Useful to anyone defining an index over these
models. Two pages.

---

## What is deliberately not a paper

**The cortical-only checkpoint finding.** Novel and unpublished, but it is neuroscience
tooling with no physics in it. It belongs in Paper 2's methods, and in Paper 3's framing.

**A software-venue article** (JOSS, SoftwareX). It would be accepted and would contain no
physics, so it does not meet the two-article requirement. The apparatus is released alongside
the papers as the reproducibility artifact.

---

## Order

Paper 1 first: it depends on nothing and guarantees one submission whatever the scan returns.
Paper 3 second if the validation runs, because it is the strongest result available.
Paper 2 last, since it consumes both.
