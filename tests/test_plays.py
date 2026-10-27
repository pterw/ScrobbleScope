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
    aggregate_weekly_artist_counts,
    select_albums,
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


class TestAggregateWeeklyArtistCounts:
    @pytest.mark.parametrize(
        "from_date, to_date, first_monday, columns",
        [
            (date(2026, 1, 7), date(2026, 1, 20), "2026-01-05", 3),  # Wed to Tue
            (date(2026, 1, 5), date(2026, 1, 11), "2026-01-05", 1),  # Mon to Sun
            (date(2026, 1, 11), date(2026, 1, 12), "2026-01-05", 2),  # Sun to Mon
            (date(2025, 3, 8), date(2026, 3, 7), "2025-03-03", 53),  # a year, Sat
        ],
    )
    def test_columns_follow_the_monday_grid(
        self, from_date, to_date, first_monday, columns
    ):
        """Column 0 starts on the Monday on or before ``from_date`` and the
        count matches the heatmap's ``numCols``. A play the Monday before the
        window is ignored; one on ``from_date`` is in column 0. Planted defect:
        step 7 days from ``from_date``."""
        days = (to_date - from_date).days + 1
        plays = [_play(_noon(from_date), "A"), _play(_noon(to_date), "A")]
        plays.append(_play(_noon(from_date - timedelta(days=1)), "A"))
        result = aggregate_weekly_artist_counts(plays, from_date, to_date)
        assert result["weeks"][0] == first_monday
        assert len(result["weeks"]) == columns
        assert columns == (from_date.weekday() + days - 1) // 7 + 1
        counts = result["artists"][0]["counts"]
        assert counts[0] >= 1 and counts[-1] >= 1
        assert sum(counts) == 2

    def test_artists_group_by_key_and_rank_by_total(self):
        """Spellings that normalise alike are one layer named by the first
        spelling seen; layers run by total descending, a tie by key. Planted
        defect: key on the raw artist string, or break ties by arrival."""
        day = date(2026, 1, 5)
        plays = [
            _play(_noon(day), "Zed"),
            _play(_noon(day), "Beta"),
            _play(_noon(day), "Radiohead"),
            _play(_noon(day), "radiohead!"),
            _play(_noon(day), "RADIOHEAD"),
        ]
        result = aggregate_weekly_artist_counts(plays, day, day)
        assert [a["name"] for a in result["artists"]] == ["Radiohead", "Beta", "Zed"]
        assert [a["counts"] for a in result["artists"]] == [[3], [1], [1]]

    @pytest.mark.parametrize("artist", ["", "!!!"])
    def test_artists_without_a_key_land_in_other(self, artist):
        """An empty or punctuation-only artist is counted in ``other``, never
        as a layer. Planted defect: drop such plays or layer them."""
        day = date(2026, 1, 5)
        result = aggregate_weekly_artist_counts([_play(_noon(day), artist)], day, day)
        assert result["artists"] == []
        assert result["other"] == [1]

    def test_artists_beyond_top_n_fold_into_other_and_stray_plays_are_ignored(self):
        """With ``top_n=2`` the third artist joins ``other``; plays outside the
        range count nowhere. Planted defect: drop the overflow artists."""
        day = date(2026, 1, 5)
        plays = [_play(_noon(day), name) for name in "AAABBC"]
        plays.append(_play(_noon(day + timedelta(days=9)), "A"))
        result = aggregate_weekly_artist_counts(plays, day, day, top_n=2)
        assert [a["name"] for a in result["artists"]] == ["A", "B"]
        assert result["other"] == [1]

    def test_each_week_adds_up_to_the_daily_counts(self):
        """Per week, artists plus ``other`` equal the daily counts of that
        column's days inside the window. Planted defect: any play lost or
        counted twice."""
        from_date, to_date = date(2026, 1, 7), date(2026, 2, 3)
        names = ["A", "B", "C", "D", "", "!!!", "a"]
        plays = [
            _play(_noon(from_date + timedelta(days=i % 30)), names[i % len(names)])
            for i in range(90)
        ]
        result = aggregate_weekly_artist_counts(plays, from_date, to_date, top_n=2)
        daily = aggregate_daily_counts(plays, from_date, to_date)
        week0 = from_date - timedelta(days=from_date.weekday())
        expected = [0] * len(result["weeks"])
        for iso, count in daily.items():
            expected[(date.fromisoformat(iso) - week0).days // 7] += count
        got = [
            sum(a["counts"][t] for a in result["artists"]) + result["other"][t]
            for t in range(len(expected))
        ]
        assert got == expected
        assert result["other"] != [0] * len(expected)


class TestZeroFill:
    def test_it_keeps_counts_and_fills_the_gaps(self):
        """Every date in the range is present, counted or zero, both ends
        included. Planted defect: stop the range one day short."""
        result = zero_fill_daily_counts(
            {"2026-01-02": 5}, date(2026, 1, 1), date(2026, 1, 3)
        )
        assert result == {"2026-01-01": 0, "2026-01-02": 5, "2026-01-03": 0}


# ---------------------------------------------------------------------------
# select_albums and AlbumSelection
# ---------------------------------------------------------------------------


def _aggregate(albums, plays_seen=0):
    """An AlbumAggregate holding ``albums`` given as {(artist, album): (plays, tracks)}."""
    built = {}
    for (artist, album), (plays, tracks) in albums.items():
        built[normalize_name(artist, album)] = {
            "play_count": plays,
            "track_counts": {f"t{n}": 1 for n in range(tracks)},
            "original_artist": artist,
            "original_album": album,
        }
    return AlbumAggregate(albums=built, plays_seen=plays_seen)


class TestSelectAlbums:
    def test_it_splits_by_both_minimums_and_counts_each_side(self):
        """Planted defect: make a minimum exclusive."""
        aggregate = _aggregate(
            {
                ("A", "Passes"): (10, 3),
                ("B", "Few Plays"): (9, 3),
                ("C", "Few Tracks"): (12, 2),
            },
            plays_seen=31,
        )

        selection = select_albums(aggregate, 10, 3, exclusion_cap=500)

        assert set(selection.eligible) == {normalize_name("A", "Passes")}
        assert set(selection.exclusions) == {
            normalize_name("B", "Few Plays"),
            normalize_name("C", "Few Tracks"),
        }
        assert selection.total_below_threshold == 2
        assert selection.unique_albums == 3
        assert selection.plays_seen == 31

    def test_stats_are_the_four_numbers_a_job_records(self):
        """Planted defect: report the capped exclusion count as the total."""
        albums = {(f"Artist{n:04d}", f"Album{n:04d}"): (1, 1) for n in range(600)}
        albums[("Big", "Hit")] = (50, 5)
        selection = select_albums(_aggregate(albums, 650), 10, 3, exclusion_cap=500)

        assert selection.stats() == {
            "total_scrobbles": 650,
            "unique_albums": 601,
            "albums_passing_filter": 1,
            "albums_below_threshold": 600,
        }
        assert len(selection.exclusions) == 500

    def test_the_cap_keeps_the_most_played_exclusions(self):
        """Planted defect: keep the first 500 inserted instead of the top 500."""
        albums = {(f"Low{n:03d}", f"Low{n:03d}"): (1, 1) for n in range(500)}
        albums.update({(f"High{n}", f"High{n}"): (9, 1) for n in range(5)})

        selection = select_albums(_aggregate(albums), 10, 3, exclusion_cap=500)

        assert {a["artist"] for a in selection.exclusions.values()} >= {
            f"High{n}" for n in range(5)
        }

    def test_the_cap_does_not_depend_on_input_order(self):
        """Every album ties on one play, so only the key can break the tie.
        Planted defect: sort by play count alone (a stable sort then keeps
        whichever tied albums were inserted first)."""
        albums = {(f"Artist{n:04d}", f"Album{n:04d}"): (1, 1) for n in range(600)}
        forward = select_albums(_aggregate(albums), 10, 3, exclusion_cap=500)
        backward = select_albums(
            _aggregate(dict(reversed(list(albums.items())))), 10, 3, exclusion_cap=500
        )

        assert len(forward.exclusions) == 500
        assert set(forward.exclusions) == set(backward.exclusions)
