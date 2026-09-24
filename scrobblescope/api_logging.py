"""Logs every provider HTTP call made through a session from
``create_optimized_session`` (``scrobblescope.utils``), in one format
regardless of which provider module issued it (Task 13, F-B23-6).

Every provider builds its session there -- ``lastfm.py``, ``spotify.py``'s
token fetch, ``orchestrator/__init__.py``'s Spotify/Deezer phase,
``release_checks.py`` for MusicBrainz, ``routes/api.py`` -- so one
``aiohttp.TraceConfig`` attached in that one place is enough; ``deezer.py``
and ``musicbrainz.py`` only ever call ``session.get`` on a session someone
else built, so they need no changes of their own.

A line never carries the query string: it can carry Last.fm's ``api_key``
and the artist/album search terms ``BATCH23_DEFINITION.md``'s Data handling
section keeps out of logs. The one exception is Last.fm's ``method`` query
parameter (for example ``user.getrecenttracks``), named explicitly because
the bare path (``/2.0/``) does not say which call it was. Request/response
bodies and headers are never logged, except the response's ``Retry-After``.

Every trace callback catches its own errors: a logging failure must never
fail the request it is describing.
"""

import logging
import time

from aiohttp import TraceConfig

# The hosts each provider's calls go to, per utils.create_optimized_session's
# callers: lastfm.py (Last.fm), spotify.py's token fetch and
# orchestrator/__init__.py's search/detail phase (Spotify), release_checks.py
# (MusicBrainz). deezer.py calls api.deezer.com on a session it is handed.
_PROVIDER_HOSTS = {
    "ws.audioscrobbler.com": "Last.fm",
    "api.spotify.com": "Spotify",
    "accounts.spotify.com": "Spotify",
    "api.deezer.com": "Deezer",
    "musicbrainz.org": "MusicBrainz",
}

# Where a session's per-provider tally lives, set on the ClientSession
# instance itself (the same object every trace callback for that session
# receives as its first argument).
_TALLY_ATTR = "_api_call_tally"


def provider_for_host(host):
    """Return the provider name for *host*, or *host* itself when unknown."""
    return _PROVIDER_HOSTS.get(host, host)


def _lastfm_method(provider, url):
    """Return Last.fm's ``method`` query value, or None elsewhere/absent.

    The only query value this module ever logs, and only for the one host
    whose bare path (``/2.0/``) does not say which call it was.
    """
    if provider != "Last.fm":
        return None
    return url.query.get("method")


def _level_for_status(status):
    """Return the logging level *status* earns (owner ruling, 2026-09-24)."""
    if status == 429 or status >= 500:
        return logging.WARNING
    if 200 <= status < 300:
        return logging.DEBUG
    return logging.INFO


def _call_outcome_line(provider, method, url, outcome, elapsed_ms, retry_after=None):
    """Build one per-call log line.

    *url* is a ``yarl.URL``; only its path is read here -- never the query
    string -- except *provider* "Last.fm", whose ``method`` value is named
    explicitly. *outcome* is a status code (as a string) or an exception
    class name.
    """
    line = f"{provider} {method} {url.path} -> {outcome} in {elapsed_ms:.0f}ms"
    lastfm_method = _lastfm_method(provider, url)
    if lastfm_method:
        line += f" method={lastfm_method}"
    if retry_after is not None:
        line += f" (Retry-After: {retry_after})"
    return line


def _elapsed_ms(start, end):
    """Return the milliseconds between two ``time.monotonic()`` readings."""
    return (end - start) * 1000


def _record(session, provider, outcome, elapsed_ms, start, end):
    """Fold one call's outcome into *session*'s per-provider tally.

    *start* and *end* are the same ``time.monotonic()`` readings the caller
    used to compute *elapsed_ms* -- one clock read per end event, so the
    per-call line's milliseconds and this tally's figures never drift apart.
    The tally keeps the earliest *start* and latest *end* seen for
    *provider*, so ``_emit_summaries`` can report the span those calls
    covered alongside the summed *elapsed_ms*.
    """
    tally = getattr(session, _TALLY_ATTR, None)
    if tally is None:
        tally = {}
        setattr(session, _TALLY_ATTR, tally)
    entry = tally.setdefault(
        provider,
        {
            "count": 0,
            "elapsed_ms": 0.0,
            "outcomes": {},
            "span_start": start,
            "span_end": end,
        },
    )
    entry["count"] += 1
    entry["elapsed_ms"] += elapsed_ms
    entry["outcomes"][outcome] = entry["outcomes"].get(outcome, 0) + 1
    if start < entry["span_start"]:
        entry["span_start"] = start
    if end > entry["span_end"]:
        entry["span_end"] = end


async def _on_request_start(session, trace_config_ctx, params):
    try:
        trace_config_ctx.start = time.monotonic()
    except Exception:  # noqa: BLE001 -- a trace hook must never fail the call
        logging.debug("api_logging: on_request_start failed", exc_info=True)


async def _on_request_end(session, trace_config_ctx, params):
    try:
        end = time.monotonic()
        start = trace_config_ctx.start
        elapsed_ms = _elapsed_ms(start, end)
        provider = provider_for_host(params.url.host)
        status = params.response.status
        retry_after = None
        if status == 429 or status >= 500:
            retry_after = params.response.headers.get("Retry-After")
        logging.log(
            _level_for_status(status),
            _call_outcome_line(
                provider,
                params.method,
                params.url,
                str(status),
                elapsed_ms,
                retry_after,
            ),
        )
        _record(session, provider, str(status), elapsed_ms, start, end)
    except Exception:  # noqa: BLE001 -- a trace hook must never fail the call
        logging.debug("api_logging: on_request_end failed", exc_info=True)


async def _on_request_exception(session, trace_config_ctx, params):
    try:
        end = time.monotonic()
        start = trace_config_ctx.start
        elapsed_ms = _elapsed_ms(start, end)
        provider = provider_for_host(params.url.host)
        exc_name = type(params.exception).__name__
        logging.warning(
            _call_outcome_line(
                provider, params.method, params.url, exc_name, elapsed_ms
            )
        )
        _record(session, provider, exc_name, elapsed_ms, start, end)
    except Exception:  # noqa: BLE001 -- a trace hook must never fail the call
        logging.debug("api_logging: on_request_exception failed", exc_info=True)


def build_trace_config():
    """Return a fresh ``TraceConfig`` that logs every call on the session it
    is attached to.

    Fresh per call: ``aiohttp.ClientSession`` freezes every trace config it
    is given at construction time, and a frozen one refuses new callbacks --
    so this cannot be a module-level singleton shared across sessions.
    """
    trace_config = TraceConfig()
    trace_config.on_request_start.append(_on_request_start)
    trace_config.on_request_end.append(_on_request_end)
    trace_config.on_request_exception.append(_on_request_exception)
    return trace_config


def _sorted_outcomes(outcomes):
    """Sort a tally's outcomes: status codes numerically, then exception
    class names alphabetically."""

    def sort_key(item):
        key = item[0]
        return (0, int(key)) if key.isdigit() else (1, key)

    return sorted(outcomes.items(), key=sort_key)


def _emit_summaries(session):
    """Log one INFO summary line per provider *session* called.

    Each line states two different numbers, not one: the *span* (wall time
    from that provider's earliest call start to its latest call end, both
    ``on_request_end`` and ``on_request_exception`` counting as an end) and
    the *time in calls* (that provider's per-call elapsed times summed).
    They answer different questions -- the span says how long the provider
    was being talked to; the time in calls says how much of that was spent
    waiting on it -- and they can diverge in either direction. Sequential
    calls throttled apart (MusicBrainz's one-request-per-second pacing, for
    example) give a span much larger than the time in calls. Calls issued
    concurrently (the Spotify search phase runs several in parallel) can
    give a time in calls that *exceeds* the span, since more than one call
    is in flight at once; that is correct and informative, not a bug.

    A session that made no calls has no tally entries and logs nothing.
    """
    tally = getattr(session, _TALLY_ATTR, None)
    if not tally:
        return
    for provider, entry in tally.items():
        try:
            outcomes = ", ".join(
                f"{count}x{key}" for key, count in _sorted_outcomes(entry["outcomes"])
            )
            span_s = entry["span_end"] - entry["span_start"]
            in_calls_s = entry["elapsed_ms"] / 1000
            logging.info(
                f"{provider}: {entry['count']} calls over {span_s:.1f}s "
                f"({in_calls_s:.1f}s in calls) -- {outcomes}"
            )
        except Exception:  # noqa: BLE001 -- a summary failure must not block close
            logging.debug(f"api_logging: summary failed for {provider}", exc_info=True)


def attach_summary_on_close(session):
    """Make *session* log its per-provider call summary the first time it
    closes, and return it.

    ``create_optimized_session()`` must keep returning a plain
    ``aiohttp.ClientSession`` used as ``async with``, so the summary needs a
    hook on close. A subclass would be the obvious one, but aiohttp 3.14
    fires a ``DeprecationWarning`` at class-definition time for any
    ``ClientSession`` subclass (``__init_subclass__`` in
    ``aiohttp.client``), which would show up as a warning on every test
    collecting this module. Rebinding ``close`` on the instance is the
    "or equivalent" the brief allows: it reaches the same one place --
    ``__aexit__`` and every explicit ``await session.close()`` both call
    ``session.close()`` -- without subclassing. ``close()`` is idempotent on
    the base class (``self.closed`` guards it), so this checks the same flag
    to emit the summary at most once.
    """
    original_close = session.close

    async def close():
        if not session.closed:
            _emit_summaries(session)
        await original_close()

    session.close = close
    return session
