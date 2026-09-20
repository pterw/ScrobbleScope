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
        it. ``cache._batch_persist_metadata`` owns this order and documents
        it; the nine-element form is the provider-aware one, where
        ``provider_album_id`` repeats ``album_id`` because that is the id
        the provider itself issued.
        """
        return (
            artist_norm,
            album_norm,
            self.album_id,
            self.release_date,
            self.image_url,
            self.track_durations,
            self.provider,
            self.album_id,
            self.url,
        )
