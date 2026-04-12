"""POST /api/scan -- single-item scan and activation download."""

import uuid

import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from ..config import settings
from ..dependencies import require_loaded_model
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
from ..services.naa import compute_naa, compute_roi_breakdown

router = APIRouter(prefix="/api", tags=["scan"])

# In-memory store for activation vectors. Replace with Redis or a small
# SQLite cache when the API moves out of single-process mode.
_activation_store: dict[str, np.ndarray] = {}


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
        result = model.predict_text(request.text)
    else:
        raise HTTPException(
            501,
            f"Modality {request.modality.value} not yet implemented for direct upload",
        )

    item_vector = result["item_vector"]

    # NAA
    naa_dict = compute_naa(item_vector)

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

    # Cache activation for the brain renderer
    scan_id = str(uuid.uuid4())
    _activation_store[scan_id] = item_vector

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
    )


@router.get("/scan/{scan_id}/activation")
async def get_activation(scan_id: str) -> Response:
    """Return the (20484,) activation vector as raw binary float32.

    The frontend brain renderer fetches this as an ``ArrayBuffer`` and
    wraps it in a ``Float32Array``. Total payload size is ``20484 * 4 =
    81,936`` bytes regardless of the input modality.
    """
    if scan_id not in _activation_store:
        raise HTTPException(404, "Scan not found")

    vector = _activation_store[scan_id]
    return Response(
        content=vector.astype(np.float32).tobytes(),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename={scan_id}.bin",
            "X-Vertex-Count": "20484",
            "X-Dtype": "float32",
        },
    )
