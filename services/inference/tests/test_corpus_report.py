"""Corpus-level AMA report assembly (objective vii).

The fixtures here are synthetic on purpose: they exercise the assembly, and none of
them ever reaches an output the reader sees. The behaviours that matter are the
refusals -- missing input, missing column, no usable rows -- because the one thing
this script must never do is produce a report-shaped artifact without measurements
behind it.
"""

from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "build_corpus_report.py"


def _load_script():
    spec = importlib.util.spec_from_file_location("build_corpus_report", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["build_corpus_report"] = module
    spec.loader.exec_module(module)
    return module


def _write_scan(path: Path, rows: list[dict]) -> None:
    fieldnames = [
        "text",
        "category",
        "id",
        "manipulative",
        "credibility",
        "source_dataset",
        "word_count",
        "naa",
        "naa_signed",
        "a_aff",
        "a_del",
        "classification",
    ]
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})


def _sample_rows() -> list[dict]:
    rows = []
    for i in range(12):
        outrage = i % 2 == 0
        rows.append(
            {
                "text": f"item {i}",
                "category": "high_outrage" if outrage else "neutral_informational",
                "id": f"x{i}",
                "manipulative": 1 if outrage else 0,
                "credibility": 0.2 if outrage else 0.9,
                "source_dataset": "fixture",
                "word_count": 160,
                # Half the rows carry no ratio NAA, mirroring the undefined regime.
                "naa": "" if outrage else f"{0.5 + i / 100:.4f}",
                "naa_signed": f"{(0.4 if outrage else -0.3) + i / 200:.4f}",
                "a_aff": "0.1",
                "a_del": "0.1",
                "classification": "HIGH" if outrage else "LOW",
            }
        )
    return rows


def _run(module, args: list[str]) -> int:
    argv = sys.argv
    sys.argv = ["build_corpus_report.py", *args]
    try:
        return module.main()
    finally:
        sys.argv = argv


class TestRefusals:
    def test_missing_csv_fails_rather_than_drawing_a_placeholder(self, tmp_path, capsys):
        module = _load_script()
        code = _run(
            module,
            ["--csv", str(tmp_path / "nope.csv"), "--out-dir", str(tmp_path / "out")],
        )
        assert code == 1
        assert "no synthetic substitute" in capsys.readouterr().err
        assert not (tmp_path / "out").exists()

    def test_missing_metric_column_fails(self, tmp_path, capsys):
        module = _load_script()
        scan = tmp_path / "scan.csv"
        _write_scan(scan, _sample_rows())
        code = _run(
            module,
            [
                "--csv", str(scan),
                "--out-dir", str(tmp_path / "out"),
                "--naa-col", "not_a_column",
            ],
        )
        assert code == 1
        assert "not in CSV header" in capsys.readouterr().err

    def test_header_only_scan_fails(self, tmp_path, capsys):
        module = _load_script()
        scan = tmp_path / "scan.csv"
        _write_scan(scan, [])
        code = _run(module, ["--csv", str(scan), "--out-dir", str(tmp_path / "out")])
        assert code == 1
        assert "no rows" in capsys.readouterr().err


class TestReport:
    @pytest.fixture()
    def built(self, tmp_path):
        module = _load_script()
        scan = tmp_path / "scan.csv"
        out = tmp_path / "out"
        _write_scan(scan, _sample_rows())
        code = _run(module, ["--csv", str(scan), "--out-dir", str(out)])
        assert code == 0
        return out

    def test_writes_every_artifact(self, built):
        for name in (
            "corpus_ranked.csv",
            "corpus_report.json",
            "fig_violin.png",
            "fig_ranked.png",
            "fig_free_energy_atlas.png",
        ):
            assert (built / name).exists(), name

    def test_ranked_table_is_ordered_and_complete(self, built):
        with open(built / "corpus_ranked.csv", newline="", encoding="utf-8") as handle:
            records = list(csv.DictReader(handle))
        assert len(records) == 12
        values = [float(r["naa_signed"]) for r in records]
        assert values == sorted(values, reverse=True)
        assert [int(r["rank"]) for r in records] == list(range(1, 13))

    def test_undefined_ratio_rows_are_counted_not_dropped(self, built):
        report = json.loads((built / "corpus_report.json").read_text(encoding="utf-8"))
        assert report["n_rows"] == 12
        assert report["n_scored"] == 12
        assert report["n_ratio_undefined"] == 6

    def test_alpha_is_swept_and_never_reported_as_a_fit(self, built):
        report = json.loads((built / "corpus_report.json").read_text(encoding="utf-8"))
        assert report["alpha_is_fitted"] is False
        assert len(report["alpha_grid"]) > 1
        assert "alpha_hat" not in (built / "corpus_report.json").read_text(encoding="utf-8")

    def test_threshold_is_marked_as_fitted_in_sample(self, built):
        report = json.loads((built / "corpus_report.json").read_text(encoding="utf-8"))
        assert report["validation"]["threshold_fitted_in_sample"] is True
        assert report["threshold_fitted_in_sample"] is True

    def test_missing_baseline_category_does_not_crash(self, tmp_path):
        module = _load_script()
        scan = tmp_path / "scan.csv"
        rows = [r for r in _sample_rows() if r["category"] == "high_outrage"]
        _write_scan(scan, rows)
        code = _run(module, ["--csv", str(scan), "--out-dir", str(tmp_path / "out2")])
        assert code == 0
        report = json.loads(
            (tmp_path / "out2" / "corpus_report.json").read_text(encoding="utf-8")
        )
        assert report["distribution"] is None
