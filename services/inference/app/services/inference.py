"""TRIBE v2 model loading and inference.

Loads the model ONCE at server startup (via the FastAPI lifespan
context) and reuses the singleton for every request. Accepts text,
audio, or video content and returns:

- Raw predictions: ``(T, 20484)`` per-TR cortical activation
- Pooled item vector: ``(20484,)`` mean-pooled activation
- Per-modality vectors (for the multimodal RGB visualisation)

The model runs on AMD Instinct MI300X via ROCm in production. Device
selection is automatic ("auto" picks CUDA/ROCm if a GPU is available).

IMPORTANT: TRIBE v2 text inference internally:

  1. Writes text to a .txt file
  2. Synthesizes audio via gTTS
  3. Transcribes with WhisperX (subprocess) to recover word timings
  4. Runs through LLaMA 3.2-3B + Wav2Vec-BERT 2.0 + the fusion transformer

So even "text-only" inference uses audio processing internally. The
container must have ``gTTS``, ``langdetect``, and ``WhisperX``
(installable via ``uvx``) available on PATH.
"""

import tempfile
from pathlib import Path
from typing import Optional

import numpy as np

from ..config import settings
from .pooling import mean_pool


class TribeInferenceService:
    """Singleton TRIBE v2 inference wrapper.

    The wrapper deliberately does NOT import tribev2 at module level so
    that unit tests and the FastAPI app can boot on a CPU-only dev box
    without paying the import cost or failing on missing GPU drivers.
    The import happens inside ``load_model``.
    """

    def __init__(self) -> None:
        self.model = None
        self._loaded = False

    def load_model(self) -> None:
        """Load TRIBE v2 from HuggingFace. Call once at server startup."""
        from tribev2.demo_utils import TribeModel  # type: ignore

        settings.cache_folder.mkdir(parents=True, exist_ok=True)

        self.model = TribeModel.from_pretrained(
            settings.tribe_model_id,
            cache_folder=settings.cache_folder,
            device=settings.tribe_device,
        )
        self._loaded = True

        try:
            import torch  # type: ignore

            device = next(self.model.parameters()).device  # type: ignore
            print(f"[Monarch] TRIBE v2 loaded on {device}")
            del torch
        except Exception:
            print("[Monarch] TRIBE v2 loaded (device introspection skipped)")

    def is_loaded(self) -> bool:
        return self._loaded

    # ----- Per-modality predictors -----

    def predict_text(self, text: str) -> dict:
        """Run inference on text content.

        Returns
        -------
        dict
            ``raw_preds``: (T, 20484) numpy array
            ``item_vector``: (20484,) mean-pooled numpy array
            ``n_trs``: int
            ``modality``: "text"
        """
        self._check_loaded()

        settings.upload_folder.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".txt",
            delete=False,
            dir=str(settings.upload_folder),
            encoding="utf-8",
        ) as f:
            f.write(text)
            text_path = Path(f.name)

        try:
            events_df = self.model.get_events_dataframe(text_path=text_path)  # type: ignore
            preds, _segments = self.model.predict(events=events_df)  # type: ignore
            preds_np = np.asarray(preds)
            item_vector = mean_pool(preds_np)
            return {
                "raw_preds": preds_np,
                "item_vector": item_vector,
                "n_trs": int(preds_np.shape[0]),
                "modality": "text",
            }
        finally:
            text_path.unlink(missing_ok=True)

    def predict_audio(self, audio_path: Path) -> dict:
        """Run inference on audio content."""
        self._check_loaded()
        events_df = self.model.get_events_dataframe(audio_path=str(audio_path))  # type: ignore
        preds, _segments = self.model.predict(events=events_df)  # type: ignore
        preds_np = np.asarray(preds)
        item_vector = mean_pool(preds_np)
        return {
            "raw_preds": preds_np,
            "item_vector": item_vector,
            "n_trs": int(preds_np.shape[0]),
            "modality": "audio",
        }

    def predict_video(self, video_path: Path) -> dict:
        """Run inference on video content."""
        self._check_loaded()
        events_df = self.model.get_events_dataframe(video_path=str(video_path))  # type: ignore
        preds, _segments = self.model.predict(events=events_df)  # type: ignore
        preds_np = np.asarray(preds)
        item_vector = mean_pool(preds_np)
        return {
            "raw_preds": preds_np,
            "item_vector": item_vector,
            "n_trs": int(preds_np.shape[0]),
            "modality": "video",
        }

    def predict_multimodal(
        self,
        text: Optional[str] = None,
        audio_path: Optional[Path] = None,
        video_path: Optional[Path] = None,
    ) -> dict:
        """Run separate per-modality passes for the multimodal RGB visualisation.

        Returns individual activation vectors for each modality plus a
        ``combined`` vector that is the simple average across modalities.
        At least one modality must be provided.
        """
        self._check_loaded()

        results: dict[str, np.ndarray] = {}
        vectors: list[np.ndarray] = []

        if text is not None:
            r = self.predict_text(text)
            results["text"] = r["item_vector"]
            vectors.append(r["item_vector"])
        if audio_path is not None:
            r = self.predict_audio(audio_path)
            results["audio"] = r["item_vector"]
            vectors.append(r["item_vector"])
        if video_path is not None:
            r = self.predict_video(video_path)
            results["video"] = r["item_vector"]
            vectors.append(r["item_vector"])

        if not vectors:
            raise ValueError("At least one modality must be provided")

        results["combined"] = np.mean(vectors, axis=0)
        return results

    def _check_loaded(self) -> None:
        if not self._loaded:
            raise RuntimeError(
                "TRIBE v2 model not loaded. Call load_model() first or "
                "set MONARCH_SKIP_MODEL_LOAD=0."
            )


# Singleton instance reused across the FastAPI app.
inference_service = TribeInferenceService()
