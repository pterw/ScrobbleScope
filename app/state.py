"""Shared application state and synchronization primitives."""

import contextvars
import threading

# Progress tracking
current_progress = {"progress": 0, "message": "Initializing...", "error": False}
progress_lock = threading.Lock()

# Unmatched album tracking
unmatched_lock = threading.Lock()
UNMATCHED: dict[str, dict] = {}

# Completed results cache
completed_results: dict[tuple, list] = {}

# Rate limiter contexts used by services
_lastfm_limiter = contextvars.ContextVar("lastfm_limiter", default=None)
_spotify_limiter = contextvars.ContextVar("spotify_limiter", default=None)
