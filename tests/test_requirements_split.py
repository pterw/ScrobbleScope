"""The production image installs requirements.txt and nothing else.

The Dockerfile runs ``pip install -r requirements.txt``. Any third-party
module the running app imports must therefore come from a distribution that
file pins; a module only requirements-dev.txt provides would import fine in
development and CI, then fail on Fly.io at startup.
"""

from __future__ import annotations

import ast
import re
import sys
from importlib.metadata import packages_distributions
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

#: What runs in the production image: the package plus the three entry
#: points the Dockerfile and fly.toml invoke.
RUNTIME_FILES = [
    ROOT / "app.py",
    ROOT / "run.py",
    ROOT / "init_db.py",
    *sorted((ROOT / "scrobblescope").rglob("*.py")),
]

FIRST_PARTY = {"scrobblescope", "app", "run", "init_db"}


def _pinned(requirements: Path) -> set[str]:
    """Return the normalised distribution names a requirements file pins."""
    names = set()
    for raw in requirements.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or line.startswith("-"):
            continue
        name = re.split(r"[=<>!~\[; ]", line, maxsplit=1)[0]
        names.add(name.lower().replace("_", "-"))
    return names


def _third_party_imports(path: Path) -> set[str]:
    """Return the top-level third-party module names a file imports."""
    modules = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            modules.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            modules.add(node.module.split(".")[0])
    return {
        m for m in modules if m not in sys.stdlib_module_names and m not in FIRST_PARTY
    }


def test_runtime_code_imports_only_what_requirements_txt_installs():
    """Every third-party import in runtime code resolves to a production pin."""
    production = _pinned(ROOT / "requirements.txt")
    distributions = packages_distributions()
    unpinned = []
    for path in RUNTIME_FILES:
        for module in sorted(_third_party_imports(path)):
            owners = {
                d.lower().replace("_", "-") for d in distributions.get(module, [])
            }
            if not owners & production:
                unpinned.append(f"{path.relative_to(ROOT)} imports {module}")

    assert not unpinned, (
        f"runtime code imports modules requirements.txt does not install: {unpinned}"
    )
