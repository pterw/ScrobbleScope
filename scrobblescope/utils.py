import asyncio
import json
import logging
import math
import sys
import threading
import time
from collections.abc import Sequence
from weakref import WeakKeyDictionary

import aiohttp
from aiolimiter import AsyncLimiter

from scrobblescope.api_logging import attach_summary_on_close, build_trace_config
from scrobblescope.config import (
    APP_USER_AGENT,
    DEEZER_REQUESTS_PER_SECOND,
    LASTFM_REQUESTS_PER_SECOND,
    MAX_RETRY_AFTER_SECONDS,
    MUSICBRAINZ_REQUESTS_PER_SECOND,
    REQUEST_CACHE_TIMEOUT,
    SPOTIFY_REQUESTS_PER_SECOND,
)

# Global state tracking
REQUEST_CACHE = {}  # Cache for API responses
_cache_lock = threading.Lock()  # Guards all REQUEST_CACHE read/write/cleanup ops

# Rate limiters are scoped per running event loop.
# AsyncLimiter instances cannot be safely reused across loops.
_LASTFM_LIMITERS = WeakKeyDictionary()
_SPOTIFY_LIMITERS = WeakKeyDictionary()
_DEEZER_LIMITERS = WeakKeyDictionary()
_MUSICBRAINZ_LIMITERS = WeakKeyDictionary()
_LIMITER_LOCK = threading.Lock()


class _GlobalThrottle:
    """Thread-safe throttle enforcing a global rate limit across all event loops.

    Each background job creates its own asyncio event loop, which means
    per-loop AsyncLimiter instances are independent. This throttle sits
    above them to cap aggregate throughput from all concurrent jobs within
    the configured API rate.
    """

    def __init__(self, max_rate, period=1.0):
        self._lock = threading.Lock()
        self._min_interval = period / max_rate
        self._next_allowed = 0.0

    def next_wait(self):
        """Return seconds to wait before the next call is allowed.

        Thread-safe. Advances the internal clock so concurrent callers
        are serialized at the configured rate.
        """
        with self._lock:
            now = time.time()
            if now >= self._next_allowed:
                self._next_allowed = now + self._min_interval
                return 0.0
            wait = self._next_allowed - now
            self._next_allowed += self._min_interval
            return wait


class _ThrottledLimiter:
    """Async context manager combining a global throttle with a per-loop limiter.

    The global throttle enforces the aggregate rate across all threads, then
    the per-loop AsyncLimiter handles intra-loop concurrency as before.
    """

    def __init__(self, throttle, limiter):
        self._throttle = throttle
        self._limiter = limiter

    async def __aenter__(self):
        wait = self._throttle.next_wait()
        if wait > 0:
            await asyncio.sleep(wait)
        await self._limiter.__aenter__()
        return self

    async def __aexit__(self, *args):
        await self._limiter.__aexit__(*args)


_LASTFM_THROTTLE = _GlobalThrottle(LASTFM_REQUESTS_PER_SECOND)
_SPOTIFY_THROTTLE = _GlobalThrottle(SPOTIFY_REQUESTS_PER_SECOND)
_DEEZER_THROTTLE = _GlobalThrottle(DEEZER_REQUESTS_PER_SECOND)
_MUSICBRAINZ_THROTTLE = _GlobalThrottle(MUSICBRAINZ_REQUESTS_PER_SECOND)


def _get_loop_limiter(cache, rate, period):
    """Return a loop-scoped AsyncLimiter, creating one if it doesn't exist yet."""
    loop = asyncio.get_running_loop()
    with _LIMITER_LOCK:
        limiter = cache.get(loop)
        if limiter is None:
            limiter = AsyncLimiter(rate, period)
            cache[loop] = limiter
    return limiter


async def _run_with_optional_semaphore(inner_fn, semaphore):
    """Run ``inner_fn`` directly or under a semaphore when one is provided."""
    if semaphore is None:
        return await inner_fn()
    async with semaphore:
        return await inner_fn()


def _resolve_backoff(backoff, attempt):
    """Return sleep seconds from either a constant or a callable backoff."""
    return backoff(attempt) if callable(backoff) else backoff


async def _sleep_retry_after(retry_after, jitter, attempt):
    """Sleep for Retry-After plus optional jitter."""
    sleep_time = retry_after + (jitter(attempt) if jitter is not None else 0)
    await asyncio.sleep(sleep_time)


def get_lastfm_limiter():
    """Return a throttled rate limiter for Last.fm API calls.

    Official limit: 5 requests/second per IP (averaged over 5 minutes).
    Runtime value comes from LASTFM_REQUESTS_PER_SECOND.
    Source: https://www.last.fm/api/tos

    Returns a _ThrottledLimiter that enforces a global cross-thread rate
    cap via _LASTFM_THROTTLE, then delegates to a per-loop AsyncLimiter.
    """
    loop_limiter = _get_loop_limiter(_LASTFM_LIMITERS, LASTFM_REQUESTS_PER_SECOND, 1)
    return _ThrottledLimiter(_LASTFM_THROTTLE, loop_limiter)


def get_spotify_limiter():
    """Return a throttled rate limiter for Spotify API calls.

    Official limit: Undisclosed, based on 30-second rolling window.
    Runtime value comes from SPOTIFY_REQUESTS_PER_SECOND.
    Source: https://developer.spotify.com/documentation/web-api/concepts/rate-limits

    Returns a _ThrottledLimiter that enforces a global cross-thread rate
    cap via _SPOTIFY_THROTTLE, then delegates to a per-loop AsyncLimiter.
    """
    loop_limiter = _get_loop_limiter(_SPOTIFY_LIMITERS, SPOTIFY_REQUESTS_PER_SECOND, 1)
    return _ThrottledLimiter(_SPOTIFY_THROTTLE, loop_limiter)


def get_deezer_limiter():
    """Return a throttled rate limiter for Deezer API calls.

    Official limit: 50 requests per 5 seconds per IP.
    Runtime value comes from DEEZER_REQUESTS_PER_SECOND.
    Source: https://developers.deezer.com/api

    Returns a _ThrottledLimiter that enforces a global cross-thread rate
    cap via _DEEZER_THROTTLE, then delegates to a per-loop AsyncLimiter.
    """
    loop_limiter = _get_loop_limiter(_DEEZER_LIMITERS, DEEZER_REQUESTS_PER_SECOND, 1)
    return _ThrottledLimiter(_DEEZER_THROTTLE, loop_limiter)


def get_musicbrainz_limiter():
    """Return a throttled rate limiter for MusicBrainz API calls.

    Official limit: 1 request/second per IP, enforced process-wide -- the
    global throttle is what makes this process-wide rather than per-loop,
    since the correction worker (a single dedicated thread) is not the only
    possible caller. Runtime value comes from MUSICBRAINZ_REQUESTS_PER_SECOND.
    Source: https://musicbrainz.org/doc/MusicBrainz_API/Rate_Limiting

    Returns a _ThrottledLimiter that enforces a global cross-thread rate
    cap via _MUSICBRAINZ_THROTTLE, then delegates to a per-loop AsyncLimiter.
    """
    loop_limiter = _get_loop_limiter(
        _MUSICBRAINZ_LIMITERS, MUSICBRAINZ_REQUESTS_PER_SECOND, 1
    )
    return _ThrottledLimiter(_MUSICBRAINZ_THROTTLE, loop_limiter)


def log_failure(message, level=logging.ERROR):
    """Log the exception being handled: its class at *level*, its traceback at DEBUG.

    *level* defaults to ERROR; a fail-open site (a cache read or write whose
    failure the job survives) passes ``logging.WARNING``.

    Call it from inside an ``except`` block, in place of ``logging.exception``.
    The line at *level* is *message* plus the exception's class and nothing more:
    an exception's text can carry a provider's URL with its query string, or
    a listener's artist, album and track names, and the traceback repeats it
    (owner ruling 2026-09-29). Both are still in the DEBUG record for whoever
    turns that level on, and the redacting formatter still runs over them.
    """
    exc_type = sys.exc_info()[0]
    name = exc_type.__name__ if exc_type is not None else "no active exception"
    logging.log(level, "%s: %s", message, name)
    logging.debug("%s (traceback)", message, exc_info=True)


def run_async_in_thread(coro):
    """Run an async coroutine synchronously in a short-lived thread.

    For request handlers that need one async call and cannot await it: the
    Last.fm user and privacy checks behind ``/validate_user`` and both start
    routes, and ``/api/artist_spotlight``. Background jobs build their own
    loop through ``worker.new_thread_event_loop`` instead.

    An exception is logged here at ERROR by class only (its message can
    carry a provider's URL or a listener's names); the full traceback goes
    to DEBUG. It is then re-raised in the calling thread, which is the only
    one that can answer the request.
    """
    result = []
    error = []

    def runner():
        loop = None
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result.append(loop.run_until_complete(coro()))
        except Exception as e:  # noqa: BLE001 - re-raised in the caller
            logging.error(f"Error in async thread: {type(e).__name__}")
            logging.debug("Async thread traceback", exc_info=True)
            error.append(e)
        finally:
            if loop is not None:
                loop.close()

    thread = threading.Thread(target=runner)
    thread.start()
    thread.join()

    if error:
        raise error[0]
    return result[0]


def create_optimized_session():
    """
    Create aiohttp session with production-ready connection pooling.

    This prevents:
    - Socket exhaustion from too many connections
    - DNS lookup overhead via caching
    - Timeout-related hangs

    Connection limits:
    - Total connections: 40 (across all hosts)
    - Per-host connections: 25 (for Spotify/Last.fm)
    - DNS cache: 5 minutes
    - Timeouts: 30s total, 10s connect, 20s read

    Every request carries ``APP_USER_AGENT`` unless it sets its own
    ``User-Agent``. Last.fm asks for an identifiable User-Agent on all
    requests and warns that an anonymous client risks suspension, and the
    other providers' guidelines want attribution too. MusicBrainz is the one
    caller that overrides it, with the contact-bearing form its API requires.

    Every request this session makes is also logged, in one format shared by
    every provider: ``scrobblescope.api_logging`` attaches an
    ``aiohttp.TraceConfig`` and wraps ``close()`` so the session's
    per-provider call summary logs when it closes (F-B23-6, Task 13).
    """
    connector = aiohttp.TCPConnector(
        limit=40,  # Max total connections across all hosts
        limit_per_host=25,  # Max connections per host (Spotify/Last.fm)
        ttl_dns_cache=300,  # Cache DNS for 5 minutes
        # enable_cleanup_closed was dropped: aiohttp 3.14 deprecates it on
        # Python >= 3.13.3, where the CPython bug it worked around
        # (python/cpython#118960) is fixed. The flag is ignored there, so
        # passing it only produced a DeprecationWarning per session.
        force_close=False,  # Allow connection reuse
    )

    timeout = aiohttp.ClientTimeout(
        total=30,  # Total timeout for request
        connect=10,  # Connection establishment timeout
        sock_read=20,  # Socket read timeout
    )

    session = aiohttp.ClientSession(
        connector=connector,
        timeout=timeout,
        raise_for_status=False,  # Manual status handling
        headers={"User-Agent": APP_USER_AGENT},
        trace_configs=[build_trace_config()],
    )
    return attach_summary_on_close(session)


# Request caching helper functions
def get_cache_key(url, params=None):
    """Generate a cache key from URL and params"""
    key = url
    if params:
        key += "_" + "_".join(f"{k}:{v}" for k, v in sorted(params.items()))
    return key


def get_cached_response(url, params=None):
    """Get cached response if available and not expired.

    Returns a direct reference to the cached object — callers must not mutate it.
    """
    key = get_cache_key(url, params)
    with _cache_lock:
        if key in REQUEST_CACHE:
            timestamp, data = REQUEST_CACHE[key]
            if time.time() - timestamp < REQUEST_CACHE_TIMEOUT:
                logging.debug(f"Cache hit for {key}")
                return data
    return None


def set_cached_response(url, data, params=None):
    """Cache a response with current timestamp"""
    key = get_cache_key(url, params)
    with _cache_lock:
        REQUEST_CACHE[key] = (time.time(), data)


def cleanup_expired_cache():
    """
    Remove expired entries from REQUEST_CACHE to prevent memory leaks.

    Called at the start of each background task to maintain bounded memory.
    This is critical for production deployment on Fly.io to avoid OOM errors.
    """
    current_time = time.time()
    with _cache_lock:
        expired_keys = [
            key
            for key, (timestamp, _) in REQUEST_CACHE.items()
            if current_time - timestamp >= REQUEST_CACHE_TIMEOUT
        ]
        for key in expired_keys:
            REQUEST_CACHE.pop(key, None)
        cache_count = len(REQUEST_CACHE)

    if expired_keys:
        logging.info(f"Cleaned up {len(expired_keys)} expired cache entries")
    logging.debug(f"Cache status: {cache_count} entries")


def format_seconds(seconds):
    """Format seconds into a user-friendly string for sorting by playtime."""
    seconds = int(math.ceil(seconds))

    if seconds < 60:
        return f"{seconds} secs"

    minutes, sec_remainder = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes} mins, {sec_remainder} secs"

    hours, min_remainder = divmod(minutes, 60)
    if hours < 24:
        return f"{hours} hrs, {min_remainder} mins"

    days, hour_remainder = divmod(hours, 24)
    return f"{days} day{'s' if days != 1 else ''}, {hour_remainder} hrs, {min_remainder} mins"


def format_seconds_mobile(seconds):
    """Format seconds into an abbreviated mobile-friendly string (max 2 units).

    Examples: "1d 12h", "4h 30m", "38m 15s", "15s".
    """
    seconds = int(math.ceil(seconds))

    if seconds < 60:
        return f"{seconds}s"

    minutes, sec_remainder = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes}m {sec_remainder}s"

    hours, min_remainder = divmod(minutes, 60)
    if hours < 24:
        return f"{hours}h {min_remainder}m"

    days, hour_remainder = divmod(hours, 24)
    return f"{days}d {hour_remainder}h"


def parse_retry_after(value, default=1):
    """Return a ``Retry-After`` header as whole seconds, *default* if unusable.

    The header may be delta-seconds or an HTTP date, and a provider can send
    either or garbage; a bad value must cost one retry, not the whole job
    (F-B23-21). Negative values count as unusable.
    """
    try:
        seconds = int(value)
    except (TypeError, ValueError):
        return default
    return seconds if seconds >= 0 else default


#: What a provider that cannot be read raises: a transport failure, a timeout,
#: or a body that is not JSON. With ``failure`` given, only these are
#: "unavailable"; any other exception is our bug and propagates.
PROVIDER_FAILURES = (aiohttp.ClientError, asyncio.TimeoutError, json.JSONDecodeError)


async def retry_with_semaphore(
    inner_fn,
    *,
    retries,
    semaphore=None,
    is_done,
    get_retry_after,
    extract_result,
    default,
    backoff,
    jitter=None,
    reraise=(),
    error_label="operation",
    failure=None,
):
    """Generic async retry loop with optional semaphore gating.

    Parameters
    ----------
    inner_fn : async callable returning a result tuple
    retries : int, max attempts
    semaphore : optional asyncio.Semaphore to gate each attempt
    is_done : callable(result_tuple) -> bool, whether the attempt succeeded
        or hit a terminal failure (no more retries needed)
    get_retry_after : callable(result_tuple) -> float | None, extract
        Retry-After seconds from a rate-limited response
    extract_result : callable(result_tuple) -> value to return on success
    default : value returned when all retries are exhausted
    backoff : callable(attempt: int) -> float | float, sleep seconds on
        transient error; accepts a constant float or a callable taking the
        attempt number
    jitter : optional callable(attempt: int) -> float, added to a Retry-After
        sleep. The cap below is checked on the Retry-After alone, before the
        jitter is added, so a sleep can run as long as
        ``MAX_RETRY_AFTER_SECONDS`` plus the jitter.
    reraise : tuple of exception types to propagate immediately
    error_label : str, the operation key every failure line names, for
        example ``"spotify.search"``. Never build it from an album, artist,
        track or user name: this helper is the one place that decides what a
        provider-failure line may say (operation, exception class, retry
        count), so it also writes no exception message, which for an HTTP
        client error can carry the request URL and its query.
    failure : optional callable(kind) -> Exception or None, ``kind`` being
        ``"rate_limited"`` or ``"unavailable"``. When given, a throttled or
        exhausted call raises ``failure(kind)`` instead of returning
        ``default``, so a caller can tell a provider that refused from a
        provider that answered "no match". ``rate_limited`` when the last
        attempt was a 429 or a Retry-After above the cap, else ``unavailable``
        (a timeout, a connection error, a 5xx, a bad body). A factory that
        returns None declines that kind and ``default`` is returned. With
        ``failure`` given, only ``PROVIDER_FAILURES`` are retried and counted
        as "unavailable"; any other exception propagates at once, so it is
        classified as ours rather than as a provider outage.

    A Retry-After above ``MAX_RETRY_AFTER_SECONDS`` is not slept: one warning
    is logged and ``default`` is returned at once, or ``failure`` raised.

    Never sleeps after the final attempt, on either path.
    """
    kind = "unavailable"
    for attempt in range(retries):
        try:
            result_tuple = await _run_with_optional_semaphore(inner_fn, semaphore)

            if is_done(result_tuple):
                return extract_result(result_tuple)

            retry_after = get_retry_after(result_tuple)
            if retry_after is not None:
                kind = "rate_limited"
                if retry_after > MAX_RETRY_AFTER_SECONDS:
                    logging.warning(
                        f"Retry-After {retry_after}s for {error_label} exceeds "
                        f"the {MAX_RETRY_AFTER_SECONDS}s cap; giving up"
                    )
                    break
                if attempt < retries - 1:
                    await _sleep_retry_after(retry_after, jitter, attempt)
                continue
            kind = "unavailable"
        except reraise:
            raise
        # Broad on purpose: a retry helper retries whatever its callable
        # raises, except the declared ``reraise`` types. What it owes the
        # reader is the exception's class, so a programming error retried
        # here cannot pass for a network blip in the log. The message is
        # left out on purpose (see ``error_label`` above).
        except Exception as e:  # noqa: BLE001
            if failure is not None and not isinstance(e, PROVIDER_FAILURES):
                logging.error(f"Error in {error_label}: {type(e).__name__}")
                raise
            kind = "unavailable"
            logging.error(f"Error in {error_label}: {type(e).__name__}")

        if attempt < retries - 1:
            await asyncio.sleep(_resolve_backoff(backoff, attempt))
    else:
        logging.error(f"All {retries} retries failed for {error_label}")

    error = failure(kind) if failure is not None else None
    if error is not None:
        raise error
    return default


async def cancel_and_drain(tasks: Sequence[asyncio.Future]) -> None:
    """Cancel every unfinished task in *tasks* and wait for all to settle.

    Called before an exception leaves a fan-out, so no fetch is left pending
    on a session that is about to close. Results and exceptions of the
    settled tasks are discarded (retrieved, so asyncio does not log them);
    the caller re-raises the original exception unchanged. *tasks* is a
    sequence, not any iterable, because it is walked twice.
    """
    for task in tasks:
        if not task.done():
            task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
