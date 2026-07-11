"""PDF report generator for a Monarch scan.

Produces a polished single-scan report: a black Monarch logo, the plain-
language audit, an NAA gauge, the Landau free-energy and susceptibility
curves, a per-ROI breakdown, and the methodology/disclaimer - assembled with
reportlab, charts rendered by ``report_charts``.

The logo SVG (white in the app) is recoloured black and rasterised to PNG via
svglib + reportlab's renderPM, so no cairo dependency is needed.
"""

from __future__ import annotations

import io
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from svglib.svglib import svg2rlg

from . import report_charts as charts

INK = colors.HexColor("#111111")
GREY = colors.HexColor("#6b6b6b")
LIGHT = colors.HexColor("#e6e6e6")
FIRE = colors.HexColor("#f0642c")
PANEL = colors.HexColor("#f6f6f4")

_REPO_ROOT = Path(__file__).resolve().parents[4]
_LOGO_SVG = _REPO_ROOT / "apps" / "web" / "public" / "monarch-logo.svg"

AUDIENCE_LABELS = {
    "general": "General reader",
    "researcher": "Researcher",
    "educator": "Educator",
    "journalist": "Journalist & editor",
    "parent": "Parent & EdTech",
    "safety": "Safety & fact-check",
    "student": "Student",
}


def _black_logo(width_mm: float):
    """The Monarch logo recoloured black, scaled to width, as a vector Drawing.

    Embedded as vector (no rasteriser / cairo needed) so it stays crisp at any
    zoom and renders identically on Windows and the Linux pod.
    """
    if not _LOGO_SVG.exists():
        return None
    svg = _LOGO_SVG.read_text(encoding="utf-8")
    svg = svg.replace('fill="white"', 'fill="black"').replace('fill="#fff"', 'fill="black"')
    drawing = svg2rlg(io.StringIO(svg))
    if drawing is None or not drawing.width:
        return None
    factor = (width_mm * mm) / drawing.width
    drawing.width *= factor
    drawing.height *= factor
    drawing.scale(factor, factor)
    return drawing


def _styles() -> dict:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("t", parent=base["Title"], fontName="Helvetica-Bold",
                                 fontSize=17, textColor=INK, spaceAfter=2, leading=20),
        "sub": ParagraphStyle("s", parent=base["Normal"], fontName="Courier",
                              fontSize=8, textColor=GREY, spaceAfter=0),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontName="Helvetica-Bold",
                             fontSize=11, textColor=INK, spaceBefore=14, spaceAfter=6),
        "body": ParagraphStyle("b", parent=base["Normal"], fontName="Helvetica",
                               fontSize=9.5, textColor=INK, leading=14, spaceAfter=4),
        "mono": ParagraphStyle("m", parent=base["Normal"], fontName="Courier",
                               fontSize=8.5, textColor=INK, leading=12),
        "caption": ParagraphStyle("c", parent=base["Normal"], fontName="Courier",
                                  fontSize=7.5, textColor=GREY, spaceBefore=2),
        "foot": ParagraphStyle("f", parent=base["Normal"], fontName="Helvetica",
                               fontSize=7.5, textColor=GREY, leading=10),
    }


def _img(png: bytes, width_mm: float) -> Image:
    reader = io.BytesIO(png)
    img = Image(reader)
    ratio = img.imageHeight / img.imageWidth
    img.drawWidth = width_mm * mm
    img.drawHeight = width_mm * mm * ratio
    return img


def _kv_table(rows: list[tuple[str, str]], st: dict) -> Table:
    data = [[Paragraph(k, st["mono"]), Paragraph(v, st["mono"])] for k, v in rows]
    table = Table(data, colWidths=[45 * mm, 40 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PANEL),
        ("LINEBELOW", (0, 0), (-1, -2), 0.4, LIGHT),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return table


def _audit_blocks(summary: str, st: dict) -> list:
    flow = []
    for chunk in [c.strip() for c in summary.split("\n\n") if c.strip()]:
        head, _, body = chunk.partition("\n")
        flow.append(Paragraph(head.strip().upper(), st["sub"]))
        flow.append(Paragraph(body.strip().replace("\n", "<br/>"), st["body"]))
        flow.append(Spacer(1, 4))
    return flow


DISCLAIMER = (
    "Monarch estimates a population-level PREDICTION of cortical processing "
    "balance from media content using Meta's TRIBE v2. NAA is a derived proxy "
    "observable, not a direct measurement of any individual's brain. The Landau "
    "/ Ising layer is a theoretical interpretation of how the signal could move "
    "collective opinion, not evidence of real-world opinion shift. Built with Llama."
)


def generate_pdf_report(
    scan_id: str,
    naa_result: dict,
    landau_result: dict,
    roi_breakdown: dict,
    output_path: Path,
    *,
    audit: Optional[dict] = None,
    content_excerpt: Optional[str] = None,
    modality: str = "text",
    demographic: str = "general",
    generated_at: Optional[str] = None,
) -> Path:
    """Render a single-scan PDF report to ``output_path``."""
    audience = AUDIENCE_LABELS.get(demographic, "General reader")
    st = _styles()
    doc = SimpleDocTemplate(
        str(output_path), pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=16 * mm,
        title=f"Monarch scan {scan_id}", author="Monarch",
    )
    story: list = []

    # --- Header: black logo + title + metadata ---
    stamp = generated_at or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    meta = Paragraph(
        f"Neural Processing Audit<br/>"
        f"<font face='Courier' size=8 color='#6b6b6b'>scan {scan_id[:12]} · {modality} · {stamp}<br/>"
        f"written for: {audience}</font>",
        st["title"],
    )
    logo = _black_logo(46)
    header_cells = [[logo if logo is not None else Paragraph("MONARCH", st["title"]), meta]]
    header = Table(header_cells, colWidths=[52 * mm, 122 * mm])
    header.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                                ("ALIGN", (1, 0), (1, 0), "RIGHT")]))
    story += [header, Spacer(1, 6), HRFlowable(width="100%", thickness=1, color=INK), Spacer(1, 8)]

    # --- Plain-language audit ---
    story.append(Paragraph("Plain-language audit", st["h2"]))
    if audit and audit.get("summary"):
        src = audit.get("source")
        tag = ("Written by Gemma via Fireworks AI (AMD)" if src == "gemma"
               else "Deterministic template (no language model configured)")
        story.append(Paragraph(f"<font color='#6b6b6b' size=7>{tag}</font>", st["caption"]))
        story += _audit_blocks(audit["summary"], st)
    else:
        story.append(Paragraph("No audit narrative available for this scan.", st["body"]))

    # --- NAA summary: gauge + table ---
    story.append(Paragraph("NAA summary", st["h2"]))
    naa_val = naa_result.get("naa")
    naa_rows = [
        ("NAA", f"{naa_val:.3f}" if naa_val is not None else "undefined"),
        ("Classification", str(naa_result.get("classification"))),
        ("Affective activation", f"{naa_result.get('a_aff', 0):.4f}"),
        ("Deliberative activation", f"{naa_result.get('a_del', 0):.4f}"),
        ("Content", (content_excerpt or "")[:48] + ("..." if content_excerpt and len(content_excerpt) > 48 else "")),
    ]
    naa_panel = Table([[_img(charts.naa_gauge_png(naa_val or 0.0), 78), _kv_table(naa_rows, st)]],
                      colWidths=[88 * mm, 86 * mm])
    naa_panel.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    story.append(naa_panel)

    # --- Physics: Landau + susceptibility ---
    story.append(Paragraph("Opinion-dynamics physics", st["h2"]))
    beta_j = landau_result.get("beta_j", 0.7)
    alpha_hat = landau_result.get("alpha_hat", 0.5)
    phys = Table([[_img(charts.landau_curve_png(landau_result), 84),
                   _img(charts.susceptibility_curve_png(naa_val or 0.0, beta_j, alpha_hat), 84)]],
                 colWidths=[87 * mm, 87 * mm])
    phys.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(phys)
    phys_rows = [
        ("Equilibrium m*", f"{landau_result.get('equilibrium_m', 0):.4f}"),
        ("Susceptibility", str(landau_result.get("susceptibility"))),
        ("External field H", f"{landau_result.get('external_field_h', 0):.4f}"),
        ("Coupling beta_j", f"{beta_j:.3f}"),
        ("alpha_hat", f"{alpha_hat:.3f}"),
    ]
    story += [Spacer(1, 4), _kv_table(phys_rows, st)]

    # --- ROI breakdown ---
    if roi_breakdown:
        story.append(Paragraph("ROI activation breakdown", st["h2"]))
        story.append(_img(charts.roi_bars_png(roi_breakdown), 150))
        story.append(Paragraph("Most-engaged regions across the affective-salience and "
                               "deliberative-control networks (HCP MMP1.0).", st["caption"]))

    # --- Methodology (the maths, with plain glosses) ---
    story.append(Paragraph("How the numbers are computed", st["h2"]))
    story.append(Paragraph("Each equation is shown with what it means in plain words.", st["caption"]))
    story.append(_img(charts.methodology_png(), 168))

    # --- Disclaimer ---
    story += [Spacer(1, 8), HRFlowable(width="100%", thickness=0.5, color=LIGHT), Spacer(1, 4),
              Paragraph(DISCLAIMER, st["foot"])]

    doc.build(story)
    return output_path


if __name__ == "__main__":
    demo_roi = {
        "AAIC": {"activation": 1.8, "system": "affective", "vertex_count": 120},
        "OFC": {"activation": 1.3, "system": "affective", "vertex_count": 200},
        "TGd": {"activation": 1.5, "system": "affective", "vertex_count": 90},
        "46": {"activation": 0.7, "system": "deliberative", "vertex_count": 150},
        "a10p": {"activation": 0.5, "system": "deliberative", "vertex_count": 80},
        "d32": {"activation": 0.6, "system": "deliberative", "vertex_count": 110},
    }
    m = [i / 50.0 for i in range(-50, 51)]
    out = generate_pdf_report(
        "demo-scan-0001",
        {"naa": 2.31, "a_aff": 1.42, "a_del": 0.61, "classification": "HIGH", "valid": True},
        {"free_energy_m": m, "free_energy_F": [0.35 * x**2 + 0.083 * x**4 - 1.15 * x for x in m],
         "equilibrium_m": 0.74, "susceptibility": 1.9, "external_field_h": 1.15,
         "beta_j": 0.7, "alpha_hat": 0.5},
        demo_roi,
        Path("./demo_report.pdf"),
        audit={"summary": "Summary\nThis text item is predicted to engage emotional systems more "
               "than reasoning systems (NAA = 2.31, class HIGH).\n\nKey findings\n- Predicted "
               "emotional-region activation: 1.42\n- Most-engaged emotional regions: AAIC, OFC, TGd"
               "\n\nCaveats\n- This is a prediction for an average brain, not a real person.",
               "source": "fallback", "model": "template"},
        content_excerpt="FED DESTROYS AMERICA -- your savings are GONE.",
    )
    print(f"wrote {out}")
