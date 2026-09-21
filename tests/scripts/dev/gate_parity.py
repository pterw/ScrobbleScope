"""Source-level facts about the frontend gate modules, for split parity tests.

F-B21-51 splits `scripts/dev/frontend_gate.py` into `_frontend_gate_*`
siblings. A move that forgets a name, or a test patch left aimed at a module
that no longer reads the name, both pass on the happy path. These helpers read
the modules' source so the parity tests can assert what each module *defines*
and *reads*, rather than what it happens to import.
"""

from __future__ import annotations

import ast
import importlib
import inspect
from pathlib import Path
from types import ModuleType

GATE_DIR = Path(__file__).resolve().parents[3] / "scripts" / "dev"


def _tree(module: ModuleType) -> ast.Module:
    """Parse the module's own source file."""
    return ast.parse(Path(inspect.getfile(module)).read_text(encoding="utf-8"))


def defined_names(module: ModuleType) -> set[str]:
    """Top-level names the module defines itself; imported names excluded."""
    names: set[str] = set()
    for node in _tree(module).body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            names.update(t.id for t in node.targets if isinstance(t, ast.Name))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
    return names


def names_read_in_functions(module: ModuleType) -> set[str]:
    """Every bare name the module's functions look up when they run.

    This is exactly the set a `patch("<module>.<name>")` can affect: a name
    read at call time through the module's globals.
    """
    names: set[str] = set()
    for node in ast.walk(_tree(module)):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for inner in ast.walk(node):
                if isinstance(inner, ast.Name) and isinstance(inner.ctx, ast.Load):
                    names.add(inner.id)
    return names


def gate_modules() -> list[ModuleType]:
    """The facade plus every `_frontend_gate_*` sibling, imported."""
    stems = ["frontend_gate"] + sorted(
        path.stem for path in GATE_DIR.glob("_frontend_gate_*.py")
    )
    return [importlib.import_module(f"scripts.dev.{stem}") for stem in stems]
