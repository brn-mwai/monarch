"""Tests for the GET /api/scan/{id}/timeseries playback endpoint.

The endpoint does not depend on the model, so we inject frames straight
into the process-local store and exercise the route via TestClient.
"""

import os

os.environ.setdefault("MONARCH_SKIP_MODEL_LOAD", "1")

import numpy as np  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.routers import scan as scan_router  # noqa: E402

VERTICES = 20484


def test_timeseries_serves_frame_major_float32():
    n_frames = 4
    frames = np.arange(n_frames * VERTICES, dtype=np.float32).reshape(
        n_frames, VERTICES
    )
    scan_router.blob_store.put(scan_router.timeseries_key("ts-roundtrip"), frames)

    with TestClient(app) as client:
        resp = client.get("/api/scan/ts-roundtrip/timeseries")

    assert resp.status_code == 200
    assert resp.headers["X-Frame-Count"] == str(n_frames)
    assert resp.headers["X-Vertex-Count"] == str(VERTICES)
    assert resp.headers["X-Dtype"] == "float32"
    assert len(resp.content) == n_frames * VERTICES * 4

    recovered = np.frombuffer(resp.content, dtype=np.float32).reshape(
        n_frames, VERTICES
    )
    assert np.array_equal(recovered, frames)


def test_timeseries_404_when_missing():
    with TestClient(app) as client:
        resp = client.get("/api/scan/does-not-exist/timeseries")
    assert resp.status_code == 404


def test_timeseries_500_on_bad_shape():
    scan_router.blob_store.put(
        scan_router.timeseries_key("ts-bad-shape"),
        np.zeros((3, 100), dtype=np.float32),
    )
    with TestClient(app) as client:
        resp = client.get("/api/scan/ts-bad-shape/timeseries")
    assert resp.status_code == 500
