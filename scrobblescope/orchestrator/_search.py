"""The Spotify search phase of album enrichment.

Split out of ``scrobblescope/orchestrator.py`` (WP-0, Batch 22): this module
owns the parallel-search step only. Every dependency that ``orchestrator``
also exposes to tests as a patchable attribute (``search_for_spotify_album_id``,
``set_job_progress``, ``add_job_unmatched``) is read through the live
``orchestrator`` module reference below rather than imported directly, so a
``mock.patch("scrobblescope.orchestrator.X")`` in the existing test suite
still reaches the call site now that it lives in a different file.
"""

import asyncio
import logging
import time

from scrobblescope import orchestrator as _orchestrator
from scrobblescope.config import SPOTIFY_REQUESTS_PER_SECOND, SPOTIFY_SEARCH_CONCURRENCY


async def _run_spotify_search_phase(
    job_id,
    session,
    cache_misses,
    token,
    search_semaphore,
):
    """Parallel Spotify search for all cache misses.

    Reports progress in the 20-40% range. Returns (spotify_id_to_key,
    spotify_id_to_original_data, search_miss_keys). A search miss is not
    registered as unmatched here: Deezer gets one fallback attempt first
    (Batch 22 WP-1 Task 5), so the caller owns the final unmatched write
    once every provider has had its turn.
    """
    logging.info(
        f"Starting parallel search for {len(cache_misses)} "
        f"Spotify albums (max {SPOTIFY_SEARCH_CONCURRENCY} "
        f"concurrent, {SPOTIFY_REQUESTS_PER_SECOND} req/s limit)"
    )
    search_start_time = time.time()

    async def search_with_semaphore(key, data):
        artist, album = key
        spotify_id = await _orchestrator.search_for_spotify_album_id(
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
        _orchestrator.set_job_progress(
            job_id,
            progress=pct,
            message=(f"Searching Spotify: {searches_done}/{total_searches} albums..."),
            phase={
                "key": "spotify_search",
                "label": "Searching Spotify",
                "unit": "album",
                "current": searches_done,
                "total": total_searches,
            },
        )

    spotify_id_to_key = {}
    spotify_id_to_original_data = {}
    search_miss_keys = set()
    for key, spotify_id, data in search_results:
        if spotify_id:
            spotify_id_to_key[spotify_id] = key
            spotify_id_to_original_data[spotify_id] = data
        else:
            search_miss_keys.add(key)

    search_duration = time.time() - search_start_time
    logging.info(
        f"Spotify search completed in {search_duration:.1f}s: "
        f"{len(spotify_id_to_key)}/{len(cache_misses)} "
        f"misses found on Spotify"
    )

    return spotify_id_to_key, spotify_id_to_original_data, search_miss_keys
