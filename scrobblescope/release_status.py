"""The release-check vocabulary: the strings the correction worker writes and
the Results page reads.

They are wire values. ``static/js/results-release-checks.js`` compares an
album's ``state`` with ``'confirmed'`` and ``'moved_out'`` and the job's
``status`` with ``'pending'`` and ``'running'``, and ``/api/release_checks``
serves all eight inside JSON. They live in their own module so the routes can
name them without importing the worker, which owns a thread and a queue
(``release_checks.py``).

    release_status <- (leaf)
"""

# Each result's ``release_check`` field, as the results page reads it.
CHECK_UNCHECKED = "unchecked"
CHECK_CONFIRMED = "confirmed"
CHECK_MOVED_OUT = "moved_out"
CHECK_UNAVAILABLE = "unavailable"

# The job's own ``progress.stats.release_check`` status. PENDING is never
# written: it is what the API reports while the key is absent, between a job
# publishing its results and the worker first reporting on them.
STATUS_PENDING = "pending"
STATUS_RUNNING = "running"
STATUS_DONE = "done"
STATUS_SKIPPED = "skipped"
