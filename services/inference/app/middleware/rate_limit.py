"""Token bucket rate limiter for the inference server.

Each IP gets a bucket with max_tokens refilled at refill_rate.
Each request costs 1 token. When empty, 429 is returned.
Second line of defense after the Convex per-user rate limit.
"""

import time
from collections import defaultdict

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,  # type: ignore[override]
        max_tokens: int = 20,
        refill_rate: float = 0.5,
    ) -> None:
        super().__init__(app)
        self.max_tokens = max_tokens
        self.refill_rate = refill_rate
        self.buckets: dict[str, dict] = defaultdict(
            lambda: {"tokens": max_tokens, "last_refill": time.time()}
        )

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if request.url.path == "/health":
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        bucket = self.buckets[client_ip]

        now = time.time()
        elapsed = now - bucket["last_refill"]
        bucket["tokens"] = min(
            self.max_tokens,
            bucket["tokens"] + elapsed * self.refill_rate,
        )
        bucket["last_refill"] = now

        if bucket["tokens"] < 1:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Try again later.",
                headers={"Retry-After": str(int(1 / self.refill_rate))},
            )

        bucket["tokens"] -= 1
        return await call_next(request)
