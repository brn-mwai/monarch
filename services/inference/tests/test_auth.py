"""Tests for APIKeyMiddleware wired onto a minimal app."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.api_key import APIKeyMiddleware

API_KEY = "secret-key-123"


def build_app() -> FastAPI:
    app = FastAPI()

    @app.get("/health")
    def health():
        return {"ok": True}

    @app.post("/api/scan")
    def scan():
        return {"ok": True}

    app.add_middleware(APIKeyMiddleware, api_key=API_KEY)
    return app


def test_missing_header_is_401():
    with TestClient(build_app()) as client:
        assert client.post("/api/scan").status_code == 401


def test_wrong_key_is_401():
    with TestClient(build_app()) as client:
        resp = client.post("/api/scan", headers={"Authorization": "Bearer wrong"})
        assert resp.status_code == 401


def test_valid_key_passes():
    with TestClient(build_app()) as client:
        resp = client.post(
            "/api/scan", headers={"Authorization": f"Bearer {API_KEY}"}
        )
        assert resp.status_code == 200


def test_health_is_exempt():
    with TestClient(build_app()) as client:
        assert client.get("/health").status_code == 200
