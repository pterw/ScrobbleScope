"""The Last.fm pre-check: one answer the album, heatmap and validate routes share.

Before a job starts, three routes ask Last.fm the same two questions: does the
user exist, and is recent listening public? Each used to carry its own copy and
its own idea of what a failure meant; the album route let an outage through and
started a job that was bound to fail. ``check_lastfm_user`` asks in the owner's
order (existence first, so a name Last.fm does not know is never given a
privacy verdict) and answers with one ``Verdict``. A lookup that cannot answer,
including one that exceeds ``LASTFM_PRECHECK_TIMEOUT_SECONDS``, is
``UNAVAILABLE``: the caller refuses retryably and starts nothing.

The two lookups are read from the ``routes`` facade at call time (see
``scrobblescope/routes/__init__.py``), so the test suite's patches at
``scrobblescope.routes._check_user_exists`` keep working.

A failure is logged by class only and never with the listener's name: the name
is listener data, and the exception text can carry the provider's URL.
"""

import enum
from dataclasses import dataclass

from scrobblescope import routes as _routes
from scrobblescope.utils import log_failure

#: What a listener is told when Last.fm could not answer. Retryable.
UNAVAILABLE_MESSAGE = "Validation service unavailable. Try again."


class Verdict(enum.Enum):
    """What Last.fm said about a name."""

    PUBLIC = "public"
    MISSING = "missing"
    PRIVATE = "private"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class UserCheck:
    """The pre-check's answer; ``registered_year`` is set only for ``PUBLIC``."""

    verdict: Verdict
    registered_year: int | None = None


def not_found_message(username):
    """Return the sentence shown when Last.fm does not know *username*."""
    return f"User '{username}' was not found on Last.fm."


def _read_existence(info):
    """Return ``(exists, registered_year)`` from the existence answer.

    Raises ``ValueError`` when the answer is not the expected shape: not a
    mapping, no boolean ``exists``, or a ``registered_year`` that is neither an
    int nor None (a missing ``registered_year`` is "unknown", not malformed).
    """
    if not isinstance(info, dict):
        raise ValueError("existence answer is not a mapping")
    exists = info.get("exists")
    if not isinstance(exists, bool):
        raise ValueError("existence answer has no boolean 'exists'")
    registered_year = info.get("registered_year")
    if registered_year is not None and (
        isinstance(registered_year, bool) or not isinstance(registered_year, int)
    ):
        raise ValueError("registered_year is not a number")
    return exists, registered_year


def check_lastfm_user(username):
    """Ask Last.fm whether *username* exists and is public; return a ``UserCheck``.

    Existence is asked first and a missing user ends the check, so the privacy
    lookup is never made for a name Last.fm does not know. An exception from
    either lookup (an HTTP failure, a bad body, a timeout) or an existence
    answer of the wrong shape is ``UNAVAILABLE``, never ``PUBLIC``: a check
    that could not answer must not let a job start, and a bad body must not
    become a 500.
    """
    try:
        exists, registered_year = _read_existence(_routes._check_user_exists(username))
    except Exception:  # noqa: BLE001 -- logged by log_failure
        log_failure("User existence check failed")
        return UserCheck(Verdict.UNAVAILABLE)

    if not exists:
        return UserCheck(Verdict.MISSING)

    try:
        public = _routes._check_profile_is_public(username)
    except Exception:  # noqa: BLE001 -- logged by log_failure
        log_failure("Profile privacy check failed")
        return UserCheck(Verdict.UNAVAILABLE)

    if not public:
        return UserCheck(Verdict.PRIVATE)
    return UserCheck(Verdict.PUBLIC, registered_year)
