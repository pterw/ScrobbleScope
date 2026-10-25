"""Builders for the album records tests hand to the cache and the results."""

from scrobblescope.enrichment import AlbumMetadata


def spotify_metadata(
    album_id="sp1",
    release_date="2025-01-01",
    image_url="https://img.example.com/a.jpg",
    track_durations=None,
    provider_artist=None,
    provider_title=None,
):
    """A Spotify album as ``album_metadata_from_details`` would return it."""
    return AlbumMetadata(
        provider="spotify",
        album_id=album_id,
        url=f"https://open.spotify.com/album/{album_id}",
        release_date=release_date,
        image_url=image_url,
        track_durations={} if track_durations is None else track_durations,
        provider_artist=provider_artist,
        provider_title=provider_title,
    )


def deezer_metadata(
    album_id="dz1",
    release_date="2025-02-02",
    image_url="https://cdn.example/dz.jpg",
    track_durations=None,
):
    """A Deezer album as ``fetch_deezer_album`` would return it."""
    return AlbumMetadata(
        provider="deezer",
        album_id=album_id,
        url=f"https://www.deezer.com/album/{album_id}",
        release_date=release_date,
        image_url=image_url,
        track_durations={} if track_durations is None else track_durations,
    )
