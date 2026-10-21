"""Listening statistics -- the rules behind the figures a page states.

Pure functions, standard library only: no clock, no timezone database, no I/O.
Two things keep every figure in UTC without a runtime check:

* Day keys are ISO dates (``"2026-03-01"``) that the pipeline already
  attributed to a UTC day when it counted plays (``plays.aggregate_daily_counts``
  reads each play's date from its UTC timestamp, and ``Play`` refuses a
  timestamp that is not UTC). This module never re-reads a time of day.
* The reference day a streak counts back from is passed in. It is the window's
  last day, which the pipeline took from a UTC clock, so a server in another
  timezone cannot move it.

The one function that accepts a moment, ``utc_date``, converts it to UTC and
refuses a naive datetime.

Each ``*_statistics`` function returns ``{name: {"value": ..., "population":
"<sentence>"}}``. The population is the answer to "what is this figure a
figure of?" and travels with the value, so a page, a CSV column or a test can
quote it and the two cannot drift apart. Dependency chain: this module is a
leaf (standard library only); ``heatmap`` and ``routes.album_flow`` import it.
"""

from __future__ import annotations

from datetime import UTC, date, timedelta


def utc_date(moment):
    """Return the UTC calendar date of *moment*.

    Args:
        moment: A timezone-aware ``datetime`` in any zone.

    Raises:
        ValueError: *moment* is naive. Reading a naive time as UTC would be a
            guess about the server's zone, which is the bug this module exists
            to rule out.
    """
    if moment.tzinfo is None or moment.utcoffset() is None:
        raise ValueError("utc_date needs a timezone-aware datetime")
    return moment.astimezone(UTC).date()


def _plays_on(daily_counts, day):
    """Return the plays recorded for *day*, 0 when the window holds no such day."""
    return daily_counts.get(day.isoformat(), 0)


def current_streak(daily_counts, today):
    """Count the consecutive days with a play, ending *today* or the day before.

    If *today* has no play yet the streak may still end yesterday: a listener
    who opens the page in the morning, before playing anything, keeps the
    streak they had. Counting stops at the first quiet day, and a day outside
    the window is a quiet day, so a streak never reaches past the window's
    first day.

    Args:
        daily_counts: ``{"YYYY-MM-DD": plays}``, UTC days.
        today: The window's last day (a ``date``, not a ``datetime``).
    """
    day = today
    if not _plays_on(daily_counts, day):
        day -= timedelta(days=1)
    streak = 0
    while _plays_on(daily_counts, day):
        streak += 1
        day -= timedelta(days=1)
    return streak


def best_day(daily_counts):
    """Return ``(day, plays)`` for the busiest day, the earliest on a tie.

    Returns ``(None, 0)`` when no day has a play: with nothing played, no day
    is the best one.
    """
    best, best_count = None, 0
    for key in sorted(daily_counts):
        if daily_counts[key] > best_count:
            best, best_count = key, daily_counts[key]
    return (date.fromisoformat(best) if best else None), best_count


def daily_average(daily_counts):
    """Return plays per day over every day of the window, quiet days included.

    The result is not rounded: how many decimals to show is the renderer's
    business. An empty window averages 0.0.
    """
    if not daily_counts:
        return 0.0
    return sum(daily_counts.values()) / len(daily_counts)


def heatmap_statistics(daily_counts, today):
    """Return the heatmap's published figures, each with its population.

    Args:
        daily_counts: The zero-filled ``{"YYYY-MM-DD": plays}`` window.
        today: The window's last UTC day.
    """
    day, count = best_day(daily_counts)
    return {
        "total_plays": {
            "value": sum(daily_counts.values()),
            "population": "all plays inside the window",
        },
        "daily_average": {
            "value": daily_average(daily_counts),
            "population": (
                "all plays inside the window, over every UTC day of the window "
                "including the days with none"
            ),
        },
        "best_day": {
            "value": {"date": day.isoformat() if day else None, "count": count},
            "population": (
                "the UTC day with the most plays inside the window; "
                "the earliest day wins a tie"
            ),
        },
        "current_streak": {
            "value": current_streak(daily_counts, today),
            "population": (
                "consecutive UTC days with a play, ending on the window's last "
                "day or the day before it, counted back no further than the "
                "window's first day"
            ),
        },
    }


def _row_plays(row):
    """Return a result row's play count as an int (missing or null is 0)."""
    return int(row.get("play_count") or 0)


def _is_unmatched(row):
    """Return True for a row listed through include-unmatched, which no provider matched."""
    return bool(row.get("unmatched_reason"))


def album_play_statistics(rows):
    """Return the Results page's play figures, each with its population.

    Args:
        rows: The result rows the page is about to list, after every filter the
            page applies (release window, limit, playtime ranking).

    ``plays_listed`` counts every row; ``plays_matched`` leaves out rows listed
    through the include-unmatched control. On a run without that control the
    two are equal.
    """
    rows = list(rows)
    return {
        "plays_listed": {
            "value": sum(_row_plays(row) for row in rows),
            "population": (
                "plays of every album row the page lists, including albums "
                "listed through include-unmatched"
            ),
        },
        "plays_matched": {
            "value": sum(_row_plays(row) for row in rows if not _is_unmatched(row)),
            "population": (
                "plays of the album rows a provider matched; albums listed "
                "through include-unmatched (unmatched) are left out"
            ),
        },
    }
