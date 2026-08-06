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

Working hypothesis for version 2: Kaggle gates both GPU and internet access behind phone
verification, and an unverified account is given neither without saying so. To be confirmed
from the account settings page before a third attempt.

The assertion at cell 1 is doing its job. Without it, both runs would have spent ten minutes
on `pip install` and the spaCy model download before failing.

### Environment note

Live scans cannot run on the development laptop: the embedding stage needs roughly 6.5 GB and
the machine had 1,025 MB free of 16 GB. This is why the scan is on Kaggle at all, and it is
not a pipeline defect.

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
