import logging
import time
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from scrobblescope.errors import ProviderError
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
    GIVEN Spotify album-details batch fetch returns a non-200, non-429,
    non-5xx status (a 400: Spotify answered, refusing)
    WHEN fetch_spotify_album_details_batch runs
    THEN it should return an empty dict without retry sleep.
    """
    session = MagicMock()

    resp_400 = AsyncMock()
    resp_400.status = 400
    resp_400.text = AsyncMock(return_value="upstream failure")
    session.get.return_value = make_response_context(resp_400)

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
    # A refusal is not an endpoint removal: fetching album by album would
    # multiply the load for nothing (F-B21-59).
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
    GIVEN Spotify search returns a 404 (not 429, not a 5xx)
    WHEN search_for_spotify_album_id runs
    THEN it should return None without retrying (done=True on a client error).
    """
    session = MagicMock()

    resp_404 = AsyncMock()
    resp_404.status = 404

    session.get.return_value = make_response_context(resp_404)

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
    assert "Error in spotify.artist_spotlight: RuntimeError" in caplog.text
    # The message (an HTTP client's carries the request URL) and the artist
    # name stay out of the line.
    assert "transport unavailable" not in caplog.text
    assert "Requested" not in caplog.text


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


_LEAK_ALBUM = "Zqxv Distinctive Album"
_LEAK_ARTIST = "Wjkl Distinctive Artist"


def _assert_no_names_logged(caplog):
    """No record, at any level, carries the listener's album or artist."""
    assert caplog.records, "the failure path logged nothing; the test proves nothing"
    for record in caplog.records:
        text = record.getMessage()
        assert _LEAK_ALBUM not in text, text
        assert _LEAK_ARTIST not in text, text


@pytest.mark.asyncio
async def test_search_failure_lines_carry_no_album_or_artist(caplog):
    """
    GIVEN Spotify search answers 429 twice and then the transport raises with
        the query text in its message
    WHEN search_for_spotify_album_id gives up
    THEN neither the warning nor the error lines name the album or artist.
    """
    session = MagicMock()

    def next_response(*args, **kwargs):
        if session.get.call_count <= 2:
            resp = AsyncMock()
            resp.status = 429
            resp.headers = {"Retry-After": "1"}
            return make_response_context(resp)
        raise aiohttp.ClientConnectionError(f"failed q={_LEAK_ARTIST} {_LEAK_ALBUM}")

    session.get.side_effect = next_response

    with (
        patch(
            "scrobblescope.spotify.get_spotify_limiter", return_value=NoopAsyncContext()
        ),
        patch("asyncio.sleep", new_callable=AsyncMock),
        caplog.at_level(logging.DEBUG),
    ):
        with pytest.raises(ProviderError):
            await search_for_spotify_album_id(
                session, _LEAK_ARTIST, _LEAK_ALBUM, "token"
            )

    assert "Spotify 429 on spotify.search" in caplog.text
    assert "Error in spotify.search: ClientConnectionError" in caplog.text
    _assert_no_names_logged(caplog)


# --- typed failures: Spotify is required, so an unanswered search is not a miss --


def _search_with(session):
    return search_for_spotify_album_id(session, "Artist", "Album", "token")


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", ["status_500", "timeout"])
async def test_search_raises_spotify_unavailable_when_spotify_cannot_answer(failure):
    """
    GIVEN Spotify search answers 500 (or times out) on every attempt
    WHEN search_for_spotify_album_id runs
    THEN every attempt is made and it raises ProviderError spotify_unavailable,
    retryable, instead of returning None as "no match".
    """
    session = MagicMock()
    if failure == "status_500":
        resp = AsyncMock()
        resp.status = 500
        session.get.return_value = make_response_context(resp)
    else:
        session.get.side_effect = TimeoutError()

    with (
        patch(
            "scrobblescope.spotify.get_spotify_limiter", return_value=NoopAsyncContext()
        ),
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        with pytest.raises(ProviderError) as excinfo:
            await _search_with(session)

    assert excinfo.value.code == "spotify_unavailable"
    assert session.get.call_count == 3


@pytest.mark.asyncio
async def test_search_throttled_past_the_cap_raises_rate_limited_not_no_match():
    """
    GIVEN Spotify search answers 429 with a Retry-After far above the cap
    WHEN search_for_spotify_album_id runs
    THEN it raises ProviderError spotify_rate_limited after one call; before,
    it returned None and the album was recorded unmatched (Codex 4140219720).
    """
    session = MagicMock()
    resp = AsyncMock()
    resp.status = 429
    resp.headers = {"Retry-After": "86400"}
    session.get.return_value = make_response_context(resp)

    with patch(
        "scrobblescope.spotify.get_spotify_limiter", return_value=NoopAsyncContext()
    ):
        with pytest.raises(ProviderError) as excinfo:
            await _search_with(session)

    assert excinfo.value.code == "spotify_rate_limited"
    assert session.get.call_count == 1


@pytest.mark.asyncio
async def test_search_retries_a_malformed_retry_after():
    """
    GIVEN Spotify answers 429 with a non-numeric Retry-After, then a match
    WHEN search_for_spotify_album_id runs
    THEN the bad header is retried after the default wait and the id returned.
    """
    session = MagicMock()
    throttled = AsyncMock()
    throttled.status = 429
    throttled.headers = {"Retry-After": "Wed, 21 Oct 2026 07:28:00 GMT"}
    found = AsyncMock()
    found.status = 200
    found.json = AsyncMock(return_value={"albums": {"items": [{"id": "sp1"}]}})
    session.get.side_effect = [
        make_response_context(throttled),
        make_response_context(found),
    ]

    with (
        patch(
            "scrobblescope.spotify.get_spotify_limiter", return_value=NoopAsyncContext()
        ),
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        assert await _search_with(session) == "sp1"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "failure",
    [TimeoutError(), aiohttp.ClientConnectionError("no route")],
    ids=["timeout", "connection_error"],
)
async def test_fetch_spotify_access_token_returns_none_on_transport_failure(failure):
    """
    GIVEN the Spotify token endpoint times out or refuses the connection
    WHEN fetch_spotify_access_token is called
    THEN it returns None, exactly as for a non-200 answer, so the caller
    degrades to Deezer; before, the exception escaped and the job failed as
    "our bug" (internal_error, not retryable).
    """
    fake_cache = {"token": None, "expires_at": 0}
    mock_session = MagicMock()
    mock_session.post.side_effect = failure
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
    assert fake_cache["token"] is None


def _status_response(status):
    resp = AsyncMock()
    resp.status = status
    resp.text = AsyncMock(return_value="upstream failure")
    return resp


@pytest.mark.asyncio
async def test_fetch_spotify_album_details_batch_5xx_reports_every_id_unanswered():
    """
    GIVEN the batch details endpoint answers 500 on every attempt
    WHEN fetch_spotify_album_details_batch runs
    THEN it retries, returns no details and lists every requested id as
    unanswered: Spotify did not answer, which is not "no details".
    """
    session = MagicMock()
    session.get.return_value = make_response_context(_status_response(500))

    with (
        patch(
            "scrobblescope.spotify.get_spotify_limiter", return_value=NoopAsyncContext()
        ),
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        result = await fetch_spotify_album_details_batch(
            session, ["id_1", "id_2"], "token", retries=2
        )

    assert result == {}
    assert result.unanswered == {"id_1", "id_2"}
    assert session.get.call_count == 2


@pytest.mark.asyncio
async def test_fetch_spotify_album_details_batch_terminal_miss_is_not_unanswered():
    """
    GIVEN the batch endpoint answers 200 without one of the requested albums
    WHEN fetch_spotify_album_details_batch runs
    THEN that id is absent from the details and NOT unanswered: Spotify
    answered, so it is not recorded as an outage.
    """
    session = MagicMock()
    resp = AsyncMock()
    resp.status = 200
    resp.json = AsyncMock(return_value={"albums": [{"id": "id_1"}, None]})
    session.get.return_value = make_response_context(resp)

    with patch(
        "scrobblescope.spotify.get_spotify_limiter", return_value=NoopAsyncContext()
    ):
        result = await fetch_spotify_album_details_batch(
            session, ["id_1", "id_2"], "token", retries=2
        )

    assert set(result) == {"id_1"}
    assert result.unanswered == frozenset()


@pytest.mark.asyncio
async def test_single_album_fallback_reports_only_the_failed_album_unanswered():
    """
    GIVEN the batch endpoint is gone (404), and of the single-album calls one
    answers 200 and the other answers 500 every time
    WHEN fetch_spotify_album_details_batch falls back album by album
    THEN the good album is returned, the failing one is listed as unanswered,
    and one failure does not lose its sibling.
    """
    session = MagicMock()

    def get(url, **kwargs):
        if url.endswith("/albums"):
            return make_response_context(_status_response(404))
        if url.endswith("good"):
            return make_response_context(_single_album_response("good"))
        return make_response_context(_status_response(500))

    session.get.side_effect = get

    with (
        patch(
            "scrobblescope.spotify.get_spotify_limiter", return_value=NoopAsyncContext()
        ),
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        result = await fetch_spotify_album_details_batch(
            session, ["good", "bad"], "token", retries=2
        )

    assert set(result) == {"good"}
    assert result.unanswered == {"bad"}


@pytest.mark.asyncio
async def test_one_by_one_details_cancel_and_settle_siblings_on_an_unexpected_error():
    """
    GIVEN three per-album detail calls where the first raises an unexpected
    error and the other two would sleep far longer than the test runs
    WHEN the albums are fetched one by one
    THEN the error reaches the caller unwrapped and both siblings were
    cancelled and settled before it did (F-B23-24). Mutation: drop the
    ``cancel_and_drain`` in the finally block and the siblings are still
    pending, so ``cancelled`` stays empty.
    """
    import asyncio

    from scrobblescope.spotify import _fetch_album_details_one_by_one

    cancelled = []

    async def single(session, album_id, token, retries):
        if album_id == "a":
            await asyncio.sleep(0.01)
            raise RuntimeError("unexpected")
        try:
            await asyncio.sleep(30)
        except asyncio.CancelledError:
            cancelled.append(album_id)
            raise

    with patch(
        "scrobblescope.spotify.fetch_spotify_album_details_single",
        side_effect=single,
    ):
        async with asyncio.timeout(2):
            with pytest.raises(RuntimeError, match="unexpected"):
                await _fetch_album_details_one_by_one(
                    MagicMock(), ["a", "b", "c"], "tok", 0
                )

    assert sorted(cancelled) == ["b", "c"]
