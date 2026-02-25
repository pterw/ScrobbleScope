import os
import sys
from pathlib import Path

import pytest

# Make scripts/ importable so all docsync test files can do
# "from docsync import ..." without repeating sys.path manipulation.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

# Provide a safe SECRET_KEY for tests so the startup guard in create_app()
# does not raise. Must be set before app.py is imported.
os.environ.setdefault("SECRET_KEY", "test-only-secret-key-min-16chars!!")

from app import create_app  # noqa: E402

# ---------------------------------------------------------------------------
# Flask fixtures
# ---------------------------------------------------------------------------


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
Batch 11 is active.

## 4. Execution log

Some preamble text.

<!-- DOCSYNC:CURRENT-BATCH-START -->

### 2026-02-20 - First entry (Batch 11 WP-1)

Did some work.

<!-- DOCSYNC:CURRENT-BATCH-END -->
"""

MINIMAL_ARCHIVE = """\
# Execution Log Archive

Archived entries below.
"""

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
        tmp_path / "docs" / "history" / "logs" / "PLAYBOOK_EXECUTION_LOG_ARCHIVE.md",
    )
    monkeypatch.setattr(
        cli_module, "SESSION_CONTEXT_PATH", tmp_path / ".claude" / "SESSION_CONTEXT.md"
    )
    monkeypatch.setattr(cli_module, "LOGS_DIR", tmp_path / "docs" / "history" / "logs")

    (tmp_path / "docs" / "history").mkdir(parents=True)
    (tmp_path / "docs" / "history" / "logs").mkdir(parents=True)
    (tmp_path / ".claude").mkdir(parents=True)

    (tmp_path / "PLAYBOOK.md").write_text(MINIMAL_PLAYBOOK, encoding="utf-8")
    archive_path = (
        tmp_path / "docs" / "history" / "logs" / "PLAYBOOK_EXECUTION_LOG_ARCHIVE.md"
    )
    archive_path.write_text(MINIMAL_ARCHIVE, encoding="utf-8")
    session_path = tmp_path / ".claude" / "SESSION_CONTEXT.md"
    session_path.write_text(MINIMAL_SESSION_CONTEXT, encoding="utf-8")
    return tmp_path
