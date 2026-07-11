"""Pre-download every model weight so nothing downloads at request time.

Request-time downloads are the biggest latency/flakiness source in TRIBE's
cascade (gTTS -> WhisperX -> LLaMA + Wav2Vec-BERT -> fusion). Run this ONCE on
the pod after install, before serving, so the first real request is fast:

    HF_TOKEN=<token> python scripts/prewarm.py

Weights land in HF_HOME (set by the Dockerfile to /app/cache/hf), so a mounted
cache volume survives restarts. Extra repos (e.g. a V-JEPA 2 checkpoint for
video) can be appended:

    python scripts/prewarm.py facebook/vjepa2-vitg-fpc64-256
"""

from __future__ import annotations

import os
import sys

# The text cascade needs TRIBE + LLaMA (text) + Wav2Vec-BERT (audio) + the
# WhisperX large-v3 backend. Video adds a V-JEPA 2 checkpoint (pass as an arg).
DEFAULT_REPOS = [
    "facebook/tribev2",
    "meta-llama/Llama-3.2-3B",
    "facebook/w2v-bert-2.0",
    "Systran/faster-whisper-large-v3",
]


def main() -> int:
    if not (os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")):
        print("[FAIL] Set HF_TOKEN (with gated Llama-3.2-3B access) before prewarming.")
        return 1

    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        print("[FAIL] huggingface_hub not installed. Run: pip install huggingface-hub")
        return 1

    repos = DEFAULT_REPOS + sys.argv[1:]
    failures: list[str] = []
    for repo in repos:
        print(f"\n=== Pre-downloading {repo} ===")
        try:
            path = snapshot_download(repo_id=repo)
            print(f"[OK] {repo} -> {path}")
        except Exception as exc:  # noqa: BLE001 - report every repo, keep going
            print(f"[FAIL] {repo}: {exc}")
            failures.append(repo)

    if failures:
        print(f"\n{len(failures)} repo(s) failed: {', '.join(failures)}")
        return 1
    print(f"\n=== Pre-warm complete: {len(repos)} repos cached ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
