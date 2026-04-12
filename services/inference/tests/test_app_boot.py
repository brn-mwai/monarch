"""Smoke-test that the FastAPI app boots and the /health route works
when MONARCH_SKIP_MODEL_LOAD is set. This is the closest we can get to
end-to-end coverage on a CPU-only dev box.
"""

import os

os.environ.setdefault("MONARCH_SKIP_MODEL_LOAD", "1")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


def test_health_endpoint():
    with TestClient(app) as client:
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["model_loaded"] is False
        assert "version" in body


def test_scan_returns_503_when_model_unloaded():
    with TestClient(app) as client:
        resp = client.post("/api/scan", json={"text": "hello world this is enough"})
        assert resp.status_code == 503
