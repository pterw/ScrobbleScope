import os
import sys
import threading
from pathlib import Path

import pytest

# Make scripts/ importable so all docsync test files can do
# "from docsync import ..." without repeating sys.path manipulation.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

# Provide a safe SECRET_KEY for tests so the startup guard in create_app()
# does not raise. Must be set before app.py is imported.
# Not setdefault: CI sets SECRET_KEY to an empty string when the repository
# secret is missing, and empty is present but still weak.
if not os.environ.get("SECRET_KEY"):
    os.environ["SECRET_KEY"] = "test-only-secret-key-min-16chars!!"

from docsync.renderer import SIDE_ARCHIVE_PREFIX  # noqa: E402

from app import create_app  # noqa: E402

# ---------------------------------------------------------------------------
# Flask fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def fresh_job_slots():
    """Give every test a fresh job-slot semaphore.

    Route tests that mock start_job_thread acquire a real slot that is
    never released (the release lives in the background task's finally
    block), so leaked slots accumulate across the test session. With the
    old MAX_ACTIVE_JOBS default of 10 the leaks never crossed the
    threshold; the drop to 5 exposed the hidden ordering coupling (a late
    /heatmap_loading test drew a real 429). Resetting per test removes
    the inter-test coupling instead of relying on the cap exceeding the
    session's leak count.
    """
    from scrobblescope import config, worker

    original = worker._active_jobs_semaphore
    worker._active_jobs_semaphore = threading.BoundedSemaphore(config.MAX_ACTIVE_JOBS)
    yield
    worker._active_jobs_semaphore = original


@pytest.fixture
def client():
    """Create a test client for the Flask application."""
    application = create_app()
    application.config["TESTING"] = True
    application.config["WTF_CSRF_ENABLED"] = False
    with application.test_client() as client:
        yield client


@pytest.fixture
def csrf_app_client():
    """Test client with CSRF protection active (WTF_CSRF_ENABLED not disabled).

    Use this fixture for tests that verify CSRF enforcement behaviour.
    The default ``client`` fixture disables CSRF for convenience; this one
    does not, so token validation runs as it would in production.
    """
    application = create_app()
    application.config["TESTING"] = True
    with application.test_client() as csrf_client:
        yield csrf_client


# ---------------------------------------------------------------------------
# docsync shared fixtures and constants
# ---------------------------------------------------------------------------

MINIMAL_PLAYBOOK = """\
# PLAYBOOK

## 3. Active batch

Batch 10 is complete.
Batch 11 is active. Definition: `BATCH11_DEFINITION.md`.

## 4. Execution log

Some preamble text.

<!-- DOCSYNC:CURRENT-BATCH-START -->

### 2026-02-20 - First entry (Batch 11 WP-1)

Did some work.

<!-- DOCSYNC:CURRENT-BATCH-END -->
"""

MINIMAL_ARCHIVE = "\n".join(SIDE_ARCHIVE_PREFIX) + "\n"

MINIMAL_SESSION_CONTEXT = """\
# SESSION_CONTEXT

Some status info.

<!-- DOCSYNC:STATUS-START -->
- placeholder
<!-- DOCSYNC:STATUS-END -->

More content.
"""


@pytest.fixture
def sync_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Set up minimal filesystem structure for docsync tests.

    Creates PLAYBOOK.md, the archive, and SESSION_CONTEXT.md in tmp_path,
    chdir's into tmp_path, and patches docsync.cli path constants so that
    cli.main() uses the tmp files instead of the repo files.
    """
    import docsync.cli as cli_module

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli_module, "PLAYBOOK_PATH", tmp_path / "PLAYBOOK.md")
    monkeypatch.setattr(
        cli_module,
        "ARCHIVE_PATH",
        tmp_path / "docs" / "logarchive" / "PLAYBOOK_EXECUTION_LOG_ARCHIVE.md",
    )
    monkeypatch.setattr(
        cli_module, "SESSION_CONTEXT_PATH", tmp_path / ".claude" / "SESSION_CONTEXT.md"
    )
    monkeypatch.setattr(cli_module, "LOGS_DIR", tmp_path / "docs" / "history" / "logs")

    (tmp_path / "docs" / "history").mkdir(parents=True)
    (tmp_path / "docs" / "history" / "logs").mkdir(parents=True)
    (tmp_path / "docs" / "logarchive").mkdir(parents=True)
    (tmp_path / ".claude").mkdir(parents=True)

    (tmp_path / "PLAYBOOK.md").write_text(MINIMAL_PLAYBOOK, encoding="utf-8")
    archive_path = (
        tmp_path / "docs" / "logarchive" / "PLAYBOOK_EXECUTION_LOG_ARCHIVE.md"
    )
    archive_path.write_text(MINIMAL_ARCHIVE, encoding="utf-8")
    session_path = tmp_path / ".claude" / "SESSION_CONTEXT.md"
    session_path.write_text(MINIMAL_SESSION_CONTEXT, encoding="utf-8")

    (tmp_path / "BATCH11_DEFINITION.md").write_text(
        "# BATCH11\n\n**Branch:** `wip/batch-11`.\n", encoding="utf-8"
    )
    (tmp_path / "AGENTS.md").write_text("See `FINDINGS.md`.\n", encoding="utf-8")
    (tmp_path / "HANDOFF_PROMPT.md").write_text("Read `AGENTS.md`.\n", encoding="utf-8")
    (tmp_path / "AGENT_NOTES.md").write_text(
        "Rules live in `AGENTS.md`.\n", encoding="utf-8"
    )
    (tmp_path / "FINDINGS.md").write_text("# Findings\n", encoding="utf-8")
    tracked_paths = frozenset(
        path.relative_to(tmp_path).as_posix()
        for path in tmp_path.rglob("*")
        if path.is_file()
    )
    monkeypatch.setattr(cli_module, "collect_tracked_paths", lambda _: tracked_paths)
    return tmp_path
