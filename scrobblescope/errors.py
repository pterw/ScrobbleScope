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
    # Met inside a job: the profile went private after the preflight passed.
    # Last.fm answers error 17 (in the body of an HTTP 403 or a 200). Not
    # retryable: the owner must make recent listening public first.
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


class ClassifiedError(Exception):
    """An exception that names its own ``ERROR_CODES`` code.

    Raised where the HTTP status is known (the provider clients), so the
    classifier never has to guess from message text. Its message carries the
    code only: nothing a provider or a listener typed.
    """

    code = None

    def __init__(self, message=None):
        super().__init__(message or self.code)


class UserNotFoundError(ClassifiedError):
    """Last.fm answered 404: the account does not exist."""

    code = "user_not_found"


class PrivateProfileError(ClassifiedError):
    """Last.fm answered error 17: recent listening is not public."""

    code = "private_profile"


class ProviderError(ClassifiedError):
    """A provider that could not be read: ``kind`` is ``unavailable`` or ``rate_limited``.

    ``source`` is the provider (``spotify``, ``deezer``, ``musicbrainz``, ...).
    A provider with no ``ERROR_CODES`` entry (Deezer, MusicBrainz) never fails
    a job: its callers catch this and degrade. Spotify's callers catch it too:
    an album whose search went unanswered falls back to Deezer, and the job
    fails only under the aggregate rule in ``_fetch_spotify_misses``.
    """

    def __init__(self, source, kind):
        self.source = source
        self.kind = kind
        self.code = f"{source}_{kind}"
        super().__init__(self.code)


def provider_failure(source):
    """Return a ``retry_with_semaphore`` ``failure`` factory for one provider.

    The helper calls it with ``"rate_limited"`` or ``"unavailable"`` once a
    call could not be answered, and raises what it returns: a provider that
    refused (a throttle, a 5xx, a timeout) must not read as one that answered
    "no match".
    """

    def failure(kind):
        return ProviderError(source, kind)

    return failure


def classify_exception_to_error_code(exc):
    """Map an exception to a classified error code, or None.

    The one classifier both background pipelines use to answer an
    unhandled exception (F-SWE-5): the album pipeline's ``_fetch_and_process``
    and the heatmap pipeline's ``_report_heatmap_failure`` each call this
    before falling back to ``internal_error``. Classification is by exception
    TYPE, never by message text: a ``ClassifiedError`` whose code is in
    ``ERROR_CODES`` answers with that code and ``SpotifyUnavailableError``
    with ``spotify_unavailable``. Anything else is our bug and returns None,
    which both callers publish as ``internal_error``.
    """
    if isinstance(exc, SpotifyUnavailableError):
        return "spotify_unavailable"
    if isinstance(exc, ClassifiedError) and exc.code in ERROR_CODES:
        return exc.code
    return None
