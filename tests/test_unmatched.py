"""Unit tests for unmatched album domain categorization and grouping."""

from scrobblescope.unmatched import (
    REASON_NO_SPOTIFY_MATCH,
    REASON_RELEASE_SCOPE,
    group_unmatched_albums,
)


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
    assert metadata[REASON_RELEASE_SCOPE]["title"] == "Outside Release Filter"
    assert metadata[REASON_NO_SPOTIFY_MATCH]["title"] == "No Spotify Match"
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
