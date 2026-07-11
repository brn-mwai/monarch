"""Report endpoints.

``POST /api/report`` produces the plain-language audit narrative for a
completed scan. ``GET /api/report/{scan_id}.pdf`` renders the full PDF report
(logo, audit, NAA gauge, physics curves, ROI breakdown). Both rebuild the
numeric summaries (NAA, Landau, per-ROI) from the cached activation vector --
cheap, no GPU -- so the report is always grounded in the server's own numbers.
"""

import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse

from ..config import settings
from ..models.schemas import (
    ReportAuditRequest,
    ReportPdfRequest,
    ReportRequest,
    ReportResponse,
)
from ..services.alpha_calibration import load_alpha_hat
from ..services.gemma_report import build_report_context, generate_report
from ..services.landau import compute_landau_analysis
from ..services.naa import compute_naa, compute_roi_breakdown
from ..services.report_generator import generate_pdf_report
from ..services.stores import blob_store
from .scan import activation_key

router = APIRouter(prefix="/api", tags=["report"])


def _rebuild(scan_id: str, content_excerpt: str | None, demographic: str = "general") -> dict:
    """Recompute NAA + Landau + ROI + audit from the cached activation."""
    item_vector = blob_store.get(activation_key(scan_id))
    if item_vector is None:
        raise HTTPException(
            404,
            "Scan activation not found or expired; re-run the scan before "
            "requesting its report.",
        )

    naa_result = compute_naa(item_vector)
    calibration = load_alpha_hat(settings.alpha_hat_file)
    landau_result = compute_landau_analysis(
        naa=naa_result["naa"] if naa_result["valid"] else 0.0,
        alpha_hat=calibration["alpha_hat"],
        beta_j=settings.beta_j,
    )
    # Per-ROI breakdown needs the tribev2 vertex atlas; degrade to empty on a
    # dev box without it so the rest of the report still renders.
    try:
        roi_breakdown = compute_roi_breakdown(item_vector)
    except RuntimeError:
        roi_breakdown = {}

    context = build_report_context(
        naa_result=naa_result,
        landau_result=landau_result,
        roi_breakdown=roi_breakdown,
        alpha_source=calibration["source"],
        content_excerpt=content_excerpt,
        demographic=demographic,
    )
    audit = generate_report(context, cfg=settings)
    return {
        "naa": naa_result,
        "landau": landau_result,
        "roi": roi_breakdown,
        "audit": audit,
        "demographic": demographic,
    }


def _roi_list_to_map(roi_breakdown: list[dict]) -> dict:
    """The report context wants a name-keyed map; the UI carries an ordered list."""
    roi_map: dict[str, dict] = {}
    for row in roi_breakdown:
        name = row.get("name")
        if not name:
            continue
        roi_map[name] = {
            "activation": row.get("activation", 0.0),
            "system": row.get("system", "deliberative"),
            "vertex_count": row.get("vertex_count", 0),
        }
    return roi_map


@router.post("/report", response_model=ReportResponse)
async def create_report(request: ReportRequest) -> ReportResponse:
    """Plain-language audit narrative (Gemma or template) for a cached scan."""
    parts = _rebuild(request.scan_id, request.content_excerpt, request.demographic)
    return ReportResponse(**parts["audit"])


@router.post("/report/audit", response_model=ReportResponse)
async def create_report_audit(request: ReportAuditRequest) -> ReportResponse:
    """Gemma audit narrative from client-supplied numbers (no cache needed)."""
    calibration = load_alpha_hat(settings.alpha_hat_file)
    # The UI carries naa without the server's `valid` flag; treat a numeric
    # naa as valid so the narrative is written, not the "undefined" fallback.
    naa = {**request.naa}
    naa.setdefault("valid", naa.get("naa") is not None)
    context = build_report_context(
        naa_result=naa,
        landau_result=request.landau,
        roi_breakdown=_roi_list_to_map(request.roi_breakdown),
        alpha_source=calibration["source"],
        content_excerpt=request.content_excerpt,
        modality=request.modality,
        demographic=request.demographic,
    )
    audit = generate_report(context, cfg=settings)
    return ReportResponse(**audit)


def _roi_list_to_map(roi_breakdown: list[dict]) -> dict:
    """The PDF chart wants a name-keyed map; the UI carries an ordered list."""
    roi_map: dict[str, dict] = {}
    for row in roi_breakdown:
        name = row.get("name")
        if not name:
            continue
        roi_map[name] = {
            "activation": row.get("activation", 0.0),
            "system": row.get("system", "deliberative"),
            "vertex_count": row.get("vertex_count", 0),
        }
    return roi_map


@router.post("/report/pdf")
async def create_report_pdf(request: ReportPdfRequest) -> FileResponse:
    """Render the full PDF from client-supplied numbers (no cache lookup)."""
    out = Path(tempfile.gettempdir()) / f"monarch-{request.scan_id}-{uuid.uuid4().hex[:8]}.pdf"
    await run_in_threadpool(
        generate_pdf_report,
        request.scan_id,
        request.naa,
        request.landau,
        _roi_list_to_map(request.roi_breakdown),
        out,
        audit=request.audit,
        content_excerpt=request.content_excerpt,
        modality=request.modality,
        demographic=request.demographic,
    )
    return FileResponse(
        out,
        media_type="application/pdf",
        filename=f"monarch-scan-{request.scan_id[:12]}.pdf",
    )


@router.get("/report/{scan_id}.pdf")
async def get_report_pdf(
    scan_id: str,
    content_excerpt: str | None = None,
    demographic: str = "general",
) -> FileResponse:
    """Render the full PDF report for a cached scan."""
    parts = _rebuild(scan_id, content_excerpt, demographic)
    out = Path(tempfile.gettempdir()) / f"monarch-{scan_id}-{uuid.uuid4().hex[:8]}.pdf"
    # PDF assembly (matplotlib + reportlab) is blocking -- keep it off the loop.
    await run_in_threadpool(
        generate_pdf_report,
        scan_id,
        parts["naa"],
        parts["landau"],
        parts["roi"],
        out,
        audit=parts["audit"],
        content_excerpt=content_excerpt,
        demographic=demographic,
    )
    return FileResponse(
        out,
        media_type="application/pdf",
        filename=f"monarch-scan-{scan_id[:12]}.pdf",
    )
