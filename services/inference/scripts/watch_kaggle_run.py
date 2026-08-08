"""Watch a Kaggle run, and when it stops, say why in one line.

Fifteen runs failed before one reached the scan, each for a different reason, and every
diagnosis cost a manual log pull and a read through thousands of entries. This does that
part: poll until the run reaches a terminal state, fetch the log, and classify the failure
against the signatures that have actually occurred, with the recommended action attached.

It diagnoses. It does not edit code, push a version, or start a run, because a fix applied
without a person reading the diagnosis is how a wrong fix ships three times.

One rule earned the hard way. Papermill echoes the *source* of the failing cell into the
log, so a progress marker found anywhere is not evidence the step ran: a run was twice
reported as having patched tribev2 when the string came from the cell text of the traceback.
Markers are therefore read from stdout only, and only from entries before the failure.

Usage
-----
    python scripts/watch_kaggle_run.py --slug brianmwa/monarch-corpus-scan --once
    python scripts/watch_kaggle_run.py --slug brianmwa/monarch-corpus-scan --watch --interval 600
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

TOKEN_PATH = Path.home() / ".kaggle" / "access_token"
OUTPUT_URL = "https://www.kaggle.com/api/v1/kernels/output?user_name={user}&kernel_slug={slug}"

TERMINAL_STATES = ("COMPLETE", "ERROR", "CANCEL")

PROGRESS_MARKERS = (
    "session environment ready",
    "tribev2 stack imports OK",
    "whisperx CLI imports OK",
    "whisperx GPU transcription OK",
    "Smoke test PASSED",
    "Scanning 400 items",
)

SCAN_LINE = re.compile(r"\[(\d+)/(\d+)\] naa=(\S+) \(([\d.]+)s/item\)")

# Ordered: the first signature that matches wins, so specific patterns precede generic ones.
FAILURE_SIGNATURES: tuple[tuple[str, str, str], ...] = (
    (
        "OutOfMemoryError",
        "gpu-out-of-memory",
        "Free each item's allocations before the next starts, and set "
        "PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True.",
    ),
    (
        "Temporary failure in name resolution",
        "no-internet",
        "Internet is off for this session. Set it in Session options before saving the "
        "version; an API push carries it in the metadata, an editor run does not.",
    ),
    (
        "kaggle_web_client",
        "secret-unavailable",
        "HF_TOKEN did not resolve. Attach the token dataset, or tick the secret in "
        "Add-ons -> Secrets; a pushed version never carries a secret attachment.",
    ),
    (
        "No module named 'app'",
        "package-root-missing",
        "The script does not put its package root on sys.path. See test_script_imports.py.",
    ),
    (
        "do not support efficient float16",
        "fp16-unsupported",
        "This card is pre-Volta. MONARCH_WHISPER_COMPUTE must be float32 below sm_70.",
    ),
    (
        "libcudnn",
        "cudnn-not-on-path",
        "torch ships cuDNN under site-packages/nvidia; prepend it to LD_LIBRARY_PATH.",
    ),
    (
        "No module named 'neuralset'",
        "tribev2-deps-missing",
        "tribev2 was installed with --no-deps. Install it with its dependencies under a "
        "constraints file pinning torch.",
    ),
    (
        "has no attribute 'NoValue'",
        "exca-too-old",
        "neuralset declares exca>=0.5.20. Install it rather than lowering the version guard.",
    ),
    (
        "No module named 'pyannote'",
        "whisperx-deps-missing",
        "whisperx was installed with --no-deps. Use a release whose torch floor the pinned "
        "build satisfies, and install it with dependencies.",
    ),
    (
        "SyntaxError",
        "notebook-python-broken",
        "A code cell or heredoc does not compile. test_notebook_syntax.py catches this "
        "locally in under a second.",
    ),
    (
        "AssertionError",
        "guard-tripped",
        "A guard fired on purpose. Read its message before changing anything: it is "
        "usually right and the assumption behind the patch is usually wrong.",
    ),
    (
        "CUDA capability",
        "gpu-arch-unsupported",
        "torch has no kernels for this card. Install a build whose arch list covers it.",
    ),
)


@dataclass
class Diagnosis:
    """What stopped the run, and what to do about it."""

    status: str
    failing_cell: Optional[str] = None
    signature: str = "unclassified"
    error_line: str = ""
    action: str = "Read the traceback: this failure has not been seen before."
    markers_reached: list[str] = field(default_factory=list)
    items_scanned: int = 0
    seconds_per_item: Optional[float] = None

    def summary(self) -> str:
        head = f"[{self.status}] {self.signature}"
        if self.failing_cell:
            head += f" at {self.failing_cell}"
        return head


def _read_token(token_path: Path = TOKEN_PATH) -> str:
    if not token_path.exists():
        raise RuntimeError(f"no Kaggle API token at {token_path}")
    return token_path.read_text(encoding="utf-8-sig").strip()


def fetch_log(slug: str, token: str) -> list[dict]:
    """The kernel's log, which Kaggle publishes only once a run has finished."""
    user, kernel = slug.split("/", 1)
    request = urllib.request.Request(
        OUTPUT_URL.format(user=user, slug=kernel),
        headers={"Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        payload = json.load(response)
    return json.loads(payload["log"])


def find_failing_cell(entries: list[dict]) -> Optional[int]:
    """Index of the entry naming the cell papermill stopped on."""
    for index, entry in enumerate(entries):
        if "Exception encountered at" in str(entry.get("data", "")):
            return index
    return None


def markers_reached(entries: list[dict], before: Optional[int] = None) -> list[str]:
    """Progress markers printed to stdout, read only from entries before the failure.

    Both conditions matter. Papermill echoes the failing cell's source, so a marker seen
    anywhere may be the cell text rather than its output.
    """
    window = entries[:before] if before is not None else entries
    stdout = [str(e.get("data", "")) for e in window if e.get("stream_name") == "stdout"]
    joined = "\n".join(stdout)
    return [marker for marker in PROGRESS_MARKERS if marker in joined]


def scan_progress(entries: list[dict]) -> tuple[int, Optional[float]]:
    """How many items were scanned, and the rate the last one reported."""
    matches = [SCAN_LINE.search(str(e.get("data", ""))) for e in entries]
    found = [m for m in matches if m]
    if not found:
        return 0, None
    last = found[-1]
    return int(last.group(1)), float(last.group(4))


def classify(entries: list[dict], status: str) -> Diagnosis:
    """Match the log against failures that have actually happened here."""
    failing_index = find_failing_cell(entries)
    diagnosis = Diagnosis(
        status=status,
        markers_reached=markers_reached(entries, failing_index),
    )
    diagnosis.items_scanned, diagnosis.seconds_per_item = scan_progress(entries)

    if failing_index is None:
        if status.startswith("COMPLETE"):
            diagnosis.signature = "completed"
            diagnosis.action = "Nothing to fix. Collect the outputs."
        elif status.startswith("CANCEL"):
            diagnosis.signature = "cancelled"
            diagnosis.action = (
                "The run was cancelled, most often by another version starting. Do not push "
                "while a run is live."
            )
        return diagnosis

    diagnosis.failing_cell = str(entries[failing_index].get("data", "")).strip()[:60]
    context = "\n".join(str(e.get("data", "")) for e in entries[max(0, failing_index - 60):failing_index])

    for needle, signature, action in FAILURE_SIGNATURES:
        if needle in context:
            diagnosis.signature = signature
            diagnosis.action = action
            for line in reversed(context.splitlines()):
                if needle in line:
                    diagnosis.error_line = line.strip()[:200]
                    break
            break
    else:
        for line in reversed(context.splitlines()):
            if "Error" in line or "error:" in line:
                diagnosis.error_line = line.strip()[:200]
                break

    return diagnosis


def poll_until_terminal(
    slug: str,
    status_reader: Callable[[str], str],
    interval_seconds: int = 600,
    max_polls: int = 80,
) -> str:
    """Block until the run leaves the running state, or the poll budget runs out."""
    for _ in range(max_polls):
        status = status_reader(slug)
        if any(state in status for state in TERMINAL_STATES):
            return status
        time.sleep(interval_seconds)
    return "TIMEOUT: still running after the poll budget"


def _status_via_cli(slug: str) -> str:
    import subprocess

    result = subprocess.run(
        [sys.executable, "-m", "kaggle", "kernels", "status", slug],
        capture_output=True,
        text=True,
        timeout=120,
    )
    return (result.stdout or result.stderr).strip().splitlines()[-1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--interval", type=int, default=600)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    status = (
        poll_until_terminal(args.slug, _status_via_cli, args.interval)
        if args.watch
        else _status_via_cli(args.slug)
    )
    print(status)

    if not any(state in status for state in TERMINAL_STATES):
        print("still running; no log is published until a run finishes")
        return 0

    entries = fetch_log(args.slug, _read_token())
    diagnosis = classify(entries, status)

    print(f"\n{diagnosis.summary()}")
    if diagnosis.error_line:
        print(f"  {diagnosis.error_line}")
    print(f"  markers reached : {', '.join(diagnosis.markers_reached) or 'none'}")
    if diagnosis.items_scanned:
        print(f"  items scanned   : {diagnosis.items_scanned} at {diagnosis.seconds_per_item}s/item")
    print(f"  action          : {diagnosis.action}")

    if args.out:
        args.out.write_text(json.dumps(diagnosis.__dict__, indent=2), encoding="utf-8")
        print(f"\nWrote {args.out}")

    return 0 if diagnosis.signature in ("completed",) else 1


if __name__ == "__main__":
    sys.exit(main())
