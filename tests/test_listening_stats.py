"""Listening statistics: every figure, its rule and its stated population."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta, timezone

import pytest

from scrobblescope.listening_stats import (
    album_play_statistics,
    best_day,
    current_streak,
    daily_average,
    heatmap_statistics,
    utc_date,
)
from tests.helpers import kpi_window, load_kpi_cases

NEW_YORK = timezone(timedelta(hours=-5))
TOKYO = timezone(timedelta(hours=9))


def _window(first, days, plays=None):
    """A zero-filled window of *days* days from *first* with *plays* by ISO date."""
    counts = {(first + timedelta(days=n)).isoformat(): 0 for n in range(days)}
    counts.update(plays or {})
    return counts


class TestUtcDate:
    def test_a_late_evening_in_new_york_is_the_next_utc_day(self):
        moment = datetime(2026, 3, 1, 23, 30, tzinfo=NEW_YORK)
        assert utc_date(moment) == date(2026, 3, 2)

    def test_an_early_morning_in_tokyo_is_the_previous_utc_day(self):
        moment = datetime(2026, 3, 2, 6, 0, tzinfo=TOKYO)
        assert utc_date(moment) == date(2026, 3, 1)

    def test_the_date_is_read_in_utc_whatever_the_host_zone_is(self):
        """A host in UTC hides a conversion that uses the system zone, so fake one.

        The moment is 20:00 UTC on 1 March. A host east of UTC (Tokyo here)
        would call it 2 March; the answer must be 1 March on every host.
        Mutation: ``moment.astimezone()`` with no argument returns 2 March.
        """

        class _MomentOnATokyoHost(datetime):
            def astimezone(self, tz=None):
                return super().astimezone(TOKYO if tz is None else tz)

        moment = _MomentOnATokyoHost(2026, 3, 1, 20, 0, tzinfo=UTC)
        assert utc_date(moment) == date(2026, 3, 1)

    def test_a_naive_moment_is_refused(self):
        """A naive datetime has no zone to convert from, so any answer is a guess."""
        with pytest.raises(ValueError, match="timezone"):
            utc_date(datetime(2026, 3, 1, 23, 30))


class TestCurrentStreak:
    def test_utc_midnight_decides_which_day_a_play_belongs_to(self):
        """A play at 23:30 in New York on 1 March is 2 March in UTC, so 2 March
        has a play and the streak is 3. Read in local time the play lands on
        1 March, 2 March is quiet, and the streak is 2."""
        counts = _window(date(2026, 2, 25), 6)
        for moment in (
            datetime(2026, 2, 28, 12, 0, tzinfo=UTC),
            datetime(2026, 3, 1, 12, 0, tzinfo=UTC),
            datetime(2026, 3, 1, 23, 30, tzinfo=NEW_YORK),
        ):
            counts[utc_date(moment).isoformat()] += 1
        assert current_streak(counts, date(2026, 3, 2)) == 3

    def test_a_streak_may_end_yesterday(self):
        counts = _window(date(2026, 3, 1), 10, {"2026-03-08": 1, "2026-03-09": 2})
        assert current_streak(counts, date(2026, 3, 10)) == 2

    def test_two_quiet_days_end_the_streak(self):
        # Today 03-10 and 03-09 are quiet, so the streak is 0. The run on
        # 03-07/03-08 is two days old: a count that began at 03-08 would say 2.
        counts = _window(date(2026, 3, 1), 10, {"2026-03-07": 4, "2026-03-08": 2})
        assert current_streak(counts, date(2026, 3, 10)) == 0

    def test_a_single_day_streak(self):
        counts = _window(date(2026, 3, 1), 10, {"2026-03-10": 1})
        assert current_streak(counts, date(2026, 3, 10)) == 1

    def test_counting_stops_at_the_first_day_of_the_window(self):
        counts = {d: 1 for d in _window(date(2026, 3, 1), 10)}
        assert current_streak(counts, date(2026, 3, 10)) == 10

    def test_an_empty_window_has_no_streak(self):
        assert current_streak({}, date(2026, 3, 10)) == 0


class TestBestDay:
    def test_the_busiest_day_and_its_count(self):
        # Busiest is 03-06 (7 plays); the first day with a play is 03-04 (3) and
        # the last is 03-08 (2), so "first" and "last" both give another answer.
        counts = _window(
            date(2026, 3, 1),
            10,
            {"2026-03-04": 3, "2026-03-06": 7, "2026-03-08": 2},
        )
        assert best_day(counts) == (date(2026, 3, 6), 7)

    def test_a_tie_goes_to_the_earlier_day(self):
        counts = _window(date(2026, 3, 1), 10, {"2026-03-02": 4, "2026-03-09": 4})
        assert best_day(counts) == (date(2026, 3, 2), 4)

    def test_a_tie_goes_to_the_earlier_day_whatever_order_the_days_arrive_in(self):
        """The later day comes first in the mapping; only sorting finds the earlier one."""
        counts = {"2026-03-09": 4, "2026-03-02": 4, "2026-03-05": 1}
        assert best_day(counts) == (date(2026, 3, 2), 4)

    def test_a_window_with_no_plays_has_no_best_day(self):
        """Not 'the first day with 0 plays': nothing was played, so no day is best."""
        assert best_day(_window(date(2026, 3, 1), 10)) == (None, 0)

    def test_an_empty_mapping_has_no_best_day(self):
        assert best_day({}) == (None, 0)


class TestDailyAverage:
    def test_quiet_days_count_as_zero(self):
        counts = _window(date(2026, 3, 1), 10, {"2026-03-02": 30})
        assert daily_average(counts) == 3.0

    def test_the_average_is_not_rounded(self):
        counts = _window(date(2026, 3, 1), 3, {"2026-03-01": 1})
        assert daily_average(counts) == pytest.approx(1 / 3)

    def test_an_empty_window_averages_zero_not_an_error(self):
        assert daily_average({}) == 0.0


@pytest.mark.parametrize("case", load_kpi_cases(), ids=lambda c: c["name"])
def test_the_published_figures_are_the_ones_the_pinned_kpis_show(case):
    """Same table the browser harness checks, so the Python rules agree with
    what readers saw before the move.

    Mutation: anchor the streak on the window's first day, or break ties
    toward the later day, and the matching cases fail.
    """
    _, to_iso, counts = kpi_window(case)
    stats = heatmap_statistics(counts, date.fromisoformat(to_iso))
    expected = case["expected"]
    best = stats["best_day"]["value"]
    # A window with no plays publishes a null best-day date: it has no best
    # day, and the page shows no date for it (the case's empty best_label).
    best_label = ""
    if best["date"] is not None:
        best_date = date.fromisoformat(best["date"])
        best_label = f"{best_date:%b}".upper() + f" {best_date.day}"

    assert f"{stats['total_plays']['value']:,}" == expected["scrobbles"]
    assert f"{stats['daily_average']['value']:.1f}" == expected["daily_average"]
    assert str(best["count"]) == expected["best_count"]
    assert best_label == expected["best_label"]
    assert str(stats["current_streak"]["value"]) == expected["streak"]


class TestHeatmapStatistics:
    def test_every_figure_states_its_population(self):
        stats = heatmap_statistics(_window(date(2026, 3, 1), 10), date(2026, 3, 10))
        assert set(stats) == {
            "total_plays",
            "daily_average",
            "best_day",
            "current_streak",
        }
        assert {name: fact["population"] for name, fact in stats.items()} == {
            "total_plays": "all plays inside the window",
            "daily_average": (
                "all plays inside the window, over every UTC day of the window "
                "including the days with none"
            ),
            "best_day": (
                "the UTC day with the most plays inside the window; "
                "the earliest day wins a tie"
            ),
            "current_streak": (
                "consecutive UTC days with a play, ending on the window's last "
                "day or the day before it, counted back no further than the "
                "window's first day"
            ),
        }

    def test_a_window_with_no_plays_publishes_null_for_best_day(self):
        stats = heatmap_statistics(_window(date(2026, 3, 1), 10), date(2026, 3, 10))
        assert stats["best_day"]["value"] == {"date": None, "count": 0}
        assert stats["current_streak"]["value"] == 0


class TestAlbumPlayStatistics:
    ROWS = [
        {"play_count": 50},
        {"play_count": 45, "unmatched_reason": "no_spotify_match"},
        {"play_count": 40},
        {"play_count": 35, "unmatched_reason": "provider_unavailable"},
    ]

    def test_listed_counts_every_row_and_matched_leaves_out_unmatched(self):
        stats = album_play_statistics(self.ROWS)
        assert stats["plays_listed"]["value"] == 170
        assert stats["plays_matched"]["value"] == 90

    def test_without_unmatched_rows_the_two_figures_agree(self):
        stats = album_play_statistics([{"play_count": 50}, {"play_count": 40}])
        assert stats["plays_listed"]["value"] == stats["plays_matched"]["value"] == 90

    def test_no_rows_is_zero_not_an_error(self):
        stats = album_play_statistics([])
        assert stats["plays_listed"]["value"] == 0
        assert stats["plays_matched"]["value"] == 0

    def test_a_missing_or_null_play_count_is_zero(self):
        stats = album_play_statistics([{"play_count": None}, {}, {"play_count": 4}])
        assert stats["plays_listed"]["value"] == 4

    def test_each_figure_says_what_it_leaves_out(self):
        """Each sentence is pinned whole: a reworded or swapped one is a lie."""
        stats = album_play_statistics(self.ROWS)
        assert stats["plays_listed"]["population"] == (
            "plays of every album row the page lists, including albums "
            "listed through include-unmatched"
        )
        assert stats["plays_matched"]["population"] == (
            "plays of the album rows a provider matched; albums listed "
            "through include-unmatched (unmatched) are left out"
        )
