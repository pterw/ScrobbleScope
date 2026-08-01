import os

# API keys from .env file
LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

# API Concurrency Configuration
# These values can be overridden via environment variables for tuning without code changes.
MAX_CONCURRENT_LASTFM = int(os.getenv("MAX_CONCURRENT_LASTFM", "10"))
LASTFM_REQUESTS_PER_SECOND = int(os.getenv("LASTFM_REQUESTS_PER_SECOND", "10"))

SPOTIFY_SEARCH_CONCURRENCY = int(os.getenv("SPOTIFY_SEARCH_CONCURRENCY", "10"))
SPOTIFY_BATCH_CONCURRENCY = int(os.getenv("SPOTIFY_BATCH_CONCURRENCY", "25"))
SPOTIFY_REQUESTS_PER_SECOND = int(os.getenv("SPOTIFY_REQUESTS_PER_SECOND", "10"))
SPOTIFY_SEARCH_RETRIES = int(os.getenv("SPOTIFY_SEARCH_RETRIES", "3"))
SPOTIFY_BATCH_RETRIES = int(os.getenv("SPOTIFY_BATCH_RETRIES", "3"))

# Global state tracking
REQUEST_CACHE_TIMEOUT = 3600  # Cache timeout in seconds (1 hour)
JOB_TTL_SECONDS = 2 * 60 * 60
# Default 5 (was 10 until 2026-07-31): the 2026-03-04 load test ran 2/3/5
# concurrent users clean while the 10-user run never completed. Each API
# has its own global throttle (`_LASTFM_THROTTLE` and `_SPOTIFY_THROTTLE`,
# utils.py:81-82), and each serializes throttle reservations with its shared
# lock. There is no per-job fairness. The binding constraint is the Last.fm
# scrobble-fetch
# phase: at 10 req/s shared across jobs, a cap of 5 averages ~2 req/s per
# job through that phase rather than guaranteeing it -- enough headroom on
# this single small Fly.io machine.
MAX_ACTIVE_JOBS = int(os.getenv("MAX_ACTIVE_JOBS", "5"))
METADATA_CACHE_TTL_DAYS = int(os.getenv("METADATA_CACHE_TTL_DAYS", "30"))

spotify_token_cache = {"token": None, "expires_at": 0}


def ensure_api_keys():
    """Raise ``RuntimeError`` if required API keys are missing."""
    if not (LASTFM_API_KEY and SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET):
        raise RuntimeError("Missing API keys! Check your .env file.")
