"""Tests for RateLimitMiddleware wired onto a minimal app."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.rate_limit import RateLimitMiddleware


def build_app(max_tokens: int, refill_rate: float = 0.0, trust_proxy: bool = True) -> FastAPI:
    app = FastAPI()

    @app.get("/health")
    def health():
        return {"ok": True}

    @app.get("/api/ping")
    def ping():
        return {"ok": True}

    app.add_middleware(
        RateLimitMiddleware,
        max_tokens=max_tokens,
        refill_rate=refill_rate,
        trust_proxy=trust_proxy,
    )
    return app


def test_blocks_after_tokens_exhausted():
    with TestClient(build_app(max_tokens=2)) as client:
        assert client.get("/api/ping").status_code == 200
        assert client.get("/api/ping").status_code == 200
        assert client.get("/api/ping").status_code == 429


def test_health_is_exempt_even_with_zero_tokens():
    with TestClient(build_app(max_tokens=0)) as client:
        for _ in range(5):
            assert client.get("/health").status_code == 200


def test_proxy_forwarded_for_separates_clients():
    with TestClient(build_app(max_tokens=1, trust_proxy=True)) as client:
        assert (
            client.get("/api/ping", headers={"X-Forwarded-For": "1.1.1.1"}).status_code
            == 200
        )
        assert (
            client.get("/api/ping", headers={"X-Forwarded-For": "1.1.1.1"}).status_code
            == 429
        )
        # A different client (different forwarded IP) has its own bucket.
        assert (
            client.get("/api/ping", headers={"X-Forwarded-For": "2.2.2.2"}).status_code
            == 200
        )
