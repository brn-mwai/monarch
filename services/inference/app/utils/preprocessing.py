"""Per-modality preprocessing helpers.

Stub. Most preprocessing happens inside TRIBE v2's
``get_events_dataframe`` (text -> gTTS audio -> WhisperX timings;
audio -> WhisperX; video -> frame extraction). This module hosts the
thin wrappers Monarch needs on top -- e.g. enforcing max-length limits,
language detection, simple SRT extraction.
"""

from langdetect import detect, LangDetectException


def detect_language(text: str, fallback: str = "en") -> str:
    """Best-effort language detection. Falls back to ``en`` on failure.

    TRIBE v2's gTTS step needs a language code; if langdetect cannot
    decide we use English so the pipeline does not crash.
    """
    try:
        return detect(text)
    except LangDetectException:
        return fallback
