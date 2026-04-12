"""Application configuration loaded from environment variables.

All settings are prefixed with `MONARCH_` (e.g. `MONARCH_TRIBE_DEVICE=cuda`).
The Settings class uses pydantic-settings v2; values are immutable after
construction so the singleton can be safely shared across requests.
"""

from pathlib import Path
from typing import Tuple

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

    # === Batch ===
    max_batch_size: int = 1500

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
