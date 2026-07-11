"""Phase 0 smoke test.

Verifies that the deployment environment is healthy enough to run
TRIBE v2 inference. Runs in this strict order:

  1. Python + PyTorch + GPU detection
  2. tribev2 / neuralset / neuraltrain / mne import chain
  3. TRIBE v2 model load from HuggingFace
  4. Single-text prediction round-trip

If any step fails it prints the error and exits non-zero. Designed to
run on the AMD MI300X deployment box; on a CPU-only dev box step 1
will report ``cuda: False`` (warning, not failure) and step 3 will
load the model on CPU which is unusably slow but technically works
once you have the disk space.

Usage:
    python scripts/smoke_test.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import torch


def main() -> int:
    print(f"Python: {sys.version}")
    print(f"PyTorch: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    print(f"ROCm/HIP available: {hasattr(torch.version, 'hip') and torch.version.hip is not None}")

    # Fail fast on the #1 documented failure: gated LLaMA-3.2-3B needs a token.
    # Catching it here beats a deep, cryptic 401 halfway through model load.
    if not (os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")):
        print(
            "\n[FAIL] No HF_TOKEN set. facebook/tribev2 and the gated "
            "meta-llama/Llama-3.2-3B download will 401.\n"
            "  export HF_TOKEN=<hf-read-token-with-llama-access>"
        )
        return 1

    if torch.cuda.is_available():
        print(f"Device count: {torch.cuda.device_count()}")
        for i in range(torch.cuda.device_count()):
            print(f"  Device {i}: {torch.cuda.get_device_name(i)}")
            mem = torch.cuda.get_device_properties(i).total_memory
            print(f"  Memory: {mem / 1e9:.1f} GB")
    else:
        print("WARNING: No GPU detected. TRIBE v2 will be very slow on CPU.")

    # --- Import chain ---
    try:
        from tribev2.demo_utils import TribeModel  # type: ignore
        print("\n[OK] tribev2 import successful")
    except ImportError as e:
        print(f"\n[FAIL] tribev2 import failed: {e}")
        print("  Run: pip install -e /path/to/tribev2[plotting]")
        return 1

    try:
        import neuralset  # type: ignore  # noqa: F401
        import neuraltrain  # type: ignore  # noqa: F401
        print("[OK] neuralset + neuraltrain")
    except ImportError as e:
        print(f"[FAIL] neuralset/neuraltrain import failed: {e}")
        print("  Run: pip install neuralset==0.0.2 neuraltrain==0.0.2")
        return 1

    try:
        import mne  # type: ignore
        print(f"[OK] mne {mne.__version__}")
    except ImportError:
        print("[FAIL] mne not installed. Run: pip install mne")
        return 1

    # --- Model load ---
    # Honour the same knobs the server uses so the smoke test proves the
    # deployment's real config, not a hardcoded one.
    cache = Path(os.environ.get("MONARCH_CACHE_FOLDER", "./cache"))
    cache.mkdir(parents=True, exist_ok=True)
    device = os.environ.get("MONARCH_TRIBE_DEVICE", "auto")

    print(f"\nLoading TRIBE v2 model on device={device} (downloads ~1 GB on first run)...")
    print("NOTE: LLaMA 3.2-3B is gated -- the HF_TOKEN above must have accepted its licence.")

    try:
        model = TribeModel.from_pretrained(
            "facebook/tribev2",
            cache_folder=cache,
            device=device,
        )
    except Exception as e:
        print(f"\n[FAIL] TRIBE v2 model load failed: {e}")
        return 1

    torch_module = getattr(model, "_model", None)
    if torch_module is not None:
        device = str(next(torch_module.parameters()).device)
    print(f"[OK] Model loaded on device: {device}")

    # --- Single text prediction ---
    test_file = cache / "smoke_test.txt"
    test_file.write_text(
        "The Federal Reserve held interest rates steady today, "
        "citing stable inflation and resilient labor market conditions."
    )

    print("\nRunning test inference on a single sentence...")
    try:
        events_df = model.get_events_dataframe(text_path=test_file)
        preds, _segments = model.predict(events=events_df, verbose=True)
    except Exception as e:
        print(f"[FAIL] Inference failed: {e}")
        return 1

    print(f"[OK] Predictions shape: {preds.shape}")
    if preds.shape[1] != 20484:
        print(f"[FAIL] Expected 20484 vertices, got {preds.shape[1]}")
        return 1

    item_vector = preds.mean(axis=0)
    print(f"[OK] Item vector shape: {item_vector.shape}")
    print(f"  Value range: [{item_vector.min():.4f}, {item_vector.max():.4f}]")
    print(f"  Mean: {item_vector.mean():.4f}")
    print(f"  Std:  {item_vector.std():.4f}")

    print("\n=== Smoke test PASSED ===")
    print(f"TRIBE v2 is working on {device}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
