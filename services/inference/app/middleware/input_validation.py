"""Defense-in-depth input validation.

Frontend sanitizes first. Server re-validates everything
because frontend validation can be bypassed.
"""

import re
import unicodedata

from fastapi import HTTPException, UploadFile

MAX_TEXT_LENGTH = 10_000
MIN_TEXT_LENGTH = 10
MAX_AUDIO_SIZE_MB = 50
MAX_VIDEO_SIZE_MB = 200

ALLOWED_AUDIO_TYPES = {"audio/wav", "audio/mpeg", "audio/mp3", "audio/x-wav"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/quicktime", "video/x-msvideo"}

INJECTION_PATTERNS = [
    r"<script",
    r"javascript:",
    r"data:text/html",
    r"on\w+\s*=",
    r"\{\{",
    r"\$\{",
    r"__proto__",
    r"eval\s*\(",
    r"Function\s*\(",
    r"; *DROP ",
    r"; *DELETE ",
    r"UNION\s+SELECT",
    r"' *OR *'1",
]

INJECTION_REGEX = re.compile(
    "|".join(INJECTION_PATTERNS),
    re.IGNORECASE | re.DOTALL,
)


def deep_sanitize_text(text: str) -> str:
    """Server-side text sanitization."""
    text = text.replace("\x00", "")
    text = "".join(
        c for c in text if unicodedata.category(c) != "Cc" or c in "\n\r\t"
    )
    text = re.sub(r"[\u200e\u200f\u202a-\u202e\u2066-\u2069]", "", text)
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"<[^>]*>", "", text)
    if INJECTION_REGEX.search(text):
        raise HTTPException(
            400,
            "Input contains potentially dangerous content and was rejected.",
        )
    return text.strip()


def validate_text_input(text: str) -> str:
    """Validate and sanitize text input."""
    if len(text) < MIN_TEXT_LENGTH:
        raise HTTPException(400, f"Text must be at least {MIN_TEXT_LENGTH} characters")
    if len(text) > MAX_TEXT_LENGTH:
        raise HTTPException(400, f"Text must be under {MAX_TEXT_LENGTH} characters")
    return deep_sanitize_text(text)


async def validate_audio_upload(file: UploadFile) -> None:
    """Validate audio file upload."""
    if file.content_type not in ALLOWED_AUDIO_TYPES:
        raise HTTPException(400, f"Invalid audio type: {file.content_type}")
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > MAX_AUDIO_SIZE_MB:
        raise HTTPException(400, f"Audio too large: {size_mb:.1f}MB (max {MAX_AUDIO_SIZE_MB}MB)")
    await file.seek(0)


async def validate_video_upload(file: UploadFile) -> None:
    """Validate video file upload."""
    if file.content_type not in ALLOWED_VIDEO_TYPES:
        raise HTTPException(400, f"Invalid video type: {file.content_type}")
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > MAX_VIDEO_SIZE_MB:
        raise HTTPException(400, f"Video too large: {size_mb:.1f}MB (max {MAX_VIDEO_SIZE_MB}MB)")
    await file.seek(0)


def validate_filename(filename: str) -> str:
    """Sanitize uploaded file names to prevent path traversal."""
    filename = filename.replace("/", "").replace("\\", "")
    filename = filename.replace("..", "")
    filename = filename.replace("\x00", "")
    filename = re.sub(r"[^a-zA-Z0-9_\-.]", "_", filename)
    return filename[:255]
