from dataclasses import dataclass


@dataclass(frozen=True)
class AlbumMetadata:
    """Album metadata from any enrichment provider (Spotify, Deezer, ...).

    ``track_durations`` holds seconds keyed by ``normalize_track_name``, the
    shape ``_build_results`` already reads.
    """

    provider: str
    album_id: str
    url: str
    release_date: str
    image_url: str | None
    track_durations: dict[str, int]

    def as_cache_row_fields(self) -> tuple:
        return (
            self.provider,
            self.album_id,
            self.url,
            self.release_date,
            self.image_url,
            self.track_durations,
        )
