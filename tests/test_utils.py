# tests/test_utils.py
import asyncio
import threading
import time

import pytest

from scrobblescope.utils import (
    REQUEST_CACHE,
    _cache_lock,
    _GlobalThrottle,
    cleanup_expired_cache,
    format_seconds,
    format_seconds_mobile,
    get_cached_response,
    get_lastfm_limiter,
    set_cached_response,
)


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear REQUEST_CACHE before and after each test to prevent state bleed."""
    with _cache_lock:
        REQUEST_CACHE.clear()
    yield
    with _cache_lock:
        REQUEST_CACHE.clear()


def test_get_cached_response_returns_fresh_entry():
    """
    GIVEN a freshly cached response
    WHEN get_cached_response is called with the same URL
    THEN it should return the cached data.
    """
    set_cached_response("/api/test", {"result": "ok"})
    result = get_cached_response("/api/test")
    assert result == {"result": "ok"}


def test_get_cached_response_returns_none_for_missing_key():
    """
    GIVEN no matching entry in REQUEST_CACHE
    WHEN get_cached_response is called
    THEN it should return None.
    """
    result = get_cached_response("/api/nonexistent")
    assert result is None


def test_get_cached_response_returns_none_for_expired_entry():
    """
    GIVEN a cache entry whose timestamp is past REQUEST_CACHE_TIMEOUT
    WHEN get_cached_response is called
    THEN it should return None (treat as miss).
    """
    with _cache_lock:
        REQUEST_CACHE["/api/stale"] = (time.time() - 7200, {"stale": True})
    result = get_cached_response("/api/stale")
    assert result is None


def test_set_cached_response_overwrites_existing_entry():
    """
    GIVEN a URL already stored in the cache
    WHEN set_cached_response is called again with a new value
    THEN it should store the latest value.
    """
    set_cached_response("/api/test", {"v": 1})
    set_cached_response("/api/test", {"v": 2})
    result = get_cached_response("/api/test")
    assert result == {"v": 2}


def test_cleanup_expired_cache_removes_expired_keeps_fresh():
    """
    GIVEN a mix of expired and fresh cache entries
    WHEN cleanup_expired_cache is called
    THEN only expired entries should be removed; fresh entries should remain.
    """
    with _cache_lock:
        REQUEST_CACHE["/old"] = (time.time() - 7200, {"old": True})
        REQUEST_CACHE["/new"] = (time.time(), {"new": True})

    cleanup_expired_cache()

    with _cache_lock:
        assert "/old" not in REQUEST_CACHE
        assert "/new" in REQUEST_CACHE


def test_cache_concurrent_write_and_cleanup_no_error():
    """
    GIVEN multiple threads simultaneously writing to and cleaning REQUEST_CACHE
    WHEN all threads run concurrently
    THEN no RuntimeError (dictionary changed size during iteration) should occur.
    This validates WP-2 thread-safety: _cache_lock guards all cache mutations.
    """
    errors = []

    def writer():
        for i in range(100):
            try:
                set_cached_response(f"/api/item/{i}", {"i": i})
            except Exception as exc:
                errors.append(exc)

    def cleaner():
        for _ in range(20):
            try:
                cleanup_expired_cache()
            except Exception as exc:
                errors.append(exc)

    threads = [threading.Thread(target=writer) for _ in range(4)]
    threads += [threading.Thread(target=cleaner) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == [], f"Concurrent cache access raised errors: {errors}"


def test_global_throttle_serializes_rapid_calls():
    """
    GIVEN a _GlobalThrottle at rate=10 (0.1s minimum interval)
    WHEN next_wait() is called 5 times in rapid succession
    THEN the first call returns 0 and subsequent calls return increasing
    positive waits, proving that concurrent callers are serialized.
    """
    throttle = _GlobalThrottle(10, 1.0)
    waits = [throttle.next_wait() for _ in range(5)]

    assert waits[0] == 0.0
    assert all(w > 0 for w in waits[1:])
    for i in range(1, len(waits) - 1):
        assert waits[i + 1] > waits[i]


def test_cross_thread_limiters_share_global_throttle():
    """
    GIVEN two threads each creating their own asyncio event loop
    WHEN both call get_lastfm_limiter()
    THEN the returned _ThrottledLimiter instances share the same
    _GlobalThrottle object, so aggregate throughput across all
    concurrent background jobs is capped at the configured rate.
    """
    throttles = []

    def capture_throttle():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def _get():
            return get_lastfm_limiter()

        try:
            limiter = loop.run_until_complete(_get())
            throttles.append(limiter._throttle)
        finally:
            loop.close()

    t1 = threading.Thread(target=capture_throttle)
    t2 = threading.Thread(target=capture_throttle)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert len(throttles) == 2
    assert throttles[0] is throttles[1]


# ------------------------------------------------------------------ #
# format_seconds tests                                                 #
# ------------------------------------------------------------------ #


@pytest.mark.parametrize(
    "seconds, expected",
    [
        (0, "0 secs"),
        (1, "1 secs"),
        (59, "59 secs"),
        (60, "1 mins, 0 secs"),
        (75, "1 mins, 15 secs"),
        (3599, "59 mins, 59 secs"),
        (3600, "1 hrs, 0 mins"),
        (3661, "1 hrs, 1 mins"),
        (16200, "4 hrs, 30 mins"),
        (86400, "1 day, 0 hrs, 0 mins"),
        (172800, "2 days, 0 hrs, 0 mins"),
        (129600, "1 day, 12 hrs, 0 mins"),
        (0.4, "1 secs"),  # ceil rounds up fractional seconds
    ],
)
def test_format_seconds(seconds, expected):
    """format_seconds returns verbose user-friendly time strings."""
    assert format_seconds(seconds) == expected


# ------------------------------------------------------------------ #
# format_seconds_mobile tests                                         #
# ------------------------------------------------------------------ #


@pytest.mark.parametrize(
    "seconds, expected",
    [
        (0, "0s"),
        (1, "1s"),
        (59, "59s"),
        (60, "1m 0s"),
        (75, "1m 15s"),
        (3599, "59m 59s"),
        (3600, "1h 0m"),
        (3661, "1h 1m"),
        (16200, "4h 30m"),
        (86400, "1d 0h"),
        (129600, "1d 12h"),
        (0.4, "1s"),  # ceil rounds up fractional seconds
    ],
)
def test_format_seconds_mobile(seconds, expected):
    """format_seconds_mobile returns abbreviated max-2-unit strings."""
    assert format_seconds_mobile(seconds) == expected


def test_format_seconds_mobile_negative_passes_through():
    """Negative input is not clamped (matches format_seconds behavior)."""
    result = format_seconds_mobile(-5)
    assert result == "-5s"
