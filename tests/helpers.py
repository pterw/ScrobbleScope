from unittest.mock import AsyncMock

# Standard form data for POST /results_loading tests (year as string, flounder14).
# Use {**VALID_FORM_DATA, "year": "2015"} to override individual fields.
VALID_FORM_DATA = {
    "username": "flounder14",
    "year": "2025",
    "sort_by": "playcount",
    "release_scope": "same",
    "min_plays": "10",
    "min_tracks": "3",
    "limit_results": "all",
}

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


#: The album object `fetch_spotify_album_details_batch` returns for "sp1" in
#: test_process_albums_persists_a_spotify_row_through_the_contract. Shared so
#: tests/test_provider_fixtures.py can check it for drift against the
#: doc-transcribed fixture without keeping its own stale copy (F-MAS-1).
SPOTIFY_ALBUM_DETAILS_MOCK = {
    "release_date": "2025-01-01",
    "images": [{"url": "https://img.example.com/a.jpg"}],
    "tracks": {"items": [{"name": "Track One", "duration_ms": 240000}]},
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
