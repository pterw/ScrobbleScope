"""Tests for scrobblescope.plays: the record and the pure calculations over it.

The daily-count tests were moved here from tests/test_heatmap.py
(``TestAggregateDailyCounts``) when the calculation stopped reading raw Last.fm
pages; the eight converted ones keep their assertions.
"""

from datetime import UTC, date, datetime, time, timedelta, timezone

import pytest

from scrobblescope.domain import normalize_name, normalize_track_name
from scrobblescope.plays import (
    AlbumAggregate,
    Play,
    Window,
    aggregate_albums,
    aggregate_daily_counts,
    zero_fill_daily_counts,
)


def _play(when, artist="Artist", album="Album", track="Song"):
    return Play(played_at=when, artist=artist, album=album, track=track)


def _noon(day):
    return datetime.combine(day, time(12), tzinfo=UTC)


def _at(day, hour, minute=0, second=0):
    return datetime.combine(day, time(hour, minute, second), tzinfo=UTC)


# ---------------------------------------------------------------------------
# Play and Window
# ---------------------------------------------------------------------------


class TestPlay:
    def test_a_play_refuses_a_naive_timestamp(self):
        """A naive datetime would be read as local time by ``.timestamp()``; a
        source that forgot to convert must fail at the border, not three modules
        later. Planted defect: drop the check in ``Play.__post_init__``."""
        with pytest.raises(ValueError):
            _play(datetime(2023, 6, 15, 12))

    def test_a_play_refuses_a_timestamp_in_another_zone(self):
        """Only UTC counts: day, weekday and hour are read straight from the
        timestamp. Planted defect: accept any aware datetime."""
        minus_five = timezone(timedelta(hours=-5))
        with pytest.raises(ValueError):
            _play(datetime(2023, 6, 15, 12, tzinfo=minus_five))

    def test_a_utc_play_keeps_its_fields(self):
        """A play in UTC is accepted and keeps all four fields as given.
        Planted defect: invert the check in ``Play.__post_init__``, so UTC is the
        one zone refused."""
        when = datetime(2023, 6, 15, 12, tzinfo=UTC)
        play = _play(when, "A", "B", "C")
        assert (play.played_at, play.artist, play.album, play.track) == (
            when,
            "A",
            "B",
            "C",
        )


class TestWindow:
    def test_a_year_window_covers_the_calendar_year_in_epoch_seconds(self):
        """2023-01-01T00:00:00Z .. 2023-12-31T23:59:59Z, the literals the Last.fm
        request has always carried. Planted defect: an end bound one second late."""
        window = Window.year(2023)
        assert window.start_ts() == 1672531200
        assert window.end_ts() == 1704067199

    def test_contains_is_inclusive_at_both_ends(self):
        """Planted defect: make either end exclusive."""
        window = Window.year(2023)
        assert window.contains(window.start)
        assert window.contains(window.end)
        assert not window.contains(window.start - timedelta(seconds=1))
        assert not window.contains(window.end + timedelta(seconds=1))

    def test_a_window_refuses_a_naive_bound(self):
        """Planted defect: drop the UTC check on the bounds in
        ``Window.__post_init__``."""
        with pytest.raises(ValueError):
            Window(start=datetime(2023, 1, 1), end=datetime(2023, 1, 2, tzinfo=UTC))

    def test_a_window_refuses_a_reversed_span(self):
        """Planted defect: drop the ``start > end`` check."""
        with pytest.raises(ValueError):
            Window(
                start=datetime(2023, 1, 2, tzinfo=UTC),
                end=datetime(2023, 1, 1, tzinfo=UTC),
            )


# ---------------------------------------------------------------------------
# aggregate_albums
# ---------------------------------------------------------------------------


class TestAggregateAlbums:
    window = Window.year(2023)

    def test_no_plays_give_an_empty_aggregate(self):
        """Planted defect: start the plays-seen counter at 1."""
        assert aggregate_albums([], self.window) == AlbumAggregate({}, 0)

    def test_it_counts_plays_and_distinct_tracks_per_album(self):
        """Planted defect: count every play as a new track."""
        day = date(2023, 6, 15)
        plays = [
            _play(_at(day, 12, n), "Radiohead", "OK Computer", title)
            for n, title in enumerate(["Airbag", "Airbag", "Karma Police"])
        ]
        aggregate = aggregate_albums(plays, self.window)
        album = aggregate.albums[normalize_name("Radiohead", "OK Computer")]
        assert album["play_count"] == 3
        assert album["track_counts"] == {
            normalize_track_name("Airbag"): 2,
            normalize_track_name("Karma Police"): 1,
        }
        assert aggregate.plays_seen == 3

    def test_a_play_outside_the_window_is_seen_but_not_counted(self):
        """Planted defect: skip the window filter."""
        inside = _play(datetime(2023, 6, 15, tzinfo=UTC))
        outside = _play(datetime(2022, 12, 31, 23, 59, 59, tzinfo=UTC))
        aggregate = aggregate_albums([inside, outside], self.window)
        assert aggregate.albums[normalize_name("Artist", "Album")]["play_count"] == 1
        assert aggregate.plays_seen == 2

    @pytest.mark.parametrize(
        "names",
        [("", "Album", "Song"), ("Artist", "", "Song"), ("Artist", "Album", "")],
        ids=["no-artist", "no-album", "no-track"],
    )
    def test_a_play_missing_any_of_the_three_names_is_skipped(self, names):
        """An album needs all three names (the heatmap does not). Planted
        defect: drop the guard."""
        artist, album, track = names
        play = _play(datetime(2023, 6, 15, tzinfo=UTC), artist, album, track)
        aggregate = aggregate_albums([play], self.window)
        assert aggregate.albums == {}
        assert aggregate.plays_seen == 1

    def test_spellings_that_normalize_alike_are_one_album_named_by_the_first(self):
        """Planted defect: let the last spelling replace the first."""
        day = date(2023, 6, 15)
        plays = [
            _play(_at(day, 12, 0), "Mitski", "Be The Cowboy", "A"),
            _play(_at(day, 12, 1), "MITSKI", "be the cowboy (Deluxe Edition)", "B"),
        ]
        aggregate = aggregate_albums(plays, self.window)
        assert len(aggregate.albums) == 1
        album = next(iter(aggregate.albums.values()))
        assert album["play_count"] == 2
        assert (album["original_artist"], album["original_album"]) == (
            "Mitski",
            "Be The Cowboy",
        )

    def test_track_titles_that_normalize_alike_are_one_track(self):
        """Planted defect: key tracks by the raw title."""
        day = date(2023, 6, 15)
        plays = [
            _play(_at(day, 12, 0), track="Karma Police"),
            _play(_at(day, 12, 1), track="karma police"),
        ]
        album = next(iter(aggregate_albums(plays, self.window).albums.values()))
        assert len(album["track_counts"]) == 1

    def test_identical_plays_each_count(self):
        """Two listens at the same second are two listens. Planted defect:
        collapse equal plays (iterate ``set(plays)``)."""
        when = datetime(2023, 6, 15, 12, tzinfo=UTC)
        album = next(
            iter(
                aggregate_albums(
                    [_play(when), _play(when)], self.window
                ).albums.values()
            )
        )
        assert album["play_count"] == 2


# ---------------------------------------------------------------------------
# aggregate_daily_counts and zero_fill_daily_counts
# ---------------------------------------------------------------------------


class TestAggregateDailyCounts:
    def test_basic_counting(self):
        """Plays on known dates produce correct per-day counts."""
        plays = [
            _play(_noon(date(2026, 1, 1))),
            _play(_noon(date(2026, 1, 1))),
            _play(_noon(date(2026, 1, 3))),
        ]
        result = aggregate_daily_counts(plays, date(2026, 1, 1), date(2026, 1, 3))
        assert result["2026-01-01"] == 2
        assert result["2026-01-02"] == 0
        assert result["2026-01-03"] == 1

    def test_fills_365_days(self):
        """A 365-day range produces exactly 365 keys (non-leap year span)."""
        from_date, to_date = date(2025, 3, 8), date(2026, 3, 7)
        result = aggregate_daily_counts([], from_date, to_date)
        assert len(result) == (to_date - from_date).days + 1
        assert all(v == 0 for v in result.values())

    def test_fills_366_days_leap_year(self):
        """A range spanning Feb 29 of a leap year produces 366 keys."""
        result = aggregate_daily_counts([], date(2023, 3, 8), date(2024, 3, 7))
        assert len(result) == 366
        assert "2024-02-29" in result

    def test_boundary_timestamps(self):
        """Plays at exactly from_date's first second and to_date's last are included."""
        from_date, to_date = date(2026, 6, 1), date(2026, 6, 2)
        plays = [_play(_at(from_date, 0)), _play(_at(to_date, 23, 59, 59))]
        result = aggregate_daily_counts(plays, from_date, to_date)
        assert result["2026-06-01"] == 1
        assert result["2026-06-02"] == 1

    def test_out_of_range_excluded(self):
        """Plays outside [from_date, to_date] are excluded. Planted defect:
        remove both range limits (the filter and the zero-fill's own bounds),
        so out-of-range days reach the result."""
        from_date, to_date = date(2026, 5, 10), date(2026, 5, 12)
        plays = [
            _play(_at(date(2026, 5, 9), 23, 59, 59)),
            _play(_noon(date(2026, 5, 11))),
            _play(_at(date(2026, 5, 13), 0, 0, 1)),
        ]
        result = aggregate_daily_counts(plays, from_date, to_date)
        assert result["2026-05-11"] == 1
        assert sum(result.values()) == 1

    def test_no_plays_give_all_zeros(self):
        result = aggregate_daily_counts([], date(2026, 1, 1), date(2026, 1, 7))
        assert len(result) == 7
        assert all(v == 0 for v in result.values())

    def test_plays_from_several_pages_are_merged(self):
        """The calculation takes one flat sequence; page boundaries are gone."""
        plays = [
            _play(_noon(date(2026, 2, 1))),
            _play(_noon(date(2026, 2, 1))),
            _play(_noon(date(2026, 2, 2))),
        ]
        result = aggregate_daily_counts(plays, date(2026, 2, 1), date(2026, 2, 2))
        assert result["2026-02-01"] == 2
        assert result["2026-02-02"] == 1

    def test_midnight_boundary_attribution(self):
        """23:59:59 UTC on day D and 00:00:01 UTC on day D+1 land on their own
        days. Planted defect: bucket by the next day's date."""
        d1, d2 = date(2026, 3, 1), date(2026, 3, 2)
        plays = [_play(_at(d1, 23, 59, 59)), _play(_at(d2, 0, 0, 1))]
        result = aggregate_daily_counts(plays, d1, d2)
        assert result["2026-03-01"] == 1
        assert result["2026-03-02"] == 1

    def test_a_play_with_no_names_still_counts(self):
        """The heatmap needs the date only (an album needs all three names).
        Planted defect: skip a play with an empty album, as the album
        calculation does."""
        play = _play(_noon(date(2026, 4, 1)), artist="", album="", track="")
        result = aggregate_daily_counts([play], date(2026, 4, 1), date(2026, 4, 1))
        assert result["2026-04-01"] == 1


class TestZeroFill:
    def test_it_keeps_counts_and_fills_the_gaps(self):
        """Every date in the range is present, counted or zero, both ends
        included. Planted defect: stop the range one day short."""
        result = zero_fill_daily_counts(
            {"2026-01-02": 5}, date(2026, 1, 1), date(2026, 1, 3)
        )
        assert result == {"2026-01-01": 0, "2026-01-02": 5, "2026-01-03": 0}
