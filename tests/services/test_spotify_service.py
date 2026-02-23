import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scrobblescope.spotify import (
    fetch_spotify_access_token,
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


# ------------------------------------------------------------------ #
# fetch_spotify_access_token tests                                     #
# ------------------------------------------------------------------ #


@pytest.mark.asyncio
async def test_fetch_spotify_access_token_returns_cached_when_valid():
    """
    GIVEN a cached token whose expires_at is in the future
    WHEN fetch_spotify_access_token is called
    THEN it should return the cached token without making any HTTP request.
    """
    fake_cache = {"token": "cached_tok_123", "expires_at": time.time() + 3600}
    with patch("scrobblescope.spotify.spotify_token_cache", fake_cache):
        token = await fetch_spotify_access_token()

    assert token == "cached_tok_123"


@pytest.mark.asyncio
async def test_fetch_spotify_access_token_refreshes_expired_token():
    """
    GIVEN an expired token cache
    WHEN fetch_spotify_access_token is called
    THEN it should POST to the Spotify token endpoint and update the cache.
    """
    fake_cache = {"token": None, "expires_at": 0}

    resp_200 = AsyncMock()
    resp_200.status = 200
    resp_200.json = AsyncMock(
        return_value={"access_token": "fresh_tok_456", "expires_in": 3600}
    )

    mock_session = MagicMock()
    mock_session.post.return_value = make_response_context(resp_200)
    mock_session_ctx = MagicMock()
    mock_session_ctx.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_ctx.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("scrobblescope.spotify.spotify_token_cache", fake_cache),
        patch("scrobblescope.spotify.SPOTIFY_CLIENT_ID", "test_id"),
        patch("scrobblescope.spotify.SPOTIFY_CLIENT_SECRET", "test_secret"),
        patch(
            "scrobblescope.spotify.create_optimized_session",
            return_value=mock_session_ctx,
        ),
    ):
        token = await fetch_spotify_access_token()

    assert token == "fresh_tok_456"
    assert fake_cache["token"] == "fresh_tok_456"
    assert fake_cache["expires_at"] > time.time()


@pytest.mark.asyncio
async def test_fetch_spotify_access_token_returns_none_on_non_200():
    """
    GIVEN the Spotify token endpoint returns a non-200 status
    WHEN fetch_spotify_access_token is called
    THEN it should log the error and return None.
    """
    fake_cache = {"token": None, "expires_at": 0}

    resp_403 = AsyncMock()
    resp_403.status = 403

    mock_session = MagicMock()
    mock_session.post.return_value = make_response_context(resp_403)
    mock_session_ctx = MagicMock()
    mock_session_ctx.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_ctx.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("scrobblescope.spotify.spotify_token_cache", fake_cache),
        patch("scrobblescope.spotify.SPOTIFY_CLIENT_ID", "test_id"),
        patch("scrobblescope.spotify.SPOTIFY_CLIENT_SECRET", "test_secret"),
        patch(
            "scrobblescope.spotify.create_optimized_session",
            return_value=mock_session_ctx,
        ),
    ):
        token = await fetch_spotify_access_token()

    assert token is None


@pytest.mark.asyncio
async def test_fetch_spotify_access_token_asserts_on_missing_credentials():
    """
    GIVEN SPOTIFY_CLIENT_ID is None
    WHEN fetch_spotify_access_token is called with an expired cache
    THEN it should raise AssertionError before making any HTTP request.
    """
    fake_cache = {"token": None, "expires_at": 0}
    with (
        patch("scrobblescope.spotify.spotify_token_cache", fake_cache),
        patch("scrobblescope.spotify.SPOTIFY_CLIENT_ID", None),
        pytest.raises(AssertionError, match="SPOTIFY_CLIENT_ID not set"),
    ):
        await fetch_spotify_access_token()


# ------------------------------------------------------------------ #
# search_for_spotify_album_id unhappy-path tests                       #
# ------------------------------------------------------------------ #


@pytest.mark.asyncio
async def test_search_returns_none_on_empty_results():
    """
    GIVEN Spotify search returns 200 with an empty items list
    WHEN search_for_spotify_album_id runs
    THEN it should return None (no match found).
    """
    session = MagicMock()

    resp_200 = AsyncMock()
    resp_200.status = 200
    resp_200.json = AsyncMock(return_value={"albums": {"items": []}})

    session.get.return_value = make_response_context(resp_200)

    with patch(
        "scrobblescope.spotify.get_spotify_limiter", return_value=NoopAsyncContext()
    ):
        result = await search_for_spotify_album_id(session, "Artist", "Album", "token")

    assert result is None


@pytest.mark.asyncio
async def test_search_returns_none_on_non_200_non_429():
    """
    GIVEN Spotify search returns a 500 error (not 429)
    WHEN search_for_spotify_album_id runs
    THEN it should return None without retrying (done=True on non-429).
    """
    session = MagicMock()

    resp_500 = AsyncMock()
    resp_500.status = 500

    session.get.return_value = make_response_context(resp_500)

    with patch(
        "scrobblescope.spotify.get_spotify_limiter", return_value=NoopAsyncContext()
    ):
        result = await search_for_spotify_album_id(session, "Artist", "Album", "token")

    assert result is None
    # Non-429 errors return done=True immediately, so only 1 call
    assert session.get.call_count == 1


@pytest.mark.asyncio
async def test_search_succeeds_on_first_try():
    """
    GIVEN Spotify search returns 200 with a valid album on the first attempt
    WHEN search_for_spotify_album_id runs
    THEN it should return the album ID with exactly 1 HTTP call and no sleeps.
    """
    session = MagicMock()

    resp_200 = AsyncMock()
    resp_200.status = 200
    resp_200.json = AsyncMock(
        return_value={"albums": {"items": [{"id": "direct_hit_123"}]}}
    )

    session.get.return_value = make_response_context(resp_200)

    with (
        patch(
            "scrobblescope.spotify.get_spotify_limiter", return_value=NoopAsyncContext()
        ),
        patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
    ):
        result = await search_for_spotify_album_id(session, "Artist", "Album", "token")

    assert result == "direct_hit_123"
    assert session.get.call_count == 1
    assert mock_sleep.await_count == 0
