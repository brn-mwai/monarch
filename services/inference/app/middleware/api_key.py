"""API key authentication for the inference server.

The gateway (Convex) sends a bearer token; requests without a valid key
are rejected with 401. This stops anyone who discovers the inference URL
from running scans directly and bypassing the gateway's credit limits.

The expected key is injected at registration (not read from the
environment here) and compared with ``hmac.compare_digest`` so the check
is constant-time and cannot be brute-forced byte-by-byte.
"""

import hmac
from collections.abc import Iterable

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class APIKeyMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        api_key: str,
        exempt_paths: Iterable[str] = ("/health",),
    ) -> None:
        super().__init__(app)
        self._api_key = api_key
        self._exempt_paths = set(exempt_paths)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if request.url.path in self._exempt_paths:
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                {"detail": "Missing or malformed Authorization header"},
                status_code=401,
            )

        token = auth_header[len("Bearer ") :]
        if not hmac.compare_digest(token, self._api_key):
            return JSONResponse({"detail": "Invalid API key"}, status_code=401)

        return await call_next(request)
