"""Plain-language audit report via Gemma on Fireworks AI.

Takes the numeric scan results (NAA, Landau, ROI breakdown) and produces a
human-readable audit paragraph plus key findings and honest caveats. The
language-model call goes to Gemma through the Fireworks AI API, which serves
on AMD hardware -- this is Monarch's lightweight AMD-compute path and its
"Best Use of Gemma" entry, independent of whether TRIBE runs on the pod.

Design constraints that this module enforces rather than hopes for:
  - The report must never present NAA as a measurement of a real person. It
    is a content-level PREDICTION for an average brain (see naa.py).
  - When alpha_hat is the uncalibrated fallback, the opinion-dynamics numbers
    are illustrative only; the report must say so.
  - Every claim is grounded in the numbers passed in; the model is instructed
    not to invent findings.

The Fireworks call degrades gracefully: with no API key or on any request
failure it returns a deterministic template report tagged ``source="fallback"``
so a live demo never hard-crashes. A successful Gemma call is tagged
``source="gemma"``.
"""

from __future__ import annotations

import json
from typing import Optional

import httpx

from ..config import Settings, settings


# One plain-language line per audience, so the report speaks to the reader
# selected in the app's demographic dropdown.
DEMOGRAPHIC_GUIDANCE = {
    "general": "a general adult reader who just wants to know what this means",
    "researcher": "a researcher who wants the method and the honest caveats",
    "educator": "a teacher deciding whether this content suits a classroom",
    "journalist": "a journalist or editor judging how a story is framed",
    "parent": "a parent deciding whether this media is too emotionally stimulating for their child",
    "safety": "a trust-and-safety or fact-checking reviewer screening for manipulation",
    "student": "a student learning about media and the brain, explained very simply",
}


def build_report_context(
    naa_result: dict,
    landau_result: dict,
    roi_breakdown: dict,
    alpha_source: str,
    *,
    content_excerpt: Optional[str] = None,
    modality: str = "text",
    demographic: str = "general",
    top_k_roi: int = 3,
) -> dict:
    """Assemble a compact, model-ready facts dict from the scan results.

    Pure function, no network. ``roi_breakdown`` is the mapping produced by
    ``naa.compute_roi_breakdown`` ({roi_name: {activation, system, ...}}).
    ``alpha_source`` is the ``source`` field from ``alpha_calibration``
    (``"calibrated"`` or ``"fallback"``), which decides whether the
    opinion-dynamics section is presented as illustrative.
    """
    affective = sorted(
        ((name, v["activation"]) for name, v in roi_breakdown.items()
         if v.get("system") == "affective"),
        key=lambda kv: kv[1],
        reverse=True,
    )
    deliberative = sorted(
        ((name, v["activation"]) for name, v in roi_breakdown.items()
         if v.get("system") == "deliberative"),
        key=lambda kv: kv[1],
        reverse=True,
    )

    return {
        "modality": modality,
        "audience": DEMOGRAPHIC_GUIDANCE.get(demographic, DEMOGRAPHIC_GUIDANCE["general"]),
        "audience_id": demographic,
        "content_excerpt": (content_excerpt or "").strip()[:400] or None,
        "naa": naa_result.get("naa"),
        "naa_valid": naa_result.get("valid", False),
        "naa_classification": naa_result.get("classification"),
        "a_aff": naa_result.get("a_aff"),
        "a_del": naa_result.get("a_del"),
        "top_affective_rois": [name for name, _ in affective[:top_k_roi]],
        "top_deliberative_rois": [name for name, _ in deliberative[:top_k_roi]],
        "equilibrium_m": landau_result.get("equilibrium_m"),
        "susceptibility": landau_result.get("susceptibility"),
        "external_field_h": landau_result.get("external_field_h"),
        "beta_j": landau_result.get("beta_j"),
        "alpha_hat": landau_result.get("alpha_hat"),
        "alpha_calibrated": alpha_source == "calibrated",
    }


SYSTEM_PROMPT = (
    "You are Monarch's audit-report writer. You explain, in direct everyday "
    "language, what a scan of a media item found. Follow these rules exactly:\n"
    "1. Write for the reader described in the facts under 'audience'. Match their "
    "concern and tone. Be direct and concrete.\n"
    "2. NO JARGON. Never use a technical term without explaining it in plain "
    "words the first time. Prefer 'emotion' over 'affective-salience' and "
    "'reasoning' over 'deliberative-control'. Do not assume the reader knows "
    "neuroscience or physics.\n"
    "3. NAA is simply how much the content leans on emotion versus reasoning. "
    "Above 1 = leans emotional; below 1 = leans reasoning. Explain it that way, "
    "not with the acronym.\n"
    "4. This is a PREDICTION for an average brain about the CONTENT. It is never a "
    "measurement of any real person. Say this plainly.\n"
    "5. If told the opinion-dynamics constant is uncalibrated, say the "
    "crowd-opinion figures are illustrative only, not proven.\n"
    "6. Ground every statement in the numbers provided. Do not invent findings. "
    "No medical or diagnostic claims.\n"
    "7. Output three short sections with these exact headers: Summary, Key "
    "findings, Caveats. Under 180 words total."
)


def render_messages(context: dict) -> list[dict]:
    """Build the chat messages for the Fireworks call. Pure, testable offline."""
    facts = json.dumps(context, indent=2, ensure_ascii=False)
    user = (
        "Write the audit report for this scan. The facts (JSON) are the only "
        "evidence you may use:\n\n" + facts
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]


def _fallback_report(context: dict) -> str:
    """Deterministic template report used when Gemma is unavailable.

    Keeps the same three-section shape and the same honesty guarantees as the
    model path so a demo degrades in wording, not in correctness.
    """
    naa = context.get("naa")
    if not context.get("naa_valid") or naa is None:
        summary = (
            "The scan did not produce a valid emotion-versus-reasoning ratio for "
            "this item (predicted activation fell outside the range where the ratio "
            "is meaningful)."
        )
    else:
        lean = (
            "emotional systems more than reasoning systems"
            if naa > 1.0
            else "reasoning systems more than emotional systems"
        )
        summary = (
            f"This {context.get('modality', 'content')} item is predicted to engage "
            f"{lean} (NAA = {naa:.2f}, class {context.get('naa_classification')})."
        )

    aff = ", ".join(context.get("top_affective_rois") or []) or "none"
    dlb = ", ".join(context.get("top_deliberative_rois") or []) or "none"
    findings = (
        f"- Predicted emotional-region activation: {context.get('a_aff')}\n"
        f"- Predicted reasoning-region activation: {context.get('a_del')}\n"
        f"- Most-engaged emotional regions: {aff}\n"
        f"- Most-engaged reasoning regions: {dlb}"
    )

    caveats = (
        "- This is a prediction for an average brain about the content, not a "
        "measurement of any real person.\n"
    )
    if not context.get("alpha_calibrated"):
        caveats += (
            "- The collective-opinion figures use an uncalibrated constant and are "
            "illustrative only, not validated predictions.\n"
        )

    return (
        f"Summary\n{summary}\n\n"
        f"Key findings\n{findings}\n\n"
        f"Caveats\n{caveats.rstrip()}"
    )


def _post_chat(messages: list[dict], cfg: Settings) -> str:
    """POST an OpenAI-compatible chat request to Fireworks. Raises on failure."""
    response = httpx.post(
        f"{cfg.fireworks_base_url}/chat/completions",
        headers={"Authorization": f"Bearer {cfg.fireworks_api_key}"},
        json={
            "model": cfg.gemma_model,
            "messages": messages,
            "max_tokens": cfg.report_max_tokens,
            "temperature": cfg.report_temperature,
        },
        timeout=cfg.report_timeout_seconds,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()


def generate_report(context: dict, cfg: Settings = settings) -> dict:
    """Produce the audit report for a scan context.

    Returns ``{"summary": str, "source": "gemma"|"fallback", "model": str}``.
    Falls back to the deterministic template when no Fireworks key is set or
    the request fails, so callers never have to handle a network exception.
    """
    if not cfg.fireworks_api_key:
        return {"summary": _fallback_report(context), "source": "fallback", "model": "template"}

    try:
        text = _post_chat(render_messages(context), cfg)
        return {"summary": text, "source": "gemma", "model": cfg.gemma_model}
    except (httpx.HTTPError, KeyError, IndexError):
        return {"summary": _fallback_report(context), "source": "fallback", "model": "template"}


if __name__ == "__main__":
    demo_context = build_report_context(
        naa_result={
            "naa": 2.31, "a_aff": 1.42, "a_del": 0.61,
            "classification": "HIGH", "valid": True,
        },
        landau_result={
            "equilibrium_m": 0.74, "susceptibility": 1.9,
            "external_field_h": 1.15, "beta_j": 0.7, "alpha_hat": 0.5,
        },
        roi_breakdown={
            "AAIC": {"activation": 1.8, "system": "affective"},
            "OFC": {"activation": 1.3, "system": "affective"},
            "46": {"activation": 0.7, "system": "deliberative"},
            "a10p": {"activation": 0.5, "system": "deliberative"},
        },
        alpha_source="fallback",
        content_excerpt="FED DESTROYS AMERICA -- your savings are GONE.",
        modality="text",
    )
    assert render_messages(demo_context)[0]["role"] == "system"
    result = generate_report(demo_context, cfg=settings)
    assert result["source"] in ("gemma", "fallback")
    assert "Summary" in result["summary"] and "Caveats" in result["summary"]
    print(f"[source={result['source']} model={result['model']}]\n")
    print(result["summary"])
