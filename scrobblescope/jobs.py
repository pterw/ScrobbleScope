"""The job module: the lifecycle of one search job, over a storage seam.

A job is born (``create``), advances through the pipeline (``start``,
``advance``, ``report_phase``), collects facts on the way (``record_stat``,
``record_unmatched``) and ends exactly one way: ``succeed`` with results, or
``fail`` with a classified error. The rules of that life live here, not in the
callers: a finished job holds results *or* an error, never both, and a write
is the only thing that renews a job's lease. Callers say what happened; this
module decides what state that leaves behind.

Storage sits behind ``JobStore``. ``MemoryJobStore`` (a dict, one lock) is the
only adapter today; a second one only has to honour the same contract and pass
``tests/test_jobs.py``. The default store is process-wide; ``use_store`` swaps
it (tests, and the future database adapter).

    jobs <- config, errors
"""

import logging
import threading
import time
from collections import namedtuple
from collections.abc import Callable
from typing import Protocol
from uuid import uuid4

from scrobblescope.config import JOB_TTL_SECONDS
from scrobblescope.errors import ERROR_CODES

# ---------------------------------------------------------------------------
# Progress vocabulary
# ---------------------------------------------------------------------------

# A band is the slice of the 0-100 bar one counted phase owns.
Band = namedtuple("Band", "start span")

# A counted phase: its band and the words the browser shows for it.
Phase = namedtuple("Phase", "band key label unit")

# The pipelines' bands. Percent for step ``done`` of ``total`` is
# ``band.start + int(band.span * done / max(total, 1))``.
ALBUM_LASTFM_FETCH = Phase(Band(5, 15), "lastfm_fetch", "Fetching scrobbles", "page")
SPOTIFY_SEARCH = Phase(Band(20, 20), "spotify_search", "Searching Spotify", "album")
SPOTIFY_DETAILS = Phase(
    Band(40, 20), "spotify_details", "Fetching Spotify details", "batch"
)
DEEZER_FALLBACK = Phase(Band(60, 15), "deezer_fallback", "Checking Deezer", "album")
HEATMAP_LASTFM_FETCH = Phase(Band(5, 75), "lastfm_fetch", "Fetching scrobbles", "page")

_ERROR_FIELDS = ("error_code", "error_source", "retryable", "retry_after")


def phase_percent(phase, done, total):
    """Return the whole percent the bar shows at *done* of *total* in *phase*."""
    return phase.band.start + int(phase.band.span * done / max(total, 1))


# ---------------------------------------------------------------------------
# The storage seam
# ---------------------------------------------------------------------------


class JobStore(Protocol):
    """What the job module needs from storage.

    A record is a plain dict: ``created_at``, ``updated_at``, ``progress``,
    ``results``, ``unmatched``, ``params``. The store keeps it and gives the
    callers below exclusive access to it for the length of one call; it knows
    nothing else about the rules.
    """

    def insert(self, job_id: str, record: dict) -> None: ...

    def read(self, job_id: str, view: Callable[[dict], object]):
        """Return ``view(record)`` for a live job, else ``None``. Never writes."""

    def modify(self, job_id: str, change: Callable[[dict], object]) -> bool:
        """Run ``change(record)`` atomically; False if the job is gone.

        A ``change`` that returns ``False`` declines: nothing is kept and the
        answer is False.
        """

    def modify_all(self, change: Callable[[dict], object]) -> int:
        """Run ``modify`` over every job; return how many ``change`` accepted."""

    def remove(self, job_id: str) -> None: ...

    def remove_stale(self, cutoff: float) -> int:
        """Delete jobs whose ``updated_at`` is before *cutoff*; return the count."""

    def ids(self) -> list: ...


class MemoryJobStore:
    """The in-memory adapter: a dict guarded by one lock."""

    def __init__(self):
        self._records = {}
        self._lock = threading.Lock()

    def insert(self, job_id, record):
        with self._lock:
            self._records[job_id] = record

    def read(self, job_id, view):
        with self._lock:
            record = self._records.get(job_id)
            if record is None:
                return None
            return view(record)

    def modify(self, job_id, change):
        with self._lock:
            record = self._records.get(job_id)
            if record is None:
                return False
            return change(record) is not False

    def modify_all(self, change):
        with self._lock:
            return sum(
                1 for record in self._records.values() if change(record) is not False
            )

    def remove(self, job_id):
        with self._lock:
            self._records.pop(job_id, None)

    def remove_stale(self, cutoff):
        with self._lock:
            stale = [
                job_id
                for job_id, record in self._records.items()
                if record.get("updated_at", record.get("created_at", 0)) < cutoff
            ]
            for job_id in stale:
                del self._records[job_id]
            return len(stale)

    def ids(self):
        with self._lock:
            return list(self._records)


_store: JobStore = MemoryJobStore()


def use_store(store):
    """Install *store* as the process-wide store; return the one it replaced."""
    global _store
    previous, _store = _store, store
    return previous


def _now():
    return time.time()


def _initial_progress():
    return {"progress": 0, "message": "Initializing...", "error": False, "stats": {}}


def _write(job_id, apply):
    """Apply *apply* to the job's record and renew its lease. False if gone."""

    def change(record):
        if apply(record) is False:
            return False
        record["updated_at"] = _now()
        return True

    return _store.modify(job_id, change)


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------


def create(params):
    """Create a job holding *params* and return its unique hex ID."""
    now = _now()
    job_id = uuid4().hex
    _store.insert(
        job_id,
        {
            "created_at": now,
            "updated_at": now,
            "progress": _initial_progress(),
            "results": None,
            "unmatched": {},
            "params": params,
        },
    )
    return job_id


def delete(job_id):
    """Remove a job, if it exists.

    Used to drop an orphan when thread startup fails after ``create``.
    """
    _store.remove(job_id)


def expire_stale():
    """Remove jobs whose last write is older than JOB_TTL_SECONDS.

    The lease is ``updated_at``, and only writers renew it. A reader never
    does, so an open page polling a finished job cannot keep that job, or an
    uploaded export's aggregate, in memory indefinitely (F-SWE-6).
    """
    removed = _store.remove_stale(_now() - JOB_TTL_SECONDS)
    if removed:
        logging.info(f"Cleaned up {removed} expired jobs")


def start(job_id, message):
    """Begin a run: 0%, *message*, no stats, no phase, no error flag."""

    def apply(record):
        progress = record["progress"]
        progress["stats"] = {}
        progress["progress"] = 0
        progress["message"] = message
        progress.pop("phase", None)
        _clear_error(progress)

    return _write(job_id, apply)


def advance(job_id, percent, message, phase=None):
    """Move the job to *percent* with *message*.

    *phase* is the counted-step payload the browser renders (``key``,
    ``label``, ``unit``, ``current``, ``total``); None clears it. Pipelines
    report counted steps through ``report_phase``, which derives the percent.
    """

    def apply(record):
        progress = record["progress"]
        progress["progress"] = percent
        progress["message"] = message
        if phase is None:
            progress.pop("phase", None)
        else:
            progress["phase"] = dict(phase)

    return _write(job_id, apply)


def report_phase(job_id, phase, done, total, message):
    """Report step *done* of *total* in *phase*; the percent comes from its band."""
    return advance(
        job_id,
        phase_percent(phase, done, total),
        message,
        phase={
            "key": phase.key,
            "label": phase.label,
            "unit": phase.unit,
            "current": done,
            "total": total,
        },
    )


def record_stat(job_id, key, value):
    """Store one stat under ``progress.stats``.

    A dict value is copied on write, so a worker that keeps mutating its own
    running tally cannot reach into the store behind its exclusion.
    """
    stored = dict(value) if isinstance(value, dict) else value

    def apply(record):
        record["progress"].setdefault("stats", {})[key] = stored

    return _write(job_id, apply)


def record_partial_source(job_id, source):
    """Note which kind of degradation made a run partial.

    ``source`` is ``"lastfm"`` (pages dropped) or ``"provider"`` (Spotify or
    Deezer could not answer). Kept beside the ``partial_data_warning`` text
    so the Results page reads the kind, not the wording. Recording the same
    source twice keeps one entry.
    """

    def apply(record):
        stats = record["progress"].setdefault("stats", {})
        sources = list(stats.get("partial_data_sources", []))
        if source not in sources:
            sources.append(source)
        stats["partial_data_sources"] = sources

    return _write(job_id, apply)


def record_unmatched(job_id, unmatched_key, payload):
    """Record an unmatched album entry, keyed by normalized name."""

    def apply(record):
        record["unmatched"][unmatched_key] = payload

    return _write(job_id, apply)


def _clear_error(progress):
    progress["error"] = False
    for field in _ERROR_FIELDS:
        progress.pop(field, None)


def _end(job_id, outcome, apply):
    """Apply the job's terminal transition, unless it has already ended.

    A job ends exactly one way. A second ``succeed`` or ``fail`` (a failure
    raised by work that follows ``succeed``, say) is refused and logged rather
    than overwriting the first ending, so results already on a page are not
    replaced by an empty error state. Returns False when refused or gone.
    """

    def guarded(record):
        if record["progress"]["progress"] >= 100:
            logging.warning(f"Job {job_id} has already ended; {outcome} refused")
            return False
        return apply(record)

    return _write(job_id, guarded)


def succeed(job_id, results, message):
    """Finish the job with *results* (list or dict) at 100%.

    Results and the completion signal land in one write, so a page that sees
    100% always finds its payload, and any earlier error is cleared: a job
    holds results or an error, never both. Refused, and logged, if the job
    has already ended (see ``_end``).
    """

    def apply(record):
        record["results"] = results
        progress = record["progress"]
        progress["progress"] = 100
        progress["message"] = message
        progress.pop("phase", None)
        _clear_error(progress)

    return _end(job_id, "succeed", apply)


def _fail(job_id, message, code, source, retryable, retry_after):
    def apply(record):
        record["results"] = []
        progress = record["progress"]
        progress["progress"] = 100
        progress["message"] = message
        progress["error"] = True
        progress["error_code"] = code
        progress["retryable"] = retryable
        for field, value in (("error_source", source), ("retry_after", retry_after)):
            if value is not None:
                progress[field] = value
        progress.pop("phase", None)

    return _end(job_id, "fail", apply)


def fail(job_id, error_code, username=None, retry_after=None):
    """Finish the job with a classified error (``errors.ERROR_CODES``).

    The job's results become an empty list: an error and a result set never
    coexist. Refused, and logged, if the job has already ended (see ``_end``).
    """
    info = ERROR_CODES.get(error_code, {})
    message = info.get("message", "An unexpected error occurred.")
    if username and "{username}" in message:
        message = message.format(username=username)
    return _fail(
        job_id,
        message,
        error_code,
        info.get("source"),
        info.get("retryable", False),
        retry_after,
    )


def reset(job_id, message=None):
    """Return the job to its initial state, keeping its params; False if gone."""

    def apply(record):
        record["progress"] = _initial_progress()
        if message is not None:
            record["progress"]["message"] = message
        record["results"] = None
        record["unmatched"] = {}

    return _write(job_id, apply)


def update_result(job_id, album_key, fields):
    """Merge *fields* into the one result matching the normalized *album_key*.

    *album_key* is a ``(artist_norm, album_norm)`` tuple, the same shape the
    metadata and original-release caches are keyed by. Result dicts carry
    that tuple as ``_normalized_key``, attached once when the results list is
    built (``_build_results`` in ``scrobblescope/orchestrator/_results.py``)
    rather than re-derived here with ``normalize_name`` on every entry: with
    up to 500 results and one call per corrected album, repeated
    normalization under the store's exclusion could stall unrelated request
    handlers. A result with no ``_normalized_key`` never matches, which is
    indistinguishable from "no album with that key".

    Returns False -- changing nothing, renewing nothing -- when the job is
    gone, has no results list yet, or holds no album with that key. The
    correction worker treats False as "stop bothering".
    """
    target_key = tuple(album_key)

    def apply(record):
        results = record.get("results")
        if not isinstance(results, list):
            return False
        for result in results:
            if result.get("_normalized_key") == target_key:
                result.update(fields)
                return True
        return False

    return _write(job_id, apply)


def mark_interrupted():
    """Fail every unfinished job as interrupted; return how many there were.

    For a store that outlives the process: a job left mid-run by a restart
    will never finish, and a page polling it must be told so rather than wait.
    The in-memory store dies with the process, so it never finds one.
    """
    info = ERROR_CODES["job_interrupted"]

    def apply(record):
        progress = record["progress"]
        if progress["error"] or progress["progress"] >= 100:
            return False
        record["results"] = []
        progress["progress"] = 100
        progress["message"] = info["message"]
        progress["error"] = True
        progress["error_code"] = "job_interrupted"
        progress["error_source"] = info["source"]
        progress["retryable"] = info["retryable"]
        progress.pop("phase", None)
        record["updated_at"] = _now()

    return _store.modify_all(apply)


# ---------------------------------------------------------------------------
# Reads. They never renew the lease: reading is not activity (F-SWE-6), and
# the release-check worker asks whether a job still exists without keeping it
# alive.
# ---------------------------------------------------------------------------


def _progress_view(record):
    progress = dict(record["progress"])
    progress["stats"] = dict(progress.get("stats", {}))
    if "phase" in progress:
        progress["phase"] = dict(progress["phase"])
    return progress


def progress(job_id):
    """Return a copy of the job's progress dict, or None if not found."""
    return _store.read(job_id, _progress_view)


def exists(job_id):
    """Return whether the job is still in the store.

    An existence probe: unlike ``context`` it copies nothing, and like every
    read it does not renew the lease.
    """
    return _store.read(job_id, lambda record: True) is True


def unmatched(job_id):
    """Return a copy of the job's unmatched albums dict, or None if not found."""
    return _store.read(job_id, lambda record: dict(record["unmatched"]))


def _context_view(record):
    results = record.get("results")
    if isinstance(results, list):
        results = list(results)
    elif isinstance(results, dict):
        # Copy the outer dict and the one known nested mutable structure
        # (daily_counts) so callers cannot mutate stored state (F-B18-8).
        results = dict(results)
        if "daily_counts" in results:
            results["daily_counts"] = dict(results["daily_counts"])
    return {
        "progress": _progress_view(record),
        "results": results,
        "unmatched": dict(record.get("unmatched", {})),
        "params": dict(record.get("params", {})),
    }


def context(job_id):
    """Return progress, results, unmatched and params as copies, or None."""
    return _store.read(job_id, _context_view)
