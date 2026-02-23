import asyncio
import logging
import math
import threading
import time
import traceback
from weakref import WeakKeyDictionary

import aiohttp
from aiolimiter import AsyncLimiter

from scrobblescope.config import (
    LASTFM_REQUESTS_PER_SECOND,
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


def _get_loop_limiter(cache, rate, period):
    """Return a loop-scoped AsyncLimiter, creating one if it doesn't exist yet."""
    loop = asyncio.get_running_loop()
    with _LIMITER_LOCK:
        limiter = cache.get(loop)
        if limiter is None:
            limiter = AsyncLimiter(rate, period)
            cache[loop] = limiter
    return limiter


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


def run_async_in_thread(coro):
    """Run an async coroutine synchronously in a short-lived thread.

    Used only by ``/validate_user``; background_task owns its own event loop.
    """
    result = []
    error = []

    def runner():
        loop = None
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result.append(loop.run_until_complete(coro()))
        except Exception as e:
            error_traceback = traceback.format_exc()
            logging.error(f"Error in async thread: {e}\n{error_traceback}")
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
    """
    connector = aiohttp.TCPConnector(
        limit=40,  # Max total connections across all hosts
        limit_per_host=25,  # Max connections per host (Spotify/Last.fm)
        ttl_dns_cache=300,  # Cache DNS for 5 minutes
        enable_cleanup_closed=True,
        force_close=False,  # Allow connection reuse
    )

    timeout = aiohttp.ClientTimeout(
        total=30,  # Total timeout for request
        connect=10,  # Connection establishment timeout
        sock_read=20,  # Socket read timeout
    )

    return aiohttp.ClientSession(
        connector=connector,
        timeout=timeout,
        raise_for_status=False,  # Manual status handling
    )


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
