"""Job admission: the one path that starts a job.

Expire stale jobs, take a concurrency slot, create the job with its
parameters, start its thread with the job id alone, and undo the job if the
thread will not start. The album route and the heatmap route used to write
this twice; the Spotify export route (Batch 23 WP-4) is the third caller.
Each route keeps its own request parsing, session key and HTTP response.

Slot ownership: ``admit`` takes the slot, and from the moment the thread is
started the thread's ``run_coroutine_in_new_loop`` releases it. When the
thread cannot be started, ``worker.start_job_thread`` releases it before
re-raising, so ``admit`` must not release it again. When the job cannot be
created at all, no thread exists to own the slot, so ``admit`` releases it.

The slot and thread functions are read from the ``routes`` facade at call time
(see ``scrobblescope/routes/__init__.py``), so the suite's patches at
``scrobblescope.routes.acquire_job_slot`` and ``.start_job_thread`` keep working.
"""

import enum

from scrobblescope import jobs
from scrobblescope import routes as _routes
from scrobblescope.utils import log_failure
from scrobblescope.worker import release_job_slot


class Refused(enum.Enum):
    """Why a job was not admitted."""

    CAPACITY = "capacity"
    START_FAILED = "start_failed"


def admit(params, target, *, label):
    """Admit one job and return its id, or a ``Refused`` member.

    Args:
        params: The job record's params, including its kind (``mode``).
        target: The thread entry point; it is called with the job id alone.
        label: Names the thread in the failure log ("Failed to start {label}
            thread").
    """
    jobs.expire_stale()

    if not _routes.acquire_job_slot():
        return Refused.CAPACITY

    try:
        job_id = jobs.create(params)
    except Exception:
        # No thread exists yet to own the slot, so hand it back here.
        release_job_slot()
        raise

    try:
        _routes.start_job_thread(target, args=(job_id,))
    except Exception:  # noqa: BLE001 -- logged by log_failure
        log_failure(f"Failed to start {label} thread")
        jobs.delete(job_id)
        return Refused.START_FAILED

    return job_id
