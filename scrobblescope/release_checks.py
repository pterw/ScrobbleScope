"""The live MusicBrainz correction worker (Task 9, Batch 22 WP-3).

Task 8 applies original-release findings that are *already* in
``original_release_cache``. This module is what puts them there: once a job's
results are on screen, it works through that job's albums in the background,
asks MusicBrainz for each one's original release date, and writes every
finding -- including "nothing found" -- back to the cache so the next job
reads it for free.

One worker thread serves the whole process, with its own event loop and a
FIFO queue of job ids. MusicBrainz allows one request per second per IP
(``scrobblescope.utils.get_musicbrainz_limiter`` enforces it process-wide),
so extra threads would only queue behind the limiter while multiplying the
DB connections and the ways a job's state can be raced.

Candidates per job, in this order and capped at ``MUSICBRAINZ_CHECKS_PER_JOB``:

1. the results, in rank order -- a correction can move one *out* of the
   target window;
2. the albums the release filter excluded whose provider year is **later**
   than that window -- a correction can move one *in*.

Nothing else can change: an original release date is never later than the
provider's own, so an album already dated at or before the window's end
cannot be corrected into it. Move-outs mark the result in place; move-ins are
counted on the job's stats, not inserted -- the results list a user is
already reading is never reordered underneath them.
"""

import asyncio
import logging
import queue
import sys
import threading

from scrobblescope.cache import (
    _batch_lookup_original_release,
    _batch_persist_original_release,
    _get_db_connection,
)
from scrobblescope.config import (
    MUSICBRAINZ_CHECKS_PER_JOB,
    MUSICBRAINZ_CONTACT,
    MUSICBRAINZ_ENABLED,
)
from scrobblescope.domain import normalize_name
from scrobblescope.musicbrainz import lookup_original_release
from scrobblescope.repositories import (
    get_job_context,
    set_job_release_check,
    update_job_result,
)
from scrobblescope.unmatched import REASON_RELEASE_SCOPE
from scrobblescope.utils import create_optimized_session

# Each result's ``release_check`` field, as the results page reads it.
CHECK_UNCHECKED = "unchecked"
CHECK_CONFIRMED = "confirmed"
CHECK_MOVED_OUT = "moved_out"
CHECK_UNAVAILABLE = "unavailable"

STATUS_RUNNING = "running"
STATUS_DONE = "done"
STATUS_SKIPPED = "skipped"

_JOB_QUEUE = queue.Queue()
_worker_lock = threading.Lock()
_worker_thread = None


def _state(status, checked=0, total=0, moved_out=0, moved_in=0):
    """Build the ``progress.stats.release_check`` payload."""
    return {
        "status": status,
        "checked": checked,
        "total": total,
        "moved_out": moved_out,
        "moved_in": moved_in,
    }


def _release_year(release_date):
    """Return the year in *release_date* as an int, or None if unusable."""
    if not release_date:
        return None
    text = str(release_date).split("-")[0]
    try:
        return int(text)
    except ValueError:
        return None


def _window_end(release_scope, year, decade=None, release_year=None):
    """Return the last year the release filter accepts, or None if unbounded.

    None means no exclusion can be moved in: either every year qualifies
    ("all"), or the scope's companion parameter is missing or unparseable and
    guessing a window would spend requests on albums that cannot qualify.
    """
    if release_scope == "same":
        return year if isinstance(year, int) else _release_year(year)
    if release_scope == "previous":
        base = year if isinstance(year, int) else _release_year(year)
        return None if base is None else base - 1
    if release_scope == "decade" and decade:
        start = _release_year(str(decade)[:3] + "0")
        return None if start is None else start + 9
    if release_scope == "custom" and release_year:
        return _release_year(release_year)
    return None


def _candidate(artist, album, kind):
    """Build one candidate record."""
    return {
        "key": normalize_name(artist, album),
        "artist": artist,
        "album": album,
        "kind": kind,
    }


def _select_candidates(context):
    """Return the ordered candidate list for the job described by *context*.

    Pure function: data-in, list-out, no I/O and no job mutation, so the
    ordering and exclusion rules can be tested without the worker around it.
    The cap and the cache short-circuit are applied by the caller, which is
    the only place that knows what is already cached.
    """
    params = context.get("params") or {}
    candidates = []
    seen = set()

    for result in context.get("results") or []:
        candidate = _candidate(
            result.get("artist", ""), result.get("album", ""), "result"
        )
        if candidate["key"] in seen:
            continue
        seen.add(candidate["key"])
        candidates.append(candidate)

    window_end = _window_end(
        params.get("release_scope"),
        params.get("year"),
        params.get("decade"),
        params.get("release_year"),
    )
    if window_end is None:
        return candidates

    for entry in (context.get("unmatched") or {}).values():
        if entry.get("reason_code") != REASON_RELEASE_SCOPE:
            continue
        provider_year = _release_year(entry.get("provider_release_date"))
        if provider_year is None or provider_year <= window_end:
            continue
        candidate = _candidate(
            entry.get("artist", ""), entry.get("album", ""), "unmatched"
        )
        if candidate["key"] in seen:
            continue
        seen.add(candidate["key"])
        candidates.append(candidate)

    return candidates


def _matches_window(original_release, params):
    """Return True when *original_release* still satisfies the job's filter.

    ``_matches_release_criteria`` is imported inside the function on purpose:
    it lives in the ``orchestrator`` package, which imports this module to
    enqueue jobs, and a module-level import here would close that cycle and
    make the two import orders behave differently.
    """
    from scrobblescope.orchestrator import _matches_release_criteria

    return _matches_release_criteria(
        original_release,
        params.get("release_scope"),
        params.get("year"),
        params.get("decade"),
        params.get("release_year"),
    )


def _resolve_cached(job_id, candidates, cached):
    """Split *candidates* into those already cached and those still to check.

    A cached row is a finding somebody already paid for, so it costs no
    request: a row carrying an original release date is why the result is in
    the list at all (Task 8 filtered on it), and a null row is a recorded
    "checked, nothing found". Both settle the result's ``release_check``
    immediately. A cached exclusion needs nothing -- Task 8 already applied
    the same finding when it built the results.
    """
    pending = []
    for candidate in candidates:
        hit = cached.get(candidate["key"])
        if hit is None:
            pending.append(candidate)
            continue
        if candidate["kind"] == "result":
            update_job_result(
                job_id,
                candidate["key"],
                {
                    "release_check": (
                        CHECK_CONFIRMED
                        if hit.get("original_release")
                        else CHECK_UNAVAILABLE
                    )
                },
            )
    return pending


def _mark_unchecked(job_id, candidates):
    """Set every result candidate's ``release_check`` back to "unchecked".

    Runs once, before any lookup, so a job that fails immediately after
    still shows "checking" on the results page rather than a stale value
    left over from a previous correction pass.
    """
    for candidate in candidates:
        if candidate["kind"] == "result":
            update_job_result(
                job_id, candidate["key"], {"release_check": CHECK_UNCHECKED}
            )


async def _lookup_cached(conn, candidates):
    """Return the cached original-release findings for *candidates*.

    Falls back to an empty dict -- every candidate pending -- when the cache
    read itself fails, so a transient DB hiccup costs requests instead of
    the whole job.
    """
    try:
        return await _batch_lookup_original_release(
            conn, [candidate["key"] for candidate in candidates]
        )
    except Exception as exc:
        logging.warning(f"Original-release cache lookup failed: {exc}")
        return {}


async def _check_pending_candidates(job_id, conn, pending, params, state):
    """Check *pending* candidates one at a time against MusicBrainz.

    Stops early, without raising, if the job disappears mid-run -- expired
    (``JOB_TTL_SECONDS``) or deleted -- since nobody can read the rest and
    the shared one-request-per-second budget is better spent elsewhere.
    """
    async with create_optimized_session() as session:
        for candidate in pending:
            if get_job_context(job_id) is None:
                logging.info(
                    f"Release checks stopped: job {job_id} is gone "
                    f"after {state['checked']}/{state['total']} checks."
                )
                return
            await _check_candidate(session, conn, job_id, candidate, params, state)
            set_job_release_check(job_id, state)


async def _check_candidate(session, conn, job_id, candidate, params, state):
    """Look one candidate up, persist the finding, and record the outcome."""
    artist_norm, album_norm = candidate["key"]
    mb_release_group, original_release = await lookup_original_release(
        session, candidate["artist"], candidate["album"]
    )

    # Persisted per check rather than batched at the end: the worker spends a
    # second per candidate and up to two hours per job, and a finding that is
    # only in memory when the process restarts is a request nobody gets back.
    try:
        await _batch_persist_original_release(
            conn, [(artist_norm, album_norm, mb_release_group, original_release)]
        )
    except Exception as exc:
        logging.warning(f"Original-release persist failed (non-fatal): {exc}")

    state["checked"] += 1
    in_window = bool(original_release) and _matches_window(original_release, params)

    if candidate["kind"] == "result":
        if not original_release:
            outcome = CHECK_UNAVAILABLE
        elif in_window:
            outcome = CHECK_CONFIRMED
        else:
            outcome = CHECK_MOVED_OUT
            state["moved_out"] += 1
        update_job_result(job_id, candidate["key"], {"release_check": outcome})
    elif in_window:
        state["moved_in"] += 1


async def run_release_checks(job_id):
    """Correct one job's release dates against MusicBrainz, in place.

    Returns without raising in every failure mode: a correction pass is an
    enhancement over results the user can already read, so nothing here may
    take the job down with it.
    """
    context = get_job_context(job_id)
    if context is None:
        return

    params = context.get("params") or {}
    candidates = _select_candidates(context)
    _mark_unchecked(job_id, candidates)

    if not MUSICBRAINZ_ENABLED:
        set_job_release_check(job_id, _state(STATUS_SKIPPED))
        return

    if not candidates:
        set_job_release_check(job_id, _state(STATUS_DONE))
        return

    conn = await _get_db_connection()
    if not conn:
        # Every finding belongs in original_release_cache; without it the
        # requests would buy one job's display and nothing for the next.
        logging.info("Release checks skipped: the cache DB is unavailable.")
        set_job_release_check(job_id, _state(STATUS_SKIPPED))
        return

    state = _state(STATUS_RUNNING)
    try:
        cached = await _lookup_cached(conn, candidates)
        pending = _resolve_cached(job_id, candidates, cached)[
            :MUSICBRAINZ_CHECKS_PER_JOB
        ]
        state["total"] = len(pending)
        set_job_release_check(job_id, state)

        if pending:
            await _check_pending_candidates(job_id, conn, pending, params, state)
    except Exception:
        logging.exception(f"Release checks failed for job {job_id}")
    finally:
        state["status"] = STATUS_DONE
        set_job_release_check(job_id, state)
        try:
            await conn.close()
        except Exception as exc:
            logging.warning(f"Closing the release-check DB connection failed: {exc}")


def _worker_loop():
    """Drain the job queue forever, one job at a time, in one event loop.

    On Windows the loop must be a ProactorEventLoop explicitly, for the same
    reason ``orchestrator.background_task`` says so: Werkzeug's reloader can
    leave a SelectorEventLoop as the policy in child threads, under which
    asyncpg mis-negotiates its PostgreSQL startup packet.
    """
    if sys.platform == "win32":
        loop = asyncio.ProactorEventLoop()
    else:
        loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        while True:
            job_id = _JOB_QUEUE.get()
            try:
                loop.run_until_complete(run_release_checks(job_id))
            except Exception:
                logging.exception(f"Release-check worker crashed on job {job_id}")
            finally:
                _JOB_QUEUE.task_done()
    finally:  # pragma: no cover - the loop above never exits in practice
        loop.close()


def _ensure_worker_started():
    """Start the single worker thread, unless it is already running."""
    global _worker_thread
    with _worker_lock:
        if _worker_thread is not None and _worker_thread.is_alive():
            return
        _worker_thread = threading.Thread(
            target=_worker_loop, name="release-checks", daemon=True
        )
        _worker_thread.start()


def enqueue_release_check(job_id):
    """Queue *job_id* for correction checks. Returns True when it was queued.

    Started lazily, on the first job that can actually use it, so a process
    that never runs one (a test session, a CLI script) never grows the
    thread. With MusicBrainz disabled or no contact address configured there
    is nothing to queue -- MusicBrainz blocks anonymous clients, so every
    request would be rejected -- and the job is marked ``skipped`` instead,
    which is what the results page needs to say so.
    """
    if not job_id:
        return False
    if not (MUSICBRAINZ_ENABLED and MUSICBRAINZ_CONTACT):
        set_job_release_check(job_id, _state(STATUS_SKIPPED))
        return False
    _ensure_worker_started()
    _JOB_QUEUE.put(job_id)
    return True
