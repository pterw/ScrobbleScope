import asyncio
import gc
import logging
import sys
import threading
import time
import weakref
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from scrobblescope.errors import ProviderError
from scrobblescope.spotify import (
    _loop_token_state,
    _token_states,
    album_metadata_from_details,
    fetch_spotify_access_token,
    fetch_spotify_album_details_batch,
    fetch_spotify_album_details_single,
    fetch_spotify_artist_spotlight,
    search_for_spotify_album_id,
    spotify_job_breaker,
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
    non-5xx status (a 400: Spotify refused the request)
    WHEN fetch_spotify_album_details_batch runs
    THEN it returns no details without a retry sleep, and lists the ID as
    unanswered: a refusal is "could not answer", never "answered, nothing".
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
    assert result.unanswered == {"id_1"}
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
    # A safety margin: a token is treated as expired a minute before Spotify
    # says so, or a job that starts with 40 s left runs its second half on a
    # rejected token (R4-backend-1).
    assert fake_cache["expires_at"] <= time.time() + 3600 - 59


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


# --- refusals are "could not answer" (R4-backend-1) ---------------------------


def _status_only(status, retry_after=None):
    resp = AsyncMock()
    resp.status = status
    resp.headers = {"Retry-After": retry_after} if retry_after else {}
    return resp


def _ok_search(spotify_id="sp1"):
    resp = AsyncMock()
    resp.status = 200
    resp.json = AsyncMock(return_value={"albums": {"items": [{"id": spotify_id}]}})
    return resp


_LIMITER = "scrobblescope.spotify.get_spotify_limiter"


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [400, 403])
async def test_search_refusal_raises_unavailable_and_is_not_no_match(status):
    """
    GIVEN Spotify refuses a search with a 400 or a 403
    WHEN search_for_spotify_album_id runs
    THEN it raises ProviderError spotify_unavailable after one request (a
    refusal is not retried), where it used to return None and record the album
    as "no match".
    """
    session = MagicMock()
    session.get.return_value = make_response_context(_status_only(status))

    with patch(_LIMITER, return_value=NoopAsyncContext()):
        with pytest.raises(ProviderError) as excinfo:
            await _search_with(session)

    assert excinfo.value.code == "spotify_unavailable"
    assert session.get.call_count == 1


@pytest.mark.asyncio
async def test_search_401_drops_the_cached_token_and_retries_once_with_a_fresh_one():
    """
    GIVEN the token the search was given is rejected (401) and Spotify accepts
    a fresh one
    WHEN search_for_spotify_album_id runs
    THEN the cached token is dropped, exactly one fresh token is fetched, and
    the retry carries it in its Authorization header and returns the match.
    """
    session = MagicMock()
    session.get.side_effect = [
        make_response_context(_status_only(401)),
        make_response_context(_ok_search("sp-fresh")),
    ]
    cache = {"token": "old", "expires_at": time.time() + 3000}
    seen_cache_at_refresh = []

    async def fresh_token():
        seen_cache_at_refresh.append(cache["expires_at"])
        return "fresh"

    with (
        patch(_LIMITER, return_value=NoopAsyncContext()),
        patch("scrobblescope.spotify.spotify_token_cache", cache),
        patch(
            "scrobblescope.spotify.fetch_spotify_access_token", side_effect=fresh_token
        ),
    ):
        result = await search_for_spotify_album_id(session, "A", "B", "old")

    assert result == "sp-fresh"
    assert seen_cache_at_refresh == [0]
    sent = [call.kwargs["headers"]["Authorization"] for call in session.get.mock_calls]
    assert sent == ["Bearer old", "Bearer fresh"]


@pytest.mark.asyncio
async def test_search_401_after_a_fresh_token_raises_and_asks_for_one_token_only():
    """
    GIVEN Spotify rejects the token and rejects the fresh one too
    WHEN search_for_spotify_album_id runs
    THEN it raises ProviderError spotify_unavailable (not "no match"), after
    exactly two requests and one token fetch: retry once, not until the
    retries run out.
    """
    session = MagicMock()
    session.get.return_value = make_response_context(_status_only(401))
    refresh = AsyncMock(return_value="fresh")

    with (
        patch(_LIMITER, return_value=NoopAsyncContext()),
        patch(
            "scrobblescope.spotify.spotify_token_cache",
            {"token": "old", "expires_at": time.time() + 3000},
        ),
        patch("scrobblescope.spotify.fetch_spotify_access_token", refresh),
    ):
        with pytest.raises(ProviderError) as excinfo:
            await search_for_spotify_album_id(session, "A", "B", "old")

    assert excinfo.value.code == "spotify_unavailable"
    assert session.get.call_count == 2
    assert refresh.await_count == 1


@pytest.mark.asyncio
async def test_search_401_with_no_token_to_be_had_raises_unavailable():
    """
    GIVEN Spotify rejects the token and the token endpoint gives nothing back
    WHEN search_for_spotify_album_id runs
    THEN it raises ProviderError spotify_unavailable after one request.
    """
    session = MagicMock()
    session.get.return_value = make_response_context(_status_only(401))

    with (
        patch(_LIMITER, return_value=NoopAsyncContext()),
        patch(
            "scrobblescope.spotify.spotify_token_cache",
            {"token": "old", "expires_at": time.time() + 3000},
        ),
        patch(
            "scrobblescope.spotify.fetch_spotify_access_token",
            new_callable=AsyncMock,
            return_value=None,
        ),
    ):
        with pytest.raises(ProviderError):
            await search_for_spotify_album_id(session, "A", "B", "old")

    assert session.get.call_count == 1


@pytest.mark.asyncio
async def test_a_sibling_that_already_replaced_the_token_is_not_replaced_again():
    """
    GIVEN a sibling call replaces the cached token while this call's request
    (sent with the old one) is in flight
    WHEN that request is rejected (401)
    THEN the newer cached token is used as it is: the cache is not dropped
    again, so one rejection costs one token request, not one per call.
    """
    cache = {"token": "stale", "expires_at": time.time() + 3000}
    responses = [
        make_response_context(_status_only(401)),
        make_response_context(_ok_search()),
    ]

    def get(*args, **kwargs):
        if len(responses) == 2:  # the first request: a sibling refreshes now
            cache.update({"token": "newer", "expires_at": time.time() + 3000})
        return responses.pop(0)

    session = MagicMock()
    session.get.side_effect = get

    with (
        patch(_LIMITER, return_value=NoopAsyncContext()),
        patch("scrobblescope.spotify.spotify_token_cache", cache),
    ):
        result = await search_for_spotify_album_id(session, "A", "B", "stale")

    assert result == "sp1"
    assert cache["expires_at"] > time.time()
    assert session.get.call_args.kwargs["headers"] == {"Authorization": "Bearer newer"}


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [400, 401, 403])
async def test_single_album_details_refusal_raises_and_404_is_an_answer(status):
    """
    GIVEN a single-album details call answers 400, 401 (not cured by a fresh
    token) or 403
    WHEN fetch_spotify_album_details_single runs
    THEN it raises ProviderError spotify_unavailable; a 404 (the album is not
    there) still returns None, an answer.
    """
    session = MagicMock()
    session.get.return_value = make_response_context(_status_only(status))

    with (
        patch(_LIMITER, return_value=NoopAsyncContext()),
        patch(
            "scrobblescope.spotify.spotify_token_cache",
            {"token": "t", "expires_at": time.time() + 3000},
        ),
        patch(
            "scrobblescope.spotify.fetch_spotify_access_token",
            new_callable=AsyncMock,
            return_value="fresh",
        ),
    ):
        with pytest.raises(ProviderError) as excinfo:
            await fetch_spotify_album_details_single(session, "x", "t")
        assert excinfo.value.code == "spotify_unavailable"

        session.get.return_value = make_response_context(_status_only(404))
        assert await fetch_spotify_album_details_single(session, "x", "t") is None


@pytest.mark.asyncio
async def test_batch_details_401_refreshes_the_token_once_and_succeeds():
    """
    GIVEN the batch details call is rejected (401) and a fresh token works
    WHEN fetch_spotify_album_details_batch runs
    THEN the details come back, answered, and the retry used the fresh token.
    """
    session = MagicMock()
    ok = AsyncMock()
    ok.status = 200
    ok.json = AsyncMock(return_value={"albums": [{"id": "a1", "name": "One"}]})
    session.get.side_effect = [
        make_response_context(_status_only(401)),
        make_response_context(ok),
    ]

    with (
        patch(_LIMITER, return_value=NoopAsyncContext()),
        patch(
            "scrobblescope.spotify.spotify_token_cache",
            {"token": "old", "expires_at": time.time() + 3000},
        ),
        patch(
            "scrobblescope.spotify.fetch_spotify_access_token",
            new_callable=AsyncMock,
            return_value="fresh",
        ),
    ):
        result = await fetch_spotify_album_details_batch(session, ["a1"], "old")

    assert result == {"a1": {"id": "a1", "name": "One"}}
    assert result.unanswered == frozenset()
    assert session.get.call_args.kwargs["headers"] == {"Authorization": "Bearer fresh"}


@pytest.mark.asyncio
async def test_batch_details_401_that_a_fresh_token_does_not_cure_is_unanswered():
    """
    GIVEN the batch details call is rejected even with a fresh token
    WHEN fetch_spotify_album_details_batch runs
    THEN every ID is listed unanswered (unavailable), not "answered, nothing".
    """
    session = MagicMock()
    session.get.return_value = make_response_context(_status_only(401))

    with (
        patch(_LIMITER, return_value=NoopAsyncContext()),
        patch(
            "scrobblescope.spotify.spotify_token_cache",
            {"token": "old", "expires_at": time.time() + 3000},
        ),
        patch(
            "scrobblescope.spotify.fetch_spotify_access_token",
            new_callable=AsyncMock,
            return_value="fresh",
        ),
    ):
        result = await fetch_spotify_album_details_batch(session, ["a1", "a2"], "old")

    assert result == {}
    assert result.unanswered == {"a1", "a2"}


# --- a per-job breaker for a Retry-After above the cap (R4-backend-3) ---------


@pytest.mark.asyncio
async def test_over_cap_retry_after_stops_the_rest_of_that_jobs_spotify_calls():
    """
    GIVEN Spotify answers 429 with a Retry-After far above the cap
    WHEN a job (inside spotify_job_breaker) searches three albums and then
    asks for details, single and batch
    THEN only the first search sends a request; every later Spotify call of
    that job raises (search, single) or reports every ID unanswered (batch)
    without one.
    """
    session = MagicMock()
    session.get.return_value = make_response_context(
        _status_only(429, retry_after="3600")
    )

    with patch(_LIMITER, return_value=NoopAsyncContext()):
        with spotify_job_breaker():
            codes = []
            for album in ("one", "two", "three"):
                with pytest.raises(ProviderError) as excinfo:
                    await search_for_spotify_album_id(session, "A", album, "tok")
                codes.append(excinfo.value.code)
            with pytest.raises(ProviderError):
                await fetch_spotify_album_details_single(session, "x", "tok")
            batch = await fetch_spotify_album_details_batch(session, ["a1"], "tok")

    assert codes == ["spotify_rate_limited"] * 3
    assert batch.unanswered == {"a1"}
    assert session.get.call_count == 1


@pytest.mark.asyncio
async def test_a_retry_after_under_the_cap_does_not_trip_the_breaker():
    """
    GIVEN Spotify answers one search 429 with Retry-After 1 (under the cap)
    WHEN the job then searches again
    THEN the second search still sends its request and returns its match.
    """
    session = MagicMock()
    session.get.side_effect = [
        make_response_context(_status_only(429, retry_after="1")),
        make_response_context(_ok_search("first")),
        make_response_context(_ok_search("second")),
    ]

    with (
        patch(_LIMITER, return_value=NoopAsyncContext()),
        patch("asyncio.sleep", new_callable=AsyncMock),
        spotify_job_breaker(),
    ):
        first = await _search_with(session)
        second = await _search_with(session)

    assert (first, second) == ("first", "second")
    assert session.get.call_count == 3


@pytest.mark.asyncio
async def test_one_jobs_tripped_breaker_does_not_stop_a_concurrent_job():
    """
    GIVEN two jobs run concurrently on one loop, and job A meets a Retry-After
    above the cap
    WHEN job B searches after A has tripped
    THEN B's request is sent and answered: the verdict is A's, not the
    module's.
    """
    import asyncio

    a_tripped = asyncio.Event()
    session_a = MagicMock()
    session_a.get.return_value = make_response_context(
        _status_only(429, retry_after="3600")
    )
    session_b = MagicMock()
    session_b.get.return_value = make_response_context(_ok_search("b-match"))

    async def job_a():
        with spotify_job_breaker():
            with pytest.raises(ProviderError):
                await _search_with(session_a)
            a_tripped.set()
            with pytest.raises(ProviderError):
                await _search_with(session_a)

    async def job_b():
        with spotify_job_breaker():
            await a_tripped.wait()
            return await _search_with(session_b)

    with patch(_LIMITER, return_value=NoopAsyncContext()):
        _, b_result = await asyncio.gather(job_a(), job_b())

    assert b_result == "b-match"
    assert session_a.get.call_count == 1
    assert session_b.get.call_count == 1


@pytest.mark.asyncio
async def test_outside_a_job_breaker_an_over_cap_429_skips_nothing():
    """
    GIVEN no spotify_job_breaker block (the spotlight, a direct call)
    WHEN two searches each meet a Retry-After above the cap
    THEN both send a request: the breaker is per job, never a module global.
    """
    session = MagicMock()
    session.get.return_value = make_response_context(
        _status_only(429, retry_after="3600")
    )

    with patch(_LIMITER, return_value=NoopAsyncContext()):
        for _ in range(2):
            with pytest.raises(ProviderError):
                await _search_with(session)

    assert session.get.call_count == 2


# --- the breaker is re-checked right before each request ----------------------


class _SuspendingGet:
    """A ``session.get`` whose response takes time, like a network call.

    The request is counted when it is sent, and the response arrives only
    after the event loop has run every other ready task. A mock that answers
    at once lets task 1 finish (and trip the breaker) before task 2 starts,
    which hides the very defect a fan-out has: all the tasks are queued
    before the first answer returns.
    """

    def __init__(self, response):
        self.response = response
        self.sent = 0

    def __call__(self, *args, **kwargs):
        self.sent += 1
        outer = self

        class _Context:
            async def __aenter__(self):
                await asyncio.sleep(0.01)
                return outer.response

            async def __aexit__(self, *exc):
                return False

        return _Context()


@pytest.mark.asyncio
async def test_a_tripped_breaker_stops_searches_already_queued_behind_the_semaphore():
    """
    GIVEN twenty searches are started at once, two may run at a time, and
    Spotify answers every request 429 with a Retry-After far above the cap
    WHEN the first answer trips the job's breaker
    THEN no queued search sends a request afterwards: only the two that were
    already in flight went out, and every search raised ProviderError. A
    breaker checked only at function entry lets all twenty out, since each
    passed that check before any answer came back.
    """
    session = MagicMock()
    session.get = _SuspendingGet(_status_only(429, retry_after="3600"))
    semaphore = asyncio.Semaphore(2)

    with patch(_LIMITER, return_value=NoopAsyncContext()):
        with spotify_job_breaker():
            results = await asyncio.gather(
                *(
                    search_for_spotify_album_id(
                        session, "A", f"album {n}", "tok", semaphore
                    )
                    for n in range(20)
                ),
                return_exceptions=True,
            )

    assert all(isinstance(r, ProviderError) for r in results)
    assert session.get.sent <= 2


@pytest.mark.asyncio
async def test_a_tripped_breaker_stops_single_details_queued_behind_the_limiter():
    """
    GIVEN the one-by-one details fallback fires twenty calls at once (no
    semaphore, only the rate limiter, here two at a time) and Spotify answers
    429 with a Retry-After above the cap
    WHEN the first answer trips the breaker
    THEN the calls still waiting for the limiter send nothing: at most the two
    in flight went out, and every ID is listed unanswered.
    """
    from scrobblescope.spotify import _fetch_album_details_one_by_one

    session = MagicMock()
    session.get = _SuspendingGet(_status_only(429, retry_after="3600"))
    ids = [f"id{n}" for n in range(20)]

    with patch(_LIMITER, return_value=asyncio.Semaphore(2)):
        with spotify_job_breaker():
            result = await _fetch_album_details_one_by_one(session, ids, "tok", 3)

    assert result.unanswered == set(ids)
    assert session.get.sent <= 2


@pytest.mark.asyncio
async def test_a_tripped_breaker_stops_batches_queued_behind_the_semaphore():
    """
    GIVEN ten batch calls are started at once, two may run at a time, and
    Spotify answers 429 with a Retry-After above the cap
    WHEN the first answer trips the breaker
    THEN at most the two in flight sent a request and every batch reports all
    its IDs unanswered.
    """
    session = MagicMock()
    session.get = _SuspendingGet(_status_only(429, retry_after="3600"))
    semaphore = asyncio.Semaphore(2)

    with patch(_LIMITER, return_value=NoopAsyncContext()):
        with spotify_job_breaker():
            results = await asyncio.gather(
                *(
                    fetch_spotify_album_details_batch(
                        session, [f"a{n}"], "tok", semaphore
                    )
                    for n in range(10)
                )
            )

    assert [r.unanswered for r in results] == [{f"a{n}"} for n in range(10)]
    assert session.get.sent <= 2


# --- a persistent refusal trips the breaker too --------------------------------


@pytest.mark.asyncio
async def test_three_refusals_in_a_row_stop_the_rest_of_the_jobs_requests():
    """
    GIVEN Spotify refuses every request with a 403 (a revoked or blocked key)
    WHEN a job searches ten albums one after the other
    THEN three requests are refused and the other seven send nothing: a
    persistent refusal costs a handful of requests, not one per album.
    """
    session = MagicMock()
    session.get.return_value = make_response_context(_status_only(403))

    with patch(_LIMITER, return_value=NoopAsyncContext()):
        with spotify_job_breaker():
            for n in range(10):
                with pytest.raises(ProviderError):
                    await search_for_spotify_album_id(session, "A", f"al {n}", "tok")

    assert session.get.call_count == 3


@pytest.mark.asyncio
async def test_an_answer_between_refusals_keeps_the_breaker_closed():
    """
    GIVEN refusals are interleaved with answers (403, 403, match, ...)
    WHEN a job searches six albums
    THEN every one sends its request: "in a row" means no answer between.
    """
    session = MagicMock()
    session.get.side_effect = [
        make_response_context(_status_only(403)),
        make_response_context(_status_only(403)),
        make_response_context(_ok_search("hit")),
        make_response_context(_status_only(403)),
        make_response_context(_status_only(403)),
        make_response_context(_ok_search("hit")),
    ]

    with patch(_LIMITER, return_value=NoopAsyncContext()):
        with spotify_job_breaker():
            outcomes = []
            for n in range(6):
                try:
                    outcomes.append(
                        await search_for_spotify_album_id(
                            session, "A", f"al {n}", "tok"
                        )
                    )
                except ProviderError:
                    outcomes.append("refused")

    assert outcomes == ["refused", "refused", "hit", "refused", "refused", "hit"]
    assert session.get.call_count == 6


@pytest.mark.asyncio
async def test_a_401_that_a_fresh_token_does_not_cure_stops_the_rest_of_the_job():
    """
    GIVEN Spotify rejects the token and also the freshly fetched one
    WHEN a job searches three albums
    THEN the first search spends two requests, and the other two send nothing.
    """
    session = MagicMock()
    session.get.return_value = make_response_context(_status_only(401))

    with (
        patch(_LIMITER, return_value=NoopAsyncContext()),
        patch(
            "scrobblescope.spotify.spotify_token_cache",
            {"token": "old", "expires_at": time.time() + 3000},
        ),
        patch(
            "scrobblescope.spotify.fetch_spotify_access_token",
            new_callable=AsyncMock,
            return_value="fresh",
        ),
        spotify_job_breaker(),
    ):
        for n in range(3):
            with pytest.raises(ProviderError):
                await search_for_spotify_album_id(session, "A", f"al {n}", "old")

    assert session.get.call_count == 2


@pytest.mark.asyncio
async def test_a_refusal_logs_one_warning_and_no_error(caplog):
    """
    GIVEN Spotify refuses two searches with a 403 in one job
    WHEN the job's breaker block ends
    THEN the log holds one WARNING naming the operation and status, one
    WARNING summarising the other refusal, and no ERROR line (the retry
    helper used to log every refusal as an error in spotify.search).
    """
    session = MagicMock()
    session.get.return_value = make_response_context(_status_only(403))

    with caplog.at_level(logging.INFO):
        with patch(_LIMITER, return_value=NoopAsyncContext()):
            with spotify_job_breaker():
                for n in range(2):
                    with pytest.raises(ProviderError):
                        await search_for_spotify_album_id(
                            session, "A", f"al {n}", "tok"
                        )

    assert not [r for r in caplog.records if r.levelno >= logging.ERROR]
    refusals = [r.getMessage() for r in caplog.records if "refused" in r.getMessage()]
    assert refusals == [
        "Spotify refused spotify.search: HTTP 403",
        "Spotify refused 1 further requests of this job (same operation and "
        "status as above)",
    ]


# --- the cached token is adopted, not rediscovered call by call ---------------


@pytest.mark.asyncio
async def test_a_call_given_a_stale_token_sends_the_valid_cached_one_first():
    """
    GIVEN the cache holds a valid token other than the one a call was given
    (an earlier call refreshed it)
    WHEN the call searches
    THEN its first request already carries the cached token: no 401 and no
    token fetch are spent to find that out.
    """
    session = MagicMock()
    session.get.return_value = make_response_context(_ok_search("hit"))
    refresh = AsyncMock(return_value="unused")

    with (
        patch(_LIMITER, return_value=NoopAsyncContext()),
        patch(
            "scrobblescope.spotify.spotify_token_cache",
            {"token": "cached", "expires_at": time.time() + 3000},
        ),
        patch("scrobblescope.spotify.fetch_spotify_access_token", refresh),
    ):
        result = await search_for_spotify_album_id(session, "A", "B", "stale")

    assert result == "hit"
    assert session.get.call_count == 1
    assert session.get.call_args.kwargs["headers"] == {"Authorization": "Bearer cached"}
    refresh.assert_not_awaited()


@pytest.mark.asyncio
async def test_an_expired_cached_token_is_not_adopted():
    """
    GIVEN the cache holds a token that has expired
    WHEN a call is given another token
    THEN the given token is sent, not the expired cached one.
    """
    session = MagicMock()
    session.get.return_value = make_response_context(_ok_search("hit"))

    with (
        patch(_LIMITER, return_value=NoopAsyncContext()),
        patch(
            "scrobblescope.spotify.spotify_token_cache",
            {"token": "expired", "expires_at": time.time() - 5},
        ),
    ):
        await search_for_spotify_album_id(session, "A", "B", "given")

    assert session.get.call_args.kwargs["headers"] == {"Authorization": "Bearer given"}


@pytest.mark.asyncio
async def test_the_one_by_one_fallback_uses_the_token_the_batch_refreshed():
    """
    GIVEN the batch call is rejected (401) and refreshes the token, and its
    retry then meets a 404 (the endpoint is gone)
    WHEN the fallback fetches the albums one by one
    THEN the single calls send the fresh token, not the original one.
    """
    single = AsyncMock()
    single.status = 200
    single.json = AsyncMock(return_value={"id": "a1"})
    session = MagicMock()
    session.get.side_effect = [
        make_response_context(_status_only(401)),
        make_response_context(_status_only(404)),
        make_response_context(single),
    ]
    cache = {"token": "old", "expires_at": time.time() + 3000}

    # The refresh is returned but not cached, so the single calls cannot find
    # it there: they have to be handed the batch's token.
    with (
        patch(_LIMITER, return_value=NoopAsyncContext()),
        patch("scrobblescope.spotify.spotify_token_cache", cache),
        patch(
            "scrobblescope.spotify.fetch_spotify_access_token",
            new_callable=AsyncMock,
            return_value="fresh",
        ),
    ):
        result = await fetch_spotify_album_details_batch(session, ["a1"], "old")

    assert set(result) == {"a1"}
    sent = [call.kwargs["headers"]["Authorization"] for call in session.get.mock_calls]
    assert sent == ["Bearer old", "Bearer fresh", "Bearer fresh"]


class _Suspending:
    """An async context manager that yields to the loop before answering."""

    def __init__(self, response):
        self._response = response

    async def __aenter__(self):
        await asyncio.sleep(0.01)
        return self._response

    async def __aexit__(self, *exc):
        return False


def _token_endpoint(requests, token="fresh", status=200):
    """A create_optimized_session stand-in whose token POST suspends and counts."""
    resp = AsyncMock()
    resp.status = status
    resp.json = AsyncMock(return_value={"access_token": token, "expires_in": 3600})
    session = MagicMock()

    def post(*args, **kwargs):
        requests.append(1)
        return _Suspending(resp)

    session.post.side_effect = post
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=session)
    ctx.__aexit__ = AsyncMock(return_value=False)
    return MagicMock(return_value=ctx)


@pytest.mark.asyncio
async def test_concurrent_rejections_of_one_token_cost_one_token_request():
    """
    GIVEN six searches in flight on one loop, all sent with a token Spotify
    rejects (401), and a token endpoint that suspends before it answers
    WHEN they all ask for a replacement
    THEN exactly one token request is made and every search retries with the
    fresh token, where each used to request its own.
    """
    cache = {"token": "old", "expires_at": time.time() + 3000}
    requests = []

    def session_for_search():
        session = MagicMock()

        def get(*args, **kwargs):
            bearer = kwargs["headers"]["Authorization"]
            status = _status_only(401) if bearer == "Bearer old" else _ok_search("m")
            return _Suspending(status)

        session.get.side_effect = get
        return session

    sessions = [session_for_search() for _ in range(6)]

    with (
        patch(_LIMITER, return_value=NoopAsyncContext()),
        patch("scrobblescope.spotify.spotify_token_cache", cache),
        patch("scrobblescope.spotify.SPOTIFY_CLIENT_ID", "id"),
        patch("scrobblescope.spotify.SPOTIFY_CLIENT_SECRET", "secret"),
        patch(
            "scrobblescope.spotify.create_optimized_session",
            _token_endpoint(requests),
        ),
    ):
        results = await asyncio.gather(
            *(search_for_spotify_album_id(s, "A", "B", "old") for s in sessions)
        )

    assert results == ["m"] * 6
    assert len(requests) == 1
    for session in sessions:
        sent = [c.kwargs["headers"]["Authorization"] for c in session.get.mock_calls]
        assert sent == ["Bearer old", "Bearer fresh"]


@pytest.mark.asyncio
async def test_concurrent_fetches_on_an_expired_cache_cost_one_token_request():
    """
    GIVEN an expired token cache and five concurrent fetches
    WHEN a suspending token endpoint answers
    THEN one token request is made and all five get the same fresh token.
    """
    cache = {"token": None, "expires_at": 0}
    requests = []

    with (
        patch("scrobblescope.spotify.spotify_token_cache", cache),
        patch("scrobblescope.spotify.SPOTIFY_CLIENT_ID", "id"),
        patch("scrobblescope.spotify.SPOTIFY_CLIENT_SECRET", "secret"),
        patch(
            "scrobblescope.spotify.create_optimized_session",
            _token_endpoint(requests),
        ),
    ):
        tokens = await asyncio.gather(*(fetch_spotify_access_token() for _ in range(5)))

    assert tokens == ["fresh"] * 5
    assert len(requests) == 1


def test_each_jobs_loop_gets_a_working_token_lock():
    """
    GIVEN two jobs, each running its own event loop in its own thread, each
    with concurrent fetches contending for the token lock
    WHEN the two jobs run one after the other (each loop still contends
    within itself)
    THEN neither fails with "bound to a different event loop", and each loop
    made its own single token request.
    """
    outcomes = {}
    requests = []

    def job(name):
        cache = {"token": None, "expires_at": 0}

        async def run():
            with (
                patch("scrobblescope.spotify.spotify_token_cache", cache),
                patch("scrobblescope.spotify.SPOTIFY_CLIENT_ID", "id"),
                patch("scrobblescope.spotify.SPOTIFY_CLIENT_SECRET", "secret"),
                patch(
                    "scrobblescope.spotify.create_optimized_session",
                    _token_endpoint(requests, token=name),
                ),
            ):
                return await asyncio.gather(
                    *(fetch_spotify_access_token() for _ in range(3))
                )

        try:
            outcomes[name] = asyncio.run(run())
        except Exception as exc:  # noqa: BLE001 - the failure is the assertion
            outcomes[name] = exc

    for name in ("job-a", "job-b"):
        thread = threading.Thread(target=job, args=(name,))
        thread.start()
        thread.join()

    assert outcomes == {"job-a": ["job-a"] * 3, "job-b": ["job-b"] * 3}
    assert len(requests) == 2


@pytest.mark.asyncio
async def test_a_failed_token_request_is_shared_by_the_calls_waiting_on_it():
    """
    GIVEN five concurrent fetches on an expired cache and a token endpoint
    that suspends and then refuses (HTTP 503)
    WHEN they all wait on the loop's lock
    THEN one token request is made and all five get no token, where each
    waiter used to issue its own request in turn.
    AND a fetch started after that failure asks again.
    """
    cache = {"token": None, "expires_at": 0}
    requests = []

    with (
        patch("scrobblescope.spotify.spotify_token_cache", cache),
        patch("scrobblescope.spotify.SPOTIFY_CLIENT_ID", "id"),
        patch("scrobblescope.spotify.SPOTIFY_CLIENT_SECRET", "secret"),
        patch(
            "scrobblescope.spotify.create_optimized_session",
            _token_endpoint(requests, status=503),
        ),
    ):
        tokens = await asyncio.gather(*(fetch_spotify_access_token() for _ in range(5)))
        assert tokens == [None] * 5
        assert len(requests) == 1

        later = await fetch_spotify_access_token()

    assert later is None
    assert len(requests) == 2


def test_a_finished_jobs_loop_is_released_by_the_next_token_fetch():
    """
    GIVEN a job whose loop had contended for the token lock and then closed
    WHEN a later job's loop asks for its token lock
    THEN the finished loop is no longer held (a contended asyncio.Lock holds
    its loop strongly, so the weak key alone never let it go).
    """
    holder = {}

    def first_job():
        cache = {"token": None, "expires_at": 0}

        async def run():
            holder["loop"] = weakref.ref(asyncio.get_running_loop())
            with (
                patch("scrobblescope.spotify.spotify_token_cache", cache),
                patch("scrobblescope.spotify.SPOTIFY_CLIENT_ID", "id"),
                patch("scrobblescope.spotify.SPOTIFY_CLIENT_SECRET", "secret"),
                patch(
                    "scrobblescope.spotify.create_optimized_session",
                    _token_endpoint([]),
                ),
            ):
                await asyncio.gather(*(fetch_spotify_access_token() for _ in range(3)))

        asyncio.run(run())

    thread = threading.Thread(target=first_job)
    thread.start()
    thread.join()

    async def second_job():
        _loop_token_state()

    asyncio.run(second_job())
    gc.collect()

    assert holder["loop"]() is None


def test_job_threads_can_share_the_token_state_dict_without_error():
    """
    GIVEN many job threads, each opening and closing its own event loop
    WHEN they all ask for their token state at once
    THEN none raises (the prune iterates and deletes on a dict every job
    thread shares) and the closed loops are gone afterwards.
    """
    errors = []
    loops = []
    start = threading.Barrier(8)

    def job_thread():
        start.wait()
        try:
            for _ in range(200):
                loop = asyncio.new_event_loop()
                try:
                    loop.run_until_complete(_state_of(loop))
                    loops.append(weakref.ref(loop))
                finally:
                    loop.close()
        except Exception as exc:  # noqa: BLE001 - any error is the failure under test
            errors.append(repr(exc))

    async def _state_of(loop):
        return _loop_token_state()

    previous = sys.getswitchinterval()
    sys.setswitchinterval(1e-6)
    try:
        threads = [threading.Thread(target=job_thread) for _ in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
    finally:
        sys.setswitchinterval(previous)

    assert errors == []

    async def last_job():
        _loop_token_state()
        return len(_token_states)

    remaining = asyncio.run(last_job())
    gc.collect()
    assert all(ref() is None for ref in loops)
    assert remaining == 1
