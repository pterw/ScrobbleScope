"""The CI quality-gate job must hold no provider secrets.

conftest.py and frontend_gate.py supply placeholder keys, and no step reads a
real one. A secret set at job level reaches every step and every third-party
action, so a step that ever needs one takes it in its own ``env:``.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

WORKFLOW = Path(__file__).resolve().parent.parent / ".github" / "workflows" / "test.yml"
SECRET_REFERENCE = re.compile(r"\$\{\{\s*secrets\.")


def _job_level_env(workflow_text: str) -> list[str]:
    """Return the lines of the job-level ``env:`` block (six-space indent)."""
    lines = workflow_text.replace("\r\n", "\n").split("\n")
    start = next(
        (i for i, line in enumerate(lines) if line == "    env:"),
        None,
    )
    assert start is not None, "no job-level env block in test.yml"
    block = []
    for line in lines[start + 1 :]:
        if line.strip() and not line.startswith("      "):
            break
        block.append(line)
    return block


def test_test_job_env_passes_no_secret():
    block = _job_level_env(WORKFLOW.read_text(encoding="utf-8"))
    assert any("FLASK_ENV" in line for line in block), "env block not read"
    leaked = [line for line in block if SECRET_REFERENCE.search(line)]
    assert not leaked, f"job-level env passes secrets: {leaked}"


def test_env_reader_flags_a_secret_and_a_missing_block():
    text = "jobs:\n  a:\n    env:\n      K: ${{ secrets.K }}\n      FLASK_ENV: x\n"
    block = _job_level_env(text)
    assert [line for line in block if SECRET_REFERENCE.search(line)]
    with pytest.raises(AssertionError, match="no job-level env"):
        _job_level_env("jobs:\n  a:\n    steps: []\n")
