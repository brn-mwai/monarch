"""POST /api/scan -- single-item scan and activation download."""

import tempfile
import uuid
from pathlib import Path

import numpy as np
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import Response

from ..config import settings
from ..dependencies import require_loaded_model
from ..middleware.input_validation import validate_text_input
from ..models.enums import Modality
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


def _build_scan_response(result: dict, modality: Modality) -> ScanResponse:
    """Turn a model prediction into NAA + Landau + ROI + cached vectors.

    Shared by the text, upload, and multimodal scan routes so the numeric
    pipeline lives in exactly one place.
    """
    item_vector = result["item_vector"]

    naa_dict = compute_naa(item_vector)
    if not naa_dict["valid"]:
        raise HTTPException(
            422,
            "NAA is undefined for this content: one or both ROI networks show "
            "below-baseline mean activation, so the affective/deliberative ratio "
            "is not a meaningful index. No processing-bias verdict is emitted.",
        )

    cal = load_alpha_hat(settings.alpha_hat_file)
    alpha_hat = cal["alpha_hat"]
    if cal["source"] == "fallback":
        print(
            f"[Monarch] WARNING: alpha_hat calibration not found at "
            f"{settings.alpha_hat_file}; using fallback {alpha_hat}"
        )

    landau = compute_landau_analysis(
        naa=naa_dict["naa"],
        alpha_hat=alpha_hat,
        beta_j=settings.beta_j,
    )

    breakdown = compute_roi_breakdown(item_vector)
    roi_list = [
        ROIBreakdown(name=name, **values) for name, values in breakdown.items()
    ]

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
        modality=modality,
        n_trs=int(result["n_trs"]),
        activation_url=f"/api/scan/{scan_id}/activation",
        timeseries_url=f"/api/scan/{scan_id}/timeseries",
    )


async def _save_upload(file: UploadFile, suffix: str) -> Path:
    """Persist an upload to the upload folder and return its path."""
    settings.upload_folder.mkdir(parents=True, exist_ok=True)
    dest = settings.upload_folder / f"{uuid.uuid4().hex}{suffix}"
    dest.write_bytes(await file.read())
    return dest


@router.post("/scan", response_model=ScanResponse)
async def scan_content(
    request: ScanRequest,
    model: TribeInferenceService = Depends(require_loaded_model),
) -> ScanResponse:
    """Scan a single TEXT content item and return NAA + Landau analysis.

    Audio and video arrive via the multipart ``/api/scan/upload`` route.
    """
    if request.modality.value != "text":
        raise HTTPException(
            400,
            "Use POST /api/scan/upload for audio or video; /api/scan is text-only.",
        )
    if not request.text:
        raise HTTPException(400, "Text content required for text modality")
    # Server-side validation + sanitization (the frontend's pass is
    # bypassable). Then run the blocking model off the event loop so one
    # scan does not stall every other request on the single worker.
    clean_text = validate_text_input(request.text)
    result = await run_in_threadpool(model.predict_text, clean_text)
    return _build_scan_response(result, Modality.TEXT)


@router.post("/scan/upload", response_model=ScanResponse)
async def scan_upload(
    file: UploadFile = File(...),
    modality: str = Form("video"),
    model: TribeInferenceService = Depends(require_loaded_model),
) -> ScanResponse:
    """Scan an uploaded audio or video file through the matching TRIBE encoder.

    Audio routes to the Wav2Vec-BERT encoder; video routes to V-JEPA 2. The
    numeric pipeline (NAA/Landau/ROI) is identical to the text route.
    """
    kind = (modality or "").lower()
    if kind not in ("audio", "video"):
        raise HTTPException(400, "modality must be 'audio' or 'video'")

    suffix = Path(file.filename or "").suffix or (".wav" if kind == "audio" else ".mp4")
    saved = await _save_upload(file, suffix)
    try:
        predictor = model.predict_audio if kind == "audio" else model.predict_video
        result = await run_in_threadpool(predictor, saved)
        return _build_scan_response(result, Modality(kind))
    finally:
        saved.unlink(missing_ok=True)


@router.post("/scan/multimodal")
async def scan_multimodal(
    text: str | None = Form(None),
    audio: UploadFile | None = File(None),
    video: UploadFile | None = File(None),
    model: TribeInferenceService = Depends(require_loaded_model),
) -> dict:
    """Run separate per-modality TRIBE passes for the RGB multimodal view.

    Each supplied modality (text / audio / video) is encoded on its own and
    the results are combined (mean) -- this is the decomposition behind the
    red=text, green=audio, blue=video cortical map from the TRIBE paper. At
    least one modality is required. Caches each vector and returns its NAA +
    activation URL.
    """
    saved: list[Path] = []
    try:
        audio_path = video_path = None
        clean_text = validate_text_input(text) if text else None
        if audio is not None:
            audio_path = await _save_upload(audio, Path(audio.filename or "a.wav").suffix or ".wav")
            saved.append(audio_path)
        if video is not None:
            video_path = await _save_upload(video, Path(video.filename or "v.mp4").suffix or ".mp4")
            saved.append(video_path)

        if clean_text is None and audio_path is None and video_path is None:
            raise HTTPException(400, "Provide at least one of text, audio, or video.")

        vectors = await run_in_threadpool(
            model.predict_multimodal, clean_text, audio_path, video_path
        )
    finally:
        for p in saved:
            p.unlink(missing_ok=True)

    scan_id = str(uuid.uuid4())
    out: dict[str, dict] = {}
    for channel, vector in vectors.items():
        key = f"{scan_id}:{channel}"
        blob_store.put(activation_key(key), vector)
        naa_dict = compute_naa(vector)
        out[channel] = {
            "naa": naa_dict["naa"] if naa_dict["valid"] else None,
            "activation_url": f"/api/scan/{key}/activation",
        }
    return {"scan_id": scan_id, "channels": out}


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
