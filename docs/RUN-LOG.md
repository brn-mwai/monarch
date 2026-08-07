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
