"""Normalized listening facts and the pure calculations over them.

A ``Play`` is one listen, however its source reported it: when, and the artist,
album and track names. Last.fm scrobbles become plays inside ``lastfm.py``;
Batch 23's Spotify export parser emits the same record. Everything downstream
(the album calculation, the heatmap) reads plays and never the shape of a
provider's payload (Global Rule 4).

A ``Play`` carries nothing else, so it cannot carry listener identity: no
username, IP address, user agent, country or platform (``BATCH23_DEFINITION.md``
"Data handling"). Rules that belong to one source -- Last.fm's now-playing
entry, the export's 30-second and private-session rules -- are applied by that
source's own module before a ``Play`` exists, never here.

    plays <- domain
"""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import TypedDict

from scrobblescope.domain import normalize_name, normalize_track_name

#: An album's identity: ``domain.normalize_name(artist, album)``.
AlbumKey = tuple[str, str]


@dataclass(frozen=True, slots=True)
class Play:
    """One listen. ``played_at`` is UTC to the second; a name is ``""`` when
    the source gave none."""

    played_at: datetime
    artist: str
    album: str
    track: str

    def __post_init__(self):
        """Refuse any timestamp whose ``tzinfo`` is not exactly ``datetime.UTC``.

        A naive datetime would be read as local time by ``.timestamp()`` and
        attribute a listen to the wrong day on a host that is not UTC; a source
        that forgot to convert fails here, at the border.
        """
        if self.played_at.tzinfo is not UTC:
            raise ValueError("Play.played_at must be a datetime with tzinfo UTC")


@dataclass(frozen=True, slots=True)
class Window:
    """A span of time, inclusive at both ends, both bounds UTC."""

    start: datetime
    end: datetime

    def __post_init__(self):
        """Refuse a bound that is not UTC and a window that ends before it starts."""
        for bound in (self.start, self.end):
            if bound.tzinfo is not UTC:
                raise ValueError("Window bounds must be datetimes with tzinfo UTC")
        if self.start > self.end:
            raise ValueError("Window.start must not be after Window.end")

    @classmethod
    def year(cls, year: int) -> "Window":
        """Return January 1 00:00:00 to December 31 23:59:59 of *year*, UTC."""
        return cls(
            start=datetime(year, 1, 1, tzinfo=UTC),
            end=datetime(year, 12, 31, 23, 59, 59, tzinfo=UTC),
        )

    def start_ts(self) -> int:
        """Return the start as epoch seconds, the form the Last.fm API takes."""
        return int(self.start.timestamp())

    def end_ts(self) -> int:
        """Return the end as epoch seconds, the form the Last.fm API takes."""
        return int(self.end.timestamp())

    def contains(self, played_at: datetime) -> bool:
        """Return whether *played_at* lies in the window, ends included."""
        return self.start <= played_at <= self.end


class AlbumTally(TypedDict):
    """What the album calculation knows about one album.

    A ``TypedDict`` on purpose: it is named and typed, but still a plain dict
    at runtime, so ``partition_albums_by_threshold``, ``_apply_pre_slice``,
    ``_build_results`` and the Deezer fallback read it unchanged.
    """

    play_count: int
    track_counts: dict[str, int]
    original_artist: str
    original_album: str


@dataclass(frozen=True, slots=True)
class AlbumAggregate:
    """Every album found in a window, before any threshold is applied.

    ``plays_seen`` counts the plays offered, including those outside the window
    and those too incomplete to be an album play, so a job's scrobble total
    matches what the source returned.
    """

    albums: dict[AlbumKey, AlbumTally]
    plays_seen: int


def aggregate_albums(plays: Iterable[Play], window: Window) -> AlbumAggregate:
    """Group the plays inside *window* into albums.

    A play with an empty artist, album or track name is not an album play (the
    heatmap, which needs only the date, still counts it). Albums are keyed by
    ``normalize_name``; the first spelling seen names the album, and tracks are
    keyed by ``normalize_track_name`` so spellings that normalize alike are one
    track. Pure: no I/O, no clock.
    """
    albums: dict[AlbumKey, AlbumTally] = {}
    seen = 0
    for play in plays:
        seen += 1
        if not window.contains(play.played_at):
            continue
        if not (play.artist and play.album and play.track):
            continue
        key = normalize_name(play.artist, play.album)
        tally = albums.get(key)
        if tally is None:
            tally = albums[key] = {
                "play_count": 0,
                "track_counts": {},
                "original_artist": play.artist,
                "original_album": play.album,
            }
        tally["play_count"] += 1
        track = normalize_track_name(play.track)
        tally["track_counts"][track] = tally["track_counts"].get(track, 0) + 1
    return AlbumAggregate(albums=albums, plays_seen=seen)


def zero_fill_daily_counts(counts, from_date: date, to_date: date) -> dict[str, int]:
    """Fill every calendar date in ``[from_date, to_date]`` with 0 where missing.

    Args:
        counts: Mapping of ``"YYYY-MM-DD"`` strings to integer counts for dates that had at least one play.
        from_date: Inclusive start date.
        to_date: Inclusive end date.

    Returns:
        A new dict with every ISO date in the range present, each mapped to
        ``counts.get(key, 0)``.
    """
    daily_counts = {}
    current = from_date
    while current <= to_date:
        key = current.isoformat()
        daily_counts[key] = counts.get(key, 0)
        current += timedelta(days=1)
    return daily_counts


def aggregate_daily_counts(
    plays: Iterable[Play], from_date: date, to_date: date
) -> dict[str, int]:
    """Count plays per UTC calendar day over ``[from_date, to_date]``.

    Every date in the range is present; a day with no plays maps to ``0``. A
    play's day is read straight from its UTC timestamp. Plays outside the range
    are ignored. The names on a play are not consulted: the heatmap counts every
    dated listen. Pure: no I/O, no clock.
    """
    counts: dict[str, int] = {}
    for play in plays:
        day = play.played_at.date()
        if from_date <= day <= to_date:
            key = day.isoformat()
            counts[key] = counts.get(key, 0) + 1
    return zero_fill_daily_counts(counts, from_date, to_date)
