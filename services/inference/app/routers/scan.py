"""POST /api/scan -- single-item scan and activation download."""

import uuid

import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import Response

from ..config import settings
from ..dependencies import require_loaded_model
from ..middleware.input_validation import validate_text_input
from ..models.schemas import (
    LandauResult,
    NAAResult,
    ROIBreakdown,
    ScanRequest,
    ScanResponse,
)
from ..services.alpha_calibration import load_alpha_hat
from ..services.inference import TribeInferenceService
from ..services.landau import compute_landau_analysis
from ..services.naa import VERTICES, compute_naa, compute_roi_breakdown
from ..services.stores import blob_store

router = APIRouter(prefix="/api", tags=["scan"])


def activation_key(scan_id: str) -> str:
    return f"act:{scan_id}"


def timeseries_key(scan_id: str) -> str:
    return f"ts:{scan_id}"


@router.post("/scan", response_model=ScanResponse)
async def scan_content(
    request: ScanRequest,
    model: TribeInferenceService = Depends(require_loaded_model),
) -> ScanResponse:
    """Scan a single content item and return NAA + Landau analysis.

    Currently only ``modality == "text"`` is wired to inference. Audio
    and video upload routes land in a follow-up phase via the dedicated
    ``UploadFile`` routers.
    """
    if request.modality.value == "text":
        if not request.text:
            raise HTTPException(400, "Text content required for text modality")
        # Server-side validation + sanitization (the frontend's pass is
        # bypassable). Then run the blocking model off the event loop so one
        # scan does not stall every other request on the single worker.
        clean_text = validate_text_input(request.text)
        result = await run_in_threadpool(model.predict_text, clean_text)
    else:
        raise HTTPException(
            501,
            f"Modality {request.modality.value} not yet implemented for direct upload",
        )

    item_vector = result["item_vector"]

    # NAA
    naa_dict = compute_naa(item_vector)
    if not naa_dict["valid"]:
        raise HTTPException(
            422,
            "NAA is undefined for this content: one or both ROI networks show "
            "below-baseline mean activation, so the affective/deliberative ratio "
            "is not a meaningful index. No processing-bias verdict is emitted.",
        )

    # Calibrated alpha_hat (or fallback)
    cal = load_alpha_hat(settings.alpha_hat_file)
    alpha_hat = cal["alpha_hat"]
    if cal["source"] == "fallback":
        print(
            f"[Monarch] WARNING: alpha_hat calibration not found at "
            f"{settings.alpha_hat_file}; using fallback {alpha_hat}"
        )

    # Landau analysis
    landau = compute_landau_analysis(
        naa=naa_dict["naa"],
        alpha_hat=alpha_hat,
        beta_j=settings.beta_j,
    )

    # Per-ROI breakdown
    breakdown = compute_roi_breakdown(item_vector)
    roi_list = [
        ROIBreakdown(name=name, **values) for name, values in breakdown.items()
    ]

    # Cache the static map and the per-TR series for the brain renderer.
    scan_id = str(uuid.uuid4())
    blob_store.put(activation_key(scan_id), item_vector)
    blob_store.put(
        timeseries_key(scan_id),
        np.ascontiguousarray(result["raw_preds"], dtype=np.float32),
    )

    return ScanResponse(
        scan_id=scan_id,
        naa=NAAResult(**naa_dict),
        landau=LandauResult(
            free_energy_m=landau["free_energy"]["m"],
            free_energy_F=landau["free_energy"]["F"],
            equilibrium_m=landau["equilibrium_m"],
            susceptibility=landau["susceptibility"],
            external_field_h=landau["external_field_h"],
            beta_j=landau["beta_j"],
            alpha_hat=landau["alpha_hat"],
        ),
        roi_breakdown=roi_list,
        modality=request.modality,
        n_trs=int(result["n_trs"]),
        activation_url=f"/api/scan/{scan_id}/activation",
        timeseries_url=f"/api/scan/{scan_id}/timeseries",
    )


@router.get("/scan/{scan_id}/activation")
async def get_activation(scan_id: str) -> Response:
    """Return the (20484,) activation vector as raw binary float32.

    The frontend brain renderer fetches this as an ``ArrayBuffer`` and
    wraps it in a ``Float32Array``. Total payload size is ``20484 * 4 =
    81,936`` bytes regardless of the input modality.
    """
    vector = blob_store.get(activation_key(scan_id))
    if vector is None:
        raise HTTPException(404, "Scan not found")

    return Response(
        content=vector.astype(np.float32).tobytes(),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename={scan_id}.bin",
            "X-Vertex-Count": "20484",
            "X-Dtype": "float32",
        },
    )


@router.get("/scan/{scan_id}/timeseries")
async def get_timeseries(scan_id: str) -> Response:
    """Return the (T, 20484) per-TR activation as raw frame-major float32.

    Frame ``f`` occupies bytes ``[f * 20484 * 4, (f + 1) * 20484 * 4)``. The
    frontend fetches this as an ``ArrayBuffer``, wraps it in a
    ``Float32Array``, and drives the brain playback at one frame per TR.
    """
    frames = blob_store.get(timeseries_key(scan_id))
    if frames is None:
        raise HTTPException(404, "Scan time series not found")

    if frames.ndim != 2 or frames.shape[1] != VERTICES:
        raise HTTPException(
            500,
            f"Unexpected time-series shape {frames.shape}; expected (T, {VERTICES})",
        )

    n_frames = int(frames.shape[0])
    return Response(
        content=frames.tobytes(),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename={scan_id}.timeseries.bin",
            "X-Frame-Count": str(n_frames),
            "X-Vertex-Count": str(VERTICES),
            "X-Dtype": "float32",
            "X-TR": "1.0",
        },
    )
