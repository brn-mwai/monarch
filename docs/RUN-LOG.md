# Run log

A dated record of what was actually run, including what failed. Kept because the methods
section is written from this file rather than from memory, and because a referee or examiner
asking "how do I reproduce this" gets a real answer.

Entries are append-only. A failure is never deleted after it is fixed; the fix is a new entry.

---

## 2026-08-06

### Corpus, already built (2026-07-28)

`monarch-data/corpus.csv`, 400 rows, four categories at 100 each, verified before upload:

```
neutral_informational  100
fear_activating        100
high_outrage           100
reward_hook            100
```

Columns present and carried through the scan: `id, text, category, manipulative,
credibility, partisan_intensity, source_dataset, source_name, word_count`.

### Checkpoint facts recorded

`scripts/verify_tribe_checkpoint.py --config tribe-ckpt/config.yaml` run locally. Two facts
the thesis needs, taken from the artifact rather than from a folder name:

```
encoder.depth                8          config.yaml:519
group                        half_depth config.yaml:591
subject_layers.n_subjects    25         config.yaml:538-539
average_subjects (trained)   false      config.yaml:542
```

Cross-checked against the loader: `tribev2/demo_utils.py:218` sets
`config["average_subjects"] = True`, which `tribev2/main.py:356-361` propagates to the
subject layers and the projector. Monarch's predictions therefore run through the averaged
subject layer and are not conditioned on any one of the 25 training subjects.

### Public site corrected and redeployed

The corrected `ScientificDisclaimer` from commit `821dbdb` (2026-07-16) had never been
deployed, so the live site still carried the false SemEval-2020 validation and NELA
calibration claims. Deploying it surfaced three further places where authored constants were
displayed in the position of measurements: the landing page score labels, the scanner example
cards, and the batch tab, which seeded its entire ranked chart and CSV export from
`expectedNAA` and wrote `0` for any item that failed to scan.

All four fixed in `f886a1f`. Deployed to Cloudflare Pages production. Verified against the
live domain rather than assumed: `buildId tdNc9uhik_q98pbvfSjQr` matches the local build, the
chunk carrying the disclaimer serves the corrected text, and the old claims return zero
matches across all served chunks.

### Kaggle setup

```
dataset  brianmwa/monarch-corpus         private, corpus.csv 433,677 bytes
kernel   brianmwa/monarch-corpus-scan    private, dataset attached, internet on
```

Two gotchas worth recording:

1. `kaggle datasets create -p <long absolute path>` fails on Windows with
   `[Errno 2] No such file or directory` while building its upload cache path. The CLI
   mangles the source path into a filename. Creating from a short path (`C:\Users\Windows\mc`)
   with a relative `-p mc` works.
2. Uploads need the newer API token in `~/.kaggle/access_token`. The legacy `kaggle.json`
   key authenticates reads only, and a write fails with an authentication prompt that does
   not name the difference.

### Scan attempts

| Version | Result | Cause |
|---|---|---|
| 1 | ERROR in seconds | `AssertionError: No GPU`. The notebook asserts CUDA before doing anything, so it cost about 0.2 GPU-hours instead of failing after the installs |
| 2 | ERROR in seconds | Same. `enable_gpu: true` plus `accelerator: nvidiaTeslaT4` in `kernel-metadata.json` did not attach a GPU |

Hypothesis after version 2 was that Kaggle gates GPU and internet behind phone verification.
**Confirmed** by the error the session surfaced:

```
Error: Permission 'kernelSessions.enableInternet' was denied
```

The account is not phone-verified, so the API accepts `enable_gpu` and `enable_internet` in
the kernel metadata and the platform then refuses both at session start. Nothing in the
notebook or the metadata can work around it: the run needs internet to clone the repository
and to pull the model weights, and it needs the GPU to run them.

Fix: verify the phone number at https://www.kaggle.com/settings, then re-push. No code
change is required, and version 3 will be identical to version 2.

The assertion at cell 1 is doing its job. Without it, both runs would have spent ten minutes
on `pip install` and the spaCy model download before failing.

### Environment note

Live scans cannot run on the development laptop: the embedding stage needs roughly 6.5 GB and
the machine had 1,025 MB free of 16 GB. This is why the scan is on Kaggle at all, and it is
not a pipeline defect.

---

### Version 3, after phone verification

Verification cleared both gates at once. GPU allocated, internet allowed, repository cloned,
the `--carry-cols` guard passed, dependencies installed. Cells 1 to 4 green.

Two new failures:

1. **Wrong card.** Kaggle allocated a Tesla P100 despite `"accelerator": "nvidiaTeslaT4"`:

   ```
   Tesla P100-PCIE-16GB with CUDA capability sm_60 is not compatible with the current
   PyTorch installation.
   ```

   PyTorch 2.10.0+cu128 no longer builds for sm_60, so the model could not have run on that
   card even with everything else correct. The metadata enum for two T4s is `gpuT4x2`.

2. **The secret does not survive an API push.** `UserSecretsClient().get_secret('HF_TOKEN')`
   returned HTTP 400. `kernel-metadata.json` has no field for secret attachments, so each
   pushed version starts with none attached, whatever was attached in the editor before.

   Consequence for the workflow: push the code by API, then attach the secret and start the
   run **from the editor**, not from another push.

### Output directory

The notebook cloned the repository into `/kaggle/working`, which is the kernel's output
directory, so every download pulled 355 files including the whole repo and tribev2. Code now
clones to `/kaggle/temp` and only `corpus.csv`, `corpus_naa.csv` and `tribe_facts.json` are
written to `/kaggle/working`.

### Reading a kernel log quickly

`kaggle kernels output` downloads every output file before the log, which took minutes with
the repo in there. The log is returned inline by the API instead:

```
GET https://www.kaggle.com/api/v1/kernels/output?user_name=<user>&kernel_slug=<slug>
```

with `Authorization: Bearer <access_token>`. The `log` field is the JSON array itself, not a
URL to it.

### Version 5: the accelerator on offer is a P100

T4 x2 and TPU are greyed out on this account, so P100 is the only choice. Rather than wait
for a T4 to free up, the notebook now adapts: a first cell reads the card name from
`nvidia-smi` and installs `torch==2.6.0+cu121` on a Pascal-class card, because those wheels
still target sm_60 while the image's cu128 build does not. It runs before any torch import,
since a live kernel keeps whichever version it loaded first, and it is skipped on cards the
image already supports. Cost is about 4 minutes against an 8.3 hour run.

The GPU check was also too weak. `torch.cuda.is_available()` returned True on the P100: the
card was visible, just unusable. It now compares the device capability against
`torch.cuda.get_arch_list()`, so a mismatch fails in the first cell rather than deep in the
model load.

### Versions 6 and 8: no internet in an editor-launched session

Both died in the torch cell with what looked like a missing package:

```
ERROR: Could not find a version that satisfies the requirement torch==2.5.1 (from versions: none)
```

The cause is above that line, in the retry warnings:

```
Failed to establish a new connection: [Errno -3] Temporary failure in name resolution
```

DNS is dead, so pip never reached the index. `from versions: none` means the index was
unreachable, not that the version does not exist. **The torch pin was never the problem.**
Version 6 showed the same signature, so the earlier reading of it as a genuinely missing
2.6.0 wheel was wrong; the 2.5.1 pin is kept because it is correct, not because it was the
fix.

Why it appeared only now: version 3 was launched by an API push, whose
`kernel-metadata.json` sets `enable_internet: true`. Versions 6 and 8 were launched from the
editor, which uses its own Session options, and Internet is off there by default. The two
launch paths do not share settings.

The run needs the network three times: cloning the repository, installing packages, and
pulling roughly 7 GB of model weights.

### The two launch paths each grant half of what the run needs

After nine versions the pattern is exact, and it is a property of Kaggle rather than of this
notebook:

| Launch path | Internet | `HF_TOKEN` | Dies at |
|---|---|---|---|
| API `kernels push` | granted by `enable_internet` in the metadata | never attached, the metadata has no field for secrets | the secrets cell, `HTTPError` from `kaggle_web_client` |
| Editor Save & Run All | off unless set in Session options | attached, it is a notebook-level setting made in the UI | the torch install, DNS failure |

Version 10 settled it. Pushed by API, it cleared every gate that had failed before:

```
installed 2.5.1+cu121 ['sm_50', 'sm_60', 'sm_70', 'sm_75', 'sm_80', 'sm_86', 'sm_90']
2.5.1+cu121 Tesla P100-PCIE-16GB sm_60 OK
OK: batch_naa.py supports --carry-cols
deps done
```

then stopped at `In [6]`, the secrets cell, with an HTTP error from the secrets client. So the
Pascal swap works, the architecture guard works, the repository guard works, and the network
works on that path. Only the secret is missing.

The combination that can work is therefore the editor path with Internet switched on in
Session options before the version is saved. Both halves exist; they have simply never been
present in the same session.

### Committing from the editor while the API pushes

```
ConcurrencyViolation Sequence number must match Draft record:
ExpectedSequence=11, ActualSequence=7
```

An API push moves the kernel's sequence number while an open editor tab still holds the
earlier draft, and Kaggle refuses the commit rather than overwrite. Reloading the tab clears
it. The workflow that avoids it: push code by API, then leave the API alone and drive the run
from the editor, since the secret attachment has to be made there anyway.

### Screenshots taken

| File | What it shows |
|---|---|
| `docs/figures/screenshots/S3-scan-refusal.png` | The scanner refusing to draw a brain map with no inference server attached: *"No brain map is shown, because Monarch does not display simulated activation in place of a real TRIBE v2 prediction."* Captured against the live site after the redeploy, so it also shows the corrected example cards reading EXAMPLE rather than an authored NAA value |

Naming: `S<n>-<slug>.png`, filed under `docs/figures/screenshots/`, listed in `FIGURES.md`
with what it is evidence of. A screenshot with no entry there does not go in the thesis.

---

## 2026-08-08

### The card question, settled

Five sessions in a row drew a Tesla P100 despite T4 x2 being requested. One of those was
pushed through the API with `machine_shape: gpuT4x2` and `--accelerator gpuT4x2`:

```
card: Tesla P100-PCIE-16GB
STOP: Tesla P100-PCIE-16GB is sm_60, below sm_70.
SystemExit: pre-Volta GPU refused
```

The accelerator field is a request the scheduler may ignore, not an allocation. Waiting for a
T4 was abandoned and the notebook now accepts a pre-Volta card, printing which card it got.

### Quota, previously misread

`quota_view()`'s JSON repr prints `totalTimeAllowed "21600s"`. The typed field says
`total_time_allowed = 1 day, 6:00:00`, which is 108000 s. The allowance is 30 GPU-h per week,
not 6. A plan built on the smaller figure was discarded. Read the timedelta fields.

### v34: the first run that finished

`--limit 50` on a P100. Status `COMPLETE`, output published.

```
rows scanned: 50 / 400
NAA (ratio) defined: 43  undefined: 7
```

No OOM, retry or skip appeared anywhere in 23642 log entries, so the `--max-skips` path
remains unexercised.

Signed NAA per category, descriptive only, no test:

```
fear_activating          n=12  mean=-0.0088  sd=0.0215
high_outrage             n=13  mean=-0.0185  sd=0.0253
neutral_informational    n=12  mean=-0.0267  sd=0.0126
reward_hook              n=13  mean=-0.0137  sd=0.0186
```

Every category mean negative, matching both prior runs. Measured spread across the 50 items:
`0.0801`. Session cost about 5900 s of quota including setup, putting the per-item cost
between 64 and 78 s, not the 187.5 s taken from an earlier partial run.

Rows verified against the source corpus: `text`, `category` and `id` match the first 50 rows
of `corpus.csv` exactly, 50 distinct values, internally consistent to the stored 6 decimals.
Apparent mismatches at 1e-9 tolerance were rounding, not error.

### Pilot analysis, run to prove the pipeline, not to claim a result

`analyze_corpus.py` and `build_corpus_report.py` both exit 0 on the 50 rows. Reported
AUC 0.6996, separation F=1.717, p=0.1767, eta^2=0.1007, flagged `NOT USABLE` by the script.

At 12 per group the design could only detect eta^2 above 0.1989, and power at the observed
0.1007 was 0.434. The pilot is therefore uninformative in both directions. Not a null.

### Power statement for the full design

`scripts/power_statement.py --out data/power_statement.json`

```
smallest detectable eta^2 : 0.0268   (Cohen's f 0.1659)
smallest detectable AUC   : 0.5916   (separation d 0.3277)
```

At 400 items, power is 1.0 if the true eta^2 equals the pilot's 0.1007, so the full scan
decides in either direction.

### v35 started

`--limit 350`, resuming from the 50 via the private dataset
`brianmwa/monarch-corpus-naa-partial`. Running at the time of writing.

---

## 2026-08-09

### The corpus is complete

v36 finished with status `COMPLETE`. `scripts/verify_scan_output.py` passes on all of it:

```
scanned 400 of 400 corpus rows
  fear_activating          100
  high_outrage             100
  neutral_informational    100
  reward_hook              100
ratio NAA defined: 331  undefined: 69
distinct texts: 400  distinct naa_signed: 400
```

The ratio form is undefined for 69 of 400 items, 17.25%, which is the rate the methods note
reports.

### RQ II: the categories separate

`python scripts/analyze_corpus.py --csv data/final/corpus_naa.csv --naa-col naa_signed
--category-col category --out data/final/rq_answers.json`

```
fear_activating        n=100  mean=-0.0018  sd=0.0204
high_outrage           n=100  mean=-0.0185  sd=0.0208
neutral_informational  n=100  mean=-0.0191  sd=0.0162   (baseline)
reward_hook            n=100  mean=-0.0128  sd=0.0228

separation: F=15.779  p=1.035e-09  eta^2=0.1068  (USABLE)
```

This is not the null both prior runs pointed at. The effect sits well above the 0.0268 the
design was powered to detect, and power at the observed value is 1.0.

**The separation is almost entirely one category.** Welch tests against the neutral baseline:

```
fear_activating vs neutral: t=+6.639  p=3.283e-10  d=+0.939
reward_hook     vs neutral: t=+2.254  p=2.539e-02  d=+0.319
high_outrage    vs neutral: t=+0.212  p=8.320e-01  d=+0.030
```

High outrage does not separate from neutral at all. The proposal predicted it would separate
most. Fear-activating carries the result.

### RQ I: modest but real

```
n=400  AUC=0.6274  F1=0.6680 (threshold fitted in sample, not the headline)
```

AUC clears the 0.5916 the design could detect, in the direction the proposal predicted. Power
at the observed AUC is 0.961.

### Every category mean is still negative

The deliberative network mean exceeds the affective mean for every category, so the signed
index never turns positive on average. The categories differ in how far below zero they sit,
not in which network leads.

### The bound, from the measured spread

`python scripts/field_bound.py --scan data/final/corpus_naa.csv --report
data/paper1/phase_boundary.json --out data/final/field_bound.json`

```
range     : -0.0698 to +0.0543
spread dX : 0.1241
alpha >= 0.1693 at beta_J 1.102
alpha >= 1.6553 at beta_J 1.496
alpha >= 4.2938 at beta_J 2.000
```

---

## Template for the next entry

```
## YYYY-MM-DD

### What was run
Command, verbatim.

### What came back
Numbers, or the error verbatim.

### What it means
One or two sentences. If nothing, write "nothing yet".
```

---

## 2026-08-16

### What was run

`monarch-corpus-scan` v39, the last 25 items of the vector rescan, resumed from the 375-row
partial published as `brianmwa/monarch-corpus-naa-partial`.

`python scripts/test_retest.py --run-a data/final/corpus_naa.csv
--run-b data/final/corpus_naa_run_b.csv --out data/final/test_retest.json`

### What came back

The run completed. `rows scanned: 400 / 400`, 25 new per-vertex maps, and
`verify_scan_output.py` exits 0 against the corpus. The 375 rows carried in from the previous
session are byte-identical in the new file, so the resume added items rather than rewriting
them. All 400 maps are 20484 vertices and every row has one.

```
paired items      : 400
naa_signed  r=0.8763  ICC=0.8725  sd(diff)=0.01029  noise/signal=0.484
a_aff       r=0.8759  ICC=0.8713  sd(diff)=0.01213  noise/signal=0.489
a_del       r=0.8576  ICC=0.8550  sd(diff)=0.01271  noise/signal=0.521
direction flips   : 51 of 400 (12.8%)
separation_run_a_shared_items   eta^2=0.1068  F=15.779  p=1.035e-09
separation_run_b_shared_items   eta^2=0.0888  F=12.861  p=4.918e-08
```

### What it means

Test-retest is now measured over the whole corpus rather than 375 of it, and nothing turns.
Reliability is a shade lower than the partial reported (ICC 0.8725 against 0.8757), the flip
rate a shade lower too (12.8% against 13.1%), and the second session's separation a shade
higher (0.0888 against 0.0839). Every conclusion drawn from the partial holds: group-level
claims are supportable, per-item ones are not. Paper 2, the dissertation front matter and
chapters 1 and 6 were corrected to the 400-item values.

The per-vertex maps exist for the full corpus for the first time, which is what the run was
for. They are the input the brain figures and the web export read.
