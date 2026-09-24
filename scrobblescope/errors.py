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
    "no_scrobbles_in_range": {
        "source": "lastfm",
        "retryable": False,
        "message": "No scrobbles found in the last 365 days for '{username}'.",
    },
    # A fault that escaped every inner classifier is ours, not an upstream's.
    # Both background entry points publish it (F-SWE-5). Not retryable: an
    # immediate identical retry meets the same bug.
    "internal_error": {
        "source": "internal",
        "retryable": False,
        "message": "Something went wrong on our side and the search stopped. Please start a new search.",
    },
}


class SpotifyUnavailableError(RuntimeError):
    """Raised when Spotify metadata is required but unavailable for cache misses."""
