from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scrobblescope.lastfm import check_user_exists, fetch_recent_tracks_page_async
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
