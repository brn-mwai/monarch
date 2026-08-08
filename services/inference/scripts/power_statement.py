"""What the 400-item corpus can detect, stated before it decides anything.

A null needs its power, and power stated after seeing the result is not a power statement,
it is a rationalisation. This is therefore runnable now, on the design alone, and its output
belongs in the methods section whatever the scan returns.

The design is four categories of 100. RQ II tests category separation by one-way ANOVA; RQ I
scores the manipulative-versus-neutral AUC, where the three non-neutral categories are the
positive class, giving 300 against 100.

Usage
-----
    python scripts/power_statement.py --out data/power_statement.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.power import statement  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n-per-group", type=int, default=100)
    parser.add_argument("--n-groups", type=int, default=4)
    parser.add_argument("--n-positive", type=int, default=300)
    parser.add_argument("--n-negative", type=int, default=100)
    parser.add_argument("--alpha", type=float, default=0.05)
    parser.add_argument("--target-power", type=float, default=0.80)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    result = statement(
        n_per_group=args.n_per_group,
        n_groups=args.n_groups,
        n_positive=args.n_positive,
        n_negative=args.n_negative,
        alpha=args.alpha,
        target_power=args.target_power,
        seed=args.seed,
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2), encoding="utf-8")

    anova = result["anova"]
    auc = result["auc"]
    print(f"Design: {anova['n_groups']} categories x {anova['n_per_group']} "
          f"= {anova['n_total']} items, alpha={result['alpha']}, "
          f"power={result['target_power']}")
    print()
    print("RQ II, category separation by one-way ANOVA:")
    print(f"  smallest detectable eta^2 : {anova['minimum_detectable_eta_squared']:.4f}")
    print(f"  equivalently Cohen's f    : {anova['minimum_detectable_cohens_f']:.4f}")
    print()
    print(f"RQ I, AUC with {auc['n_positive']} manipulative against {auc['n_negative']} neutral:")
    print(f"  smallest detectable AUC   : {auc['minimum_detectable_auc']:.4f}")
    print(f"  equivalent separation d   : {auc['minimum_detectable_separation']:.4f}")
    print()
    print("Read as: an effect below these values would probably be missed by this design,")
    print("so a null here excludes effects above them and is silent about smaller ones.")
    print(f"\nWrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
