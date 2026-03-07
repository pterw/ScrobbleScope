"""Tests for scrobblescope.heatmap -- daily-count aggregation and task lifecycle.

Covers:
- _aggregate_daily_counts: pure function with mock page data, "now playing"
  skips, 365/366-day range fill, boundary timestamps, empty pages.
- _fetch_and_process_heatmap: upstream error, partial data, zero scrobbles,
  happy path result dict, progress callback percentages.
- heatmap_task: release_job_slot called in finally (even on exception).
- no_scrobbles_in_range error code existence.
"""

from datetime import date, datetime
from datetime import time as dt_time
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest

from scrobblescope.heatmap import (
    _aggregate_daily_counts,
    _fetch_and_process_heatmap,
    heatmap_task,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_track(day, uts_override=None):
    """Build a minimal Last.fm track dict for a given date.

    Args:
        day: ``datetime.date`` instance.
        uts_override: Optional int to use as the uts value instead of
            computing from *day*.  Pass ``None`` to omit the date field
            entirely (simulates "now playing").
    """
    if uts_override is False:
        # Explicitly no date field -> "now playing" track.
        return {"name": "Song", "artist": {"#text": "Artist"}}
    uts = uts_override or int(datetime.combine(day, dt_time(12, 0)).timestamp())
    return {
        "name": "Song",
        "artist": {"#text": "Artist"},
        "date": {"uts": str(uts)},
    }


def _wrap_tracks(tracks):
    """Wrap a list of track dicts into a single Last.fm page dict."""
    return {"recenttracks": {"track": tracks}}


# ===========================================================================
# _aggregate_daily_counts
# ===========================================================================


class TestAggregateDailyCounts:
    """Unit tests for the pure aggregation function."""

    def test_basic_counting(self):
        """Tracks on known dates produce correct per-day counts."""
        from_date = date(2026, 1, 1)
        to_date = date(2026, 1, 3)
        pages = [
            _wrap_tracks(
                [
                    _make_track(date(2026, 1, 1)),
                    _make_track(date(2026, 1, 1)),
                    _make_track(date(2026, 1, 3)),
                ]
            )
        ]
        result = _aggregate_daily_counts(pages, from_date, to_date)

        assert result["2026-01-01"] == 2
        assert result["2026-01-02"] == 0
        assert result["2026-01-03"] == 1

    def test_now_playing_skipped(self):
        """Tracks without a date field ('now playing') are silently skipped."""
        from_date = date(2026, 3, 1)
        to_date = date(2026, 3, 1)
        now_playing = _make_track(None, uts_override=False)
        normal = _make_track(date(2026, 3, 1))
        pages = [_wrap_tracks([now_playing, normal])]

        result = _aggregate_daily_counts(pages, from_date, to_date)
        assert result["2026-03-01"] == 1

    def test_fills_365_days(self):
        """A 365-day range produces exactly 365 keys (non-leap year span)."""
        from_date = date(2025, 3, 8)
        to_date = date(2026, 3, 7)
        expected_days = (to_date - from_date).days + 1  # inclusive
        pages = []  # no scrobbles

        result = _aggregate_daily_counts(pages, from_date, to_date)
        assert len(result) == expected_days
        assert all(v == 0 for v in result.values())

    def test_fills_366_days_leap_year(self):
        """A range spanning Feb 29 of a leap year produces 366 keys."""
        # 2024 is a leap year.
        from_date = date(2023, 3, 8)
        to_date = date(2024, 3, 7)
        expected_days = (to_date - from_date).days + 1
        assert expected_days == 366  # sanity: range includes 2024-02-29
        pages = []

        result = _aggregate_daily_counts(pages, from_date, to_date)
        assert len(result) == 366
        assert "2024-02-29" in result

    def test_boundary_timestamps(self):
        """Tracks at exactly from_date start and to_date end are included."""
        from_date = date(2026, 6, 1)
        to_date = date(2026, 6, 2)
        # Track at start of from_date (00:00:00).
        start_uts = int(datetime.combine(from_date, dt_time.min).timestamp())
        # Track at end of to_date (23:59:59).
        end_uts = int(datetime.combine(to_date, dt_time(23, 59, 59)).timestamp())
        pages = [
            _wrap_tracks(
                [
                    _make_track(from_date, uts_override=start_uts),
                    _make_track(to_date, uts_override=end_uts),
                ]
            )
        ]
        result = _aggregate_daily_counts(pages, from_date, to_date)
        assert result["2026-06-01"] == 1
        assert result["2026-06-02"] == 1

    def test_out_of_range_excluded(self):
        """Tracks outside the [from_date, to_date] window are excluded."""
        from_date = date(2026, 5, 10)
        to_date = date(2026, 5, 12)
        before_uts = int(
            datetime.combine(date(2026, 5, 9), dt_time(23, 59, 59)).timestamp()
        )
        after_uts = int(
            datetime.combine(date(2026, 5, 13), dt_time(0, 0, 1)).timestamp()
        )
        inside = _make_track(date(2026, 5, 11))
        pages = [
            _wrap_tracks(
                [
                    _make_track(date(2026, 5, 9), uts_override=before_uts),
                    inside,
                    _make_track(date(2026, 5, 13), uts_override=after_uts),
                ]
            )
        ]
        result = _aggregate_daily_counts(pages, from_date, to_date)
        assert result["2026-05-11"] == 1
        assert sum(result.values()) == 1  # only the inside track counted

    def test_empty_pages_all_zeros(self):
        """Empty page list produces a dict of all zeros for the range."""
        from_date = date(2026, 1, 1)
        to_date = date(2026, 1, 7)
        result = _aggregate_daily_counts([], from_date, to_date)
        assert len(result) == 7
        assert all(v == 0 for v in result.values())

    def test_multiple_pages_combined(self):
        """Tracks across multiple pages are merged into one count dict."""
        from_date = date(2026, 2, 1)
        to_date = date(2026, 2, 2)
        pages = [
            _wrap_tracks([_make_track(date(2026, 2, 1))]),
            _wrap_tracks(
                [
                    _make_track(date(2026, 2, 1)),
                    _make_track(date(2026, 2, 2)),
                ]
            ),
        ]
        result = _aggregate_daily_counts(pages, from_date, to_date)
        assert result["2026-02-01"] == 2
        assert result["2026-02-02"] == 1


# ===========================================================================
# _fetch_and_process_heatmap
# ===========================================================================


class TestFetchAndProcessHeatmap:
    """Async orchestrator tests -- mock all I/O, assert on job state calls."""

    @pytest.mark.asyncio
    async def test_upstream_error_sets_job_error(self):
        """When Last.fm returns an error, set_job_error is called and we return."""
        with (
            patch("scrobblescope.heatmap.cleanup_expired_cache"),
            patch("scrobblescope.heatmap.cleanup_expired_jobs"),
            patch("scrobblescope.heatmap.set_job_progress"),
            patch("scrobblescope.heatmap.set_job_stat"),
            patch(
                "scrobblescope.heatmap.fetch_all_recent_tracks_async",
                new_callable=AsyncMock,
                return_value=([], {"status": "error", "reason": "lastfm_unavailable"}),
            ),
            patch("scrobblescope.heatmap.set_job_error") as mock_set_error,
            patch("scrobblescope.heatmap.set_job_results") as mock_set_results,
        ):
            await _fetch_and_process_heatmap("job-1", "testuser")
            mock_set_error.assert_called_once_with(
                "job-1", "lastfm_unavailable", username="testuser"
            )
            mock_set_results.assert_not_called()

    @pytest.mark.asyncio
    async def test_partial_data_stores_warning_and_continues(self):
        """Partial fetch stores a warning stat but still produces results."""
        # One page with one track so total > 0.
        track_date = date(2026, 3, 1)
        page = _wrap_tracks([_make_track(track_date)])
        meta = {
            "status": "partial",
            "pages_expected": 10,
            "pages_received": 8,
            "pages_dropped": 2,
        }
        with (
            patch("scrobblescope.heatmap.cleanup_expired_cache"),
            patch("scrobblescope.heatmap.cleanup_expired_jobs"),
            patch("scrobblescope.heatmap.set_job_progress"),
            patch(
                "scrobblescope.heatmap.fetch_all_recent_tracks_async",
                new_callable=AsyncMock,
                return_value=([page], meta),
            ),
            patch("scrobblescope.heatmap.set_job_stat") as mock_stat,
            patch("scrobblescope.heatmap.set_job_results") as mock_results,
            patch("scrobblescope.heatmap.set_job_error") as mock_error,
        ):
            await _fetch_and_process_heatmap("job-2", "partialuser")

            # Warning stat was recorded.
            warning_calls = [
                c for c in mock_stat.call_args_list if c[0][1] == "partial_data_warning"
            ]
            assert len(warning_calls) == 1
            assert "2 of 10" in warning_calls[0][0][2]

            # Results were stored (not an error).
            mock_results.assert_called_once()
            mock_error.assert_not_called()

    @pytest.mark.asyncio
    async def test_zero_scrobbles_fires_no_scrobbles_error(self):
        """All-zero daily counts triggers the no_scrobbles_in_range error."""
        # Return an empty page set -> total == 0.
        meta = {"status": "ok", "pages_expected": 1, "pages_received": 1}
        with (
            patch("scrobblescope.heatmap.cleanup_expired_cache"),
            patch("scrobblescope.heatmap.cleanup_expired_jobs"),
            patch("scrobblescope.heatmap.set_job_progress"),
            patch("scrobblescope.heatmap.set_job_stat"),
            patch(
                "scrobblescope.heatmap.fetch_all_recent_tracks_async",
                new_callable=AsyncMock,
                return_value=([], meta),
            ),
            patch("scrobblescope.heatmap.set_job_error") as mock_error,
            patch("scrobblescope.heatmap.set_job_results") as mock_results,
        ):
            await _fetch_and_process_heatmap("job-3", "emptyuser")
            mock_error.assert_called_once_with(
                "job-3", "no_scrobbles_in_range", username="emptyuser"
            )
            mock_results.assert_not_called()

    @pytest.mark.asyncio
    async def test_happy_path_stores_correct_result_dict(self):
        """Successful fetch stores a result dict with expected keys and values."""
        # Build a page with scrobbles on a known day.
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        page = _wrap_tracks(
            [
                _make_track(yesterday),
                _make_track(yesterday),
                _make_track(today),
            ]
        )
        meta = {"status": "ok", "pages_expected": 1, "pages_received": 1}

        stored_result = {}

        def _capture_result(job_id, results):
            stored_result.update(results)
            return True

        with (
            patch("scrobblescope.heatmap.cleanup_expired_cache"),
            patch("scrobblescope.heatmap.cleanup_expired_jobs"),
            patch("scrobblescope.heatmap.set_job_progress"),
            patch("scrobblescope.heatmap.set_job_stat"),
            patch(
                "scrobblescope.heatmap.fetch_all_recent_tracks_async",
                new_callable=AsyncMock,
                return_value=([page], meta),
            ),
            patch(
                "scrobblescope.heatmap.set_job_results",
                side_effect=_capture_result,
            ),
            patch("scrobblescope.heatmap.set_job_error") as mock_error,
        ):
            await _fetch_and_process_heatmap("job-4", "happyuser")
            mock_error.assert_not_called()

        # Verify result structure.
        assert stored_result["username"] == "happyuser"
        assert "from_date" in stored_result
        assert "to_date" in stored_result
        assert stored_result["total_scrobbles"] == 3
        assert stored_result["max_count"] == 2  # yesterday had 2
        assert stored_result["daily_counts"][yesterday.isoformat()] == 2
        assert stored_result["daily_counts"][today.isoformat()] == 1

    @pytest.mark.asyncio
    async def test_progress_callback_sends_correct_percentages(self):
        """The progress callback maps fetch phases into 5-80% range."""
        today = datetime.now().date()
        page = _wrap_tracks([_make_track(today)])
        meta = {"status": "ok", "pages_expected": 1, "pages_received": 1}

        progress_calls = []

        def _capture_progress(job_id, **kwargs):
            if "progress" in kwargs:
                progress_calls.append(kwargs["progress"])
            return True

        with (
            patch("scrobblescope.heatmap.cleanup_expired_cache"),
            patch("scrobblescope.heatmap.cleanup_expired_jobs"),
            patch(
                "scrobblescope.heatmap.set_job_progress",
                side_effect=_capture_progress,
            ),
            patch("scrobblescope.heatmap.set_job_stat"),
            patch(
                "scrobblescope.heatmap.fetch_all_recent_tracks_async",
                new_callable=AsyncMock,
                return_value=([page], meta),
            ),
            patch("scrobblescope.heatmap.set_job_results"),
            patch("scrobblescope.heatmap.set_job_error"),
        ):
            await _fetch_and_process_heatmap("job-5", "progressuser")

        # Should include 0 (init), 5 (pre-fetch), 80 (aggregation), 100 (done).
        assert 0 in progress_calls
        assert 5 in progress_calls
        assert 80 in progress_calls
        assert 100 in progress_calls


# ===========================================================================
# heatmap_task (thread entry point)
# ===========================================================================


class TestHeatmapTask:
    """Tests for the synchronous thread entry point."""

    def test_release_job_slot_called_on_success(self):
        """release_job_slot is called even when the task succeeds."""
        with (
            patch("scrobblescope.heatmap.release_job_slot") as mock_release,
            patch(
                "scrobblescope.heatmap._fetch_and_process_heatmap",
                new_callable=AsyncMock,
            ),
        ):
            heatmap_task("job-ok", "user")
            mock_release.assert_called_once()

    def test_release_job_slot_called_on_exception(self):
        """release_job_slot is called even when the async pipeline explodes."""
        with (
            patch("scrobblescope.heatmap.release_job_slot") as mock_release,
            patch(
                "scrobblescope.heatmap._fetch_and_process_heatmap",
                new_callable=AsyncMock,
                side_effect=RuntimeError("boom"),
            ),
            patch("scrobblescope.heatmap.set_job_error"),
        ):
            # Should NOT raise -- heatmap_task catches exceptions.
            heatmap_task("job-err", "user")
            mock_release.assert_called_once()


# ===========================================================================
# Error code registry
# ===========================================================================


class TestErrorCode:
    """Verify the no_scrobbles_in_range error code is registered correctly."""

    def test_no_scrobbles_in_range_exists(self):
        """The error code is present in ERROR_CODES with correct fields."""
        from scrobblescope.errors import ERROR_CODES

        code = ERROR_CODES.get("no_scrobbles_in_range")
        assert code is not None, "no_scrobbles_in_range not in ERROR_CODES"
        assert code["source"] == "lastfm"
        assert code["retryable"] is False
        assert "{username}" in code["message"]

    def test_no_scrobbles_in_range_message_formats(self):
        """The message template accepts a username substitution."""
        from scrobblescope.errors import ERROR_CODES

        msg = ERROR_CODES["no_scrobbles_in_range"]["message"]
        formatted = msg.format(username="testuser")
        assert "testuser" in formatted
        assert "365" in formatted
