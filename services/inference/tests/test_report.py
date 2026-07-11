"""Unit + integration tests for the audit-report path.

These run fully offline: no Fireworks key, no network, no GPU. They cover
the pure context builder, the message rendering, the deterministic fallback
that guarantees a live demo never hard-crashes on a report call, and the
POST /api/report route end-to-end against a seeded activation cache.
"""

import os

os.environ.setdefault("MONARCH_SKIP_MODEL_LOAD", "1")

from fastapi.testclient import TestClient  # noqa: E402

from app.config import Settings
from app.main import app  # noqa: E402
from app.routers.scan import activation_key  # noqa: E402
from app.services.gemma_report import (  # noqa: E402
    build_report_context,
    generate_report,
    render_messages,
)
from app.services.stores import blob_store  # noqa: E402

HIGH_NAA = {
    "naa": 2.31,
    "a_aff": 1.42,
    "a_del": 0.61,
    "classification": "HIGH",
    "valid": True,
}
LANDAU = {
    "equilibrium_m": 0.74,
    "susceptibility": 1.9,
    "external_field_h": 1.15,
    "beta_j": 0.7,
    "alpha_hat": 0.5,
}
ROI_BREAKDOWN = {
    "AAIC": {"activation": 1.8, "system": "affective"},
    "OFC": {"activation": 1.3, "system": "affective"},
    "46": {"activation": 0.7, "system": "deliberative"},
    "a10p": {"activation": 0.5, "system": "deliberative"},
}


def _context(alpha_source: str = "fallback") -> dict:
    return build_report_context(
        naa_result=HIGH_NAA,
        landau_result=LANDAU,
        roi_breakdown=ROI_BREAKDOWN,
        alpha_source=alpha_source,
        content_excerpt="FED DESTROYS AMERICA -- your savings are GONE.",
    )


def test_context_ranks_top_rois_by_activation():
    context = _context()
    assert context["top_affective_rois"][0] == "AAIC"
    assert context["top_deliberative_rois"][0] == "46"
    assert context["naa"] == 2.31
    assert context["alpha_calibrated"] is False


def test_context_flags_calibrated_alpha():
    assert _context("calibrated")["alpha_calibrated"] is True


def test_context_tolerates_empty_roi_breakdown():
    context = build_report_context(
        naa_result=HIGH_NAA,
        landau_result=LANDAU,
        roi_breakdown={},
        alpha_source="fallback",
    )
    assert context["top_affective_rois"] == []
    assert context["top_deliberative_rois"] == []


def test_render_messages_shape():
    messages = render_messages(_context())
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert "audit report" in messages[1]["content"].lower()


def test_fallback_report_when_no_key():
    # Empty fireworks_api_key forces the deterministic template path.
    cfg = Settings(FIREWORKS_API_KEY="")
    result = generate_report(_context(), cfg=cfg)
    assert result["source"] == "fallback"
    assert result["model"] == "template"
    for header in ("Summary", "Key findings", "Caveats"):
        assert header in result["summary"]


def test_fallback_states_uncalibrated_caveat():
    cfg = Settings(FIREWORKS_API_KEY="")
    result = generate_report(_context("fallback"), cfg=cfg)
    assert "illustrative only" in result["summary"]


def test_fallback_omits_uncalibrated_caveat_when_calibrated():
    cfg = Settings(FIREWORKS_API_KEY="")
    result = generate_report(_context("calibrated"), cfg=cfg)
    assert "illustrative only" not in result["summary"]


def test_fallback_reports_undefined_naa_honestly():
    cfg = Settings(FIREWORKS_API_KEY="")
    undefined = {
        "naa": None,
        "a_aff": -0.2,
        "a_del": 0.4,
        "classification": "UNDEFINED",
        "valid": False,
    }
    context = build_report_context(
        naa_result=undefined,
        landau_result=LANDAU,
        roi_breakdown=ROI_BREAKDOWN,
        alpha_source="fallback",
    )
    result = generate_report(context, cfg=cfg)
    assert result["source"] == "fallback"
    assert "did not produce a valid" in result["summary"]


def _auth_headers() -> dict:
    """Bearer header when the inference API key is configured (auth on)."""
    from app.config import settings
    key = settings.inference_api_key
    return {"Authorization": f"Bearer {key}"} if key else {}


def test_report_route_404_for_unknown_scan():
    with TestClient(app) as client:
        resp = client.post("/api/report", json={"scan_id": "does-not-exist"},
                           headers=_auth_headers())
        assert resp.status_code == 404


def test_report_route_returns_fallback_for_seeded_scan(
    stub_roi_cache, synthetic_item_vector
):
    scan_id = "seeded-scan-for-report-test"
    blob_store.put(activation_key(scan_id), synthetic_item_vector)

    with TestClient(app) as client:
        resp = client.post("/api/report", json={"scan_id": scan_id},
                           headers=_auth_headers())

    assert resp.status_code == 200
    body = resp.json()
    # No Fireworks key configured in the test env, so the route must degrade
    # to the deterministic template rather than error.
    assert body["source"] == "fallback"
    for header in ("Summary", "Key findings", "Caveats"):
        assert header in body["summary"]


def test_report_pdf_route_renders_from_client_payload():
    """POST /api/report/pdf renders a PDF from UI-supplied numbers, no cache."""
    payload = {
        "scan_id": "client-supplied-scan",
        "naa": HIGH_NAA,
        "landau": {
            **LANDAU,
            "free_energy_m": [-1.0, 0.0, 1.0],
            "free_energy_F": [0.6, 0.0, -0.2],
        },
        "roi_breakdown": [
            {"name": "AAIC", "activation": 1.8, "system": "affective", "vertex_count": 120},
            {"name": "46", "activation": 0.7, "system": "deliberative", "vertex_count": 90},
        ],
        "audit": {
            "summary": "Summary\nHigh emotional pull.",
            "source": "fallback",
            "model": "template",
        },
        "content_excerpt": "FED DESTROYS AMERICA",
        "demographic": "general",
    }

    with TestClient(app) as client:
        resp = client.post("/api/report/pdf", json=payload, headers=_auth_headers())

    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content[:4] == b"%PDF"
