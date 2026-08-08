"""Tests for the scan-output check, including the false failure it was written to avoid."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "verify_scan_output.py"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("verify_scan_output", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["verify_scan_output"] = module
    spec.loader.exec_module(module)
    return module


def corpus_rows(n: int = 4) -> list[dict]:
    return [
        {"text": f"article {i}", "category": f"cat{i % 2}", "id": str(i)}
        for i in range(n)
    ]


def scan_rows(n: int = 2) -> list[dict]:
    rows = []
    for i in range(n):
        a_aff = 0.010000 + i / 1000
        a_del = 0.040000
        rows.append({
            "text": f"article {i}",
            "category": f"cat{i % 2}",
            "id": str(i),
            "a_aff": f"{a_aff:.6f}",
            "a_del": f"{a_del:.6f}",
            "naa_signed": f"{a_aff - a_del:.6f}",
            "naa": "0.25",
        })
    return rows


class TestPasses:
    def test_a_matching_partial_scan_passes(self, mod):
        failures, facts = mod.check(corpus_rows(4), scan_rows(2))
        assert failures == []
        assert facts["complete"] is False
        assert facts["n_scanned"] == 2

    def test_a_complete_scan_is_flagged_complete(self, mod):
        failures, facts = mod.check(corpus_rows(2), scan_rows(2))
        assert failures == []
        assert facts["complete"] is True

    def test_six_decimal_rounding_is_not_a_failure(self, mod):
        # The check that failed by hand at 1e-9: separately rounded columns disagree by 1e-6.
        rows = scan_rows(1)
        rows[0]["naa_signed"] = "-0.029999"  # a_aff - a_del is -0.030000
        failures, _ = mod.check(corpus_rows(1), rows)
        assert failures == []

    def test_worst_case_triple_rounding_still_passes(self, mod):
        # Three independently rounded 6-dp columns can disagree by up to 1.5e-6. A tolerance
        # of 1e-6 rejected 4 sound rows out of 50 in the first completed run.
        rows = scan_rows(2)
        rows[0]["naa_signed"] = "-0.0299985"
        failures, _ = mod.check(corpus_rows(2), rows)
        assert failures == []

    def test_undefined_ratio_values_are_counted_not_failed(self, mod):
        rows = scan_rows(2)
        rows[1]["naa"] = ""
        failures, facts = mod.check(corpus_rows(2), rows)
        assert failures == []
        assert facts["ratio_undefined"] == 1
        assert facts["ratio_defined"] == 1


class TestFailures:
    def test_text_not_matching_the_corpus_fails(self, mod):
        rows = scan_rows(2)
        rows[1]["text"] = "something else"
        failures, _ = mod.check(corpus_rows(2), rows)
        assert any("differ from the corpus on text" in f for f in failures)

    def test_rows_out_of_order_fail(self, mod):
        failures, _ = mod.check(corpus_rows(2), list(reversed(scan_rows(2))))
        assert any("differ from the corpus" in f for f in failures)

    def test_a_real_inconsistency_beyond_rounding_fails(self, mod):
        rows = scan_rows(1)
        rows[0]["naa_signed"] = "-0.020000"
        failures, _ = mod.check(corpus_rows(1), rows)
        assert any("does not equal a_aff - a_del" in f for f in failures)

    def test_duplicate_texts_fail(self, mod):
        rows = scan_rows(2)
        rows[1]["text"] = rows[0]["text"]
        corpus = corpus_rows(2)
        corpus[1]["text"] = corpus[0]["text"]
        failures, _ = mod.check(corpus, rows)
        assert any("duplicate texts" in f for f in failures)

    def test_a_constant_column_fails_as_not_a_measurement(self, mod):
        rows = scan_rows(2)
        for row in rows:
            row["a_aff"] = "0.010000"
            row["a_del"] = "0.040000"
            row["naa_signed"] = "-0.030000"
        failures, _ = mod.check(corpus_rows(2), rows)
        assert any("not a measurement" in f for f in failures)

    def test_more_scanned_rows_than_corpus_rows_fails(self, mod):
        failures, _ = mod.check(corpus_rows(1), scan_rows(2))
        assert any("corpus only has" in f for f in failures)

    def test_an_empty_scan_fails(self, mod):
        failures, _ = mod.check(corpus_rows(2), [])
        assert failures == ["scan output is empty"]
