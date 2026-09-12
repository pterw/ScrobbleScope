"""Domain logic, category definitions, and grouping for unmatched albums.

Separates unmatched aggregation and presentation metadata from Flask routes
and async background workers.
"""

from __future__ import annotations

from typing import Any

#: Stable reason codes stored on unmatched items.
REASON_BELOW_THRESHOLD = "below_threshold"
REASON_RELEASE_SCOPE = "release_scope"
REASON_NO_SPOTIFY_MATCH = "no_spotify_match"

#: Human copy, badges, and fix hints associated with each reason code.
CATEGORY_METADATA = {
    REASON_BELOW_THRESHOLD: {
        "title": "Below your thresholds",
        "description": "Albums that did not meet one or both listening minimums.",
        "badge": "Threshold",
        "fix_hint": "Lower either minimum on a new search to include these albums.",
    },
    REASON_RELEASE_SCOPE: {
        "title": "Outside Release Filter",
        "description": "Albums released outside your selected release-date scope.",
        "badge": "Release date",
        "fix_hint": 'Choose "All years (no filter)" on a new search to include these releases.',
    },
    REASON_NO_SPOTIFY_MATCH: {
        "title": "No Spotify Match",
        "description": "Albums found in your Last.fm history that could not be matched on Spotify.",
        "badge": "Not on Spotify",
        "fix_hint": "Check album title formatting or artist naming on Last.fm.",
    },
}


def partition_albums_by_threshold(
    albums: dict[tuple[str, str], dict[str, Any]],
    min_plays: int,
    min_tracks: int,
) -> tuple[
    dict[tuple[str, str], dict[str, Any]],
    dict[tuple[str, str], dict[str, Any]],
]:
    """Split aggregated albums into eligible and threshold-excluded mappings.

    Each excluded album appears once even when it fails both configured
    minimums. The exclusion payload keeps only the facts needed by the job
    repository and report; eligible values retain their original aggregation
    data for Spotify enrichment.

    Args:
        albums: Aggregated albums keyed by normalized artist and album names.
        min_plays: Inclusive minimum Last.fm play count.
        min_tracks: Inclusive minimum normalized unique-track count.

    Returns:
        A pair of ``(eligible, excluded)`` mappings using the input keys.
    """
    eligible: dict[tuple[str, str], dict[str, Any]] = {}
    excluded: dict[tuple[str, str], dict[str, Any]] = {}

    for key, album in albums.items():
        play_count = int(album.get("play_count", 0))
        track_count = len(album.get("track_counts", {}))
        failed_thresholds = []
        if play_count < min_plays:
            failed_thresholds.append("plays")
        if track_count < min_tracks:
            failed_thresholds.append("tracks")

        if not failed_thresholds:
            eligible[key] = album
            continue

        excluded[key] = {
            "artist": album.get("original_artist", key[0]),
            "album": album.get("original_album", key[1]),
            "play_count": play_count,
            "track_count": track_count,
            "failed_thresholds": failed_thresholds,
            "min_plays": min_plays,
            "min_tracks": min_tracks,
            "reason_code": REASON_BELOW_THRESHOLD,
            "reason": (
                f"Played {play_count} times across {track_count} unique tracks; "
                f"minimum is {min_plays} plays and {min_tracks} unique tracks"
            ),
        }

    return eligible, excluded


def group_unmatched_albums(
    unmatched_data: dict[str, dict[str, Any]],
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, int], dict[str, dict[str, str]]]:
    """Group unmatched album items by their stable ``reason_code``.

    If an item lacks ``reason_code`` (legacy jobs), it falls back to the
    per-album ``reason`` string so historical data remains viewable.

    Returns:
        tuple of ``(groups, counts, metadata)`` where:
        - ``groups`` maps each group key to its list of album items.
        - ``counts`` maps each group key to the count of items in that group.
        - ``metadata`` maps each group key to a dict with ``title``,
          ``description``, ``badge``, and ``fix_hint``.
    """
    groups: dict[str, list[dict[str, Any]]] = {}
    metadata: dict[str, dict[str, str]] = {}

    for item in unmatched_data.values():
        code = item.get("reason_code")
        if code and code in CATEGORY_METADATA:
            group_key = code
            meta = CATEGORY_METADATA[code]
        else:
            prose = item.get("reason", "Unknown reason")
            group_key = prose
            meta = {
                "title": prose,
                "description": "Excluded from results based on search criteria.",
                "badge": "Excluded",
                "fix_hint": "Excluded from results based on criteria.",
            }

        groups.setdefault(group_key, []).append(item)
        if group_key not in metadata:
            metadata[group_key] = meta

    def _album_sort_key(item: dict[str, Any]) -> tuple[float, str, str]:
        """Rank known play counts first, then stabilize ties by identity."""
        play_count = item.get("play_count")
        numeric_count = (
            float(play_count) if isinstance(play_count, (int, float)) else -1
        )
        return (
            -numeric_count,
            str(item.get("artist", "")).casefold(),
            str(item.get("album", "")).casefold(),
        )

    for albums in groups.values():
        albums.sort(key=_album_sort_key)

    # Deterministic sort: canonical codes first, then alphabetical
    def _sort_key(k: str) -> tuple[int, str]:
        order = [
            REASON_BELOW_THRESHOLD,
            REASON_RELEASE_SCOPE,
            REASON_NO_SPOTIFY_MATCH,
        ]
        return (order.index(k) if k in order else 99, k)

    MAX_UNMATCHED_GROUP_CAP = 500
    sorted_groups = {
        k: groups[k][:MAX_UNMATCHED_GROUP_CAP]
        for k in sorted(groups.keys(), key=_sort_key)
    }
    counts = {k: len(v) for k, v in sorted_groups.items()}

    return sorted_groups, counts, metadata
