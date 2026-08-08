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
> and null**

The approved title, with the amendment carried in the subtitle rather than discovered in
Chapter 5. Requires supervisor sign-off on `docs/amendment/PROPOSAL-AMENDMENT.pdf` first.

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

**Status.** `scripts/phase_boundary.py` produces all six figures and the exponent check.
Missing: vector output for submission, and the prose.

**Venue.** Physica A, European Physical Journal B, or Journal of Physics: Complexity.
Preprint to arXiv physics.soc-ph on submission day.

---

## Paper 2 — the instrument and the corpus

> **A cortical-proxy observable for emotionally manipulative media: an instrument, a
> 400-item corpus, and a null result**

**Blocked on the scan.** This is the thesis compressed, with the physics kept in front.

**Contents.** The field mapping `h = α·NAA`, taking the observable from predicted cortical
activity rather than from a chosen constant; free energy at each category's measured mean,
swept over `α` and never fitted; susceptibility across the measured range; the measured
spread fed into Paper 1's bound, which turns a null calibration into a quantitative
constraint; then the measurement chapter — corpus design, length matching, source balancing,
the cortical-proxy limitation, the null with its power statement, AUC as the headline.

**What makes the null publishable.** `α ≥ h_c(βJ)/ΔNAA` converts "we did not detect a
coupling" into "the coupling would have to exceed this value, and the measurement excludes
that range".

**Status.** Instrument, corpus and analysis scripts done and tested. Needs `corpus_naa.csv`.

**Venue.** Physica A or Entropy.

---

## Paper 3 — the validation

> **Does an average brain predict any brain? Held-out validation of the released TRIBE v2
> average-subject checkpoint**

**The one most likely to be cited, and the one nobody has published openly.**

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

**Feasibility.** No large GPU. The checkpoint outputs fsaverage5, the same surface CNeuroMod
and Algonauts publish. The work is data preparation and evaluation discipline, not compute.

**Status.** Not started. Estimated three to five days, most of it alignment and preprocessing.

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
