"""The job-facing side of the DB metadata cache in ``process_albums``.

``scrobblescope.cache.AlbumCache`` owns the connection and decides what a
database error means: it never raises into a job and says what failed through
``lookup_failed`` and ``persist_failed``. These two functions are Phase 1 (DB
Batch Lookup) and Phase 4 (DB Batch Persist) of ``process_albums`` as far as
the job is concerned: they turn the cache's answers into the job's stats and
log lines. The original-release lookup (Phase 4b) needs no job message and
calls ``AlbumCache.lookup_original_releases`` directly.
"""

import logging

from scrobblescope import jobs


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
        jobs.record_stat(job_id, "db_cache_lookup_hits", len(cached_metadata))
        logging.info(
            f"DB cache: {len(cached_metadata)} hits / {len(album_keys)} total albums"
        )
    return cached_metadata


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
