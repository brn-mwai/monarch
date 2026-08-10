# Paper 2 skeleton

> **A cortical-proxy observable for emotionally manipulative media: an instrument, a
> 400-item corpus, a confounded separation, and an unidentified coupling**

The scan is complete and verified, so sections 4 and 5 are no longer stubs: they are written
from `services/inference/data/final/rq_answers.json`, `field_bound.json` and
`power_statement.json`, and from no other source. Section 6 reports that the coupling is
unidentified rather than null, which is a different claim and a weaker one.

Every number below is quoted from an artifact and is re-derivable by the script named beside
it. No number is carried over from a partial run.

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
  edge case: across the full corpus it is undefined for 69 of 400 items, 17.25%.
- **Signed form** `A_aff - A_del`, defined everywhere, which is why it carries the analysis.

State plainly here, not in a footnote: this is a **cortical proxy**. The checkpoint is
cortical-only. It is never called the amygdala.

## 3. Instrument and corpus design

- The cascade: text to speech, word timings, text and audio embeddings, encoder, activation.
- The checkpoint's facts taken from the artifact, not the folder name: depth, subject
  handling, and that the loader forces the average-subject configuration.
- Corpus: 400 items, four categories of 100, length-matched. Mean word counts are 167.4
  fear-activating, 163.5 high outrage, 163.7 neutral, 162.2 reward-hook, with sd between
  10.2 and 12.8, so length is not the confound.
- **Not source-balanced, and the paper must not claim it is.** Each category is drawn from
  exactly one source: fear-activating from ISOT-fake, high outrage from SemEval-2019 Task 4,
  reward-hook from Webis-Clickbait-17, neutral from PubMed and ISOT-true. Category and
  provenance therefore cannot be told apart, and this is stated in section 4 before any
  interpretation of the separation, not deferred to limitations.
- Category definitions and how items were assigned.
- What was stripped to prevent leakage, and why: the ISOT True/Fake split leaks through the
  Reuters wire dateline, and near-perfect separation on this construct is far more likely an
  artifact than a discovery.

## 4. Measurement

Reports, and nothing beyond them. Source: `scripts/analyze_corpus.py` into
`data/final/rq_answers.json`.

- 400 rows scanned and verified row-for-row against the source on text, category and id by
  `scripts/verify_scan_output.py`. Ratio undefined for 69.
- RQ II: `F = 15.779`, `p = 1.035e-09`, `eta^2 = 0.1068` across four categories, n = 400.
- The power statement alongside, always: smallest detectable `eta^2` 0.0268, smallest
  detectable AUC 0.5916, at alpha 0.05 and power 0.80. The observed effect is roughly four
  times the smallest the design could detect.
- RQ I: `AUC = 0.6274` as the headline, against the pre-scan `manipulative` label. F1 is
  reported but labelled, since its threshold is fitted in sample.
- Effect size against neutral, per category: fear-activating `d = 0.9389`, reward-hook
  `d = 0.3188`, high outrage `d = 0.0300`.

Three readings the data forces, in this order:

1. **The confound comes first.** The separation is between corpora. It cannot be attributed
   to framing rather than provenance.
2. **The separation is one category.** High outrage does not separate from neutral, and it is
   the category the proposal expected to separate most. The one argument against a pure
   source artifact is that high outrage has its own distinct source and still does not
   separate.
3. **Every category mean is negative**, so deliberative activation leads throughout. The
   instrument does not find affective dominance anywhere in this corpus.

Readings were fixed in advance in `docs/POST-SCAN-RUNBOOK.md` and are not revised after
seeing the numbers.

## 5. The physics

- Field mapping `h = alpha X`, with the observable taken from predicted activity rather than
  chosen.
- Free energy at each category's measured mean, swept over `alpha`, never fitted.
- Susceptibility across the measured range.
- The measured spread fed into Paper 1's bound via `scripts/field_bound.py`: `dX = 0.1241`
  over all 400 rows gives `alpha >= 4.2938` at `beta_J = 2`. Figures from partial runs are
  superseded and none may be quoted.

## 6. Calibration: unidentified, not null

`scripts/calibrate_alpha.py` with bootstrap intervals. On 400 items the interval no longer
straddles zero, so the earlier null reading is withdrawn. It is not replaced by a detection:

- Held-out `R^2` is negative, so the fit does not predict data it has not seen.
- The estimate scales inversely with `beta_J`, which this study does not measure.

The honest statement is that the coupling is **unidentified**. **No `alpha_hat` is quoted as
a point value anywhere in this paper**, and the bound in section 5 is the only quantitative
claim the calibration supports.

## 7. What a confounded separation and an unidentified coupling still constrain

The section the paper exists for, and its argument has changed with the data.

The measurement does not establish that framing moves the observable, because category is
confounded with source. It does establish a spread, and a spread is what the bound consumes:
combined with Paper 1, any study proposing this mechanism must supply a coupling of at least
`h_c(beta_J) / dX`, which at `beta_J = 2` is 4.2938. That constraint survives the confound,
because it depends on the measured range of the observable and not on why the range arises.

The negative result that does survive cleanly is narrower and worth stating in its own
sentence: on this corpus, at this power, the observable does not separate high-outrage
content from neutral content.

## 7b. Session reliability

Reported before the limitations, not inside them, because it is a measurement rather than a
caveat. A second GPU session rescanned 375 of the 400 items with identical text, code and ROI
definitions. Source: `scripts/test_retest.py` into `data/final/test_retest.json`.

- Agreement on `NAA_signed`: `r = 0.8812`, `ICC(2,1) = 0.8757`, `sd of differences = 0.01006`,
  which is 47.5% of the between-item sd. ICC is quoted alongside `r` because a session that
  shifted every score by a constant would still correlate perfectly.
- **The separation replicates.** Second session on the shared items: `eta^2 = 0.0839`,
  `F = 11.328`, `p = 3.988e-07`. First session on the same items: `eta^2 = 0.1054`,
  `F = 14.576`, `p = 5.397e-09`. Both clear the detectable floor of `0.0268`. The second is
  about a fifth smaller, the attenuation additional measurement error produces.
- **Direction flips for 49 of 375 items, 13.1%.** No per-item verdict is therefore stated
  anywhere in the paper.

Neither session is corrected toward the other and they are not averaged, since an average
would carry a precision neither run has.

## 8. Limitations

1. Cortical proxy, not a subcortical measurement. The checkpoint cannot speak to the
   structure the proposal originally named.

2. Single-session scores are noisy: ICC `0.8757`, session sd 47.5% of between-item sd.
   Category-level conclusions survive this, per-item ones do not.
2. Predicted activation is not measured activation. Whether the encoder tracks real cortex is
   Paper 3's question, and until it is answered this instrument measures a model's output.
   A published audit reports the released average-subject checkpoint anti-correlated with
   cortex, and replicating that is unfinished work.
3. Category is confounded with source dataset. This is the dominant limitation and it is
   stated in section 4 as well as here.
4. Average-subject configuration, forced by the loader.
5. Mean-field, single population, static field, binary opinion.
6. Corpus is English-language and drawn from specific sources; the spread is a property of
   that corpus, not of media in general.

---

## Order of work

Sections 1 to 3 and 7 to 8 can be drafted straight from the thesis chapters, which already
contain them. Sections 4 to 6 are transcriptions of verified artifacts and must be checked
against `rq_answers.json`, `field_bound.json` and `power_statement.json` at draft time rather
than against this file, which is a plan and not a source.
