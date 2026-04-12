"""GET /api/report/{scan_id} -- retrieve a generated PDF report.

Stub. Implementation lands in a follow-up phase together with
``services.report_generator``.
"""

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api", tags=["report"])


@router.get("/report/{scan_id}")
async def get_report(_scan_id: str) -> dict:
    raise HTTPException(501, "Report endpoint lands in a follow-up phase.")
