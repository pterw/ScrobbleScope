"""Tests for scripts/doc_state_sync.py -- focused on non-happy-path behaviour.

These tests exercise edge cases, error conditions, and adversarial inputs
to ensure the deterministic sync tool fails safely and handles boundary
conditions correctly. All filesystem interactions are isolated via tmp_path.
"""

from __future__ import annotations

import sys
from pathlib import Path
from textwrap import dedent

import pytest

# Make the scripts package importable.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import doc_state_sync as dss

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _lines(text: str) -> list[str]:
    """Dedent a triple-quoted block and split into lines (no trailing newline)."""
    return dedent(text).strip().splitlines()


# Minimal valid PLAYBOOK content for integration tests.
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


# ---------------------------------------------------------------------------
# _read_lines -- missing file
# ---------------------------------------------------------------------------


class TestReadLines:
    def test_missing_file_raises_sync_error(self, tmp_path: Path):
        with pytest.raises(dss.SyncError, match="Required file is missing"):
            dss._read_lines(tmp_path / "nonexistent.md")


# ---------------------------------------------------------------------------
# _find_section -- heading not found
# ---------------------------------------------------------------------------


class TestFindSection:
    def test_missing_heading_raises_sync_error(self):
        lines = ["# Title", "", "Some text"]
        with pytest.raises(dss.SyncError, match="Could not find section heading"):
            dss._find_section(lines, dss.SECTION_3_RE, "test section")

    def test_section_at_end_of_file(self):
        lines = ["# Title", "", "## 3. Active batch", "", "Content here"]
        start, end = dss._find_section(lines, dss.SECTION_3_RE, "test section")
        assert start == 2
        assert end == len(lines)  # extends to end when no next ##

    def test_section_bounded_by_next_heading(self):
        lines = [
            "## 3. Active batch",
            "Content",
            "## 4. Execution log",
            "More content",
        ]
        start, end = dss._find_section(lines, dss.SECTION_3_RE, "test section")
        assert start == 0
        assert end == 2  # stops at ## 4


# ---------------------------------------------------------------------------
# _find_marker_pair -- missing or inverted markers
# ---------------------------------------------------------------------------


class TestFindMarkerPair:
    def test_missing_start_marker(self):
        lines = ["some text", dss.CURRENT_BATCH_END_MARKER]
        with pytest.raises(dss.SyncError, match="must contain start marker"):
            dss._find_marker_pair(
                lines,
                dss.CURRENT_BATCH_START_MARKER,
                dss.CURRENT_BATCH_END_MARKER,
                "test",
            )

    def test_missing_end_marker(self):
        lines = [dss.CURRENT_BATCH_START_MARKER, "some text"]
        with pytest.raises(dss.SyncError, match="must contain start marker"):
            dss._find_marker_pair(
                lines,
                dss.CURRENT_BATCH_START_MARKER,
                dss.CURRENT_BATCH_END_MARKER,
                "test",
            )

    def test_inverted_markers(self):
        lines = [
            dss.CURRENT_BATCH_END_MARKER,
            "content",
            dss.CURRENT_BATCH_START_MARKER,
        ]
        with pytest.raises(dss.SyncError, match="marker order is invalid"):
            dss._find_marker_pair(
                lines,
                dss.CURRENT_BATCH_START_MARKER,
                dss.CURRENT_BATCH_END_MARKER,
                "test",
            )

    def test_same_line_markers_raises(self):
        """Start and end on same index (only end marker present once) -- edge case."""
        # If only one marker string matches both patterns, start >= end.
        lines = ["other", dss.CURRENT_BATCH_START_MARKER]
        with pytest.raises(dss.SyncError, match="must contain start marker"):
            dss._find_marker_pair(
                lines,
                dss.CURRENT_BATCH_START_MARKER,
                dss.CURRENT_BATCH_END_MARKER,
                "test",
            )


# ---------------------------------------------------------------------------
# _parse_entries -- edge cases
# ---------------------------------------------------------------------------


class TestParseEntries:
    def test_no_entries_returns_empty(self):
        lines = ["Some text", "No headings here", ""]
        entries, first_idx = dss._parse_entries(lines)
        assert entries == []
        assert first_idx is None

    def test_single_entry_with_trailing_blanks(self):
        lines = ["### 2026-01-01 - Test entry", "Content", "", "", ""]
        entries, first_idx = dss._parse_entries(lines)
        assert len(entries) == 1
        assert first_idx == 0
        # Trailing blanks should be stripped from the entry.
        assert entries[0].lines[-1].strip() != ""

    def test_entries_preserve_order(self):
        lines = [
            "### 2026-01-01 - First",
            "Content A",
            "### 2026-01-02 - Second",
            "Content B",
        ]
        entries, _ = dss._parse_entries(lines)
        assert len(entries) == 2
        assert entries[0].date == "2026-01-01"
        assert entries[1].date == "2026-01-02"

    def test_fingerprint_ignores_trailing_whitespace(self):
        lines_a = ["### 2026-01-01 - Entry", "Content   "]
        lines_b = ["### 2026-01-01 - Entry", "Content"]
        entries_a, _ = dss._parse_entries(lines_a)
        entries_b, _ = dss._parse_entries(lines_b)
        assert entries_a[0].fingerprint == entries_b[0].fingerprint


# ---------------------------------------------------------------------------
# _parse_active_batch_state -- boundary conditions
# ---------------------------------------------------------------------------


class TestParseActiveBatchState:
    def test_no_signals_returns_all_none(self):
        state = dss._parse_active_batch_state(["Nothing relevant here."])
        assert state.current_batch is None
        assert state.last_completed_batch is None
        assert state.next_undefined_batch is None

    def test_completed_only_infers_next(self):
        """When only completed batches exist and no 'not yet defined' guard,
        current_batch should be inferred as last_completed + 1."""
        state = dss._parse_active_batch_state(
            ["Batch 10 is complete.", "Working on next items."]
        )
        assert state.current_batch == 11
        assert state.last_completed_batch == 10

    def test_current_equals_undefined_clears_current(self):
        """If current_batch matches next_undefined, current should be None."""
        state = dss._parse_active_batch_state(
            [
                "Batch 10 is complete.",
                "Batch 11 is not yet defined.",
                "Next batch to execute: Batch 11.",
            ]
        )
        assert state.current_batch is None
        assert state.next_undefined_batch == 11

    def test_explicit_current_wins(self):
        state = dss._parse_active_batch_state(
            [
                "Batch 10 is complete.",
                "Batch 11 is active.",
            ]
        )
        assert state.current_batch == 11
        assert state.last_completed_batch == 10

    def test_multiple_completed_picks_max(self):
        state = dss._parse_active_batch_state(
            [
                "Batch 8 is complete.",
                "Batch 9 is complete.",
                "Batch 10 is complete.",
            ]
        )
        assert state.last_completed_batch == 10

    def test_undefined_without_completed(self):
        state = dss._parse_active_batch_state(["Batch 1 is not yet defined."])
        assert state.current_batch is None
        assert state.next_undefined_batch == 1
        assert state.last_completed_batch is None


# ---------------------------------------------------------------------------
# _extract_entry_batch / _collect_wp_numbers -- edge cases
# ---------------------------------------------------------------------------


class TestExtractEntryBatch:
    def test_no_batch_tag(self):
        entry = dss.Entry(
            heading="### 2026-01-01 - Side fix",
            date="2026-01-01",
            title="Side fix",
            lines=("### 2026-01-01 - Side fix",),
            start_idx=0,
            fingerprint="abc",
        )
        assert dss._extract_entry_batch(entry) is None

    def test_batch_tag_extracted(self):
        entry = dss.Entry(
            heading="### 2026-01-01 - Work (Batch 11 WP-1)",
            date="2026-01-01",
            title="Work (Batch 11 WP-1)",
            lines=("### 2026-01-01 - Work (Batch 11 WP-1)",),
            start_idx=0,
            fingerprint="abc",
        )
        assert dss._extract_entry_batch(entry) == 11


class TestCollectWpNumbers:
    def test_no_wp_tags(self):
        entry = dss.Entry(
            heading="### 2026-01-01 - Side fix",
            date="2026-01-01",
            title="Side fix",
            lines=("### 2026-01-01 - Side fix",),
            start_idx=0,
            fingerprint="abc",
        )
        assert dss._collect_wp_numbers([entry]) == []

    def test_multiple_wp_tags(self):
        e1 = dss.Entry(
            heading="### 2026-01-01 - WP-1 work (Batch 11 WP-1)",
            date="2026-01-01",
            title="WP-1 work (Batch 11 WP-1)",
            lines=("### 2026-01-01 - WP-1 work (Batch 11 WP-1)",),
            start_idx=0,
            fingerprint="a",
        )
        e2 = dss.Entry(
            heading="### 2026-01-02 - WP-3 work (Batch 11 WP-3)",
            date="2026-01-02",
            title="WP-3 work (Batch 11 WP-3)",
            lines=("### 2026-01-02 - WP-3 work (Batch 11 WP-3)",),
            start_idx=0,
            fingerprint="b",
        )
        assert dss._collect_wp_numbers([e1, e2]) == [1, 3]


# ---------------------------------------------------------------------------
# _trim_trailing_blank -- edge cases
# ---------------------------------------------------------------------------


class TestTrimTrailingBlank:
    def test_empty_list(self):
        assert dss._trim_trailing_blank([]) == []

    def test_all_blank_lines(self):
        assert dss._trim_trailing_blank(["", "  ", "   "]) == []

    def test_preserves_internal_blanks(self):
        result = dss._trim_trailing_blank(["a", "", "b", ""])
        assert result == ["a", "", "b"]


# ---------------------------------------------------------------------------
# _remove_marker_lines
# ---------------------------------------------------------------------------


class TestRemoveMarkerLines:
    def test_removes_both_markers(self):
        lines = [
            "before",
            dss.CURRENT_BATCH_START_MARKER,
            "content",
            dss.CURRENT_BATCH_END_MARKER,
            "after",
        ]
        result = dss._remove_marker_lines(lines)
        assert dss.CURRENT_BATCH_START_MARKER not in result
        assert dss.CURRENT_BATCH_END_MARKER not in result
        assert result == ["before", "content", "after"]

    def test_no_markers_unchanged(self):
        lines = ["a", "b", "c"]
        assert dss._remove_marker_lines(lines) == lines


# ---------------------------------------------------------------------------
# _normalize_block / _fingerprint -- whitespace handling
# ---------------------------------------------------------------------------


class TestFingerprintNormalization:
    def test_trailing_whitespace_ignored(self):
        fp1 = dss._fingerprint(["line one   ", "line two  "])
        fp2 = dss._fingerprint(["line one", "line two"])
        assert fp1 == fp2

    def test_different_content_different_fingerprint(self):
        fp1 = dss._fingerprint(["line one"])
        fp2 = dss._fingerprint(["line two"])
        assert fp1 != fp2

    def test_empty_input(self):
        # Should not crash on empty input.
        fp = dss._fingerprint([])
        assert isinstance(fp, str)
        assert len(fp) == 64  # SHA-256 hex digest


# ---------------------------------------------------------------------------
# _build_status_block -- boundary conditions
# ---------------------------------------------------------------------------


class TestBuildStatusBlock:
    def test_no_entries_between_batches(self):
        state = dss.ActiveBatchState(
            current_batch=None,
            last_completed_batch=10,
            next_undefined_batch=None,
        )
        block = dss._build_status_block(state, [])
        text = "\n".join(block)
        assert "between batches" in text
        assert "Batch 10" in text
        assert "entries in active log block: 0" in text

    def test_no_entries_with_undefined_next(self):
        state = dss.ActiveBatchState(
            current_batch=None,
            last_completed_batch=10,
            next_undefined_batch=11,
        )
        block = dss._build_status_block(state, [])
        text = "\n".join(block)
        assert "Batch 11 is not yet defined" in text

    def test_no_entries_all_none(self):
        state = dss.ActiveBatchState(
            current_batch=None,
            last_completed_batch=None,
            next_undefined_batch=None,
        )
        block = dss._build_status_block(state, [])
        text = "\n".join(block)
        assert "unknown" in text

    def test_entries_with_wp_gap(self):
        """WP-1 and WP-3 present -- next expected should be WP-2."""
        e1 = dss.Entry(
            heading="### 2026-02-20 - Work (Batch 11 WP-1)",
            date="2026-02-20",
            title="Work (Batch 11 WP-1)",
            lines=("### 2026-02-20 - Work (Batch 11 WP-1)", "Content"),
            start_idx=0,
            fingerprint="a",
        )
        e2 = dss.Entry(
            heading="### 2026-02-21 - Work (Batch 11 WP-3)",
            date="2026-02-21",
            title="Work (Batch 11 WP-3)",
            lines=("### 2026-02-21 - Work (Batch 11 WP-3)", "Content"),
            start_idx=0,
            fingerprint="b",
        )
        state = dss.ActiveBatchState(
            current_batch=11, last_completed_batch=10, next_undefined_batch=None
        )
        block = dss._build_status_block(state, [e1, e2])
        text = "\n".join(block)
        assert "WP-2" in text
        assert "Batch 11" in text

    def test_entries_without_wp_tags(self):
        """Entries with no WP- tags -- completed should say 'none'."""
        entry = dss.Entry(
            heading="### 2026-02-20 - Side task fix",
            date="2026-02-20",
            title="Side task fix",
            lines=("### 2026-02-20 - Side task fix", "Content"),
            start_idx=0,
            fingerprint="a",
        )
        state = dss.ActiveBatchState(
            current_batch=11, last_completed_batch=10, next_undefined_batch=None
        )
        block = dss._build_status_block(state, [entry])
        text = "\n".join(block)
        assert "none" in text.lower() or "unknown" in text.lower()

    def test_current_batch_none_infers_from_completed(self):
        """When current_batch is None but last_completed_batch exists,
        the label should still resolve via fallback."""
        entry = dss.Entry(
            heading="### 2026-02-20 - Work (Batch 11 WP-1)",
            date="2026-02-20",
            title="Work (Batch 11 WP-1)",
            lines=("### 2026-02-20 - Work (Batch 11 WP-1)", "Content"),
            start_idx=0,
            fingerprint="a",
        )
        state = dss.ActiveBatchState(
            current_batch=None, last_completed_batch=10, next_undefined_batch=None
        )
        block = dss._build_status_block(state, [entry])
        text = "\n".join(block)
        # Should infer Batch 11 from last_completed_batch + 1.
        assert "Batch 11" in text


# ---------------------------------------------------------------------------
# _cross_validate -- mismatch and stale detection
# ---------------------------------------------------------------------------


class TestCrossValidate:
    def test_no_counts_no_warnings(self):
        warnings = dss._cross_validate(
            ["# PLAYBOOK", "No counts here"],
            ["# SESSION", "No counts here"],
        )
        assert warnings == []

    def test_matching_counts_no_warning(self):
        warnings = dss._cross_validate(
            ["**121 tests passing**"],
            ["**121 passing**"],
        )
        assert warnings == []

    def test_mismatched_counts_warns(self):
        warnings = dss._cross_validate(
            ["**121 tests passing**"],
            ["**119 passing**"],
        )
        assert len(warnings) == 1
        assert "mismatch" in warnings[0].lower()

    def test_stale_header_in_playbook(self):
        warnings = dss._cross_validate(
            ["# PLAYBOOK: refactor monolithic app.py", "content"],
            ["# SESSION", "content"],
        )
        assert any("Stale header" in w for w in warnings)

    def test_stale_header_in_session_context(self):
        warnings = dss._cross_validate(
            ["# PLAYBOOK", "content"],
            ["# SESSION: Post-Batch 8 cleanup", "content"],
        )
        assert any("Stale header" in w for w in warnings)

    def test_stale_phrase_beyond_first_5_lines_not_detected(self):
        """Stale phrase detection only scans the first 5 lines."""
        playbook = ["line"] * 6 + ["refactor monolithic mentioned late"]
        warnings = dss._cross_validate(playbook, ["# SESSION"])
        stale_warnings = [w for w in warnings if "Stale header" in w]
        assert stale_warnings == []

    def test_counts_only_in_one_file_no_warning(self):
        """If only one file has counts, there's nothing to compare."""
        warnings = dss._cross_validate(
            ["**121 tests passing**"],
            ["No counts here"],
        )
        assert warnings == []

    def test_section4_historical_count_ignored(self):
        """Historical counts in Section 4 should not trigger a mismatch."""
        playbook = [
            "# PLAYBOOK",
            "",
            "## 3. Active batch",
            "",
            "Current test count: **199 tests passing**",
            "",
            "## 4. Execution log",
            "",
            "### 2026-02-20 - Some prior commit",
            "",
            "Validated: **185 passed**",
            "",
        ]
        session = ["# SESSION", "", "Test count: **199 tests passing**"]
        warnings = dss._cross_validate(playbook, session)
        count_warnings = [w for w in warnings if "mismatch" in w.lower()]
        assert count_warnings == []

    def test_section3_mismatch_still_detected(self):
        """A genuine mismatch in Section 3 vs SESSION_CONTEXT still warns."""
        playbook = [
            "# PLAYBOOK",
            "",
            "## 3. Active batch",
            "",
            "Current test count: **195 tests passing**",
            "",
            "## 4. Execution log",
            "",
            "### 2026-02-20 - Some prior commit",
            "",
            "Validated: **185 passed**",
            "",
        ]
        session = ["# SESSION", "", "Test count: **199 tests passing**"]
        warnings = dss._cross_validate(playbook, session)
        assert any("mismatch" in w.lower() for w in warnings)

    def test_archive_link_exists_no_warning(self, tmp_path, monkeypatch):
        """No warning when linked archive file exists."""
        archive_dir = tmp_path / "docs" / "history"
        archive_dir.mkdir(parents=True)
        (archive_dir / "BATCH0_DEFINITION.md").write_text("# Batch 0")
        monkeypatch.chdir(tmp_path)
        playbook = [
            "| 0 | Title | `docs/history/BATCH0_DEFINITION.md` |",
        ]
        warnings = dss._cross_validate(playbook, ["# SESSION"])
        archive_warnings = [w for w in warnings if "Broken archive link" in w]
        assert archive_warnings == []

    def test_archive_link_missing_warns(self, tmp_path, monkeypatch):
        """Warning when linked archive file does not exist."""
        monkeypatch.chdir(tmp_path)
        playbook = [
            "| 1 | Title | `docs/history/BATCH1_DEFINITION.md` |",
        ]
        warnings = dss._cross_validate(playbook, ["# SESSION"])
        assert any("Broken archive link" in w for w in warnings)
        assert any("BATCH1_DEFINITION.md" in w for w in warnings)

    def test_archive_link_multiple_missing(self, tmp_path, monkeypatch):
        """Each broken link produces its own warning."""
        monkeypatch.chdir(tmp_path)
        playbook = [
            "| 0 | A | `docs/history/BATCH0_DEFINITION.md` |",
            "| 1 | B | `docs/history/BATCH1_DEFINITION.md` |",
        ]
        warnings = dss._cross_validate(playbook, ["# SESSION"])
        archive_warnings = [w for w in warnings if "Broken archive link" in w]
        assert len(archive_warnings) == 2

    def test_archive_link_multiple_on_same_line(self, tmp_path, monkeypatch):
        """Multiple archive links on one line are all validated."""
        monkeypatch.chdir(tmp_path)
        playbook = [
            "| 0 | A | `docs/history/A.md` `docs/history/B.md` |",
        ]
        warnings = dss._cross_validate(playbook, ["# SESSION"])
        archive_warnings = [w for w in warnings if "Broken archive link" in w]
        assert len(archive_warnings) == 2
        assert "A.md" in archive_warnings[0]
        assert "B.md" in archive_warnings[1]


# ---------------------------------------------------------------------------
# _render_section4 -- edge and empty cases
# ---------------------------------------------------------------------------


class TestRenderSection4:
    def test_empty_current_and_non_current(self):
        prefix = ["## 4. Execution log", "", "Preamble text."]
        result = dss._render_section4(prefix, [], [])
        text = "\n".join(result)
        assert dss.CURRENT_BATCH_START_MARKER in text
        assert dss.CURRENT_BATCH_END_MARKER in text
        # No entries between markers.
        start_idx = result.index(dss.CURRENT_BATCH_START_MARKER)
        end_idx = result.index(dss.CURRENT_BATCH_END_MARKER)
        between = [line for line in result[start_idx + 1 : end_idx] if line.strip()]
        assert between == []

    def test_non_current_entries_after_end_marker(self):
        prefix = ["## 4. Execution log"]
        entry = dss.Entry(
            heading="### 2026-01-01 - Old entry",
            date="2026-01-01",
            title="Old entry",
            lines=("### 2026-01-01 - Old entry", "Content"),
            start_idx=0,
            fingerprint="a",
        )
        result = dss._render_section4(prefix, [], [entry])
        end_marker_idx = result.index(dss.CURRENT_BATCH_END_MARKER)
        # The old entry should appear after the end marker.
        assert any("Old entry" in line for line in result[end_marker_idx + 1 :])


# ---------------------------------------------------------------------------
# _render_archive -- edge cases
# ---------------------------------------------------------------------------


class TestRenderArchive:
    def test_empty_entries(self):
        prefix = ["# Archive", "", "Prefix text."]
        result = dss._render_archive(prefix, [])
        assert result == ["# Archive", "", "Prefix text."]

    def test_entries_appended_after_prefix(self):
        prefix = ["# Archive"]
        entry = dss.Entry(
            heading="### 2026-01-01 - Entry",
            date="2026-01-01",
            title="Entry",
            lines=("### 2026-01-01 - Entry", "Content"),
            start_idx=0,
            fingerprint="a",
        )
        result = dss._render_archive(prefix, [entry])
        assert any("Entry" in line for line in result)


# ---------------------------------------------------------------------------
# _sync integration tests -- filesystem-based, isolated via tmp_path
# ---------------------------------------------------------------------------


@pytest.fixture
def sync_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Set up minimal filesystem structure for _sync and chdir into tmp_path."""
    monkeypatch.chdir(tmp_path)
    # Monkey-patch module-level paths so _sync uses tmp_path.
    monkeypatch.setattr(dss, "PLAYBOOK_PATH", tmp_path / "PLAYBOOK.md")
    monkeypatch.setattr(
        dss,
        "ARCHIVE_PATH",
        tmp_path / "docs" / "history" / "PLAYBOOK_EXECUTION_LOG_ARCHIVE.md",
    )
    monkeypatch.setattr(
        dss, "SESSION_CONTEXT_PATH", tmp_path / ".claude" / "SESSION_CONTEXT.md"
    )

    (tmp_path / "docs" / "history").mkdir(parents=True)
    (tmp_path / ".claude").mkdir(parents=True)

    (tmp_path / "PLAYBOOK.md").write_text(MINIMAL_PLAYBOOK, encoding="utf-8")
    archive_path = tmp_path / "docs" / "history" / "PLAYBOOK_EXECUTION_LOG_ARCHIVE.md"
    archive_path.write_text(MINIMAL_ARCHIVE, encoding="utf-8")
    session_path = tmp_path / ".claude" / "SESSION_CONTEXT.md"
    session_path.write_text(MINIMAL_SESSION_CONTEXT, encoding="utf-8")
    return tmp_path


class TestSyncIntegration:
    def test_basic_sync_succeeds(self, sync_env: Path):
        result = dss._sync(keep_non_current=4)
        assert result.current_batch_entry_count == 1
        assert result.rotated_count == 0

    def test_missing_playbook_raises(self, sync_env: Path):
        (sync_env / "PLAYBOOK.md").unlink()
        with pytest.raises(dss.SyncError, match="Required file is missing"):
            dss._sync(keep_non_current=4)

    def test_missing_archive_raises(self, sync_env: Path):
        (sync_env / "docs" / "history" / "PLAYBOOK_EXECUTION_LOG_ARCHIVE.md").unlink()
        with pytest.raises(dss.SyncError, match="Required file is missing"):
            dss._sync(keep_non_current=4)

    def test_missing_session_context_succeeds(self, sync_env: Path):
        """SESSION_CONTEXT.md is optional; missing file should not raise."""
        (sync_env / ".claude" / "SESSION_CONTEXT.md").unlink()
        result = dss._sync(keep_non_current=4)
        assert result.session_lines is None
        assert result.current_batch_entry_count == 1

    def test_missing_section_3_raises(self, sync_env: Path):
        playbook = sync_env / "PLAYBOOK.md"
        playbook.write_text(
            "# PLAYBOOK\n\n## 4. Execution log\n\nContent\n"
            f"\n{dss.CURRENT_BATCH_START_MARKER}\n{dss.CURRENT_BATCH_END_MARKER}\n",
            encoding="utf-8",
        )
        with pytest.raises(dss.SyncError, match="Could not find section heading"):
            dss._sync(keep_non_current=4)

    def test_missing_markers_in_section_4_raises(self, sync_env: Path):
        playbook = sync_env / "PLAYBOOK.md"
        playbook.write_text(
            "# PLAYBOOK\n\n## 3. Active batch\n\nBatch 11 is active.\n\n"
            "## 4. Execution log\n\nNo markers here.\n",
            encoding="utf-8",
        )
        with pytest.raises(dss.SyncError, match="must contain start marker"):
            dss._sync(keep_non_current=4)

    def test_stale_entries_rotated_to_archive(self, sync_env: Path):
        """Entries from a completed batch inside current-batch markers
        should be rotated out."""
        playbook_text = dedent(
            """\
            # PLAYBOOK

            ## 3. Active batch

            Batch 10 is complete.
            Batch 11 is active.

            ## 4. Execution log

            Preamble.

            <!-- DOCSYNC:CURRENT-BATCH-START -->

            ### 2026-02-18 - Old work (Batch 10 WP-5)

            This is stale -- batch 10 is done.

            ### 2026-02-20 - Current work (Batch 11 WP-1)

            This is current.

            <!-- DOCSYNC:CURRENT-BATCH-END -->
        """
        )
        (sync_env / "PLAYBOOK.md").write_text(playbook_text, encoding="utf-8")
        result = dss._sync(keep_non_current=4)
        # Stale Batch 10 entry should be rotated.
        assert result.rotated_count == 1
        assert result.current_batch_entry_count == 1
        # Verify stale entry ended up in archive.
        archive_text = "\n".join(result.archive_lines)
        assert "Batch 10 WP-5" in archive_text
        # Verify current entry stayed in playbook.
        playbook_text_after = "\n".join(result.playbook_lines)
        assert "Batch 11 WP-1" in playbook_text_after

    def test_deduplication_across_archive(self, sync_env: Path):
        """An entry that already exists in the archive (same fingerprint)
        should not be duplicated on rotation."""
        entry_text = (
            "### 2026-02-15 - Duplicate entry (Batch 10 WP-1)\n\nSame content.\n"
        )

        # Put the entry in both PLAYBOOK (non-current) and archive.
        playbook_text = dedent(
            f"""\
            # PLAYBOOK

            ## 3. Active batch

            Batch 10 is complete.
            Batch 11 is active.

            ## 4. Execution log

            Preamble.

            <!-- DOCSYNC:CURRENT-BATCH-START -->

            ### 2026-02-20 - Current work (Batch 11 WP-1)

            Current content.

            <!-- DOCSYNC:CURRENT-BATCH-END -->

            {entry_text}
        """
        )
        archive_text = f"# Archive\n\n{entry_text}"

        (sync_env / "PLAYBOOK.md").write_text(playbook_text, encoding="utf-8")
        archive_path = (
            sync_env / "docs" / "history" / "PLAYBOOK_EXECUTION_LOG_ARCHIVE.md"
        )
        archive_path.write_text(archive_text, encoding="utf-8")

        result = dss._sync(keep_non_current=0)
        # Should only appear once in archive after dedup.
        archive_out = "\n".join(result.archive_lines)
        count = archive_out.count("Duplicate entry (Batch 10 WP-1)")
        assert count == 1

    def test_keep_non_current_zero_rotates_all(self, sync_env: Path):
        """With keep_non_current=0, all non-current entries should rotate."""
        playbook_text = dedent(
            """\
            # PLAYBOOK

            ## 3. Active batch

            Batch 11 is active. Batch 10 is complete.

            ## 4. Execution log

            Preamble.

            <!-- DOCSYNC:CURRENT-BATCH-START -->

            ### 2026-02-20 - Current (Batch 11 WP-1)

            Current.

            <!-- DOCSYNC:CURRENT-BATCH-END -->

            ### 2026-02-10 - Old untagged entry

            Should be rotated with keep_non_current=0.
        """
        )
        (sync_env / "PLAYBOOK.md").write_text(playbook_text, encoding="utf-8")
        result = dss._sync(keep_non_current=0)
        assert result.kept_non_current_count == 0
        assert result.rotated_count == 1

    def test_empty_section_4_no_entries(self, sync_env: Path):
        """Section 4 with markers but no entries (valid at batch boundary)."""
        playbook_text = dedent(
            """\
            # PLAYBOOK

            ## 3. Active batch

            Batch 10 is complete. Batch 11 is not yet defined.

            ## 4. Execution log

            Preamble.

            <!-- DOCSYNC:CURRENT-BATCH-START -->

            <!-- DOCSYNC:CURRENT-BATCH-END -->
        """
        )
        (sync_env / "PLAYBOOK.md").write_text(playbook_text, encoding="utf-8")
        result = dss._sync(keep_non_current=4)
        assert result.current_batch_entry_count == 0
        assert result.rotated_count == 0

    def test_session_context_status_block_updated(self, sync_env: Path):
        """STATUS markers in SESSION_CONTEXT should be refreshed."""
        result = dss._sync(keep_non_current=4)
        session_text = "\n".join(result.session_lines)
        assert "Batch 11" in session_text
        assert "Section 3 and Section 4" in session_text

    def test_session_context_missing_status_markers_raises(self, sync_env: Path):
        session_path = sync_env / ".claude" / "SESSION_CONTEXT.md"
        session_path.write_text(
            "# SESSION CONTEXT\n\nNo markers here.\n", encoding="utf-8"
        )
        with pytest.raises(dss.SyncError, match="must contain start marker"):
            dss._sync(keep_non_current=4)

    def test_untagged_entries_kept_when_no_current_batch_tags(self, sync_env: Path):
        """When no entries are tagged for the current batch, ambiguous
        untagged entries should be kept (not rotated) to avoid data loss."""
        playbook_text = dedent(
            """\
            # PLAYBOOK

            ## 3. Active batch

            Batch 11 is active. Batch 10 is complete.

            ## 4. Execution log

            Preamble.

            <!-- DOCSYNC:CURRENT-BATCH-START -->

            ### 2026-02-20 - Side task fix

            Untagged entry, no batch number.

            <!-- DOCSYNC:CURRENT-BATCH-END -->
        """
        )
        (sync_env / "PLAYBOOK.md").write_text(playbook_text, encoding="utf-8")
        result = dss._sync(keep_non_current=4)
        # Untagged entry should be kept as current (not rotated).
        assert result.current_batch_entry_count == 1
        assert result.rotated_count == 0

    def test_untagged_entries_stale_when_tagged_current_exists(self, sync_env: Path):
        """When tagged current-batch entries exist, untagged entries inside
        the markers should be treated as stale."""
        playbook_text = dedent(
            """\
            # PLAYBOOK

            ## 3. Active batch

            Batch 11 is active. Batch 10 is complete.

            ## 4. Execution log

            Preamble.

            <!-- DOCSYNC:CURRENT-BATCH-START -->

            ### 2026-02-19 - Side task fix

            Untagged entry.

            ### 2026-02-20 - Real work (Batch 11 WP-1)

            Tagged current entry.

            <!-- DOCSYNC:CURRENT-BATCH-END -->
        """
        )
        (sync_env / "PLAYBOOK.md").write_text(playbook_text, encoding="utf-8")
        result = dss._sync(keep_non_current=4)
        # Untagged should be moved to non-current, tagged should stay.
        assert result.current_batch_entry_count == 1
        # The untagged entry is non-current but within keep limit.
        assert result.kept_non_current_count == 1


# ---------------------------------------------------------------------------
# main() argument handling
# ---------------------------------------------------------------------------


class TestMainArgs:
    def test_both_check_and_fix_returns_2(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr("sys.argv", ["doc_state_sync.py", "--check", "--fix"])
        assert dss.main() == 2

    def test_negative_keep_non_current_returns_2(
        self, sync_env: Path, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.setattr(
            "sys.argv", ["doc_state_sync.py", "--fix", "--keep-non-current", "-1"]
        )
        assert dss.main() == 2

    def test_no_mode_defaults_to_check(
        self, sync_env: Path, monkeypatch: pytest.MonkeyPatch, capsys
    ):
        monkeypatch.setattr("sys.argv", ["doc_state_sync.py"])
        exit_code = dss.main()
        captured = capsys.readouterr()
        assert "defaulting to --check" in captured.err
        # Fresh fixture has a stale placeholder in SESSION_CONTEXT, so
        # check mode should detect drift (exit 1).
        assert exit_code == 1

    def test_check_detects_drift(
        self, sync_env: Path, monkeypatch: pytest.MonkeyPatch, capsys
    ):
        """Dirty SESSION_CONTEXT (status block is stale placeholder) should
        cause --check to return 1."""
        monkeypatch.setattr("sys.argv", ["doc_state_sync.py", "--check"])
        exit_code = dss.main()
        # The placeholder "- placeholder" in session context differs from
        # the generated status block, so drift should be detected.
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "drift detected" in captured.out

    def test_fix_writes_files(
        self, sync_env: Path, monkeypatch: pytest.MonkeyPatch, capsys
    ):
        monkeypatch.setattr("sys.argv", ["doc_state_sync.py", "--fix"])
        exit_code = dss.main()
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "wrote updates" in captured.out or "no changes" in captured.out

    def test_fix_then_check_is_clean(
        self, sync_env: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """Running --fix followed by --check should pass (exit 0)."""
        monkeypatch.setattr("sys.argv", ["doc_state_sync.py", "--fix"])
        dss.main()
        monkeypatch.setattr("sys.argv", ["doc_state_sync.py", "--check"])
        assert dss.main() == 0

    def test_cross_validate_warnings_printed(
        self, sync_env: Path, monkeypatch: pytest.MonkeyPatch, capsys
    ):
        """Cross-validation warnings should appear on stderr."""
        # Inject mismatched test counts into Section 3 (not Section 4).
        playbook_path = sync_env / "PLAYBOOK.md"
        content = playbook_path.read_text(encoding="utf-8")
        content = content.replace(
            "Batch 11 is active.",
            "Batch 11 is active.\n\n**121 tests passing**",
        )
        playbook_path.write_text(content, encoding="utf-8")

        session_path = sync_env / ".claude" / "SESSION_CONTEXT.md"
        s_content = session_path.read_text(encoding="utf-8")
        s_content += "\n**99 passing**\n"
        session_path.write_text(s_content, encoding="utf-8")

        monkeypatch.setattr("sys.argv", ["doc_state_sync.py", "--fix"])
        dss.main()
        captured = capsys.readouterr()
        assert "WARNING" in captured.err
        assert "mismatch" in captured.err.lower()


# ---------------------------------------------------------------------------
# Missing SESSION_CONTEXT.md regression tests (CI environment)
# ---------------------------------------------------------------------------


class TestMissingSessionContext:
    def test_check_passes_without_session_context(
        self, sync_env: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """--check must not fail solely because SESSION_CONTEXT.md is missing."""
        (sync_env / ".claude" / "SESSION_CONTEXT.md").unlink()
        monkeypatch.setattr("sys.argv", ["doc_state_sync.py", "--check"])
        exit_code = dss.main()
        # Playbook and archive are already in sync for the minimal fixture,
        # so check should pass (exit 0) even without SESSION_CONTEXT.md.
        assert exit_code == 0

    def test_fix_does_not_create_session_context(
        self, sync_env: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """--fix must not create SESSION_CONTEXT.md when it does not exist."""
        session_path = sync_env / ".claude" / "SESSION_CONTEXT.md"
        session_path.unlink()
        monkeypatch.setattr("sys.argv", ["doc_state_sync.py", "--fix"])
        dss.main()
        assert not session_path.exists()

    def test_cross_validate_skips_session_checks_when_none(self):
        """_cross_validate with session_lines=None should not raise and
        should produce no session-specific warnings."""
        warnings = dss._cross_validate(["# PLAYBOOK", "content"], None)
        session_warnings = [w for w in warnings if "SESSION_CONTEXT" in w]
        assert session_warnings == []


class TestRegexPatterns:
    def test_section_3_re_case_insensitive(self):
        assert dss.SECTION_3_RE.match("## 3. ACTIVE BATCH")
        assert dss.SECTION_3_RE.match("## 3 Active batch and more")
        assert not dss.SECTION_3_RE.match("## 4. Execution log")

    def test_section_4_re_case_insensitive(self):
        assert dss.SECTION_4_RE.match("## 4. EXECUTION LOG")
        assert dss.SECTION_4_RE.match("## 4 Execution log details")
        assert not dss.SECTION_4_RE.match("## 3. Active batch")

    def test_entry_heading_re(self):
        m = dss.ENTRY_HEADING_RE.match("### 2026-02-20 - Some title (Batch 11 WP-1)")
        assert m is not None
        assert m.group(1) == "2026-02-20"
        assert "Batch 11" in m.group(2)

    def test_entry_heading_re_rejects_malformed(self):
        assert dss.ENTRY_HEADING_RE.match("### 2026-02-20 No dash separator") is None
        assert dss.ENTRY_HEADING_RE.match("## 2026-02-20 - Wrong level") is None
        assert dss.ENTRY_HEADING_RE.match("### not-a-date - Title") is None

    def test_batch_complete_re(self):
        assert dss.BATCH_COMPLETE_RE.search("Batch 10 is complete.")
        assert dss.BATCH_COMPLETE_RE.search("batch 10 is Complete")
        assert not dss.BATCH_COMPLETE_RE.search("Batch 10 is active")

    def test_batch_current_re(self):
        assert dss.BATCH_CURRENT_RE.search("Batch 11 is active.")
        assert dss.BATCH_CURRENT_RE.search("Batch 11 is current")
        assert dss.BATCH_CURRENT_RE.search("Batch 11 is in-progress")
        assert dss.BATCH_CURRENT_RE.search("Batch 11 is in progress")
        assert not dss.BATCH_CURRENT_RE.search("Batch 11 is complete")

    def test_batch_not_defined_re(self):
        assert dss.BATCH_NOT_DEFINED_RE.search("Batch 12 is not yet defined.")
        assert not dss.BATCH_NOT_DEFINED_RE.search("Batch 12 is active.")
