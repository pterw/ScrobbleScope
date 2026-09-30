import asyncio
import logging

import pytest

from scrobblescope.errors import ProviderError
from scrobblescope.utils import parse_retry_after, retry_with_semaphore


@pytest.mark.asyncio
async def test_returns_result_on_first_success():
    """Inner function succeeds immediately: result returned, no retries."""

    async def inner():
        return ("data", None)

    result = await retry_with_semaphore(
        inner,
        retries=3,
        is_done=lambda t: t[0] is not None,
        get_retry_after=lambda t: t[1],
        extract_result=lambda t: t[0],
        default=None,
        backoff=lambda _: 0,
    )
    assert result == "data"


@pytest.mark.asyncio
async def test_retries_on_transient_failure_then_succeeds():
    """Inner fails twice, succeeds third: result returned."""
    calls = []

    async def inner():
        calls.append(1)
        if len(calls) < 3:
            return (None, None)
        return ("ok", None)

    result = await retry_with_semaphore(
        inner,
        retries=5,
        is_done=lambda t: t[0] is not None,
        get_retry_after=lambda t: t[1],
        extract_result=lambda t: t[0],
        default="default",
        backoff=lambda _: 0,
    )
    assert result == "ok"
    assert len(calls) == 3


@pytest.mark.asyncio
async def test_returns_default_after_all_retries_exhausted(caplog):
    """Inner always fails: default returned, exhaustion logged."""

    async def inner():
        return (None, None)

    with caplog.at_level(logging.ERROR):
        result = await retry_with_semaphore(
            inner,
            retries=2,
            is_done=lambda t: t[0] is not None,
            get_retry_after=lambda t: t[1],
            extract_result=lambda t: t[0],
            default="fallback",
            backoff=lambda _: 0,
            error_label="test op",
        )
    assert result == "fallback"
    assert "All 2 retries failed for test op" in caplog.text


@pytest.mark.asyncio
async def test_respects_retry_after_from_inner():
    """When inner returns retry_after, loop sleeps and retries."""
    calls = []

    async def inner():
        calls.append(1)
        if len(calls) == 1:
            return (None, 0.001, False)  # rate limited
        return ("done", None, True)

    result = await retry_with_semaphore(
        inner,
        retries=3,
        is_done=lambda t: t[2],
        get_retry_after=lambda t: t[1],
        extract_result=lambda t: t[0],
        default=None,
        backoff=lambda _: 0,
    )
    assert result == "done"
    assert len(calls) == 2


@pytest.mark.asyncio
async def test_jitter_added_to_retry_after():
    """When jitter is provided, it's added to retry_after sleep."""
    slept = []
    original_sleep = asyncio.sleep

    async def patched_sleep(seconds):
        slept.append(seconds)
        await original_sleep(0)  # don't actually wait

    calls = []

    async def inner():
        calls.append(1)
        if len(calls) == 1:
            return (None, 1.0, False)
        return ("ok", None, True)

    # Monkeypatch asyncio.sleep in the utils module
    import scrobblescope.utils as utils_mod

    orig = utils_mod.asyncio.sleep
    utils_mod.asyncio.sleep = patched_sleep
    try:
        await retry_with_semaphore(
            inner,
            retries=3,
            is_done=lambda t: t[2],
            get_retry_after=lambda t: t[1],
            extract_result=lambda t: t[0],
            default=None,
            backoff=lambda _: 0,
            jitter=lambda _a: 0.05,
        )
    finally:
        utils_mod.asyncio.sleep = orig

    # First sleep should be retry_after + jitter = 1.05
    assert len(slept) >= 1
    assert abs(slept[0] - 1.05) < 0.001


@pytest.mark.asyncio
async def test_reraise_propagates_specified_exception():
    """Exceptions in reraise tuple propagate immediately, no retries."""
    calls = []

    async def inner():
        calls.append(1)
        raise ValueError("fatal")

    with pytest.raises(ValueError, match="fatal"):
        await retry_with_semaphore(
            inner,
            retries=5,
            is_done=lambda t: True,
            get_retry_after=lambda t: None,
            extract_result=lambda t: t,
            default=None,
            backoff=lambda _: 0,
            reraise=(ValueError,),
        )
    assert len(calls) == 1  # no retries after ValueError


@pytest.mark.asyncio
async def test_semaphore_gates_inner_calls():
    """When semaphore is provided, inner runs inside semaphore context."""
    sem = asyncio.Semaphore(1)
    inside_sem = []

    async def inner():
        # If semaphore is properly acquired, it should appear locked here
        acquired = sem.locked()
        inside_sem.append(acquired)
        return ("ok", None)

    result = await retry_with_semaphore(
        inner,
        retries=1,
        semaphore=sem,
        is_done=lambda t: t[0] is not None,
        get_retry_after=lambda t: t[1],
        extract_result=lambda t: t[0],
        default=None,
        backoff=lambda _: 0,
    )
    assert result == "ok"
    assert inside_sem == [True]


@pytest.mark.asyncio
async def test_constant_float_backoff_accepted():
    """backoff may be a plain float instead of a callable."""
    calls = []

    async def inner():
        calls.append(1)
        if len(calls) < 2:
            return (None, None)
        return ("ok", None)

    result = await retry_with_semaphore(
        inner,
        retries=3,
        is_done=lambda t: t[0] is not None,
        get_retry_after=lambda t: t[1],
        extract_result=lambda t: t[0],
        default="fallback",
        backoff=0,  # constant float, not a callable
    )
    assert result == "ok"
    assert len(calls) == 2


def _record_sleeps(monkeypatch):
    """Patch utils' asyncio.sleep to record requested durations, not wait."""
    slept = []

    async def fake_sleep(seconds):
        slept.append(seconds)

    monkeypatch.setattr("scrobblescope.utils.asyncio.sleep", fake_sleep)
    return slept


def _kwargs(**over):
    base = dict(
        retries=3,
        is_done=lambda t: t[2],
        get_retry_after=lambda t: t[1],
        extract_result=lambda t: t[0],
        default="default",
        backoff=lambda _: 0.5,
        error_label="cap op",
    )
    base.update(over)
    return base


def test_max_retry_after_default_is_30():
    from scrobblescope import config

    assert config.MAX_RETRY_AFTER_SECONDS == 30


@pytest.mark.asyncio
async def test_retry_after_above_cap_gives_up_without_sleeping(monkeypatch, caplog):
    slept = _record_sleeps(monkeypatch)
    calls = []

    async def inner():
        calls.append(1)
        return (None, 86400, False)

    with caplog.at_level(logging.WARNING):
        result = await retry_with_semaphore(inner, **_kwargs())

    assert result == "default"
    assert len(calls) == 1
    assert slept == []
    assert "86400" in caplog.text
    assert "30s cap" in caplog.text
    assert "cap op" in caplog.text


@pytest.mark.asyncio
async def test_retry_after_at_cap_sleeps_and_retries(monkeypatch):
    slept = _record_sleeps(monkeypatch)
    calls = []

    async def inner():
        calls.append(1)
        if len(calls) == 1:
            return (None, 30, False)
        return ("ok", None, True)

    result = await retry_with_semaphore(inner, **_kwargs())

    assert result == "ok"
    assert len(calls) == 2
    assert slept == [30]


@pytest.mark.asyncio
async def test_cap_is_read_from_utils_config_value(monkeypatch):
    slept = _record_sleeps(monkeypatch)
    monkeypatch.setattr("scrobblescope.utils.MAX_RETRY_AFTER_SECONDS", 5)
    calls = []

    async def inner():
        calls.append(1)
        return (None, 10, False)

    result = await retry_with_semaphore(inner, **_kwargs())

    assert result == "default"
    assert len(calls) == 1
    assert slept == []


@pytest.mark.asyncio
async def test_transient_failures_sleep_between_tries_not_after_last(monkeypatch):
    slept = _record_sleeps(monkeypatch)
    calls = []

    async def inner():
        calls.append(1)
        return (None, None, False)

    result = await retry_with_semaphore(inner, **_kwargs())

    assert result == "default"
    assert len(calls) == 3
    assert slept == [0.5, 0.5]


@pytest.mark.asyncio
async def test_rate_limit_on_final_attempt_does_not_sleep(monkeypatch):
    slept = _record_sleeps(monkeypatch)
    calls = []

    async def inner():
        calls.append(1)
        return (None, 10, False)

    result = await retry_with_semaphore(inner, **_kwargs(retries=2))

    assert result == "default"
    assert len(calls) == 2
    assert slept == [10]


@pytest.mark.asyncio
async def test_failure_lines_name_the_operation_and_class_never_the_message(caplog):
    """
    GIVEN a callable that raises an error whose message carries a request URL
        with an album and artist in its query (as aiohttp's do)
    WHEN retries run out
    THEN every line names the operation key and the exception class, and no
        record at any level carries the message.
    """
    secret = "https://api.example.com/search?q=Wjkl+Zqxv"

    async def inner():
        raise ConnectionError(f"cannot reach url='{secret}'")

    with caplog.at_level(logging.DEBUG):
        result = await retry_with_semaphore(
            inner,
            retries=2,
            is_done=lambda t: True,
            get_retry_after=lambda t: None,
            extract_result=lambda t: t,
            default="fallback",
            backoff=lambda _: 0,
            error_label="spotify.search",
        )

    assert result == "fallback"
    assert "Error in spotify.search: ConnectionError" in caplog.text
    assert "All 2 retries failed for spotify.search" in caplog.text
    for record in caplog.records:
        assert "Wjkl" not in record.getMessage()
        assert "Zqxv" not in record.getMessage()
        assert "api.example.com" not in record.getMessage()


# --- typed failure instead of the miss value (Codex 4140219720) --------------


def _spotify_failure(kind):
    return ProviderError("spotify", kind)


@pytest.mark.asyncio
async def test_retry_after_above_cap_raises_the_typed_failure_not_the_default(
    monkeypatch,
):
    """
    GIVEN a call throttled with a Retry-After above the cap and a ``failure``
    WHEN the retry helper gives up
    THEN it raises the rate-limited failure after one call, instead of
    returning ``default``, which the caller would read as "no match".
    """
    slept = _record_sleeps(monkeypatch)
    calls = []

    async def inner():
        calls.append(1)
        return (None, 86400, False)

    with pytest.raises(ProviderError) as excinfo:
        await retry_with_semaphore(inner, **_kwargs(failure=_spotify_failure))

    assert excinfo.value.code == "spotify_rate_limited"
    assert len(calls) == 1
    assert slept == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("outcome", "code"),
    [
        ("raise", "spotify_unavailable"),
        ("not_done", "spotify_unavailable"),
        ("throttled", "spotify_rate_limited"),
    ],
)
async def test_exhausted_retries_raise_the_typed_failure(monkeypatch, outcome, code):
    """
    GIVEN a call that keeps timing out, failing, or being throttled
    WHEN every retry is spent and a ``failure`` is given
    THEN it raises unavailable for a timeout or a bad answer and rate_limited
    when the last attempt was a 429; the default is not returned.
    """
    _record_sleeps(monkeypatch)

    async def inner():
        if outcome == "raise":
            raise TimeoutError
        if outcome == "throttled":
            return (None, 5, False)
        return (None, None, False)

    with pytest.raises(ProviderError) as excinfo:
        await retry_with_semaphore(inner, **_kwargs(failure=_spotify_failure))

    assert excinfo.value.code == code


@pytest.mark.asyncio
async def test_a_failure_factory_can_decline_and_the_default_is_returned(monkeypatch):
    """
    GIVEN a ``failure`` factory that returns None for the kind that occurred
    WHEN the retries are spent
    THEN the helper returns ``default`` as it always did.
    """
    _record_sleeps(monkeypatch)

    async def inner():
        return (None, None, False)

    result = await retry_with_semaphore(inner, **_kwargs(failure=lambda kind: None))

    assert result == "default"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("7", 7),
        ("0", 0),
        (None, 1),
        ("", 1),
        ("Wed, 21 Oct 2026 07:28:00 GMT", 1),
        ("soon", 1),
        ("-5", 1),
    ],
)
def test_parse_retry_after_never_raises(value, expected):
    """A malformed or missing Retry-After becomes the default, never an error."""
    assert parse_retry_after(value) == expected


@pytest.mark.asyncio
async def test_an_exception_that_is_not_a_provider_failure_propagates(monkeypatch):
    """
    GIVEN a ``failure`` factory and a callable that raises a programming error
    WHEN the retry helper runs
    THEN the error propagates after one call, un-retried and unlabelled, so
    it is classified as ours (internal_error) and not as a provider outage;
    a network failure (TimeoutError, aiohttp.ClientError) is still retried.
    """
    _record_sleeps(monkeypatch)
    calls = []

    async def inner():
        calls.append(1)
        raise AttributeError("'list' object has no attribute 'get'")

    with pytest.raises(AttributeError):
        await retry_with_semaphore(inner, **_kwargs(failure=_spotify_failure))

    assert len(calls) == 1
