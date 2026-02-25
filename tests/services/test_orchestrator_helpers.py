import logging
from unittest.mock import patch

import pytest

from scrobblescope.orchestrator import (
    _PLAYTIME_ALBUM_CAP,
    _apply_post_slice,
    _apply_pre_slice,
    _build_results,
    _classify_exception_to_error_code,
    _detect_spotify_total_failure,
    _get_user_friendly_reason,
    _matches_release_criteria,
)
from scrobblescope.repositories import create_job
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


def test_detect_spotify_total_failure_fires_when_all_unmatched():
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
        assert _detect_spotify_total_failure(job_id, [], filtered) is True
        mock_err.assert_called_once_with(job_id, "spotify_unavailable")


def test_detect_spotify_total_failure_does_not_fire_partial_match():
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
        assert _detect_spotify_total_failure(job_id, [], filtered) is False
