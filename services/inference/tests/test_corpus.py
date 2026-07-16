"""Tests for the four-category corpus builder (proposal objective (i)).

The two properties under test are the ones that decide whether the corpus can
support RQ II at all: passages must be length-matched across categories, and the
ISOT wire dateline must not survive into the text. Both failures are silent,
which is why they are tested rather than eyeballed.
"""

import csv
import importlib.util
import sqlite3
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def _load_build_corpus():
    """Import build_corpus.py by path: scripts/ is not an importable package."""
    spec = importlib.util.spec_from_file_location(
        "build_corpus", SCRIPTS / "build_corpus.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["build_corpus"] = module
    spec.loader.exec_module(module)
    return module


bc = _load_build_corpus()


def _sentences(count: int, words_each: int = 12) -> str:
    return " ".join(
        " ".join(f"word{i}" for i in range(words_each)) + "." for _ in range(count)
    )


class TestStripDateline:
    """The ISOT True/Fake leak. Left in, "(Reuters)" alone yields ~1.0 AUC."""

    @pytest.mark.parametrize(
        "raw",
        [
            "WASHINGTON (Reuters) - The council met.",
            "NEW YORK (Reuters) - The council met.",
            "SAN FRANCISCO/LONDON (Reuters) - The council met.",
        ],
    )
    def test_removes_leading_dateline(self, raw):
        assert bc._strip_dateline(raw) == "The council met."

    def test_removes_mid_body_agency_mention(self):
        cleaned = bc._strip_dateline("A source told (Reuters) the vote failed.")
        assert "reuters" not in cleaned.lower()

    def test_leaves_clean_text_intact(self):
        assert bc._strip_dateline("The council met.") == "The council met."

    def test_collapses_whitespace(self):
        assert bc._strip_dateline("a\n\n  b") == "a b"


class TestToPassage:
    def test_returns_none_below_min_words(self):
        assert bc._to_passage("Too short.", min_words=50, max_words=200) is None

    def test_returns_none_on_empty(self):
        assert bc._to_passage("", min_words=10, max_words=20) is None

    def test_reaches_target_and_stops(self):
        passage = bc._to_passage(_sentences(40), min_words=150, max_words=200)
        assert passage is not None
        assert 150 <= len(passage.split()) <= 200

    def test_ends_on_sentence_boundary(self):
        passage = bc._to_passage(_sentences(40), min_words=150, max_words=200)
        assert passage.endswith(".")

    def test_never_exceeds_max(self):
        passage = bc._to_passage(_sentences(60), min_words=10, max_words=30)
        assert len(passage.split()) <= 30

    def test_min_words_is_the_target(self):
        """Passages cluster just above min_words, so min_words drives length.

        This is why DEFAULT_MIN_WORDS is 150 rather than §5.2's lower bound of
        50: the knob that controls how far the stimuli sit from TRIBE's training
        distribution is min_words, not max_words.
        """
        short = bc._to_passage(_sentences(60), min_words=50, max_words=200)
        long = bc._to_passage(_sentences(60), min_words=150, max_words=200)
        assert len(short.split()) < 70
        assert len(long.split()) >= 150


class TestRequireColumns:
    def test_passes_when_present(self):
        bc._require_columns(["a", "b", "c"], ("a", "b"), "x")

    def test_raises_listing_actual_and_expected(self):
        with pytest.raises(ValueError) as excinfo:
            bc._require_columns(["headline", "body"], ("title", "text"), "ISOT x")
        message = str(excinfo.value)
        assert "missing column" in message
        assert "headline" in message
        assert "title" in message


class TestIsot:
    def _write(self, path: Path, rows: list[tuple[str, str, str]]) -> Path:
        with open(path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["title", "text", "subject", "date"])
            for title, text, subject in rows:
                writer.writerow([title, text, subject, "2017-01-01"])
        return path

    def test_fear_filter_keeps_only_threat_language(self, tmp_path):
        path = self._write(
            tmp_path / "Fake.csv",
            [
                ("Deadly virus outbreak", _sentences(40), "News"),
                ("Council approves budget", _sentences(40), "News"),
            ],
        )
        items = list(bc.read_isot(path, fear_only=True, dataset="ISOT-fake"))
        assert len(items) == 1
        assert "virus" in items[0]["title"].lower()

    def test_fear_filter_off_keeps_all(self, tmp_path):
        path = self._write(
            tmp_path / "True.csv",
            [
                ("Wire one", _sentences(40), "politicsNews"),
                ("Wire two", _sentences(40), "politicsNews"),
            ],
        )
        assert len(list(bc.read_isot(path, fear_only=False, dataset="ISOT-true"))) == 2

    def test_dateline_stripped_from_emitted_text(self, tmp_path):
        path = self._write(
            tmp_path / "True.csv",
            [("Wire", f"WASHINGTON (Reuters) - {_sentences(40)}", "politicsNews")],
        )
        items = list(bc.read_isot(path, fear_only=False, dataset="ISOT-true"))
        assert items
        assert "reuters" not in items[0]["text"].lower()

    def test_rejects_wrong_schema(self, tmp_path):
        path = tmp_path / "bad.csv"
        with open(path, "w", newline="", encoding="utf-8") as handle:
            csv.writer(handle).writerow(["headline", "body"])
        with pytest.raises(ValueError, match="missing column"):
            list(bc.read_isot(path, fear_only=False, dataset="x"))


class TestNela:
    def test_keeps_only_unreliable_sources_and_rescales(self, tmp_path):
        db = tmp_path / "nela.db"
        connection = sqlite3.connect(str(db))
        connection.execute(
            "CREATE TABLE newsdata (id TEXT, source TEXT, title TEXT, content TEXT)"
        )
        for source in ("bad_src", "good_src"):
            connection.execute(
                "INSERT INTO newsdata VALUES (?,?,?,?)",
                ("1", source, "t", _sentences(40)),
            )
        connection.commit()
        connection.close()

        labels = tmp_path / "labels.csv"
        with open(labels, "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["source", "aggregated_label"])
            writer.writerow(["bad_src", "2"])
            writer.writerow(["good_src", "0"])

        items = list(bc.read_nela(db, labels))
        assert len(items) == 1
        assert items[0]["source_name"] == "bad_src"
        assert items[0]["credibility"] == "-1.0"

    def test_missing_table_names_the_table(self, tmp_path):
        db = tmp_path / "empty.db"
        sqlite3.connect(str(db)).close()
        labels = tmp_path / "labels.csv"
        with open(labels, "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["source", "aggregated_label"])
            writer.writerow(["s", "2"])
        with pytest.raises(ValueError, match="newsdata"):
            list(bc.read_nela(db, labels))


class TestReport:
    def _rows(self, lengths: dict[str, int]) -> list[dict]:
        return [
            {"category": category, "word_count": str(count)}
            for category, count in lengths.items()
            for _ in range(5)
        ]

    def test_balanced_lengths_pass(self, capsys):
        assert bc._report(self._rows(dict.fromkeys(bc.CATEGORIES, 150))) is True

    def test_imbalanced_lengths_fail(self, capsys):
        lengths = dict.fromkeys(bc.CATEGORIES, 150)
        lengths["reward_hook"] = 12
        assert bc._report(self._rows(lengths)) is False
        assert "IMBALANCED" in capsys.readouterr().out
