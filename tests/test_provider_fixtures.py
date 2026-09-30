import json
from datetime import date
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from tests.helpers import SPOTIFY_ALBUM_DETAILS_MOCK

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name):
    return json.loads((FIXTURES / name).read_text())


def test_spotify_fixture_has_every_field_the_app_reads():
    """A field the app reads but the doc-transcribed fixture lacks would
    already fail here (F-MAS-1)."""
    from scrobblescope.spotify import album_metadata_from_details

    album = _load("spotify_get_album.json")
    meta = album_metadata_from_details("sp1", album)

    assert meta.release_date == album["release_date"]
    assert meta.url == album["external_urls"]["spotify"]
    assert meta.image_url == album["images"][0]["url"]
    assert meta.track_durations  # at least one track survived translation


def test_lastfm_fixture_flows_through_aggregate_daily_counts():
    """Runs the fixture through the heatmap's real aggregator instead of just
    asserting the fixture has fields nobody reads: `date.uts` is what
    `_aggregate_daily_counts` keys scrobbles off of, so a fixture that drops
    or renames it fails here, not just in a hand-written field check."""
    from scrobblescope.heatmap import _aggregate_daily_counts

    page = _load("lastfm_recenttracks_page.json")

    counts = _aggregate_daily_counts([page], date(2008, 6, 9), date(2008, 6, 9))

    assert counts == {"2008-06-09": 1}


@pytest.mark.asyncio
async def test_lastfm_fixture_flows_through_fetch_top_albums():
    """Runs the fixture through the real orchestrator pipeline: a fixture
    missing `artist.#text`, `album.#text` or `date.uts` would fail to
    produce an eligible album here."""
    from scrobblescope.domain import normalize_name
    from scrobblescope.orchestrator import fetch_top_albums_async

    page = _load("lastfm_recenttracks_page.json")
    track = page["recenttracks"]["track"][0]

    with patch(
        "scrobblescope.orchestrator.fetch_all_recent_tracks_async",
        new_callable=AsyncMock,
        return_value=(
            [page],
            {"status": "ok", "pages_expected": 1, "pages_received": 1},
        ),
    ):
        eligible, _, _ = await fetch_top_albums_async(
            "RJ", 2008, min_plays=1, min_tracks=1
        )

    key = normalize_name(track["artist"]["#text"], track["album"]["#text"])
    assert eligible[key]["original_artist"] == track["artist"]["#text"]
    assert eligible[key]["original_album"] == track["album"]["#text"]
    assert eligible[key]["play_count"] == 1


def test_existing_spotify_mocks_do_not_drift_from_the_transcribed_shape():
    """The orchestrator contract test's shared mock's keys must be a subset
    of the doc-transcribed fixture's -- the regression guard Q7 asks for."""
    fixture = _load("spotify_get_album.json")
    fixture_keys = set(fixture)

    assert set(SPOTIFY_ALBUM_DETAILS_MOCK) <= fixture_keys
    assert set(SPOTIFY_ALBUM_DETAILS_MOCK["images"][0]) <= set(fixture["images"][0])
    assert set(SPOTIFY_ALBUM_DETAILS_MOCK["tracks"]["items"][0]) <= set(
        fixture["tracks"]["items"][0]
    )
