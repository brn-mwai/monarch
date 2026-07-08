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
from .middleware.api_key import APIKeyMiddleware
from .middleware.rate_limit import RateLimitMiddleware
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

# Middleware runs outermost-first in reverse registration order, so the
# request flow is: CORS -> rate limit -> auth -> route. Auth and rate limit
# are added before CORS here so CORS ends up outermost (preflight + headers
# are handled before any rejection).
if settings.inference_api_key:
    app.add_middleware(APIKeyMiddleware, api_key=settings.inference_api_key)
else:
    print(
        "[Monarch] WARNING: INFERENCE_API_KEY is not set; API authentication "
        "is DISABLED. Set it before exposing this service publicly."
    )

app.add_middleware(
    RateLimitMiddleware,
    max_tokens=settings.rate_limit_max_tokens,
    refill_rate=settings.rate_limit_refill_rate,
    trust_proxy=settings.trust_proxy,
)

# CORS for the Next.js frontend(s). Explicit methods/headers rather than
# wildcards since credentials are allowed.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
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
