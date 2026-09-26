"""The authoritative test count must not depend on log-retention settings."""

import re

import pytest
from docsync.logic import (
    _sync,
    latest_test_count_authority,
    resolved_test_count_authority,
)
from docsync.models import TestCountAuthority as CountAuthority
from docsync.renderer import SIDE_ARCHIVE_PREFIX, rewrite_recorded_counts

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
    "### 2026-08-05 - Later side task\n\n- Validation: `pytest -q` -- **521 passed**.\n"
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
    """Several bold counts without `pytest -q` must not revive a stale number.

    Asserting the rendered unknown state rather than the absence of one literal:
    an earlier version of this test only checked that 521 was gone, and passed
    while the block published 390 from the current-batch entry.
    """
    ambiguous = (
        "### 2026-08-06 - Ambiguous entry\n\n"
        "- Validation: focused suite **12 passed**; full suite **530 passed**.\n\n"
        "### 2026-08-05 - Later side task\n\n"
        "- Validation: `pytest -q` -- **521 passed**.\n"
    )
    result = _sync(_playbook(ambiguous), ARCHIVE.splitlines(), SESSION.splitlines(), 4)
    status = _status(result)
    assert "Latest validated test count: unknown" in status
    for revived in ("**521 passed**", "**390 passed**", "**530 passed**"):
        assert revived not in status


def test_live_side_entry_outranks_a_same_date_archived_entry():
    """Retention splitting one date across both files must not pick the larger.

    The live side-task entry is newer by construction, so source precedence --
    not the numeric value -- has to break the tie.
    """
    same_date_archive = (
        "\n".join(SIDE_ARCHIVE_PREFIX)
        + "\n\n### 2026-08-05 - Earlier side task\n\n"
        + "- Validation: `pytest -q` -- **999 passed**.\n"
    )
    live = (
        "### 2026-08-05 - Later side task\n\n"
        "- Validation: `pytest -q` -- **100 passed**.\n"
    )
    result = _sync(
        _playbook(live), same_date_archive.splitlines(), SESSION.splitlines(), 4
    )
    assert "**100 passed**" in _status(result)
    assert "**999 passed**" not in _status(result)


def test_legacy_sole_bold_count_resolves_after_rotation():
    """A pre-`pytest -q` entry stays authoritative once retention archives it.

    The legacy fallback walks the same ordering as the strict pass, so the
    archive is in scope for both.
    """
    legacy_archive = (
        "\n".join(SIDE_ARCHIVE_PREFIX)
        + "\n\n### 2026-08-05 - Legacy side task\n\n"
        + "- Validation: **477 tests passing**.\n"
    )
    playbook = (
        "# PLAYBOOK\n\n"
        "## 3. Active batch\n\n"
        "Batch 21 is active. Definition: `BATCH21_DEFINITION.md`.\n\n"
        "## 4. Execution log\n\n"
        "<!-- DOCSYNC:CURRENT-BATCH-START -->\n\n"
        "### 2026-07-24 - Batch opened (Batch 21 WP-0)\n\n"
        "- Scope: no validation line, so no count is recorded here.\n\n"
        "<!-- DOCSYNC:CURRENT-BATCH-END -->\n\n"
    ).splitlines()
    result = _sync(playbook, legacy_archive.splitlines(), SESSION.splitlines(), 4)
    assert "**477 passed**" in _status(result)


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


def test_same_date_batch_logs_prefer_the_later_batch():
    """Batch chronology breaks a date tie across separate archived logs."""

    def batch_log(batch: int, count: int) -> list[str]:
        return (
            f"# Batch {batch} Execution Log\n\n"
            f"### 2026-08-05 - Batch {batch} done (Batch {batch} WP-1)\n\n"
            f"- Validation: `pytest -q` -- **{count} passed**.\n"
        ).splitlines()

    authority = latest_test_count_authority(
        _playbook(),
        ARCHIVE.splitlines(),
        {20: batch_log(20, 600), 21: batch_log(21, 700)},
    )

    assert authority.count == 700
    assert authority.ambiguous is False


# ---------------------------------------------------------------------------
# TestLatestTestCount -- latest_test_count_authority (moved from
# tests/test_docsync_logic.py, F-DOCSYNC-7/F-MAS-3)
# ---------------------------------------------------------------------------


class TestLatestTestCount:
    def _minimal_playbook(self, entry_body_lines: list[str]) -> list[str]:
        """Wrap entry_body_lines inside a minimal PLAYBOOK with Section 4 markers."""
        return [
            "# PLAYBOOK",
            "",
            "## 3. Active batch",
            "",
            "Batch 11 is active.",
            "",
            "## 4. Execution log",
            "",
            "<!-- DOCSYNC:CURRENT-BATCH-START -->",
            "",
            "### 2026-02-20 - Work (Batch 11 WP-1)",
            "",
            *entry_body_lines,
            "",
            "<!-- DOCSYNC:CURRENT-BATCH-END -->",
        ]

    def test_no_markers_returns_none(self):
        """Flat playbook with no Section 4 markers returns None."""
        playbook = ["# PLAYBOOK", "", "## 4. Execution log", "", "Some content."]
        assert latest_test_count_authority(playbook).count is None

    def test_entry_with_count_returns_count(self):
        """Bold test count in a current-batch entry body is extracted."""
        playbook = self._minimal_playbook(["Validated: **142 passed**"])
        assert latest_test_count_authority(playbook).count == 142

    def test_entry_without_count_returns_none(self):
        """Entry with no bold count produces None."""
        playbook = self._minimal_playbook(["No count here."])
        assert latest_test_count_authority(playbook).count is None

    def test_multiple_entries_uses_newest(self):
        """With two entries inside markers, the newest (last appended) entry's count is used."""
        playbook = [
            "# PLAYBOOK",
            "",
            "## 3. Active batch",
            "",
            "Batch 11 is active.",
            "",
            "## 4. Execution log",
            "",
            "<!-- DOCSYNC:CURRENT-BATCH-START -->",
            "",
            "### 2026-02-20 - Older work (Batch 11 WP-1)",
            "",
            "**190 tests passing**",
            "",
            "### 2026-02-21 - Newer work (Batch 11 WP-2)",
            "",
            "**200 tests passing**",
            "",
            "<!-- DOCSYNC:CURRENT-BATCH-END -->",
        ]
        # latest_test_count_authority scans in reverse to find newest.
        result = latest_test_count_authority(playbook).count
        assert result == 200

    def test_newest_first_file_order_still_returns_last(self):
        """When entries are in reverse chronological file order, the last
        entry in the file is still treated as newest (append convention)."""
        playbook = [
            "# PLAYBOOK",
            "",
            "## 3. Active batch",
            "",
            "Batch 11 is active.",
            "",
            "## 4. Execution log",
            "",
            "<!-- DOCSYNC:CURRENT-BATCH-START -->",
            "",
            "### 2026-02-21 - Newer work (Batch 11 WP-2)",
            "",
            "**200 tests passing**",
            "",
            "### 2026-02-20 - Older work (Batch 11 WP-1)",
            "",
            "**190 tests passing**",
            "",
            "<!-- DOCSYNC:CURRENT-BATCH-END -->",
        ]
        assert latest_test_count_authority(playbook).count == 190

    def test_newest_side_task_full_suite_count_is_authoritative(self):
        """The top side-task full-suite result supersedes the Batch WP baseline."""
        playbook = self._minimal_playbook(["`pytest -q` -- **390 passed**."])
        playbook.extend(
            [
                "",
                "### 2026-08-05 - Review remediation (side-task)",
                "",
                "Focused docsync suite -- **112 passed**. `pytest -q` --",
                "**420 passed**.",
            ]
        )

        assert latest_test_count_authority(playbook).count == 420

    def test_focused_side_task_does_not_override_full_suite_count(self):
        """A focused-only result cannot become the repository test authority."""
        playbook = self._minimal_playbook(["`pytest -q` -- **390 passed**."])
        playbook.extend(
            [
                "",
                "### 2026-08-06 - Focused follow-up (side-task)",
                "",
                "Validation: focused docsync suite -- **112 passed**.",
                "",
                "### 2026-08-05 - Full validation (side-task)",
                "",
                "Validation: `pytest -q` -- **420 passed**.",
            ]
        )

        assert latest_test_count_authority(playbook).count == 420


# ---------------------------------------------------------------------------
# Unbold full-suite results must not publish a stale authority (moved from
# tests/test_docsync_logic.py)
# ---------------------------------------------------------------------------


def test_unbold_full_suite_does_not_publish_focused_or_older_authority():
    lines = [
        "## 4. Execution log",
        "<!-- DOCSYNC:CURRENT-BATCH-START -->",
        "<!-- DOCSYNC:CURRENT-BATCH-END -->",
        "### 2026-09-15 - Newest",
        "Focused: **12 passed**.",
        "Validation: `pytest -q` -- 1154 passed.",
        "### 2026-09-14 - Older",
        "Validation: `pytest -q` -- **1153 passed**.",
    ]
    result = latest_test_count_authority(lines)
    assert result.count is None
    assert result.ambiguous


def test_wrapped_unbold_full_suite_suppresses_focused_and_older_authority():
    lines = [
        "## 4. Execution log",
        "<!-- DOCSYNC:CURRENT-BATCH-START -->",
        "<!-- DOCSYNC:CURRENT-BATCH-END -->",
        "### 2026-09-15 - Newest",
        "Focused: **12 passed**.",
        "Validation: `pytest -q` --",
        "1154 passed.",
        "### 2026-09-14 - Older",
        "Validation: `pytest -q` -- **1153 passed**.",
    ]
    result = latest_test_count_authority(lines)
    assert result.count is None
    assert result.ambiguous


# ---------------------------------------------------------------------------
# rewrite_recorded_counts -- Task 1, F-DOCSYNC-12 (moved from
# tests/test_docsync_logic.py)
# ---------------------------------------------------------------------------


class TestRewriteRecordedCounts:
    def test_replaces_only_the_digits_in_a_matching_line(self):
        lines = ["| Tests | **1849 passing** across 68 tracked test modules |"]
        pattern = re.compile(
            r"^\|\s*Tests\s*\|\s*\*\*(\d+)\s+(?:tests?\s+)?pass(?:ing|ed)\*\*"
        )
        assert rewrite_recorded_counts(lines, 1850, [pattern]) == [
            "| Tests | **1850 passing** across 68 tracked test modules |"
        ]

    def test_leaves_a_non_matching_line_untouched(self):
        pattern = re.compile(r"^## 6\.")
        assert rewrite_recorded_counts(["some other line"], 5, [pattern]) == [
            "some other line"
        ]

    def test_first_matching_pattern_wins(self):
        lines = ["## 6. Test structure (1849 tests)"]
        heading = re.compile(r"^##\s+\d+\.\s+Test structure\s+\((\d+)\s+tests\)\s*$")
        decoy = re.compile(r"nomatch")
        assert rewrite_recorded_counts(lines, 1900, [decoy, heading]) == [
            "## 6. Test structure (1900 tests)"
        ]


# ---------------------------------------------------------------------------
# resolved_test_count_authority -- Task 1, F-DOCSYNC-11/-22 (moved from
# tests/test_docsync_logic.py)
# ---------------------------------------------------------------------------


def _authority_playbook(active_line: str, body: str) -> list[str]:
    # Named distinctly from this module's own _playbook() (side-entry helper
    # above): both moved into this file and would otherwise collide.
    lines = [
        "# PLAYBOOK",
        "",
        "## 3. Active batch",
        "",
        active_line,
        "",
        "## 4. Execution log",
        "",
        "<!-- DOCSYNC:CURRENT-BATCH-START -->",
        "",
    ]
    lines.extend(body.splitlines())
    if "<!-- DOCSYNC:CURRENT-BATCH-END -->" not in body:
        lines.append("")
        lines.append("<!-- DOCSYNC:CURRENT-BATCH-END -->")
    return lines


def _playbook_with_entry(bold_count: str) -> list[str]:
    return _authority_playbook(
        "- **Batch 1 is active.**",
        f"### 2026-09-20 - one entry\n\nBody.\n\n`pytest -q` -- {bold_count}\n",
    )


def _playbook_two_same_date_entries(older: str, newer: str) -> list[str]:
    # "newer" sits below the end marker (a live side-task entry, the
    # highest-precedence source on a same-date tie) and "older" sits inside
    # the current-batch window -- so an unpinned, prose-only scan picks
    # "newer", not "older", on this same date. Naming still follows
    # F-DOCSYNC-22: "older" is the entry an author corrected after the fact,
    # and only a pin -- not a reordering of same-date prose -- can make the
    # correction stick.
    return _authority_playbook(
        "- **Batch 1 is active.**",
        f"### 2026-09-20 - current-batch entry\n\nBody.\n\n`pytest -q` -- **{older}**\n"
        f"<!-- DOCSYNC:CURRENT-BATCH-END -->\n\n"
        f"### 2026-09-20 - side task\n\nBody.\n\n`pytest -q` -- **{newer}**\n",
    )


class TestResolvedTestCountAuthority:
    def test_explicit_count_always_wins(self):
        playbook = _playbook_with_entry("**999 passed**")
        result = resolved_test_count_authority(
            playbook, pinned=1, explicit_test_count=1850
        )
        assert result == CountAuthority(count=1850, ambiguous=False)

    def test_a_pinned_count_outranks_fresh_prose(self):
        """F-DOCSYNC-22: an entry corrected out of position must not shadow
        a value already pinned in config/docsync.toml."""
        # Two same-date entries, the classic F-DOCSYNC-11/-22 tie: the
        # position-based scan alone would pick 1849, not 1850.
        playbook = _playbook_two_same_date_entries(
            older="1850 passed", newer="1849 passed"
        )
        result = resolved_test_count_authority(playbook, pinned=1850)
        assert result == CountAuthority(count=1850, ambiguous=False)

    def test_falls_back_to_prose_when_nothing_is_pinned_yet(self):
        """Cold start: no [test_count] table still resolves from the
        entries, exactly as latest_test_count_authority always has."""
        playbook = _playbook_with_entry("**142 passed**")
        result = resolved_test_count_authority(playbook, pinned=None)
        assert result == CountAuthority(count=142, ambiguous=False)
