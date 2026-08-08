# Post-scan runbook

Everything that happens once the corpus scan finishes, in order, with the command for each
step and the condition that decides whether it passed.

Written while the scan was still running, deliberately. The readings in Phase C commit to
how each outcome is interpreted **before** the numbers exist, so the interpretation cannot be
chosen to suit whatever arrives. Nothing below may be edited after seeing the full CSV except
to record what actually happened.

All commands run from `services/inference/`.

---

## Phase A. Finish the scan

The corpus is 400 items. Runs are capped by `--limit` so each ends inside the 12 h session
cap and publishes its output; a killed session is not known to publish anything.

| run | version | `--limit` | new items | status |
|---|---|---|---|---|
| 1 | v34 | 50 | 50 | done, `COMPLETE` |
| 2 | v35 | 350 | 300 | running |
| 3 | pending | 400 | 50 | not started |

**A1. When a run ends, download and check it.**
```bash
kaggle kernels output brianmwa/monarch-corpus-scan -p <dir>
```
Pass condition: `rows scanned: N / 400` appears in the log and `corpus_naa.csv` has N rows.

**A2. Verify the rows are genuine before trusting them.**
```bash
python scripts/verify_scan_output.py --corpus data/corpus.csv --scan <dir>/corpus_naa.csv
```
Exit 0 means every scanned row matches the corpus on `text`, `category` and `id`, values are
distinct, and `naa_signed` agrees with `a_aff - a_del`. Do not tighten the tolerance: three
independently rounded six-decimal columns disagree by up to 1.5e-6, and a 1e-6 threshold
rejected 4 of the 50 sound rows in run 1.

**A3. Republish the partial so the next run resumes instead of rescanning.**
```bash
kaggle datasets version -p <dir-with-corpus_naa.csv> -m "after run N" -t
```
The kernel already lists `brianmwa/monarch-corpus-naa-partial` in `dataset_sources`.

**A4. Raise `--limit` in the scan cell, then push.** Never push while a run is live: an API
push auto-runs and cancels whatever is running.

Time: 1.5 to 9 h per run, dominated by items scanned.

---

## Phase B. Freeze the corpus

**B1.** Confirm 400 rows, four categories of 100, no duplicate `id`.

**B2.** Record how many ratio NAA values are undefined. This is a result in its own right and
feeds the methods note on ratio observables over z-scored encoder output. It was 7 of 50 in
run 1.

**B3.** Commit the final `corpus_naa.csv` and publish it as a dataset version. This file cost
GPU hours that cannot be cheaply repeated; it is the artifact everything downstream reads.

Time: 15 minutes.

---

## Phase C. Analysis, objective (vii)

**C1. The power statement, unchanged from what is already committed.**
```bash
python scripts/power_statement.py --out data/power_statement.json
```
Already produced for this design: smallest detectable eta^2 `0.0268`, smallest detectable AUC
`0.5916`, at alpha 0.05 and power 0.80.

**C2. RQ I and RQ II.**
```bash
python scripts/analyze_corpus.py \
  --csv data/corpus_naa.csv --naa-col naa_signed --category-col category \
  --out data/rq_answers.json
```
Exit 0 means the index discriminates, exit 2 means it does not. Both are results.

**C3. The report and its figures.**
```bash
python scripts/build_corpus_report.py --csv data/corpus_naa.csv --out-dir data/report
```

**C4. The bound, which is what makes a null publishable.**
```bash
python scripts/field_bound.py \
  --scan data/corpus_naa.csv --report data/paper1/phase_boundary.json \
  --out data/field_bound.json
```
Reads the observable's measured spread from the scan and the spinodal from the solver, and
reports the coupling a media mechanism would need. On the first 50 rows, `dX = 0.0801` gave
`alpha >= 6.6563` at `beta_J = 2.000`. Run it on the full corpus before quoting any figure.

**C5. Calibration, on CPU, separate from the scan.**
```bash
python scripts/calibrate_alpha.py \
  --csv data/corpus_naa.csv --naa-col naa_signed --outcome-col credibility \
  --bootstrap 10000 --out data/calibration.json
```

### Readings committed in advance

- **AUC is the headline, not F1.** The threshold is fitted in sample, which inflates F1 while
  AUC stays honest.
- **AUC below 0.5** means the index runs opposite to the proposal's hypothesis. Report it as
  measured. Do not flip the sign to recover a positive number.
- **AUC at or above 0.95** is treated as a leak, not a discovery, until the source of the
  separation is identified.
- **Separation not significant at 400 items** is a null, and is reported with C1's numbers
  attached: effects above eta^2 0.0268 are excluded, smaller ones are not addressed.
- **Any alpha_hat interval straddling zero** is the result. It is never quoted as a point
  value, and no alpha_hat appears in any output, figure or chapter.
- **The observable is a cortical proxy.** It is never called the amygdala anywhere.

Time: about 1 hour.

---

## Phase D. The papers

**D1. Paper 1, theory, independent of the scan.** Draft complete at `docs/paper1/paper1.tex`,
compiling to 10 pages.
```bash
python scripts/phase_boundary.py --out-dir data/paper1 --formats png,pdf,svg
python scripts/paper1_numbers.py --report data/paper1/phase_boundary.json \
  --out data/paper1/numbers.tex
cd docs/paper1 && latexmk -pdf paper1.tex
```
Remaining: the bibliography needs the sociophysics literature that assigns the field by hand,
each reference verified to exist, plus an affiliation. Estimate 3 to 5 hours.

**D2. Paper 2, the instrument and the corpus.** Consumes Phase C. Its central move is feeding
the corpus's measured spread `dX` into Paper 1's bound, which converts a null calibration into
the quantitative constraint `alpha >= h_c(beta_J) / dX`. Run 1's 50 items gave a spread of
`0.0801`; the final figure comes from all 400. Estimate 2 to 3 weeks of writing.

**D3. Paper 3, the validation.** Evaluation core is built and tested at
`app/services/encoder_validation.py`: per-vertex Pearson r, leave-one-subject-out noise
ceiling, seeded bootstrap intervals. Remaining work is data preparation, not compute: obtain
public naturalistic fMRI on fsaverage5, align it to the checkpoint's output, run the
evaluation. Estimate 3 to 5 days.

---

## Phase E. Housekeeping, easy to forget

1. Rotate the HF token in the private dataset once the last run finishes.
2. Send the amendment email, `docs/amendment/EMAIL.txt` plus the compiled PDF. Gates
   supervisor sign-off on the dissertation title.
3. Update `docs/RUN-LOG.md` with each run's version, card, items and outcome.
4. Delete the intermediate partial datasets once the final CSV is committed.

---

## Traps that have already cost hours

1. Papermill echoes the failing cell's **source** into the log, so a progress marker found
   anywhere is not evidence the step ran. Read markers from stdout only, and only before the
   failure.
2. `kernels status` reports the last **finished** version, so a watcher can exit on a stale
   verdict while a run is alive. Liveness is reported correctly; the version's verdict is not.
3. A log is published only when a run finishes. Silence during a run is normal.
4. `machine_shape: gpuT4x2` is a request the scheduler may ignore. Five sessions running drew
   a P100 regardless, including one pushed through the API.
5. `quota_view()`'s JSON repr prints `totalTimeAllowed "21600s"` for a 108000 s allowance.
   Read the typed timedelta fields instead.
