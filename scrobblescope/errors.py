"""Application-level error types and classified error codes.

Kept separate from domain.py so that normalization/business logic does not
import infrastructure concerns (user-facing messages, retryability flags).

This module is a leaf -- it imports nothing from the scrobblescope package.
"""

# The phrase ``lastfm.py`` puts in the ValueError it raises for a private
# profile met inside a job; the classifier below looks for it.
PRIVATE_PROFILE_MARKER = "profile is private"

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
    # Met inside a job: the profile went private after the preflight passed.
    # Last.fm answers HTTP 403 (error 17). Not retryable: the owner must make
    # recent listening public first.
    "private_profile": {
        "source": "lastfm",
        "retryable": False,
        "message": "This Last.fm profile is private. Make recent listening public and try again.",
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
    # A job a restart left mid-run (``jobs.mark_interrupted``). Retryable: the
    # search itself was fine, the process holding it went away.
    "job_interrupted": {
        "source": "internal",
        "retryable": True,
        "message": "The search was interrupted by a restart. Please start a new search.",
    },
}


class SpotifyUnavailableError(RuntimeError):
    """Raised when Spotify metadata is required but unavailable for cache misses."""


def classify_exception_to_error_code(error_message):
    """Map an exception message to a classified error code, or None.

    The one classifier both background pipelines use to answer an
    unhandled exception (F-SWE-5): the album pipeline's ``_fetch_and_process``
    and the heatmap pipeline's ``_report_heatmap_failure`` each call this
    before falling back to ``internal_error``, so a known upstream failure
    (a Last.fm 404, a provider's rate limit) is blamed on the source that
    actually failed rather than on the app.

    Returns 'spotify_rate_limited', 'lastfm_rate_limited', 'private_profile',
    'user_not_found', or None for unclassified errors.
    """
    if "Too Many Requests" in error_message:
        if "spotify" in error_message.lower():
            return "spotify_rate_limited"
        return "lastfm_rate_limited"
    if PRIVATE_PROFILE_MARKER in error_message:
        return "private_profile"
    if "not found" in error_message.lower() and "user" in error_message.lower():
        return "user_not_found"
    return None
