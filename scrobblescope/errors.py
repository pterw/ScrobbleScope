"""Application-level error types and classified error codes.

Kept separate from domain.py so that normalization/business logic does not
import infrastructure concerns (user-facing messages, retryability flags).

This module is a leaf -- it imports nothing from the scrobblescope package.
"""

# Error classification codes for upstream failures.
# Each code maps to a source, retryability flag, and user-facing message.
ERROR_CODES = {
    "lastfm_unavailable": {
        "source": "lastfm",
        "retryable": True,
        "message": "Last.fm is currently unavailable. Please try again in a few minutes.",
    },
    "spotify_unavailable": {
        "source": "spotify",
        "retryable": True,
        "message": "Spotify is currently unavailable. Please try again in a few minutes.",
    },
    "spotify_rate_limited": {
        "source": "spotify",
        "retryable": True,
        "message": "Spotify rate limit reached. Please try again in a few minutes.",
    },
    "lastfm_rate_limited": {
        "source": "lastfm",
        "retryable": True,
        "message": "Last.fm rate limit reached. Please try again in a few minutes.",
    },
    "user_not_found": {
        "source": "lastfm",
        "retryable": False,
        "message": "User '{username}' was not found on Last.fm.",
    },
}


class SpotifyUnavailableError(RuntimeError):
    """Raised when Spotify metadata is required but unavailable for cache misses."""
