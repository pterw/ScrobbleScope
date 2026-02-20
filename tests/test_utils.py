# tests/test_utils.py
import threading
import time

import pytest

from scrobblescope.utils import (
    REQUEST_CACHE,
    _cache_lock,
    cleanup_expired_cache,
    get_cached_response,
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
