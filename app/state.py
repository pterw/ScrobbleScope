"""Shared application state and synchronization primitives."""

import contextvars
import threading
from typing import Optional

import aiohttp


# Progress tracking
current_progress = {"progress": 0, "message": "Initializing...", "error": False}
progress_lock = threading.Lock()

# Unmatched album tracking
unmatched_lock = threading.Lock()
UNMATCHED: dict[str, dict] = {}

# Completed results cache
completed_results: dict[tuple, list] = {}

# Shared aiohttp session
http_session: Optional[aiohttp.ClientSession] = None

# Rate limiter contexts used by services
_lastfm_limiter = contextvars.ContextVar("lastfm_limiter", default=None)
_spotify_limiter = contextvars.ContextVar("spotify_limiter", default=None)


async def get_session() -> aiohttp.ClientSession:
    """Return the global ``aiohttp.ClientSession``, creating it if necessary."""

    global http_session
    if http_session is None or http_session.closed:
        http_session = aiohttp.ClientSession()
    return http_session


async def close_session() -> None:
    """Close the global ``aiohttp.ClientSession`` if open."""

    global http_session
    if http_session and not http_session.closed:
        await http_session.close()
    http_session = None


from aiolimiter import AsyncLimiter


def get_lastfm_limiter() -> AsyncLimiter:
    """Return a shared rate limiter for Last.fm requests."""
    limiter = _lastfm_limiter.get()
    if limiter is None:
        limiter = AsyncLimiter(20, 1)
        _lastfm_limiter.set(limiter)
    return limiter


def get_spotify_limiter() -> AsyncLimiter:
    """Return a shared rate limiter for Spotify requests."""
    limiter = _spotify_limiter.get()
    if limiter is None:
        limiter = AsyncLimiter(20, 1)
        _spotify_limiter.set(limiter)
    return limiter
