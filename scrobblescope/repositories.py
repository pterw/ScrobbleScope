import logging
import threading
import time
from uuid import uuid4

from scrobblescope.config import JOB_TTL_SECONDS
from scrobblescope.errors import ERROR_CODES

# Per-job state tracking
JOBS = {}
jobs_lock = threading.Lock()


def _initial_progress():
    """Return the default progress dict for a newly created job."""
    return {
        "progress": 0,
        "message": "Initializing...",
        "error": False,
        "stats": {},
    }


def cleanup_expired_jobs():
    """Remove jobs whose last write is older than JOB_TTL_SECONDS.

    The lease is ``updated_at``, and only writers renew it. A getter never
    does, so an open page polling a finished job cannot keep that job, or
    an uploaded export's aggregate, in memory indefinitely (F-SWE-6).
    """
    cutoff = time.time() - JOB_TTL_SECONDS
    with jobs_lock:
        expired_job_ids = [
            job_id
            for job_id, payload in JOBS.items()
            if payload.get("updated_at", payload.get("created_at", 0)) < cutoff
        ]
        for job_id in expired_job_ids:
            JOBS.pop(job_id, None)

    if expired_job_ids:
        logging.info(f"Cleaned up {len(expired_job_ids)} expired jobs")


def create_job(params):
    """Create a new job entry in JOBS and return its unique hex ID."""
    now = time.time()
    job_id = uuid4().hex
    with jobs_lock:
        JOBS[job_id] = {
            "created_at": now,
            "updated_at": now,
            "progress": _initial_progress(),
            "results": None,
            "unmatched": {},
            "params": params,
        }
    return job_id


_UNSET = object()


def set_job_progress(
    job_id,
    progress=None,
    message=None,
    error=None,
    reset_stats=False,
    error_code=None,
    error_source=None,
    retryable=None,
    retry_after=None,
    phase=_UNSET,
):
    """Update one or more progress fields on an existing job."""
    with jobs_lock:
        job = JOBS.get(job_id)
        if not job:
            return False
        if reset_stats:
            job["progress"]["stats"] = {}
        if progress is not None:
            job["progress"]["progress"] = progress
        if message is not None:
            job["progress"]["message"] = message
        if error is not None:
            job["progress"]["error"] = error
        if error_code is not None:
            job["progress"]["error_code"] = error_code
        if error_source is not None:
            job["progress"]["error_source"] = error_source
        if retryable is not None:
            job["progress"]["retryable"] = retryable
        if retry_after is not None:
            job["progress"]["retry_after"] = retry_after
        if phase is not _UNSET:
            if phase is None:
                job["progress"].pop("phase", None)
            else:
                job["progress"]["phase"] = dict(phase)
        job["updated_at"] = time.time()
    return True


def set_job_error(job_id, error_code, username=None, retry_after=None):
    """Set a classified error on a job using a predefined error code."""
    info = ERROR_CODES.get(error_code, {})
    message = info.get("message", "An unexpected error occurred.")
    if username and "{username}" in message:
        message = message.format(username=username)
    set_job_progress(
        job_id,
        progress=100,
        message=message,
        error=True,
        error_code=error_code,
        error_source=info.get("source"),
        retryable=info.get("retryable", False),
        retry_after=retry_after,
        phase=None,
    )
    set_job_results(job_id, [])


def set_job_stat(job_id, key, value):
    """Store a single stat key-value pair in a job's progress.stats dict."""
    with jobs_lock:
        job = JOBS.get(job_id)
        if not job:
            return False
        job["progress"].setdefault("stats", {})[key] = value
        job["updated_at"] = time.time()
    return True


def set_job_release_check(job_id, state):
    """Store the correction worker's state at progress.stats.release_check.

    *state* is the whole ``{"status", "checked", "total", "moved_out",
    "moved_in"}`` dict, replaced on every update rather than merged: the
    worker owns the key outright and always knows the full state, so a
    merge could only ever preserve a stale count. Copied on write so a
    worker that keeps mutating its own running tally cannot reach into
    JOBS behind the lock.
    """
    with jobs_lock:
        job = JOBS.get(job_id)
        if not job:
            return False
        job["progress"].setdefault("stats", {})["release_check"] = dict(state)
        job["updated_at"] = time.time()
    return True


def update_job_result(job_id, album_key, fields):
    """Merge *fields* into the one result matching the normalized *album_key*.

    *album_key* is a ``(artist_norm, album_norm)`` tuple, the same shape the
    metadata and original-release caches are keyed by. Result dicts carry
    that same tuple as ``_normalized_key``, attached once when the results
    list is built (``_build_results`` in
    ``scrobblescope/orchestrator/_results.py``, which already has the key on
    hand from partitioning cache hits and just forwards it) rather than
    re-derived here with ``normalize_name`` on every entry. That turns the
    lookup into a cheap tuple comparison per entry instead of an O(n)
    ``normalize_name`` scan taken while holding the process-global
    ``jobs_lock`` -- with up to 500 results and one call per corrected
    album, repeated normalization under that lock could stall unrelated
    Flask request handlers. A result dict with no ``_normalized_key`` (none
    of this module's own producers omit it, but a caller could) simply never
    matches, which is indistinguishable from the existing "no album with
    that key" case.

    Returns False -- changing nothing -- when the job is gone, has no results
    list yet, or holds no album with that key. The correction worker outlives
    neither condition silently: it treats False as "stop bothering".
    """
    with jobs_lock:
        job = JOBS.get(job_id)
        if not job:
            return False
        results = job.get("results")
        if not isinstance(results, list):
            return False
        target_key = tuple(album_key)
        for result in results:
            if result.get("_normalized_key") == target_key:
                result.update(fields)
                job["updated_at"] = time.time()
                return True
    return False


def set_job_results(job_id, results):
    """Store the final results payload (list or dict) on a job."""
    with jobs_lock:
        job = JOBS.get(job_id)
        if not job:
            return False
        job["results"] = results
        job["updated_at"] = time.time()
    return True


def add_job_unmatched(job_id, unmatched_key, unmatched_payload):
    """Record an unmatched album entry on a job, keyed by normalized name."""
    with jobs_lock:
        job = JOBS.get(job_id)
        if not job:
            return False
        job["unmatched"][unmatched_key] = unmatched_payload
        job["updated_at"] = time.time()
    return True


def reset_job_state(job_id):
    """Reset a job's progress, results, and unmatched data to initial state."""
    with jobs_lock:
        job = JOBS.get(job_id)
        if not job:
            return False
        job["progress"] = _initial_progress()
        job["results"] = None
        job["unmatched"] = {}
        job["updated_at"] = time.time()
    return True


def get_job_progress(job_id):
    """Return a shallow copy of a job's progress dict, or None if not found.

    Reading is not activity: this never renews the job's lease, so a polled
    job still expires JOB_TTL_SECONDS after its last write (F-SWE-6).
    """
    with jobs_lock:
        job = JOBS.get(job_id)
        if not job:
            return None
        progress = dict(job["progress"])
        progress["stats"] = dict(progress.get("stats", {}))
        if "phase" in progress:
            progress["phase"] = dict(progress["phase"])
        return progress


def get_job_unmatched(job_id):
    """Return a copy of a job's unmatched albums dict, or None if not found.

    Never renews the job's lease; see get_job_progress.
    """
    with jobs_lock:
        job = JOBS.get(job_id)
        if not job:
            return None
        return dict(job["unmatched"])


def delete_job(job_id):
    """Remove a job entry from JOBS, if it exists.

    Used to clean up an orphaned job when thread startup fails after
    create_job() has already been called.
    """
    with jobs_lock:
        JOBS.pop(job_id, None)


def get_job_context(job_id):
    """Return the full job context (progress, results, unmatched, params).

    All mutable containers are shallow-copied to prevent callers from
    mutating shared state. Returns None if the job does not exist.

    Never renews the job's lease; see get_job_progress. The release-check
    worker calls this to ask whether a job still exists, and that question
    must not keep the job alive.
    """
    with jobs_lock:
        job = JOBS.get(job_id)
        if not job:
            return None

        results = job.get("results")
        if isinstance(results, list):
            results = list(results)
        elif isinstance(results, dict):
            # Shallow copy the outer dict, then explicitly copy the known
            # nested mutable structure (daily_counts) so callers cannot mutate
            # shared state through the returned reference.  Closes F-B18-8.
            results = dict(results)
            if "daily_counts" in results:
                results["daily_counts"] = dict(results["daily_counts"])

        progress = dict(job["progress"])
        progress["stats"] = dict(progress.get("stats", {}))
        if "phase" in progress:
            progress["phase"] = dict(progress["phase"])
        return {
            "progress": progress,
            "results": results,
            "unmatched": dict(job.get("unmatched", {})),
            "params": dict(job.get("params", {})),
        }
