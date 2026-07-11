"""Job-backed scan API: submit returns immediately, poll returns the result.

The scan itself outlives any proxy request timeout, so what matters here is
that the job id comes back at once, that the result is retrievable afterwards,
and that a failing scan surfaces as an error status rather than a hang.
"""

import os

os.environ.setdefault("MONARCH_SKIP_MODEL_LOAD", "1")

import numpy as np  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.services.jobs import JobStatus, JobStore  # noqa: E402

TEXT = "The Federal Reserve held interest rates steady, citing stable inflation."


def _auth_headers() -> dict:
    from app.config import settings

    key = settings.inference_api_key
    return {"Authorization": f"Bearer {key}"} if key else {}


@pytest.fixture
def loaded_model(stub_roi_cache):
    """Override the model dependency with a stub returning a fixed vector."""
    from app.dependencies import require_loaded_model

    class StubModel:
        def is_loaded(self) -> bool:
            return True

        def predict_text(self, text: str) -> dict:
            vector = np.zeros(20484, dtype=np.float32)
            vector[0:200] = 0.4
            vector[200:400] = 0.1
            return {
                "item_vector": vector,
                "raw_preds": np.tile(vector, (3, 1)),
                "n_trs": 3,
            }

    stub = StubModel()
    app.dependency_overrides[require_loaded_model] = lambda: stub
    yield stub
    app.dependency_overrides.clear()


def test_job_store_lifecycle():
    store = JobStore()
    job = store.create()
    assert job.status is JobStatus.PENDING

    store.mark_running(job.job_id)
    assert store.get(job.job_id).status is JobStatus.RUNNING

    store.mark_done(job.job_id, {"scan_id": "abc"})
    done = store.get(job.job_id)
    assert done.status is JobStatus.DONE
    assert done.as_dict()["result"] == {"scan_id": "abc"}
    assert "error" not in done.as_dict()


def test_job_store_records_error():
    store = JobStore()
    job = store.create()
    store.mark_error(job.job_id, "whisperx failed")

    body = store.get(job.job_id).as_dict()
    assert body["status"] == "error"
    assert body["error"] == "whisperx failed"
    assert "result" not in body


def test_job_store_evicts_past_max():
    store = JobStore(max_jobs=3)
    ids = [store.create().job_id for _ in range(5)]

    alive = [jid for jid in ids if store.get(jid) is not None]
    assert len(alive) <= 3
    assert ids[-1] in alive


def test_unknown_job_is_404():
    with TestClient(app) as client:
        resp = client.get("/api/scan/jobs/does-not-exist", headers=_auth_headers())
        assert resp.status_code == 404


def test_submit_returns_202_with_job_id(loaded_model):
    with TestClient(app) as client:
        resp = client.post(
            "/api/scan/jobs", json={"text": TEXT}, headers=_auth_headers()
        )
        assert resp.status_code == 202
        body = resp.json()
        assert body["job_id"]
        assert body["status"] in ("pending", "running", "done")


def test_polling_yields_the_scan_result(loaded_model):
    with TestClient(app) as client:
        submitted = client.post(
            "/api/scan/jobs", json={"text": TEXT}, headers=_auth_headers()
        ).json()

        # TestClient runs background tasks before returning, so by the time the
        # submit response lands the scan has already been recorded.
        polled = client.get(
            f"/api/scan/jobs/{submitted['job_id']}", headers=_auth_headers()
        )
        assert polled.status_code == 200
        body = polled.json()
        assert body["status"] == "done"
        # Both ROI means are above baseline here, so the ratio NAA applies:
        # 0.4 / (0.1 + delta).
        assert body["result"]["naa"]["naa"] == pytest.approx(0.4 / 0.101, rel=1e-3)
        assert body["result"]["n_trs"] == 3


def test_job_returns_signed_naa_when_ratio_is_undefined(loaded_model):
    """Below-baseline content must still produce a result, not a 422."""

    def below_baseline(text: str) -> dict:
        vector = np.zeros(20484, dtype=np.float32)
        vector[0:200] = -0.2
        vector[200:400] = -0.5
        return {
            "item_vector": vector,
            "raw_preds": np.tile(vector, (3, 1)),
            "n_trs": 3,
        }

    loaded_model.predict_text = below_baseline

    with TestClient(app) as client:
        submitted = client.post(
            "/api/scan/jobs", json={"text": TEXT}, headers=_auth_headers()
        ).json()
        body = client.get(
            f"/api/scan/jobs/{submitted['job_id']}", headers=_auth_headers()
        ).json()

        assert body["status"] == "done"
        assert body["result"]["naa"]["naa"] == pytest.approx(0.3, abs=1e-6)


def test_failing_scan_surfaces_as_error_status(monkeypatch, loaded_model):
    def boom(text: str) -> dict:
        raise RuntimeError("whisperx failed")

    monkeypatch.setattr(loaded_model, "predict_text", boom)

    with TestClient(app) as client:
        submitted = client.post(
            "/api/scan/jobs", json={"text": TEXT}, headers=_auth_headers()
        ).json()
        body = client.get(
            f"/api/scan/jobs/{submitted['job_id']}", headers=_auth_headers()
        ).json()

        assert body["status"] == "error"
        assert "whisperx failed" in body["error"]
