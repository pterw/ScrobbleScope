"""The DB metadata cache lookup and persist steps of ``process_albums``.

Split out of ``scrobblescope/orchestrator.py`` (WP-0, Batch 22): these two
functions are ``process_albums``'s Phase 1 (DB Batch Lookup) and Phase 4 (DB
Batch Persist) blocks, extracted verbatim with the connection still owned and
closed by the caller. See ``scrobblescope/orchestrator/_search.py`` for why
``batch_lookup_metadata``, ``batch_persist_metadata``,
and ``cleanup_stale_metadata`` are read through the live ``orchestrator``
module reference rather than imported directly.
"""

import logging

from scrobblescope import jobs
from scrobblescope import orchestrator as _orchestrator
from scrobblescope.cache import (
    SCHEMA_OUT_OF_DATE_REMEDIATION as _SCHEMA_OUT_OF_DATE_REMEDIATION,
)
from scrobblescope.cache import (
    schema_is_out_of_date as _schema_is_out_of_date,
)
from scrobblescope.utils import log_failure


async def _lookup_cached_metadata(conn, job_id, album_keys):
    """DB Batch Lookup. Returns {key: AlbumMetadata}; {} without raising if the DB
    read failed."""
    cached_metadata = {}
    if not conn:
        jobs.record_stat(
            job_id,
            "db_cache_warning",
            "DB cache unavailable; using Spotify fallback.",
        )
        return cached_metadata

    try:
        cached_metadata = await _orchestrator.batch_lookup_metadata(conn, album_keys)
        jobs.record_stat(job_id, "db_cache_lookup_hits", len(cached_metadata))
        logging.info(
            f"DB cache: {len(cached_metadata)} hits / {len(album_keys)} total albums"
        )
    # Fail open: a failed cache read makes every album a miss, not a failed job.
    except Exception as exc:  # noqa: BLE001
        if _schema_is_out_of_date(exc):
            log_failure(
                "DB lookup failed, proceeding without cache "
                f"({_SCHEMA_OUT_OF_DATE_REMEDIATION})",
                logging.WARNING,
            )
        else:
            log_failure("DB lookup failed, proceeding without cache", logging.WARNING)
        jobs.record_stat(
            job_id, "db_cache_warning", "DB lookup failed; cache bypassed."
        )
        cached_metadata = {}
    # Opportunistic stale-row cleanup -- non-fatal, errors swallowed inside.
    await _orchestrator.cleanup_stale_metadata(conn)
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
        return await _orchestrator.batch_lookup_original_release(conn, keys)
    # Fail open: a missing correction only skips the display upgrade.
    except Exception:  # noqa: BLE001
        log_failure("Original-release cache lookup failed (non-fatal)", logging.WARNING)
        return {}


async def _persist_new_metadata(conn, job_id, new_metadata):
    """DB Batch Persist. Non-fatal on failure.

    *new_metadata* maps (artist_norm, album_norm) to the ``AlbumMetadata`` the
    providers returned this job.
    """
    if not (conn and new_metadata):
        return
    try:
        await _orchestrator.batch_persist_metadata(conn, new_metadata)
        jobs.record_stat(job_id, "db_cache_persisted", len(new_metadata))
        logging.info(f"Persisted {len(new_metadata)} new metadata rows to DB cache")
    # Fail open: a failed persist costs the next job a lookup, not this one.
    except Exception:  # noqa: BLE001
        log_failure("DB persist failed (non-fatal)", logging.WARNING)
        jobs.record_stat(job_id, "db_cache_warning", "DB persist failed.")
