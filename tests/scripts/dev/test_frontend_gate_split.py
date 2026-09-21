"""Invariants the frontend gate split must keep (F-B21-51).

Three ways a split can pass every existing check while being wrong:

1. A moved check drops out of `CHECKS`. Nothing fails, because the planned
   run count is derived from the same tuple; the check just stops running in
   CI.
2. A test keeps patching `frontend_gate.X` after the code that reads `X`
   moved. The patch lands in a namespace nobody reads, and the test runs
   against the real object.
3. A sibling imports `scrobblescope` above the facade's environment
   bootstrap, and `scrobblescope.config` freezes empty provider keys, so the
   gate refuses to start in CI's production mode only.
"""

from __future__ import annotations

import importlib
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.dev import frontend_gate
from tests.scripts.dev.gate_parity import (
    defined_names,
    gate_modules,
    names_read_in_functions,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
TEST_DIR = Path(__file__).resolve().parent

_PATCH_STRING = re.compile(
    r'patch\(\s*"scripts\.dev\.(?P<module>\w+)\.(?P<name>\w+)"', re.MULTILINE
)
_PATCH_OBJECT = re.compile(
    r'patch\.object\(\s*(?P<module>_?frontend_gate\w*)\s*,\s*"(?P<name>\w+)"',
    re.MULTILINE,
)


def _module_for_test_file(path: Path) -> str:
    """test_frontend_gate.py -> frontend_gate; test_frontend_gate_x.py -> _frontend_gate_x."""
    stem = path.stem.removeprefix("test_")
    return stem if stem == "frontend_gate" else f"_{stem}"


def _patch_targets() -> list[tuple[str, str, str]]:
    """(test file, module, name) for every gate patch in the gate test files."""
    targets = []
    for path in sorted(TEST_DIR.glob("test_frontend_gate*.py")):
        text = path.read_text(encoding="utf-8")
        for pattern in (_PATCH_STRING, _PATCH_OBJECT):
            for match in pattern.finditer(text):
                targets.append((path.name, match["module"], match["name"]))
    return targets


def test_every_check_in_every_gate_module_is_registered_once() -> None:
    registered = [entry[1] for entry in frontend_gate.CHECKS]
    assert len(registered) == len(set(registered)), "a check is registered twice"
    defined = {
        getattr(module, name)
        for module in gate_modules()
        for name in defined_names(module)
        if name.startswith("check_") and callable(getattr(module, name))
    }
    missing = sorted(check.__name__ for check in defined - set(registered))
    assert not missing, f"defined but never run by the gate: {missing}"


def test_the_patch_target_scan_finds_the_known_patches() -> None:
    # Guards the guard: if the regexes stop matching, the next test passes
    # vacuously over an empty list.
    names = {name for _file, _module, name in _patch_targets()}
    assert {"create_app", "make_server", "CHECKS", "run_checks"} <= names


@pytest.mark.parametrize(
    ("test_file", "module", "name"),
    _patch_targets(),
    ids=lambda value: str(value),
)
def test_each_patch_targets_the_module_that_reads_the_name(
    test_file: str, module: str, name: str
) -> None:
    expected = _module_for_test_file(Path(test_file))
    assert module == expected, (
        f"{test_file} patches {module}.{name}; tests patch only the module "
        f"they cover ({expected}). Move the test beside its subject."
    )
    owner = importlib.import_module(f"scripts.dev.{module}")
    assert name in names_read_in_functions(owner), (
        f"{test_file} patches {module}.{name}, but no function in {module} "
        f"reads {name}, so the patch reaches nothing."
    )


def test_the_gate_sets_provider_keys_before_config_reads_them() -> None:
    env = {
        key: value
        for key, value in os.environ.items()
        if key
        not in {
            "LASTFM_API_KEY",
            "SPOTIFY_CLIENT_ID",
            "SPOTIFY_CLIENT_SECRET",
            "SECRET_KEY",
            "DEBUG_MODE",
        }
    }
    code = (
        "import scripts.dev.frontend_gate\n"
        "from scrobblescope import config\n"
        "print('KEY=' + str(config.LASTFM_API_KEY))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    assert "KEY=frontend-gate-placeholder" in result.stdout
