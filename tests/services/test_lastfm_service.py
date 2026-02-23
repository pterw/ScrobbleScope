from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scrobblescope.lastfm import (
    check_user_exists,
    fetch_all_recent_tracks_async,
    fetch_recent_tracks_page_async,
)
from tests.helpers import NoopAsyncContext, make_response_context


@pytest.mark.asyncio
async def test_check_user_exists_success():
    """
    GIVEN a username that exists
    WHEN check_user_exists is called
    THEN it should return exists=True with a registered_year.
    """
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "user": {
                "name": "testuser",
                "registered": {"unixtime": "1451606400", "#text": "2016-01-01 00:00"},
            }
        }
        mock_get.return_value.__aenter__.return_value = mock_response

        result = await check_user_exists("any_user")
        assert result["exists"] is True
        assert result["registered_year"] == 2016


@pytest.mark.asyncio
async def test_check_user_does_not_exist():
    """
    GIVEN a username that does NOT exist
    WHEN check_user_exists is called
    THEN it should return exists=False.
    """
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_get.return_value.__aenter__.return_value = mock_response

        result = await check_user_exists("nonexistent_user")
        assert result["exists"] is False
        assert result["registered_year"] is None


@pytest.mark.asyncio
async def test_fetch_recent_tracks_page_retries_429_then_succeeds():
    """
    GIVEN Last.fm page fetch receives a 429 then a 200 response
    WHEN fetch_recent_tracks_page_async runs
    THEN it should retry once and return the successful payload.
    """
    session = MagicMock()

    resp_429 = AsyncMock()
    resp_429.status = 429
    resp_429.headers = {"Retry-After": "1"}

    payload = {"recenttracks": {"track": [], "@attr": {"totalPages": "1"}}}
    resp_200 = AsyncMock()
    resp_200.status = 200
    resp_200.json = AsyncMock(return_value=payload)

    session.get.side_effect = [
        make_response_context(resp_429),
        make_response_context(resp_200),
    ]

    with (
        patch("scrobblescope.lastfm.get_cached_response", return_value=None),
        patch(
            "scrobblescope.lastfm.get_lastfm_limiter", return_value=NoopAsyncContext()
        ),
        patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
    ):
        result = await fetch_recent_tracks_page_async(
            session, "flounder14", 1, 2, page=1, retries=3
        )

    assert result == payload
    assert session.get.call_count == 2
    assert mock_sleep.await_count >= 1


@pytest.mark.asyncio
async def test_fetch_recent_tracks_page_404_raises_user_not_found():
    """
    GIVEN Last.fm responds with 404 for a page fetch
    WHEN fetch_recent_tracks_page_async runs
    THEN it should raise ValueError for user-not-found classification.
    """
    session = MagicMock()
    resp_404 = AsyncMock()
    resp_404.status = 404
    session.get.return_value = make_response_context(resp_404)

    with (
        patch("scrobblescope.lastfm.get_cached_response", return_value=None),
        patch(
            "scrobblescope.lastfm.get_lastfm_limiter", return_value=NoopAsyncContext()
        ),
    ):
        with pytest.raises(ValueError, match="not found"):
            await fetch_recent_tracks_page_async(
                session, "ghost_user_xyz", 1, 2, page=1, retries=1
            )


@pytest.mark.asyncio
async def test_check_user_exists_missing_registration_data():
    """
    GIVEN a 200 OK response with an empty body (no user/registered keys)
    WHEN check_user_exists is called
    THEN it should return exists=True with registered_year=None.

    Covers the missing-key fallback path now inlined inside check_user_exists
    (previously tested via _extract_registered_year in test_domain.py).
    """
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {}
        mock_get.return_value.__aenter__.return_value = mock_response

        result = await check_user_exists("sparse_user")
        assert result["exists"] is True
        assert result["registered_year"] is None


# --- progress_cb tests for fetch_all_recent_tracks_async ---


def _make_page(total_pages, tracks=None):
    """Build a minimal Last.fm page payload."""
    return {
        "recenttracks": {
            "@attr": {"totalPages": str(total_pages)},
            "track": tracks or [],
        }
    }


@pytest.mark.asyncio
async def test_progress_cb_called_per_page():
    """
    GIVEN a 3-page fetch with progress_cb provided
    WHEN fetch_all_recent_tracks_async runs
    THEN progress_cb is invoked 3 times: (1,3), (2,3), (3,3).
    """
    cb = MagicMock()
    page_payload = _make_page(3)

    with (
        patch(
            "scrobblescope.lastfm.fetch_recent_tracks_page_async",
            new_callable=AsyncMock,
            return_value=page_payload,
        ),
        patch("scrobblescope.lastfm.create_optimized_session") as mock_session,
    ):
        mock_session.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
        mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

        pages, meta = await fetch_all_recent_tracks_async("user", 0, 1, progress_cb=cb)

    assert cb.call_count == 3
    # First call is always (1, total_pages) after page 1
    cb.assert_any_call(1, 3)
    # Final call should report all pages done
    cb.assert_any_call(3, 3)
    assert meta["status"] == "ok"


@pytest.mark.asyncio
async def test_progress_cb_single_page():
    """
    GIVEN a 1-page fetch with progress_cb provided
    WHEN fetch_all_recent_tracks_async runs
    THEN progress_cb is invoked exactly once with (1, 1).
    """
    cb = MagicMock()
    page_payload = _make_page(1)

    with (
        patch(
            "scrobblescope.lastfm.fetch_recent_tracks_page_async",
            new_callable=AsyncMock,
            return_value=page_payload,
        ),
        patch("scrobblescope.lastfm.create_optimized_session") as mock_session,
    ):
        mock_session.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
        mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

        pages, meta = await fetch_all_recent_tracks_async("user", 0, 1, progress_cb=cb)

    cb.assert_called_once_with(1, 1)
    assert len(pages) == 1


@pytest.mark.asyncio
async def test_progress_cb_none_uses_gather_path():
    """
    GIVEN a multi-page fetch with progress_cb=None
    WHEN fetch_all_recent_tracks_async runs
    THEN fetch_pages_batch_async is called (gather path), not as_completed.
    """
    page_payload = _make_page(2)

    with (
        patch(
            "scrobblescope.lastfm.fetch_recent_tracks_page_async",
            new_callable=AsyncMock,
            return_value=page_payload,
        ),
        patch("scrobblescope.lastfm.create_optimized_session") as mock_session,
        patch(
            "scrobblescope.lastfm.fetch_pages_batch_async",
            new_callable=AsyncMock,
            return_value=[page_payload],
        ) as mock_batch,
    ):
        mock_session.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
        mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

        pages, meta = await fetch_all_recent_tracks_async("user", 0, 1)

    mock_batch.assert_called_once()
    assert meta["status"] == "ok"


@pytest.mark.asyncio
async def test_progress_cb_counts_failed_pages():
    """
    GIVEN a 3-page fetch where page 3 fails (returns None)
    WHEN fetch_all_recent_tracks_async runs with progress_cb
    THEN progress_cb still fires for the failed page and metadata shows partial.
    """
    cb = MagicMock()
    page_payload = _make_page(3)

    side_effects = [page_payload, page_payload, None]  # page 1, 2 ok; 3 fails

    with (
        patch(
            "scrobblescope.lastfm.fetch_recent_tracks_page_async",
            new_callable=AsyncMock,
            side_effect=side_effects,
        ),
        patch("scrobblescope.lastfm.create_optimized_session") as mock_session,
    ):
        mock_session.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
        mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

        pages, meta = await fetch_all_recent_tracks_async("user", 0, 1, progress_cb=cb)

    # All 3 pages trigger callbacks (1 initial + 2 remaining)
    assert cb.call_count == 3
    assert meta["status"] == "partial"
    assert meta["pages_dropped"] == 1
    # Only 2 successful pages collected
    assert len(pages) == 2
