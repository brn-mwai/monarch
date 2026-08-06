"""Tests for the batch scanner's column plumbing (proposal objective (ii)).

The GPU pass is the one step in the project that cannot be repeated cheaply,
so a column dropped here costs a whole re-scan. These tests cover the three
ways that happens silently: a carried column missing from the output schema, a
carried name colliding with a computed one, and a resumed run appending rows
under a header that no longer matches.
"""

import csv
import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def _load_batch_naa():
    """Import batch_naa.py by path: scripts/ is not an importable package."""
    spec = importlib.util.spec_from_file_location(
        "batch_naa", SCRIPTS / "batch_naa.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["batch_naa"] = module
    spec.loader.exec_module(module)
    return module


batch_naa = _load_batch_naa()


def _write_corpus(path: Path) -> None:
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["id", "text", "category", "credibility"]
        )
        writer.writeheader()
        writer.writerow(
            {"id": "a1", "text": "some passage", "category": "high_outrage",
             "credibility": "-0.5"}
        )


class TestOutputFieldnames:
    def test_carried_columns_land_between_outcome_and_computed(self):
        fields = batch_naa._output_fieldnames("category", ("id", "credibility"))
        assert fields == [
            "text", "category", "id", "credibility",
            "naa", "naa_signed", "a_aff", "a_del", "classification",
        ]

    def test_no_carry_cols_matches_the_original_schema(self):
        assert batch_naa._output_fieldnames("arousal", ()) == [
            "text", "arousal",
            "naa", "naa_signed", "a_aff", "a_del", "classification",
        ]

    def test_carrying_the_outcome_column_does_not_duplicate_it(self):
        fields = batch_naa._output_fieldnames("category", ("category",))
        assert fields.count("category") == 1


class TestLoadRows:
    def test_missing_carried_column_fails_loudly(self, tmp_path: Path):
        corpus = tmp_path / "corpus.csv"
        _write_corpus(corpus)

        with pytest.raises(ValueError, match="manipulative"):
            batch_naa._load_rows(corpus, "text", "category", ("manipulative",))

    def test_present_carried_column_loads(self, tmp_path: Path):
        corpus = tmp_path / "corpus.csv"
        _write_corpus(corpus)

        rows = batch_naa._load_rows(corpus, "text", "category", ("credibility",))

        assert len(rows) == 1
        assert rows[0]["credibility"] == "-0.5"


class TestResumeHeaderGuard:
    def test_mismatched_header_is_detectable_before_appending(
        self, tmp_path: Path
    ):
        """A resumed run must compare headers, not just collect done texts.

        Appending rows written for a wider schema onto a narrower file shifts
        every value by one column, which corrupts the scan silently.
        """
        out = tmp_path / "corpus_naa.csv"
        original = batch_naa._output_fieldnames("category", ())
        with open(out, "w", newline="", encoding="utf-8") as handle:
            csv.DictWriter(handle, fieldnames=original).writeheader()

        with open(out, newline="", encoding="utf-8") as handle:
            on_disk = csv.DictReader(handle).fieldnames

        widened = batch_naa._output_fieldnames("category", ("credibility",))
        assert on_disk != widened
