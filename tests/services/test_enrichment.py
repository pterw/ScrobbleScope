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
    assert meta.as_cache_row_fields() == (
        "deezer",
        "6237061",
        "https://www.deezer.com/album/6237061",
        "1977-02-04",
        "https://cdn.example/cover.jpg",
        {"dreams": 260},
    )
