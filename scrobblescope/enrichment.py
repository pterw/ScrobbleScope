import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

#: Spotify's classic album page. A cache row older than the provider columns
#: carries no link, and a Spotify payload that names none falls back to this.
SPOTIFY_ALBUM_URL = "https://open.spotify.com/album/{album_id}"


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

    @property
    def spotify_id(self) -> str | None:
        """The Spotify album id, or None for an album from any other provider.

        The legacy ``spotify_id`` column and the Results page's ``spotify_id``
        field hold a Spotify id only. A Deezer album keeps its own id in
        ``album_id``.
        """
        return self.album_id if self.provider == "spotify" else None

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> "AlbumMetadata | None":
        """Read one ``spotify_cache`` row as an album, or None if it names none.

        The one place a stored row becomes an ``AlbumMetadata``. Rows written
        before the provider columns existed hold only ``spotify_id``: they are
        Spotify albums, and a Spotify album with no stored link gets
        ``SPOTIFY_ALBUM_URL``. A NULL release date reads as ``""`` and
        ``track_durations`` as a dict (the driver may hand back JSON text). A
        row with no provider and no album id returns None, so the caller treats
        it as a miss.

        Args:
            row: A mapping with the ``spotify_cache`` data columns, read with
                ``.get`` (an asyncpg ``Record`` or a dict).
        """
        spotify_id = row.get("spotify_id")
        provider = row.get("provider") or ("spotify" if spotify_id else None)
        album_id = row.get("provider_album_id") or spotify_id
        if not provider or not album_id:
            return None
        url = row.get("provider_url")
        if not url:
            url = (
                SPOTIFY_ALBUM_URL.format(album_id=album_id)
                if provider == "spotify"
                else ""
            )
        durations = row.get("track_durations")
        if isinstance(durations, str):
            durations = json.loads(durations) if durations else {}
        return cls(
            provider=provider,
            album_id=album_id,
            url=url,
            release_date=row.get("release_date") or "",
            image_url=row.get("album_image_url"),
            track_durations=durations or {},
        )

    def as_cache_row(self, artist_norm: str, album_norm: str) -> tuple:
        """Return one row in the order ``batch_persist_metadata`` unpacks.

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
