"""POST /api/batch -- batch corpus scan with checkpoint-resume.

Stub. The full handler will accept an uploaded JSONL or CSV manifest,
create a ``BatchCheckpoint``, dispatch inference items in cost order
(text -> audio -> video), and stream progress updates over a websocket.
"""

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api", tags=["batch"])


@router.post("/batch")
async def submit_batch() -> dict:
    raise HTTPException(501, "Batch endpoint lands in a follow-up phase.")
