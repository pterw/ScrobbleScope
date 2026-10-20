"""The shared Last.fm pre-check: one answer for the album, heatmap and validate routes."""

import asyncio
import logging
import time
from unittest.mock import patch

import pytest

from scrobblescope import routes
from scrobblescope.routes.precheck import (
    UNAVAILABLE_MESSAGE,
    UserCheck,
    Verdict,
    check_lastfm_user,
    not_found_message,
)

KNOWN = {"exists": True, "registered_year": 2016}


def test_an_existing_public_user_is_public_and_carries_the_registration_year():
    with (
        patch("scrobblescope.routes._check_user_exists", return_value=KNOWN),
        patch("scrobblescope.routes._check_profile_is_public", return_value=True),
    ):
        assert check_lastfm_user("flounder14") == UserCheck(Verdict.PUBLIC, 2016)


def test_a_missing_user_is_missing_and_privacy_is_never_asked():
    """Existence first (owner's order): a ghost gets "not found", not a privacy verdict."""
    with (
        patch(
            "scrobblescope.routes._check_user_exists",
            return_value={"exists": False, "registered_year": None},
        ),
        patch("scrobblescope.routes._check_profile_is_public") as privacy,
    ):
        assert check_lastfm_user("ghost") == UserCheck(Verdict.MISSING)

    privacy.assert_not_called()


def test_an_existing_private_user_is_private():
    with (
        patch("scrobblescope.routes._check_user_exists", return_value=KNOWN),
        patch("scrobblescope.routes._check_profile_is_public", return_value=False),
    ):
        assert check_lastfm_user("private_user") == UserCheck(Verdict.PRIVATE)


@pytest.mark.parametrize(
    "answer",
    [
        None,
        [],
        {},
        {"registered_year": 2016},
        {"exists": "yes", "registered_year": 2016},
        {"exists": None, "registered_year": 2016},
        {"exists": True, "registered_year": "2016"},
    ],
    ids=[
        "none",
        "not-a-mapping",
        "empty",
        "no-exists-key",
        "exists-not-a-bool",
        "exists-null",
        "year-not-a-number",
    ],
)
def test_a_malformed_existence_answer_is_unavailable_never_an_error(answer):
    """
    GIVEN Last.fm answers the existence check with a body that is not the
    expected shape (a missing key, a wrong type)
    WHEN the pre-check reads it
    THEN the answer is UNAVAILABLE (retryable) and privacy is not asked; it is
    neither an unhandled exception (a 500) nor a guess that the user exists.

    Mutation: read `info["exists"]` outside the try, and the rows without the
    key raise KeyError; read it with `info.get("exists")` and the
    no-exists-key row becomes MISSING.
    """
    with (
        patch("scrobblescope.routes._check_user_exists", return_value=answer),
        patch("scrobblescope.routes._check_profile_is_public") as privacy,
    ):
        assert check_lastfm_user("flounder14") == UserCheck(Verdict.UNAVAILABLE)

    privacy.assert_not_called()


def test_an_unreported_registration_year_is_unknown_not_malformed():
    """Last.fm may not report a registration year; that is no outage."""
    with (
        patch("scrobblescope.routes._check_user_exists", return_value={"exists": True}),
        patch("scrobblescope.routes._check_profile_is_public", return_value=True),
    ):
        assert check_lastfm_user("flounder14") == UserCheck(Verdict.PUBLIC, None)


def test_an_outage_on_the_existence_check_is_unavailable_and_privacy_is_not_asked():
    with (
        patch(
            "scrobblescope.routes._check_user_exists", side_effect=RuntimeError("down")
        ),
        patch("scrobblescope.routes._check_profile_is_public") as privacy,
    ):
        assert check_lastfm_user("flounder14") == UserCheck(Verdict.UNAVAILABLE)

    privacy.assert_not_called()


def test_an_outage_on_the_privacy_check_is_unavailable_never_public():
    """Fail closed: a check that could not answer must not let a job start.

    Mutation: return PUBLIC from the privacy `except` branch and this fails.
    """
    with (
        patch("scrobblescope.routes._check_user_exists", return_value=KNOWN),
        patch(
            "scrobblescope.routes._check_profile_is_public",
            side_effect=RuntimeError("down"),
        ),
    ):
        assert check_lastfm_user("flounder14") == UserCheck(Verdict.UNAVAILABLE)


def test_the_messages_the_routes_show():
    assert UNAVAILABLE_MESSAGE == "Validation service unavailable. Try again."
    assert not_found_message("flounder14") == (
        "User 'flounder14' was not found on Last.fm."
    )


def test_a_failed_check_logs_the_class_and_never_the_listeners_name(caplog):
    """
    GIVEN a check that raises with the listener's name and a URL in its text
    WHEN the pre-check fails
    THEN no WARNING-or-higher line carries the name or the text, only the class.

    Mutation: log the username in precheck's failure line and this fails.
    """
    secret = "zqxv_listener"
    with (
        patch(
            "scrobblescope.routes._check_user_exists",
            side_effect=RuntimeError(f"failed url=https://x/?user={secret}"),
        ),
        caplog.at_level(logging.DEBUG),
    ):
        check_lastfm_user(secret)

    loud = [r.getMessage() for r in caplog.records if r.levelno >= logging.WARNING]
    assert any("RuntimeError" in line for line in loud)
    assert not any(secret in line for line in loud)


@pytest.mark.parametrize(
    "check, provider",
    [
        ("_check_user_exists", "check_user_exists"),
        ("_check_profile_is_public", "check_profile_is_public"),
    ],
)
def test_a_stalled_last_fm_lookup_gives_up_within_the_precheck_budget(check, provider):
    """
    GIVEN Last.fm accepts the request and never answers
    WHEN the facade's lookup runs
    THEN it raises TimeoutError within the pre-check budget, not after the
    session's 30 seconds.

    Mutation: drop `timeout=` from either facade function and that row waits
    out the stall and returns instead of raising.
    """

    async def stalled(_username):
        await asyncio.sleep(3)

    with (
        patch(f"scrobblescope.routes.{provider}", stalled),
        patch("scrobblescope.routes.LASTFM_PRECHECK_TIMEOUT_SECONDS", 0.05),
    ):
        started = time.monotonic()
        with pytest.raises(TimeoutError):
            getattr(routes, check)("someone")

    assert time.monotonic() - started < 1.5
