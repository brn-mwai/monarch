"""Compile every Python block in the Kaggle notebooks before they cost GPU time.

A run reached the Kaggle cluster with a broken string literal inside a heredoc and died
in the third cell. Nothing catches that: the notebook is JSON, so the Python inside a bash
cell is just text until the moment it executes on a machine we are paying for.

This walks each notebook, compiles plain code cells and the body of every quoted heredoc,
and fails locally in under a second instead of ten minutes into a session.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

NOTEBOOKS = sorted((Path(__file__).resolve().parents[3] / "notebooks").glob("*.ipynb"))

# python3 - <<'TAG' ... TAG   and   python - <<'TAG' ... TAG
HEREDOC = re.compile(r"python3?\s+-\s+<<'(\w+)'\n(.*?)\n\1", re.S)


def _cells(path: Path):
    # utf-8-sig: monarch_kaggle.ipynb carries a BOM, which json.loads rejects outright.
    return json.loads(path.read_text(encoding="utf-8-sig"))["cells"]


@pytest.mark.parametrize("path", NOTEBOOKS, ids=lambda p: p.name)
def test_notebook_is_valid_json_with_cells(path: Path):
    cells = _cells(path)
    assert cells, f"{path.name} has no cells"


@pytest.mark.parametrize("path", NOTEBOOKS, ids=lambda p: p.name)
def test_every_python_block_compiles(path: Path):
    failures = []
    for index, cell in enumerate(_cells(path)):
        if cell.get("cell_type") != "code":
            continue
        source = "".join(cell["source"])

        for match in HEREDOC.finditer(source):
            try:
                compile(match.group(2), f"{path.name}:cell{index}:heredoc", "exec")
            except SyntaxError as exc:
                failures.append(f"{path.name} cell {index} heredoc: {exc}")

        # A %%bash cell is shell, not Python; its embedded Python is covered above.
        if source.lstrip().startswith("%%"):
            continue
        try:
            compile(source, f"{path.name}:cell{index}", "exec")
        except SyntaxError as exc:
            failures.append(f"{path.name} cell {index}: {exc}")

    assert not failures, "\n".join(failures)
