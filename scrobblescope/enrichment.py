import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from scrobblescope.domain import normalize_name

#: Spotify's classic album page. A cache row older than the provider columns
#: carries no link, and a Spotify payload that names none falls back to this.
SPOTIFY_ALBUM_URL = "https://open.spotify.com/album/{album_id}"

#: What ``AlbumMetadata.match_for`` says about a cached row and a key.
MATCH_FITS = "fits"
MATCH_WRONG = "wrong"
MATCH_UNSTAMPED = "unstamped"


@dataclass(frozen=True)
class AlbumMetadata:
    """Album metadata from any enrichment provider (Spotify, Deezer, ...).

    ``track_durations`` holds seconds keyed by ``normalize_track_name``, the
    shape ``_build_results`` already reads. ``provider_artist`` and
    ``provider_title`` are the names the provider itself gave the album (None
    for a row written before they were stored); ``match_for`` compares them
    with the key the row is cached under.
    """

    provider: str
    album_id: str
    url: str
    release_date: str
    image_url: str | None
    track_durations: dict[str, int]
    provider_artist: str | None = None
    provider_title: str | None = None

    @property
    def spotify_id(self) -> str | None:
        """The Spotify album id, or None for an album from any other provider.

        The legacy ``spotify_id`` column and the Results page's ``spotify_id``
        field hold a Spotify id only. A Deezer album keeps its own id in
        ``album_id``.
        """
        return self.album_id if self.provider == "spotify" else None

    def match_for(self, key: tuple[str, str]) -> str:
        """Say whether this row is the album ``key`` asks for.

        The one place the re-verify rule lives. Any provider but Spotify is
        ``MATCH_FITS`` (Deezer accepts a candidate only on an exact key match).
        A Spotify row with either name missing is ``MATCH_UNSTAMPED``; with both
        present it is ``MATCH_FITS`` when they normalize to ``key``, else
        ``MATCH_WRONG``.
        """
        if self.provider != "spotify":
            return MATCH_FITS
        if self.provider_artist is None or self.provider_title is None:
            return MATCH_UNSTAMPED
        fits = normalize_name(self.provider_artist, self.provider_title) == key
        return MATCH_FITS if fits else MATCH_WRONG

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
            provider_artist=row.get("provider_artist"),
            provider_title=row.get("provider_title"),
        )
