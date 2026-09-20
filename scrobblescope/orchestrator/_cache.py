"""The DB metadata cache lookup and persist steps of ``process_albums``.

Split out of ``scrobblescope/orchestrator.py`` (WP-0, Batch 22): these two
functions are ``process_albums``'s Phase 1 (DB Batch Lookup) and Phase 4 (DB
Batch Persist) blocks, extracted verbatim with the connection still owned and
closed by the caller. See ``scrobblescope/orchestrator/_search.py`` for why
``_batch_lookup_metadata``, ``_batch_persist_metadata``,
``_cleanup_stale_metadata`` and ``set_job_stat`` are read through the live
``orchestrator`` module reference rather than imported directly.
"""

import logging

from scrobblescope import orchestrator as _orchestrator


async def _lookup_cached_metadata(conn, job_id, album_keys):
    """DB Batch Lookup. Returns {} without raising if the DB read failed."""
    cached_metadata = {}
    if not conn:
        _orchestrator.set_job_stat(
            job_id,
            "db_cache_warning",
            "DB cache unavailable; using Spotify fallback.",
        )
        return cached_metadata

    try:
        cached_metadata = await _orchestrator._batch_lookup_metadata(conn, album_keys)
        _orchestrator.set_job_stat(job_id, "db_cache_lookup_hits", len(cached_metadata))
        logging.info(
            f"DB cache: {len(cached_metadata)} hits / {len(album_keys)} total albums"
        )
    except Exception as exc:
        logging.warning(f"DB lookup failed, proceeding without cache: {exc}")
        _orchestrator.set_job_stat(
            job_id, "db_cache_warning", "DB lookup failed; cache bypassed."
        )
        cached_metadata = {}
    # Opportunistic stale-row cleanup -- non-fatal, errors swallowed inside.
    await _orchestrator._cleanup_stale_metadata(conn)
    return cached_metadata


async def _lookup_cached_original_release(conn, keys):
    """Original-release correction lookup (Task 8, Batch 22 WP-3).

    Returns {} without raising if the DB is unavailable or the read failed --
    a missing correction only skips the display upgrade, it must never block
    a job the way a metadata-fetch failure would.
    """
    if not conn:
        return {}
    try:
        return await _orchestrator._batch_lookup_original_release(conn, keys)
    except Exception as exc:
        logging.warning(f"Original-release cache lookup failed (non-fatal): {exc}")
        return {}


async def _persist_new_metadata(conn, job_id, new_metadata_rows):
    """DB Batch Persist. Non-fatal on failure."""
    if not (conn and new_metadata_rows):
        return
    try:
        await _orchestrator._batch_persist_metadata(conn, new_metadata_rows)
        _orchestrator.set_job_stat(job_id, "db_cache_persisted", len(new_metadata_rows))
        logging.info(
            f"Persisted {len(new_metadata_rows)} new metadata rows to DB cache"
        )
    except Exception as exc:
        logging.warning(f"DB persist failed (non-fatal): {exc}")
        _orchestrator.set_job_stat(job_id, "db_cache_warning", "DB persist failed.")
