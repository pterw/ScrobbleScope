"""Tests for docsync.parser._parse_active_batch_state."""

from __future__ import annotations

from docsync.parser import _parse_active_batch_state


class TestParseActiveBatchStateConflicting:
    def test_conflicting_complete_and_active_same_batch(self):
        """When a batch is marked both complete and active, active wins."""
        lines = [
            "## 3. Active batch",
            "- Batch 10 is complete.",
            "- Batch 10 is active.",
        ]
        state = _parse_active_batch_state(lines)
        # Active signal should override complete for the same batch number.
        assert state.current_batch == 10
        assert state.last_completed_batch == 10
