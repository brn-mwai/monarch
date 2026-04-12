"""PDF report generation.

Stub. The full report generator (cover page, NAA gauge, Landau plot,
ROI breakdown table, methodology disclaimers) will be implemented in a
later phase using ``reportlab``. The router stub at /api/report/{id}
returns 501 for now.
"""

from pathlib import Path


def generate_pdf_report(
    scan_id: str,
    naa_result: dict,
    landau_result: dict,
    roi_breakdown: dict,
    output_path: Path,
) -> Path:
    """Render a single-scan PDF report. Not yet implemented."""
    raise NotImplementedError(
        "PDF report generation lands in a follow-up phase."
    )
