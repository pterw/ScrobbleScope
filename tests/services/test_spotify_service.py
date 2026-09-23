import logging
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scrobblescope.spotify import (
    album_metadata_from_details,
    fetch_spotify_access_token,
    fetch_spotify_album_details_batch,
    fetch_spotify_artist_spotlight,
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
    # A server error is not an endpoint removal: fetching album by album
    # would multiply the load on a struggling upstream (F-B21-59).
    assert session.get.call_count == 1


def _single_album_response(album_id):
    """Return a 200 response for GET /v1/albums/{album_id}."""
    resp = AsyncMock()
    resp.status = 200
    resp.json = AsyncMock(return_value={"id": album_id, "release_date": "2020-01-01"})
    return resp


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [403, 404])
async def test_fetch_spotify_album_details_batch_falls_back_to_single_album_calls(
    status,
):
    """
    GIVEN the Get Several Albums call answers 403 or 404, the status an endpoint
        Spotify removed from Development Mode apps returns (F-B21-59)
    WHEN fetch_spotify_album_details_batch runs
    THEN it fetches each album from GET /v1/albums/{id}, returns the same
        id-keyed dict, and reports the fallback once through on_fallback.
    """
    session = MagicMock()
    removed = AsyncMock()
    removed.status = status
    removed.text = AsyncMock(return_value="endpoint removed")

    def route(url, **kwargs):
        if url.endswith("/v1/albums"):
            return make_response_context(removed)
        return make_response_context(_single_album_response(url.rsplit("/", 1)[1]))

    session.get.side_effect = route
    on_fallback = MagicMock()

    with (
        patch(
            "scrobblescope.spotify.get_spotify_limiter", return_value=NoopAsyncContext()
        ),
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        result = await fetch_spotify_album_details_batch(
            session, ["id_1", "id_2"], "token", retries=2, on_fallback=on_fallback
        )

    assert result == {
        "id_1": {"id": "id_1", "release_date": "2020-01-01"},
        "id_2": {"id": "id_2", "release_date": "2020-01-01"},
    }
    single_urls = sorted(
        call.args[0]
        for call in session.get.call_args_list
        if not call.args[0].endswith("/v1/albums")
    )
    assert single_urls == [
        "https://api.spotify.com/v1/albums/id_1",
        "https://api.spotify.com/v1/albums/id_2",
    ]
    on_fallback.assert_called_once_with(status)


@pytest.mark.asyncio
async def test_single_album_fallback_retries_429_and_skips_missing_albums():
    """
    GIVEN the batch call is removed, one single-album call answers 429 then 200,
        and another answers 404
    WHEN fetch_spotify_album_details_batch runs
    THEN the rate-limited album is retried and returned, and the missing album
        is left out rather than failing the batch.
    """
    session = MagicMock()
    removed = AsyncMock()
    removed.status = 403
    removed.text = AsyncMock(return_value="endpoint removed")
    limited = AsyncMock()
    limited.status = 429
    limited.headers = {"Retry-After": "1"}
    missing = AsyncMock()
    missing.status = 404
    responses = {
        "https://api.spotify.com/v1/albums": [removed],
        "https://api.spotify.com/v1/albums/id_1": [
            limited,
            _single_album_response("id_1"),
        ],
        "https://api.spotify.com/v1/albums/gone": [missing],
    }

    def route(url, **kwargs):
        return make_response_context(responses[url].pop(0))

    session.get.side_effect = route

    with (
        patch(
            "scrobblescope.spotify.get_spotify_limiter", return_value=NoopAsyncContext()
        ),
        patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
    ):
        result = await fetch_spotify_album_details_batch(
            session, ["id_1", "gone"], "token", retries=3
        )

    assert result == {"id_1": {"id": "id_1", "release_date": "2020-01-01"}}
    assert mock_sleep.await_count >= 1


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
@pytest.mark.parametrize(
    ("client_id", "client_secret"),
    [(None, "test_secret"), ("test_id", None), ("", "test_secret")],
    ids=["id-missing", "secret-missing", "id-empty"],
)
async def test_fetch_spotify_access_token_returns_none_without_credentials(
    client_id, client_secret, caplog
):
    """
    GIVEN a Spotify credential is missing or empty
    WHEN fetch_spotify_access_token is called with an expired cache
    THEN it returns None -- the same answer as a rejected token request, so
    callers fall back to Deezer -- without making any HTTP request. It used
    to `assert`, which `python -O` strips (F-B22-2) and which otherwise
    raised past that fallback and failed the whole job.
    """
    fake_cache = {"token": None, "expires_at": 0}
    with (
        patch("scrobblescope.spotify.spotify_token_cache", fake_cache),
        patch("scrobblescope.spotify.SPOTIFY_CLIENT_ID", client_id),
        patch("scrobblescope.spotify.SPOTIFY_CLIENT_SECRET", client_secret),
        patch("scrobblescope.spotify.create_optimized_session") as session,
        caplog.at_level(logging.ERROR),
    ):
        token = await fetch_spotify_access_token()

    assert token is None
    session.assert_not_called()
    assert "credentials are not configured" in caplog.text


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


@pytest.mark.asyncio
@pytest.mark.parametrize("by_id", [True, False])
@pytest.mark.parametrize(
    "artist",
    [
        {},
        {
            "id": "found",
            "name": "Found",
            "images": [{"url": "photo"}],
            "external_urls": {"spotify": "link"},
        },
    ],
)
async def test_artist_spotlight_parses_details_and_missing_fields(by_id, artist):
    """Both lookup paths preserve sparse-field fallbacks and image metadata."""
    response = AsyncMock(status=200)
    response.json.return_value = artist if by_id else {"artists": {"items": [artist]}}
    session = MagicMock()
    session.get.return_value = make_response_context(response)
    with patch(
        "scrobblescope.spotify.get_spotify_limiter", return_value=NoopAsyncContext()
    ):
        result = await fetch_spotify_artist_spotlight(
            session, "Requested", "requested-id" if by_id else None, "token"
        )
    assert result == {
        "name": artist.get("name", "Requested"),
        "artist_id": artist.get("id", "requested-id" if by_id else None),
        "image_url": "photo" if artist else None,
        "spotify_url": "link" if artist else None,
    }


@pytest.mark.asyncio
@pytest.mark.parametrize("items", [[], [{"name": "Search match"}]])
async def test_artist_spotlight_falls_back_from_failed_id_lookup(items):
    """An unsuccessful ID lookup searches by name, including no-match results."""
    failed = AsyncMock(status=404)
    found = AsyncMock(status=200)
    found.json.return_value = {"artists": {"items": items}}
    session = MagicMock()
    session.get.side_effect = [
        make_response_context(failed),
        make_response_context(found),
    ]
    with patch(
        "scrobblescope.spotify.get_spotify_limiter", return_value=NoopAsyncContext()
    ):
        result = await fetch_spotify_artist_spotlight(
            session, "Requested", "missing", "token"
        )
    assert result == (
        {
            "name": "Search match",
            "artist_id": None,
            "image_url": None,
            "spotify_url": None,
        }
        if items
        else None
    )
    assert session.get.call_args.kwargs["params"]["q"] == "artist:Requested"


@pytest.mark.asyncio
async def test_artist_spotlight_network_error_preserves_fallback(caplog):
    """Transport failures log a warning and let the route retain album art."""
    session = MagicMock()
    session.get.side_effect = RuntimeError("transport unavailable")
    with patch(
        "scrobblescope.spotify.get_spotify_limiter", return_value=NoopAsyncContext()
    ):
        result = await fetch_spotify_artist_spotlight(
            session, "Requested", token="token"
        )
    assert result is None
    assert "transport unavailable" in caplog.text


def test_album_metadata_from_details_translates_one_payload():
    """One Spotify album object becomes the provider contract, whole."""
    from scrobblescope.domain import normalize_track_name
    from scrobblescope.enrichment import AlbumMetadata

    details = {
        "release_date": "1977-02-04",
        "images": [
            {"url": "https://i.scdn.co/cover-large.jpg"},
            {"url": "https://i.scdn.co/cover-small.jpg"},
        ],
        "external_urls": {"spotify": "https://open.spotify.com/album/sp1"},
        "tracks": {
            "items": [
                {"name": "Dreams - 2004 Remaster", "duration_ms": 257800},
                {"name": "Songbird", "duration_ms": 200000},
            ]
        },
    }

    assert album_metadata_from_details("sp1", details) == AlbumMetadata(
        provider="spotify",
        album_id="sp1",
        url="https://open.spotify.com/album/sp1",
        release_date="1977-02-04",
        image_url="https://i.scdn.co/cover-large.jpg",
        track_durations={
            normalize_track_name("Dreams - 2004 Remaster"): 257,
            normalize_track_name("Songbird"): 200,
        },
    )


@pytest.mark.parametrize("images", [None, []], ids=["no-key", "empty"])
def test_album_metadata_from_details_degrades_field_by_field(images):
    """A sparse payload yields defaults, never an exception (global rule 6)."""
    details = {} if images is None else {"images": images}

    meta = album_metadata_from_details("sp2", details)

    assert meta.url == "https://open.spotify.com/album/sp2"
    assert meta.release_date == ""
    assert meta.image_url is None
    assert meta.track_durations == {}
