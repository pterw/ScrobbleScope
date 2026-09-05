"""Tests for scrobblescope.heatmap -- daily-count aggregation and task lifecycle.

Covers:
- _aggregate_daily_counts: pure function with mock page data, "now playing"
  skips, 365/366-day range fill, boundary timestamps, midnight boundary
  attribution, empty pages.
- _fetch_and_process_heatmap: upstream error, partial data, partial+zero
  scrobbles combination, zero scrobbles, happy path result dict, progress
  callback percentages.
- heatmap_task: release_job_slot called in finally (even on exception).
- no_scrobbles_in_range error code existence.
"""

from datetime import date, datetime
from datetime import time as dt_time
from datetime import timedelta, timezone
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
    # Build UTS as UTC to match production decode (heatmap.py: tz=utc).
    uts = uts_override or int(
        datetime.combine(day, dt_time(12, 0), tzinfo=timezone.utc).timestamp()
    )
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
        # Track at start of from_date (00:00:00 UTC).
        start_uts = int(
            datetime.combine(from_date, dt_time.min, tzinfo=timezone.utc).timestamp()
        )
        # Track at end of to_date (23:59:59 UTC).
        end_uts = int(
            datetime.combine(
                to_date, dt_time(23, 59, 59), tzinfo=timezone.utc
            ).timestamp()
        )
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
            datetime.combine(
                date(2026, 5, 9), dt_time(23, 59, 59), tzinfo=timezone.utc
            ).timestamp()
        )
        after_uts = int(
            datetime.combine(
                date(2026, 5, 13), dt_time(0, 0, 1), tzinfo=timezone.utc
            ).timestamp()
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

    def test_midnight_boundary_attribution(self):
        """Tracks at 23:59:59 UTC on day D and 00:00:01 UTC on day D+1 land
        on correct days.

        Adversarial: catches an off-by-one in the uts->date conversion (e.g.
        rounding to the wrong second).
        """
        d1 = date(2026, 3, 1)
        d2 = date(2026, 3, 2)
        late_uts = int(
            datetime.combine(d1, dt_time(23, 59, 59), tzinfo=timezone.utc).timestamp()
        )
        early_uts = int(
            datetime.combine(d2, dt_time(0, 0, 1), tzinfo=timezone.utc).timestamp()
        )
        pages = [
            _wrap_tracks(
                [
                    _make_track(d1, uts_override=late_uts),
                    _make_track(d2, uts_override=early_uts),
                ]
            )
        ]
        result = _aggregate_daily_counts(pages, d1, d2)
        assert result["2026-03-01"] == 1
        assert result["2026-03-02"] == 1

    def test_utc_decode_invariant_against_local_tz_drift(self):
        """A UTS whose UTC-day and local-tz-day differ is attributed by UTC.

        Adversarial: catches a regression to naive ``datetime.fromtimestamp``.
        We pick a timestamp at 23:30 UTC on day D so that on any timezone west
        of UTC (Americas) it is still day D, but on any timezone east of UTC
        with offset >= +01 (Europe, Asia, Africa) it has already rolled to
        day D+1.  The production decode must agree with the UTS's *UTC*
        calendar date regardless of where the test runs.
        """
        d_utc = date(2026, 4, 10)
        # 23:30 UTC -- definitively day d_utc under UTC, definitively
        # d_utc+1 under any local tz with offset >= +01:00.
        ts_utc = int(
            datetime.combine(d_utc, dt_time(23, 30), tzinfo=timezone.utc).timestamp()
        )
        # Sanity: a naive decode using the running host's local tz must
        # disagree with the UTC decode for the test to be meaningful on a
        # UTC host (where local == UTC, the assertion still holds but the
        # adversarial signal is weaker).  We document the intent in the
        # docstring rather than skip on UTC hosts so the assertion runs
        # everywhere.
        pages = [_wrap_tracks([_make_track(d_utc, uts_override=ts_utc)])]
        from_date = d_utc - timedelta(days=1)
        to_date = d_utc + timedelta(days=1)
        result = _aggregate_daily_counts(pages, from_date, to_date)
        assert result[d_utc.isoformat()] == 1
        # The bucket on d_utc+1 must be zero -- this is what fails when
        # production naive-decodes the timestamp on a +01 or later host.
        assert result[(d_utc + timedelta(days=1)).isoformat()] == 0


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
    async def test_partial_data_with_zero_scrobbles_fires_error(self):
        """Partial fetch that yields no in-range tracks triggers no_scrobbles_in_range.

        Adversarial: verifies the zero-scrobble guard runs *after* the partial-data
        warning, so both branches execute correctly in combination.  A naive
        implementation might skip the zero check when status is "partial".
        """
        meta = {
            "status": "partial",
            "pages_expected": 5,
            "pages_received": 2,
            "pages_dropped": 3,
        }
        with (
            patch("scrobblescope.heatmap.cleanup_expired_cache"),
            patch("scrobblescope.heatmap.cleanup_expired_jobs"),
            patch("scrobblescope.heatmap.set_job_progress"),
            patch(
                "scrobblescope.heatmap.fetch_all_recent_tracks_async",
                new_callable=AsyncMock,
                return_value=([], meta),  # partial status but no tracks returned
            ),
            patch("scrobblescope.heatmap.set_job_stat") as mock_stat,
            patch("scrobblescope.heatmap.set_job_error") as mock_error,
            patch("scrobblescope.heatmap.set_job_results") as mock_results,
        ):
            await _fetch_and_process_heatmap("job-partial-zero", "partialuser")

        # Partial-data warning must still be recorded.
        warning_calls = [
            c for c in mock_stat.call_args_list if c[0][1] == "partial_data_warning"
        ]
        assert len(warning_calls) == 1
        # Zero-scrobble guard fires, not success.
        mock_error.assert_called_once_with(
            "job-partial-zero", "no_scrobbles_in_range", username="partialuser"
        )
        mock_results.assert_not_called()

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
        today = datetime.now(timezone.utc).date()
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
        completion_events = []

        def _capture_result(job_id, results):
            stored_result.update(results)
            completion_events.append("results")
            return True

        def _capture_progress(job_id, **kwargs):
            if kwargs.get("progress") == 100:
                completion_events.append("ready")
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
        assert completion_events == ["results", "ready"]

    @pytest.mark.asyncio
    async def test_success_is_readable_through_repository_at_100_percent(self):
        """A real job exposes its payload whenever progress reports complete."""
        from scrobblescope.repositories import create_job, delete_job, get_job_context

        today = datetime.now(timezone.utc).date()
        page = _wrap_tracks([_make_track(today)])
        metadata = {"status": "ok", "pages_expected": 1, "pages_received": 1}
        job_id = create_job({"username": "wired-user", "mode": "heatmap"})

        try:
            with (
                patch("scrobblescope.heatmap.cleanup_expired_cache"),
                patch("scrobblescope.heatmap.cleanup_expired_jobs"),
                patch(
                    "scrobblescope.heatmap.fetch_all_recent_tracks_async",
                    new_callable=AsyncMock,
                    return_value=([page], metadata),
                ),
            ):
                await _fetch_and_process_heatmap(job_id, "wired-user")

            context = get_job_context(job_id)
            assert context is not None
            assert context["progress"]["progress"] == 100
            assert context["progress"]["error"] is False
            assert context["results"]["username"] == "wired-user"
            assert context["results"]["total_scrobbles"] == 1
            assert context["progress"]["stats"]["pages_received"] == 1
            assert context["progress"]["stats"]["active_days"] == 1
        finally:
            delete_job(job_id)

    @pytest.mark.asyncio
    async def test_progress_callback_sends_correct_percentages(self):
        """The progress callback maps fetch phases into 5-80% range."""
        today = datetime.now(timezone.utc).date()
        page = _wrap_tracks([_make_track(today)])
        meta = {"status": "ok", "pages_expected": 1, "pages_received": 1}

        progress_calls = []

        def _capture_progress(job_id, **kwargs):
            if "progress" in kwargs:
                progress_calls.append(kwargs)
            return True

        async def _fetch_with_progress(*_args, **kwargs):
            kwargs["progress_cb"](1, 1)
            return [page], meta

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
                side_effect=_fetch_with_progress,
            ),
            patch("scrobblescope.heatmap.set_job_results"),
            patch("scrobblescope.heatmap.set_job_error"),
        ):
            await _fetch_and_process_heatmap("job-5", "progressuser")

        # The phase owns the operation name; the live statistic owns N / T.
        assert {
            "progress": 0,
            "message": "Initializing heatmap...",
            "error": False,
            "reset_stats": True,
        } in progress_calls
        assert {
            "progress": 5,
            "message": "Fetching your scrobble history from Last.fm...",
            "error": False,
            "phase": None,
        } in progress_calls
        assert {
            "progress": 80,
            "message": "Counting your daily scrobbles...",
            "phase": None,
        } in progress_calls
        assert {
            "progress": 100,
            "message": "Heatmap ready!",
            "error": False,
            "phase": None,
        } in progress_calls
        page_calls = [
            update
            for update in progress_calls
            if update.get("message") == "Reading your Last.fm history..."
        ]
        assert page_calls == [
            {
                "progress": 80,
                "message": "Reading your Last.fm history...",
                "phase": {
                    "key": "lastfm_fetch",
                    "label": "Fetching scrobbles",
                    "unit": "page",
                    "current": 1,
                    "total": 1,
                },
            }
        ]


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


class TestHeatmapPhaseProgress:
    """Verify phase reporting during heatmap fetch and clear at completion."""

    @pytest.mark.asyncio
    async def test_heatmap_lastfm_phase_and_cleared_at_completion(self):
        """Heatmap pipeline reports exact Last.fm phase and clears phase at completion."""
        from scrobblescope.repositories import create_job, get_job_progress

        job_id = create_job({"username": "user", "mode": "heatmap"})
        observed_phase = None

        today = datetime.now(timezone.utc).date()
        page = _wrap_tracks([_make_track(today)])
        meta = {"status": "ok", "pages_expected": 102, "pages_received": 23}

        async def fake_fetch(username, from_ts, to_ts, progress_cb=None):
            nonlocal observed_phase
            if progress_cb:
                progress_cb(23, 102, 23)
                observed_phase = get_job_progress(job_id).get("phase")
            return [page], meta

        with (
            patch("scrobblescope.heatmap.cleanup_expired_cache"),
            patch("scrobblescope.heatmap.cleanup_expired_jobs"),
            patch(
                "scrobblescope.heatmap.fetch_all_recent_tracks_async",
                side_effect=fake_fetch,
            ),
        ):
            await _fetch_and_process_heatmap(job_id, "user")

        assert observed_phase == {
            "key": "lastfm_fetch",
            "label": "Fetching scrobbles",
            "unit": "page",
            "current": 23,
            "total": 102,
        }
        final_progress = get_job_progress(job_id)
        assert "phase" not in final_progress
