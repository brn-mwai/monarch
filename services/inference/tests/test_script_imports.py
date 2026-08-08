"""Every script that imports the app package must be runnable as `python scripts/x.py`.

Python puts the script's own directory on sys.path, not the working directory, so
`from app.services...` fails unless the script adds the package root itself. Four scripts
were missing that line, including batch_naa.py, which is the eight-hour GPU scan: it would
have died on the import twenty-five minutes into a session that had already paid for the
model download.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
SCRIPTS = sorted(SCRIPTS_DIR.glob("*.py"))

IMPORTS_APP = re.compile(r"^\s*(from app[.\s]|import app[.\s])", re.M)
ADDS_PACKAGE_ROOT = re.compile(
    r"sys\.path\.insert\(\s*0\s*,\s*str\(Path\(__file__\)\.resolve\(\)\.parents\[1\]\)\s*\)"
)


def _scripts_importing_app() -> list[Path]:
    return [path for path in SCRIPTS if IMPORTS_APP.search(path.read_text(encoding="utf-8"))]


def test_some_scripts_import_the_app_package():
    assert _scripts_importing_app(), "no scripts import app; this test is watching nothing"


@pytest.mark.parametrize("path", _scripts_importing_app(), ids=lambda p: p.name)
def test_script_adds_the_package_root_to_sys_path(path: Path):
    source = path.read_text(encoding="utf-8")
    assert ADDS_PACKAGE_ROOT.search(source), (
        f"{path.name} imports app but never puts the package root on sys.path, so it "
        f"raises ModuleNotFoundError when run as `python scripts/{path.name}`"
    )


@pytest.mark.parametrize("path", _scripts_importing_app(), ids=lambda p: p.name)
def test_package_root_is_added_before_the_app_import(path: Path):
    source = path.read_text(encoding="utf-8")
    insert = ADDS_PACKAGE_ROOT.search(source)
    first_top_level_app_import = IMPORTS_APP.search(source)
    if first_top_level_app_import is None:
        pytest.skip("app is imported lazily inside a function")
    assert insert.start() < first_top_level_app_import.start(), (
        f"{path.name} adds the package root after importing app"
    )
