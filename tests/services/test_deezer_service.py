import logging
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from scrobblescope.deezer import fetch_deezer_album, search_deezer_album
from scrobblescope.errors import ProviderError
from tests.helpers import NoopAsyncContext, make_response_context


@pytest.mark.asyncio
async def test_search_deezer_album_skips_non_matching_candidates():
    """
    GIVEN a search response whose first result is a tribute single and whose
    third is the real album
    WHEN search_deezer_album runs
    THEN it returns the third result's id, comparing normalized names rather
    than trusting result order.
    """
    session = MagicMock()
    resp = AsyncMock()
    resp.status = 200
    resp.json = AsyncMock(
        return_value={
            "data": [
                {
                    "id": 1,
                    "title": "Rumours",
                    "artist": {"name": "Grey Orton"},
                    "record_type": "single",
                },
                {
                    "id": 2,
                    "title": "Rumours (Tribute Version)",
                    "artist": {"name": "Someone Else"},
                    "record_type": "album",
                },
                {
                    "id": 6237061,
                    "title": "Rumours",
                    "artist": {"name": "Fleetwood Mac"},
                    "record_type": "album",
                },
            ]
        }
    )
    session.get.return_value = make_response_context(resp)

    with patch(
        "scrobblescope.deezer.get_deezer_limiter", return_value=NoopAsyncContext()
    ):
        result = await search_deezer_album(session, "Fleetwood Mac", "Rumours")

    assert result == 6237061


@pytest.mark.asyncio
async def test_search_deezer_album_returns_none_without_a_match():
    """
    GIVEN a search response with no candidate matching the key
    WHEN search_deezer_album runs
    THEN it returns None rather than guessing the first result.
    """
    session = MagicMock()
    resp = AsyncMock()
    resp.status = 200
    resp.json = AsyncMock(
        return_value={
            "data": [{"id": 1, "title": "Something Else", "artist": {"name": "Nobody"}}]
        }
    )
    session.get.return_value = make_response_context(resp)

    with patch(
        "scrobblescope.deezer.get_deezer_limiter", return_value=NoopAsyncContext()
    ):
        result = await search_deezer_album(session, "Fleetwood Mac", "Rumours")

    assert result is None


@pytest.mark.asyncio
async def test_search_deezer_album_no_data_error_returns_none():
    """
    GIVEN Deezer answers HTTP 200 with body {"error": {"code": 800}}
    WHEN search_deezer_album runs
    THEN it returns None -- error code 800 means "no data", a terminal miss.
    """
    session = MagicMock()
    resp = AsyncMock()
    resp.status = 200
    resp.json = AsyncMock(
        return_value={
            "error": {"type": "DataException", "message": "no data", "code": 800}
        }
    )
    session.get.return_value = make_response_context(resp)

    with patch(
        "scrobblescope.deezer.get_deezer_limiter", return_value=NoopAsyncContext()
    ):
        result = await search_deezer_album(session, "Fleetwood Mac", "Rumours")

    assert result is None


@pytest.mark.asyncio
async def test_search_deezer_album_quota_error_retries_then_succeeds():
    """
    GIVEN Deezer answers HTTP 200 with body {"error": {"code": 4}} (quota)
        and then a successful body
    WHEN search_deezer_album runs
    THEN it retries after a wait and returns the eventual match.
    """
    session = MagicMock()
    resp_quota = AsyncMock()
    resp_quota.status = 200
    resp_quota.json = AsyncMock(
        return_value={
            "error": {"type": "QuotaException", "message": "quota exceeded", "code": 4}
        }
    )
    resp_ok = AsyncMock()
    resp_ok.status = 200
    resp_ok.json = AsyncMock(
        return_value={
            "data": [
                {"id": 6237061, "title": "Rumours", "artist": {"name": "Fleetwood Mac"}}
            ]
        }
    )
    session.get.side_effect = [
        make_response_context(resp_quota),
        make_response_context(resp_ok),
    ]

    with (
        patch(
            "scrobblescope.deezer.get_deezer_limiter", return_value=NoopAsyncContext()
        ),
        patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
    ):
        result = await search_deezer_album(session, "Fleetwood Mac", "Rumours")

    assert result == 6237061
    assert session.get.call_count == 2
    assert mock_sleep.await_count >= 1


@pytest.mark.asyncio
async def test_fetch_deezer_album_pulls_full_track_list_beyond_album_endpoint_cap():
    """
    GIVEN an album that reports 30 tracks but whose /album/{id} response
        lists only 25 (Deezer's own cap)
    WHEN fetch_deezer_album runs
    THEN it also calls /album/{id}/tracks?limit=500 and returns all 30 track
        durations, not the 25 the album endpoint would give alone.
    """
    session = MagicMock()

    album_resp = AsyncMock()
    album_resp.status = 200
    album_resp.json = AsyncMock(
        return_value={
            "id": 79484,
            "link": "https://www.deezer.com/album/79484",
            "release_date": "1968-11-22",
            "cover_xl": "https://cdn.example/white-album.jpg",
            "nb_tracks": 30,
        }
    )

    tracks_resp = AsyncMock()
    tracks_resp.status = 200
    tracks_resp.json = AsyncMock(
        return_value={
            "data": [{"title": f"Track {i}", "duration": 100 + i} for i in range(30)]
        }
    )

    def route(url, params=None, **kwargs):
        if url.endswith("/tracks"):
            assert params == {"limit": 500}
            return make_response_context(tracks_resp)
        return make_response_context(album_resp)

    session.get.side_effect = route

    with patch(
        "scrobblescope.deezer.get_deezer_limiter", return_value=NoopAsyncContext()
    ):
        result = await fetch_deezer_album(session, 79484)

    assert result.provider == "deezer"
    assert result.album_id == "79484"
    assert result.url == "https://www.deezer.com/album/79484"
    assert result.release_date == "1968-11-22"
    assert result.image_url == "https://cdn.example/white-album.jpg"
    assert len(result.track_durations) == 30
    assert result.track_durations["track 0"] == 100
    assert result.track_durations["track 29"] == 129


@pytest.mark.asyncio
async def test_fetch_deezer_album_raises_unavailable_when_album_details_fail():
    """
    GIVEN the album-details request never succeeds (HTTP 500)
    WHEN fetch_deezer_album runs
    THEN it raises ProviderError deezer_unavailable, not None (an outage is
    not "no match"), without calling the tracks endpoint at all.
    """
    session = MagicMock()
    resp = AsyncMock()
    resp.status = 500
    session.get.return_value = make_response_context(resp)

    with patch(
        "scrobblescope.deezer.get_deezer_limiter", return_value=NoopAsyncContext()
    ):
        with pytest.raises(ProviderError) as excinfo:
            await fetch_deezer_album(session, 79484, retries=1)

    assert excinfo.value.code == "deezer_unavailable"
    assert session.get.call_count == 1


@pytest.mark.asyncio
async def test_fetch_deezer_album_raises_unavailable_when_tracks_fail():
    """
    GIVEN album details succeed but the tracks endpoint never does (HTTP 500)
    WHEN fetch_deezer_album runs
    THEN it raises ProviderError deezer_unavailable rather than returning an
    AlbumMetadata with no durations, or None.
    """
    session = MagicMock()
    album_resp = AsyncMock()
    album_resp.status = 200
    album_resp.json = AsyncMock(
        return_value={
            "id": 1,
            "link": "https://www.deezer.com/album/1",
            "release_date": "2020-01-01",
        }
    )
    tracks_resp = AsyncMock()
    tracks_resp.status = 500

    def route(url, params=None, **kwargs):
        if url.endswith("/tracks"):
            return make_response_context(tracks_resp)
        return make_response_context(album_resp)

    session.get.side_effect = route

    with patch(
        "scrobblescope.deezer.get_deezer_limiter", return_value=NoopAsyncContext()
    ):
        with pytest.raises(ProviderError) as excinfo:
            await fetch_deezer_album(session, 1, retries=1)

    assert excinfo.value.code == "deezer_unavailable"


@pytest.mark.asyncio
async def test_fetch_deezer_album_skips_a_track_with_a_null_title():
    """
    GIVEN /album/{id}/tracks lists a track whose title is null
    WHEN fetch_deezer_album runs
    THEN that track is skipped and the rest are returned, instead of a
    TypeError from normalising None failing the job (F-B23-24).
    """
    session = MagicMock()

    album_resp = AsyncMock()
    album_resp.status = 200
    album_resp.json = AsyncMock(return_value={"id": 1, "link": "https://x/1"})

    tracks_resp = AsyncMock()
    tracks_resp.status = 200
    tracks_resp.json = AsyncMock(
        return_value={
            "data": [
                {"title": None, "duration": 50},
                {"title": "Real Track", "duration": 200},
            ]
        }
    )

    def route(url, params=None, **kwargs):
        if url.endswith("/tracks"):
            return make_response_context(tracks_resp)
        return make_response_context(album_resp)

    session.get.side_effect = route

    with patch(
        "scrobblescope.deezer.get_deezer_limiter", return_value=NoopAsyncContext()
    ):
        result = await fetch_deezer_album(session, 1)

    assert result.track_durations == {"real track": 200}


_LEAK_ALBUM = "Zqxv Distinctive Album"
_LEAK_ARTIST = "Wjkl Distinctive Artist"


@pytest.mark.asyncio
async def test_search_failure_lines_carry_no_album_or_artist(caplog):
    """
    GIVEN the Deezer transport raises with the query text in its message
    WHEN search_deezer_album exhausts its retries
    THEN it raises ProviderError deezer_unavailable, and no record at any
    level names the album or artist.
    """
    session = MagicMock()
    session.get.side_effect = aiohttp.ClientConnectionError(
        f"failed q={_LEAK_ARTIST} {_LEAK_ALBUM}"
    )

    with (
        patch(
            "scrobblescope.deezer.get_deezer_limiter", return_value=NoopAsyncContext()
        ),
        patch("asyncio.sleep", new_callable=AsyncMock),
        caplog.at_level(logging.DEBUG),
    ):
        with pytest.raises(ProviderError) as excinfo:
            await search_deezer_album(session, _LEAK_ARTIST, _LEAK_ALBUM, retries=2)

    assert excinfo.value.code == "deezer_unavailable"
    assert "All 2 retries failed for deezer.search" in caplog.text
    assert caplog.records
    for record in caplog.records:
        assert _LEAK_ALBUM not in record.getMessage()
        assert _LEAK_ARTIST not in record.getMessage()


@pytest.mark.asyncio
async def test_fetch_deezer_album_skips_a_track_with_no_title_key():
    """
    GIVEN /album/{id}/tracks lists a track object with no ``title`` key at all
    WHEN fetch_deezer_album runs
    THEN that track is skipped and the rest are returned: the old filter read
    a missing title as "" (a str), passed it, and t["title"] raised KeyError,
    losing the album's Deezer metadata (Codex 4140219711).
    """
    session = MagicMock()

    album_resp = AsyncMock()
    album_resp.status = 200
    album_resp.json = AsyncMock(return_value={"id": 1, "link": "https://x/1"})

    tracks_resp = AsyncMock()
    tracks_resp.status = 200
    tracks_resp.json = AsyncMock(
        return_value={
            "data": [
                {"duration": 50},
                {"title": "Real Track", "duration": 200},
            ]
        }
    )

    def route(url, params=None, **kwargs):
        if url.endswith("/tracks"):
            return make_response_context(tracks_resp)
        return make_response_context(album_resp)

    session.get.side_effect = route

    with patch(
        "scrobblescope.deezer.get_deezer_limiter", return_value=NoopAsyncContext()
    ):
        result = await fetch_deezer_album(session, 1)

    assert result.track_durations == {"real track": 200}


@pytest.mark.asyncio
async def test_search_deezer_album_raises_when_throttled_not_no_match():
    """
    GIVEN Deezer answers its quota error (code 4) on every attempt
    WHEN search_deezer_album runs
    THEN it raises ProviderError deezer_rate_limited, not None: a throttled
    search says nothing about whether the album exists (Codex 4140219720).
    """
    session = MagicMock()
    resp = AsyncMock()
    resp.status = 200
    resp.json = AsyncMock(return_value={"error": {"type": "Exception", "code": 4}})
    session.get.return_value = make_response_context(resp)

    with (
        patch(
            "scrobblescope.deezer.get_deezer_limiter", return_value=NoopAsyncContext()
        ),
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        with pytest.raises(ProviderError) as excinfo:
            await search_deezer_album(session, "Artist", "Album", retries=2)

    assert excinfo.value.code == "deezer_rate_limited"
    assert session.get.call_count == 2


@pytest.mark.asyncio
async def test_deezer_search_5xx_on_every_attempt_raises_unavailable_not_no_match():
    """
    GIVEN Deezer answers HTTP 500 on every attempt
    WHEN the album is searched
    THEN ProviderError deezer_unavailable is raised after every retry, not
    None: an outage must not read as "no match" (the album is then recorded
    as unavailable, not as one Deezer does not have).
    """
    session = MagicMock()
    resp = AsyncMock()
    resp.status = 500
    session.get.return_value = make_response_context(resp)

    with (
        patch(
            "scrobblescope.deezer.get_deezer_limiter", return_value=NoopAsyncContext()
        ),
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        with pytest.raises(ProviderError) as excinfo:
            await search_deezer_album(session, "Artist", "Album", retries=2)

    assert excinfo.value.code == "deezer_unavailable"
    assert session.get.call_count == 2


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "body",
    [
        {"data": None},
        {"data": "not a list"},
        {"data": [None, "junk", {"id": 1, "title": None, "artist": None}]},
        {"data": [{"id": 1, "title": "Rumours", "artist": "Fleetwood Mac"}]},
        ["not", "a", "dict"],
    ],
    ids=["null_data", "string_data", "null_fields", "string_artist", "list_body"],
)
async def test_search_deezer_album_reads_a_strange_body_as_a_miss(body):
    """
    GIVEN Deezer answers 200 with a body of an unexpected shape (a null
    "data", a null "artist", a non-object candidate, a list)
    WHEN search_deezer_album runs
    THEN it reads that as no match and returns None: enrichment degrades, it
    never raises TypeError/AttributeError and fails the job as internal_error.
    """
    session = MagicMock()
    resp = AsyncMock()
    resp.status = 200
    resp.json = AsyncMock(return_value=body)
    session.get.return_value = make_response_context(resp)

    with patch(
        "scrobblescope.deezer.get_deezer_limiter", return_value=NoopAsyncContext()
    ):
        result = await search_deezer_album(session, "Fleetwood Mac", "Rumours")

    assert result is None


def _album_session(album_body, tracks_body):
    """A session answering /album/{id} with *album_body*, /tracks with *tracks_body*."""
    session = MagicMock()
    album_resp = AsyncMock()
    album_resp.status = 200
    album_resp.json = AsyncMock(return_value=album_body)
    tracks_resp = AsyncMock()
    tracks_resp.status = 200
    tracks_resp.json = AsyncMock(return_value=tracks_body)

    def route(url, params=None, **kwargs):
        if url.endswith("/tracks"):
            return make_response_context(tracks_resp)
        return make_response_context(album_resp)

    session.get.side_effect = route
    return session


_GOOD_ALBUM = {"id": 1, "link": "https://x/1", "release_date": "2020-01-01"}
_GOOD_TRACKS = {"data": [{"title": "Real Track", "duration": 200}]}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("album_body", "tracks_body"),
    [
        (["not", "a", "dict"], _GOOD_TRACKS),
        ("a string", _GOOD_TRACKS),
    ],
    ids=["album_list", "album_string"],
)
async def test_fetch_deezer_album_reads_a_strange_body_as_a_miss(
    album_body, tracks_body
):
    """
    GIVEN /album/{id} answers 200 with a body of an unexpected shape (a list,
    a string)
    WHEN fetch_deezer_album runs
    THEN it returns None, a miss, exactly as the search does: never a
    TypeError or AttributeError, which would publish internal_error for the
    whole job.
    """
    session = _album_session(album_body, tracks_body)

    with patch(
        "scrobblescope.deezer.get_deezer_limiter", return_value=NoopAsyncContext()
    ):
        result = await fetch_deezer_album(session, 1)

    assert result is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "tracks_body",
    [
        {},
        None,
        ["not", "a", "dict"],
        "a string",
        {"data": None},
        {"data": "not a list"},
        {"data": {"title": "Real Track"}},
    ],
    ids=[
        "tracks_empty_object",
        "tracks_json_null",
        "tracks_list",
        "tracks_string",
        "tracks_null_data",
        "tracks_string_data",
        "tracks_object_data",
    ],
)
async def test_fetch_deezer_album_keeps_the_album_when_the_track_list_is_unreadable(
    tracks_body,
):
    """
    GIVEN a readable album body but a tracks body with no usable `data` list
    (missing key, null, a string, an object, or not an object at all, the
    whole body being JSON null included)
    WHEN fetch_deezer_album runs
    THEN the album is kept with its release metadata and no track durations:
    only an album body that cannot be read is a miss (the pre-15a behaviour
    for a missing `data` key).
    """
    session = _album_session(_GOOD_ALBUM, tracks_body)

    with patch(
        "scrobblescope.deezer.get_deezer_limiter", return_value=NoopAsyncContext()
    ):
        result = await fetch_deezer_album(session, 1)

    assert result is not None
    assert result.release_date == "2020-01-01"
    assert result.url == "https://x/1"
    assert result.track_durations == {}


@pytest.mark.asyncio
async def test_fetch_deezer_album_keeps_the_album_when_optional_fields_are_odd():
    """
    GIVEN an album whose link, release date and cover are null or not text, and
    tracks whose durations are null, text or a bool
    WHEN fetch_deezer_album runs
    THEN the album is still returned, with the defaults for what was odd and a
    duration of 0 for each odd one: a null duration left in the map would raise
    TypeError in the play-time sum later.
    """
    album = {"id": 1, "link": None, "release_date": None, "cover_xl": 42}
    tracks = {
        "data": [
            {"title": "Null", "duration": None},
            {"title": "Text", "duration": "180"},
            {"title": "Bool", "duration": True},
            {"title": "Good", "duration": 200},
        ]
    }
    session = _album_session(album, tracks)

    with patch(
        "scrobblescope.deezer.get_deezer_limiter", return_value=NoopAsyncContext()
    ):
        result = await fetch_deezer_album(session, 7)

    assert result.url == "https://www.deezer.com/album/7"
    assert result.release_date == ""
    assert result.image_url is None
    assert result.track_durations == {"null": 0, "text": 0, "bool": 0, "good": 200}


# --- HTTP-status refusals are "could not answer" (R4-backend-1) ---------------


def _http_status(status, retry_after=None):
    resp = AsyncMock()
    resp.status = status
    resp.headers = {"Retry-After": retry_after} if retry_after else {}
    return resp


@pytest.mark.asyncio
async def test_deezer_http_429_honours_retry_after_then_succeeds():
    """
    GIVEN Deezer answers HTTP 429 with Retry-After: 3, then a match
    WHEN search_deezer_album runs
    THEN it sleeps the stated 3 seconds and returns the id: a throttle is a
    wait, not "no match".
    """
    session = MagicMock()
    found = AsyncMock()
    found.status = 200
    found.json = AsyncMock(
        return_value={
            "data": [{"id": 7, "title": "Album", "artist": {"name": "Artist"}}]
        }
    )
    session.get.side_effect = [
        make_response_context(_http_status(429, retry_after="3")),
        make_response_context(found),
    ]

    with (
        patch(
            "scrobblescope.deezer.get_deezer_limiter", return_value=NoopAsyncContext()
        ),
        patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
    ):
        result = await search_deezer_album(session, "Artist", "Album", retries=2)

    assert result == 7
    mock_sleep.assert_awaited_once_with(3)


@pytest.mark.asyncio
async def test_deezer_http_429_on_every_attempt_raises_rate_limited_not_no_match():
    """
    GIVEN Deezer answers HTTP 429 on every attempt
    WHEN search_deezer_album runs
    THEN ProviderError deezer_rate_limited is raised, not None.
    """
    session = MagicMock()
    session.get.return_value = make_response_context(_http_status(429))

    with (
        patch(
            "scrobblescope.deezer.get_deezer_limiter", return_value=NoopAsyncContext()
        ),
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        with pytest.raises(ProviderError) as excinfo:
            await search_deezer_album(session, "Artist", "Album", retries=2)

    assert excinfo.value.code == "deezer_rate_limited"
    assert session.get.call_count == 2


@pytest.mark.asyncio
async def test_deezer_http_403_raises_unavailable_not_no_match():
    """
    GIVEN Deezer answers HTTP 403 on every attempt
    WHEN search_deezer_album runs
    THEN ProviderError deezer_unavailable is raised, not None.
    """
    session = MagicMock()
    session.get.return_value = make_response_context(_http_status(403))

    with (
        patch(
            "scrobblescope.deezer.get_deezer_limiter", return_value=NoopAsyncContext()
        ),
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        with pytest.raises(ProviderError) as excinfo:
            await search_deezer_album(session, "Artist", "Album", retries=2)

    assert excinfo.value.code == "deezer_unavailable"
    assert session.get.call_count == 2


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "tracks_answer",
    [{"error": {"type": "DataException", "code": 800}}, None],
    ids=["error_body_800", "http_404"],
)
async def test_fetch_deezer_album_is_a_miss_when_the_track_call_ends_in_an_error(
    tracks_answer,
):
    """
    GIVEN a readable album body but a /tracks call that ends in a terminal
    error (an error body, or HTTP 404)
    WHEN fetch_deezer_album runs
    THEN it returns None, a miss that is not persisted: an album kept with no
    durations would sit in the 30-day cache and vanish from the playtime
    ranking even after Deezer recovers.
    """
    session = MagicMock()
    album_resp = AsyncMock()
    album_resp.status = 200
    album_resp.json = AsyncMock(return_value=_GOOD_ALBUM)
    tracks_resp = AsyncMock()
    if tracks_answer is None:
        tracks_resp.status = 404
    else:
        tracks_resp.status = 200
        tracks_resp.json = AsyncMock(return_value=tracks_answer)

    def route(url, params=None, **kwargs):
        return make_response_context(
            tracks_resp if url.endswith("/tracks") else album_resp
        )

    session.get.side_effect = route

    with patch(
        "scrobblescope.deezer.get_deezer_limiter", return_value=NoopAsyncContext()
    ):
        result = await fetch_deezer_album(session, 1)

    assert result is None
