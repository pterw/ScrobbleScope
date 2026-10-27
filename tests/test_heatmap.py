"""Tests for scrobblescope.heatmap -- daily-count aggregation and task lifecycle.

Covers:
- ``plays.aggregate_daily_counts`` is tested in ``tests/test_plays.py``.
- _fetch_and_process_heatmap: upstream error, partial data, partial+zero
  scrobbles combination, zero scrobbles, happy path result dict, progress
  callback percentages.
- heatmap_task: release_job_slot called in finally (even on exception).
- no_scrobbles_in_range error code existence.
"""

import asyncio
from datetime import UTC, date, datetime, timedelta
from datetime import time as dt_time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scrobblescope import jobs
from scrobblescope.errors import ProviderError, UserNotFoundError
from scrobblescope.heatmap import (
    _fetch_and_process_heatmap,
    heatmap_task,
)
from scrobblescope.lastfm import FetchSummary, ScrobbleFetch
from scrobblescope.plays import Play

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _play(day):
    """A play at noon UTC on ``day`` (a ``datetime.date``)."""
    return Play(
        played_at=datetime.combine(day, dt_time(12, 0), tzinfo=UTC),
        artist="Artist",
        album="Album",
        track="Song",
    )


def _fetch(plays, expected=1, received=1):
    """What ``fetch_scrobbles`` returns for ``plays`` read from ``received`` of
    ``expected`` pages."""
    return ScrobbleFetch(tuple(plays), FetchSummary(expected, received), 0, 0)


# ===========================================================================
# _fetch_and_process_heatmap
# ===========================================================================


class TestFetchAndProcessHeatmap:
    """Async orchestrator tests -- mock all I/O, assert on job state calls."""

    @pytest.mark.asyncio
    async def test_a_total_lastfm_failure_propagates_to_the_backstop(self):
        """A total Last.fm failure is an exception now: the pipeline neither
        swallows it nor publishes a terminal state itself.

        Planted defect: catch the provider failure in the pipeline and publish
        lastfm_unavailable from there."""
        with (
            patch("scrobblescope.heatmap.cleanup_expired_cache"),
            patch("scrobblescope.jobs.expire_stale"),
            patch("scrobblescope.jobs.start"),
            patch("scrobblescope.jobs.advance"),
            patch("scrobblescope.jobs.record_stat"),
            patch(
                "scrobblescope.heatmap.fetch_scrobbles",
                new_callable=AsyncMock,
                side_effect=ProviderError("lastfm", "unavailable"),
            ),
            patch("scrobblescope.jobs.fail") as mock_set_error,
            patch("scrobblescope.jobs.succeed") as mock_set_results,
        ):
            with pytest.raises(ProviderError):
                await _fetch_and_process_heatmap("job-1", "testuser")
            mock_set_error.assert_not_called()
            mock_set_results.assert_not_called()

    @pytest.mark.asyncio
    async def test_partial_data_stores_warning_and_continues(self):
        """Partial fetch stores a warning stat but still produces results."""
        # One play so total > 0.
        track_date = date(2026, 3, 1)
        with (
            patch("scrobblescope.heatmap.cleanup_expired_cache"),
            patch("scrobblescope.jobs.expire_stale"),
            patch("scrobblescope.jobs.start"),
            patch("scrobblescope.jobs.advance"),
            patch(
                "scrobblescope.heatmap.fetch_scrobbles",
                new_callable=AsyncMock,
                return_value=_fetch([_play(track_date)], expected=10, received=8),
            ),
            patch("scrobblescope.jobs.record_stat") as mock_stat,
            patch("scrobblescope.jobs.succeed") as mock_results,
            patch("scrobblescope.jobs.fail") as mock_error,
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
        with (
            patch("scrobblescope.heatmap.cleanup_expired_cache"),
            patch("scrobblescope.jobs.expire_stale"),
            patch("scrobblescope.jobs.start"),
            patch("scrobblescope.jobs.advance"),
            patch(
                "scrobblescope.heatmap.fetch_scrobbles",
                new_callable=AsyncMock,
                return_value=_fetch([], expected=5, received=2),  # partial, no plays
            ),
            patch("scrobblescope.jobs.record_stat") as mock_stat,
            patch("scrobblescope.jobs.fail") as mock_error,
            patch("scrobblescope.jobs.succeed") as mock_results,
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
        # Return no plays -> total == 0.
        with (
            patch("scrobblescope.heatmap.cleanup_expired_cache"),
            patch("scrobblescope.jobs.expire_stale"),
            patch("scrobblescope.jobs.start"),
            patch("scrobblescope.jobs.advance"),
            patch("scrobblescope.jobs.record_stat"),
            patch(
                "scrobblescope.heatmap.fetch_scrobbles",
                new_callable=AsyncMock,
                return_value=_fetch([]),
            ),
            patch("scrobblescope.jobs.fail") as mock_error,
            patch("scrobblescope.jobs.succeed") as mock_results,
        ):
            await _fetch_and_process_heatmap("job-3", "emptyuser")
            mock_error.assert_called_once_with(
                "job-3", "no_scrobbles_in_range", username="emptyuser"
            )
            mock_results.assert_not_called()

    @pytest.mark.asyncio
    async def test_happy_path_stores_correct_result_dict(self):
        """Successful fetch stores a result dict with expected keys and values."""
        # Plays on a known day.
        today = datetime.now(UTC).date()
        yesterday = today - timedelta(days=1)

        stored_result = {}
        completion_events = []

        def _capture_success(job_id, results, message):
            stored_result.update(results)
            completion_events.append(message)
            return True

        with (
            patch("scrobblescope.heatmap.cleanup_expired_cache"),
            patch("scrobblescope.jobs.expire_stale"),
            patch("scrobblescope.jobs.start"),
            patch("scrobblescope.jobs.advance"),
            patch("scrobblescope.jobs.record_stat"),
            patch(
                "scrobblescope.heatmap.fetch_scrobbles",
                new_callable=AsyncMock,
                return_value=_fetch([_play(yesterday), _play(yesterday), _play(today)]),
            ),
            patch(
                "scrobblescope.jobs.succeed",
                side_effect=_capture_success,
            ),
            patch("scrobblescope.jobs.fail") as mock_error,
        ):
            await _fetch_and_process_heatmap("job-4", "happyuser")
            mock_error.assert_not_called()

        # Verify result structure.
        assert stored_result["username"] == "happyuser"
        assert "from_date" in stored_result
        assert "to_date" in stored_result
        assert stored_result["total_scrobbles"] == 3
        assert stored_result["max_count"] == 2  # yesterday had 2
        # Python publishes the KPI figures; the browser renders them.
        assert stored_result["statistics"]["total_plays"]["value"] == 3
        assert stored_result["statistics"]["best_day"]["value"] == {
            "date": yesterday.isoformat(),
            "count": 2,
        }
        assert stored_result["statistics"]["current_streak"]["value"] == 2
        assert stored_result["statistics"]["daily_average"]["value"] == pytest.approx(
            3 / 365
        )
        assert stored_result["daily_counts"][yesterday.isoformat()] == 2
        assert stored_result["daily_counts"][today.isoformat()] == 1
        # The payload and the 100% travel in one call: no window between them.
        assert completion_events == ["Heatmap ready!"]

    @pytest.mark.asyncio
    async def test_success_is_readable_through_repository_at_100_percent(self):
        """A real job exposes its payload whenever progress reports complete."""
        today = datetime.now(UTC).date()
        job_id = jobs.create({"username": "wired-user", "mode": "heatmap"})

        try:
            with (
                patch("scrobblescope.heatmap.cleanup_expired_cache"),
                patch("scrobblescope.jobs.expire_stale"),
                patch(
                    "scrobblescope.heatmap.fetch_scrobbles",
                    new_callable=AsyncMock,
                    return_value=_fetch([_play(today)]),
                ),
            ):
                await _fetch_and_process_heatmap(job_id, "wired-user")

            context = jobs.context(job_id)
            assert context is not None
            assert context["progress"]["progress"] == 100
            assert context["progress"]["error"] is False
            assert context["results"]["username"] == "wired-user"
            assert context["results"]["total_scrobbles"] == 1
            assert context["progress"]["stats"]["pages_received"] == 1
            assert context["progress"]["stats"]["active_days"] == 1
        finally:
            jobs.delete(job_id)

    def test_statistics_reach_the_browser_through_heatmap_data(self, client):
        """
        GIVEN a heatmap job run through the real pipeline: 2 plays yesterday
        and 1 today, stored by ``_fetch_and_process_heatmap``
        WHEN the browser asks /heatmap_data
        THEN the response carries the published statistics with their
        populations, so the whole path (task, store, route) is covered.

        Worked by hand: total 3, best day yesterday with 2, streak 2
        (today and yesterday both have plays).

        Mutation: delete ``"statistics": statistics,`` from the ``jobs.succeed``
        payload in heatmap.py and ``body["statistics"]`` raises KeyError; build
        the /heatmap_data response from named keys that omit ``statistics`` and
        the same line fails.

        Synchronous on purpose: ``client`` keeps its request context open for
        the test's life, and an async test runs in a task whose context copy
        cannot release it at teardown (LookupError). ``asyncio.run`` drives
        the coroutine instead.
        """
        today = datetime.now(UTC).date()
        yesterday = today - timedelta(days=1)
        job_id = jobs.create({"username": "stats-user", "mode": "heatmap"})
        try:
            with (
                patch("scrobblescope.heatmap.cleanup_expired_cache"),
                patch("scrobblescope.jobs.expire_stale"),
                patch(
                    "scrobblescope.heatmap.fetch_scrobbles",
                    new_callable=AsyncMock,
                    return_value=_fetch(
                        [_play(yesterday), _play(yesterday), _play(today)]
                    ),
                ),
            ):
                asyncio.run(_fetch_and_process_heatmap(job_id, "stats-user"))
            body = client.get(f"/heatmap_data?job_id={job_id}").get_json()
        finally:
            jobs.delete(job_id)

        assert body["ready"] is True
        assert body["statistics"]["total_plays"]["value"] == 3
        assert body["statistics"]["current_streak"]["value"] == 2
        assert body["statistics"]["best_day"]["value"]["count"] == 2
        assert all(fact["population"] for fact in body["statistics"].values())

    @pytest.mark.asyncio
    async def test_progress_callback_sends_correct_percentages(self):
        """The progress callback maps fetch phases into 5-80% range."""
        today = datetime.now(UTC).date()

        progress_calls = []

        def _capture_advance(job_id, percent, message, phase=None):
            progress_calls.append(
                {"progress": percent, "message": message, "phase": phase}
            )
            return True

        started = []

        async def _fetch_with_progress(*_args, **kwargs):
            kwargs["progress_cb"](1, 1, 1)
            return _fetch([_play(today)])

        with (
            patch("scrobblescope.heatmap.cleanup_expired_cache"),
            patch("scrobblescope.jobs.expire_stale"),
            patch(
                "scrobblescope.jobs.start",
                side_effect=lambda job_id, message: started.append(message),
            ),
            patch("scrobblescope.jobs.advance", side_effect=_capture_advance),
            patch("scrobblescope.jobs.record_stat"),
            patch(
                "scrobblescope.heatmap.fetch_scrobbles",
                new_callable=AsyncMock,
                side_effect=_fetch_with_progress,
            ),
            patch("scrobblescope.jobs.succeed"),
            patch("scrobblescope.jobs.fail"),
        ):
            await _fetch_and_process_heatmap("job-5", "progressuser")

        # The phase owns the operation name; the live statistic owns N / T.
        assert started == ["Connecting to Last.fm"]
        assert {
            "progress": 5,
            "message": "Fetching your scrobble history from Last.fm",
            "phase": None,
        } in progress_calls
        assert {
            "progress": 80,
            "message": "Counting your daily scrobbles",
            "phase": None,
        } in progress_calls
        page_calls = [
            update
            for update in progress_calls
            if update.get("message") == "Reading your Last.fm history"
        ]
        assert page_calls == [
            {
                "progress": 80,
                "message": "Reading your Last.fm history",
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

    @staticmethod
    def _job():
        return jobs.create({"username": "user", "mode": "heatmap"})

    def test_release_job_slot_called_on_success(self):
        """release_job_slot is called even when the task succeeds."""
        with (
            patch("scrobblescope.heatmap.release_job_slot") as mock_release,
            patch(
                "scrobblescope.heatmap._fetch_and_process_heatmap",
                new_callable=AsyncMock,
            ),
        ):
            heatmap_task(self._job())
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
            patch("scrobblescope.jobs.fail"),
        ):
            # Should NOT raise -- heatmap_task catches exceptions.
            heatmap_task(self._job())
            mock_release.assert_called_once()

    def test_release_job_slot_called_when_event_loop_setup_raises(self):
        """release_job_slot is called even if event loop setup raises (F-B21-1)."""
        with (
            patch(
                "asyncio.set_event_loop", side_effect=RuntimeError("loop setup failed")
            ),
            patch("scrobblescope.heatmap.release_job_slot") as mock_release,
            patch("scrobblescope.jobs.fail"),
        ):
            heatmap_task(self._job())
            mock_release.assert_called_once()

    def test_release_job_slot_called_when_loop_close_raises(self):
        """release_job_slot is called even if loop.close raises."""
        mock_loop = MagicMock()
        mock_loop.run_until_complete.side_effect = lambda coroutine: coroutine.close()
        mock_loop.close.side_effect = RuntimeError("close failed")
        with (
            patch("asyncio.new_event_loop", return_value=mock_loop),
            patch("asyncio.ProactorEventLoop", return_value=mock_loop, create=True),
            patch("asyncio.set_event_loop"),
            patch("scrobblescope.heatmap.release_job_slot") as mock_release,
            patch("scrobblescope.jobs.fail"),
        ):
            with pytest.raises(RuntimeError, match="close failed"):
                heatmap_task(self._job())
            mock_release.assert_called_once()

    def test_unhandled_crash_publishes_internal_error(self):
        """A crash that escapes the pipeline ends the job as internal_error,
        not as a Last.fm outage that never happened (F-SWE-5)."""
        from tests.helpers import TEST_JOB_PARAMS

        job_id = jobs.create(TEST_JOB_PARAMS)
        with (
            patch("scrobblescope.heatmap.release_job_slot"),
            patch(
                "scrobblescope.heatmap._fetch_and_process_heatmap",
                new_callable=AsyncMock,
                side_effect=ZeroDivisionError("ours"),
            ),
        ):
            heatmap_task(job_id)

        progress = jobs.progress(job_id)
        assert progress["error"] is True
        assert progress["error_code"] == "internal_error"
        assert progress["error_source"] == "internal"
        assert progress["retryable"] is False

    def test_user_not_found_crash_publishes_user_not_found(self):
        """A Last.fm 404 (UserNotFoundError) escaping the pipeline is classified
        as user_not_found, not blamed on the app as internal_error (Finding 1)."""
        from tests.helpers import TEST_JOB_PARAMS

        job_id = jobs.create(TEST_JOB_PARAMS)
        with (
            patch("scrobblescope.heatmap.release_job_slot"),
            patch(
                "scrobblescope.heatmap._fetch_and_process_heatmap",
                new_callable=AsyncMock,
                side_effect=UserNotFoundError(),
            ),
        ):
            heatmap_task(job_id)

        progress = jobs.progress(job_id)
        assert progress["error"] is True
        assert progress["error_code"] == "user_not_found"
        assert progress["error_source"] == "lastfm"
        assert progress["retryable"] is False

    def test_lastfm_outage_crash_publishes_lastfm_unavailable(self):
        """A Last.fm outage escaping the pipeline is classified by type as
        lastfm_unavailable: retryable, blamed on Last.fm.

        Planted defect: classify every escaped exception as internal_error.
        The thread entry point takes the job id alone (PR #3): the username is
        read from the job record."""
        job_id = jobs.create({"username": "user", "mode": "heatmap"})
        with (
            patch("scrobblescope.heatmap.release_job_slot"),
            patch(
                "scrobblescope.heatmap._fetch_and_process_heatmap",
                new_callable=AsyncMock,
                side_effect=ProviderError("lastfm", "unavailable"),
            ),
        ):
            heatmap_task(job_id)

        progress = jobs.progress(job_id)
        assert progress["error_code"] == "lastfm_unavailable"
        assert progress["error_source"] == "lastfm"
        assert progress["retryable"] is True

    def test_untyped_not_found_text_is_ours_not_user_not_found(self):
        """An unrelated ValueError whose text reads "user ... not found" is not
        user_not_found: classification is by type (F-B23-16)."""
        from tests.helpers import TEST_JOB_PARAMS

        job_id = jobs.create(TEST_JOB_PARAMS)
        with (
            patch("scrobblescope.heatmap.release_job_slot"),
            patch(
                "scrobblescope.heatmap._fetch_and_process_heatmap",
                new_callable=AsyncMock,
                side_effect=ValueError("User 'ghost' not found on Last.fm"),
            ),
        ):
            heatmap_task(job_id)

        progress = jobs.progress(job_id)
        assert progress["error_code"] == "internal_error"
        assert progress["retryable"] is False

    def test_the_username_comes_from_the_job_record(self):
        """heatmap_task takes only the job id and reads the name from the record.

        Mutation: pass a literal name to the pipeline and this fails.
        """
        job_id = jobs.create({"username": "recorded", "mode": "heatmap"})
        with (
            patch("scrobblescope.heatmap.release_job_slot"),
            patch(
                "scrobblescope.heatmap._fetch_and_process_heatmap",
                new_callable=AsyncMock,
            ) as mock_pipeline,
        ):
            heatmap_task(job_id)

        mock_pipeline.assert_awaited_once_with(job_id, "recorded")

    def test_a_vanished_job_runs_nothing_and_frees_its_slot(self):
        """Mutation: drop the release in the vanished-job branch and the slot leaks."""
        with (
            patch("scrobblescope.heatmap.release_job_slot") as mock_release,
            patch(
                "scrobblescope.heatmap._fetch_and_process_heatmap",
                new_callable=AsyncMock,
            ) as mock_pipeline,
        ):
            heatmap_task("no-such-job")

        mock_pipeline.assert_not_called()
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

    def test_internal_error_exists(self):
        """internal_error is registered for faults that are ours (F-SWE-5)."""
        from scrobblescope.errors import ERROR_CODES

        code = ERROR_CODES.get("internal_error")
        assert code is not None, "internal_error not in ERROR_CODES"
        assert code["source"] == "internal"
        assert code["retryable"] is False
        assert "{username}" not in code["message"]


class TestHeatmapPhaseProgress:
    """Verify phase reporting during heatmap fetch and clear at completion."""

    @pytest.mark.asyncio
    async def test_heatmap_lastfm_phase_and_cleared_at_completion(self):
        """Heatmap pipeline reports exact Last.fm phase and clears phase at completion."""
        job_id = jobs.create({"username": "user", "mode": "heatmap"})
        observed_phase = None

        today = datetime.now(UTC).date()

        async def fake_fetch(username, window, progress_cb=None):
            nonlocal observed_phase
            if progress_cb:
                progress_cb(23, 102, 23)
                observed_phase = jobs.progress(job_id).get("phase")
            return _fetch([_play(today)], expected=102, received=23)

        with (
            patch("scrobblescope.heatmap.cleanup_expired_cache"),
            patch("scrobblescope.jobs.expire_stale"),
            patch(
                "scrobblescope.heatmap.fetch_scrobbles",
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
        final_progress = jobs.progress(job_id)
        assert "phase" not in final_progress
