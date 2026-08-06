"""Record what the loaded TRIBE v2 checkpoint actually is, as re-runnable evidence.

Chapter 4 must state the model's depth and how it handles subject identity. Both
were open questions in the Gate 1 handoff, and both were being inferred from a run
folder name (``.../tribe_release/half_depth/...``), which is a claim, not evidence.

This script writes ``tribe_facts.json``: every field carries the module path,
attribute or tensor shape it was read from, so a reader can re-derive it. Nothing
here is interpreted -- the paper does the interpreting, from these numbers.

Two modes:

    python scripts/verify_tribe_checkpoint.py --config tribe-ckpt/config.yaml \
        --out tribe_facts.json

        Config only. No GPU, no weights. Reports what the checkpoint was TRAINED
        with.

    python scripts/verify_tribe_checkpoint.py --load-model --out tribe_facts.json

        Loads the model through the same path Monarch's inference uses and reports
        what is TRUE AT INFERENCE. These two answers differ for subject handling,
        which is exactly why both are recorded.
"""

from __future__ import annotations

import argparse
import inspect
import json
import sys
from pathlib import Path
from typing import Any


def _tolerant_loader():
    """A YAML loader that survives the checkpoint's python-object tags.

    The config was dumped with `!!python/object` tags for exca/neuralset classes.
    `UnsafeLoader` needs those classes importable, which defeats the point of a
    verifier that must run before the environment is complete; every tagged node
    is therefore reduced to its plain structure.
    """
    import yaml

    class TolerantLoader(yaml.SafeLoader):
        pass

    def _plain(loader, tag_suffix, node):
        if isinstance(node, yaml.MappingNode):
            return loader.construct_mapping(node, deep=True)
        if isinstance(node, yaml.SequenceNode):
            return loader.construct_sequence(node, deep=True)
        return loader.construct_scalar(node)

    TolerantLoader.add_multi_constructor("tag:yaml.org,2002:python/", _plain)
    TolerantLoader.add_multi_constructor("!", _plain)
    return TolerantLoader


def _from_config(config_path: Path) -> dict:
    import yaml

    with open(config_path, encoding="utf-8") as handle:
        config = yaml.load(handle, Loader=_tolerant_loader())

    brain = config.get("brain_model_config", {}) or {}
    encoder = brain.get("encoder", {}) or {}
    subject_layers = brain.get("subject_layers", {}) or {}
    infra = config.get("infra", {}) or {}

    return {
        "source": str(config_path),
        "run_folder": infra.get("folder"),
        "encoder_name": encoder.get("name"),
        "encoder_depth": encoder.get("depth"),
        "encoder_heads": encoder.get("heads"),
        "subject_layers_name": subject_layers.get("name"),
        "n_subjects": subject_layers.get("n_subjects"),
        "subject_dropout": subject_layers.get("subject_dropout"),
        "subject_layers_mode": subject_layers.get("mode"),
        "average_subjects_trained": subject_layers.get("average_subjects"),
        "average_subjects_top_level": config.get("average_subjects"),
        "seed": config.get("seed"),
    }


def _module_evidence(module: Any) -> dict:
    """Class, defining file and parameter shapes for one module."""
    cls = type(module)
    try:
        source_file = inspect.getsourcefile(cls)
    except (TypeError, OSError):
        source_file = None
    shapes = {
        name: list(param.shape)
        for name, param in getattr(module, "named_parameters", lambda: [])()
    }
    return {
        "class": f"{cls.__module__}.{cls.__qualname__}",
        "defined_in": source_file,
        "parameter_shapes": shapes,
    }


def _from_model() -> dict:
    from app.services.inference import TribeInferenceService

    service = TribeInferenceService()
    service.load_model()
    model = service.model

    facts: dict = {"loaded_via": "app.services.inference.TribeInferenceService.load_model"}

    # Depth: count the repeated encoder blocks rather than trusting the config, since
    # a half-depth release would keep the full-depth config around it.
    import torch

    named = dict(model.named_modules()) if hasattr(model, "named_modules") else {}
    block_prefixes = set()
    for name in named:
        parts = name.split(".")
        for i, part in enumerate(parts):
            if part.isdigit() and i > 0:
                block_prefixes.add(".".join(parts[: i + 1]))
    depth_by_prefix: dict[str, int] = {}
    for prefix in block_prefixes:
        parent = prefix.rsplit(".", 1)[0]
        depth_by_prefix[parent] = depth_by_prefix.get(parent, 0) + 1
    facts["module_repeat_counts"] = dict(sorted(depth_by_prefix.items()))

    # Subject handling at inference. demo_utils.from_pretrained overrides the trained
    # setting, so this is the value that governs Monarch's predictions.
    subject_modules = {
        name: _module_evidence(mod)
        for name, mod in named.items()
        if "subject" in name.lower() and list(getattr(mod, "parameters", lambda: [])())
    }
    facts["subject_modules"] = subject_modules
    for name, mod in named.items():
        if hasattr(mod, "average_subjects"):
            facts.setdefault("average_subjects_flags", {})[name] = bool(
                getattr(mod, "average_subjects")
            )

    total_params = sum(p.numel() for p in model.parameters())
    facts["total_parameters"] = int(total_params)
    facts["torch_version"] = torch.__version__
    try:
        facts["device"] = str(next(model.parameters()).device)
    except StopIteration:
        facts["device"] = "unknown"

    return facts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--load-model", action="store_true")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    if not args.config and not args.load_model:
        print("[FAIL] pass --config, --load-model, or both", file=sys.stderr)
        return 1

    facts: dict = {}
    if args.config:
        if not args.config.exists():
            print(f"[FAIL] no config at {args.config}", file=sys.stderr)
            return 1
        facts["trained_config"] = _from_config(args.config)
    if args.load_model:
        facts["at_inference"] = _from_model()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(facts, indent=2), encoding="utf-8")
    print(json.dumps(facts, indent=2))
    print(f"\nWrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
