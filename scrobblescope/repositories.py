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
    """Remove jobs older than JOB_TTL_SECONDS from the in-memory JOBS dict."""
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


def set_job_results(job_id, results):
    """Store the final album results list on a job."""
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
    """Return a shallow copy of a job's progress dict, or None if not found."""
    with jobs_lock:
        job = JOBS.get(job_id)
        if not job:
            return None
        job["updated_at"] = time.time()
        progress = dict(job["progress"])
        progress["stats"] = dict(progress.get("stats", {}))
        return progress


def get_job_unmatched(job_id):
    """Return a copy of a job's unmatched albums dict, or None if not found."""
    with jobs_lock:
        job = JOBS.get(job_id)
        if not job:
            return None
        job["updated_at"] = time.time()
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
    """
    with jobs_lock:
        job = JOBS.get(job_id)
        if not job:
            return None
        job["updated_at"] = time.time()

        results = job.get("results")
        if isinstance(results, list):
            results = list(results)

        progress = dict(job["progress"])
        progress["stats"] = dict(progress.get("stats", {}))
        return {
            "progress": progress,
            "results": results,
            "unmatched": dict(job.get("unmatched", {})),
            "params": dict(job.get("params", {})),
        }
