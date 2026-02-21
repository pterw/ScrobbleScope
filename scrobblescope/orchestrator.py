import asyncio
import logging
import threading
import time
from math import ceil

from scrobblescope.cache import (
    _batch_lookup_metadata,
    _batch_persist_metadata,
    _get_db_connection,
)
from scrobblescope.config import (
    SPOTIFY_BATCH_CONCURRENCY,
    SPOTIFY_REQUESTS_PER_SECOND,
    SPOTIFY_SEARCH_CONCURRENCY,
)
from scrobblescope.domain import (
    SpotifyUnavailableError,
    normalize_name,
    normalize_track_name,
)
from scrobblescope.lastfm import fetch_top_albums_async
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
)
from scrobblescope.worker import release_job_slot


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

    def matches_release_criteria(release_date):
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

    def get_user_friendly_reason(release_date):
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
    new_metadata_rows = []

    try:
        if cache_misses:
            token = await fetch_spotify_access_token()
            if not token:
                logging.error(
                    "Spotify token fetch failed. Cannot process cache misses."
                )
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
            else:
                async with create_optimized_session() as session:
                    search_semaphore = asyncio.Semaphore(SPOTIFY_SEARCH_CONCURRENCY)

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
                        search_with_semaphore(key, data)
                        for key, data in cache_misses.items()
                    ]
                    search_results = await asyncio.gather(*search_tasks)

                    spotify_id_to_key = {}
                    spotify_id_to_original_data = {}
                    for key, spotify_id, data in search_results:
                        if spotify_id:
                            spotify_id_to_key[spotify_id] = key
                            spotify_id_to_original_data[spotify_id] = data
                        else:
                            original_artist = data["original_artist"]
                            original_album = data["original_album"]
                            unmatched_key = "|".join(
                                normalize_name(original_artist, original_album)
                            )
                            add_job_unmatched(
                                job_id,
                                unmatched_key,
                                {
                                    "artist": original_artist,
                                    "album": original_album,
                                    "reason": "No Spotify match",
                                },
                            )

                    valid_spotify_ids = list(spotify_id_to_original_data.keys())
                    search_duration = time.time() - search_start_time
                    logging.info(
                        f"Spotify search completed in {search_duration:.1f}s: "
                        f"{len(valid_spotify_ids)}/{len(cache_misses)} "
                        f"misses found on Spotify"
                    )

                    # Batch detail fetch
                    if valid_spotify_ids:
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

                        batch_tasks = [
                            fetch_batch_with_semaphore(batch) for batch in batch_groups
                        ]
                        batch_results = await asyncio.gather(*batch_tasks)

                        all_album_details = {}
                        for batch_result in batch_results:
                            all_album_details.update(batch_result)

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
                                normalize_track_name(t.get("name", "")): t.get(
                                    "duration_ms", 0
                                )
                                // 1000
                                for t in album_details.get("tracks", {}).get(
                                    "items", []
                                )
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

    results = []
    for key, entry in cache_hits.items():
        cached = entry["cached"]
        original_data = entry["original"]

        release_date = cached.get("release_date", "")
        if not matches_release_criteria(release_date):
            artist = original_data["original_artist"]
            album = original_data["original_album"]
            reason = get_user_friendly_reason(release_date)
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

        filtered_albums, fetch_metadata = await fetch_top_albums_async(
            job_id, username, year, min_plays=min_plays, min_tracks=min_tracks
        )
        step_elapsed = time.time() - step_start_time
        logging.info(f"Time elapsed (Last.fm data fetch): {step_elapsed:.1f}s")

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

        set_job_progress(
            job_id, progress=30, message="Preparing to fetch album data..."
        )

        step_start_time = time.time()
        set_job_progress(
            job_id,
            progress=40,
            message="Processing album data from Spotify...",
        )

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

        # Detect Spotify total failure: had albums but got 0 results
        # because every single one was "No Spotify match"
        if not results and filtered_albums:
            job_ctx = get_job_context(job_id)
            unmatched = job_ctx.get("unmatched", {}) if job_ctx else {}
            spotify_no_match = sum(
                1 for v in unmatched.values() if v.get("reason") == "No Spotify match"
            )
            if spotify_no_match == len(filtered_albums):
                set_job_error(job_id, "spotify_unavailable")
                return []

        set_job_progress(
            job_id, progress=60, message="Adding album art to your results..."
        )

        set_job_progress(
            job_id, progress=80, message="Compiling your top album list..."
        )

        set_job_progress(job_id, progress=90, message="Finalizing list...")

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
        error_code = None

        if "Too Many Requests" in error_message:
            if "spotify" in error_message.lower():
                error_code = "spotify_rate_limited"
            else:
                error_code = "lastfm_rate_limited"
        elif "not found" in error_message.lower() and "user" in error_message.lower():
            error_code = "user_not_found"

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
