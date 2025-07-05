"""Application configuration module."""

from __future__ import annotations

import os


class Config:
    """Default configuration class."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev")
    CACHE_TYPE = "SimpleCache"
    CACHE_DEFAULT_TIMEOUT = 300
