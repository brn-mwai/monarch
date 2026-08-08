"""Prepare a Kaggle session to run the TRIBE cascade.

The notebook used to carry this as shell heredocs and inline Python inside its JSON,
where nothing could lint or test it. Two runs were lost there: a string literal broken
by an escaping bug, and a source patch written against a different checkout of tribev2.
Both would have been caught by a unit test, so the logic lives here and the notebook
calls it in three lines.

Everything the session needs from the environment is decided by four functions:

    select_whisper_compute_type   fp16 only where the GPU supports it
    find_cudnn_library_dirs       torch ships cuDNN off the loader path
    read_hf_token                 dataset first, Kaggle secret second
    apply_session_environment     the only function with side effects

Import it, do not run it as a subprocess: the environment has to be set in the kernel
that later cells and the whisperx subprocess inherit.
"""

from __future__ import annotations

import glob
import os
from pathlib import Path
from typing import Callable, Optional

# ctranslate2 requires compute capability 7.0 for an efficient fp16 path. The T4 (sm_75)
# clears it, the P100 (sm_60) does not, and which card Kaggle allocates is not ours to choose.
MIN_FP16_CAPABILITY = 7

KAGGLE_INPUT_ROOT = Path("/kaggle/input")
TOKEN_FILENAME = "hf_token.txt"

SESSION_DEFAULTS = {
    "HF_HUB_DISABLE_XET": "1",
    "MONARCH_WHISPER_MODEL": "small",
    "MONARCH_WHISPER_DEVICE": "cuda",
    "MONARCH_WHISPERX_CMD": "whisperx",
    "MONARCH_TRIBE_DEVICE": "cuda",
}


def select_whisper_compute_type(capability_major: int) -> str:
    """Precision whisperx can actually run on this card."""
    return "float16" if capability_major >= MIN_FP16_CAPABILITY else "float32"


def find_cudnn_library_dirs(package_roots: Optional[list[Path]] = None) -> list[Path]:
    """Directories holding the cuDNN and cuBLAS shared objects torch ships.

    ctranslate2 dlopens these at inference rather than linking them, and pip installs
    them under site-packages instead of a system library path, so a transcription only
    fails once a convolution runs.

    ``package_roots`` is injected by tests; left unset it resolves the installed packages.
    """
    if package_roots is None:
        import nvidia.cublas
        import nvidia.cudnn

        package_roots = [
            Path(nvidia.cudnn.__file__).parent,
            Path(nvidia.cublas.__file__).parent,
        ]

    directories = [root / "lib" for root in package_roots]
    missing = [str(directory) for directory in directories if not directory.is_dir()]
    if missing:
        raise RuntimeError(f"expected CUDA library directories are absent: {missing}")

    convolution_libraries = list(directories[0].glob("libcudnn_cnn*"))
    if not convolution_libraries:
        raise RuntimeError(
            f"no libcudnn_cnn in {directories[0]}; ctranslate2 cannot run convolutions"
        )
    return directories


def read_hf_token(
    input_root: Path = KAGGLE_INPUT_ROOT,
    secret_reader: Optional[Callable[[str], str]] = None,
) -> str:
    """Hugging Face token, from an attached dataset or the Kaggle secret store.

    Two sources because the two launch paths differ: a run started from the editor
    carries the secret, while a version pushed through the API never does, since the
    kernel metadata has no field for secret attachments.
    """
    for path in sorted(glob.glob(str(input_root / "**" / TOKEN_FILENAME), recursive=True)):
        token = Path(path).read_text(encoding="utf-8").strip()
        if token:
            print(f"HF token from dataset: {path}")
            return token

    if secret_reader is None:
        from kaggle_secrets import UserSecretsClient

        secret_reader = UserSecretsClient().get_secret

    print("HF token from Kaggle secret")
    token = secret_reader("HF_TOKEN")
    if not token:
        raise RuntimeError(
            "no Hugging Face token: attach a dataset holding hf_token.txt, or add "
            "HF_TOKEN under Add-ons -> Secrets"
        )
    return token


def apply_session_environment(
    capability_major: Optional[int] = None,
    input_root: Path = KAGGLE_INPUT_ROOT,
    secret_reader: Optional[Callable[[str], str]] = None,
    environ: Optional[dict] = None,
    repo_root: Path = Path("/kaggle/temp"),
) -> dict:
    """Set every variable the cascade reads, and return them for inspection.

    The only function here that mutates anything. Returns the applied values so a caller
    can assert on them rather than reading os.environ back out.
    """
    target = os.environ if environ is None else environ

    if capability_major is None:
        import torch

        capability_major = (
            torch.cuda.get_device_capability(0)[0] if torch.cuda.is_available() else 0
        )

    compute_type = select_whisper_compute_type(capability_major)
    # Always ":" rather than os.pathsep: LD_LIBRARY_PATH is read by the Linux loader on the
    # session box, whatever separator the machine building this string happens to use.
    library_path = ":".join(
        [directory.as_posix() for directory in find_cudnn_library_dirs()]
        + [target.get("LD_LIBRARY_PATH", "")]
    )

    applied = dict(SESSION_DEFAULTS)
    applied["HF_TOKEN"] = read_hf_token(input_root, secret_reader)
    applied["MONARCH_WHISPER_COMPUTE"] = compute_type
    applied["LD_LIBRARY_PATH"] = library_path
    applied["PYTHONPATH"] = str(repo_root / "tribev2")

    target.update(applied)

    print(f"GPU capability sm_{capability_major}x -> whisper compute_type {compute_type}")
    print(f"cuDNN on loader path: {library_path.split(os.pathsep)[0]}")
    print("session environment ready")
    return applied
