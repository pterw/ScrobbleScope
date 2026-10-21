"""Phase 5 of ``process_albums``: build the sorted results list.

Split out of ``scrobblescope/orchestrator.py`` (WP-0, Batch 22). Pure
synchronous logic -- no I/O -- except for the one cross-cutting call,
``jobs.record_unmatched``.
"""

import logging

from scrobblescope import jobs
from scrobblescope.domain import matches_release_criteria, normalize_name
from scrobblescope.unmatched import (
    REASON_NO_SPOTIFY_MATCH,
    REASON_PROVIDER_UNAVAILABLE,
    REASON_RELEASE_SCOPE,
)
from scrobblescope.utils import format_seconds, format_seconds_mobile


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

    This is wording only. Which years each scope accepts is the table in
    ``domain.release_window``; the branches here mirror its rows so the reader
    is told the year the filter wanted, and must change with it.
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
    a non-null ``original_release`` replaces the provider's date for the
    release filter and the display, and a null one (a cached "checked,
    nothing found") leaves behaviour unchanged. How the date is chosen, and
    why ``provider_release_date`` is kept, is explained once in
    ``docs/architecture/runtime-system.md`` ("How an album gets its release
    date").

    Pure synchronous logic -- no I/O.  Extracted from process_albums Phase 5
    so the data-transformation layer can be tested independently of the async
    fetch pipeline.
    """
    original_release_hits = original_release_hits or {}
    results = []
    for key, entry in cache_hits.items():
        metadata = entry["cached"]
        original_data = entry["original"]

        provider_release_date = metadata.release_date
        correction = original_release_hits.get(key)
        corrected = bool(correction and correction.get("original_release"))
        release_date = (
            correction["original_release"] if corrected else provider_release_date
        )

        if not matches_release_criteria(
            release_date, release_scope, year, decade, release_year
        ):
            artist = original_data["original_artist"]
            album = original_data["original_album"]
            reason = _get_user_friendly_reason(
                release_date, release_scope, year, decade, release_year, corrected
            )
            logging.debug(f"Skipped an album outside the release scope: {reason}")
            unmatched_key = "|".join(normalize_name(artist, album))
            unmatched_entry = {
                "artist": artist,
                "album": album,
                "reason": reason,
                "reason_code": REASON_RELEASE_SCOPE,
                "album_image": metadata.image_url,
                "spotify_id": metadata.spotify_id,
                "provider": metadata.provider,
                # An empty link is no link: the page tests it for truth and
                # the JSON has always said null.
                "album_url": metadata.url or None,
                "play_count": original_data.get("play_count"),
                # Always the provider's own date, corrected or not. The
                # correction worker (Task 9) reads it back off the unmatched
                # entry to decide which exclusions a MusicBrainz lookup could
                # still move in -- an original date is never later than the
                # provider's, so only an entry dated after the target window
                # is worth a request, and it cannot tell without this field.
                "provider_release_date": provider_release_date,
            }
            jobs.record_unmatched(job_id, unmatched_key, unmatched_entry)
            continue

        track_durations = metadata.track_durations

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
            "album_image": metadata.image_url,
            "spotify_id": metadata.spotify_id,
            "provider": metadata.provider,
            "album_url": metadata.url or None,
            # Carries the cache_hits key -- already the normalized
            # (artist_norm, album_norm) tuple, no extra normalize_name call
            # needed -- forward so jobs.update_result can match by
            # key comparison instead of re-deriving one per lookup under the
            # store's exclusion. Not surfaced anywhere: results.html and the
            # JSON endpoints read named fields only, never dump the dict.
            "_normalized_key": key,
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


#: The unmatched reasons an include run lists on Results. Below-threshold and
#: release-scope exclusions are filters, not misses, so they never appear.
_INCLUDED_UNMATCHED_REASONS = (REASON_NO_SPOTIFY_MATCH, REASON_PROVIDER_UNAVAILABLE)


def merge_unmatched_rows(results, unmatched):
    """Return *results* with the job's unmatched Last.fm albums merged in.

    Used only when the listener chose "Include" (unmatched albums). Every
    *unmatched* entry whose ``reason_code`` is ``no_spotify_match`` or
    ``provider_unavailable`` becomes a result row carrying its play count and
    ``unmatched_reason``; the rows share no provider data (no cover, link,
    provider or release date) and no play time, because none was computed and
    none is invented. Entries filtered by a listening minimum or the release
    scope are never merged.

    The new list holds *results* in their order, then the merged rows in
    *unmatched*'s order, stably sorted by ``play_count`` descending, so a
    matched row stays ahead of an unmatched row with equal plays. Neither input
    is modified. ``proportion_of_max`` and ``proportion_of_total`` are left off
    the merged rows: nothing outside ``_build_results`` reads them.

    Pure synchronous logic -- no I/O.
    """
    merged = list(results)
    for entry in (unmatched or {}).values():
        reason = entry.get("reason_code")
        if reason not in _INCLUDED_UNMATCHED_REASONS:
            continue
        artist = entry["artist"]
        album = entry["album"]
        merged.append(
            {
                "artist": artist,
                "album": album,
                "play_count": int(entry.get("play_count") or 0),
                "play_time_seconds": 0,
                "play_time": "",
                "play_time_mobile": "",
                "album_image": None,
                "album_url": None,
                "provider": None,
                "spotify_id": None,
                "release_date": None,
                "unmatched_reason": reason,
                # Same tuple _build_results sets, so jobs.update_result and the
                # release-check worker can address the row.
                "_normalized_key": normalize_name(artist, album),
            }
        )
    merged.sort(key=lambda row: row["play_count"], reverse=True)
    return merged
