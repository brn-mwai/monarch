"""Retry policy and state for the scan loop.

The decisions under test are the ones that spend GPU quota. A restart is worth spending only
when a fresh session can fix the failure by itself; a syntax error or a missing dependency
reproduces exactly the same failure and costs the same hours to find out.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "kaggle_run_state.py"


@pytest.fixture(scope="module")
def runner():
    spec = importlib.util.spec_from_file_location("kaggle_run_state", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["kaggle_run_state"] = module
    spec.loader.exec_module(module)
    return module


def diagnosis(runner, signature: str, seconds=None):
    # The module re-exports Diagnosis, so the test does not depend on import order.
    return runner.Diagnosis(status="ERROR", signature=signature, seconds_per_item=seconds)


def now_iso(offset_hours: float = 0.0) -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=offset_hours)).isoformat(timespec="seconds")


class TestRetryPolicy:
    @pytest.mark.parametrize(
        "signature",
        ["cancelled", "gpu-out-of-memory", "no-internet", "secret-unavailable", "gpu-arch-unsupported"],
    )
    def test_restartable_failures_are_retried(self, runner, signature):
        allowed, _ = runner.should_retry(diagnosis(runner, signature), [], 6, scanned=12)
        assert allowed

    @pytest.mark.parametrize(
        "signature",
        [
            "notebook-python-broken",
            "package-root-missing",
            "tribev2-deps-missing",
            "exca-too-old",
            "whisperx-deps-missing",
            "guard-tripped",
            "fp16-unsupported",
            "unclassified",
        ],
    )
    def test_code_failures_are_not_retried(self, runner, signature):
        allowed, reason = runner.should_retry(diagnosis(runner, signature), [], 6, scanned=12)
        assert not allowed
        assert "code change" in reason

    def test_a_finished_scan_is_never_restarted(self, runner):
        allowed, reason = runner.should_retry(
            diagnosis(runner, "gpu-out-of-memory"), [], 6, scanned=400
        )
        assert not allowed
        assert reason == "scan complete"

    def test_a_completed_run_is_never_restarted(self, runner):
        allowed, _ = runner.should_retry(diagnosis(runner, "completed"), [], 6, scanned=400)
        assert not allowed


class TestRetryBudget:
    def test_budget_stops_a_loop(self, runner):
        attempts = [now_iso(-h) for h in range(6)]
        allowed, reason = runner.should_retry(
            diagnosis(runner, "gpu-out-of-memory"), attempts, 6, scanned=10
        )
        assert not allowed
        assert "budget spent" in reason

    def test_attempts_older_than_a_day_do_not_count(self, runner):
        attempts = [now_iso(-30), now_iso(-48)]
        assert runner.retries_in_last_day(attempts) == 0

    def test_malformed_timestamps_are_ignored_not_fatal(self, runner):
        assert runner.retries_in_last_day(["not-a-date", now_iso(-1)]) == 1


class TestAcceleratorPinning:
    def test_push_metadata_is_forced_to_two_t4s(self, runner, tmp_path):
        metadata = tmp_path / "kernel-metadata.json"
        metadata.write_text(json.dumps({"id": "x/y", "accelerator": "nvidiaTeslaP100"}), encoding="utf-8")

        changed = runner.force_t4(tmp_path)
        written = json.loads(metadata.read_text(encoding="utf-8"))

        assert changed["previous"] == "nvidiaTeslaP100"
        assert written["accelerator"] == "gpuT4x2"
        assert written["enable_gpu"] is True
        assert written["enable_internet"] is True

    def test_the_enum_is_the_one_kaggle_accepts(self, runner):
        # "nvidiaTeslaT4" is silently ignored and falls back to a P100.
        assert runner.ACCELERATOR == "gpuT4x2"


class TestProgressCarrying:
    def test_rows_are_counted_from_the_partial_csv(self, runner):
        text = "text,naa\na,0.1\nb,\nc,0.3\n"
        assert runner.count_scanned(text) == 3

    def test_an_empty_partial_counts_as_no_progress(self, runner):
        assert runner.count_scanned("text,naa\n") == 0

    def test_progress_never_goes_backwards_in_state(self, runner):
        state = runner.build_state("x/y", "ERROR", None, scanned=12, previous={"scanned": 12})
        assert state["scanned"] == 12
        assert state["total"] == 400
        assert state["running"] is False

    def test_running_state_is_marked_running(self, runner):
        state = runner.build_state("x/y", "KernelWorkerStatus.RUNNING", None, 40, {})
        assert state["running"] is True
        assert state["signature"] == "running"
