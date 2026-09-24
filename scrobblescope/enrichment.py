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

    def as_cache_row(self, artist_norm: str, album_norm: str) -> tuple:
        """Return one row in the order ``_batch_persist_metadata`` unpacks.

        The keys are arguments because this object does not carry them: it
        describes an album a provider returned, not which lookup asked for
        it. The nine-element form is the provider-aware one: ``spotify_id``
        carries ``album_id`` only for a Spotify row, and ``provider_album_id``
        always carries the id the provider itself issued.
        """
        return (
            artist_norm,
            album_norm,
            # The legacy spotify_id column holds a Spotify id only. Any other
            # provider writes None there -- as the live Deezer fallback always
            # has -- and keeps its own id in provider_album_id below.
            self.album_id if self.provider == "spotify" else None,
            self.release_date,
            self.image_url,
            self.track_durations,
            self.provider,
            self.album_id,
            self.url,
        )
