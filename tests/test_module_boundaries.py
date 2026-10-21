"""Module boundaries: no module reaches into another module's private names.

A name with a leading underscore belongs to its own module, or, for the
packages ``orchestrator`` and ``routes``, to its own package (their submodules
read the facade's names on purpose; see the ``orchestrator`` module docstring).
These tests walk the source with ``ast`` and fail on the first cross-boundary
read, so the next private name that gains a second caller is caught on the day
it does (architecture-walk-2, B-7).
"""

import ast
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "scrobblescope"
ROOT = SRC.parent


def _module_name(path):
    """The dotted module a source file defines (``__init__`` names its package)."""
    parts = list(path.relative_to(ROOT).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _unit(module):
    """The boundary a module sits in: its package, or itself for a lone file."""
    parts = module.split(".")
    return parts[1] if len(parts) > 1 else ""


def _is_private(name):
    return name.startswith("_") and not name.startswith("__")


def _private_reads():
    """Every private name one boundary reads from another, as readable strings."""
    found = []
    for path in sorted(SRC.rglob("*.py")):
        importer = _module_name(path)
        tree = ast.parse(path.read_text(encoding="utf-8"))
        aliases = {}
        for node in ast.walk(tree):
            if not (
                isinstance(node, ast.ImportFrom)
                and node.module
                and node.module.startswith("scrobblescope")
            ):
                continue
            for item in node.names:
                aliases[item.asname or item.name] = f"{node.module}.{item.name}"
                if _is_private(item.name) and _unit(node.module) != _unit(importer):
                    found.append(f"{importer}: from {node.module} import {item.name}")
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Attribute)
                and _is_private(node.attr)
                and isinstance(node.value, ast.Name)
            ):
                target = aliases.get(node.value.id)
                if target and _unit(target) != _unit(importer):
                    found.append(f"{importer}: {node.value.id}.{node.attr} ({target})")
    return found


def test_no_module_reads_another_modules_private_name():
    """
    GIVEN every module under scrobblescope/
    WHEN its imports and attribute reads are walked
    THEN none reads an underscore name from a module in another package.

    Planted defect: add ``from scrobblescope.utils import _GlobalThrottle`` to
    ``release_checks.py``; the test names it.
    """
    assert _private_reads() == []


def test_the_routes_never_import_the_correction_worker():
    """
    GIVEN the route modules
    WHEN their imports are read
    THEN none imports ``release_checks``: the routes read its vocabulary from
    ``release_status`` and the job's stats, and never start or touch the
    worker thread.

    Every import form counts. Planted defects, each added to ``routes/api.py``:
    ``from scrobblescope.release_checks import enqueue_release_check``,
    ``from scrobblescope import release_checks``, and
    ``import scrobblescope.release_checks``.
    """
    module = "scrobblescope.release_checks"
    offenders = []
    for path in sorted((SRC / "routes").glob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.ImportFrom):
                names = {f"{node.module}.{alias.name}" for alias in node.names}
                if node.module == module or module in names:
                    offenders.append(path.name)
            elif isinstance(node, ast.Import):
                if any(alias.name == module for alias in node.names):
                    offenders.append(path.name)
    assert offenders == []


def test_release_status_strings_are_the_ones_the_browser_compares():
    """
    GIVEN the release-check vocabulary
    WHEN the Results page's script and the worker are compared with it
    THEN the strings the script tests for are exactly the module's values, and
    the other four are pinned here, because they travel in JSON a page reads.

    Planted defect: change ``CHECK_MOVED_OUT`` to ``"moved-out"``.
    """
    from scrobblescope import release_status

    script = (ROOT / "static/js/results-release-checks.js").read_text(encoding="utf-8")
    for value in (
        release_status.CHECK_CONFIRMED,
        release_status.CHECK_MOVED_OUT,
        release_status.STATUS_PENDING,
        release_status.STATUS_RUNNING,
    ):
        assert f"'{value}'" in script
    assert (
        release_status.CHECK_UNCHECKED,
        release_status.CHECK_CONFIRMED,
        release_status.CHECK_MOVED_OUT,
        release_status.CHECK_UNAVAILABLE,
    ) == ("unchecked", "confirmed", "moved_out", "unavailable")
    assert (
        release_status.STATUS_PENDING,
        release_status.STATUS_RUNNING,
        release_status.STATUS_DONE,
        release_status.STATUS_SKIPPED,
    ) == ("pending", "running", "done", "skipped")


PAGE_LAYER = {"fetch_recent_tracks_page_async", "fetch_all_recent_tracks_async"}


def test_nothing_outside_lastfm_reads_the_page_layer():
    """
    GIVEN every module under scrobblescope/ except lastfm.py
    WHEN its imports and attribute reads are walked
    THEN none names the Last.fm page functions: callers get plays from
    ``lastfm.fetch_scrobbles`` and raw pages never leave the module.

    Planted defect: add ``from scrobblescope.lastfm import
    fetch_all_recent_tracks_async`` to ``heatmap.py``.
    """
    offenders = []
    for path in sorted(SRC.rglob("*.py")):
        module = _module_name(path)
        if module == "scrobblescope.lastfm":
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.ImportFrom) and node.module == (
                "scrobblescope.lastfm"
            ):
                offenders += [
                    f"{module}: imports {item.name}"
                    for item in node.names
                    if item.name in PAGE_LAYER
                ]
            if isinstance(node, ast.Attribute) and node.attr in PAGE_LAYER:
                offenders.append(f"{module}: reads .{node.attr}")
    assert offenders == []


METADATA_CACHE_FUNCTIONS = frozenset(
    {"batch_lookup_metadata", "batch_persist_metadata", "cleanup_stale_metadata"}
)


def test_only_the_cache_module_reads_or_writes_the_metadata_table():
    """
    GIVEN every module under scrobblescope/
    WHEN its imports, attribute reads and string constants are walked
    THEN no module but cache.py names the metadata table's read, write or
    cleanup functions, and exactly one module holds an INSERT into it.

    The shared table's contract (no listening facts) is held by one write
    path: ``AlbumCache.persist`` taking ``AlbumMetadata``. A second writer
    would be a second place to inspect.

    Planted defect: add ``from scrobblescope.cache import batch_persist_metadata``
    to ``release_checks.py``; the test names it.
    """
    offenders = []
    writers = []
    for path in sorted(SRC.rglob("*.py")):
        module = _module_name(path)
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if module != "scrobblescope.cache":
                if (
                    isinstance(node, ast.ImportFrom)
                    and node.module == "scrobblescope.cache"
                ):
                    offenders += [
                        f"{module} imports {item.name}"
                        for item in node.names
                        if item.name in METADATA_CACHE_FUNCTIONS
                    ]
                if (
                    isinstance(node, ast.Attribute)
                    and node.attr in METADATA_CACHE_FUNCTIONS
                ):
                    offenders.append(f"{module} reads .{node.attr}")
            if (
                isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and "INSERT INTO spotify_cache" in node.value
            ):
                writers.append(module)
    assert offenders == []
    assert writers == ["scrobblescope.cache"]
