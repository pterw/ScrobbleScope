"""Application configuration and environment loading."""

import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration loaded from environment variables."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev")
    LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")
    SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
    SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")


def ensure_api_keys() -> None:
    """Raise an error if required API keys are missing."""

    if not all(
        [
            Config.LASTFM_API_KEY,
            Config.SPOTIFY_CLIENT_ID,
            Config.SPOTIFY_CLIENT_SECRET,
        ]
    ):
        raise RuntimeError("Missing API keys! Check your .env file.")
