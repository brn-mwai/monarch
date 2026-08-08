"""Turn a measured observable spread into the coupling a media mechanism would need.

This is the bridge between the theory paper and the corpus. Paper 1 derives that no
media-driven transition is possible unless

    alpha  >=  h_c(beta_J) / dX

for an observable used as a field through ``h = alpha X``. Paper 2 supplies ``dX`` by
measuring it on the scanned corpus. The product is the sentence that makes a null result
publishable: not "no coupling was detected" but "the coupling would have to exceed this, and
the measurement excludes that range".

The spread is read from the scan rather than assumed, and the spinodal from the solver's own
JSON rather than retyped, so the bound moves when either does.

Two things this deliberately does not do. It does not compute or quote an ``alpha_hat``:
calibration is a separate step and its interval is reported there. And it does not decide
whether the required coupling is plausible, because ``alpha`` has no independent scale; it
reports what would be required and leaves the judgement where it belongs.

Usage
-----
    python scripts/field_bound.py --scan data/corpus_naa.csv \
        --report data/paper1/phase_boundary.json --out data/field_bound.json
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

REPORTED_BETA_J = (1.1, 1.5, 2.0)


def observed_spread(rows: list[dict], column: str) -> dict:
    """Range of the observable across the scanned corpus.

    Rows where the observable is undefined are excluded and counted rather than treated as
    zero, since a zero would widen the spread and weaken the bound in the flattering
    direction.
    """
    values = [float(r[column]) for r in rows if r.get(column) not in (None, "")]
    if len(values) < 2:
        raise ValueError(f"need at least 2 defined values in {column}, got {len(values)}")
    return {
        "column": column,
        "n_defined": len(values),
        "n_undefined": len(rows) - len(values),
        "min": min(values),
        "max": max(values),
        "spread": max(values) - min(values),
    }


def required_coupling(spread: float, critical_field: float) -> float:
    """The bound itself: what alpha must exceed for the mechanism to be possible."""
    if spread <= 0:
        raise ValueError(f"spread must be positive, got {spread}")
    return critical_field / spread


def bound_table(spread: float, beta_j: list[float], h_c: list[float],
                targets: tuple[float, ...] = REPORTED_BETA_J) -> list[dict]:
    """Required coupling at each reported coupling strength.

    The solver's grid rarely lands exactly on a round beta_J, so the nearest sampled point is
    used and reported as the value actually read, not as the value asked for.
    """
    table = []
    for target in targets:
        index = min(range(len(beta_j)), key=lambda i: abs(beta_j[i] - target))
        field = h_c[index]
        if field != field:  # NaN: below the critical point, no spinodal exists
            continue
        table.append({
            "beta_j_requested": target,
            "beta_j_used": beta_j[index],
            "critical_field": field,
            "alpha_required": required_coupling(spread, field),
        })
    return table


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scan", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--naa-col", default="naa_signed")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    for path in (args.scan, args.report):
        if not path.exists():
            print(f"[FAIL] {path} not found", file=sys.stderr)
            return 1

    with open(args.scan, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    report = json.loads(args.report.read_text(encoding="utf-8"))
    spread = observed_spread(rows, args.naa_col)
    table = bound_table(
        spread["spread"],
        report["phase_boundary"]["beta_j"],
        report["phase_boundary"]["h_c"],
    )

    result = {
        "n_scanned": len(rows),
        "observable": spread,
        "bound": table,
        "note": "necessary condition only; clearing it does not establish the mechanism",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(f"scanned rows            : {len(rows)}")
    print(f"observable              : {spread['column']}")
    print(f"  defined               : {spread['n_defined']}  undefined: {spread['n_undefined']}")
    print(f"  range                 : {spread['min']:+.4f} to {spread['max']:+.4f}")
    print(f"  spread dX             : {spread['spread']:.4f}")
    print()
    print("coupling required before media can drive a transition:")
    for row in table:
        print(f"  beta_J = {row['beta_j_used']:.3f}   h_c = {row['critical_field']:.5f}"
              f"   alpha >= {row['alpha_required']:.4f}")
    print()
    print("Necessary condition only. Clearing it does not establish the mechanism;")
    print("falling below it excludes the mechanism within the model's assumptions.")
    print(f"\nWrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
