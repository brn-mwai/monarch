# Paper 2 skeleton

> **A cortical-proxy observable for emotionally manipulative media: an instrument, a
> 400-item corpus, and a null result**

Sections 1 to 3 and 7 to 8 do not depend on the scan and can be written now. Sections 4 to 6
are stubs on purpose. **No sentence describing a result may be drafted before the result
exists**, because prose written in advance sets an expectation the data is then read against.

Venue: Physica A, or Entropy.

---

## 1. Introduction (data-independent)

The argument in order:

1. Media is routinely modelled as an external field on a population of coupled agents.
2. That field is almost never measured. Paper 1 states what any candidate observable must
   satisfy: `alpha >= h_c(beta_J) / dX`.
3. This paper supplies the missing half: an observable computed from content, a corpus on
   which its spread is measured, and the resulting constraint.
4. The physics stays in front. The encoder is the thermometer, not the subject.

## 2. The observable (data-independent)

Definition of NAA from predicted cortical activation, and the two forms:

- **Ratio form**, undefined whenever either network mean sits below baseline. This is not an
  edge case: it was undefined for 7 of the first 50 items scanned, 14%.
- **Signed form** `A_aff - A_del`, defined everywhere, which is why it carries the analysis.

State plainly here, not in a footnote: this is a **cortical proxy**. The checkpoint is
cortical-only. It is never called the amygdala.

## 3. Instrument and corpus design (data-independent)

- The cascade: text to speech, word timings, text and audio embeddings, encoder, activation.
- The checkpoint's facts taken from the artifact, not the folder name: depth, subject
  handling, and that the loader forces the average-subject configuration.
- Corpus: 400 items, four categories of 100, length-matched and source-balanced.
- Category definitions and how items were assigned.
- What was stripped to prevent leakage, and why: the ISOT True/Fake split leaks through the
  Reuters wire dateline, and near-perfect separation on this construct is far more likely an
  artifact than a discovery.

## 4. Measurement (STUB, needs the full scan)

Reports, and nothing beyond them:

- Rows scanned, ratio values undefined, per-category descriptives.
- RQ II: separation across categories, `F`, `p`, `eta^2`.
- RQ I: AUC as the headline. F1 reported but labelled, since its threshold is fitted in
  sample.
- The power statement alongside, always: smallest detectable `eta^2` 0.0268, smallest
  detectable AUC 0.5916, at alpha 0.05 and power 0.80.

Readings are fixed in advance in `docs/POST-SCAN-RUNBOOK.md` and are not to be revised after
seeing the numbers.

## 5. The physics (STUB, needs the measured spread)

- Field mapping `h = alpha X`, with the observable taken from predicted activity rather than
  chosen.
- Free energy at each category's measured mean, swept over `alpha`, never fitted.
- Susceptibility across the measured range.
- The measured spread fed into Paper 1's bound via `scripts/field_bound.py`. On the first 50
  rows this gave `alpha >= 6.6563` at `beta_J = 2.000`; the reported figure comes from all
  400 and no other source.

## 6. Calibration (STUB)

`scripts/calibrate_alpha.py` with bootstrap intervals. If the interval straddles zero, that
is the result. **No `alpha_hat` is quoted as a point value anywhere in this paper.**

## 7. What makes a null publishable (data-independent)

The section the paper exists for. A null calibration on its own says only that nothing was
detected. Combined with the bound it says the coupling would have to exceed
`h_c(beta_J) / dX`, and that the measurement excludes that range at the stated power. That is
a constraint on every study that proposes this mechanism, and it is available to any study
that reports a spread alongside its null.

## 8. Limitations (data-independent)

1. Cortical proxy, not a subcortical measurement. The checkpoint cannot speak to the
   structure the proposal originally named.
2. Predicted activation is not measured activation. Whether the encoder tracks real cortex is
   Paper 3's question, and until it is answered this instrument measures a model's output.
3. Average-subject configuration, forced by the loader.
4. Mean-field, single population, static field, binary opinion.
5. Corpus is English-language and drawn from specific sources; the spread is a property of
   that corpus, not of media in general.

---

## Order of work

Sections 1 to 3 and 7 to 8 first, while the scan runs. Sections 4 to 6 only once
`corpus_naa.csv` holds 400 verified rows and the runbook's Phase C has been run.
