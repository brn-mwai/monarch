"""Pydantic schemas for request/response validation."""

from typing import Any, Optional

from pydantic import BaseModel, Field

from .enums import Modality, NAAClassification


# === Request models ===


class ScanRequest(BaseModel):
    text: Optional[str] = Field(None, min_length=10, max_length=10000)
    modality: Modality = Modality.TEXT


class CompareRequest(BaseModel):
    content_a: str = Field(..., min_length=10, max_length=10000)
    content_b: str = Field(..., min_length=10, max_length=10000)
    modality: Modality = Modality.TEXT


class ReportRequest(BaseModel):
    scan_id: str = Field(..., min_length=1, max_length=100)
    content_excerpt: Optional[str] = Field(None, max_length=10000)
    demographic: str = Field("general", max_length=40)


class ReportPdfRequest(BaseModel):
    """Render a PDF from numbers the client already holds.

    Decouples the PDF from the server-side activation cache so any scan the
    UI is showing -- live or synthetic demo -- renders exactly what is on
    screen, no re-computation.
    """

    scan_id: str = Field(..., min_length=1, max_length=100)
    naa: dict[str, Any]
    landau: dict[str, Any]
    roi_breakdown: list[dict[str, Any]] = Field(default_factory=list)
    audit: Optional[dict[str, Any]] = None
    content_excerpt: Optional[str] = Field(None, max_length=10000)
    demographic: str = Field("general", max_length=40)
    modality: str = Field("text", max_length=20)


class ReportAuditRequest(BaseModel):
    """Generate the Gemma audit narrative from numbers the client holds.

    Lets the plain-language report work for any scan the UI is showing -- live
    or synthetic demo -- without a server-side cached activation, so the
    Gemma-written report is demoable even before the model is on the pod.
    """

    naa: dict[str, Any]
    landau: dict[str, Any]
    roi_breakdown: list[dict[str, Any]] = Field(default_factory=list)
    content_excerpt: Optional[str] = Field(None, max_length=10000)
    demographic: str = Field("general", max_length=40)
    modality: str = Field("text", max_length=20)


# === Response models ===


class NAAResult(BaseModel):
    naa: float
    a_aff: float
    a_del: float
    classification: NAAClassification
    valid: bool = True


class LandauResult(BaseModel):
    free_energy_m: list[float]
    free_energy_F: list[float]
    equilibrium_m: float
    susceptibility: Optional[float]
    external_field_h: float
    beta_j: float
    alpha_hat: float


class ROIBreakdown(BaseModel):
    name: str
    activation: float
    system: str
    vertex_count: int


class ScanResponse(BaseModel):
    scan_id: str
    naa: NAAResult
    landau: LandauResult
    roi_breakdown: list[ROIBreakdown]
    modality: Modality
    n_trs: int
    activation_url: str  # URL for the predicted (20484,) Float32 binary blob
    timeseries_url: Optional[str] = None  # URL for the (T, 20484) Float32 playback blob
    # URL for a recorded ground-truth (20484,) Float32 blob, present only for
    # benchmark stimuli that ship with real fMRI. None for arbitrary content,
    # which has no recorded reference -- the client renders an honest
    # "reference unavailable" state rather than inventing one.
    true_activation_url: Optional[str] = None


class CompareResponse(BaseModel):
    content_a: ScanResponse
    content_b: ScanResponse
    naa_difference: float


class ReportResponse(BaseModel):
    summary: str
    source: str  # "gemma" (Fireworks) or "fallback" (deterministic template)
    model: str


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    version: str
