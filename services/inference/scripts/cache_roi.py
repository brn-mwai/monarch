"""Pre-compute the HCP MMP1.0 ROI vertex-index cache.

Run this ONCE on a machine that has tribev2 installed. The output JSON
goes to ``data/roi_definitions.json`` and lets the API server resolve
NAA ROIs without paying the tribev2 import cost on every boot.
"""

from pathlib import Path

from app.services.roi import cache_roi_indices


def main() -> int:
    output = Path("./data/roi_definitions.json")
    cache_roi_indices(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
