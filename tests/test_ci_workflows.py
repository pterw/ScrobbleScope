"""The CI quality-gate job must hold no provider secrets.

conftest.py and frontend_gate.py supply placeholder keys, and no step reads a
real one. A secret set at workflow or job level reaches every step and every
third-party action, so a step that ever needs one takes it in its own step-level
``env:``. The guard reads the whole file: a secret in a top-level ``env:``, a
``with:`` input or an inline ``run:`` script is refused as well.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

WORKFLOW = Path(__file__).resolve().parent.parent / ".github" / "workflows" / "test.yml"
SECRET_REFERENCE = re.compile(r"\$\{\{\s*secrets\.")

#: A step's own ``env:`` key sits at this indent (``      - name:`` is six, the
#: step's keys are eight); the workflow ``env:`` is at 0 and the job's at 4.
STEP_ENV_INDENT = 8


def _lines(workflow_text: str) -> list[str]:
    return workflow_text.replace("\r\n", "\n").split("\n")


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _job_level_env(workflow_text: str) -> list[str]:
    """Return the lines of the job-level ``env:`` block (six-space indent)."""
    lines = _lines(workflow_text)
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


def _secret_lines_outside_step_env(workflow_text: str) -> list[str]:
    """Return every secret reference that is not inside a step-level ``env:``."""
    lines = _lines(workflow_text)
    leaked = []
    for number, line in enumerate(lines):
        if not SECRET_REFERENCE.search(line):
            continue
        if line.lstrip().startswith("#"):
            continue
        owner = _indent(line)
        for above in reversed(lines[:number]):
            if above.strip() and _indent(above) < owner:
                if above.strip() == "env:" and _indent(above) == STEP_ENV_INDENT:
                    break
                leaked.append(f"line {number + 1}: {line.strip()}")
                break
        else:
            leaked.append(f"line {number + 1}: {line.strip()}")
    return leaked


def test_test_job_env_passes_no_secret():
    text = WORKFLOW.read_text(encoding="utf-8")
    block = _job_level_env(text)
    assert any("FLASK_ENV" in line for line in block), "env block not read"
    leaked = _secret_lines_outside_step_env(text)
    assert not leaked, f"the workflow passes secrets outside a step env: {leaked}"


def test_env_reader_flags_a_secret_and_a_missing_block():
    text = "jobs:\n  a:\n    env:\n      K: ${{ secrets.K }}\n      FLASK_ENV: x\n"
    block = _job_level_env(text)
    assert [line for line in block if SECRET_REFERENCE.search(line)]
    with pytest.raises(AssertionError, match="no job-level env"):
        _job_level_env("jobs:\n  a:\n    steps: []\n")


STEP = "jobs:\n  a:\n    steps:\n      - name: s\n"


@pytest.mark.parametrize(
    "workflow",
    [
        "env:\n  K: ${{ secrets.K }}\njobs:\n  a:\n    steps: []\n",
        "jobs:\n  a:\n    env:\n      K: ${{ secrets.K }}\n",
        STEP + "        with:\n          token: ${{ secrets.K }}\n",
        STEP + "        run: curl -H ${{ secrets.K }} example.org\n",
    ],
    ids=["workflow-env", "job-env", "with-input", "inline-run"],
)
def test_guard_flags_a_secret_anywhere_but_a_step_env(workflow):
    assert _secret_lines_outside_step_env(workflow)


def test_guard_allows_a_secret_in_a_step_level_env():
    workflow = STEP + "        env:\n          K: ${{ secrets.K }}\n"
    assert _secret_lines_outside_step_env(workflow) == []
