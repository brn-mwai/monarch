"""Unit tests for app.services.inference.

Only the structural / non-GPU paths are tested here. The actual model
load + predict paths require TRIBE v2 + GPU and are exercised by the
smoke test on the deployment box.
"""

import pytest

from app.services.inference import TribeInferenceService, inference_service


def test_singleton_starts_unloaded():
    svc = TribeInferenceService()
    assert svc.is_loaded() is False


def test_predict_text_raises_when_unloaded():
    svc = TribeInferenceService()
    with pytest.raises(RuntimeError, match="not loaded"):
        svc.predict_text("hello world this is a longer string")


def test_module_singleton_exists():
    assert inference_service is not None
    # The module-level singleton may or may not be loaded depending on
    # the lifespan, but the instance must exist.
    assert hasattr(inference_service, "load_model")
    assert hasattr(inference_service, "predict_text")
    assert hasattr(inference_service, "predict_audio")
    assert hasattr(inference_service, "predict_video")
    assert hasattr(inference_service, "predict_multimodal")
