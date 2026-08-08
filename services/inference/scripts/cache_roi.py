"""Pre-compute the HCP MMP1.0 ROI vertex-index cache.

Run this ONCE on a machine that has tribev2 installed. The output JSON
goes to ``data/roi_definitions.json`` and lets the API server resolve
NAA ROIs without paying the tribev2 import cost on every boot.
"""

import sys
from pathlib import Path

# Python puts the script's own directory on sys.path, not the working directory, so the
# app package is invisible when this is run as `python scripts/cache_roi.py`.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.roi import cache_roi_indices  # noqa: E402


def main() -> int:
    output = Path("./data/roi_definitions.json")
    cache_roi_indices(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
