"""Tests for scrobblescope.api_logging (Task 13, F-B23-6).

Every provider builds its aiohttp session through
``scrobblescope.utils.create_optimized_session``, so the trace hook it
attaches is exercised here against a real local server
(``aiohttp.test_utils.TestServer``) rather than against a mocked
``session.get`` -- the mocked-session pattern the existing provider tests
use never fires an aiohttp trace callback at all, which is exactly why
those tests are unaffected by this module.

The TestServer's host is always ``127.0.0.1``, which only exercises the
"unknown host named by its hostname" branch of the provider map. The four
real provider hosts, and the Last.fm-only ``method`` exception, are pure
functions of a host string / a ``yarl.URL`` and are tested directly below
without any network at all.
"""

import asyncio
import logging
import re
from contextlib import asynccontextmanager
from types import SimpleNamespace

import pytest
from aiohttp import ClientConnectorError, ClientTimeout, web
from aiohttp.test_utils import TestServer, unused_port
from yarl import URL

from scrobblescope.api_logging import (
    _call_outcome_line,
    _emit_summaries,
    _lastfm_method,
    _record,
    provider_for_host,
)
from scrobblescope.utils import create_optimized_session


async def _ok(request):
    return web.json_response({"ok": True})


async def _not_found(request):
    return web.Response(status=404)


async def _unavailable(request):
    return web.Response(status=503)


async def _rate_limited(request):
    return web.Response(status=429, headers={"Retry-After": "2"})


async def _slow(request):
    await asyncio.sleep(0.5)
    return web.json_response({"ok": True})


def _make_app():
    app = web.Application()
    app.router.add_get("/ok", _ok)
    app.router.add_get("/notfound", _not_found)
    app.router.add_get("/unavailable", _unavailable)
    app.router.add_get("/limited", _rate_limited)
    app.router.add_get("/slow", _slow)
    return app


@asynccontextmanager
async def _running_server():
    """Start a local aiohttp server for one test and tear it down after.

    A plain async context manager rather than a pytest fixture: nothing else
    in this suite uses an async fixture, and ``pytest-asyncio`` strict mode
    (the mode every other test file here relies on implicitly) would need a
    second decorator to support one.
    """
    server = TestServer(_make_app())
    await server.start_server()
    try:
        yield server
    finally:
        await server.close()


def _messages(caplog, level=None, contains=None):
    """Return the caplog messages matching *level* and/or a substring.

    Restricted to the root logger: ``TestServer`` runs a real local aiohttp
    web app, whose own ``aiohttp.access`` logger writes the full request
    line -- query string included -- for every request it serves. That is
    the server's own access log, not this module, and it would otherwise
    make the query-string adversarial test below see its own forbidden
    values and fail for the wrong reason.
    """
    records = [r for r in caplog.records if r.name == "root"]
    if level is not None:
        records = [r for r in records if r.levelno == level]
    messages = [r.getMessage() for r in records]
    if contains is not None:
        messages = [m for m in messages if contains in m]
    return messages


# --- Pure functions: the host map and the Last.fm method exception ---------


def test_provider_for_host_names_all_four_providers():
    assert provider_for_host("ws.audioscrobbler.com") == "Last.fm"
    assert provider_for_host("api.spotify.com") == "Spotify"
    assert provider_for_host("accounts.spotify.com") == "Spotify"
    assert provider_for_host("api.deezer.com") == "Deezer"
    assert provider_for_host("musicbrainz.org") == "MusicBrainz"


def test_provider_for_host_names_an_unknown_host_by_its_hostname():
    assert provider_for_host("127.0.0.1") == "127.0.0.1"
    assert provider_for_host("example.com") == "example.com"


def test_call_line_carries_the_lastfm_method_but_never_the_rest_of_the_query():
    """The one query value this module ever logs: Last.fm's own ``method``."""
    url = URL("https://ws.audioscrobbler.com/2.0/").with_query(
        api_key="SECRET-KEY", artist="Radiohead", method="user.getrecenttracks"
    )
    line = _call_outcome_line("Last.fm", "GET", url, "200", 12.3)

    assert "SECRET-KEY" not in line
    assert "Radiohead" not in line
    assert "method=user.getrecenttracks" in line
    assert "/2.0/" in line


def test_call_line_for_a_non_lastfm_provider_never_carries_a_method_value():
    url = URL("https://api.spotify.com/v1/search").with_query(q="Radiohead OK Computer")
    line = _call_outcome_line("Spotify", "GET", url, "200", 5.0)

    assert "Radiohead" not in line
    assert "method=" not in line


def test_lastfm_method_is_none_off_the_lastfm_host():
    url = URL("https://api.spotify.com/v1/search").with_query(
        method="user.getrecenttracks"
    )
    assert _lastfm_method("Spotify", url) is None


def test_lastfm_method_is_none_when_the_call_carries_no_method():
    url = URL("https://ws.audioscrobbler.com/2.0/").with_query(api_key="k")
    assert _lastfm_method("Last.fm", url) is None


# --- End-to-end: create_optimized_session's real trace hook ----------------


@pytest.mark.asyncio
async def test_a_200_logs_one_debug_line_and_nothing_at_info(caplog):
    with caplog.at_level(logging.DEBUG):
        async with _running_server() as server, create_optimized_session() as session:
            async with session.get(server.make_url("/ok")) as resp:
                await resp.read()
                assert resp.status == 200

    debug_lines = _messages(caplog, logging.DEBUG, "/ok")
    assert len(debug_lines) == 1
    assert "GET" in debug_lines[0]
    assert "200" in debug_lines[0]

    # The summary (INFO) never repeats the path, so filtering on "/ok"
    # isolates the per-call line from the end-of-session summary line.
    assert _messages(caplog, logging.INFO, "/ok") == []


@pytest.mark.asyncio
async def test_404_logs_at_info_and_503_logs_at_warning(caplog):
    with caplog.at_level(logging.DEBUG):
        async with _running_server() as server, create_optimized_session() as session:
            async with session.get(server.make_url("/notfound")) as resp:
                await resp.read()
            async with session.get(server.make_url("/unavailable")) as resp:
                await resp.read()

    notfound_lines = _messages(caplog, logging.INFO, "/notfound")
    assert len(notfound_lines) == 1
    assert "404" in notfound_lines[0]

    unavailable_lines = _messages(caplog, logging.WARNING, "/unavailable")
    assert len(unavailable_lines) == 1
    assert "503" in unavailable_lines[0]


@pytest.mark.asyncio
async def test_429_logs_at_warning_naming_its_retry_after_value(caplog):
    with caplog.at_level(logging.DEBUG):
        async with _running_server() as server, create_optimized_session() as session:
            async with session.get(server.make_url("/limited")) as resp:
                await resp.read()

    limited_lines = _messages(caplog, logging.WARNING, "/limited")
    assert len(limited_lines) == 1
    assert "429" in limited_lines[0]
    assert "Retry-After: 2" in limited_lines[0]


@pytest.mark.asyncio
async def test_a_timeout_logs_at_warning_and_still_reaches_the_caller(caplog):
    with caplog.at_level(logging.DEBUG):
        async with _running_server() as server, create_optimized_session() as session:
            with pytest.raises(TimeoutError):
                async with session.get(
                    server.make_url("/slow"), timeout=ClientTimeout(total=0.05)
                ):
                    pass

    timeout_lines = _messages(caplog, logging.WARNING, "/slow")
    assert len(timeout_lines) == 1
    assert "TimeoutError" in timeout_lines[0]


@pytest.mark.asyncio
async def test_a_connection_error_logs_at_warning_and_still_reaches_the_caller(caplog):
    bad_port = unused_port()
    with caplog.at_level(logging.DEBUG):
        async with create_optimized_session() as session:
            with pytest.raises(ClientConnectorError):
                async with session.get(f"http://127.0.0.1:{bad_port}/unreachable"):
                    pass

    error_lines = _messages(caplog, logging.WARNING, "/unreachable")
    assert len(error_lines) == 1
    assert "ClientConnectorError" in error_lines[0]


@pytest.mark.asyncio
async def test_never_logs_the_query_string_end_to_end(caplog):
    """Integration-level companion to the pure-function query-exclusion
    tests above: proves the real trace hook, not just the line-builder, never
    lets a query value through.
    """
    with caplog.at_level(logging.DEBUG):
        async with _running_server() as server, create_optimized_session() as session:
            async with session.get(
                server.make_url("/ok"),
                params={"api_key": "SECRET-KEY", "artist": "Radiohead"},
            ) as resp:
                await resp.read()

    all_text = "\n".join(_messages(caplog))
    assert "SECRET-KEY" not in all_text
    assert "Radiohead" not in all_text


@pytest.mark.asyncio
async def test_closing_the_session_logs_one_summary_per_provider(caplog):
    with caplog.at_level(logging.DEBUG):
        async with _running_server() as server, create_optimized_session() as session:
            for _ in range(2):
                async with session.get(server.make_url("/ok")) as resp:
                    await resp.read()
            async with session.get(server.make_url("/notfound")) as resp:
                await resp.read()

    summary_lines = _messages(caplog, logging.INFO, "127.0.0.1:")
    assert len(summary_lines) == 1
    message = summary_lines[0]
    assert message.startswith("127.0.0.1: 3 calls over")
    assert "2x200" in message
    assert "1x404" in message
    assert re.fullmatch(
        r"127\.0\.0\.1: 3 calls over \d+\.\d+s \(\d+\.\d+s in calls\) -- 2x200, 1x404",
        message,
    )


@pytest.mark.asyncio
async def test_a_session_that_made_no_calls_logs_no_summary(caplog):
    with caplog.at_level(logging.DEBUG):
        async with create_optimized_session():
            pass

    assert _messages(caplog, logging.INFO, "calls over") == []


# --- The summary's span vs. its time in calls -------------------------------
#
# These four drive ``_record``/``_emit_summaries`` directly against a plain
# stand-in session object (nothing but something ``setattr`` works on), so
# the span/in-calls arithmetic is checked deterministically instead of
# through real (and therefore only approximately controllable) timing --
# except the last, which proves the real trace hook wires real
# ``time.monotonic()`` readings through to the same arithmetic.


def test_span_is_not_the_sum_of_per_call_durations(caplog):
    """The owner's misreading: MusicBrainz is throttled a second apart by
    the global throttle in scrobblescope/utils.py, so its summary must not
    read as though the provider itself ran faster than that."""
    session = SimpleNamespace()
    with caplog.at_level(logging.DEBUG):
        _record(session, "X", "200", (0.1 - 0.0) * 1000, 0.0, 0.1)
        _record(session, "X", "200", (10.2 - 10.0) * 1000, 10.0, 10.2)
        _emit_summaries(session)

    summary_lines = _messages(caplog, logging.INFO, "X:")
    assert summary_lines == ["X: 2 calls over 10.2s (0.3s in calls) -- 2x200"]


def test_overlapping_calls_make_time_in_calls_exceed_the_span(caplog):
    """Concurrent calls (the Spotify search phase) can spend more total time
    in calls than the span they occupy; that is correct, not a bug."""
    session = SimpleNamespace()
    with caplog.at_level(logging.DEBUG):
        _record(session, "X", "200", 1000.0, 0.0, 1.0)
        _record(session, "X", "200", 1000.0, 0.0, 1.0)
        _emit_summaries(session)

    summary_lines = _messages(caplog, logging.INFO, "X:")
    assert summary_lines == ["X: 2 calls over 1.0s (2.0s in calls) -- 2x200"]


def test_an_exception_ending_after_the_last_success_extends_the_span(caplog):
    session = SimpleNamespace()
    with caplog.at_level(logging.DEBUG):
        _record(session, "X", "200", 100.0, 0.0, 0.1)
        _record(session, "X", "RuntimeError", 200.0, 0.2, 0.4)
        _emit_summaries(session)

    summary_lines = _messages(caplog, logging.INFO, "X:")
    assert summary_lines == [
        "X: 2 calls over 0.4s (0.3s in calls) -- 1x200, 1xRuntimeError"
    ]


@pytest.mark.asyncio
async def test_the_span_reflects_real_elapsed_time_between_calls(caplog):
    """End to end against the real session and trace hook: no upper bound on
    the span or the in-calls figure (timing-based upper bounds flake), just
    the lower bound the sleep between the two calls guarantees."""
    with caplog.at_level(logging.DEBUG):
        async with _running_server() as server, create_optimized_session() as session:
            async with session.get(server.make_url("/ok")) as resp:
                await resp.read()
            await asyncio.sleep(0.3)
            async with session.get(server.make_url("/ok")) as resp:
                await resp.read()

    summary_lines = _messages(caplog, logging.INFO, "127.0.0.1:")
    assert len(summary_lines) == 1
    match = re.search(r"over (?P<span>[\d.]+)s", summary_lines[0])
    assert match is not None
    assert float(match.group("span")) >= 0.3


@pytest.mark.asyncio
async def test_a_recording_failure_never_fails_the_request(caplog, monkeypatch):
    """A logging failure must never fail a request (task-13-brief.md:66).

    ``_record`` is the per-request recording every trace callback calls to
    fold a call's outcome into the session's tally; breaking it stands in
    for any callback-internal failure. The callbacks' own ``try/except`` is
    what is supposed to keep that failure from ever reaching the caller --
    proved end to end here: a real request through ``create_optimized_session``
    still returns its response normally, and an explicit ``close()`` on the
    session afterwards still does not raise.
    """

    def _boom(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr("scrobblescope.api_logging._record", _boom)

    with caplog.at_level(logging.DEBUG):
        async with _running_server() as server:
            session = create_optimized_session()
            try:
                async with session.get(server.make_url("/ok")) as resp:
                    body = await resp.json()
                    assert resp.status == 200
                    assert body == {"ok": True}
            finally:
                await session.close()
