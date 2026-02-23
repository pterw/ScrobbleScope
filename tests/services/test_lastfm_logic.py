"""Tests for fetch_top_albums_async business logic.

Covers aggregation, min_plays/min_tracks filters, timestamp-boundary
enforcement, the now-playing sentinel, non-Latin track deduplication,
and fetch-metadata stat reporting.  Network calls are fully mocked.
"""

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from scrobblescope.lastfm import fetch_top_albums_async

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _track(artist, album, name, year=2023, month=6, day=15):
    """Build a minimal Last.fm track dict with a timestamp in the given year."""
    ts = int(datetime(year, month, day).timestamp())
    return {
        "artist": {"#text": artist},
        "album": {"#text": album},
        "name": name,
        "date": {"uts": str(ts)},
    }


def _page(tracks):
    """Wrap a list of track dicts in a Last.fm recenttracks page envelope."""
    return {"recenttracks": {"track": tracks}}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fetch_top_albums_aggregates_play_counts():
    """
    GIVEN 15 scrobbles spanning 4 distinct tracks from the same album
    WHEN fetch_top_albums_async runs with min_plays=10, min_tracks=3
    THEN the album appears in results with play_count=15 and 4 distinct tracks.
    """
    tracks = (
        [_track("Radiohead", "OK Computer", "Paranoid Android")] * 5
        + [_track("Radiohead", "OK Computer", "Karma Police")] * 4
        + [_track("Radiohead", "OK Computer", "Airbag")] * 3
        + [_track("Radiohead", "OK Computer", "Exit Music")] * 3
    )
    pages = [_page(tracks)]
    fetch_meta = {"status": "ok", "pages_expected": 1, "pages_received": 1}

    with (
        patch(
            "scrobblescope.lastfm.fetch_all_recent_tracks_async",
            new=AsyncMock(return_value=(pages, fetch_meta)),
        ),
    ):
        result, _ = await fetch_top_albums_async("testuser", 2023)

    assert len(result) == 1
    key = next(iter(result))
    assert result[key]["play_count"] == 15
    assert len(result[key]["track_counts"]) == 4


@pytest.mark.asyncio
async def test_fetch_top_albums_min_plays_filter():
    """
    GIVEN album A with 8 plays (below default min_plays=10) and album B with 12
    WHEN fetch_top_albums_async runs with default thresholds
    THEN only album B survives the filter.
    """
    tracks_a = [_track("Artist A", "Album A", f"Track {i}") for i in range(8)]
    tracks_b = [_track("Artist B", "Album B", f"Track {i}") for i in range(12)]
    pages = [_page(tracks_a + tracks_b)]
    fetch_meta = {"status": "ok"}

    with (
        patch(
            "scrobblescope.lastfm.fetch_all_recent_tracks_async",
            new=AsyncMock(return_value=(pages, fetch_meta)),
        ),
    ):
        result, _ = await fetch_top_albums_async("testuser", 2023)

    artist_keys = {v["original_artist"] for v in result.values()}
    assert "Artist B" in artist_keys
    assert "Artist A" not in artist_keys


@pytest.mark.asyncio
async def test_fetch_top_albums_min_tracks_filter():
    """
    GIVEN album A with 15 plays but only 2 distinct track names (below min_tracks=3)
    and album B with 15 plays and 5 distinct track names (above min_tracks=3)
    WHEN fetch_top_albums_async runs with default thresholds
    THEN only album B is returned.
    """
    tracks_a = [_track("Artist A", "Album A", "Song One")] * 8 + [
        _track("Artist A", "Album A", "Song Two")
    ] * 7
    tracks_b = [_track("Artist B", "Album B", f"Song {i}") for i in range(5)] * 3
    pages = [_page(tracks_a + tracks_b)]
    fetch_meta = {"status": "ok"}

    with (
        patch(
            "scrobblescope.lastfm.fetch_all_recent_tracks_async",
            new=AsyncMock(return_value=(pages, fetch_meta)),
        ),
    ):
        result, _ = await fetch_top_albums_async("testuser", 2023)

    artist_keys = {v["original_artist"] for v in result.values()}
    assert "Artist B" in artist_keys
    assert "Artist A" not in artist_keys


@pytest.mark.asyncio
async def test_fetch_top_albums_skips_out_of_bounds_timestamps():
    """
    GIVEN tracks from year 2020 included in the API response for a 2023 request
    WHEN fetch_top_albums_async runs
    THEN the 2020 tracks are silently excluded and do not inflate play counts.
    """
    out_of_bounds = [
        _track("Artist X", "Album X", f"Track {i}", year=2020) for i in range(12)
    ]
    in_bounds = [_track("Artist Y", "Album Y", f"Track {i}") for i in range(10)]
    pages = [_page(out_of_bounds + in_bounds)]
    fetch_meta = {"status": "ok"}

    with (
        patch(
            "scrobblescope.lastfm.fetch_all_recent_tracks_async",
            new=AsyncMock(return_value=(pages, fetch_meta)),
        ),
    ):
        result, _ = await fetch_top_albums_async("testuser", 2023, min_plays=5)

    artist_keys = {v["original_artist"] for v in result.values()}
    assert "Artist X" not in artist_keys


@pytest.mark.asyncio
async def test_fetch_top_albums_skips_now_playing_track():
    """
    GIVEN a track without a 'date' field (the Last.fm 'now playing' sentinel)
    followed by 12 normal scrobbles
    WHEN fetch_top_albums_async runs
    THEN the now-playing entry is excluded; play_count must equal 12, not 13.
    """
    now_playing = {
        "artist": {"#text": "Artist Z"},
        "album": {"#text": "Album Z"},
        "name": "Now Playing Song",
        "@attr": {"nowplaying": "true"},
        # no 'date' key -- this is how Last.fm marks the currently playing track
    }
    normal_tracks = (
        [_track("Artist Z", "Album Z", "Song One")] * 4
        + [_track("Artist Z", "Album Z", "Song Two")] * 4
        + [_track("Artist Z", "Album Z", "Song Three")] * 4
    )
    pages = [_page([now_playing] + normal_tracks)]
    fetch_meta = {"status": "ok"}

    with (
        patch(
            "scrobblescope.lastfm.fetch_all_recent_tracks_async",
            new=AsyncMock(return_value=(pages, fetch_meta)),
        ),
    ):
        result, _ = await fetch_top_albums_async(
            "testuser", 2023, min_plays=10, min_tracks=3
        )

    assert len(result) == 1
    key = next(iter(result))
    assert result[key]["play_count"] == 12


@pytest.mark.asyncio
async def test_fetch_top_albums_non_latin_tracks_counted_distinctly():
    """
    GIVEN an album whose track names are Japanese katakana
    WHEN fetch_top_albums_async runs with min_plays=10, min_tracks=3
    THEN each distinct track name is preserved and counted separately so the
    album is NOT incorrectly eliminated by the min_tracks filter.

    Regression test: normalize_track_name previously used NFKD +
    encode('ascii', 'ignore'), collapsing every non-Latin track name to the
    empty string ''. That made len(track_counts) == 1 regardless of how many
    distinct Japanese tracks were played, silently failing the min_tracks
    filter and excluding the album from results entirely.
    """
    tracks = (
        # Katakana: "Gimme Chocolate!!", "Megitsune", "Iine!"
        [_track("BABYMETAL", "BABYMETAL", "\u30ae\u30df\u30c1\u30e7\u30b3\uff01\uff01")]
        * 6
        + [_track("BABYMETAL", "BABYMETAL", "\u30e1\u30ae\u30c4\u30cd")] * 6
        + [_track("BABYMETAL", "BABYMETAL", "\u3044\u3044\u306d\uff01")] * 6
    )
    pages = [_page(tracks)]
    fetch_meta = {"status": "ok"}

    with (
        patch(
            "scrobblescope.lastfm.fetch_all_recent_tracks_async",
            new=AsyncMock(return_value=(pages, fetch_meta)),
        ),
    ):
        result, _ = await fetch_top_albums_async(
            "testuser", 2023, min_plays=10, min_tracks=3
        )

    assert len(result) == 1, (
        "Japanese-titled album should survive the min_tracks filter. "
        "If 0 results, normalize_track_name is still stripping non-Latin characters."
    )
    key = next(iter(result))
    assert len(result[key]["track_counts"]) == 3


@pytest.mark.asyncio
async def test_fetch_top_albums_returns_stats_in_metadata():
    """
    GIVEN 18 scrobbles of one album with 3 distinct tracks (passes both filters)
    WHEN fetch_top_albums_async runs
    THEN fetch_metadata["stats"] contains total_scrobbles=18, unique_albums=1,
    and albums_passing_filter=1.
    """
    tracks = [_track("Artist A", "Album A", f"Track {i}") for i in range(3)] * 6
    pages = [_page(tracks)]
    fetch_meta = {"status": "ok"}

    with (
        patch(
            "scrobblescope.lastfm.fetch_all_recent_tracks_async",
            new=AsyncMock(return_value=(pages, fetch_meta)),
        ),
    ):
        _, metadata = await fetch_top_albums_async(
            "testuser", 2023, min_plays=10, min_tracks=3
        )

    stats = metadata["stats"]
    assert stats["total_scrobbles"] == 18
    assert stats["unique_albums"] == 1
    assert stats["albums_passing_filter"] == 1
