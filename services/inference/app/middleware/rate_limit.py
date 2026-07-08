"""Token-bucket rate limiter for the inference server.

Each client gets a bucket of ``max_tokens`` refilled at ``refill_rate``
tokens/second; each request costs one token; an empty bucket returns 429.
Second line of defense after the gateway's per-user limit.

Behind a load balancer the socket peer is the balancer, so all clients
would share one bucket. With ``trust_proxy`` the first ``X-Forwarded-For``
hop identifies the client instead. Idle buckets are evicted so the table
cannot grow without bound.
"""

import time
from collections import OrderedDict

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

EXEMPT_PATHS = {"/health"}
IDLE_EVICTION_SECONDS = 3600
MAX_BUCKETS = 10_000


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        max_tokens: int = 20,
        refill_rate: float = 0.5,
        trust_proxy: bool = True,
    ) -> None:
        super().__init__(app)
        self._max_tokens = max_tokens
        self._refill_rate = refill_rate
        self._trust_proxy = trust_proxy
        self._buckets: "OrderedDict[str, dict]" = OrderedDict()

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)

        client = self._client_id(request)
        now = time.time()
        self._evict_idle(now)

        bucket = self._buckets.get(client)
        if bucket is None:
            bucket = {"tokens": float(self._max_tokens), "last_refill": now}
            self._buckets[client] = bucket

        elapsed = now - bucket["last_refill"]
        bucket["tokens"] = min(
            self._max_tokens, bucket["tokens"] + elapsed * self._refill_rate
        )
        bucket["last_refill"] = now
        self._buckets.move_to_end(client)

        if bucket["tokens"] < 1:
            retry_after = int(1 / self._refill_rate) if self._refill_rate > 0 else 60
            return JSONResponse(
                {"detail": "Rate limit exceeded. Try again later."},
                status_code=429,
                headers={"Retry-After": str(retry_after)},
            )

        bucket["tokens"] -= 1
        return await call_next(request)

    def _client_id(self, request: Request) -> str:
        if self._trust_proxy:
            forwarded = request.headers.get("X-Forwarded-For", "")
            if forwarded:
                return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _evict_idle(self, now: float) -> None:
        stale = [
            client
            for client, bucket in self._buckets.items()
            if now - bucket["last_refill"] > IDLE_EVICTION_SECONDS
        ]
        for client in stale:
            self._buckets.pop(client, None)
        while len(self._buckets) > MAX_BUCKETS:
            self._buckets.popitem(last=False)
