from scrobblescope.enrichment import AlbumMetadata


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
    assert meta.as_cache_row("fleetwood mac", "rumours") == (
        "fleetwood mac",
        "rumours",
        None,
        "1977-02-04",
        "https://cdn.example/cover.jpg",
        {"dreams": 260},
        "deezer",
        "6237061",
        "https://www.deezer.com/album/6237061",
    )


def test_cache_row_matches_what_the_persistence_layer_unpacks():
    """The row order is `_batch_persist_metadata`'s, not this module's.

    The previous shape led with `provider`, so a caller who passed it
    straight through would have written the provider name into
    `artist_norm`. Nothing called it, but the name invited exactly that.
    """
    meta = AlbumMetadata(
        provider="deezer",
        album_id="6237061",
        url="https://www.deezer.com/album/6237061",
        release_date="1977-02-04",
        image_url=None,
        track_durations={},
    )
    row = meta.as_cache_row("artist", "album")

    assert (row[0], row[1]) == ("artist", "album")
    # The spotify_id column holds a Spotify id only; a Deezer row carries its
    # id in provider_album_id (row[7]), as the live fallback always wrote it.
    assert row[2] is None
    assert (row[6], row[7], row[8]) == (meta.provider, meta.album_id, meta.url)


def test_cache_row_puts_a_spotify_album_id_in_the_spotify_column():
    """A Spotify row keeps its id in both spotify_id and provider_album_id."""
    meta = AlbumMetadata(
        provider="spotify",
        album_id="sp1",
        url="https://open.spotify.com/album/sp1",
        release_date="2025-01-01",
        image_url=None,
        track_durations={},
    )
    row = meta.as_cache_row("artist", "album")

    assert row[2] == "sp1"
    assert (row[6], row[7], row[8]) == (
        "spotify",
        "sp1",
        "https://open.spotify.com/album/sp1",
    )
