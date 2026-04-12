"""One-time alpha_hat calibration on NELA-GT-2021.

Stub. The full pipeline regresses observed share-rate proxies (e.g.
within-corpus virality) against TRIBE v2 NAA values across the
NELA-GT-2021 corpus, fits an OLS slope, and writes the result plus a
95% confidence interval to ``data/alpha_hat.json``.

Lands in a follow-up phase. Until then the API uses the
``DEFAULT_ALPHA_HAT = 0.5`` fallback in
``app.services.alpha_calibration``.
"""

import sys


def main() -> int:
    print("calibrate_alpha.py is a stub. Implement in a follow-up phase.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
