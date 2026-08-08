"""Track the scan, carry its progress forward, and restart it when a restart can help.

The scan needs two to three sessions at 204 to 227 s/item, and a session that ends leaves its
partial ``corpus_naa.csv`` inside a finished run where the next session cannot see it. This
closes that loop: read the run's state, carry the partial output into the dataset the notebook
already reads, and push a fresh version.

Two rules keep the loop from becoming a quota fire.

**Only restart what a restart can fix.** A cancelled session, a missing secret, a session
without internet or an allocator failure can all be retried, because a pushed version carries
its own accelerator, internet and dataset attachments, and the scan resumes from the carried
partial. A syntax error, a missing dependency or a tripped guard cannot: those need a code
change, and retrying them burns GPU quota to reproduce a known failure.

**A budget, and a lock.** At most ``--max-retries`` restarts per rolling day, one process at a
time. The state file records every attempt, so the budget survives a restart of this script.

Usage
-----
    python scripts/kaggle_run_state.py --slug brianmwa/monarch-corpus-scan
    python scripts/kaggle_run_state.py --slug ... --auto-retry --kernel-dir C:/Users/Windows/mk
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.watch_kaggle_run import (  # noqa: E402
    TERMINAL_STATES,
    Diagnosis,
    classify,
    fetch_log,
)

STATE_PATH = Path.home() / ".claude" / ".kaggle-run.json"
TOKEN_PATH = Path.home() / ".kaggle" / "access_token"
OUTPUT_URL = "https://www.kaggle.com/api/v1/kernels/output?user_name={user}&kernel_slug={slug}"

# A fresh pushed version carries its own accelerator, internet and dataset attachments, so
# these fail for reasons a new session resolves by itself.
RETRYABLE = frozenset(
    {
        "cancelled",
        "gpu-out-of-memory",
        "no-internet",
        "secret-unavailable",
        "gpu-arch-unsupported",
    }
)

# Two T4s, the enum Kaggle accepts. "nvidiaTeslaT4" is not a valid value and silently falls
# back to a P100, which costs the fp16 path and roughly doubles the per-item time.
ACCELERATOR = "gpuT4x2"

TOTAL_ITEMS = 400


def read_token(token_path: Path = TOKEN_PATH) -> str:
    if not token_path.exists():
        raise RuntimeError(f"no Kaggle API token at {token_path}")
    return token_path.read_text(encoding="utf-8-sig").strip()


def read_status(slug: str) -> str:
    result = subprocess.run(
        [sys.executable, "-m", "kaggle", "kernels", "status", slug],
        capture_output=True,
        text=True,
        timeout=180,
    )
    lines = [line for line in (result.stdout or result.stderr).splitlines() if line.strip()]
    return lines[-1].strip() if lines else "UNKNOWN"


def is_terminal(status: str) -> bool:
    return any(state in status for state in TERMINAL_STATES)


def download_partial_scan(slug: str, token: str) -> Optional[str]:
    """The scan output from the last finished run, or None when it produced none."""
    user, kernel = slug.split("/", 1)
    request = urllib.request.Request(
        OUTPUT_URL.format(user=user, slug=kernel),
        headers={"Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        payload = json.load(response)

    for entry in payload.get("files", []):
        if entry.get("fileName") == "corpus_naa.csv":
            file_request = urllib.request.Request(
                entry["url"], headers={"Authorization": f"Bearer {token}"}
            )
            with urllib.request.urlopen(file_request, timeout=300) as handle:
                return handle.read().decode("utf-8", "replace")
    return None


def count_scanned(csv_text: str) -> int:
    return sum(1 for _ in csv.DictReader(io.StringIO(csv_text)))


def retries_in_last_day(attempts: list[str], now: Optional[datetime] = None) -> int:
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(days=1)
    recent = 0
    for stamp in attempts:
        try:
            if datetime.fromisoformat(stamp) > cutoff:
                recent += 1
        except ValueError:
            continue
    return recent


def should_retry(
    diagnosis: Diagnosis, attempts: list[str], max_retries: int, scanned: int
) -> tuple[bool, str]:
    """Whether a fresh session is worth spending, and why."""
    if scanned >= TOTAL_ITEMS:
        return False, "scan complete"
    if diagnosis.signature == "completed":
        return False, "run completed"
    if diagnosis.signature not in RETRYABLE:
        return False, f"{diagnosis.signature} needs a code change, not a restart"
    if retries_in_last_day(attempts) >= max_retries:
        return False, f"retry budget spent ({max_retries} in the last day)"
    return True, "retryable failure with progress still to make"


def force_t4(kernel_dir: Path) -> dict:
    """Pin the metadata to two T4s before pushing, and report what changed."""
    metadata_path = kernel_dir / "kernel-metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    previous = metadata.get("accelerator")
    metadata["accelerator"] = ACCELERATOR
    metadata["enable_gpu"] = True
    metadata["enable_internet"] = True
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return {"previous": previous, "accelerator": ACCELERATOR}


def carry_partial_to_dataset(csv_text: str, dataset_dir: Path, message: str) -> str:
    """Publish the partial scan so the next session resumes instead of restarting.

    The notebook already globs /kaggle/input for corpus_naa.csv and seeds the working copy
    from it, so a new dataset version is all the resume path needs.
    """
    dataset_dir.mkdir(parents=True, exist_ok=True)
    (dataset_dir / "corpus_naa.csv").write_text(csv_text, encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "kaggle", "datasets", "version", "-p", str(dataset_dir), "-m", message],
        capture_output=True,
        text=True,
        timeout=600,
    )
    return (result.stdout or result.stderr).strip().splitlines()[-1]


def push_kernel(kernel_dir: Path) -> str:
    result = subprocess.run(
        [sys.executable, "-m", "kaggle", "kernels", "push", "-p", str(kernel_dir)],
        capture_output=True,
        text=True,
        timeout=600,
    )
    return (result.stdout or result.stderr).strip().splitlines()[-1]


def build_state(
    slug: str,
    status: str,
    diagnosis: Optional[Diagnosis],
    scanned: int,
    previous: dict,
) -> dict:
    return {
        "slug": slug,
        "status": status,
        "running": not is_terminal(status),
        "version": previous.get("version"),
        "scanned": scanned,
        "total": TOTAL_ITEMS,
        "seconds_per_item": diagnosis.seconds_per_item if diagnosis else None,
        "signature": diagnosis.signature if diagnosis else "running",
        "action": diagnosis.action if diagnosis else "",
        "attempts": previous.get("attempts", []),
        "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slug", default="brianmwa/monarch-corpus-scan")
    parser.add_argument("--state", type=Path, default=STATE_PATH)
    parser.add_argument("--auto-retry", action="store_true")
    parser.add_argument("--kernel-dir", type=Path, default=Path.home() / "mk")
    parser.add_argument("--partial-dir", type=Path, default=Path.home() / "mpartial")
    parser.add_argument("--max-retries", type=int, default=6)
    args = parser.parse_args()

    previous = {}
    if args.state.exists():
        previous = json.loads(args.state.read_text(encoding="utf-8"))

    status = read_status(args.slug)
    diagnosis = None
    scanned = previous.get("scanned", 0)

    if is_terminal(status):
        token = read_token()
        diagnosis = classify(fetch_log(args.slug, token), status)
        partial = download_partial_scan(args.slug, token)
        if partial:
            scanned = max(scanned, count_scanned(partial))

        if args.auto_retry:
            allowed, reason = should_retry(
                diagnosis, previous.get("attempts", []), args.max_retries, scanned
            )
            print(f"retry: {'yes' if allowed else 'no'} ({reason})")
            if allowed:
                if partial:
                    print(carry_partial_to_dataset(
                        partial, args.partial_dir, f"partial scan, {scanned} items"
                    ))
                print(json.dumps(force_t4(args.kernel_dir)))
                print(push_kernel(args.kernel_dir))
                previous.setdefault("attempts", []).append(
                    datetime.now(timezone.utc).isoformat(timespec="seconds")
                )
                time.sleep(5)
                status = read_status(args.slug)

    state = build_state(args.slug, status, diagnosis, scanned, previous)
    args.state.parent.mkdir(parents=True, exist_ok=True)
    args.state.write_text(json.dumps(state, indent=2), encoding="utf-8")

    print(f"{state['status']} | {state['scanned']}/{TOTAL_ITEMS} | {state['signature']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
