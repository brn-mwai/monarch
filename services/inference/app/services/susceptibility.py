"""Population susceptibility chi(NAA).

Thin convenience layer over ``landau.susceptibility`` /
``landau.compute_susceptibility_curve``. Kept as its own module to give
a stable import path for the report-page susceptibility panel and to
host any future per-population variants (e.g. heterogeneous beta_J).
"""

from .landau import (
    compute_susceptibility_curve as compute_curve,
    susceptibility as compute_point,
)

__all__ = ["compute_curve", "compute_point"]
