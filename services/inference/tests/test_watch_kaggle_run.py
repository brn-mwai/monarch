"""Failure classification for Kaggle runs.

Every case below is a log this project actually produced. The marker tests carry the most
weight: a run was twice reported as having patched tribev2 because papermill echoes the
failing cell's source into the log and the marker matched that text rather than any output.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "watch_kaggle_run.py"


@pytest.fixture(scope="module")
def watcher():
    spec = importlib.util.spec_from_file_location("watch_kaggle_run", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["watch_kaggle_run"] = module
    spec.loader.exec_module(module)
    return module


def entry(data: str, stream: str = "stderr") -> dict:
    return {"data": data, "stream_name": stream}


def failing_log(error_text: str, cell: str = "In [4]") -> list[dict]:
    return [
        entry("session environment ready", "stdout"),
        entry(error_text),
        entry(f'Exception encountered at "{cell}":'),
    ]


class TestFailureSignatures:
    @pytest.mark.parametrize(
        "error_text,expected",
        [
            ("torch.OutOfMemoryError: CUDA out of memory. Tried to allocate 862.00 MiB", "gpu-out-of-memory"),
            ("NewConnectionError: Temporary failure in name resolution", "no-internet"),
            ("File kaggle_web_client.py in make_post_request", "secret-unavailable"),
            ("ModuleNotFoundError: No module named 'app'", "package-root-missing"),
            ("ValueError: Requested float16 compute type, but the target device or backend do not support efficient float16 computation.", "fp16-unsupported"),
            ("Unable to load any of {libcudnn_cnn.so.9.1.0}", "cudnn-not-on-path"),
            ("ModuleNotFoundError: No module named 'neuralset'", "tribev2-deps-missing"),
            ("AttributeError: module 'exca.steps.base' has no attribute 'NoValue'", "exca-too-old"),
            ("ModuleNotFoundError: No module named 'pyannote'", "whisperx-deps-missing"),
            ("SyntaxError: unterminated string literal (detected at line 7)", "notebook-python-broken"),
            ("AssertionError: compute_type line not found: tribev2 changed", "guard-tripped"),
        ],
    )
    def test_known_failures_are_named(self, watcher, error_text, expected):
        diagnosis = watcher.classify(failing_log(error_text), "ERROR")
        assert diagnosis.signature == expected
        assert diagnosis.action
        assert diagnosis.error_line

    def test_unknown_failure_is_not_guessed(self, watcher):
        diagnosis = watcher.classify(failing_log("RuntimeError: something new"), "ERROR")
        assert diagnosis.signature == "unclassified"
        assert "has not been seen before" in diagnosis.action

    def test_first_matching_signature_wins(self, watcher):
        # An OOM traceback also mentions CUDA; the memory signature is the actionable one.
        log = failing_log("torch.OutOfMemoryError: CUDA out of memory")
        assert watcher.classify(log, "ERROR").signature == "gpu-out-of-memory"


class TestMarkersAreEvidence:
    def test_marker_in_echoed_cell_source_is_not_counted(self, watcher):
        # papermill prints the failing cell's source to stderr. That is not output.
        log = [
            entry("Smoke test PASSED", "stderr"),
            entry('Exception encountered at "In [7]":'),
        ]
        assert watcher.markers_reached(log, watcher.find_failing_cell(log)) == []

    def test_marker_on_stdout_before_the_failure_is_counted(self, watcher):
        log = [
            entry("Smoke test PASSED", "stdout"),
            entry("boom"),
            entry('Exception encountered at "In [9]":'),
        ]
        assert "Smoke test PASSED" in watcher.markers_reached(log, watcher.find_failing_cell(log))

    def test_marker_printed_after_the_failure_is_ignored(self, watcher):
        log = [
            entry('Exception encountered at "In [3]":'),
            entry("Smoke test PASSED", "stdout"),
        ]
        assert watcher.markers_reached(log, watcher.find_failing_cell(log)) == []


class TestScanProgress:
    def test_reads_the_last_item_and_its_rate(self, watcher):
        log = [
            entry("[1/400] naa=0.0789 (204.3s/item)", "stdout"),
            entry("[3/400] naa=UNDEFINED (227.4s/item)", "stdout"),
        ]
        scanned, rate = watcher.scan_progress(log)
        assert (scanned, rate) == (3, 227.4)

    def test_no_scan_lines_reports_zero(self, watcher):
        assert watcher.scan_progress([entry("nothing here")]) == (0, None)

    def test_progress_survives_a_failed_run(self, watcher):
        log = [
            entry("[12/400] naa=0.0421 (210.0s/item)", "stdout"),
            entry("torch.OutOfMemoryError: CUDA out of memory"),
            entry('Exception encountered at "In [11]":'),
        ]
        diagnosis = watcher.classify(log, "ERROR")
        assert diagnosis.items_scanned == 12
        assert diagnosis.signature == "gpu-out-of-memory"


class TestTerminalStates:
    def test_completed_run_needs_no_action(self, watcher):
        diagnosis = watcher.classify([entry("all done", "stdout")], "COMPLETE")
        assert diagnosis.signature == "completed"

    def test_cancelled_run_is_named_as_such(self, watcher):
        diagnosis = watcher.classify([entry("", "stdout")], "CANCEL_ACKNOWLEDGED")
        assert diagnosis.signature == "cancelled"
        assert "while a run is live" in diagnosis.action

    def test_polling_stops_on_a_terminal_state(self, watcher):
        seen = []

        def reader(slug):
            seen.append(slug)
            return "RUNNING" if len(seen) < 3 else "ERROR"

        assert watcher.poll_until_terminal("x/y", reader, interval_seconds=0) == "ERROR"
        assert len(seen) == 3

    def test_polling_gives_up_rather_than_hanging(self, watcher):
        result = watcher.poll_until_terminal("x/y", lambda s: "RUNNING", interval_seconds=0, max_polls=3)
        assert "TIMEOUT" in result
