"""The Spotify batch-detail phase of album enrichment.

Split out of ``scrobblescope/orchestrator.py`` (WP-0, Batch 22). See
``scrobblescope/orchestrator/_search.py`` for why cross-cutting dependencies
(``fetch_spotify_album_details_batch``, ``set_job_progress``) are read
through the live ``orchestrator`` module reference rather than imported
directly.
"""

import asyncio
import logging
import time
from math import ceil

from scrobblescope import orchestrator as _orchestrator
from scrobblescope.config import SPOTIFY_BATCH_CONCURRENCY
from scrobblescope.domain import normalize_track_name


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
    fallback_reported = False

    def report_fallback(status):
        # Every batch in a job meets the same removed endpoint, so one line
        # says it; a line per batch would bury the rest of the job's log.
        nonlocal fallback_reported
        if fallback_reported:
            return
        fallback_reported = True
        logging.warning(
            f"Spotify Get Several Albums answered {status}; job {job_id} is "
            "fetching album details with single-album calls (F-B21-59)."
        )

    async def fetch_batch_with_semaphore(batch_ids):
        return await _orchestrator.fetch_spotify_album_details_batch(
            session,
            batch_ids,
            token,
            semaphore=batch_semaphore,
            on_fallback=report_fallback,
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
        _orchestrator.set_job_progress(
            job_id,
            progress=pct,
            message=(
                f"Enriched {enriched_so_far}/"
                f"{len(valid_spotify_ids)} albums from Spotify..."
            ),
            phase={
                "key": "spotify_details",
                "label": "Fetching Spotify details",
                "unit": "batch",
                "current": batches_done,
                "total": num_batches,
            },
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
