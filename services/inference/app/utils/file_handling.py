"""Temp-file management for upload routes.

Stub. The upload routers will eventually use these helpers to
materialise FastAPI ``UploadFile`` instances onto disk so TRIBE v2's
file-path-based event extraction can read them.
"""

import shutil
from pathlib import Path

from fastapi import UploadFile

from ..config import settings


def save_upload_to_disk(upload: UploadFile, suffix: str) -> Path:
    """Stream a FastAPI UploadFile to disk under ``settings.upload_folder``.

    Returns the on-disk path. Caller is responsible for deleting it once
    inference completes.
    """
    settings.upload_folder.mkdir(parents=True, exist_ok=True)
    target = settings.upload_folder / f"{upload.filename}{suffix}"
    with target.open("wb") as f:
        shutil.copyfileobj(upload.file, f)
    return target
