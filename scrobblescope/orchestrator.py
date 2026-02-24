import asyncio
import logging
import threading
import time
from collections import defaultdict
from datetime import datetime
from math import ceil
from typing import Any, cast

from scrobblescope.cache import (
    _batch_lookup_metadata,
    _batch_persist_metadata,
    _cleanup_stale_metadata,
    _get_db_connection,
)
from scrobblescope.config import (
    SPOTIFY_BATCH_CONCURRENCY,
    SPOTIFY_REQUESTS_PER_SECOND,
    SPOTIFY_SEARCH_CONCURRENCY,
)
from scrobblescope.domain import normalize_name, normalize_track_name
from scrobblescope.errors import SpotifyUnavailableError
from scrobblescope.lastfm import fetch_all_recent_tracks_async
from scrobblescope.repositories import (
    add_job_unmatched,
    cleanup_expired_jobs,
    get_job_context,
    set_job_error,
    set_job_progress,
    set_job_results,
    set_job_stat,
)
from scrobblescope.spotify import (
    fetch_spotify_access_token,
    fetch_spotify_album_details_batch,
    search_for_spotify_album_id,
)
from scrobblescope.utils import (
    cleanup_expired_cache,
    create_optimized_session,
    format_seconds,
    format_seconds_mobile,
)
from scrobblescope.worker import release_job_slot

# Hard upper bound on the number of albums sent to process_albums when sorting
# by playtime. Playtime ranking requires Spotify track durations, so pre-slicing
# is impossible -- but an unbounded album count creates proportional Spotify API
# load. 500 albums at 20 per batch = 25 batch requests, well within practical
# limits. A user with 500+ albums passing min_plays/min_tracks is an extreme
# outlier; raw play_count is the best available proxy for culling the tail.
_PLAYTIME_ALBUM_CAP = 500


async def fetch_top_albums_async(
    username, year, min_plays=10, min_tracks=3, progress_cb=None
):
    """Fetch and filter top albums. Returns (filtered_albums, fetch_metadata) tuple.

    The returned ``fetch_metadata`` dict includes a ``stats`` key with
    aggregation counters (total_scrobbles, pages_fetched, unique_albums,
    albums_passing_filter) so the caller can record them as job stats.

    Args:
        progress_cb: Optional ``Callable[[int, int], None]`` forwarded to
            ``fetch_all_recent_tracks_async`` for per-page progress.
    """
    logging.debug(f"Start fetch_top_albums_async(user={username}, year={year})")
    from_ts = int(datetime(year, 1, 1).timestamp())
    to_ts = int(datetime(year, 12, 31, 23, 59, 59).timestamp())
    pages, fetch_metadata = await fetch_all_recent_tracks_async(
        username, from_ts, to_ts, progress_cb=progress_cb
    )
    logging.debug(f"Pages fetched: {len(pages)}")
    total_tracks = sum(len(p.get("recenttracks", {}).get("track", [])) for p in pages)
    logging.debug(f"Total tracks: {total_tracks}")

    if fetch_metadata.get("status") == "partial":
        dropped = fetch_metadata["pages_dropped"]
        expected = fetch_metadata["pages_expected"]
        pct = round((dropped / expected) * 100)
        fetch_metadata["partial_data_warning"] = (
            f"Note: {dropped} of {expected} Last.fm pages failed to load "
            f"({pct}% data loss). Results may be incomplete."
        )

    albums: defaultdict[tuple[str, str], dict[str, Any]] = defaultdict(
        lambda: {"play_count": 0, "track_counts": defaultdict(int)}
    )
    for page in pages:
        for t in page.get("recenttracks", {}).get("track", []):
            alb = t.get("album", {}).get("#text", "...")
            art = t.get("artist", {}).get("#text", "...")
            name = t.get("name", "...")
            date = t.get("date", {}).get("uts")
            if not date:
                continue
            ts = int(date)
            if ts < from_ts or ts > to_ts:
                continue
            if alb and art and name:
                key = normalize_name(art, alb)
                if "original_artist" not in albums[key]:
                    albums[key]["original_artist"] = art
                    albums[key]["original_album"] = alb
                albums[key]["play_count"] += 1
                normalized = normalize_track_name(name)
                albums[key]["track_counts"][normalized] += 1
    logging.debug(f"Unique albums: {len(albums)}")

    filtered = {
        k: v
        for k, v in albums.items()
        if v["play_count"] >= min_plays and len(v["track_counts"]) >= min_tracks
    }
    logging.debug(f"Albums after filter: {len(filtered)}")

    fetch_metadata["stats"] = {
        "total_scrobbles": total_tracks,
        "pages_fetched": len(pages),
        "unique_albums": len(albums),
        "albums_passing_filter": len(filtered),
    }

    return filtered, fetch_metadata


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
    release_date, release_scope, year, decade=None, release_year=None
):
    """Return a human-readable explanation for why an album was filtered out.

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
            return f"Released in {rel_year} instead of {year}"
        if release_scope == "previous":
            return f"Released in {rel_year} instead of {year - 1}"
        if release_scope == "decade" and decade:
            decade_start = int(decade[:3] + "0")
            decade_end = decade_start + 9
            return f"Released in {rel_year}, outside of {decade_start}-{decade_end}"
        if release_scope == "custom" and release_year:
            return f"Released in {rel_year} instead of {release_year}"
        return f"Release year {rel_year} does not match filter"
    except ValueError:
        return f"Unknown release year: {release_date}"


async def _run_spotify_search_phase(
    job_id,
    session,
    cache_misses,
    token,
    search_semaphore,
):
    """Parallel Spotify search for all cache misses.

    Reports progress in the 20-40% range. Registers unmatched albums via
    add_job_unmatched. Returns (spotify_id_to_key, spotify_id_to_original_data).
    """
    logging.info(
        f"Starting parallel search for {len(cache_misses)} "
        f"Spotify albums (max {SPOTIFY_SEARCH_CONCURRENCY} "
        f"concurrent, {SPOTIFY_REQUESTS_PER_SECOND} req/s limit)"
    )
    search_start_time = time.time()

    async def search_with_semaphore(key, data):
        artist, album = key
        spotify_id = await search_for_spotify_album_id(
            session,
            artist,
            album,
            token,
            semaphore=search_semaphore,
        )
        return key, spotify_id, data

    search_tasks = [
        search_with_semaphore(key, data) for key, data in cache_misses.items()
    ]

    search_results = []
    searches_done = 0
    total_searches = len(search_tasks)
    for fut in asyncio.as_completed(search_tasks):
        result = await fut
        search_results.append(result)
        searches_done += 1
        # Map search progress into the 20%-40% range
        pct = 20 + int(20 * searches_done / max(total_searches, 1))
        set_job_progress(
            job_id,
            progress=pct,
            message=(
                f"Searching Spotify: {searches_done}/" f"{total_searches} albums..."
            ),
        )

    spotify_id_to_key = {}
    spotify_id_to_original_data = {}
    for key, spotify_id, data in search_results:
        if spotify_id:
            spotify_id_to_key[spotify_id] = key
            spotify_id_to_original_data[spotify_id] = data
        else:
            original_artist = data["original_artist"]
            original_album = data["original_album"]
            unmatched_key = "|".join(normalize_name(original_artist, original_album))
            add_job_unmatched(
                job_id,
                unmatched_key,
                {
                    "artist": original_artist,
                    "album": original_album,
                    "reason": "No Spotify match",
                },
            )

    search_duration = time.time() - search_start_time
    logging.info(
        f"Spotify search completed in {search_duration:.1f}s: "
        f"{len(spotify_id_to_key)}/{len(cache_misses)} "
        f"misses found on Spotify"
    )

    return spotify_id_to_key, spotify_id_to_original_data


async def _run_spotify_batch_detail_phase(
    job_id,
    session,
    valid_spotify_ids,
    token,
    spotify_id_to_key,
    spotify_id_to_original_data,
    cache_hits,
):
    """Batch-fetch Spotify album details for all found IDs.

    Reports progress in the 40-60% range. Promotes enriched albums into
    cache_hits (mutated in place). Returns new_metadata_rows.
    """
    new_metadata_rows = []
    batch_size = 20
    num_batches = ceil(len(valid_spotify_ids) / batch_size)
    logging.info(
        f"Fetching album details for "
        f"{len(valid_spotify_ids)} albums "
        f"in {num_batches} parallel batches "
        f"(batch size: {batch_size})"
    )
    batch_start_time = time.time()

    batch_groups = [
        valid_spotify_ids[i : i + batch_size]
        for i in range(0, len(valid_spotify_ids), batch_size)
    ]
    batch_semaphore = asyncio.Semaphore(SPOTIFY_BATCH_CONCURRENCY)

    async def fetch_batch_with_semaphore(batch_ids):
        return await fetch_spotify_album_details_batch(
            session,
            batch_ids,
            token,
            semaphore=batch_semaphore,
        )

    batch_tasks = [fetch_batch_with_semaphore(batch) for batch in batch_groups]

    all_album_details = {}
    batches_done = 0
    for fut in asyncio.as_completed(batch_tasks):
        batch_result = await fut
        all_album_details.update(batch_result)
        batches_done += 1
        # Map batch progress into the 40%-60% range
        pct = 40 + int(20 * batches_done / max(num_batches, 1))
        enriched_so_far = len(all_album_details)
        set_job_progress(
            job_id,
            progress=pct,
            message=(
                f"Enriched {enriched_so_far}/"
                f"{len(valid_spotify_ids)} albums from Spotify..."
            ),
        )

    batch_duration = time.time() - batch_start_time
    logging.info(
        f"Album details fetch completed in "
        f"{batch_duration:.1f}s: Got details for "
        f"{len(all_album_details)} albums"
    )

    # Extract cacheable fields, promote to cache_hits
    for spotify_id, album_details in all_album_details.items():
        if not album_details:
            continue
        original_data = spotify_id_to_original_data.get(spotify_id)
        if not original_data:
            continue
        key = spotify_id_to_key[spotify_id]

        release_date = album_details.get("release_date", "")
        album_image_url = (
            album_details.get("images", [{}])[0].get("url")
            if album_details.get("images")
            else None
        )
        track_durations = {
            normalize_track_name(t.get("name", "")): t.get("duration_ms", 0) // 1000
            for t in album_details.get("tracks", {}).get("items", [])
        }

        cache_hits[key] = {
            "cached": {
                "spotify_id": spotify_id,
                "release_date": release_date,
                "album_image_url": album_image_url,
                "track_durations": track_durations,
            },
            "original": original_data,
        }

        new_metadata_rows.append(
            (
                key[0],
                key[1],
                spotify_id,
                release_date,
                album_image_url,
                track_durations,
            )
        )

    return new_metadata_rows


async def _fetch_spotify_misses(job_id, cache_misses, cache_hits):
    """Fetch Spotify metadata for cache misses via search + batch detail.

    Mutates *cache_hits* in place by promoting newly found entries.
    Returns a list of new_metadata_rows tuples for DB persistence.
    Raises SpotifyUnavailableError if token fetch fails and no cache_hits exist.
    """
    if not cache_misses:
        return []

    token = await fetch_spotify_access_token()
    if not token:
        logging.error("Spotify token fetch failed. Cannot process cache misses.")
        if not cache_hits:
            raise SpotifyUnavailableError(
                "Spotify token fetch failed while processing cache misses."
            )
        set_job_stat(
            job_id,
            "partial_data_warning",
            (
                "Spotify is temporarily unavailable. "
                "Showing cached albums only for this request."
            ),
        )
        return []

    new_metadata_rows = []
    async with create_optimized_session() as session:
        search_semaphore = asyncio.Semaphore(SPOTIFY_SEARCH_CONCURRENCY)
        spotify_id_to_key, spotify_id_to_original_data = (
            await _run_spotify_search_phase(
                job_id, session, cache_misses, token, search_semaphore
            )
        )
        valid_spotify_ids = list(spotify_id_to_original_data.keys())
        if valid_spotify_ids:
            new_metadata_rows = await _run_spotify_batch_detail_phase(
                job_id,
                session,
                valid_spotify_ids,
                token,
                spotify_id_to_key,
                spotify_id_to_original_data,
                cache_hits,
            )
    return new_metadata_rows


def _build_results(
    cache_hits, job_id, year, sort_mode, release_scope, decade=None, release_year=None
):
    """Transform unified cache_hits into the sorted results list for the frontend.

    Applies release-date filtering, computes play-time totals, sorts by the
    chosen mode, and calculates proportion-of-max/total percentages.
    Albums that fail the release filter are logged and added to job unmatched.

    Pure synchronous logic -- no I/O.  Extracted from process_albums Phase 5
    so the data-transformation layer can be tested independently of the async
    fetch pipeline.
    """
    results = []
    for key, entry in cache_hits.items():
        cached = entry["cached"]
        original_data = entry["original"]

        release_date = cached.get("release_date", "")
        if not _matches_release_criteria(
            release_date, release_scope, year, decade, release_year
        ):
            artist = original_data["original_artist"]
            album = original_data["original_album"]
            reason = _get_user_friendly_reason(
                release_date, release_scope, year, decade, release_year
            )
            logging.debug(f"Skipped '{album}' by '{artist}': {reason}")
            unmatched_key = "|".join(normalize_name(artist, album))
            add_job_unmatched(
                job_id,
                unmatched_key,
                {"artist": artist, "album": album, "reason": reason},
            )
            continue

        track_durations = cached.get("track_durations") or {}

        play_time_sec = sum(
            track_durations.get(track, 0) * count
            for track, count in original_data["track_counts"].items()
        )

        results.append(
            {
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
            }
        )

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


async def process_albums(
    job_id,
    filtered_albums,
    year,
    sort_mode,
    release_scope,
    decade=None,
    release_year=None,
):
    """Process albums using cached metadata when available, fetching from
    Spotify only for cache misses, then persisting new results."""
    logging.info(
        f"Processing {len(filtered_albums)} albums. "
        f"Filters: year={year}, release_scope={release_scope}, "
        f"decade={decade}, release_year={release_year}"
    )

    # =================================================================
    # Phase 1: DB Batch Lookup
    # =================================================================
    conn = await _get_db_connection()
    set_job_stat(job_id, "db_cache_enabled", bool(conn))
    cached_metadata = {}
    if conn:
        try:
            cached_metadata = await _batch_lookup_metadata(
                conn, list(filtered_albums.keys())
            )
            set_job_stat(job_id, "db_cache_lookup_hits", len(cached_metadata))
            logging.info(
                f"DB cache: {len(cached_metadata)} hits / "
                f"{len(filtered_albums)} total albums"
            )
        except Exception as exc:
            logging.warning(f"DB lookup failed, proceeding without cache: {exc}")
            set_job_stat(
                job_id, "db_cache_warning", "DB lookup failed; cache bypassed."
            )
            cached_metadata = {}
        # Opportunistic stale-row cleanup -- non-fatal, errors swallowed inside.
        await _cleanup_stale_metadata(conn)
    else:
        set_job_stat(
            job_id,
            "db_cache_warning",
            "DB cache unavailable; using Spotify fallback.",
        )

    # =================================================================
    # Phase 2: Partition into cache hits and misses
    # =================================================================
    cache_hits = {}  # key -> {"cached": dict, "original": original_data}
    cache_misses = {}  # key -> original_data

    for key, original_data in filtered_albums.items():
        if key in cached_metadata:
            cache_hits[key] = {
                "cached": cached_metadata[key],
                "original": original_data,
            }
        else:
            cache_misses[key] = original_data

    db_hit_count = len(cache_hits)
    set_job_stat(job_id, "cache_hits", db_hit_count)
    logging.info(f"Cache partition: {db_hit_count} hits, {len(cache_misses)} misses")

    # =================================================================
    # Phase 3: Spotify fetch for misses only
    # =================================================================
    try:
        new_metadata_rows = await _fetch_spotify_misses(
            job_id, cache_misses, cache_hits
        )

        # =============================================================
        # Phase 4: DB Batch Persist
        # =============================================================
        if conn and new_metadata_rows:
            try:
                await _batch_persist_metadata(conn, new_metadata_rows)
                set_job_stat(job_id, "db_cache_persisted", len(new_metadata_rows))
                logging.info(
                    f"Persisted {len(new_metadata_rows)} new metadata "
                    f"rows to DB cache"
                )
            except Exception as exc:
                logging.warning(f"DB persist failed (non-fatal): {exc}")
                set_job_stat(job_id, "db_cache_warning", "DB persist failed.")
    finally:
        if conn:
            await conn.close()

    # =================================================================
    # Phase 5: Build results from unified cache_hits
    # =================================================================
    total_matched = len(cache_hits)
    set_job_stat(job_id, "spotify_matched", total_matched)
    set_job_stat(
        job_id,
        "spotify_unmatched",
        len(filtered_albums) - total_matched,
    )

    return _build_results(
        cache_hits, job_id, year, sort_mode, release_scope, decade, release_year
    )


def _record_lastfm_stats(job_id, fetch_metadata):
    """Write Last.fm aggregation stats and partial-data warning into the job."""
    lastfm_stats = fetch_metadata.get("stats")
    if isinstance(lastfm_stats, dict):
        for stat_key, stat_val in lastfm_stats.items():
            set_job_stat(job_id, stat_key, stat_val)
    partial_warning = fetch_metadata.get("partial_data_warning")
    if partial_warning:
        set_job_stat(job_id, "partial_data_warning", partial_warning)
        set_job_stat(job_id, "pages_dropped", fetch_metadata.get("pages_dropped", 0))


def _apply_pre_slice(filtered_albums, sort_mode, limit_results, release_scope):
    """Apply pre-Spotify pre-slicing and playtime cap.

    Playcount pre-slice: only when sort_mode='playcount', release_scope='all',
    and limit_results is a valid integer. Playtime cap: fires at
    _PLAYTIME_ALBUM_CAP when sort_mode='playtime'. Returns the (possibly
    reduced) dict.
    """
    if sort_mode == "playcount" and limit_results != "all" and release_scope == "all":
        try:
            limit = int(limit_results)
            if len(filtered_albums) > limit:
                sorted_items = sorted(
                    filtered_albums.items(),
                    key=lambda kv: cast(int, kv[1]["play_count"]),
                    reverse=True,
                )
                filtered_albums = dict(sorted_items[:limit])
                logging.info(f"Pre-sliced filtered_albums to top {limit} by play_count")
        except ValueError:
            pass  # malformed limit_results handled by the post-process slice

    if sort_mode == "playtime" and len(filtered_albums) > _PLAYTIME_ALBUM_CAP:
        sorted_items = sorted(
            filtered_albums.items(),
            key=lambda kv: cast(int, kv[1]["play_count"]),
            reverse=True,
        )
        filtered_albums = dict(sorted_items[:_PLAYTIME_ALBUM_CAP])
        logging.warning(
            f"Playtime album cap applied: capped {len(sorted_items)} albums "
            f"to top {_PLAYTIME_ALBUM_CAP} by play_count before Spotify fetch"
        )

    return filtered_albums


def _detect_spotify_total_failure(job_id, results, filtered_albums):
    """Return True and set job error if all filtered albums had no Spotify match.

    Only fires when results is empty but filtered_albums is non-empty.
    Reads job unmatched state to count 'No Spotify match' entries.
    """
    if not results and filtered_albums:
        job_ctx = get_job_context(job_id)
        unmatched = job_ctx.get("unmatched", {}) if job_ctx else {}
        spotify_no_match = sum(
            1 for v in unmatched.values() if v.get("reason") == "No Spotify match"
        )
        if spotify_no_match == len(filtered_albums):
            set_job_error(job_id, "spotify_unavailable")
            return True
    return False


def _apply_post_slice(results, limit_results):
    """Truncate results to limit_results if it is a valid integer."""
    if limit_results != "all":
        try:
            limit = int(limit_results)
            if len(results) > limit:
                results = results[:limit]
                logging.info(f"Limited results to top {limit} albums")
        except ValueError:
            logging.warning(
                f"Invalid limit_results value: {limit_results}, showing all results"
            )
    return results


def _classify_exception_to_error_code(error_message):
    """Map an exception message to a classified error code, or None.

    Returns 'spotify_rate_limited', 'lastfm_rate_limited', 'user_not_found',
    or None for unclassified errors.
    """
    if "Too Many Requests" in error_message:
        if "spotify" in error_message.lower():
            return "spotify_rate_limited"
        return "lastfm_rate_limited"
    if "not found" in error_message.lower() and "user" in error_message.lower():
        return "user_not_found"
    return None


async def _fetch_and_process(
    job_id,
    username,
    year,
    sort_mode,
    release_scope,
    decade=None,
    release_year=None,
    min_plays=10,
    min_tracks=3,
    limit_results="all",
):
    """Fetch and process albums in the background for a single job."""
    try:
        overall_start_time = time.time()
        cleanup_expired_cache()
        cleanup_expired_jobs()

        set_job_progress(
            job_id,
            progress=0,
            message="Initializing...",
            error=False,
            reset_stats=True,
        )

        step_start_time = time.time()
        set_job_progress(
            job_id,
            progress=5,
            message="Fetching your data from Last.fm...",
            error=False,
        )

        def _lastfm_progress(pages_done, total_pages):
            """Map page-fetching progress into the 5%-20% range."""
            pct = 5 + int(15 * pages_done / max(total_pages, 1))
            set_job_progress(
                job_id,
                progress=pct,
                message=f"Fetching Last.fm page {pages_done}/{total_pages}...",
            )

        filtered_albums, fetch_metadata = await fetch_top_albums_async(
            username,
            year,
            min_plays=min_plays,
            min_tracks=min_tracks,
            progress_cb=_lastfm_progress,
        )
        step_elapsed = time.time() - step_start_time
        logging.info(f"Time elapsed (Last.fm data fetch): {step_elapsed:.1f}s")

        _record_lastfm_stats(job_id, fetch_metadata)

        # Upstream failure: Last.fm was unreachable
        if fetch_metadata.get("status") == "error":
            set_job_error(
                job_id,
                fetch_metadata.get("reason", "lastfm_unavailable"),
                username=username,
            )
            return []

        # Legitimate empty result: user has scrobbles but none pass filters
        if not filtered_albums:
            set_job_results(job_id, [])
            set_job_progress(
                job_id,
                progress=100,
                message="No albums found for the specified criteria.",
                error=False,
            )
            return []

        set_job_progress(job_id, progress=20, message="Processing your albums...")

        filtered_albums = _apply_pre_slice(
            filtered_albums, sort_mode, limit_results, release_scope
        )

        set_job_progress(
            job_id,
            progress=20,
            message=f"Preparing {len(filtered_albums)} albums for Spotify lookup...",
        )

        step_start_time = time.time()

        try:
            results = await process_albums(
                job_id,
                filtered_albums,
                year,
                sort_mode,
                release_scope,
                decade,
                release_year,
            )
        except SpotifyUnavailableError:
            set_job_error(job_id, "spotify_unavailable")
            return []
        step_elapsed = time.time() - step_start_time
        logging.info(f"Time elapsed (Spotify album processing): {step_elapsed:.1f}s")

        if _detect_spotify_total_failure(job_id, results, filtered_albums):
            return []

        set_job_progress(
            job_id, progress=60, message="Adding album art to your results..."
        )

        set_job_progress(
            job_id, progress=80, message="Compiling your top album list..."
        )

        set_job_progress(job_id, progress=90, message="Finalizing list...")

        results = _apply_post_slice(results, limit_results)

        overall_elapsed = time.time() - overall_start_time
        logging.info(f"Total time elapsed: {overall_elapsed:.1f}s")

        set_job_results(job_id, results)
        set_job_progress(
            job_id,
            progress=100,
            message=f"Done! Found {len(results)} albums matching your criteria.",
            error=False,
        )
        return results

    except Exception as exc:
        error_message = str(exc)
        error_code = _classify_exception_to_error_code(error_message)

        if error_code:
            set_job_error(job_id, error_code, username=username)
        else:
            set_job_results(job_id, [])
            set_job_progress(
                job_id,
                progress=100,
                message=f"Error: {error_message}",
                error=True,
                error_code="unknown",
                retryable=True,
            )

        logging.exception(f"Error processing request for {username} in {year}")
        return []


def background_task(
    job_id,
    username,
    year,
    sort_mode,
    release_scope,
    decade=None,
    release_year=None,
    min_plays=10,
    min_tracks=3,
    limit_results="all",
):
    """Run the async fetch pipeline in a dedicated event loop on this thread."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(
            _fetch_and_process(
                job_id,
                username,
                year,
                sort_mode,
                release_scope,
                decade,
                release_year,
                min_plays,
                min_tracks,
                limit_results,
            )
        )
    except Exception:
        logging.exception(f"Unhandled error in background task for {username}/{year}")
    finally:
        loop.close()
        release_job_slot()
