# Execution plans

One plan per task. Each states what finishing means, how it is verified, and what has already
gone wrong. A task is done when its acceptance check passes, not when the work feels finished.

The failure protocol at the end applies to every plan and is the part that matters: fifteen
runs failed before one reached the scan, and the cost was never the fix, it was mistaking one
failure for another.

---

## The failure protocol

Applies to any run, local or on Kaggle. Steps in order, no skipping.

**1. Get the evidence before forming a theory.**

```
python scripts/watch_kaggle_run.py --slug brianmwa/monarch-corpus-scan --out data/diagnosis.json
```

It prints the terminal state, the failing cell, the matched signature, the markers actually
reached, how many items were scanned, and the recommended action.

**2. Trust stdout, not the traceback text.** Papermill echoes the failing cell's *source* into
the log. A progress marker found anywhere is not evidence the step ran. Twice a run was
reported as having patched tribev2 when the string came from the echoed cell. The watcher
reads markers from stdout only, and only from before the failure; do the same by hand.

**3. Name the failure before touching anything.** One line: what the machine did, not what it
should have done. If it does not match a known signature, say "unclassified" rather than
picking the nearest one.

**4. Find the cause, not the symptom.** Three cases from this project:

- `No module named 'neuralset'` was not a missing package. tribev2 was installed `--no-deps`,
  so six dependencies were missing and neuralset was merely the first import to fail.
- `exca.steps.base has no attribute 'NoValue'` was not a version guard problem. The guard was
  correct; a previous fix had silenced it instead of installing the version it asked for.
- `AssertionError: compute_type line not found` was not tribev2 changing. The patch was
  written against a local checkout while Kaggle clones from GitHub, where the value is
  already read from the environment and needed no patch at all.

**5. Fix at the right layer.** Prefer configuration to patching a dependency's source.
Prefer a tested module to a notebook cell. If the fix belongs in a cell, ask why it is not in
`scripts/`.

**6. Add the check that would have caught it.** Every fix ships with its test:
`test_notebook_syntax.py` after a broken heredoc, `test_script_imports.py` after a missing
`sys.path` line, `test_kaggle_bootstrap.py` after fp16 on a P100. This is the rule that turns
a loop into progress.

**7. Verify locally, then push once.** `pytest -q` must be green before any push. Never push
while a run is live: a push starts a new version and cancels the running one.

**8. Record it.** Append to `docs/RUN-LOG.md`: what was run, what came back verbatim, what it
means. Failures are never deleted after they are fixed.

---

## Task 1 — Run the 400-item scan to completion

**Done when** `corpus_naa.csv` holds 400 rows and the summary prints the defined/undefined
counts.

**Known arithmetic.** 204 to 227 s/item measured on a P100 at float32, so roughly 23 GPU-hours
against a 12-hour session cap and a 30-hour weekly quota. Two to three sessions. Not one.

**Steps.**
1. Push the notebook; confirm the run starts and reaches `[1/400]`.
2. Let it run until the session ends or it stops.
3. Download the partial `corpus_naa.csv`, publish it as a dataset, attach it to the next run.
4. Repeat until 400 rows.

**Acceptance.**
```
python -c "import csv;rows=list(csv.DictReader(open('corpus_naa.csv',encoding='utf-8')));\
print(len(rows), sum(1 for r in rows if r['naa']), sum(1 for r in rows if not r['naa']))"
```
400 rows, and the defined plus undefined counts summing to 400.

**Failure modes seen.** GPU out of memory (fixed, unverified past item 3), no internet in an
editor session, secret not attached to a pushed version, wrong accelerator enum, cancelled by
a concurrent push.

**Resume is not optional.** `batch_naa.py` matches on text and refuses to append when the
header differs, so the flags must be identical between sessions.

---

## Task 2 — Send the amendment email

**Done when** it is sent, with the PDF attached.

**Not blocked by anything.** Longest latency in the project and the only item waiting on a
person. Three blocking decisions cannot be resolved by working harder on the code.

**Add before sending:** two sentences on the external audit of the average-subject
checkpoint, flagged as unreplicated.

---

## Task 3 — Draft Paper 1

**Done when** a manuscript exists with six figures and the exponent table, and the preprint is
posted on submission day.

**Depends on no data.** This is the guarantee that one submission happens whatever the scan
returns.

**Steps.**
1. `python scripts/phase_boundary.py --out-dir data/paper1` — figures and `phase_boundary.json`
2. Add `--format pdf`; journals need vector, the scripts emit PNG
3. Write against `docs/FIGURES.md`, F1 to F6
4. Preprint to arXiv physics.soc-ph

**Acceptance.** The script exits 0, which it only does when the fitted exponents land within
tolerance of `β = 1/2`, `γ = 1`, `δ = 3`.

---

## Task 4 — Analysis and the corpus report

**Done when** `rq_answers.json`, `corpus_report.json`, `corpus_ranked.csv` and three figures
exist, generated from the scan output.

**Steps.**
```
python scripts/analyze_corpus.py --csv corpus_naa.csv --out data/rq_answers.json
python scripts/build_corpus_report.py --csv corpus_naa.csv --out-dir data/report
```

**Acceptance.** `corpus_report.json` reports `alpha_is_fitted: false`,
`threshold_fitted_in_sample: true`, and undefined rows counted rather than dropped. Both
scripts already fail loudly on a missing input; neither will invent a figure.

**One hour of work, once the CSV exists.**

---

## Task 5 — Dissertation chapters

**Done when** all seven chapters are drafted and the pre-submission checklist in the
`research-integrity` skill passes.

Chapters 1 to 4 depend on no result and are written while the GPU runs. Chapter 5 waits on
Task 4. The amendment goes on page 3, not in Chapter 5.

**Non-negotiables.** No `alpha_hat` anywhere. Never call the cortical proxy the amygdala. AUC
as the headline, with the Youden threshold labelled fitted in sample. The power statement
present: `d = 0.40` pairwise, Cohen's `f = 0.166` across four categories at n = 100 each.

---

## Task 6 — Validate the checkpoint (Paper 3)

**Done when** vertex-level Pearson `r` against held-out subjects is measured, with a noise
ceiling and bootstrap intervals, and the sign is reported either way.

**Steps.**
1. Obtain public naturalistic fMRI on fsaverage5, the surface the checkpoint already outputs
2. Predict held-out subjects and stimuli with the released checkpoint, unchanged
3. Compute per-vertex `r`, the inter-subject noise ceiling, and 10,000-resample intervals
4. Decompose by Yeo network and report per subject

**Acceptance.** Every number carries an interval, and the ceiling is measured rather than
assumed. A positive result and a negative result are equally publishable; a result without a
ceiling is neither.

**Three to five days**, mostly preprocessing. No large GPU.

---

## Task 7 — Draft Paper 2

**Done when** the manuscript exists and the preprint is posted.

**Blocked by** Tasks 3 and 4: it consumes Paper 1's bound and the corpus report.

**The one figure that carries it** is the measured `ΔNAA` against the `α_required` curve,
which converts the null into a constraint with a number.

---

## Tasks 8 to 10 — Product

**Not thesis work. Nothing starts before Task 1 finishes.**

Under one rule, from `docs/PRODUCT-ROADMAP.md`: until held-out vertex `r` is measured, no
surface may claim to report what a brain does. The defensible claim is a percentile against a
documented corpus, with the validation status printed beside it.

**8. Static results and the percentile base.** Export the scan to JSON, ship it with the site,
retire the live-server dependency. Done when the site serves real measurements with no GPU.

**9. Per-second read-out and multimodal.** Both already exist in `inference.py` and are
switched off by scope, not capability. Done when a scan returns a time series and audio or
video runs end to end.

**10. Grounded explanation.** Typed entities, the model sees only the result object, a
validator rejects banned claims, refusal is the default outside the object. Done when a
question the data cannot answer is refused rather than narrated.
