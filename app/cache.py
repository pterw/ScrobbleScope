"""In-memory caching helpers for API requests."""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional, Tuple

# Cache dictionary maps keys to ``(timestamp, data)`` tuples
REQUEST_CACHE: Dict[str, Tuple[float, Any]] = {}

# How long cached responses remain valid
REQUEST_CACHE_TIMEOUT = 3600


def get_cache_key(url: str, params: Optional[Dict[str, Any]] = None) -> str:
    """Return a unique cache key for the given request."""
    key = url
    if params:
        key += "_" + "_".join(f"{k}:{v}" for k, v in sorted(params.items()))
    return key


def get_cached_response(
    url: str, params: Optional[Dict[str, Any]] = None
) -> Optional[Any]:
    """Return cached data for the request if it hasn't expired."""
    key = get_cache_key(url, params)
    if key in REQUEST_CACHE:
        timestamp, data = REQUEST_CACHE[key]
        if time.time() - timestamp < REQUEST_CACHE_TIMEOUT:
            logging.debug("Cache hit for %s", key)
            return data
    return None


def set_cached_response(
    url: str, data: Any, params: Optional[Dict[str, Any]] = None
) -> None:
    """Store ``data`` in the cache for the given request."""
    key = get_cache_key(url, params)
    REQUEST_CACHE[key] = (time.time(), data)
