from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scrobblescope.deezer import fetch_deezer_album, search_deezer_album
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
async def test_fetch_deezer_album_returns_none_when_album_details_fail():
    """
    GIVEN the album-details request never succeeds
    WHEN fetch_deezer_album runs
    THEN it returns None without calling the tracks endpoint at all.
    """
    session = MagicMock()
    resp = AsyncMock()
    resp.status = 500
    session.get.return_value = make_response_context(resp)

    with patch(
        "scrobblescope.deezer.get_deezer_limiter", return_value=NoopAsyncContext()
    ):
        result = await fetch_deezer_album(session, 79484, retries=1)

    assert result is None
    assert session.get.call_count == 1


@pytest.mark.asyncio
async def test_fetch_deezer_album_returns_none_when_tracks_fail():
    """
    GIVEN album details succeed but the tracks endpoint never does
    WHEN fetch_deezer_album runs
    THEN it returns None rather than an AlbumMetadata with no durations.
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
        result = await fetch_deezer_album(session, 1, retries=1)

    assert result is None
