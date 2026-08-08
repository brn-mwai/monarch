"""The manuscript's numbers come from the solver's JSON, so the bridge is tested.

A wrong macro here is worse than a crash: it puts a plausible number in a paper.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "paper1_numbers.py"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("paper1_numbers", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["paper1_numbers"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def report() -> dict:
    return {
        "exponents": {
            "beta": {"fitted": 0.4872, "exact": 0.5, "error": 0.0128},
            "gamma": {"fitted": 1.0, "exact": 1.0, "error": 0.0},
            "delta": {"fitted": 3.0042, "exact": 3.0, "error": 0.0042},
            "window": 0.05,
            "points": 60,
        },
        "solver_agreement": {"max_abs_difference": 1.1471579797195375e-09,
                             "at_beta_j_h": [0.95, 0.01]},
        "critical_beta_j": 1.0,
        "phase_boundary": {"beta_j": [1.001, 2.0], "h_c": [0.00002, 0.53284]},
        "alpha_required_per_spread": {"0.1": [0.0002, 5.3284], "1": [0.00002, 0.53284]},
        "bistable_at_zero_field_above_critical": True,
    }


class TestMacros:
    def test_exponents_carry_through_unrounded_to_four_places(self, mod, report):
        pairs = mod.macros(report)
        assert pairs["pbBetaFitted"] == "0.4872"
        assert pairs["pbDeltaFitted"] == "3.0042"
        assert pairs["pbGammaError"] == "0.0000"

    def test_spinodal_is_read_at_the_top_of_the_sweep(self, mod, report):
        pairs = mod.macros(report)
        assert pairs["pbHcAtMax"] == "0.53284"
        assert pairs["pbBetaJMax"] == "2.00"

    def test_solver_agreement_renders_as_latex_scientific(self, mod, report):
        assert mod.macros(report)["pbSolverAgreement"] == r"1.15\times 10^{-9}"

    def test_alpha_macros_exist_only_for_present_spreads(self, mod, report):
        pairs = mod.macros(report)
        assert pairs["pbAlphaRequiredOneTenth"] == "5.3284"
        assert pairs["pbAlphaRequiredUnity"] == "0.5328"
        assert "pbAlphaRequiredHalf" not in pairs

    def test_macro_names_are_letters_only(self, mod, report):
        # TeX control sequences cannot contain digits or underscores.
        for name in mod.macros(report):
            assert name.isalpha(), name


class TestRender:
    def test_every_macro_appears_as_a_newcommand(self, mod, report):
        body = mod.render(mod.macros(report))
        for name, value in mod.macros(report).items():
            assert rf"\newcommand{{\{name}}}{{{value}}}" in body

    def test_output_warns_against_hand_editing(self, mod, report):
        assert "Do not edit" in mod.render(mod.macros(report))


class TestCli:
    def test_missing_report_fails_rather_than_writing_an_empty_file(self, mod, tmp_path):
        out = tmp_path / "numbers.tex"
        argv = sys.argv
        sys.argv = ["paper1_numbers.py", "--report", str(tmp_path / "absent.json"),
                    "--out", str(out)]
        try:
            assert mod.main() == 1
        finally:
            sys.argv = argv
        assert not out.exists()

    def test_run_writes_a_file_the_manuscript_can_input(self, mod, tmp_path, report):
        source = tmp_path / "phase_boundary.json"
        source.write_text(json.dumps(report), encoding="utf-8")
        out = tmp_path / "numbers.tex"
        argv = sys.argv
        sys.argv = ["paper1_numbers.py", "--report", str(source), "--out", str(out)]
        try:
            assert mod.main() == 0
        finally:
            sys.argv = argv
        assert r"\newcommand{\pbBetaFitted}{0.4872}" in out.read_text(encoding="utf-8")
