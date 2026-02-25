import asyncio
import logging
import time
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from scrobblescope.config import (
    LASTFM_API_KEY,
    LASTFM_REQUESTS_PER_SECOND,
    MAX_CONCURRENT_LASTFM,
)
from scrobblescope.utils import (
    create_optimized_session,
    get_cached_response,
    get_lastfm_limiter,
    retry_with_semaphore,
    set_cached_response,
)


async def check_user_exists(username):
    """Verify if a Last.fm user exists and return registration year.

    Returns a dict with ``exists`` (bool) and ``registered_year`` (int or None).
    """

    def _extract_year(data):
        try:
            ts = int(data["user"]["registered"]["unixtime"])
            return datetime.fromtimestamp(ts, tz=timezone.utc).year
        except (KeyError, TypeError, ValueError):
            return None

    url = "https://ws.audioscrobbler.com/2.0/"
    params = {
        "method": "user.getinfo",
        "user": username,
        "api_key": LASTFM_API_KEY,
        "format": "json",
    }
    # check cache first
    cached_response = get_cached_response(url, params)
    if cached_response:
        return {
            "exists": True,
            "registered_year": _extract_year(cached_response),
        }
    # If not cached, proceed with the request
    async with create_optimized_session() as session:
        try:
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    set_cached_response(url, data, params)
                    return {
                        "exists": True,
                        "registered_year": _extract_year(data),
                    }
                elif resp.status == 404:
                    return {"exists": False, "registered_year": None}
                else:
                    # let the error propagate for other status codes
                    resp.raise_for_status()
                    return {"exists": False, "registered_year": None}
        except Exception as e:
            logging.error(f"Error checking user existence: {e}")
            # return exists=True to continue processing - we'll get a more specific error later
            return {"exists": True, "registered_year": None}


async def fetch_recent_tracks_page_async(
    session, username, from_ts, to_ts, page, retries=3, semaphore=None
):
    """Fetch a single page of Last.fm scrobbles with retry and rate limiting.

    Returns parsed JSON on success or None after all retries are exhausted.
    Raises ``ValueError`` if the user is not found (HTTP 404).
    """
    url = "https://ws.audioscrobbler.com/2.0/"
    params = {
        "method": "user.getrecenttracks",
        "user": username,
        "api_key": LASTFM_API_KEY,
        "format": "json",
        "from": from_ts,
        "to": to_ts,
        "limit": 200,
        "page": page,
    }

    # check cache first
    cached_response = get_cached_response(url, params)
    if cached_response:
        return cached_response

    limiter = get_lastfm_limiter()

    async def fetch_once():
        async with limiter:
            logging.debug(f"Requesting Last.fm page {page}")
            async with session.get(url, params=params) as resp:
                if resp.status == 429:
                    retry_after = int(resp.headers.get("Retry-After", "1"))
                    logging.warning(
                        f"⚠️ LAST.FM RATE LIMIT (429) on page {page}! "
                        f"Retry after {retry_after}s. "
                        f"Current limiter: {LASTFM_REQUESTS_PER_SECOND} req/s, consider reducing concurrency."
                    )
                    return None, retry_after
                if resp.status == 404:
                    # User not found
                    logging.error(f"User {username} not found on Last.fm")
                    raise ValueError(f"User '{username}' not found on Last.fm")
                if resp.status != 200:
                    body = await resp.text()
                    logging.warning(
                        f"❌ Unexpected Last.fm status {resp.status} on page {page}: {body[:200]}"
                    )
                    return None, None
                try:
                    data = await resp.json()
                    # Cache the response for future use
                    set_cached_response(url, data, params)
                    return data, None
                except Exception:
                    body = await resp.text()
                    logging.error(
                        f"❌ Invalid JSON from Last.fm page {page}. Body starts with: {body[:200]}"
                    )
                    return None, None

    return await retry_with_semaphore(
        fetch_once,
        retries=retries,
        semaphore=semaphore,
        is_done=lambda t: t[0] is not None,
        get_retry_after=lambda t: t[1],
        extract_result=lambda t: t[0],
        default=None,
        backoff=lambda a: min(0.25 * (a + 1), 1.0),
        reraise=(ValueError,),
        error_label=f"Last.fm page {page}",
    )


async def fetch_pages_batch_async(session, username, from_ts, to_ts, pages):
    """
    Fetch Last.fm pages with controlled concurrency to respect rate limits.
    Semaphore (MAX_CONCURRENT_LASTFM) caps in-flight requests; rate limiter
    (_LASTFM_LIMITER) caps throughput. Called once with all pages rather than
    in sequential batches to avoid idle gaps.
    """
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_LASTFM)

    async def fetch_with_semaphore(page):
        return await fetch_recent_tracks_page_async(
            session, username, from_ts, to_ts, page, semaphore=semaphore
        )

    tasks = [fetch_with_semaphore(p) for p in pages]
    results = await asyncio.gather(*tasks)

    successful = sum(1 for r in results if r is not None)
    logging.debug(f"Batch {min(pages)}-{max(pages)}: {successful}/{len(results)} pages")
    return results


async def fetch_all_recent_tracks_async(username, from_ts, to_ts, progress_cb=None):
    """Fetch all Last.fm scrobble pages. Returns (pages, metadata) tuple.

    Args:
        progress_cb: Optional ``Callable[[int, int], None]`` invoked as
            ``progress_cb(pages_done, total_pages)`` after each page
            fetch completes.
    """
    fetch_start_time = time.time()
    async with create_optimized_session() as session:
        first = await fetch_recent_tracks_page_async(
            session, username, from_ts, to_ts, 1
        )
        if not first or "recenttracks" not in first:
            logging.error("Failed to fetch initial page from Last.fm")
            error_meta: dict[str, Any] = {
                "status": "error",
                "reason": "lastfm_unavailable",
            }
            return [], error_meta

        total_pages = int(first["recenttracks"]["@attr"]["totalPages"])
        logging.info(f"Last.fm: Fetching {total_pages} pages of scrobbles")
        all_pages = [first]

        if progress_cb is not None:
            progress_cb(1, total_pages)

        if total_pages > 1:
            remaining = range(2, total_pages + 1)

            if progress_cb is not None:
                # Per-page progress: use as_completed instead of gather
                semaphore = asyncio.Semaphore(MAX_CONCURRENT_LASTFM)
                tasks = [
                    asyncio.ensure_future(
                        fetch_recent_tracks_page_async(
                            session,
                            username,
                            from_ts,
                            to_ts,
                            p,
                            semaphore=semaphore,
                        )
                    )
                    for p in remaining
                ]
                completed = 1  # page 1 already done
                for fut in asyncio.as_completed(tasks):
                    result = await fut
                    completed += 1
                    if result is not None:
                        all_pages.append(result)
                    progress_cb(completed, total_pages)
            else:
                results = await fetch_pages_batch_async(
                    session, username, from_ts, to_ts, remaining
                )
                all_pages.extend([r for r in results if r])

        fetch_elapsed = time.time() - fetch_start_time
        logging.info(
            f"⏱️  Time elapsed (fetching {total_pages} Last.fm pages): {fetch_elapsed:.1f}s"
        )

        pages_expected = total_pages
        pages_received = len(all_pages)
        metadata: dict[str, Any] = {
            "status": "ok",
            "pages_expected": pages_expected,
            "pages_received": pages_received,
        }
        if pages_received < pages_expected:
            metadata["status"] = "partial"
            metadata["pages_dropped"] = pages_expected - pages_received

        logging.info(f"Last.fm: Fetched {pages_received}/{pages_expected} pages")
        return all_pages, metadata
