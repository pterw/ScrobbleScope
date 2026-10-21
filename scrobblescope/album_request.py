"""The album request: one form, one validated record or one refusal.

The album form's fields used to be read, converted and checked inline in
``routes/album_flow.results_loading``, and only the year was ever validated:
a bad ``decade`` made every album fail the release filter, so the listener saw
"no albums" instead of a mistake. This module is the one owner of what a valid
album request is. ``parse_album_request`` is pure (no Flask, no I/O): a form
mapping and the current year go in, an ``AlbumRequest`` or a ``Refusal`` naming
the field and the sentence comes out. The Spotify export route (Batch 23 WP-4)
calls the same function with ``require_username=False``.

The sets and bounds below are the ones ``templates/index.html`` offers.
``tests/test_album_request.py`` reads the template and fails if the two drift.

    album_request <- jobs
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, fields

from scrobblescope import jobs

MIN_LISTENING_YEAR = 2002
MIN_RELEASE_YEAR = 1900
#: The limit ``/validate_user`` already enforces. The form's input allows 100
#: characters, but a Last.fm name is far shorter, so 64 refuses nothing real.
MAX_USERNAME_LENGTH = 64
MIN_PLAYS_BOUNDS = (1, 50)
MIN_TRACKS_BOUNDS = (1, 10)

SORT_MODES = ("playcount", "playtime")
RELEASE_SCOPES = ("same", "previous", "decade", "custom", "all")
DECADES = (
    "2020s",
    "2010s",
    "2000s",
    "1990s",
    "1980s",
    "1970s",
    "1960s",
    "1950s",
)
LIMIT_OPTIONS = ("all", "10", "25", "50", "100")

#: Every form field ``parse_album_request`` reads. The loading page's Retry
#: re-posts the form from this list's contract (tests read it from here).
FORM_FIELDS = (
    "username",
    "year",
    "sort_by",
    "include_unmatched",
    "release_scope",
    "decade",
    "release_year",
    "min_plays",
    "min_tracks",
    "limit_results",
)

# Defaults, declared once: AlbumRequest's field defaults and the parser's
# "missing means default" rule both read these.
DEFAULT_SORT_MODE = "playcount"
DEFAULT_RELEASE_SCOPE = "same"
DEFAULT_MIN_PLAYS = 10
DEFAULT_MIN_TRACKS = 3
DEFAULT_LIMIT = "all"


@dataclass(frozen=True)
class Refusal:
    """A form the listener must fix: the form field and the sentence to show."""

    field: str
    message: str


@dataclass(frozen=True)
class AlbumRequest:
    """A validated album request: the ten parameters a job runs with."""

    username: str | None
    year: int
    sort_mode: str = DEFAULT_SORT_MODE
    include_unmatched: bool = False
    release_scope: str = DEFAULT_RELEASE_SCOPE
    decade: str | None = None
    release_year: int | None = None
    min_plays: int = DEFAULT_MIN_PLAYS
    min_tracks: int = DEFAULT_MIN_TRACKS
    limit_results: str = DEFAULT_LIMIT

    def to_params(self):
        """Return the job record's params: the ten fields plus the job kind."""
        params = {f.name: getattr(self, f.name) for f in fields(self)}
        params["mode"] = jobs.MODE_ALBUM
        return params

    @classmethod
    def from_params(cls, params):
        """Rebuild a request from a job record's params.

        The record was written by ``to_params``, so nothing is re-validated.
        Keys that are not request fields (``mode``) are ignored; a record
        without ``username`` or ``year`` raises ``TypeError``.
        """
        names = {f.name for f in fields(cls)}
        return cls(**{key: value for key, value in params.items() if key in names})


def _text(form, key, default=None):
    """Return the stripped value of *key*, or *default* when absent or blank."""
    value = (form.get(key) or "").strip()
    return value if value else default


def _whole_number(raw):
    """Return *raw* as an int, or None when it is not a whole number."""
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _bounded(form, key, default, bounds, label):
    """Return ``(value, None)`` or ``(None, Refusal)`` for a bounded count."""
    raw = _text(form, key)
    if raw is None:
        return default, None
    low, high = bounds
    value = _whole_number(raw)
    if value is None or not low <= value <= high:
        return None, Refusal(
            key, f"{label} must be a whole number from {low} to {high}."
        )
    return value, None


def parse_album_request(
    form: Mapping, *, current_year: int, require_username: bool = True
):
    """Turn a submitted form into an ``AlbumRequest`` or a ``Refusal``.

    Checks run in the order the form reads, so the first problem a listener
    sees is the first field they would fix. A blank field counts as missing and
    takes its default. Only the release field of the chosen scope is kept: a
    hidden decade posted with a custom year cannot narrow the run. An include
    run (``include_unmatched == "1"``) is always a play-count run, because an
    unmatched album has no play time; the page disables the choice and this
    keeps a form posted without scripts to the same rule.

    Args:
        form: A mapping of field name to string (``request.form``).
        current_year: The upper bound for the listening and release years. The
            caller supplies it so this function stays pure and testable.
        require_username: False for the export route, which has no Last.fm
            name; the request then carries ``username=None``.
    """
    username = _text(form, "username")
    raw_year = _text(form, "year")
    if (require_username and username is None) or raw_year is None:
        if require_username:
            field = "username" if username is None else "year"
            return Refusal(field, "Username and year are required.")
        return Refusal("year", "Year is required.")
    if username is not None and len(username) > MAX_USERNAME_LENGTH:
        return Refusal("username", "Username is too long.")

    year = _whole_number(raw_year)
    if year is None:
        return Refusal("year", "Year must be a valid number.")
    if not MIN_LISTENING_YEAR <= year <= current_year:
        return Refusal(
            "year", f"Year must be between {MIN_LISTENING_YEAR} and {current_year}."
        )

    release_scope = _text(form, "release_scope", DEFAULT_RELEASE_SCOPE)
    if release_scope not in RELEASE_SCOPES:
        return Refusal("release_scope", "Choose a release filter from the list.")

    decade = None
    release_year = None
    if release_scope == "decade":
        decade = _text(form, "decade")
        if decade not in DECADES:
            return Refusal("decade", "Choose a decade from the list.")
    elif release_scope == "custom":
        raw_release_year = _text(form, "release_year")
        if raw_release_year is None:
            return Refusal("release_year", "Enter a release year.")
        release_year = _whole_number(raw_release_year)
        if release_year is None:
            return Refusal("release_year", "Release year must be a valid number.")
        if not MIN_RELEASE_YEAR <= release_year <= current_year:
            return Refusal(
                "release_year",
                f"Release year must be between {MIN_RELEASE_YEAR} and {current_year}.",
            )

    sort_mode = _text(form, "sort_by", DEFAULT_SORT_MODE)
    if sort_mode not in SORT_MODES:
        return Refusal("sort_by", "Choose Play count or Play time to rank by.")
    include_unmatched = form.get("include_unmatched") == "1"
    if include_unmatched and sort_mode == "playtime":
        sort_mode = "playcount"

    limit_results = _text(form, "limit_results", DEFAULT_LIMIT)
    if limit_results not in LIMIT_OPTIONS:
        return Refusal("limit_results", "Choose how many albums to show from the list.")

    min_plays, refusal = _bounded(
        form, "min_plays", DEFAULT_MIN_PLAYS, MIN_PLAYS_BOUNDS, "Minimum plays"
    )
    if refusal:
        return refusal
    min_tracks, refusal = _bounded(
        form,
        "min_tracks",
        DEFAULT_MIN_TRACKS,
        MIN_TRACKS_BOUNDS,
        "Minimum unique tracks",
    )
    if refusal:
        return refusal

    return AlbumRequest(
        username=username,
        year=year,
        sort_mode=sort_mode,
        include_unmatched=include_unmatched,
        release_scope=release_scope,
        decade=decade,
        release_year=release_year,
        min_plays=min_plays,
        min_tracks=min_tracks,
        limit_results=limit_results,
    )


def registration_refusal(year, registered_year):
    """Return a ``Refusal`` when *year* predates the Last.fm account, else None.

    The registration year is a hint, not a gate on the lookup: an account whose
    registration year Last.fm did not report (``None``) is never refused here.
    A failed lookup is not this function's concern: the pre-check refuses it
    before this is asked.
    """
    if registered_year and year < registered_year:
        return Refusal(
            "year",
            f"Year {year} is before your Last.fm registration year"
            f" ({registered_year}). Please choose {registered_year} or later.",
        )
    return None
