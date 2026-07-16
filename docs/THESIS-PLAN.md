# What we are writing, and why

**Four-day writing plan.** Companion to `PROPOSAL-AMENDMENT.md` (the findings)
and `ROADMAP.md` (the schedule).

---

## Read this first: what the proposal actually promised

The proposal does **not** promise a positive result. It promises an instrument.
Three times, in its own words:

> "The primary deliverable is a functional **Asynchronous Measurement Apparatus
> (AMA)**: an offline batch-inference pipeline producing physics-grounded audit
> reports on arbitrary media corpora." (Abstract)

> "The AMA is the primary deliverable of this project, **not a proposed future
> application and not a conceptual description**." (§5.8)

> "It proposes a thermometer, and delivers it as working, open-source code that
> can be run today." (§6)

This governs everything below. **A thermometer that reads zero is still a
delivered thermometer.** The null does not fail the proposal. Failing to ship
the AMA would.

The thesis is therefore **the proposal, executed, with one amendment**. It is not
a pivot to a different project, and it must not read as one.

## The argument, in one sentence

> We built the sociophysics framework and the measurement apparatus the proposal
> specified, discovered during deployment that the released TRIBE v2 checkpoint
> constrains the observable to a cortical proxy, answered the research questions
> within that constraint, and shipped the instrument.

Every chapter serves that sentence. If a paragraph does not, cut it.

## What the document delivers, in the proposal's own order of priority

1. **The AMA, shipped and working.** Objective (vii). The primary deliverable.
   Codebase, corpus manifest, and one complete example report over the corpus.
   **This is the thing that must exist on submission day.** If time runs out,
   time runs out of the analysis, never out of this.
2. **The framework, derived in full.** Objectives (iv) and (v). The Landau /
   Ising treatment is implemented and tested and stands independently of any
   empirical result.
3. **The research questions, answered.** RQ I to RQ IV, honestly, at whatever n
   is reached.

## The three empirical claims

Supporting the above, in descending order of confidence:

1. **The released TRIBE v2 checkpoint is cortical-only**, so the observable is
   constrained to a cortical proxy. Novel, unpublished, verifiable in five
   minutes. This is a **constraint on RQ I and a contribution in its own right**.
   It is not the thesis, and writing it as though it were would be a pivot away
   from the proposal.
2. **Ratio observables over standardized encoder output are undefined on real
   content.** Evidenced at 4/40 and 1/10. A general methodological point.
3. **The cortical proxy does not track manipulation.** The null, at whatever n
   the scan reaches.

Claims 1 and 2 are already evidenced by the runs on file. **Nothing in this
document is hostage to the scan finishing.**

---

## Why a null is the right thing to write

Three reasons. Give all three, in this order, in the viva.

**It is true.** The alternative is quoting an `alpha_hat` whose confidence
interval straddles zero, or calling a cortical proxy the amygdala. Both would
survive exactly until someone checked. There is no version of this project where
inventing the result is the better play.

**It is novel.** This is the first independent research application of TRIBE v2.
The limitation is not documented anywhere in the literature. A student who reads
a foundation model's technical report, checks it against the released weights,
and finds the gap has done the thing science is for.

**A rigorous null is a physics result.** This is the disciplinary norm, not a
consolation. Michelson-Morley measured nothing and is the most important
experiment of its century. The value of a null lies entirely in its rigour: an
underpowered null says nothing, a well-powered null with the confounds mapped
constrains what everyone after you needs to believe. That is why n, the
bootstrap CI, the eta-squared veto, and the confound list matter, and it is the
standard this document is held to.

**What it is not.** It is not a claim that the amygdala hypothesis is wrong, and
it must never be written as one. The instrument could not test it. The claim is
narrower and defensible: *this measurement, with this checkpoint, does not
recover that signal.* Overreaching here is the single easiest way to lose the
viva.

---

## The chapters

Chapters 1-4 are a rewrite of the proposal against the amendment. **They depend
on no result and can be written while the GPU runs.** Chapter 5 is the only
chapter that waits.

### Ch 1: Introduction
Straight from proposal §1, largely intact. Sociophysics needs an empirically
grounded external field `H`; it has never had one; TRIBE v2 makes it tractable.

**Add one paragraph at the end: the contribution, stated honestly.** That this
is the first independent application of TRIBE v2, that the released checkpoint
cannot support the proposed observable, and that the study reports the
reformulation and its empirical result. Say it in the introduction. An examiner
who meets the amendment for the first time in Chapter 5 will read it as a
retreat; one who meets it on page 3 reads it as the design.

### Ch 2: Literature Review
Proposal §3, essentially unchanged. BOLD physics, neural encoding models,
sociophysics (Ising, Galam, Castellano), emotional contagion, information theory,
the research gap. Cheapest chapter in the document.

### Ch 3: Theoretical Framework
Proposal §4, amended.

- **Eq. (4) is replaced.** `NAA_signed = A_aff - A_del` over cortical ROI
  unions. Derive why: TRIBE predicts standardized activation, ROI means sit near
  zero, the ratio sign-flips or explodes. State that the index is **no longer
  dimensionless** and carries the units of standardized output.
- **The ROI table is replaced.** Cortical HCP MMP1.0 parcels. Nucleus accumbens
  and DMN are dropped and the reason is given.
- **Fix Eq. (10).** The proposal writes `a = 1-betaJ`, `b = betaJ^3/3`. These do
  not derive from its own Eq. (7). Correct is `a = (1-betaJ)/2`, `b = 1/12`,
  from `artanh(m) ~= m + m^3/3`. This is what `landau.py` implements. **Fix it
  quietly in the derivation; do not flag it as an erratum.**
- Everything else (self-consistency, stability, susceptibility, free energy)
  stands as proposed. This is the strongest chapter and it is already correct.

### Ch 4: Methodology
Proposal §5, amended. Text-only corpus, four categories, the actual n. The TRIBE
cascade. Cortical ROI extraction. Signed NAA. The statistical, Landau and
validation methods. The AMA.

**State the length-matching and the dateline strip as design decisions**, with
the reasons. They are evidence of rigour and cost two paragraphs: passages are
length-matched because sequence length would otherwise confound category, and
the ISOT dateline is stripped because "(Reuters)" alone separates the classes.

### Ch 5: Results
Structured as the RQ answers, in order. The only chapter that waits on the scan.

- **5.1 RQ I: instrument characterisation.** The headline. The evidence table
  (config.yaml, n_outputs=20484, smoke test, Meta's demo notebook, both runs).
  The ratio undefined at 4/40 and 1/10. The reformulation. Then the classifier
  result: AUC, F1, precision, recall. **Report AUC as the headline, not F1** (a
  null corpus gives F1=0.735 at AUC=0.451 because the threshold is fitted
  in-sample; F1 alone would look like success).
- **5.2 RQ II: distribution across categories.** Per-category mean, sd, skew,
  kurtosis; Cohen's d vs neutral; KL divergence; entropy; and the separation
  test with eta-squared. Output of `analyze_corpus.py`.
- **5.3 RQ III: phase structure.** `m*(NAA)`, `chi(NAA)`, `F(m)`. **Present the
  phase structure as a function of `alpha` across a plausible range** and state
  that the data does not constrain `alpha`. The calibration null goes here:
  both runs, both CIs straddling zero, negative holdout R^2. **No `alpha_hat` is
  quoted anywhere in the document.**
- **RQ IV is out of scope.** One honest paragraph: the per-modality mutual
  information in §5.6 required audio and video, which were dropped, and the
  narrowed text-only version was not reached within the project timeline.

### Ch 6: Discussion
- What Claim 1 means for in-silico neuroscience: a technical report describing an
  architecture is not a warranty about released weights, and anyone building on a
  foundation model must verify the checkpoint rather than the paper.
- **Why the null, in order of suspicion.** (i) Out-of-distribution stimuli:
  TRIBE was trained on naturalistic movie watching and was fed TTS'd passages.
  (ii) ROI specification: `a_aff` sat below baseline for 36/40 items, which is
  systematic rather than noisy, and a signed NAA negative for 50/50 items with
  no sign variation looks more like a fixed baseline offset between two ROI
  unions than like content-driven variation. (iii) Outcome mismatch: EmoBank
  arousal is a text rating, not a neural measure.
- Limitations, stated before an examiner has to ask.
- What would be required: a subcortical checkpoint, which means the training
  grid, the four source fMRI corpora, and compute outside this project.

### Ch 7: Conclusion
The framework is derived, the apparatus is shipped, the research questions are
answered within the constraint the released checkpoint imposes. The contribution
is the instrument plus the documented limitation plus the honest empirical
result. Future work is the subcortical checkpoint.

---

## The AMA: objective (vii), the primary deliverable

Everything else in this plan is subordinate to this section. The proposal is an
instrument-delivery project and this is the instrument.

**Already working:** the offline batch CLI (`batch_naa.py`), per-item
checkpoint-resume, the TRIBE cascade, ROI extraction, signed NAA, the full
Landau analysis, and a single-scan PDF report with NAA gauge, `F(m)` curve,
`chi(NAA)` curve, ROI breakdown and methodology figure.

**Missing for the corpus-level report §5.8(iii):** the ranked NAA table over all
items, per-category violin plots, the free-energy atlas over category mean NAA,
and per-item flags against the ROC-optimal threshold. The single-item chart
machinery in `report_charts.py` already covers most of the drawing; this is
assembly, not new science.

**Also required at completion (§5.8 Outcome):** public release of the codebase,
the corpus manifest, and **one complete example report applied to the corpus**.
The example report is part of the deliverable, not a nice-to-have.

**Priority rule for the last four days.** If something has to give, it gives from
the analysis, never from the AMA. An unfinished scan with a shipped instrument
answers the proposal. A finished scan with no instrument does not.

---

## The journal version

Same argument, compressed, written **from** the finished thesis, not alongside
it. Lit review collapses to a paragraph. The derivation collapses to its
results. Methodology collapses to reproducibility.

**Lead with Claim 1**, because it is the only part that is genuinely new to a
reader who is not your examiner. The null is the second half of the paper.

Physica A is the realistic venue. Post the preprint at submission: it is a real,
citable, dated output on the day it goes up, and it does not wait on reviewers.

---

## Two rules while writing

1. **No `alpha_hat`. Anywhere.** Not in a table, not "for illustration", not in
   a figure caption. `data/alpha_hat.json` ships `source: "fallback"`.
2. **Never call the cortical proxy the amygdala.** Not once. The whole
   contribution is that the distinction is real.
