from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scrobblescope.spotify import (
    fetch_spotify_album_details_batch,
    search_for_spotify_album_id,
)
from tests.helpers import NoopAsyncContext, make_response_context


@pytest.mark.asyncio
async def test_search_for_spotify_album_id_retries_429_then_returns_id():
    """
    GIVEN Spotify search returns 429 and then a valid 200 payload
    WHEN search_for_spotify_album_id runs
    THEN it should retry and return the matched album ID.
    """
    session = MagicMock()

    resp_429 = AsyncMock()
    resp_429.status = 429
    resp_429.headers = {"Retry-After": "1"}

    resp_200 = AsyncMock()
    resp_200.status = 200
    resp_200.json = AsyncMock(
        return_value={"albums": {"items": [{"id": "spotify_album_123"}]}}
    )

    session.get.side_effect = [
        make_response_context(resp_429),
        make_response_context(resp_200),
    ]

    with (
        patch(
            "scrobblescope.spotify.get_spotify_limiter", return_value=NoopAsyncContext()
        ),
        patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
    ):
        result = await search_for_spotify_album_id(session, "Artist", "Album", "token")

    assert result == "spotify_album_123"
    assert session.get.call_count == 2
    assert mock_sleep.await_count >= 1


@pytest.mark.asyncio
async def test_fetch_spotify_album_details_batch_retries_429_then_succeeds():
    """
    GIVEN Spotify album-details batch fetch returns 429 then 200
    WHEN fetch_spotify_album_details_batch runs
    THEN it should retry and return album details keyed by Spotify ID.
    """
    session = MagicMock()

    resp_429 = AsyncMock()
    resp_429.status = 429
    resp_429.headers = {"Retry-After": "1"}

    resp_200 = AsyncMock()
    resp_200.status = 200
    resp_200.json = AsyncMock(
        return_value={"albums": [{"id": "id_1", "name": "Album One"}]}
    )

    session.get.side_effect = [
        make_response_context(resp_429),
        make_response_context(resp_200),
    ]

    with (
        patch(
            "scrobblescope.spotify.get_spotify_limiter", return_value=NoopAsyncContext()
        ),
        patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
    ):
        result = await fetch_spotify_album_details_batch(
            session, ["id_1"], "token", retries=2
        )

    assert result == {"id_1": {"id": "id_1", "name": "Album One"}}
    assert session.get.call_count == 2
    assert mock_sleep.await_count >= 1


@pytest.mark.asyncio
async def test_fetch_spotify_album_details_batch_non_200_returns_empty_dict():
    """
    GIVEN Spotify album-details batch fetch returns a non-200 non-429 status
    WHEN fetch_spotify_album_details_batch runs
    THEN it should return an empty dict without retry sleep.
    """
    session = MagicMock()

    resp_500 = AsyncMock()
    resp_500.status = 500
    resp_500.text = AsyncMock(return_value="upstream failure")
    session.get.return_value = make_response_context(resp_500)

    with (
        patch(
            "scrobblescope.spotify.get_spotify_limiter", return_value=NoopAsyncContext()
        ),
        patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
    ):
        result = await fetch_spotify_album_details_batch(
            session, ["id_1"], "token", retries=2
        )

    assert result == {}
    assert mock_sleep.await_count == 0
