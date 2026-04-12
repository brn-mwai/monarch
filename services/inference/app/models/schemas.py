"""Pydantic schemas for request/response validation."""

from typing import Optional

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


# === Response models ===


class NAAResult(BaseModel):
    naa: float
    a_aff: float
    a_del: float
    classification: NAAClassification


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
    activation_url: str  # URL for the (20484,) Float32 binary blob


class CompareResponse(BaseModel):
    content_a: ScanResponse
    content_b: ScanResponse
    naa_difference: float


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    version: str
