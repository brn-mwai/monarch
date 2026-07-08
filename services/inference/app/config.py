"""Application configuration loaded from environment variables.

All settings are prefixed with `MONARCH_` (e.g. `MONARCH_TRIBE_DEVICE=cuda`).
The Settings class uses pydantic-settings v2; values are immutable after
construction so the singleton can be safely shared across requests.
"""

from pathlib import Path
from typing import Tuple

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # === Paths ===
    cache_folder: Path = Path("./cache")
    data_folder: Path = Path("./data")
    upload_folder: Path = Path("./uploads")

    # === TRIBE v2 ===
    tribe_model_id: str = "facebook/tribev2"
    tribe_device: str = "auto"  # "auto", "cuda", "cpu"
    # When True, the FastAPI lifespan startup will NOT load the TRIBE v2
    # weights. Useful for local dev / CI / running unit tests against the
    # FastAPI app without a GPU. The /api/scan endpoint will return 503
    # while the model is unloaded.
    skip_model_load: bool = False

    # === NAA ===
    # Regularization constant in eq. (4) -- prevents division by zero
    # when the deliberative-control system has near-zero activation.
    naa_delta: float = 1e-3

    # === Ising / Landau ===
    # Social coupling constant. Default 0.7 follows Castellano et al.
    # (2009) "Statistical physics of social dynamics".
    beta_j: float = 0.7
    beta_j_range: Tuple[float, float] = (0.5, 2.0)
    beta_j_step: float = 0.1

    # === Calibration ===
    alpha_hat_file: Path = Path("./data/alpha_hat.json")

    # === Gemma report (via Fireworks AI on AMD hardware) ===
    # Read from FIREWORKS_API_KEY (no MONARCH_ prefix) to match the
    # Fireworks-issued env name. Empty disables the LLM call and the
    # report service falls back to a deterministic template.
    fireworks_api_key: str = Field(default="", validation_alias="FIREWORKS_API_KEY")
    fireworks_base_url: str = "https://api.fireworks.ai/inference/v1"
    # Fireworks model slug for Gemma. Verify against the live Fireworks
    # catalogue before the demo -- slugs change between model generations.
    gemma_model: str = "accounts/fireworks/models/gemma-2-9b-it"
    report_max_tokens: int = 600
    report_temperature: float = 0.4
    report_timeout_seconds: float = 30.0

    # === Batch ===
    max_batch_size: int = 1500

    # === Auth ===
    # Bearer token the gateway (Convex) sends. Read from INFERENCE_API_KEY
    # (no MONARCH_ prefix) to match the deployment env name. Empty disables
    # auth and the app logs a loud warning at startup.
    inference_api_key: str = Field(default="", validation_alias="INFERENCE_API_KEY")

    # === Rate limiting ===
    rate_limit_max_tokens: int = 20
    rate_limit_refill_rate: float = 0.5  # tokens per second
    # Behind a load balancer the socket peer is the LB; trust the first
    # X-Forwarded-For hop for per-client buckets. Disable if not proxied.
    trust_proxy: bool = True

    # === Blob store (activation + time-series cache) ===
    # Empty redis_url falls back to the in-memory store (single-process dev).
    redis_url: str = ""
    blob_ttl_seconds: int = 3600
    blob_max_entries: int = 256

    # === Server ===
    host: str = "0.0.0.0"
    port: int = 8000

    # === CORS ===
    # Comma-separated list passed via env (MONARCH_CORS_ORIGINS=...).
    cors_origins: str = (
        "http://localhost:3000,http://localhost:3300,https://monarch.brianmwai.com"
    )

    model_config = SettingsConfigDict(
        env_prefix="MONARCH_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
