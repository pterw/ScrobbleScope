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
        "6237061",
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
    assert row[2] == meta.album_id
    assert (row[6], row[7], row[8]) == (meta.provider, meta.album_id, meta.url)
