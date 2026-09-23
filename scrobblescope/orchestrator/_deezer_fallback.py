"""The Deezer fallback phase of album enrichment (Batch 22 WP-1 Task 5).

Runs after Spotify search and batch-detail: one pass over whatever those
two phases could not enrich (a search miss, or a detail-fetch failure).
See ``scrobblescope/orchestrator/_search.py`` for why cross-cutting
dependencies are read through the live ``orchestrator`` module reference
rather than imported directly.
"""

import asyncio
import logging
import time

from scrobblescope import orchestrator as _orchestrator
from scrobblescope.domain import normalize_name
from scrobblescope.unmatched import REASON_NO_SPOTIFY_MATCH


async def _run_deezer_fallback_phase(job_id, session, misses, cache_hits):
    """Deezer fallback pass over albums Spotify could not enrich.

    *misses* is a dict keyed by (artist_norm, album_norm) tuples, mapping to
    each album's original data -- the same shape ``cache_misses`` already
    uses. Reports progress in the 60-75% range. Promotes matched albums
    into *cache_hits* (mutated in place) and registers the final unmatched
    entry for anything neither provider could enrich, since this is the
    last phase in the chain. Returns new_metadata_rows for the newly
    matched Deezer albums.
    """
    if not misses:
        return []

    logging.info(
        f"Starting Deezer fallback for {len(misses)} albums Spotify could not enrich"
    )
    fallback_start_time = time.time()

    async def enrich_one(key, data):
        artist, album = key
        album_id = await _orchestrator.search_deezer_album(session, artist, album)
        if not album_id:
            return key, data, None
        metadata = await _orchestrator.fetch_deezer_album(session, album_id)
        return key, data, metadata

    tasks = [enrich_one(key, data) for key, data in misses.items()]

    new_metadata_rows = []
    matched_count = 0
    done = 0
    total = len(tasks)
    for fut in asyncio.as_completed(tasks):
        key, data, metadata = await fut
        done += 1
        pct = 60 + int(15 * done / max(total, 1))
        _orchestrator.set_job_progress(
            job_id,
            progress=pct,
            message=f"Checking Deezer: {done}/{total} albums...",
            phase={
                "key": "deezer_fallback",
                "label": "Checking Deezer",
                "unit": "album",
                "current": done,
                "total": total,
            },
        )

        if metadata is not None:
            matched_count += 1
            cache_hits[key] = {
                "cached": {
                    "spotify_id": None,
                    "release_date": metadata.release_date,
                    "album_image_url": metadata.image_url,
                    "track_durations": metadata.track_durations,
                    "provider": metadata.provider,
                    "provider_album_id": metadata.album_id,
                    "provider_url": metadata.url,
                },
                "original": data,
            }
            new_metadata_rows.append(metadata.as_cache_row(key[0], key[1]))
        else:
            original_artist = data["original_artist"]
            original_album = data["original_album"]
            unmatched_key = "|".join(normalize_name(original_artist, original_album))
            _orchestrator.add_job_unmatched(
                job_id,
                unmatched_key,
                {
                    "artist": original_artist,
                    "album": original_album,
                    "reason": "No match on Spotify or Deezer",
                    "reason_code": REASON_NO_SPOTIFY_MATCH,
                    "album_image": None,
                    "spotify_id": None,
                    "play_count": data.get("play_count"),
                },
            )

    fallback_duration = time.time() - fallback_start_time
    logging.info(
        f"Deezer fallback completed in {fallback_duration:.1f}s: "
        f"{matched_count}/{total} misses found on Deezer"
    )
    return new_metadata_rows
