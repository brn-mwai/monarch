"""POST /api/compare -- side-by-side scan of two content items.

Stub. The full handler will run two scans, compute the NAA difference,
and return a ``CompareResponse``. Wired into the app router for path
discovery; returns 501 until inference is fully verified on the AMD
deployment box.
"""

from fastapi import APIRouter, HTTPException

from ..models.schemas import CompareRequest, CompareResponse

router = APIRouter(prefix="/api", tags=["compare"])


@router.post("/compare", response_model=CompareResponse)
async def compare_content(_request: CompareRequest) -> CompareResponse:
    raise HTTPException(501, "Compare endpoint lands in a follow-up phase.")
