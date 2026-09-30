"""The Spotify search phase of album enrichment.

Split out of ``scrobblescope/orchestrator.py`` (WP-0, Batch 22): this module
owns the parallel-search step only. Every dependency that ``orchestrator``
also exposes to tests as a patchable attribute (``search_for_spotify_album_id``)
is read through the live
``orchestrator`` module reference below rather than imported directly, so a
``mock.patch("scrobblescope.orchestrator.X")`` in the existing test suite
still reaches the call site now that it lives in a different file.
"""

import asyncio
import logging
import time

from scrobblescope import jobs
from scrobblescope import orchestrator as _orchestrator
from scrobblescope.config import SPOTIFY_REQUESTS_PER_SECOND, SPOTIFY_SEARCH_CONCURRENCY
from scrobblescope.errors import ProviderError
from scrobblescope.lastfm import _cancel_and_drain


async def _run_spotify_search_phase(
    job_id,
    session,
    cache_misses,
    token,
    search_semaphore,
):
    """Parallel Spotify search for all cache misses.

    Reports progress in the 20-40% range. Returns (spotify_id_to_key,
    spotify_id_to_original_data, search_miss_keys, unanswered_keys). A search
    miss is not registered as unmatched here: Deezer gets one fallback
    attempt first (Batch 22 WP-1 Task 5), so the caller owns the final
    unmatched write once every provider has had its turn. A search Spotify
    could not answer (429, 5xx, timeout) is neither a hit nor a miss: its
    album goes into ``unanswered_keys``, the siblings carry on, and the
    caller sends the album to Deezer and records it as unavailable, not as
    "no match", if Deezer has nothing either.
    """
    logging.info(
        f"Starting parallel search for {len(cache_misses)} "
        f"Spotify albums (max {SPOTIFY_SEARCH_CONCURRENCY} "
        f"concurrent, {SPOTIFY_REQUESTS_PER_SECOND} req/s limit)"
    )
    search_start_time = time.time()

    async def search_with_semaphore(key, data):
        artist, album = key
        try:
            spotify_id = await _orchestrator.search_for_spotify_album_id(
                session,
                artist,
                album,
                token,
                semaphore=search_semaphore,
            )
        except ProviderError as exc:
            logging.warning(
                f"Spotify could not answer one album search ({exc.code}); "
                "it falls back to Deezer"
            )
            return key, None, data, False
        return key, spotify_id, data, True

    search_tasks = [
        asyncio.ensure_future(search_with_semaphore(key, data))
        for key, data in cache_misses.items()
    ]

    search_results = []
    searches_done = 0
    total_searches = len(search_tasks)
    try:
        for fut in asyncio.as_completed(search_tasks):
            result = await fut
            search_results.append(result)
            searches_done += 1
            jobs.report_phase(
                job_id,
                jobs.SPOTIFY_SEARCH,
                searches_done,
                total_searches,
                f"Searching Spotify: {searches_done}/{total_searches} albums...",
            )
    finally:
        # An unexpected exception from one search must not leave its siblings
        # running on a session that is about to close.
        await _cancel_and_drain(search_tasks)

    spotify_id_to_key = {}
    spotify_id_to_original_data = {}
    search_miss_keys = set()
    unanswered_keys = set()
    for key, spotify_id, data, answered in search_results:
        if not answered:
            unanswered_keys.add(key)
        elif spotify_id:
            spotify_id_to_key[spotify_id] = key
            spotify_id_to_original_data[spotify_id] = data
        else:
            search_miss_keys.add(key)

    search_duration = time.time() - search_start_time
    logging.info(
        f"Spotify search completed in {search_duration:.1f}s: "
        f"{len(spotify_id_to_key)}/{len(cache_misses)} "
        f"misses found on Spotify ({len(unanswered_keys)} unanswered)"
    )

    return (
        spotify_id_to_key,
        spotify_id_to_original_data,
        search_miss_keys,
        unanswered_keys,
    )
