import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import aiohttp

from scrobblescope.config import (
    LASTFM_API_KEY,
    LASTFM_REQUESTS_PER_SECOND,
    MAX_CONCURRENT_LASTFM,
)
from scrobblescope.errors import PrivateProfileError, ProviderError, UserNotFoundError
from scrobblescope.plays import Play, Window
from scrobblescope.utils import (
    cancel_and_drain,
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
            return datetime.fromtimestamp(ts, tz=UTC).year
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


async def _error_number(resp) -> str:
    """Return the Last.fm error number in *resp*'s body, or ``"unknown"``.

    Digits only: the body itself is never returned, so a caller can log the
    result without a message or a listener's names reaching a log line.
    """
    try:
        data = await resp.json(content_type=None)
    except (aiohttp.ClientError, ValueError):
        return "unknown"
    number = str(data.get("error")) if isinstance(data, dict) else ""
    return number if number.isdigit() and len(number) <= 3 else "unknown"


async def fetch_recent_tracks_page_async(
    session, username, from_ts, to_ts, page, retries=3, semaphore=None
):
    """Fetch a single page of Last.fm scrobbles with retry and rate limiting.

    Returns parsed JSON on success or None after all retries are exhausted.
    A body that is not a well-formed page (see ``_is_well_formed_page``) is
    treated like a non-200 response: retried, and None if it stays bad. Only
    a well-formed page is cached.
    Raises ``UserNotFoundError`` if the user is not found (HTTP 404) and
    ``PrivateProfileError`` if the profile is private (error 17, in the body
    of an HTTP 403 or of a 200); neither is retried. Any other 403 is an
    operational failure, retried like a non-200 status.
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
                    # Last.fm's error page names no HTTP status for any error
                    # code, so a 403 is not proof of error 17: read the body.
                    # Only error 17 (the profile went private after the
                    # preflight) is a privacy verdict, and retrying cannot help.
                    error_number = await _error_number(resp)
                    if error_number == "17":
                        logging.error("Profile went private on Last.fm during a job")
                        raise PrivateProfileError()
                    # Any other 403 (10 invalid key, 26 suspended key, an
                    # unknown body) is our access failing, not the listener's
                    # privacy: log the status and number, never the body, and
                    # take the unavailable path (retried, then the page drops).
                    logging.error(
                        f"Last.fm refused page {page}: HTTP 403, "
                        f"error number {error_number}"
                    )
                    return None, None
                if resp.status == 404:
                    # User not found
                    logging.error("User not found on Last.fm during a job")
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
            # One fan-out for every caller, with or without a progress
            # callback. The semaphore (MAX_CONCURRENT_LASTFM) caps in-flight
            # requests and the rate limiter caps throughput; all remaining
            # pages are submitted at once rather than in sequential batches,
            # to avoid idle gaps.
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
                for p in range(2, total_pages + 1)
            ]
            completed = 1  # page 1 already done
            try:
                for fut in asyncio.as_completed(tasks):
                    result = await fut
                    completed += 1
                    if result is not None:
                        all_pages.append(result)
                    if progress_cb is not None:
                        progress_cb(completed, total_pages, len(all_pages))
            finally:
                # An exception (the mid-job 404) must not leave sibling
                # fetches pending on a session that is about to close.
                await cancel_and_drain(tasks)

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


@dataclass(frozen=True, slots=True)
class FetchSummary:
    """How complete a fetch was: the pages Last.fm reported and the pages read."""

    pages_expected: int
    pages_received: int

    @property
    def pages_dropped(self) -> int:
        """Return how many pages never arrived."""
        return max(0, self.pages_expected - self.pages_received)

    @property
    def partial(self) -> bool:
        """Return whether any page was lost."""
        return self.pages_received < self.pages_expected

    @property
    def data_loss_pct(self) -> int:
        """Return the share of pages lost, as a whole percent (0 when none expected)."""
        if self.pages_expected == 0:
            return 0
        return round((self.pages_dropped / self.pages_expected) * 100)


@dataclass(frozen=True, slots=True)
class ScrobbleFetch:
    """The scrobbles of one user in one window, with how complete they are.

    ``dropped_undated`` counts entries with no date (the now-playing entry);
    ``dropped_malformed`` counts entries that could not be read. Neither is
    ever logged by content.
    """

    plays: tuple[Play, ...]
    summary: FetchSummary
    dropped_undated: int
    dropped_malformed: int


def _page_number(page: Any) -> int:
    """Return the page's own number, or 0 when it carries none.

    Pages are sorted by this so the plays leave in page order, not in the order
    the network happened to answer; a stable sort leaves unnumbered pages as
    received.
    """
    try:
        return int(page["recenttracks"]["@attr"]["page"])
    except (KeyError, TypeError, ValueError):
        return 0


def _name_of(entry: dict, key: str) -> str:
    """Return the ``#text`` of an entry's artist or album object, or ``""``."""
    value = entry.get(key)
    text = value.get("#text") if isinstance(value, dict) else None
    return text if isinstance(text, str) else ""


def _plays_from_pages(pages: list) -> tuple[list[Play], int, int]:
    """Turn well-formed Last.fm pages into plays; count the entries that cannot be.

    Returns ``(plays, dropped_undated, dropped_malformed)``. The date comes from
    ``date.uts`` decoded as UTC, never from ``date["#text"]``, which is
    locale-dependent. Nothing but the timestamp and the three names is kept:
    no mbid, image, url or username ever leaves this function.
    """
    plays: list[Play] = []
    undated = 0
    malformed = 0
    for page in sorted(pages, key=_page_number):
        for entry in page.get("recenttracks", {}).get("track", []):
            if not isinstance(entry, dict):
                malformed += 1
                continue
            date_field = entry.get("date")
            uts = date_field.get("uts") if isinstance(date_field, dict) else None
            if not uts:
                undated += 1
                continue
            try:
                played_at = datetime.fromtimestamp(int(uts), tz=UTC)
            except (TypeError, ValueError, OverflowError, OSError):
                malformed += 1
                continue
            name = entry.get("name")
            plays.append(
                Play(
                    played_at=played_at,
                    artist=_name_of(entry, "artist"),
                    album=_name_of(entry, "album"),
                    track=name if isinstance(name, str) else "",
                )
            )
    return plays, undated, malformed


async def fetch_scrobbles(username, window: Window, progress_cb=None) -> ScrobbleFetch:
    """Return the scrobbles of *username* inside *window* as normalized plays.

    Pagination, retries, the page cache and every Last.fm quirk stay behind this
    function; raw pages never leave it. ``progress_cb(pages_done, pages_expected,
    pages_received)`` is passed to the page fan-out untouched.

    Raises the typed failures the page layer raises (``UserNotFoundError``,
    ``PrivateProfileError``) and, when page 1 never answered,
    ``ProviderError("lastfm", "unavailable")``. A total failure is an exception,
    never a status value. Partial data is a value, not an exception: see
    ``ScrobbleFetch.summary``. No message names the user or any page content.
    """
    pages, meta = await fetch_all_recent_tracks_async(
        username, window.start_ts(), window.end_ts(), progress_cb=progress_cb
    )
    if meta.get("status") == "error":
        raise ProviderError("lastfm", "unavailable")
    plays, undated, malformed = _plays_from_pages(pages)
    if malformed:
        logging.warning(
            f"Last.fm: {malformed} entries could not be read and were skipped"
        )
    summary = FetchSummary(
        pages_expected=meta.get("pages_expected", 0),
        pages_received=meta.get("pages_received", len(pages)),
    )
    return ScrobbleFetch(tuple(plays), summary, undated, malformed)
