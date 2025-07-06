import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev")
    LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")
    SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
    SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
    DEBUG_MODE = os.getenv("DEBUG_MODE", "0") == "1"
