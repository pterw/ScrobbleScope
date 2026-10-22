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


IMAGE_STEP = "Read the runner image version"
RESTORE_STEP = "Restore Playwright system packages"
INSTALL_STEP = "Install Playwright browser"
SAVE_STEP = "Save Playwright system packages"
APT_ARCHIVES = "/var/cache/apt/archives"


def _steps(workflow_text: str) -> dict[str, list[str]]:
    """Return each step's lines, keyed by its name, in file order."""
    steps: dict[str, list[str]] = {}
    current = None
    for line in _lines(workflow_text):
        stripped = line.strip()
        if line.startswith("      - name: "):
            current = stripped.removeprefix("- name: ")
            steps[current] = []
        elif current is not None and (not line.strip() or _indent(line) > 6):
            steps[current].append(line)
        elif current is not None:
            current = None
    return steps


def _code(step: list[str]) -> list[str]:
    """Return a step's stripped, non-blank, non-comment lines."""
    stripped = (line.strip() for line in step)
    return [line for line in stripped if line and not line.startswith("#")]


def _value(step: list[str], key: str) -> str | None:
    """Return the value of the step's first ``key: value`` line, if any."""
    prefix = f"{key}: "
    for line in _code(step):
        if line.startswith(prefix):
            return line.removeprefix(prefix)
    return None


def _first_restore_key(step: list[str]) -> str | None:
    """Return the first line under the step's ``restore-keys: |`` block."""
    code = _code(step)
    for i, line in enumerate(code):
        if line.startswith("restore-keys:"):
            return code[i + 1] if i + 1 < len(code) else None
    return None


def _copies(line: str, source: str, target: str) -> bool:
    """True if the ``cp`` line names ``source`` before ``target``."""
    start = line.find(source)
    return (
        "cp" in line.split()
        and start != -1
        and line.find(target, start + len(source)) != -1
    )


def test_playwright_packages_are_restored_seeded_and_saved_around_the_install():
    """The packages are restored before the install, copied into apt's cache
    directory before it, copied back after it and saved even when a later
    step fails, so a slow mirror is paid for at most once (F-B23-57)."""
    steps = _steps(WORKFLOW.read_text(encoding="utf-8"))
    names = list(steps)
    for name in (IMAGE_STEP, RESTORE_STEP, INSTALL_STEP, SAVE_STEP):
        assert name in names, f"step {name!r} is missing from {names}"
    order = [
        names.index(n) for n in (IMAGE_STEP, RESTORE_STEP, INSTALL_STEP, SAVE_STEP)
    ]
    assert order == sorted(order), f"steps are out of order: {names}"

    restore, install, save = steps[RESTORE_STEP], steps[INSTALL_STEP], steps[SAVE_STEP]
    restore_id = _value(restore, "id")
    image_id = _value(steps[IMAGE_STEP], "id")
    assert restore_id, "the restore step needs an id for the save step to read"
    assert image_id, "the runner-image step needs an id for the key to read"
    assert str(_value(restore, "uses")).startswith("actions/cache/restore@")
    assert str(_value(save, "uses")).startswith("actions/cache/save@")

    path = _value(restore, "path")
    assert path, "the restore step has no path"
    assert _value(save, "path") == path, "restore and save use different paths"
    assert _value(save, "key") == (
        "${{ steps." + restore_id + ".outputs.cache-primary-key }}"
    ), "the save step must store under the restore step's primary key"
    assert _value(save, "if") == (
        "steps." + restore_id + ".outputs.cache-hit != 'true'"
    ), "the save step must run only when the exact key was not found"

    key = _value(restore, "key") or ""
    assert f"steps.{image_id}.outputs." in key, "the key omits the runner image"
    prefix = _first_restore_key(restore)
    assert prefix and key.startswith(prefix), "restore-keys is not a key prefix"

    code = _code(install)
    runs = [
        i for i, line in enumerate(code) if "playwright install --with-deps" in line
    ]
    assert len(runs) == 1, f"expected one browser install line, found {runs}"
    seeds = [line for line in code[: runs[0]] if _copies(line, path, APT_ARCHIVES)]
    saves = [line for line in code[runs[0] + 1 :] if _copies(line, APT_ARCHIVES, path)]
    assert seeds, "no line before the install copies the cache into apt's archives"
    assert saves, "no line after the install copies apt's archives back to the cache"
