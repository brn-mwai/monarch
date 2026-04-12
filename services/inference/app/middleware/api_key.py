"""API key authentication for the inference server.

Convex actions include an API key in the Authorization header.
Requests without a valid key are rejected with 401. This prevents
anyone who discovers the inference URL from running scans directly,
bypassing credit limits and rate limits.
"""

import os

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

INFERENCE_API_KEY = os.environ.get("INFERENCE_API_KEY", "")


class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if request.url.path == "/health":
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise HTTPException(401, "Missing Authorization header")

        token = auth_header[7:]
        if not INFERENCE_API_KEY or token != INFERENCE_API_KEY:
            raise HTTPException(401, "Invalid API key")

        return await call_next(request)
