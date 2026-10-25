import dataclasses

import pytest

from scrobblescope.enrichment import (
    MATCH_FITS,
    MATCH_UNSTAMPED,
    MATCH_WRONG,
    SPOTIFY_ALBUM_URL,
    AlbumMetadata,
)


def test_album_metadata_carries_its_provider_and_url():
    meta = AlbumMetadata(
        provider="deezer",
        album_id="6237061",
        url="https://www.deezer.com/album/6237061",
        release_date="1977-02-04",
        image_url="https://cdn.example/cover.jpg",
        track_durations={"dreams": 260},
    )
    assert meta.provider == "deezer"
    assert meta.url == "https://www.deezer.com/album/6237061"


def _row(**overrides):
    """A modern spotify_cache row for a Spotify album; override columns freely."""
    row = {
        "spotify_id": "sp1",
        "release_date": "1997-06-16",
        "album_image_url": "https://img.example.com/ok.jpg",
        "track_durations": {"paranoid android": 383},
        "provider": "spotify",
        "provider_album_id": "sp1",
        "provider_url": "https://open.spotify.com/album/sp1",
    }
    row.update(overrides)
    return row


_DEEZER_COLUMNS = {
    "spotify_id": None,
    "provider": "deezer",
    "provider_album_id": "6237061",
    "provider_url": "https://www.deezer.com/album/6237061",
}


def test_only_a_spotify_album_has_a_spotify_id():
    """The legacy spotify_id column and the Results page's spotify_id field hold
    a Spotify id and nothing else; a Deezer id is not one."""
    spotify = AlbumMetadata.from_row(_row())
    deezer = AlbumMetadata.from_row(_row(**_DEEZER_COLUMNS))

    assert spotify.spotify_id == "sp1"
    assert deezer.spotify_id is None


def test_a_stored_row_maps_every_field_to_the_album():
    """Each column lands in its own field (distinct values, so a swap shows)."""
    album = AlbumMetadata.from_row(_row())

    assert album == AlbumMetadata(
        provider="spotify",
        album_id="sp1",
        url="https://open.spotify.com/album/sp1",
        release_date="1997-06-16",
        image_url="https://img.example.com/ok.jpg",
        track_durations={"paranoid android": 383},
    )


def test_a_deezer_row_keeps_the_deezer_id_and_link():
    """A Deezer row has no spotify_id; its id and link come from the provider
    columns."""
    album = AlbumMetadata.from_row(_row(**_DEEZER_COLUMNS))

    assert album is not None
    assert (album.provider, album.album_id, album.url) == (
        "deezer",
        "6237061",
        "https://www.deezer.com/album/6237061",
    )


def test_a_deezer_row_with_no_stored_link_has_no_link():
    """Only a Spotify album can be given a link from its id; a Deezer id on a
    Spotify page would point at the wrong album, so the link stays empty."""
    album = AlbumMetadata.from_row(_row(**{**_DEEZER_COLUMNS, "provider_url": None}))

    assert album is not None
    assert (album.provider, album.album_id) == ("deezer", "6237061")
    assert album.url == ""


@pytest.mark.parametrize(
    "columns",
    [
        {"provider": None, "provider_album_id": None, "provider_url": None},
        {"provider_url": None},
    ],
    ids=["written_before_the_provider_columns", "backfilled_without_a_link"],
)
def test_an_older_spotify_row_is_a_spotify_album_with_the_classic_link(columns):
    """A row with no provider value is a Spotify row, and a Spotify row with no
    stored link gets Spotify's classic album page, as the Results page has
    always shown it."""
    album = AlbumMetadata.from_row(_row(**columns))

    assert album is not None
    assert (album.provider, album.album_id) == ("spotify", "sp1")
    assert album.url == SPOTIFY_ALBUM_URL.format(album_id="sp1")
    assert album.url == "https://open.spotify.com/album/sp1"


@pytest.mark.parametrize(
    ("stored", "expected"),
    [
        ('{"a": 1, "b": 2}', {"a": 1, "b": 2}),
        ({"a": 1}, {"a": 1}),
        ("{}", {}),
        ("", {}),
        (None, {}),
    ],
    ids=["json_text", "dict", "empty_object", "empty_text", "null"],
)
def test_track_durations_read_as_a_dict_whatever_the_driver_returned(stored, expected):
    """asyncpg returns JSONB as text unless a codec is registered; either way the
    album's durations are a dict, empty when there are none."""
    assert AlbumMetadata.from_row(_row(track_durations=stored)).track_durations == (
        expected
    )


def test_a_row_with_no_release_date_has_an_empty_one():
    """release_date is a nullable column. An album with no date is excluded by
    every release scope but "all"; it must not carry None into the filter, which
    splits the date as text."""
    assert AlbumMetadata.from_row(_row(release_date=None)).release_date == ""


@pytest.mark.parametrize(
    "columns",
    [
        {"provider": None, "spotify_id": None, "provider_album_id": None},
        {"provider": "deezer", "spotify_id": None, "provider_album_id": None},
    ],
    ids=["no_provider", "no_album_id"],
)
def test_a_row_that_names_no_provider_album_reads_as_nothing(columns):
    """Such a row cannot be shown or linked; reading it as None makes it a cache
    miss that the next fetch overwrites."""
    assert AlbumMetadata.from_row(_row(**columns)) is None


def test_album_metadata_holds_album_facts_only():
    """These fields are the shared cache's columns (BATCH23 "Data handling":
    shared cache rows contain no listening facts). Adding a field here adds a
    column there, so the field set is pinned: a change must be deliberate."""
    assert {field.name for field in dataclasses.fields(AlbumMetadata)} == {
        "provider",
        "album_id",
        "url",
        "release_date",
        "image_url",
        "track_durations",
        "provider_artist",
        "provider_title",
    }


def test_a_row_reads_the_providers_own_names_and_a_row_without_them_reads_none():
    """The two name columns land in their fields; a pre-migration row (columns
    absent from the mapping) and a NULL both read as None."""
    named = AlbumMetadata.from_row(
        _row(provider_artist="Xiu Xiu", provider_title="A Promise")
    )
    absent = AlbumMetadata.from_row(_row())
    null = AlbumMetadata.from_row(_row(provider_artist=None, provider_title=None))

    assert (named.provider_artist, named.provider_title) == ("Xiu Xiu", "A Promise")
    assert (absent.provider_artist, absent.provider_title) == (None, None)
    assert (null.provider_artist, null.provider_title) == (None, None)


_XIU_KEY = ("xiu xiu", "a promise")


@pytest.mark.parametrize(
    ("columns", "expected"),
    [
        (
            {"provider_artist": "Xiu Xiu", "provider_title": "A Promise"},
            MATCH_FITS,
        ),
        (
            {"provider_artist": "Captain Beefheart", "provider_title": "Safe As Milk"},
            MATCH_WRONG,
        ),
        (
            {"provider_artist": "Xiu Xiu", "provider_title": "A Promise 2"},
            MATCH_WRONG,
        ),
        ({"provider_artist": None, "provider_title": None}, MATCH_UNSTAMPED),
        ({"provider_artist": "Xiu Xiu", "provider_title": None}, MATCH_UNSTAMPED),
        ({"provider_artist": None, "provider_title": "A Promise"}, MATCH_UNSTAMPED),
        (
            {**_DEEZER_COLUMNS, "provider_artist": None, "provider_title": None},
            MATCH_FITS,
        ),
    ],
    ids=[
        "names_equal_the_key",
        "another_artists_album",
        "a_sibling_title",
        "no_names",
        "no_title",
        "no_artist",
        "deezer_needs_no_names",
    ],
)
def test_match_for_says_whether_a_cached_row_fits_its_key(columns, expected):
    """A Spotify row fits only when its stored names normalize to the key; a
    Spotify row with either name NULL is unstamped; any other provider fits."""
    album = AlbumMetadata.from_row(_row(**columns))

    assert album.match_for(_XIU_KEY) == expected
