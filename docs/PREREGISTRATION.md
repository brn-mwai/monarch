# Pre-registration, 400-item corpus scan

Written **before** `corpus_naa.csv` exists. Committed on 2026-08-07, while the scan was
still blocked at the Kaggle session settings and no item had been measured. The git history
of this file is the evidence for that claim.

The point is narrow: a prediction written after seeing results is not a prediction. Whatever
the scan returns, this file fixes what was expected, what would count as being wrong, and
which analysis was chosen in advance.

---

## What is being measured

`NAA_signed = A_aff - A_del`, the difference between mean predicted activation over
cortical affective-salience ROIs and over deliberative-control ROIs, from TRIBE v2's
20,484-vertex output, mean-pooled over each item's predicted time course.

This is a **cortical proxy**. The released checkpoint does not predict the amygdala. Nothing
below is a claim about the amygdala or about any individual's brain.

Corpus: 400 items, 100 in each of four categories, length-matched to within 3.1%,
wire-agency mentions removed, sources balanced round-robin within each category.

---

## Predictions

### H1, primary: manipulative content scores higher than neutral

Pooling `high_outrage`, `fear_activating` and `reward_hook` against
`neutral_informational`, the manipulative pool has a **higher mean signed NAA**.

Direction is predicted, one contrast, decided now.

**Confidence: low.** Two prior calibration runs on a different corpus returned intervals
straddling zero. The reason for testing again is that those used single sentences of about
9 TRs against a model whose window is 100 TRs, badly out of distribution, while these
passages run 60 to 90 TRs, inside the operating range for the first time. That is a reason
for a different result, not a reason to expect one.

### H2: the ratio form of NAA is undefined for most items

More than half of the 400 items produce no usable value for `A_aff / (A_del + delta)`.

**Confidence: high.** TRIBE output is standardised, so an ROI mean sits below zero about
half the time, and on the 40-item EmoBank run the ratio was undefined for every item.

### H3: classification is weak

For manipulative versus neutral, **AUC below 0.70**, and the interval includes 0.5.

**Confidence: moderate.** Stated so that a strong result cannot be quietly reclassified as
expected. If AUC exceeds 0.80, the first response is to suspect leakage, not to celebrate:
the corpus mixes source datasets across categories by construction, and a classifier that
scores that well is more likely reading a source artifact than an effect.

### No prediction is offered on the ordering within the manipulative categories

There is no basis to rank outrage against fear against reward hooks. Any ordering that
appears is exploratory and will be reported as such.

---

## What would falsify each

| # | Falsified if |
|---|---|
| H1 | The manipulative pool's mean is at or below neutral's, or the contrast's confidence interval includes zero |
| H2 | The ratio is defined for 200 or more of the 400 items |
| H3 | AUC is at or above 0.70 with an interval excluding 0.5 |

H1 failing is the outcome the prior points at. It is reported as the result, with the power
statement below, not softened into "a trend".

---

## Analysis, fixed in advance

**Primary metric:** `naa_signed`. Chosen before the scan because the ratio form is expected
to be undefined for most items, which is H2.

**Primary test:** the pooled contrast in H1, Welch's t-test, two-sided, alpha 0.05.

**Secondary:** one-way test across all four categories; each manipulative category against
neutral with Holm correction for the three comparisons; Cohen's d and KL divergence against
the neutral baseline; AUC with the Youden threshold reported and labelled as fitted in
sample.

**Everything is computed by `scripts/analyze_corpus.py` and `scripts/build_corpus_report.py`,
both written and tested before the scan ran.**

---

## Power

At n = 100 per category, alpha 0.05 two-sided, 80% power:

- **Pairwise:** the smallest detectable effect is **d = 0.40**.
- **Across four categories:** the smallest detectable effect is **Cohen's f = 0.166**,
  which is eta-squared of about **0.027**.

Anything smaller than that, this design cannot see. A null is therefore a statement about
effects of at least this size and no smaller, and it will be written that way.

---

## Where the physics enters

The measured spread `dNAA` feeds the bound derived in `scripts/phase_boundary.py`:

```
alpha  >=  h_c(beta_J) / dNAA
```

At `beta_J = 2` the spinodal field is `h_c = 0.533`, so an observable spanning 0.5 units
requires `alpha > 1.07` before media could drive an opinion transition. **This holds whether
or not H1 survives**, which is why a null still produces a number rather than a shrug.

---

## Committed not to do

1. Quote a value for `alpha_hat`. Its interval straddles zero; `data/alpha_hat.json` ships
   `source: "fallback"`.
2. Regroup categories after seeing the values, or drop the pooled contrast in favour of
   whichever comparison happens to separate.
3. Drop items after seeing their NAA. Undefined rows are counted and reported, never removed.
4. Report F1 as the headline. A null corpus returned F1 = 0.735 at AUC = 0.451 because the
   threshold is fitted in sample.
5. Stop the scan early on a favourable partial result. All 400 items are scanned, and a
   killed session resumes rather than restarting.

---

## Deviations

Any departure from this document is recorded here with its reason, rather than by editing
the text above.

*(none yet)*
