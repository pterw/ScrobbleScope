import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any

import aiohttp

from scrobblescope.config import (
    LASTFM_API_KEY,
    LASTFM_REQUESTS_PER_SECOND,
    MAX_CONCURRENT_LASTFM,
)
from scrobblescope.errors import PrivateProfileError, UserNotFoundError
from scrobblescope.utils import (
    create_optimized_session,
    get_cached_response,
    get_lastfm_limiter,
    parse_retry_after,
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
    # If not cached, proceed with the request. Every caller already wraps
    # this in its own try/except (F-B22-1): a raised exception here reaches
    # the caller as "validation unavailable", which is the correct signal
    # for a rate limit, timeout, or malformed response. Reporting exists=True
    # instead would show a confirmed-valid username for input Last.fm never
    # actually verified.
    async with create_optimized_session() as session:
        async with session.get(url, params=params) as resp:
            if resp.status == 200:
                data = await resp.json()
                # Last.fm can answer error 6 ("User not found") in a 200
                # body: that is not-found, and never cached as a hit.
                if isinstance(data, dict) and str(data.get("error")) == "6":
                    return {"exists": False, "registered_year": None}
                # Only a body that carries the user is a verified account.
                if isinstance(data, dict) and isinstance(data.get("user"), dict):
                    set_cached_response(url, data, params)
                return {
                    "exists": True,
                    "registered_year": _extract_year(data),
                }
            elif resp.status == 404:
                return {"exists": False, "registered_year": None}
            else:
                resp.raise_for_status()


async def check_profile_is_public(username: str) -> bool:
    """Return whether Last.fm permits access to *username*'s recent listening.

    A private profile is distinct from an account with no scrobbles: Last.fm
    answers ``user.getrecenttracks`` with HTTP 403 and error 17 only when
    recent listening is not public. Every other failure remains an operational
    error for the caller to handle rather than a privacy verdict.
    """

    def _is_private_profile(data: Any) -> bool:
        return isinstance(data, dict) and str(data.get("error")) == "17"

    url = "https://ws.audioscrobbler.com/2.0/"
    params = {
        "method": "user.getrecenttracks",
        "user": username,
        "api_key": LASTFM_API_KEY,
        "format": "json",
        "limit": 1,
    }
    # Only a well-formed public answer is ever cached, so a hit is public.
    # A private verdict is never cached: the owner told to make the profile
    # public must not be refused from the cache for an hour after doing so.
    if get_cached_response(url, params):
        return True

    async with create_optimized_session() as session:
        async with session.get(url, params=params) as resp:
            data = await resp.json()
            if _is_private_profile(data):
                return False
            resp.raise_for_status()
            if isinstance(data, dict) and isinstance(data.get("recenttracks"), dict):
                set_cached_response(url, data, params)
            return True


def _is_well_formed_page(data: Any) -> bool:
    """Return True if *data* has the shape the fetch pipeline reads.

    That is a ``recenttracks`` mapping carrying ``@attr.totalPages`` that
    parses as an integer. It guards REQUEST_CACHE: a page that fails this
    (an error payload Last.fm serves as a 200, or a page with no ``@attr``)
    must not be cached, or every retry within REQUEST_CACHE_TIMEOUT would be
    answered with the same bad page and never reach the network.
    """
    if not isinstance(data, dict):
        return False
    recenttracks = data.get("recenttracks")
    if not isinstance(recenttracks, dict):
        return False
    attr = recenttracks.get("@attr")
    if not isinstance(attr, dict):
        return False
    try:
        int(attr["totalPages"])
    except (KeyError, TypeError, ValueError):
        return False
    # ``track`` is a list; a lone object is normalised to one by
    # ``_normalise_track_list`` before this predicate runs. A page that
    # carries any other shape is refused (and retried).
    return isinstance(recenttracks.get("track", []), list)


def _normalise_track_list(data: Any) -> None:
    """Turn a lone ``recenttracks.track`` object into a one-item list, in place.

    Last.fm serves a single-item collection as a bare object in some JSON
    responses; both aggregators iterate ``track`` as a list (F-B23-30).
    Anything else is left for ``_is_well_formed_page`` to refuse.
    """
    if not isinstance(data, dict):
        return
    recenttracks = data.get("recenttracks")
    if isinstance(recenttracks, dict) and isinstance(recenttracks.get("track"), dict):
        recenttracks["track"] = [recenttracks["track"]]


def _page_defect(data: Any) -> str:
    """Name the class of defect in a malformed page, never its body."""
    if not isinstance(data, dict):
        return f"body is {type(data).__name__}, not an object"
    if "error" in data:
        return "error payload"
    recenttracks = data.get("recenttracks")
    if isinstance(recenttracks, dict) and "track" in recenttracks:
        if not isinstance(recenttracks["track"], list):
            return "recenttracks.track is not a list"
    return "missing recenttracks.@attr.totalPages"


async def _cancel_and_drain(tasks) -> None:
    """Cancel every unfinished task in *tasks* and wait for all to settle.

    Called before an exception leaves a fan-out, so no page fetch is left
    pending on a session that is about to close. Results and exceptions of
    the settled tasks are discarded (retrieved, so asyncio does not log
    them); the caller re-raises the original exception unchanged.
    """
    for task in tasks:
        if not task.done():
            task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)


async def fetch_recent_tracks_page_async(
    session, username, from_ts, to_ts, page, retries=3, semaphore=None
):
    """Fetch a single page of Last.fm scrobbles with retry and rate limiting.

    Returns parsed JSON on success or None after all retries are exhausted.
    A body that is not a well-formed page (see ``_is_well_formed_page``) is
    treated like a non-200 response: retried, and None if it stays bad. Only
    a well-formed page is cached.
    Raises ``UserNotFoundError`` if the user is not found (HTTP 404) and
    ``PrivateProfileError`` if the profile is private (HTTP 403 or error 17);
    neither is retried.
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
                    retry_after = parse_retry_after(resp.headers.get("Retry-After"))
                    logging.warning(
                        f"⚠️ LAST.FM RATE LIMIT (429) on page {page}! "
                        f"Retry after {retry_after}s. "
                        f"Current limiter: {LASTFM_REQUESTS_PER_SECOND} req/s, consider reducing concurrency."
                    )
                    return None, retry_after
                if resp.status == 403:
                    # Error 17: the profile went private after the preflight.
                    # Retrying cannot help; typed as PrivateProfileError.
                    logging.error(f"Profile of {username} is private on Last.fm")
                    raise PrivateProfileError()
                if resp.status == 404:
                    # User not found
                    logging.error(f"User {username} not found on Last.fm")
                    raise UserNotFoundError()
                if resp.status != 200:
                    body = await resp.text(errors="replace")
                    # Status, size and type only: a recenttracks body carries
                    # the listener's track, artist and album names.
                    logging.warning(
                        f"❌ Unexpected Last.fm status {resp.status} on page {page}: "
                        f"{len(body.encode('utf-8'))} bytes, "
                        f"content type {resp.content_type}"
                    )
                    return None, None
                # Only the parse is guarded: an HTML page served as 200
                # (ContentTypeError) or a malformed body (JSONDecodeError, a
                # ValueError). Anything else propagates to retry_with_semaphore,
                # which retries it and logs it under its own class rather than
                # calling every failure invalid JSON (F-MAS-4).
                try:
                    data = await resp.json()
                except (aiohttp.ContentTypeError, ValueError):
                    body = await resp.text(errors="replace")
                    logging.error(
                        f"❌ Invalid JSON from Last.fm page {page}: "
                        f"{len(body.encode('utf-8'))} bytes, "
                        f"content type {resp.content_type}"
                    )
                    return None, None
                # A page that is not well-formed (an error payload served as a
                # 200, a body without @attr.totalPages) is treated like a
                # non-200 response: retried, and dropped if it stays bad. It
                # is never cached, so a bad 200 is not replayed to every retry
                # for an hour.
                if isinstance(data, dict) and str(data.get("error")) == "17":
                    raise PrivateProfileError()
                _normalise_track_list(data)
                if not _is_well_formed_page(data):
                    logging.warning(
                        f"Malformed Last.fm page {page}: {_page_defect(data)}"
                    )
                    return None, None
                set_cached_response(url, data, params)
                return data, None

    return await retry_with_semaphore(
        fetch_once,
        retries=retries,
        semaphore=semaphore,
        is_done=lambda t: t[0] is not None,
        get_retry_after=lambda t: t[1],
        extract_result=lambda t: t[0],
        default=None,
        backoff=lambda a: min(0.25 * (a + 1), 1.0),
        reraise=(UserNotFoundError, PrivateProfileError),
        error_label=f"lastfm.page {page}",
    )


async def fetch_pages_batch_async(session, username, from_ts, to_ts, pages):
    """
    Fetch Last.fm pages with controlled concurrency to respect rate limits.
    Semaphore (MAX_CONCURRENT_LASTFM) caps in-flight requests; rate limiter
    (_LASTFM_LIMITER) caps throughput. Called once with all pages rather than
    in sequential batches to avoid idle gaps. If one page raises, the other
    page fetches are cancelled and awaited before the exception propagates.
    """
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_LASTFM)

    async def fetch_with_semaphore(page):
        return await fetch_recent_tracks_page_async(
            session, username, from_ts, to_ts, page, semaphore=semaphore
        )

    tasks = [asyncio.ensure_future(fetch_with_semaphore(p)) for p in pages]
    try:
        results = await asyncio.gather(*tasks)
    finally:
        await _cancel_and_drain(tasks)

    successful = sum(1 for r in results if r is not None)
    logging.debug(f"Batch {min(pages)}-{max(pages)}: {successful}/{len(results)} pages")
    return results


async def fetch_all_recent_tracks_async(username, from_ts, to_ts, progress_cb=None):
    """Fetch all Last.fm scrobble pages. Returns (pages, metadata) tuple.

    Args:
        progress_cb: Optional callback invoked as
            ``progress_cb(pages_done, total_pages, pages_received)`` after
            each page fetch.
    """
    fetch_start_time = time.time()
    async with create_optimized_session() as session:
        first = await fetch_recent_tracks_page_async(
            session, username, from_ts, to_ts, 1
        )
        if not _is_well_formed_page(first):
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
            progress_cb(1, total_pages, len(all_pages))

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
                try:
                    for fut in asyncio.as_completed(tasks):
                        result = await fut
                        completed += 1
                        if result is not None:
                            all_pages.append(result)
                        progress_cb(completed, total_pages, len(all_pages))
                finally:
                    # An exception (the mid-job 404) must not leave sibling
                    # fetches pending on a session that is about to close.
                    await _cancel_and_drain(tasks)
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
