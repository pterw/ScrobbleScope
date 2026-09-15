"""Phase 5 of ``process_albums``: build the sorted results list.

Split out of ``scrobblescope/orchestrator.py`` (WP-0, Batch 22). Pure
synchronous logic -- no I/O -- except for the one cross-cutting call,
``add_job_unmatched``, which the existing test suite patches at
``scrobblescope.orchestrator.add_job_unmatched``; see
``scrobblescope/orchestrator/_search.py`` for why that call goes through the
live ``orchestrator`` module reference rather than a direct import.
"""

import logging

from scrobblescope import orchestrator as _orchestrator
from scrobblescope.domain import normalize_name
from scrobblescope.unmatched import REASON_RELEASE_SCOPE
from scrobblescope.utils import format_seconds, format_seconds_mobile


def _matches_release_criteria(
    release_date, release_scope, year, decade=None, release_year=None
):
    """Check whether a release date matches the user's filter criteria.

    Pure function: data-in, bool-out.  Extracted from process_albums so it
    can be unit-tested in isolation without mocking the async I/O pipeline.
    """
    if release_scope == "all":
        return True
    if not release_date:
        return False

    release_year_str = (
        release_date.split("-")[0] if "-" in release_date else release_date
    )
    try:
        rel_year = int(release_year_str)
        if release_scope == "same":
            return rel_year == year
        if release_scope == "previous":
            return rel_year == year - 1
        if release_scope == "decade" and decade:
            decade_start = int(decade[:3] + "0")
            return decade_start <= rel_year < decade_start + 10
        if release_scope == "custom" and release_year:
            return rel_year == release_year
        return True
    except ValueError:
        logging.warning(f"Couldn't parse release year from: {release_date}")
        return False


def _get_user_friendly_reason(
    release_date, release_scope, year, decade=None, release_year=None, corrected=False
):
    """Return a human-readable explanation for why an album was filtered out.

    ``corrected=True`` (Task 8, Batch 22 WP-3) means *release_date* is a
    MusicBrainz original-release finding, not the provider's own date, so
    the wording says "First released ... not ..." instead of "Released ...
    instead of ..." -- the reader is being told the true original year, not
    that the app misread the provider's date.

    Pure function: data-in, string-out.  Extracted from process_albums so it
    can be unit-tested in isolation without mocking the async I/O pipeline.
    """
    if release_scope == "all":
        return "Should not be filtered (All Years selected)"

    release_year_str = (
        release_date.split("-")[0] if "-" in release_date else release_date
    )
    try:
        rel_year = int(release_year_str)
        if release_scope == "same":
            if corrected:
                return f"First released in {rel_year}, not {year}"
            return f"Released in {rel_year} instead of {year}"
        if release_scope == "previous":
            if corrected:
                return f"First released in {rel_year}, not {year - 1}"
            return f"Released in {rel_year} instead of {year - 1}"
        if release_scope == "decade" and decade:
            decade_start = int(decade[:3] + "0")
            decade_end = decade_start + 9
            if corrected:
                return f"First released in {rel_year}, outside of {decade_start}-{decade_end}"
            return f"Released in {rel_year}, outside of {decade_start}-{decade_end}"
        if release_scope == "custom" and release_year:
            if corrected:
                return f"First released in {rel_year}, not {release_year}"
            return f"Released in {rel_year} instead of {release_year}"
        if corrected:
            return f"First released in {rel_year}, which does not match filter"
        return f"Release year {rel_year} does not match filter"
    except ValueError:
        return f"Unknown release year: {release_date}"


def _album_provider(cached):
    """Return the provider that supplied *cached*'s metadata, or None.

    ``provider`` is only present on rows written since Batch 22 WP-1
    Task 2 (or backfilled by its migration). A row with a ``spotify_id``
    but no ``provider`` predates that column and is a Spotify row in
    every case, so it falls back to "spotify" rather than reporting an
    unknown source for data that is, in fact, known.
    """
    return cached.get("provider") or ("spotify" if cached.get("spotify_id") else None)


def _album_url(cached):
    """Return the link to *cached*'s album page on its provider, or None.

    ``provider_url`` is only present on rows written since Task 2; a
    Spotify row from before that (or fetched live before Task 5 wired the
    provider fields into the live fetch path) carries only ``spotify_id``,
    from which the classic Spotify album URL is reconstructed.
    """
    url = cached.get("provider_url")
    if url:
        return url
    spotify_id = cached.get("spotify_id")
    if spotify_id:
        return f"https://open.spotify.com/album/{spotify_id}"
    return None


def _build_results(
    cache_hits,
    job_id,
    year,
    sort_mode,
    release_scope,
    decade=None,
    release_year=None,
    original_release_hits=None,
):
    """Transform unified cache_hits into the sorted results list for the frontend.

    Applies release-date filtering, computes play-time totals, sorts by the
    chosen mode, and calculates proportion-of-max/total percentages.
    Albums that fail the release filter are logged and added to job unmatched.

    ``original_release_hits`` (Task 8, Batch 22 WP-3) is an optional dict
    keyed by the same ``(artist_norm, album_norm)`` tuples as *cache_hits*,
    holding any already-cached MusicBrainz finding
    (``{"mb_release_group": ..., "original_release": ...}``). A finding with
    a non-null ``original_release`` drives both the release filter and the
    displayed date in place of the provider's own date, which survives as
    ``provider_release_date`` on the result. No finding, or one whose
    ``original_release`` is null (a cached "checked, nothing found"),
    leaves behaviour unchanged from before this parameter existed.

    Pure synchronous logic -- no I/O.  Extracted from process_albums Phase 5
    so the data-transformation layer can be tested independently of the async
    fetch pipeline.
    """
    original_release_hits = original_release_hits or {}
    results = []
    for key, entry in cache_hits.items():
        cached = entry["cached"]
        original_data = entry["original"]

        provider_release_date = cached.get("release_date", "")
        correction = original_release_hits.get(key)
        corrected = bool(correction and correction.get("original_release"))
        release_date = (
            correction["original_release"] if corrected else provider_release_date
        )

        if not _matches_release_criteria(
            release_date, release_scope, year, decade, release_year
        ):
            artist = original_data["original_artist"]
            album = original_data["original_album"]
            reason = _get_user_friendly_reason(
                release_date, release_scope, year, decade, release_year, corrected
            )
            logging.debug(f"Skipped '{album}' by '{artist}': {reason}")
            unmatched_key = "|".join(normalize_name(artist, album))
            unmatched_entry = {
                "artist": artist,
                "album": album,
                "reason": reason,
                "reason_code": REASON_RELEASE_SCOPE,
                "album_image": cached.get("album_image_url"),
                "spotify_id": cached.get("spotify_id"),
                "provider": _album_provider(cached),
                "album_url": _album_url(cached),
                "play_count": original_data.get("play_count"),
                # Always the provider's own date, corrected or not. The
                # correction worker (Task 9) reads it back off the unmatched
                # entry to decide which exclusions a MusicBrainz lookup could
                # still move in -- an original date is never later than the
                # provider's, so only an entry dated after the target window
                # is worth a request, and it cannot tell without this field.
                "provider_release_date": provider_release_date,
            }
            _orchestrator.add_job_unmatched(job_id, unmatched_key, unmatched_entry)
            continue

        track_durations = cached.get("track_durations") or {}

        play_time_sec = sum(
            track_durations.get(track, 0) * count
            for track, count in original_data["track_counts"].items()
        )

        result = {
            "artist": original_data["original_artist"],
            "album": original_data["original_album"],
            "play_count": original_data["play_count"],
            "play_time": format_seconds(play_time_sec),
            "play_time_mobile": format_seconds_mobile(play_time_sec),
            "play_time_seconds": play_time_sec,
            "different_songs": len(original_data["track_counts"]),
            "release_date": release_date,
            "album_image": cached.get("album_image_url"),
            "spotify_id": cached.get("spotify_id", ""),
            "provider": _album_provider(cached),
            "album_url": _album_url(cached),
        }
        if corrected:
            result["provider_release_date"] = provider_release_date
        results.append(result)

    if sort_mode == "playtime":
        results.sort(key=lambda x: x["play_time_seconds"], reverse=True)
    else:
        results.sort(key=lambda x: x["play_count"], reverse=True)

    if results:
        if sort_mode == "playtime":
            max_val = results[0]["play_time_seconds"] or 1
            total_val = sum(r["play_time_seconds"] for r in results) or 1
            sort_key = "play_time_seconds"
        else:
            max_val = results[0]["play_count"] or 1
            total_val = sum(r["play_count"] for r in results) or 1
            sort_key = "play_count"

        for result in results:
            result["proportion_of_max"] = (result[sort_key] / max_val) * 100
            result["proportion_of_total"] = (result[sort_key] / total_val) * 100

    return results
