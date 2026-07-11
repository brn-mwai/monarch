"""POST /api/batch -- score a corpus of text items by NAA.

Runs each item through the text encoder, computes NAA, and returns the
corpus ranked most-reactive first. Items whose NAA is undefined (a network
below baseline) are reported with ``naa: null`` rather than dropped, so the
caller sees the full corpus. The model is required; on a box without it the
route returns 503 via the shared dependency.
"""

from fastapi import APIRouter, Depends
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from ..dependencies import require_loaded_model
from ..middleware.input_validation import validate_text_input
from ..services.inference import TribeInferenceService
from ..services.naa import compute_naa

router = APIRouter(prefix="/api", tags=["batch"])

MAX_ITEMS = 1500


class BatchItem(BaseModel):
    id: str = Field(..., min_length=1, max_length=200)
    text: str = Field(..., min_length=1, max_length=10000)
    category: str | None = Field(None, max_length=60)


class BatchRequest(BaseModel):
    items: list[BatchItem] = Field(..., min_length=1, max_length=MAX_ITEMS)


class BatchResult(BaseModel):
    id: str
    category: str | None
    naa: float | None
    classification: str


class BatchResponse(BaseModel):
    count: int
    results: list[BatchResult]


@router.post("/batch", response_model=BatchResponse)
async def submit_batch(
    request: BatchRequest,
    model: TribeInferenceService = Depends(require_loaded_model),
) -> BatchResponse:
    results: list[BatchResult] = []
    for item in request.items:
        prediction = await run_in_threadpool(
            model.predict_text, validate_text_input(item.text)
        )
        naa_dict = compute_naa(prediction["item_vector"])
        results.append(
            BatchResult(
                id=item.id,
                category=item.category,
                naa=naa_dict["naa"] if naa_dict["valid"] else None,
                classification=naa_dict["classification"],
            )
        )

    # Most reactive first; undefined-NAA items sink to the bottom.
    results.sort(key=lambda r: (r.naa is None, -(r.naa or 0.0)))
    return BatchResponse(count=len(results), results=results)
