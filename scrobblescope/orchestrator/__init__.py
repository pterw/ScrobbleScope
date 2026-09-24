"""Stable public facade for the album-enrichment pipeline.

WP-0 (Batch 22) split the former ``scrobblescope/orchestrator.py`` into this
package. The self-contained phase steps live in private submodules
(``_search``, ``_details``, ``_cache``, ``_results``); the pipeline glue that
ties them together -- ``fetch_top_albums_async``, ``process_albums``,
``_fetch_and_process``, ``background_task`` and their small helpers -- stays
here because each one calls the next in a single, tightly-coupled sequence.

Every external dependency stays imported here, unchanged, even where only a
submodule still calls it directly: the existing test suite patches many of
them at ``scrobblescope.orchestrator.<name>``, and a submodule reads the
current value of a same-named attribute through the ``orchestrator`` module
reference at the top of each phase file, not through its own import. Moving
an import out of this file without also checking every submodule that reads
it this way silently breaks that patch path. Importers should continue to
use this facade so that the internal module boundaries may evolve safely.
"""

import asyncio
import logging
import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from scrobblescope.cache import (
    _batch_lookup_metadata,
    _batch_lookup_original_release,
    _batch_persist_metadata,
    _cleanup_stale_metadata,
    _get_db_connection,
)
from scrobblescope.config import SPOTIFY_SEARCH_CONCURRENCY
from scrobblescope.deezer import fetch_deezer_album, search_deezer_album
from scrobblescope.domain import normalize_name, normalize_track_name
from scrobblescope.errors import SpotifyUnavailableError
from scrobblescope.lastfm import fetch_all_recent_tracks_async
from scrobblescope.release_checks import enqueue_release_check
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
    album_metadata_from_details,
    fetch_spotify_access_token,
    fetch_spotify_album_details_batch,
    search_for_spotify_album_id,
)
from scrobblescope.unmatched import (
    REASON_NO_SPOTIFY_MATCH,
    partition_albums_by_threshold,
)
from scrobblescope.utils import cleanup_expired_cache, create_optimized_session
from scrobblescope.worker import (
    new_thread_event_loop,
    release_job_slot,
    run_coroutine_in_new_loop,
)

# Hard upper bound on the number of albums sent to process_albums across all sort
# modes. An unbounded album count creates proportional Spotify API load and
# frontend DOM bloat. 500 albums at 20 per batch = 25 batch requests, well within
# practical limits. A user with 500+ albums passing min_plays/min_tracks is an extreme
# outlier; raw play_count is the best available proxy for culling the tail.
_MAX_ALBUM_CAP = 500
_PLAYTIME_ALBUM_CAP = _MAX_ALBUM_CAP


def _cap_threshold_exclusions(threshold_exclusions):
    """Cap a threshold-exclusions dict to ``_MAX_ALBUM_CAP`` entries.

    Called by ``fetch_top_albums_async`` after partitioning albums by the
    listening thresholds; Batch 23's export path will be the second caller.

    Returns the dict unchanged when it is already at or below the cap, or a
    new dict holding only the top ``_MAX_ALBUM_CAP`` entries by play count
    otherwise.
    """
    if len(threshold_exclusions) > _MAX_ALBUM_CAP:
        # Ties are broken by normalized key so the retained set does not depend on
        # the mapping's insertion order. A stable sort alone would keep whichever
        # tied album happened to be inserted first, which is a property of the
        # fetch path rather than of this decision.
        sorted_exclusion_keys = sorted(
            threshold_exclusions.keys(),
            key=lambda k: (-int(threshold_exclusions[k].get("play_count", 0)), k),
        )[:_MAX_ALBUM_CAP]
        threshold_exclusions = {
            k: threshold_exclusions[k] for k in sorted_exclusion_keys
        }
    return threshold_exclusions


async def fetch_top_albums_async(
    username, year, min_plays=10, min_tracks=3, progress_cb=None
):
    """Fetch and partition top albums by the configured listening thresholds.

    Returns an ``(eligible_albums, threshold_exclusions, fetch_metadata)``
    tuple. Threshold exclusions retain report facts but never enter Spotify
    enrichment.

    The returned ``fetch_metadata`` dict includes a ``stats`` key with
    aggregation counters (total_scrobbles, pages_fetched, unique_albums,
    albums_passing_filter) so the caller can record them as job stats.

    Args:
        progress_cb: Optional ``Callable[[int, int], None]`` forwarded to
            ``fetch_all_recent_tracks_async`` for per-page progress.
    """
    logging.debug(f"Start fetch_top_albums_async(user={username}, year={year})")
    from_ts = int(datetime(year, 1, 1, tzinfo=timezone.utc).timestamp())
    to_ts = int(datetime(year, 12, 31, 23, 59, 59, tzinfo=timezone.utc).timestamp())
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

    filtered, threshold_exclusions = partition_albums_by_threshold(
        dict(albums), min_plays, min_tracks
    )
    logging.debug(f"Albums after filter: {len(filtered)}")

    total_below_threshold = len(threshold_exclusions)
    threshold_exclusions = _cap_threshold_exclusions(threshold_exclusions)

    fetch_metadata["stats"] = {
        "total_scrobbles": total_tracks,
        "pages_fetched": len(pages),
        "unique_albums": len(albums),
        "albums_passing_filter": len(filtered),
        "albums_below_threshold": total_below_threshold,
    }

    return filtered, threshold_exclusions, fetch_metadata


async def _fetch_spotify_misses(job_id, cache_misses, cache_hits):
    """Enrich cache misses via Spotify search + batch detail, then Deezer
    for whatever Spotify still could not enrich.

    Mutates *cache_hits* in place by promoting newly found entries.
    Returns a list of new_metadata_rows tuples for DB persistence.
    Raises SpotifyUnavailableError only when Spotify's token fetch fails,
    nothing was already cached before this call, and Deezer could not
    enrich a single album either -- a Deezer-only run that finds at least
    one match is a valid, if partial, outcome, not a failure.
    """
    if not cache_misses:
        return []

    had_cache_hits = bool(cache_hits)
    new_metadata_rows = []
    token = await fetch_spotify_access_token()
    still_missing = cache_misses

    if not token:
        logging.error(
            "Spotify token fetch failed. Falling back to Deezer for all misses."
        )
        set_job_stat(
            job_id,
            "partial_data_warning",
            "Spotify is temporarily unavailable; checking Deezer for album details.",
        )
    else:
        async with create_optimized_session() as session:
            search_semaphore = asyncio.Semaphore(SPOTIFY_SEARCH_CONCURRENCY)
            (
                spotify_id_to_key,
                spotify_id_to_original_data,
                _search_miss_keys,
            ) = await _run_spotify_search_phase(
                job_id, session, cache_misses, token, search_semaphore
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
        still_missing = {
            key: data for key, data in cache_misses.items() if key not in cache_hits
        }

    if still_missing:
        async with create_optimized_session() as session:
            deezer_rows = await _run_deezer_fallback_phase(
                job_id, session, still_missing, cache_hits
            )
        new_metadata_rows.extend(deezer_rows)

    if not token and not had_cache_hits and not new_metadata_rows:
        raise SpotifyUnavailableError(
            "Spotify token fetch failed and Deezer could not enrich any album."
        )

    return new_metadata_rows


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
    cached_metadata = await _lookup_cached_metadata(
        conn, job_id, list(filtered_albums.keys())
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
        await _persist_new_metadata(conn, job_id, new_metadata_rows)

        # =============================================================
        # Phase 4b: Original-release correction lookup (Task 8, Batch 22
        # WP-3). Applies findings already in original_release_cache --
        # the live MusicBrainz worker (Task 9) is what populates new ones.
        # =============================================================
        original_release_hits = await _lookup_cached_original_release(
            conn, list(cache_hits.keys())
        )
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
        cache_hits,
        job_id,
        year,
        sort_mode,
        release_scope,
        decade,
        release_year,
        original_release_hits,
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
    """Apply pre-Spotify pre-slicing and safety cap.

    Playcount pre-slice: only when sort_mode='playcount', release_scope='all',
    and limit_results is a valid integer. Safety cap: fires at
    _MAX_ALBUM_CAP across all sort modes to protect Spotify API quotas and
    results rendering performance. Returns the (possibly reduced) dict.

    Both reductions order by descending play count and then by normalized key,
    so a tied play count does not let the input mapping's insertion order decide
    which albums are kept.
    """
    if sort_mode == "playcount" and limit_results != "all" and release_scope == "all":
        try:
            limit = int(limit_results)
            if len(filtered_albums) > limit:
                sorted_items = sorted(
                    filtered_albums.items(),
                    key=lambda kv: (-int(kv[1]["play_count"]), kv[0]),
                )
                filtered_albums = dict(sorted_items[:limit])
                logging.info(f"Pre-sliced filtered_albums to top {limit} by play_count")
        except ValueError:
            pass  # malformed limit_results handled by the post-process slice

    if len(filtered_albums) > _MAX_ALBUM_CAP:
        sorted_items = sorted(
            filtered_albums.items(),
            key=lambda kv: (-int(kv[1]["play_count"]), kv[0]),
        )
        filtered_albums = dict(sorted_items[:_MAX_ALBUM_CAP])
        prefix = "Playtime album cap" if sort_mode == "playtime" else "Album cap"
        logging.warning(
            f"{prefix} applied: capped {len(sorted_items)} albums "
            f"to top {_MAX_ALBUM_CAP} by play_count before Spotify fetch"
        )

    return filtered_albums


def _detect_enrichment_total_failure(job_id, results, filtered_albums):
    """Return True and set job error if no filtered album matched any provider.

    Only fires when results is empty but filtered_albums is non-empty.
    Reads job unmatched state to count 'no_spotify_match' entries -- the
    reason_code is unchanged (Task 5 only changed its reason text, "No
    match on Spotify or Deezer"), so this still fires only once both
    providers have had their turn on every album.
    """
    if not results and filtered_albums:
        job_ctx = get_job_context(job_id)
        unmatched = job_ctx.get("unmatched", {}) if job_ctx else {}
        spotify_no_match = sum(
            1
            for v in unmatched.values()
            if v.get("reason_code") == REASON_NO_SPOTIFY_MATCH
            or (not v.get("reason_code") and v.get("reason") == "No Spotify match")
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


async def _fetch_job_albums(job_id, username, year, min_plays, min_tracks):
    """Fetch Last.fm albums and finish upstream-error or empty jobs in place.

    None means this stage has already written terminal job state. A nonempty
    album mapping proceeds to Spotify; exceptions retain the outer classifier.
    """
    step_start_time = time.time()
    set_job_progress(
        job_id,
        progress=5,
        message="Fetching your data from Last.fm...",
        error=False,
        phase=None,
    )

    def _lastfm_progress(pages_done, total_pages):
        """Map page-fetching progress into the 5%-20% range."""
        pct = 5 + int(15 * pages_done / max(total_pages, 1))
        set_job_progress(
            job_id,
            progress=pct,
            message="Reading your Last.fm history...",
            phase={
                "key": "lastfm_fetch",
                "label": "Fetching scrobbles",
                "unit": "page",
                "current": pages_done,
                "total": total_pages,
            },
        )

    (
        filtered_albums,
        threshold_exclusions,
        fetch_metadata,
    ) = await fetch_top_albums_async(
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
        return None

    for unmatched_key, item in threshold_exclusions.items():
        add_job_unmatched(job_id, "|".join(unmatched_key), item)

    # Legitimate empty result: user has scrobbles but none pass filters
    if not filtered_albums:
        set_job_results(job_id, [])
        set_job_progress(
            job_id,
            progress=100,
            message="No albums found for the specified criteria.",
            error=False,
            phase=None,
        )
        return None
    return filtered_albums


async def _process_filtered_albums(
    job_id,
    filtered_albums,
    year,
    sort_mode,
    release_scope,
    decade,
    release_year,
    limit_results,
    overall_start_time,
):
    """Slice, enrich, and finalize a job's already-filtered albums.

    This is the tail of ``_fetch_and_process``: pre-slicing for the Spotify
    lookup, enrichment via ``process_albums``, post-slicing, storing the
    results, and handing the job off to the release-check worker. It is
    called by ``_fetch_and_process`` right after ``fetch_metadata``'s
    "Processing your albums..." progress update, and Batch 23's export
    task will be the second caller, invoking it after its own aggregation
    so both paths share the same "Done" progress and release-check
    hand-off instead of duplicating them.

    ``overall_start_time`` is passed in from the caller so the "Total time
    elapsed" log still measures from the start of the job (the start of
    ``_fetch_and_process``), not from this function's own start.

    Returns the results list on success, or ``[]`` when Spotify is
    unavailable or every album fails enrichment -- in both cases the job
    error/results state has already been recorded before returning.
    """
    filtered_albums = _apply_pre_slice(
        filtered_albums, sort_mode, limit_results, release_scope
    )

    set_job_progress(
        job_id,
        progress=20,
        message=f"Preparing {len(filtered_albums)} albums for Spotify lookup...",
        phase=None,
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

    if _detect_enrichment_total_failure(job_id, results, filtered_albums):
        return []

    set_job_progress(
        job_id,
        progress=80,
        message="Adding album art to your results...",
        phase=None,
    )

    set_job_progress(
        job_id,
        progress=85,
        message="Compiling your top album list...",
        phase=None,
    )

    set_job_progress(
        job_id,
        progress=90,
        message="Finalizing list...",
        phase=None,
    )

    results = _apply_post_slice(results, limit_results)

    overall_elapsed = time.time() - overall_start_time
    logging.info(f"Total time elapsed: {overall_elapsed:.1f}s")

    set_job_results(job_id, results)
    set_job_progress(
        job_id,
        progress=100,
        message=f"Done! Found {len(results)} albums matching your criteria.",
        error=False,
        phase=None,
    )
    # Hand the finished job to the MusicBrainz correction worker (Task 9)
    # so it can replace reissue dates with original ones while the results
    # page is open. Only here, on the happy path: the error paths below
    # set an empty results list, and there is nothing to correct in one.
    enqueue_release_check(job_id)
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
            phase=None,
        )

        filtered_albums = await _fetch_job_albums(
            job_id, username, year, min_plays, min_tracks
        )
        if filtered_albums is None:
            return []

        set_job_progress(
            job_id,
            progress=20,
            message="Processing your albums...",
            phase=None,
        )

        return await _process_filtered_albums(
            job_id,
            filtered_albums,
            year,
            sort_mode,
            release_scope,
            decade,
            release_year,
            limit_results,
            overall_start_time,
        )

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
                phase=None,
            )

        logging.exception(f"Error processing request for {username} in {year}")
        return []


def _report_album_failure(job_id, username, year):
    """Log the crash and publish this pipeline's terminal state.

    Called from inside the helper's ``except`` block, so ``logging.exception``
    still sees the active exception. Publishes the same ``internal_error``
    the heatmap entry point does: two entry points, one answer (F-SWE-5).
    Before this, the album backstop only logged, and a page polling the job
    waited on a job that would never finish.
    """
    logging.exception(f"Unhandled error in background task for {username}/{year}")
    set_job_error(job_id, "internal_error", username=username)


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
    """Run the album pipeline on this thread, in a loop the worker owns.

    The build-run-close-release protocol lives in
    ``worker.run_coroutine_in_new_loop``. What stays here is the reaction to
    a failed run: ``_report_album_failure`` logs it and publishes
    ``internal_error``. Upstream failures are classified deeper in, inside
    ``_fetch_and_process``, so this backstop only sees faults that are ours.
    """
    run_coroutine_in_new_loop(
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
        ),
        # Passed explicitly rather than left to the helper's own defaults: the tests
        # patch ``scrobblescope.orchestrator.release_job_slot``, and a default taken
        # from the helper's module would move that patch target without failing.
        make_loop=new_thread_event_loop,
        release_slot=release_job_slot,
        on_run_error=lambda _exc: _report_album_failure(job_id, username, year),
    )


# Phase submodules import this package back (``from scrobblescope import
# orchestrator``) to reach the dependencies above through a live attribute
# lookup rather than a frozen-at-import-time binding, which is what keeps
# them patchable at ``scrobblescope.orchestrator.<name>``. They must be
# imported last, after every name above is defined.
from scrobblescope.orchestrator._cache import (  # noqa: E402
    _lookup_cached_metadata,
    _lookup_cached_original_release,
    _persist_new_metadata,
)
from scrobblescope.orchestrator._deezer_fallback import (  # noqa: E402
    _run_deezer_fallback_phase,
)
from scrobblescope.orchestrator._details import (  # noqa: E402
    _run_spotify_batch_detail_phase,
)
from scrobblescope.orchestrator._results import (  # noqa: E402
    _build_results,
    _get_user_friendly_reason,
    _matches_release_criteria,
)
from scrobblescope.orchestrator._search import _run_spotify_search_phase  # noqa: E402

__all__ = [
    "_MAX_ALBUM_CAP",
    "_PLAYTIME_ALBUM_CAP",
    "_apply_post_slice",
    "_apply_pre_slice",
    "_batch_lookup_metadata",
    "_batch_lookup_original_release",
    "_batch_persist_metadata",
    "_build_results",
    "_classify_exception_to_error_code",
    "_cleanup_stale_metadata",
    "_detect_enrichment_total_failure",
    "_fetch_and_process",
    "_fetch_job_albums",
    "_fetch_spotify_misses",
    "_get_db_connection",
    "_get_user_friendly_reason",
    "_lookup_cached_metadata",
    "_lookup_cached_original_release",
    "_matches_release_criteria",
    "_persist_new_metadata",
    "_record_lastfm_stats",
    "_run_deezer_fallback_phase",
    "_run_spotify_batch_detail_phase",
    "_run_spotify_search_phase",
    "add_job_unmatched",
    "album_metadata_from_details",
    "background_task",
    "cleanup_expired_jobs",
    "create_optimized_session",
    "enqueue_release_check",
    "fetch_all_recent_tracks_async",
    "fetch_deezer_album",
    "fetch_spotify_access_token",
    "fetch_spotify_album_details_batch",
    "fetch_top_albums_async",
    "get_job_context",
    "process_albums",
    "release_job_slot",
    "search_deezer_album",
    "search_for_spotify_album_id",
    "set_job_error",
    "set_job_progress",
    "set_job_results",
    "set_job_stat",
]
