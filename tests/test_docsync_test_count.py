"""The authoritative test count must not depend on log-retention settings."""

import pytest
from docsync.logic import _sync
from docsync.renderer import SIDE_ARCHIVE_PREFIX

ARCHIVE = "\n".join(SIDE_ARCHIVE_PREFIX) + "\n"
SESSION = (
    "# SESSION_CONTEXT\n\n"
    "| Tests | **521 passing** |\n\n"
    "<!-- DOCSYNC:STATUS-START -->\n- placeholder\n<!-- DOCSYNC:STATUS-END -->\n"
)


def _playbook(side_entries: str = "") -> list[str]:
    """Build a PLAYBOOK whose newest full-suite count is a side-task entry."""
    return (
        "# PLAYBOOK\n\n"
        "## 3. Active batch\n\n"
        "Batch 21 is active. Definition: `BATCH21_DEFINITION.md`.\n\n"
        "## 4. Execution log\n\n"
        "<!-- DOCSYNC:CURRENT-BATCH-START -->\n\n"
        "### 2026-07-24 - Batch opened (Batch 21 WP-0)\n\n"
        "- Validation: `pytest -q` -- **390 passed**.\n\n"
        "<!-- DOCSYNC:CURRENT-BATCH-END -->\n\n"
        f"{side_entries}"
    ).splitlines()


NEWEST_SIDE_ENTRY = (
    "### 2026-08-05 - Later side task\n\n"
    "- Validation: `pytest -q` -- **521 passed**.\n"
)


def _status(result) -> str:
    """Return the rendered managed status block as one string."""
    return "\n".join(result.session_lines)


@pytest.mark.parametrize(
    "keep_non_current", [4, 1, 0], ids=("keep-4", "keep-1", "purge")
)
def test_close_out_rotation_preserves_the_authoritative_count(keep_non_current):
    """--keep-non-current is a retention knob, not the source of a repo fact."""
    result = _sync(
        _playbook(NEWEST_SIDE_ENTRY),
        ARCHIVE.splitlines(),
        SESSION.splitlines(),
        keep_non_current,
    )
    assert "**521 passed**" in _status(result)
    assert "**390 passed**" not in _status(result)


def test_count_survives_once_the_entry_has_been_rotated_out():
    """After rotation the fact lives in the archive, so it must be read there."""
    rotated_archive = (
        "\n".join(SIDE_ARCHIVE_PREFIX)
        + "\n\n### 2026-08-05 - Later side task\n\n"
        + "- Validation: `pytest -q` -- **521 passed**.\n"
    )
    result = _sync(_playbook(), rotated_archive.splitlines(), SESSION.splitlines(), 0)
    assert "**521 passed**" in _status(result)


def test_ambiguous_newest_entry_does_not_republish_an_older_count():
    """Several bold counts without `pytest -q` must not revive a stale number."""
    ambiguous = (
        "### 2026-08-06 - Ambiguous entry\n\n"
        "- Validation: focused suite **12 passed**; full suite **530 passed**.\n\n"
        "### 2026-08-05 - Later side task\n\n"
        "- Validation: `pytest -q` -- **521 passed**.\n"
    )
    result = _sync(_playbook(ambiguous), ARCHIVE.splitlines(), SESSION.splitlines(), 4)
    assert "**521 passed**" not in _status(result)


def test_documented_close_out_command_stays_self_consistent():
    """The batch close-out command must not contradict SESSION_CONTEXT."""
    purged = _sync(
        _playbook(NEWEST_SIDE_ENTRY), ARCHIVE.splitlines(), SESSION.splitlines(), 0
    )
    kept = _sync(
        _playbook(NEWEST_SIDE_ENTRY), ARCHIVE.splitlines(), SESSION.splitlines(), 4
    )
    assert purged.rotated_count == 1
    assert _status(purged) == _status(kept)
