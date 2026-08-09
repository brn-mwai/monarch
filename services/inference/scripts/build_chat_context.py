"""Build the fact sheet the site's chat is allowed to answer from.

Everything here is read out of artifacts the pipeline produced. Nothing is written by hand
and nothing is summarised by a model, because a fact sheet assembled by a language model is
the same hallucination risk one step earlier.

The chat is instructed to answer only from this file. If a question is not covered, the
correct answer is that the data does not say, which is why the sheet also records what the
project refuses to claim.

Usage
-----
    python scripts/build_chat_context.py --out ../../apps/web/functions/context.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
INFERENCE = REPO / "services" / "inference"


def _load(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def build() -> dict:
    corpus = _load(REPO / "apps" / "web" / "public" / "data" / "corpus.json")
    rq = _load(INFERENCE / "data" / "final" / "rq_answers.json")
    power = _load(INFERENCE / "data" / "power_statement.json")
    bound = _load(INFERENCE / "data" / "final" / "field_bound.json")
    phase = _load(INFERENCE / "data" / "paper1" / "phase_boundary.json")

    missing = [n for n, v in (("corpus", corpus), ("rq_answers", rq),
                              ("power_statement", power), ("field_bound", bound)) if v is None]
    if missing:
        print(f"[FAIL] missing artifacts: {', '.join(missing)}", file=sys.stderr)
        raise SystemExit(1)

    summary = corpus["summary"]

    facts = {
        "what_monarch_is": (
            "An instrument that scores how far a piece of text leans on emotion rather than "
            "reasoning. Text is spoken, transcribed, embedded, and passed to TRIBE v2, an "
            "encoder that predicts cortical responses. Two regions are averaged from that "
            "prediction, one linked to emotional salience and one to deliberate control, and "
            "the score is the difference between them."
        ),
        "corpus": {
            "items": summary["nScanned"],
            "categories": [c["category"] for c in summary["categories"]],
            "per_category": {c["category"]: c["n"] for c in summary["categories"]},
            "ratio_undefined": summary["nRatioUndefined"],
            "spread": summary["spread"],
            "range": [summary["min"], summary["max"]],
            "category_means": {c["category"]: c["mean"] for c in summary["categories"]},
        },
        "results": {
            "rq2_separation": rq.get("separation", {}),
            "rq1_classifier": rq.get("classifier", {}),
        },
        "power": {
            "min_detectable_eta_squared":
                power["anova"]["minimum_detectable_eta_squared"],
            "min_detectable_auc": power["auc"]["minimum_detectable_auc"],
            "alpha": power["alpha"],
            "target_power": power["target_power"],
        },
        "physics_bound": {
            "formula": "alpha >= h_c(beta_J) / dX",
            "measured_spread": bound["observable"]["spread"],
            "required_coupling": {
                str(row["beta_j_used"]): row["alpha_required"] for row in bound["bound"]
            },
            "meaning": (
                "A necessary condition only. Clearing it does not establish that media moves "
                "populations; falling below it excludes the mechanism within the model."
            ),
        },
        "critical_beta_j": phase["critical_beta_j"] if phase else None,
        "confound": (
            "Each category is drawn from exactly one source dataset: fear-activating from "
            "ISOT-fake, high outrage from SemEval-2019 Task 4, reward-hook from "
            "Webis-Clickbait-17, neutral from PubMed and ISOT-true. The separation is "
            "therefore between corpora and cannot be attributed to framing rather than "
            "provenance. Word counts are matched across categories, so length is not the "
            "confound."
        ),
        "must_never_say": [
            "Do not quote any value for alpha_hat. The coupling is unidentified: significant "
            "in sample, negative held-out R squared, and it scales inversely with a beta_J "
            "the study does not measure.",
            "Never call the measured regions the amygdala. The checkpoint is cortical-only "
            "and the observable is a cortical proxy.",
            "Never say the instrument is validated against real brains. No fMRI comparison "
            "has been run. A published audit reports the released average-subject checkpoint "
            "anti-correlated with cortex, and replicating it is unfinished work.",
            "Never describe the values as measured brain activity. They are predictions from "
            "an encoder; nobody was scanned.",
            "Never claim the instrument detects manipulation. It separates four corpora, and "
            "category is confounded with source.",
        ],
        "when_unsure": (
            "If a question is not answered by these facts, say that the data does not cover "
            "it. Do not estimate, extrapolate, or fill the gap from general knowledge."
        ),
    }
    return facts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    facts = build()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(facts, indent=2), encoding="utf-8")

    print(f"corpus items     : {facts['corpus']['items']}")
    print(f"refusal rules    : {len(facts['must_never_say'])}")
    print(f"\nWrote {args.out} ({args.out.stat().st_size / 1024:.1f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
