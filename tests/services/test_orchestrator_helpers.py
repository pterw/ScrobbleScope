import logging
from unittest.mock import AsyncMock, patch

import pytest

from scrobblescope.domain import release_window
from scrobblescope.orchestrator import (
    _MAX_ALBUM_CAP,
    _PLAYTIME_ALBUM_CAP,
    _apply_post_slice,
    _apply_pre_slice,
    _build_results,
    _classify_exception_to_error_code,
    _detect_enrichment_total_failure,
    _get_user_friendly_reason,
    _lookup_cached_original_release,
    _matches_release_criteria,
)
from scrobblescope.repositories import create_job, get_job_unmatched
from tests.helpers import TEST_JOB_PARAMS

# =====================================================================
# Adversarial tests for extracted helpers (Batch 11 WP-2)
# =====================================================================


@pytest.mark.parametrize(
    "release_date, expected",
    [
        ("XXXX-01-01", False),  # unparseable year -> ValueError fallback
        ("not-a-date", False),  # fully non-numeric prefix
        ("", False),  # empty string -> guard returns False
        (None, False),  # None -> guard returns False
        ("2025", True),  # year-only string, no dash, matches year=2025
    ],
)
def test_matches_release_criteria_adversarial(release_date, expected):
    """Edge-case inputs must not crash -- they must return False gracefully
    via the ValueError fallback or the empty-string guard.

    The parametrized cases cover:
    - Unparseable year prefix ("XXXX") -> ValueError -> returns False
    - Non-numeric prefix ("not") -> ValueError -> returns False
    - Empty string -> `if not release_date` guard -> returns False
    - None -> same guard -> returns False
    - Year-only string without dash -> succeeds (no split needed)
    """
    result = _matches_release_criteria(release_date, release_scope="same", year=2025)
    assert result is expected


# =====================================================================
# F-B23-5: one release-window rule, in domain.py
# =====================================================================


# The rule two consumers now derive from: the release-window scope table used
# to be restated in both `_matches_release_criteria` (here) and
# `release_checks._window_end`. Task 12 moves it to `domain.release_window`,
# and this parity test pins `_matches_release_criteria`'s current outputs
# first, so the refactor has a net -- it must keep passing, unchanged.
@pytest.mark.parametrize(
    "release_date, release_scope, year, decade, release_year, expected",
    [
        # The four bounded scopes: one match, one miss each.
        ("2025-06-01", "same", 2025, None, None, True),
        ("2024-06-01", "same", 2025, None, None, False),
        ("2024-06-01", "previous", 2025, None, None, True),
        ("2025-06-01", "previous", 2025, None, None, False),
        ("1994-06-01", "decade", 2025, "1990s", None, True),
        ("2001-06-01", "decade", 2025, "1990s", None, False),
        ("1991-06-01", "custom", 2025, None, 1991, True),
        ("1990-06-01", "custom", 2025, None, 1991, False),
        # (a) "custom" with no release_year: unbounded, matches every album.
        ("1800-06-01", "custom", 2025, None, None, True),
        # (b) "decade" with an unparseable value: excludes every album.
        # (The warning it logs changes to name the decade; not asserted here.)
        ("2025-06-01", "decade", 2025, "nope", None, False),
        # (d) an unknown scope: unbounded, matches every album.
        ("2025-06-01", "unknown-scope", 2025, None, None, True),
        # (e) "decade"/"custom" with a falsy companion: unbounded.
        ("2025-06-01", "decade", 2025, None, None, True),
        ("2025-06-01", "decade", 2025, "", None, True),
        ("2025-06-01", "decade", 2025, 0, None, True),
        ("2025-06-01", "custom", 2025, None, None, True),
        ("2025-06-01", "custom", 2025, None, "", True),
        ("2025-06-01", "custom", 2025, None, 0, True),
        # (f) a bounded scope with no release date -> False; "all" -> True.
        (None, "same", 2025, None, None, False),
        (None, "all", 2025, None, None, True),
    ],
)
def test_matches_release_criteria_parity_before_release_window(
    release_date, release_scope, year, decade, release_year, expected
):
    """
    GIVEN every divergence F-B23-5 names plus the four bounded scopes
    WHEN `_matches_release_criteria` is called before it derives from
        `domain.release_window`
    THEN it returns today's output -- the net Task 12's refactor must not
        tear, since every case here keeps passing afterward unchanged.
    """
    result = _matches_release_criteria(
        release_date, release_scope, year, decade, release_year
    )
    assert result is expected


@pytest.mark.parametrize(
    "release_scope, year, decade, release_year, expected",
    [
        ("same", 2025, None, None, (2025, 2025)),
        ("previous", 2025, None, None, (2024, 2024)),
        ("decade", 2025, "1990s", None, (1990, 1999)),
        ("custom", 2025, None, 1991, (1991, 1991)),
    ],
)
def test_release_window_per_scope(release_scope, year, decade, release_year, expected):
    """
    GIVEN each of the four bounded release scopes
    WHEN release_window computes the inclusive year range it accepts
    THEN it returns that scope's own (first, last) bound.
    """
    assert release_window(release_scope, year, decade, release_year) == expected


@pytest.mark.parametrize(
    "release_scope, year, decade, release_year",
    [
        ("all", 2025, None, None),
        ("some-unknown-scope", 2025, None, None),
        ("decade", 2025, None, None),
        ("decade", 2025, "", None),
        ("decade", 2025, 0, None),
        ("custom", 2025, None, None),
        ("custom", 2025, None, ""),
        ("custom", 2025, None, 0),
    ],
)
def test_release_window_unbounded_returns_none(
    release_scope, year, decade, release_year
):
    """
    GIVEN a scope that accepts every year -- "all", an unrecognized scope, or
        "decade"/"custom" with a falsy companion
    WHEN release_window computes the window
    THEN it returns None rather than a range, since there is nothing to
        bound it with.
    """
    assert release_window(release_scope, year, decade, release_year) is None


def test_release_window_unparseable_decade_raises():
    """
    GIVEN a "decade" scope whose companion parameter cannot be parsed as a
        year (the route does not validate `decade`, so a crafted request can
        reach this)
    WHEN release_window computes the window
    THEN it raises ValueError rather than guessing -- the caller decides how
        to log the bad input and what to return.
    """
    with pytest.raises(ValueError):
        release_window("decade", 2025, decade="nope")


def test_get_user_friendly_reason_adversarial():
    """When release_scope='decade' but decade=None, the function must not
    raise a TypeError on `decade[:3]`.  It should fall through to the
    generic mismatch message instead.

    Also verifies the ValueError branch for unparseable dates.
    """
    # decade=None: the `if release_scope == "decade" and decade:` guard
    # is False, so it falls through to the generic message.
    reason = _get_user_friendly_reason(
        "2020-01-01", release_scope="decade", year=2025, decade=None
    )
    assert "does not match filter" in reason
    assert "2020" in reason

    # Unparseable date -> ValueError branch
    reason_bad = _get_user_friendly_reason("XXXX", release_scope="same", year=2025)
    assert reason_bad == "Unknown release year: XXXX"


def test_build_results_zero_playtime_no_division_error():
    """When all albums have zero play_time_seconds and sort_mode='playtime',
    the `or 1` guard in proportion calculation must prevent ZeroDivisionError.

    Also verifies that missing track_durations (None) defaults to an empty
    dict, producing play_time_seconds=0 rather than a TypeError.
    """
    job_id = create_job(TEST_JOB_PARAMS)
    cache_hits = {
        ("artist", "album"): {
            "cached": {
                "spotify_id": "sp1",
                "release_date": "2025-01-01",
                "album_image_url": "https://img.example.com/a.jpg",
                "track_durations": None,  # missing durations
            },
            "original": {
                "play_count": 20,
                "track_counts": {"song a": 5, "song b": 3},
                "original_artist": "Artist",
                "original_album": "Album",
            },
        }
    }

    results = _build_results(
        cache_hits, job_id, year=2025, sort_mode="playtime", release_scope="same"
    )

    assert len(results) == 1
    assert results[0]["play_time_seconds"] == 0
    assert results[0]["play_time"] == "0 secs"
    assert results[0]["play_time_mobile"] == "0s"
    # proportion_of_max uses `or 1` guard: 0 / 1 * 100 = 0.0
    assert results[0]["proportion_of_max"] == 0.0
    assert results[0]["proportion_of_total"] == 0.0


def _corrected_cache_hits(provider_release_date):
    """One album whose provider date is *provider_release_date*, ready for an
    ``original_release_hits`` lookup keyed the same way ``_build_results``
    keys ``cache_hits``: ``(artist_norm, album_norm)``.
    """
    return {
        ("artist", "album"): {
            "cached": {
                "spotify_id": "sp1",
                "release_date": provider_release_date,
                "album_image_url": "https://img.example.com/a.jpg",
                "track_durations": {},
            },
            "original": {
                "play_count": 20,
                "track_counts": {"song a": 5},
                "original_artist": "Artist",
                "original_album": "Album",
            },
        }
    }


@pytest.mark.asyncio
async def test_lookup_cached_original_release_without_connection_skips_query():
    """No DB connection means no correction lookup and an empty result."""
    album_keys = [("artist", "album")]

    with patch(
        "scrobblescope.orchestrator._batch_lookup_original_release",
        new_callable=AsyncMock,
    ) as mock_lookup:
        result = await _lookup_cached_original_release(None, album_keys)

    assert result == {}
    mock_lookup.assert_not_awaited()


@pytest.mark.asyncio
async def test_lookup_cached_original_release_failure_is_non_fatal(caplog):
    """A correction-cache failure is logged and cannot block album results."""
    mock_conn = AsyncMock()
    album_keys = [("artist", "album")]

    with (
        caplog.at_level(logging.WARNING),
        patch(
            "scrobblescope.orchestrator._batch_lookup_original_release",
            new_callable=AsyncMock,
            side_effect=RuntimeError("database unavailable"),
        ),
    ):
        result = await _lookup_cached_original_release(mock_conn, album_keys)

    assert result == {}
    assert "Original-release cache lookup failed (non-fatal): database unavailable" in (
        caplog.text
    )


def test_build_results_cached_original_release_excludes_album_outside_filter():
    """A cached MusicBrainz correction, not the provider's reissue date,
    drives the release filter. Task 8, Batch 22 WP-3: 1977 original vs a
    2011 provider date, filtered by year=2011, must exclude the album and
    explain the exclusion in terms of the original year, not the provider's.
    """
    job_id = create_job(TEST_JOB_PARAMS)
    cache_hits = _corrected_cache_hits("2011-11-11")
    original_release_hits = {
        ("artist", "album"): {
            "mb_release_group": "mbid-1",
            "original_release": "1977-02-04",
        }
    }

    results = _build_results(
        cache_hits,
        job_id,
        year=2011,
        sort_mode="playcount",
        release_scope="same",
        original_release_hits=original_release_hits,
    )

    assert results == []
    unmatched = get_job_unmatched(job_id)
    entry = unmatched["artist|album"]
    assert entry["reason"] == "First released in 1977, not 2011"
    assert entry["reason_code"] == "release_scope"
    assert entry["provider_release_date"] == "2011-11-11"


def test_build_results_cached_original_release_includes_album_matching_filter():
    """The same correction, filtered by the original year (1977), keeps the
    album in the results and displays the corrected date -- the provider's
    own reissue date survives separately as ``provider_release_date``.
    """
    job_id = create_job(TEST_JOB_PARAMS)
    cache_hits = _corrected_cache_hits("2011-11-11")
    original_release_hits = {
        ("artist", "album"): {
            "mb_release_group": "mbid-1",
            "original_release": "1977-02-04",
        }
    }

    results = _build_results(
        cache_hits,
        job_id,
        year=1977,
        sort_mode="playcount",
        release_scope="same",
        original_release_hits=original_release_hits,
    )

    assert len(results) == 1
    assert results[0]["release_date"] == "1977-02-04"
    assert results[0]["provider_release_date"] == "2011-11-11"


def test_build_results_no_cached_original_release_behaves_as_before():
    """With no correction cached at all (omitted kwarg) or a 'checked,
    nothing found' row (both fields null), the provider's own release_date
    drives filtering and display exactly as it did before Task 8, and no
    ``provider_release_date`` key is added to the result.
    """
    job_id = create_job(TEST_JOB_PARAMS)

    # Case A: original_release_hits not passed at all.
    results_a = _build_results(
        _corrected_cache_hits("2011-11-11"),
        job_id,
        year=2011,
        sort_mode="playcount",
        release_scope="same",
    )
    assert len(results_a) == 1
    assert results_a[0]["release_date"] == "2011-11-11"
    assert "provider_release_date" not in results_a[0]

    # Case B: a real "checked, nothing found" cache row (both fields null).
    job_id_b = create_job(TEST_JOB_PARAMS)
    results_b = _build_results(
        _corrected_cache_hits("2011-11-11"),
        job_id_b,
        year=2011,
        sort_mode="playcount",
        release_scope="same",
        original_release_hits={
            ("artist", "album"): {"mb_release_group": None, "original_release": None}
        },
    )
    assert len(results_b) == 1
    assert results_b[0]["release_date"] == "2011-11-11"
    assert "provider_release_date" not in results_b[0]


def test_get_user_friendly_reason_corrected_wording_covers_every_scope():
    """``corrected=True`` swaps every scope's wording to name the original
    release year ("First released...") instead of implying the app misread
    the provider's own date ("Released..."). Adversarial per AGENTS.md Test
    Quality Rules: covers same/previous/decade/custom, not just the one
    scope the plan's own example uses.
    """
    assert (
        _get_user_friendly_reason(
            "1977-02-04", release_scope="same", year=2011, corrected=True
        )
        == "First released in 1977, not 2011"
    )
    assert (
        _get_user_friendly_reason(
            "1977-02-04", release_scope="previous", year=2012, corrected=True
        )
        == "First released in 1977, not 2011"
    )
    assert (
        _get_user_friendly_reason(
            "1977-02-04",
            release_scope="decade",
            year=2011,
            decade="1970s",
            corrected=True,
        )
        == "First released in 1977, outside of 1970-1979"
    )
    assert (
        _get_user_friendly_reason(
            "1977-02-04",
            release_scope="custom",
            year=2011,
            release_year=2011,
            corrected=True,
        )
        == "First released in 1977, not 2011"
    )


def test_build_results_records_reason_code():
    """Albums excluded by release criteria must record reason_code='release_scope'."""
    from scrobblescope.repositories import get_job_unmatched

    job_id = create_job(TEST_JOB_PARAMS)
    cache_hits = {
        ("artist", "album"): {
            "cached": {
                "spotify_id": "sp1",
                "release_date": "2018-01-01",
                "album_image_url": "https://img.example.com/a.jpg",
                "track_durations": {},
            },
            "original": {
                "play_count": 20,
                "track_counts": {"song a": 5},
                "original_artist": "Artist",
                "original_album": "Album",
            },
        }
    }

    results = _build_results(
        cache_hits, job_id, year=2024, sort_mode="playcount", release_scope="same"
    )

    assert len(results) == 0
    unmatched = get_job_unmatched(job_id)
    key = "artist|album"
    assert key in unmatched
    assert unmatched[key]["reason_code"] == "release_scope"
    assert unmatched[key]["album_image"] == "https://img.example.com/a.jpg"
    assert unmatched[key]["spotify_id"] == "sp1"
    assert unmatched[key]["play_count"] == 20


# ---------------------------------------------------------------------------
# WP-3 adversarial tests for extracted _fetch_and_process helpers
# ---------------------------------------------------------------------------


def test_apply_pre_slice_playcount_all_scope_slices():
    """5 albums, limit=2, sort_mode='playcount', release_scope='all' -> 2."""
    albums = {
        (f"a{i}", f"b{i}"): {"play_count": 10 - i, "track_counts": {}} for i in range(5)
    }
    result = _apply_pre_slice(albums, "playcount", "2", "all")
    assert len(result) == 2


def test_apply_pre_slice_playcount_scoped_release_no_slice():
    """Same setup but release_scope='same' -> all 5 returned."""
    albums = {
        (f"a{i}", f"b{i}"): {"play_count": 10 - i, "track_counts": {}} for i in range(5)
    }
    result = _apply_pre_slice(albums, "playcount", "2", "same")
    assert len(result) == 5


def test_apply_pre_slice_playtime_cap_fires():
    """501 albums, sort_mode='playtime' -> capped at _PLAYTIME_ALBUM_CAP."""
    albums = {
        (f"a{i}", f"b{i}"): {"play_count": 1000 - i, "track_counts": {}}
        for i in range(501)
    }
    result = _apply_pre_slice(albums, "playtime", "all", "all")
    assert len(result) == _PLAYTIME_ALBUM_CAP


def test_apply_pre_slice_playcount_cap_fires():
    """501 albums, sort_mode='playcount' -> capped at _MAX_ALBUM_CAP."""
    albums = {
        (f"a{i}", f"b{i}"): {"play_count": 1000 - i, "track_counts": {}}
        for i in range(501)
    }
    result = _apply_pre_slice(albums, "playcount", "all", "same")
    assert len(result) == _MAX_ALBUM_CAP


def test_apply_pre_slice_playtime_below_cap_unchanged():
    """5 albums, sort_mode='playtime' -> all 5 returned."""
    albums = {
        (f"a{i}", f"b{i}"): {"play_count": 10, "track_counts": {}} for i in range(5)
    }
    result = _apply_pre_slice(albums, "playtime", "all", "all")
    assert len(result) == 5


def test_apply_post_slice_limits_results():
    """10 results, limit_results='5' -> 5 returned."""
    results = [{"album": f"a{i}"} for i in range(10)]
    out = _apply_post_slice(results, "5")
    assert len(out) == 5


def test_apply_post_slice_malformed_limit_no_error(caplog):
    """limit_results='banana' -> all results returned, warning logged."""
    results = [{"album": f"a{i}"} for i in range(3)]
    with caplog.at_level(logging.WARNING):
        out = _apply_post_slice(results, "banana")
    assert len(out) == 3
    assert "Invalid limit_results value" in caplog.text


def test_classify_exception_to_error_code_spotify_rate_limited():
    """'Too Many Requests' + 'spotify' -> 'spotify_rate_limited'."""
    assert (
        _classify_exception_to_error_code("spotify Too Many Requests")
        == "spotify_rate_limited"
    )


def test_classify_exception_to_error_code_user_not_found():
    """'user not found' -> 'user_not_found'."""
    assert (
        _classify_exception_to_error_code("User not found on Last.fm")
        == "user_not_found"
    )


def test_classify_exception_to_error_code_unclassified_returns_none():
    """'connection timeout' -> None."""
    assert _classify_exception_to_error_code("connection timeout") is None


def test_detect_enrichment_total_failure_fires_when_all_unmatched():
    """All filtered_albums unmatched -> returns True, set_job_error called."""
    job_id = create_job(TEST_JOB_PARAMS)
    filtered = {("a", "b"): {}, ("c", "d"): {}}
    with (
        patch(
            "scrobblescope.orchestrator.get_job_context",
            return_value={
                "unmatched": {
                    "a|b": {"reason": "No Spotify match"},
                    "c|d": {"reason": "No Spotify match"},
                }
            },
        ),
        patch("scrobblescope.orchestrator.set_job_error") as mock_err,
    ):
        assert _detect_enrichment_total_failure(job_id, [], filtered) is True
        mock_err.assert_called_once_with(job_id, "spotify_unavailable")


def test_detect_enrichment_total_failure_does_not_fire_partial_match():
    """Only some albums unmatched -> returns False."""
    job_id = create_job(TEST_JOB_PARAMS)
    filtered = {("a", "b"): {}, ("c", "d"): {}}
    with patch(
        "scrobblescope.orchestrator.get_job_context",
        return_value={
            "unmatched": {
                "a|b": {"reason": "No Spotify match"},
            }
        },
    ):
        assert _detect_enrichment_total_failure(job_id, [], filtered) is False


def test_detect_enrichment_total_failure_bases_detection_on_reason_code():
    """Failure detection must check reason_code, not written prose."""
    from scrobblescope.unmatched import REASON_NO_SPOTIFY_MATCH

    job_id = create_job(TEST_JOB_PARAMS)
    filtered = {("a", "b"): {}, ("c", "d"): {}}
    with (
        patch(
            "scrobblescope.orchestrator.get_job_context",
            return_value={
                "unmatched": {
                    "a|b": {
                        "reason": "Different prose string",
                        "reason_code": REASON_NO_SPOTIFY_MATCH,
                    },
                    "c|d": {
                        "reason": "Another prose message",
                        "reason_code": REASON_NO_SPOTIFY_MATCH,
                    },
                }
            },
        ),
        patch("scrobblescope.orchestrator.set_job_error") as mock_err,
    ):
        assert _detect_enrichment_total_failure(job_id, [], filtered) is True
        mock_err.assert_called_once_with(job_id, "spotify_unavailable")


def test_detect_enrichment_total_failure_does_not_fire_for_other_reason_codes():
    """Items with non-matching reason_code do not trigger spotify_unavailable."""
    from scrobblescope.unmatched import REASON_RELEASE_SCOPE

    job_id = create_job(TEST_JOB_PARAMS)
    filtered = {("a", "b"): {}, ("c", "d"): {}}
    with patch(
        "scrobblescope.orchestrator.get_job_context",
        return_value={
            "unmatched": {
                "a|b": {
                    "reason": "Release scope reason",
                    "reason_code": REASON_RELEASE_SCOPE,
                },
                "c|d": {
                    "reason": "Release scope reason",
                    "reason_code": REASON_RELEASE_SCOPE,
                },
            }
        },
    ):
        assert _detect_enrichment_total_failure(job_id, [], filtered) is False


def _tied_albums(count):
    """Build *count* eligible albums sharing one play count, so every sort ties."""
    return {
        (f"a{i:03d}", f"b{i:03d}"): {"play_count": 1, "track_counts": {}}
        for i in range(count)
    }


def test_apply_pre_slice_pre_slice_is_independent_of_input_order():
    """The playcount pre-slice must not let insertion order choose the survivors.

    Mutation: restore `key=play_count, reverse=True` and this test fails. The sort
    is stable, so with every album tied it keeps whichever were inserted first,
    and the two inputs below then disagree.
    """
    albums = _tied_albums(300)

    forward = _apply_pre_slice(dict(albums), "playcount", "100", "all")
    backward = _apply_pre_slice(
        dict(reversed(list(albums.items()))), "playcount", "100", "all"
    )

    assert len(forward) == 100
    assert set(forward) == set(backward)


def test_apply_pre_slice_cap_is_independent_of_input_order():
    """The safety cap must not let insertion order choose the survivors.

    Mutation: restore `key=play_count, reverse=True` and this test fails for the
    same reason -- with more tied albums than the cap, the stable sort keeps the
    first-inserted ones.
    """
    albums = _tied_albums(_MAX_ALBUM_CAP + 100)

    forward = _apply_pre_slice(dict(albums), "playtime", "all", "all")
    backward = _apply_pre_slice(
        dict(reversed(list(albums.items()))), "playtime", "all", "all"
    )

    assert len(forward) == _MAX_ALBUM_CAP
    assert set(forward) == set(backward)
