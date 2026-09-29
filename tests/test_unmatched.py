"""Unit tests for unmatched album domain categorization and grouping."""

import pytest

from scrobblescope.unmatched import (
    REASON_BELOW_THRESHOLD,
    REASON_NO_SPOTIFY_MATCH,
    REASON_RELEASE_SCOPE,
    describe_shortfall,
    group_unmatched_albums,
    partition_albums_by_threshold,
)


def test_partition_albums_by_threshold_keeps_each_exclusion_once():
    """An album below both minimums is retained once with both failures."""
    albums = {
        ("artist", "both low"): {
            "original_artist": "Artist",
            "original_album": "Both Low",
            "play_count": 7,
            "track_counts": {"one": 4, "two": 3},
        },
        ("artist", "eligible"): {
            "original_artist": "Artist",
            "original_album": "Eligible",
            "play_count": 10,
            "track_counts": {"one": 4, "two": 3, "three": 3},
        },
    }

    eligible, excluded = partition_albums_by_threshold(albums, 10, 3)

    assert list(eligible) == [("artist", "eligible")]
    assert list(excluded) == [("artist", "both low")]
    item = excluded[("artist", "both low")]
    assert item["reason_code"] == REASON_BELOW_THRESHOLD
    assert item["failed_thresholds"] == ["plays", "tracks"]
    assert item["play_count"] == 7
    assert item["track_count"] == 2
    assert item["min_plays"] == 10
    assert item["min_tracks"] == 3


def test_partition_albums_by_threshold_stores_the_shortfall_beside_the_reason():
    """The report row prints the shortfall; the full sentence stays as `reason`."""
    albums = {
        ("artist", "both low"): {
            "original_artist": "Artist",
            "original_album": "Both Low",
            "play_count": 7,
            "track_counts": {"one": 4, "two": 3},
        },
    }

    _, excluded = partition_albums_by_threshold(albums, 10, 3)

    item = excluded[("artist", "both low")]
    assert item["shortfall"] == "3 plays and 1 track short"
    assert item["reason"] == (
        "Played 7 times across 2 unique tracks; minimum is 10 plays and 3 unique tracks"
    )


@pytest.mark.parametrize(
    ("counts", "expected"),
    [
        pytest.param((9, 3, 10, 3), "1 play short", id="one-play-short"),
        pytest.param((7, 5, 10, 3), "3 plays short", id="plays-short-plural"),
        pytest.param((12, 2, 10, 3), "1 track short", id="one-track-short"),
        pytest.param((12, 1, 10, 3), "2 tracks short", id="tracks-short-plural"),
        pytest.param((9, 2, 10, 3), "1 play and 1 track short", id="both-singular"),
        pytest.param((7, 1, 10, 3), "3 plays and 2 tracks short", id="both-plural"),
        pytest.param((0, 0, 2, 1), "2 plays and 1 track short", id="zero-counts"),
        pytest.param((10, 3, 10, 3), "", id="exactly-at-both-minimums"),
        pytest.param((40, 9, 10, 3), "", id="above-both-minimums"),
    ],
)
def test_describe_shortfall_names_only_the_measures_that_fell_short(counts, expected):
    """Each unit is singular at a gap of one; an album that met both is ''."""
    assert describe_shortfall(*counts) == expected


def test_group_unmatched_albums_groups_by_reason_code():
    """Albums with different release years must group under the single release_scope code."""
    data = {
        "art1|alb1": {
            "artist": "Artist 1",
            "album": "Album 1",
            "reason": "Released in 2018 (filter requires 2024)",
            "reason_code": REASON_RELEASE_SCOPE,
        },
        "art2|alb2": {
            "artist": "Artist 2",
            "album": "Album 2",
            "reason": "Released in 2019 (filter requires 2024)",
            "reason_code": REASON_RELEASE_SCOPE,
        },
        "art3|alb3": {
            "artist": "Artist 3",
            "album": "Album 3",
            "reason": "No Spotify match",
            "reason_code": REASON_NO_SPOTIFY_MATCH,
        },
    }

    groups, counts, metadata = group_unmatched_albums(data)

    assert len(groups) == 2
    assert counts[REASON_RELEASE_SCOPE] == 2
    assert counts[REASON_NO_SPOTIFY_MATCH] == 1
    assert len(groups[REASON_RELEASE_SCOPE]) == 2
    assert len(groups[REASON_NO_SPOTIFY_MATCH]) == 1
    # Sentence case, and the control is named as the search form labels it.
    assert metadata[REASON_RELEASE_SCOPE]["title"] == "Outside release filter"
    assert metadata[REASON_RELEASE_SCOPE]["description"] == (
        "Albums released outside your release filter."
    )
    assert metadata[REASON_NO_SPOTIFY_MATCH]["title"] == "No match found"
    # Row detail preserved
    assert (
        groups[REASON_RELEASE_SCOPE][0]["reason"]
        == "Released in 2018 (filter requires 2024)"
    )


def test_group_unmatched_albums_handles_legacy_missing_reason_code():
    """Legacy jobs with missing reason_code must fall back gracefully to prose reason."""
    data = {
        "art1|alb1": {
            "artist": "Artist 1",
            "album": "Album 1",
            "reason": "Custom unclassified reason",
        }
    }

    groups, counts, metadata = group_unmatched_albums(data)

    assert "Custom unclassified reason" in groups
    assert counts["Custom unclassified reason"] == 1
    assert (
        metadata["Custom unclassified reason"]["title"] == "Custom unclassified reason"
    )


def test_group_unmatched_albums_ranks_top_offenders_deterministically():
    """Visible rows rank by plays, with stable identity ties and missing counts last."""
    data = {
        "low": {
            "artist": "Artist Low",
            "album": "Low Plays",
            "play_count": 3,
            "reason_code": REASON_RELEASE_SCOPE,
        },
        "tie-z": {
            "artist": "Artist Z",
            "album": "High Plays Z",
            "play_count": 20,
            "reason_code": REASON_RELEASE_SCOPE,
        },
        "missing": {
            "artist": "Artist Unknown",
            "album": "Unknown Plays",
            "play_count": None,
            "reason_code": REASON_RELEASE_SCOPE,
        },
        "tie-a": {
            "artist": "Artist A",
            "album": "High Plays A",
            "play_count": 20,
            "reason_code": REASON_RELEASE_SCOPE,
        },
    }

    groups, _, _ = group_unmatched_albums(data)

    assert [item["album"] for item in groups[REASON_RELEASE_SCOPE]] == [
        "High Plays A",
        "High Plays Z",
        "Low Plays",
        "Unknown Plays",
    ]
