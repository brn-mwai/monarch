"""Out-of-memory handling in the scan loop.

Two runs died at item 3 and item 4 of 400 because a single long passage needed most of the
card in one attention allocation. Losing 396 items to one item is the failure these tests
exist to prevent, and the rule they enforce is that a skipped item is recorded as absent,
never as a value.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "batch_naa.py"


@pytest.fixture(scope="module")
def batch():
    spec = importlib.util.spec_from_file_location("batch_naa_module", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["batch_naa_module"] = module
    spec.loader.exec_module(module)
    return module


class FakeOutOfMemoryError(Exception):
    """Stands in for torch.OutOfMemoryError, which is what recent torch raises."""

    def __init__(self, message="CUDA out of memory. Tried to allocate 982.00 MiB"):
        super().__init__(message)


FakeOutOfMemoryError.__name__ = "OutOfMemoryError"


class TestRecognisingMemoryFailures:
    def test_the_named_error_type_is_recognised(self, batch):
        assert batch.is_out_of_memory(FakeOutOfMemoryError())

    def test_older_torch_raises_a_plain_runtime_error(self, batch):
        assert batch.is_out_of_memory(RuntimeError("CUDA out of memory"))

    def test_case_does_not_matter(self, batch):
        assert batch.is_out_of_memory(RuntimeError("CUDA Out Of Memory"))

    @pytest.mark.parametrize(
        "error",
        [ValueError("bad input"), KeyError("missing"), RuntimeError("shape mismatch")],
    )
    def test_real_defects_are_not_treated_as_memory_pressure(self, batch, error):
        assert not batch.is_out_of_memory(error)


class TestRetryBehaviour:
    def test_a_transient_failure_succeeds_on_the_retry(self, batch, monkeypatch):
        monkeypatch.setattr(batch, "free_gpu_memory", lambda: None)
        calls = {"n": 0}

        class Service:
            def predict_text(self, text):
                calls["n"] += 1
                if calls["n"] == 1:
                    raise FakeOutOfMemoryError()
                return {"item_vector": "ok"}

        assert batch.scan_one_item(Service(), "text")["item_vector"] == "ok"
        assert calls["n"] == 2

    def test_it_retries_once_and_no_more(self, batch, monkeypatch):
        monkeypatch.setattr(batch, "free_gpu_memory", lambda: None)
        calls = {"n": 0}

        class Service:
            def predict_text(self, text):
                calls["n"] += 1
                raise FakeOutOfMemoryError()

        with pytest.raises(Exception):
            batch.scan_one_item(Service(), "text")
        assert calls["n"] == 2

    def test_the_cache_is_cleared_between_attempts(self, batch, monkeypatch):
        cleared = {"n": 0}
        monkeypatch.setattr(batch, "free_gpu_memory", lambda: cleared.__setitem__("n", cleared["n"] + 1))

        class Service:
            def __init__(self):
                self.first = True

            def predict_text(self, text):
                if self.first:
                    self.first = False
                    raise FakeOutOfMemoryError()
                return {"item_vector": "ok"}

        batch.scan_one_item(Service(), "text")
        assert cleared["n"] == 1

    def test_a_real_defect_is_raised_immediately_without_retrying(self, batch, monkeypatch):
        monkeypatch.setattr(batch, "free_gpu_memory", lambda: None)
        calls = {"n": 0}

        class Service:
            def predict_text(self, text):
                calls["n"] += 1
                raise ValueError("shape mismatch")

        with pytest.raises(ValueError):
            batch.scan_one_item(Service(), "text")
        assert calls["n"] == 1, "a genuine bug must not be retried 400 times"
