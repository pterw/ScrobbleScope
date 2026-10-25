"""The job-facing side of the DB metadata cache in ``process_albums``.

``scrobblescope.cache.AlbumCache`` owns the connection and decides what a
database error means: it never raises into a job and says what failed through
``lookup_failed`` and ``persist_failed``. These two functions are Phase 1 (DB
Batch Lookup) and Phase 4 (DB Batch Persist) of ``process_albums`` as far as
the job is concerned: they turn the cache's answers into the job's stats and
log lines. The original-release lookup (Phase 4b) needs no job message and
calls ``AlbumCache.lookup_original_releases`` directly.
"""

import asyncio
import logging

from scrobblescope import jobs
from scrobblescope import orchestrator as _orchestrator
from scrobblescope.config import SPOTIFY_BATCH_CONCURRENCY
from scrobblescope.enrichment import MATCH_FITS, MATCH_UNSTAMPED

# Spotify's Get Several Albums takes at most 20 IDs; equal to ``batch_size`` in
# ``_details.py``, which this module does not import from.
_STAMP_BATCH_SIZE = 20


async def _lookup_cached_metadata(album_cache, job_id, album_keys):
    """DB Batch Lookup. Returns ``{key: AlbumMetadata}``, ``{}`` if the cache is
    off or the read failed, and records which on the job."""
    cached_metadata = await album_cache.lookup(album_keys)
    if not album_cache.enabled:
        jobs.record_stat(
            job_id,
            "db_cache_warning",
            "DB cache unavailable; using Spotify fallback.",
        )
    elif album_cache.lookup_failed:
        jobs.record_stat(
            job_id, "db_cache_warning", "DB lookup failed; cache bypassed."
        )
    else:
        cached_metadata = await _stamp_unstamped_spotify_rows(
            album_cache, job_id, cached_metadata
        )
        jobs.record_stat(job_id, "db_cache_lookup_hits", len(cached_metadata))
        logging.info(
            f"DB cache: {len(cached_metadata)} hits / {len(album_keys)} total albums"
        )
    return cached_metadata


async def _fetch_stamping_details(ids, token):
    """Details for *ids* by cached ID, in chunks of ``_STAMP_BATCH_SIZE``.

    Returns ``(details, unanswered)``. Never searches. Runs under the job's
    Spotify breaker, so a tripped breaker answers every ID as unanswered.
    """
    chunks = [
        ids[i : i + _STAMP_BATCH_SIZE] for i in range(0, len(ids), _STAMP_BATCH_SIZE)
    ]
    semaphore = asyncio.Semaphore(SPOTIFY_BATCH_CONCURRENCY)
    with _orchestrator.spotify_job_breaker():
        async with _orchestrator.create_optimized_session() as session:
            results = await asyncio.gather(
                *(
                    _orchestrator.fetch_spotify_album_details_batch(
                        session, chunk, token, semaphore=semaphore
                    )
                    for chunk in chunks
                )
            )
    details = {}
    unanswered = set()
    for result in results:
        details.update(result)
        unanswered.update(getattr(result, "unanswered", ()))
    return details, unanswered


async def _stamp_unstamped_spotify_rows(album_cache, job_id, cached_metadata):
    """Give each old Spotify row (no stored names) its names, by its cached ID.

    Returns *cached_metadata* with every ``MATCH_UNSTAMPED`` entry replaced by
    its stamped row when Spotify's details fit the key (and persisted), or
    removed when they do not or Spotify has no such album (a miss, searched
    again). Fails open: with no token, a tripped breaker, an unanswered ID or a
    failed persist the unstamped entry stays for this job and nothing is
    dropped. A job with no unstamped rows makes no Spotify call.
    """
    unstamped = {
        key: metadata
        for key, metadata in cached_metadata.items()
        if metadata.match_for(key) == MATCH_UNSTAMPED
    }
    if not unstamped:
        return cached_metadata

    token = await _orchestrator.fetch_spotify_access_token()
    if not token:
        logging.warning(
            f"Cache stamping skipped: no Spotify token; kept {len(unstamped)} rows"
        )
        return cached_metadata

    ids = list(dict.fromkeys(metadata.album_id for metadata in unstamped.values()))
    details, unanswered = await _fetch_stamping_details(ids, token)

    stamped = {}
    dropped = set()
    kept = 0
    for key, metadata in unstamped.items():
        if metadata.album_id in unanswered:
            kept += 1
            continue
        album_details = details.get(metadata.album_id)
        candidate = (
            _orchestrator.album_metadata_from_details(
                metadata.album_id, album_details, key
            )
            if album_details
            else None
        )
        if candidate is not None and candidate.match_for(key) == MATCH_FITS:
            stamped[key] = candidate
        else:
            dropped.add(key)

    if stamped:
        await album_cache.persist(stamped)
        if album_cache.persist_failed:
            kept += len(stamped)
            stamped = {}

    logging.info(
        f"Cache stamping: kept {kept}, stamped {len(stamped)}, "
        f"dropped {len(dropped)}, unanswered {len(unanswered)} of "
        f"{len(unstamped)} unstamped rows"
    )
    result = {k: v for k, v in cached_metadata.items() if k not in dropped}
    result.update(stamped)
    return result


async def _persist_new_metadata(album_cache, job_id, new_metadata):
    """DB Batch Persist. Non-fatal on failure; records the outcome on the job."""
    if not (album_cache.enabled and new_metadata):
        return
    await album_cache.persist(new_metadata)
    if album_cache.persist_failed:
        jobs.record_stat(job_id, "db_cache_warning", "DB persist failed.")
    else:
        jobs.record_stat(job_id, "db_cache_persisted", len(new_metadata))
        logging.info(f"Persisted {len(new_metadata)} new metadata rows to DB cache")
