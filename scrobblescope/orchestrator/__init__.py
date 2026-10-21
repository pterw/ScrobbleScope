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
The cache is the exception: its operations are patched at
``scrobblescope.cache.<name>``, because ``open_album_cache`` is the only door to it.
"""

import asyncio
import logging
import time

from scrobblescope import jobs
from scrobblescope.album_request import AlbumRequest
from scrobblescope.cache import open_album_cache
from scrobblescope.config import SPOTIFY_SEARCH_CONCURRENCY
from scrobblescope.deezer import fetch_deezer_album, search_deezer_album
from scrobblescope.errors import (
    SpotifyUnavailableError,
    classify_exception_to_error_code,
)
from scrobblescope.lastfm import fetch_scrobbles
from scrobblescope.plays import Window, aggregate_albums, select_albums
from scrobblescope.release_checks import enqueue_release_check
from scrobblescope.spotify import (
    album_metadata_from_details,
    fetch_spotify_access_token,
    fetch_spotify_album_details_batch,
    search_for_spotify_album_id,
    spotify_job_breaker,
)
from scrobblescope.utils import (
    cleanup_expired_cache,
    create_optimized_session,
    log_failure,
)
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


async def fetch_top_albums_async(
    username, year, min_plays=10, min_tracks=3, progress_cb=None
):
    """Read *username*'s scrobbles for *year* and select the albums that pass.

    Returns ``(selection, summary)``: an ``AlbumSelection`` (eligible albums,
    the capped threshold exclusions and the four aggregation counts) and the
    ``FetchSummary`` of the Last.fm read. A total Last.fm failure raises; it is
    never a return value. Threshold exclusions keep their report facts but never
    enter Spotify enrichment.

    Args:
        progress_cb: Optional ``Callable[[int, int, int], None]`` forwarded to
            ``fetch_scrobbles`` for per-page progress.
    """
    logging.debug(f"Start fetch_top_albums_async(year={year})")
    window = Window.year(year)
    fetch = await fetch_scrobbles(username, window, progress_cb=progress_cb)
    selection = select_albums(
        aggregate_albums(fetch.plays, window), min_plays, min_tracks, _MAX_ALBUM_CAP
    )
    return selection, fetch.summary


async def _fetch_spotify_misses(job_id, cache_misses, cache_hits):
    """Enrich cache misses via Spotify search + batch detail, then Deezer
    for whatever Spotify still could not enrich.

    Mutates *cache_hits* in place by promoting newly found entries.
    Returns the newly fetched metadata as
    ``{(artist_norm, album_norm): AlbumMetadata}`` for DB persistence.
    Spotify being down degrades, per album: a token that cannot be had, or
    a search Spotify could not answer, sends that album to Deezer, and an
    album Deezer cannot match either is recorded as unavailable, never as
    "no match". Raises SpotifyUnavailableError only when Spotify gave
    nothing for every miss (no token, or every miss either a search it did not
    answer or a matched album whose details it did not answer), nothing was
    already cached before this call, and Deezer could not enrich a single
    album either -- a run that finds at least one match is a valid, if
    partial, outcome, not a failure. A miss whose search Spotify answered
    with "no match" is an answer, so it keeps the run from failing here, and a
    run where both providers answered "no match" for every album succeeds
    with no albums and its unmatched list (owner ruling 2026-09-30).

    The Spotify calls run under ``spotify_job_breaker``: once one of them
    meets a Retry-After above the cap, the rest of this job's Spotify calls
    are skipped and those albums go to Deezer as unanswered.
    """
    if not cache_misses:
        return {}

    had_cache_hits = bool(cache_hits)
    new_metadata = {}
    token = await fetch_spotify_access_token()
    still_missing = cache_misses
    unanswered_keys = set(cache_misses)
    detail_unavailable_keys = set()

    if not token:
        logging.error(
            "Spotify token fetch failed. Falling back to Deezer for all misses."
        )
        jobs.record_stat(
            job_id,
            "partial_data_warning",
            "Spotify is temporarily unavailable; checking Deezer for album details.",
        )
        jobs.record_partial_source(job_id, "provider")
    else:
        with spotify_job_breaker():
            async with create_optimized_session() as session:
                search_semaphore = asyncio.Semaphore(SPOTIFY_SEARCH_CONCURRENCY)
                (
                    spotify_id_to_key,
                    spotify_id_to_original_data,
                    _search_miss_keys,
                    unanswered_keys,
                ) = await _run_spotify_search_phase(
                    job_id, session, cache_misses, token, search_semaphore
                )
                if unanswered_keys:
                    jobs.record_stat(
                        job_id,
                        "partial_data_warning",
                        "Spotify is temporarily unavailable for some albums; "
                        "checking Deezer for their details.",
                    )
                    jobs.record_partial_source(job_id, "provider")
                valid_spotify_ids = list(spotify_id_to_original_data.keys())
                if valid_spotify_ids:
                    new_metadata = await _run_spotify_batch_detail_phase(
                        job_id,
                        session,
                        valid_spotify_ids,
                        token,
                        spotify_id_to_key,
                        spotify_id_to_original_data,
                        cache_hits,
                        detail_unavailable_keys=detail_unavailable_keys,
                    )
                    if detail_unavailable_keys and not unanswered_keys:
                        jobs.record_stat(
                            job_id,
                            "partial_data_warning",
                            "Spotify is temporarily unavailable for some albums; "
                            "checking Deezer for their details.",
                        )
                        jobs.record_partial_source(job_id, "provider")
        still_missing = {
            key: data for key, data in cache_misses.items() if key not in cache_hits
        }

    if still_missing:
        async with create_optimized_session() as session:
            deezer_metadata = await _run_deezer_fallback_phase(
                job_id,
                session,
                still_missing,
                cache_hits,
                spotify_unavailable_keys=unanswered_keys,
                spotify_detail_unavailable_keys=detail_unavailable_keys,
            )
        new_metadata.update(deezer_metadata)

    # Spotify "gave nothing" for a miss when its search went unanswered or,
    # having matched it, its details did. Both are outages, not answers.
    spotify_gave_nothing = set(cache_misses) <= (
        unanswered_keys | detail_unavailable_keys
    )
    if spotify_gave_nothing and not had_cache_hits and not new_metadata:
        if not token:
            raise SpotifyUnavailableError(
                "Spotify token fetch failed and Deezer could not enrich any album."
            )
        if detail_unavailable_keys:
            raise SpotifyUnavailableError(
                "Spotify could not answer a search or a details call for any "
                "album and Deezer could not enrich any album."
            )
        raise SpotifyUnavailableError(
            "Spotify answered no search and Deezer could not enrich any album."
        )

    return new_metadata


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

    async with open_album_cache() as album_cache:
        # =============================================================
        # Phase 1: DB Batch Lookup
        # =============================================================
        jobs.record_stat(job_id, "db_cache_enabled", album_cache.enabled)
        cached_metadata = await _lookup_cached_metadata(
            album_cache, job_id, list(filtered_albums.keys())
        )

        # =============================================================
        # Phase 2: Partition into cache hits and misses
        # =============================================================
        cache_hits = {}  # key -> {"cached": AlbumMetadata, "original": original_data}
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
        jobs.record_stat(job_id, "cache_hits", db_hit_count)
        logging.info(
            f"Cache partition: {db_hit_count} hits, {len(cache_misses)} misses"
        )

        # =============================================================
        # Phase 3: Spotify fetch for misses only
        # =============================================================
        new_metadata = await _fetch_spotify_misses(job_id, cache_misses, cache_hits)

        # =============================================================
        # Phase 4: DB Batch Persist
        # =============================================================
        await _persist_new_metadata(album_cache, job_id, new_metadata)

        # =============================================================
        # Phase 4b: Original-release correction lookup (Task 8, Batch 22
        # WP-3). Applies findings already in original_release_cache --
        # the live MusicBrainz worker (Task 9) is what populates new ones.
        # =============================================================
        original_release_hits = await album_cache.lookup_original_releases(
            list(cache_hits.keys())
        )

    # =================================================================
    # Phase 5: Build results from unified cache_hits
    # =================================================================
    total_matched = len(cache_hits)
    jobs.record_stat(job_id, "spotify_matched", total_matched)
    jobs.record_stat(
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


def _record_fetch_stats(job_id, summary):
    """Write the Last.fm-only job stats: pages fetched, and the page-loss notice.

    They stay out of ``finish_album_job`` because an export has no pages.
    """
    jobs.record_stat(job_id, "pages_fetched", summary.pages_received)
    if summary.partial:
        jobs.record_stat(
            job_id,
            "partial_data_warning",
            f"Note: {summary.pages_dropped} of {summary.pages_expected} Last.fm "
            f"pages failed to load ({summary.data_loss_pct}% data loss). "
            "Results may be incomplete.",
        )
        jobs.record_partial_source(job_id, "lastfm")
        jobs.record_stat(job_id, "pages_dropped", summary.pages_dropped)


def _publish_selection(job_id, selection):
    """Record a selection's four stats and one unmatched entry per exclusion."""
    for key, value in selection.stats().items():
        jobs.record_stat(job_id, key, value)
    for key, item in selection.exclusions.items():
        jobs.record_unmatched(job_id, "|".join(key), item)


async def finish_album_job(job_id, selection, album, *, overall_start_time):
    """Publish an album selection to its job and carry the job to its end.

    The step every album source shares once it holds an ``AlbumSelection``: a
    Last.fm job calls it after ``fetch_top_albums_async``; Batch 23's export job
    calls it after ``plays.select_albums``. It records the selection's stats and
    one unmatched entry per exclusion, in that order, then either ends the job
    on the spot -- nothing is eligible, so ``jobs.succeed`` with an empty result
    and the "no albums" message, and no hand-off to the correction worker -- or
    runs ``_process_filtered_albums`` on the eligible albums.

    ``album`` is the job's validated ``AlbumRequest``: it supplies the year,
    sort mode, release scope, decade, release year, result limit and
    ``include_unmatched`` the enrichment tail needs. Its ``username`` is
    ``None`` for an export, and its minimums were applied by ``select_albums``
    before this call, so they are not read here.

    ``overall_start_time`` is the job's start, so "Total time elapsed" measures
    the whole job. Returns the results list, ``[]`` when the job ended empty or
    failed.
    """
    _publish_selection(job_id, selection)
    if not selection.eligible:
        jobs.succeed(job_id, [], "No albums found for the specified criteria.")
        return []
    jobs.advance(job_id, 20, "Processing your albums...")
    return await _process_filtered_albums(
        job_id,
        selection.eligible,
        album.year,
        album.sort_mode,
        album.release_scope,
        album.decade,
        album.release_year,
        album.limit_results,
        overall_start_time,
        include_unmatched=album.include_unmatched,
    )


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
    include_unmatched=False,
):
    """Slice, enrich, and finalize a job's already-filtered albums.

    This is the tail of ``_fetch_and_process``: pre-slicing for the Spotify
    lookup, enrichment via ``process_albums``, post-slicing, storing the
    results, and handing the job off to the release-check worker. It is
    called through ``finish_album_job``, which Batch 23's export task also
    calls, so both paths share the same "Done" progress and release-check
    hand-off.

    ``overall_start_time`` is passed in from the caller so the "Total time
    elapsed" log still measures from the start of the job (the start of
    ``_fetch_and_process``), not from this function's own start.

    ``include_unmatched`` is the listener's "Include" choice (the unmatched-albums control).
    When on, the job's ``no_spotify_match`` and
    ``provider_unavailable`` albums are merged into the results after
    ``process_albums`` and before the post-slice, so ``limit_results`` applies
    to the combined list (see ``_results.merge_unmatched_rows``). It adds no
    provider call. When off the results list is used as ``process_albums``
    returned it.

    Returns the results list on success (empty when no album could be
    enriched: the run still succeeds, with its unmatched list), or ``[]``
    when Spotify is unavailable -- in which case the job error state has
    already been recorded before returning.
    """
    filtered_albums = _apply_pre_slice(
        filtered_albums, sort_mode, limit_results, release_scope
    )

    jobs.advance(
        job_id,
        20,
        f"Preparing {len(filtered_albums)} albums for Spotify lookup...",
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
        jobs.fail(job_id, "spotify_unavailable")
        return []
    step_elapsed = time.time() - step_start_time
    logging.info(f"Time elapsed (Spotify album processing): {step_elapsed:.1f}s")

    jobs.advance(job_id, 80, "Adding album art to your results...")
    jobs.advance(job_id, 85, "Compiling your top album list...")
    jobs.advance(job_id, 90, "Finalizing list...")

    if include_unmatched:
        results = merge_unmatched_rows(results, jobs.unmatched(job_id))

    results = _apply_post_slice(results, limit_results)

    overall_elapsed = time.time() - overall_start_time
    logging.info(f"Total time elapsed: {overall_elapsed:.1f}s")

    jobs.succeed(
        job_id,
        results,
        f"Done! Found {len(results)} albums matching your criteria.",
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
    include_unmatched=False,
):
    """Fetch and process albums in the background for a single job.

    ``include_unmatched`` is passed to ``_process_filtered_albums``, which
    lists the albums no provider could match alongside the matched ones.

    An exception that escapes the pipeline is classified by type
    (``errors.classify_exception_to_error_code``): a typed provider failure
    publishes its own code, and anything else is our bug and publishes
    ``internal_error`` -- the answer the heatmap gives too.
    """
    try:
        overall_start_time = time.time()
        cleanup_expired_cache()
        jobs.expire_stale()

        jobs.start(job_id, "Initializing...")
        jobs.advance(job_id, 5, "Fetching your data from Last.fm...")

        def _lastfm_progress(pages_done, total_pages, _pages_received):
            """Report page-fetching progress inside the album fetch band."""
            jobs.report_phase(
                job_id,
                jobs.ALBUM_LASTFM_FETCH,
                pages_done,
                total_pages,
                "Reading your Last.fm history...",
            )

        step_start_time = time.time()
        selection, summary = await fetch_top_albums_async(
            username,
            year,
            min_plays=min_plays,
            min_tracks=min_tracks,
            progress_cb=_lastfm_progress,
        )
        logging.info(
            f"Time elapsed (Last.fm data fetch): {time.time() - step_start_time:.1f}s"
        )
        _record_fetch_stats(job_id, summary)

        album = AlbumRequest(
            username=username,
            year=year,
            sort_mode=sort_mode,
            include_unmatched=include_unmatched,
            release_scope=release_scope,
            decade=decade,
            release_year=release_year,
            min_plays=min_plays,
            min_tracks=min_tracks,
            limit_results=limit_results,
        )
        return await finish_album_job(
            job_id, selection, album, overall_start_time=overall_start_time
        )

    except Exception as exc:  # noqa: BLE001 -- logged by log_failure
        # Classified by type; anything unrecognised is our bug and is
        # published as internal_error, never with the exception's text.
        error_code = classify_exception_to_error_code(exc) or "internal_error"
        jobs.fail(job_id, error_code, username=username)

        log_failure(f"Error processing request for job {job_id} in {year}")
        return []


def _report_album_failure(job_id, username, year):
    """Log the crash and publish this pipeline's terminal state.

    Called from inside the helper's ``except`` block, so ``log_failure``
    still sees the active exception. This worker-level backstop always
    publishes ``internal_error`` and does not classify; the pipelines
    classify by exception type first (``_fetch_and_process`` for albums,
    ``_report_heatmap_failure`` for the heatmap), so only an exception that
    got past them lands here (F-SWE-5). Before this, the album backstop
    only logged, and a page polling the job waited on a job that would never
    finish.
    """
    log_failure(f"Unhandled error in background task for job {job_id}, year {year}")
    jobs.fail(job_id, "internal_error", username=username)


def _album_request_for(job_id):
    """Return the job's ``AlbumRequest`` read from its record, or None.

    None means the run cannot start: the job expired between admission and the
    thread's first line (nothing to publish to), or its record is not a usable
    request (published as ``internal_error`` so a polling page stops waiting).
    """
    params = jobs.params(job_id)
    if params is None:
        logging.warning("Album job %s was gone before its thread started.", job_id)
        return None
    try:
        return AlbumRequest.from_params(params)
    except TypeError:
        log_failure("Album job record is not a usable request")
        jobs.fail(job_id, "internal_error")
        return None


def background_task(job_id):
    """Run the album pipeline on this thread, in a loop the worker owns.

    The parameters come from the job record (``jobs.params``), not from
    arguments: admission stored them there. A job that is gone or unreadable
    runs nothing, and the slot the route acquired is still released.

    The build-run-close-release protocol lives in
    ``worker.run_coroutine_in_new_loop``. What stays here is the reaction to
    a failed run: ``_report_album_failure`` logs it and publishes
    ``internal_error``. Upstream failures are classified deeper in, inside
    ``_fetch_and_process``, so this backstop only sees faults that are ours.

    ``include_unmatched`` (default off) keeps the albums Spotify and Deezer
    could not match in the results, ranked by play count.
    """
    album = _album_request_for(job_id)
    if album is None:
        release_job_slot()
        return
    run_coroutine_in_new_loop(
        _fetch_and_process(
            job_id,
            album.username,
            album.year,
            album.sort_mode,
            album.release_scope,
            album.decade,
            album.release_year,
            album.min_plays,
            album.min_tracks,
            album.limit_results,
            include_unmatched=album.include_unmatched,
        ),
        # Passed explicitly rather than left to the helper's own defaults: the tests
        # patch ``scrobblescope.orchestrator.release_job_slot``, and a default taken
        # from the helper's module would move that patch target without failing.
        make_loop=new_thread_event_loop,
        release_slot=release_job_slot,
        on_run_error=lambda _exc: _report_album_failure(
            job_id, album.username, album.year
        ),
    )


# Phase submodules import this package back (``from scrobblescope import
# orchestrator``) to reach the dependencies above through a live attribute
# lookup rather than a frozen-at-import-time binding, which is what keeps
# them patchable at ``scrobblescope.orchestrator.<name>``. They must be
# imported last, after every name above is defined.
from scrobblescope.orchestrator._cache import (  # noqa: E402
    _lookup_cached_metadata,
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
    merge_unmatched_rows,
)
from scrobblescope.orchestrator._search import _run_spotify_search_phase  # noqa: E402

__all__ = [
    "_MAX_ALBUM_CAP",
    "_PLAYTIME_ALBUM_CAP",
    "_apply_post_slice",
    "_apply_pre_slice",
    "_build_results",
    "_fetch_and_process",
    "_fetch_spotify_misses",
    "_get_user_friendly_reason",
    "_lookup_cached_metadata",
    "_persist_new_metadata",
    "_run_deezer_fallback_phase",
    "_run_spotify_batch_detail_phase",
    "_run_spotify_search_phase",
    "album_metadata_from_details",
    "background_task",
    "create_optimized_session",
    "enqueue_release_check",
    "fetch_deezer_album",
    "fetch_scrobbles",
    "fetch_spotify_access_token",
    "fetch_spotify_album_details_batch",
    "fetch_top_albums_async",
    "finish_album_job",
    "merge_unmatched_rows",
    "open_album_cache",
    "process_albums",
    "release_job_slot",
    "search_deezer_album",
    "search_for_spotify_album_id",
    "spotify_job_breaker",
]
