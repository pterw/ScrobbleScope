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

from scrobblescope import jobs
from scrobblescope import orchestrator as _orchestrator
from scrobblescope.domain import normalize_name
from scrobblescope.errors import ProviderError
from scrobblescope.unmatched import (
    REASON_NO_SPOTIFY_MATCH,
    REASON_PROVIDER_UNAVAILABLE,
)
from scrobblescope.utils import cancel_and_drain

#: Row text for an album neither provider matched, by what each provider said.
#: One line per distinct combination, so the row never claims a provider
#: "had no match" when it was not asked or could not answer.
REASON_SPOTIFY_SEARCH_DOWN_DEEZER_NO_MATCH = (
    "Spotify was unavailable and Deezer had no match"
)
REASON_SPOTIFY_SEARCH_DOWN_DEEZER_DOWN = "Spotify and Deezer were both unavailable"
REASON_SPOTIFY_DETAILS_DOWN_DEEZER_NO_MATCH = (
    "Spotify matched it but could not load its details, and Deezer had no match"
)
REASON_SPOTIFY_DETAILS_DOWN_DEEZER_DOWN = (
    "Spotify matched it but could not load its details, and Deezer was unavailable"
)
REASON_DEEZER_DOWN_SPOTIFY_NO_MATCH = "Deezer was unavailable and Spotify had no match"


def _unmatched_reason(key, spotify_search_down, spotify_details_down, deezer_down):
    """Return ``(row text, reason code)`` for an album neither provider matched."""
    if key in spotify_search_down:
        text = (
            REASON_SPOTIFY_SEARCH_DOWN_DEEZER_DOWN
            if deezer_down
            else REASON_SPOTIFY_SEARCH_DOWN_DEEZER_NO_MATCH
        )
    elif key in spotify_details_down:
        text = (
            REASON_SPOTIFY_DETAILS_DOWN_DEEZER_DOWN
            if deezer_down
            else REASON_SPOTIFY_DETAILS_DOWN_DEEZER_NO_MATCH
        )
    elif deezer_down:
        text = REASON_DEEZER_DOWN_SPOTIFY_NO_MATCH
    else:
        return "No match on Spotify or Deezer", REASON_NO_SPOTIFY_MATCH
    return text, REASON_PROVIDER_UNAVAILABLE


async def _run_deezer_fallback_phase(
    job_id,
    session,
    misses,
    cache_hits,
    spotify_unavailable_keys=frozenset(),
    spotify_detail_unavailable_keys=frozenset(),
):
    """Deezer fallback pass over albums Spotify could not enrich.

    *misses* is a dict keyed by (artist_norm, album_norm) tuples, mapping to
    each album's original data -- the same shape ``cache_misses`` already
    uses. Reports progress in the 60-75% range. Promotes matched albums
    into *cache_hits* (mutated in place) and registers the final unmatched
    entry for anything neither provider could enrich, since this is the
    last phase in the chain. Returns new_metadata_rows for the newly
    matched Deezer albums.

    An album neither provider matched is recorded as a no-match only when
    both providers answered. If Spotify could not answer for it (its key is
    in *spotify_unavailable_keys*, or Spotify matched it but could not load
    its details, in *spotify_detail_unavailable_keys*) or Deezer could not,
    it is recorded with the distinct "provider unavailable" reason: a
    listener must not be told an album does not exist because a provider was
    down. The row text names exactly which provider said what.
    """
    if not misses:
        return []

    logging.info(
        f"Starting Deezer fallback for {len(misses)} albums Spotify could not enrich"
    )
    fallback_start_time = time.time()

    unchecked = set()

    async def enrich_one(key, data):
        artist, album = key
        try:
            album_id = await _orchestrator.search_deezer_album(session, artist, album)
            if not album_id:
                return key, data, None
            metadata = await _orchestrator.fetch_deezer_album(session, album_id)
        except ProviderError as exc:
            # Deezer is an enrichment: a throttled or failing Deezer leaves
            # this album unenriched. It is not a "no match", so the unmatched
            # entry below says the album could not be checked.
            logging.warning(
                f"Deezer could not be read for one album ({exc.code}); "
                "it will not be recorded as a no-match"
            )
            unchecked.add(key)
            return key, data, None
        return key, data, metadata

    tasks = [
        asyncio.ensure_future(enrich_one(key, data)) for key, data in misses.items()
    ]

    new_metadata_rows = []
    matched_count = 0
    done = 0
    total = len(tasks)
    try:
        for fut in asyncio.as_completed(tasks):
            key, data, metadata = await fut
            done += 1
            jobs.report_phase(
                job_id,
                jobs.DEEZER_FALLBACK,
                done,
                total,
                f"Checking Deezer: {done}/{total} albums...",
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
                unmatched_key = "|".join(
                    normalize_name(original_artist, original_album)
                )
                reason, reason_code = _unmatched_reason(
                    key,
                    spotify_unavailable_keys,
                    spotify_detail_unavailable_keys,
                    key in unchecked,
                )
                jobs.record_unmatched(
                    job_id,
                    unmatched_key,
                    {
                        "artist": original_artist,
                        "album": original_album,
                        "reason": reason,
                        "reason_code": reason_code,
                        "album_image": None,
                        "spotify_id": None,
                        "play_count": data.get("play_count"),
                    },
                )
    finally:
        # An exception from one album must not leave its siblings running on
        # a session that is about to close (F-B23-24).
        await cancel_and_drain(tasks)

    existing = jobs.progress(job_id) or {}
    if unchecked and not existing.get("stats", {}).get("partial_data_warning"):
        jobs.record_stat(
            job_id,
            "partial_data_warning",
            "Deezer could not be reached for some albums, so they were not checked there.",
        )

    fallback_duration = time.time() - fallback_start_time
    logging.info(
        f"Deezer fallback completed in {fallback_duration:.1f}s: "
        f"{matched_count}/{total} misses found on Deezer"
    )
    return new_metadata_rows
