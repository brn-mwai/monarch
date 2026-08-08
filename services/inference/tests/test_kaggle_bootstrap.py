"""Session bootstrap for the Kaggle scan.

Each case here corresponds to a run that was actually lost: fp16 requested on a P100,
a token that reached only one of the two launch paths, and a cuDNN directory that
exists but holds no convolution library. They cost GPU hours to find and now cost
milliseconds to catch.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "kaggle_bootstrap.py"


@pytest.fixture(scope="module")
def bootstrap():
    spec = importlib.util.spec_from_file_location("kaggle_bootstrap", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["kaggle_bootstrap"] = module
    spec.loader.exec_module(module)
    return module


class TestComputeTypeSelection:
    @pytest.mark.parametrize("capability,expected", [(6, "float32"), (7, "float16"), (8, "float16")])
    def test_precision_follows_capability(self, bootstrap, capability, expected):
        assert bootstrap.select_whisper_compute_type(capability) == expected

    def test_p100_never_asks_for_fp16(self, bootstrap):
        # sm_60 with float16 is the exact ValueError that killed one run.
        assert bootstrap.select_whisper_compute_type(6) != "float16"

    def test_cpu_only_session_falls_back(self, bootstrap):
        assert bootstrap.select_whisper_compute_type(0) == "float32"


class TestTokenResolution:
    def _write_token(self, root: Path, value: str) -> Path:
        dataset = root / "monarch-hf-token"
        dataset.mkdir(parents=True, exist_ok=True)
        path = dataset / "hf_token.txt"
        path.write_text(value, encoding="utf-8")
        return path

    def test_dataset_is_preferred_over_the_secret_store(self, bootstrap, tmp_path):
        self._write_token(tmp_path, "hf_from_dataset")

        def unused_reader(name):
            raise AssertionError("secret store must not be consulted when a dataset is attached")

        assert bootstrap.read_hf_token(tmp_path, unused_reader) == "hf_from_dataset"

    def test_falls_back_to_the_secret_store(self, bootstrap, tmp_path):
        assert bootstrap.read_hf_token(tmp_path, lambda name: "hf_from_secret") == "hf_from_secret"

    def test_blank_dataset_file_is_ignored(self, bootstrap, tmp_path):
        self._write_token(tmp_path, "   \n")
        assert bootstrap.read_hf_token(tmp_path, lambda name: "hf_from_secret") == "hf_from_secret"

    def test_no_token_anywhere_raises_with_instructions(self, bootstrap, tmp_path):
        with pytest.raises(RuntimeError, match="hf_token.txt"):
            bootstrap.read_hf_token(tmp_path, lambda name: "")


class TestCudnnDiscovery:
    def test_missing_convolution_library_is_an_error(self, bootstrap, tmp_path):
        for package in ("cudnn", "cublas"):
            (tmp_path / package / "lib").mkdir(parents=True)
        roots = [tmp_path / "cudnn", tmp_path / "cublas"]

        with pytest.raises(RuntimeError, match="libcudnn_cnn"):
            bootstrap.find_cudnn_library_dirs(roots)

    def test_absent_directory_is_reported(self, bootstrap, tmp_path):
        with pytest.raises(RuntimeError, match="absent"):
            bootstrap.find_cudnn_library_dirs([tmp_path / "nope"])

    def test_returns_both_directories_when_present(self, bootstrap, tmp_path):
        for package in ("cudnn", "cublas"):
            (tmp_path / package / "lib").mkdir(parents=True)
        (tmp_path / "cudnn" / "lib" / "libcudnn_cnn.so.9").touch()

        found = bootstrap.find_cudnn_library_dirs([tmp_path / "cudnn", tmp_path / "cublas"])
        assert [d.name for d in found] == ["lib", "lib"]


class TestEnvironmentApplication:
    def test_sets_every_variable_the_cascade_reads(self, bootstrap, tmp_path, monkeypatch):
        (tmp_path / "tok").mkdir()
        (tmp_path / "tok" / "hf_token.txt").write_text("hf_x", encoding="utf-8")
        monkeypatch.setattr(bootstrap, "find_cudnn_library_dirs", lambda: [Path("/cudnn/lib")])

        environ = {}
        applied = bootstrap.apply_session_environment(
            capability_major=6, input_root=tmp_path, environ=environ
        )

        assert applied["MONARCH_WHISPER_COMPUTE"] == "float32"
        assert applied["HF_TOKEN"] == "hf_x"
        assert applied["LD_LIBRARY_PATH"].startswith(Path("/cudnn/lib").as_posix())
        assert environ["MONARCH_WHISPER_DEVICE"] == "cuda"
        assert environ["PYTHONPATH"].endswith("tribev2")

    def test_does_not_touch_the_real_environment(self, bootstrap, tmp_path, monkeypatch):
        (tmp_path / "tok").mkdir()
        (tmp_path / "tok" / "hf_token.txt").write_text("hf_x", encoding="utf-8")
        monkeypatch.setattr(bootstrap, "find_cudnn_library_dirs", lambda: [Path("/cudnn/lib")])

        import os

        before = dict(os.environ)
        bootstrap.apply_session_environment(
            capability_major=7, input_root=tmp_path, environ={}
        )
        assert dict(os.environ) == before

    def test_existing_library_path_is_preserved(self, bootstrap, tmp_path, monkeypatch):
        (tmp_path / "tok").mkdir()
        (tmp_path / "tok" / "hf_token.txt").write_text("hf_x", encoding="utf-8")
        monkeypatch.setattr(bootstrap, "find_cudnn_library_dirs", lambda: [Path("/cudnn/lib")])

        applied = bootstrap.apply_session_environment(
            capability_major=7,
            input_root=tmp_path,
            environ={"LD_LIBRARY_PATH": "/existing"},
        )
        assert applied["LD_LIBRARY_PATH"].endswith("/existing")
