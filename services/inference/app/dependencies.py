"""Shared FastAPI dependencies.

Currently a thin layer over the singleton inference service. Kept as a
separate module so future per-request scoping (auth, rate limiting,
tenant isolation) can be added without churning every router.
"""

from fastapi import HTTPException

from .services.inference import inference_service


def require_loaded_model():
    """Dependency that returns the loaded TribeInferenceService or 503s."""
    if not inference_service.is_loaded():
        raise HTTPException(
            status_code=503,
            detail="TRIBE v2 model not loaded yet. Try again in a moment.",
        )
    return inference_service
