"""FastAPI application entry point.

Loads the TRIBE v2 model into the singleton ``inference_service`` at
startup via the lifespan context manager. The lifespan honours the
``MONARCH_SKIP_MODEL_LOAD`` setting so the app can boot on a CPU-only
dev box without paying the (multi-GB, GPU-only) model download.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import __version__
from .config import settings
from .models.schemas import HealthResponse
from .routers import batch, compare, report, scan
from .services.inference import inference_service


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Bootstrap the inference singleton."""
    settings.cache_folder.mkdir(parents=True, exist_ok=True)
    settings.upload_folder.mkdir(parents=True, exist_ok=True)
    settings.data_folder.mkdir(parents=True, exist_ok=True)

    if settings.skip_model_load:
        print(
            "[Monarch] MONARCH_SKIP_MODEL_LOAD is set; TRIBE v2 will not be "
            "loaded. /api/scan will return 503 until you restart with "
            "MONARCH_SKIP_MODEL_LOAD=0."
        )
    else:
        print("[Monarch] Loading TRIBE v2 model...")
        inference_service.load_model()
        print("[Monarch] Server ready.")

    yield

    print("[Monarch] Shutting down.")


app = FastAPI(
    title="Monarch",
    description=(
        "Neural Processing Scanner API. Predicts cortical processing "
        "balance (NAA) from media content using TRIBE v2 and maps the "
        "result through a Landau / Ising mean-field opinion-dynamics layer."
    ),
    version=__version__,
    lifespan=lifespan,
)

# CORS for the Next.js frontend(s).
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers.
app.include_router(scan.router)
app.include_router(compare.router)
app.include_router(batch.router)
app.include_router(report.router)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        model_loaded=inference_service.is_loaded(),
        version=__version__,
    )
