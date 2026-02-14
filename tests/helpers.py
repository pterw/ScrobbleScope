from unittest.mock import AsyncMock

TEST_JOB_PARAMS = {
    "username": "testuser",
    "year": 2025,
    "sort_mode": "playcount",
    "release_scope": "same",
    "decade": None,
    "release_year": None,
    "min_plays": 10,
    "min_tracks": 3,
    "limit_results": "all",
}


class NoopAsyncContext:
    """A no-op async context manager for patching rate limiters in tests."""

    async def __aenter__(self):
        return None

    async def __aexit__(self, exc_type, exc, tb):
        return False


def make_response_context(response):
    """Build an async context manager whose __aenter__ returns response."""
    cm = AsyncMock()
    cm.__aenter__.return_value = response
    return cm
