import json
from pathlib import Path

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


def test_lastfm_fixture_has_every_field_the_app_reads():
    """The recenttracks fixture carries every field callers key off of."""
    page = _load("lastfm_recenttracks_page.json")
    track = page["recenttracks"]["track"][0]

    assert track["artist"]["#text"]
    assert track["album"]["#text"]
    assert track["name"]
    assert track["date"]["uts"].isdigit()


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
