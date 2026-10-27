"""Idle watchdog -- stops the server once nothing has happened for a while.

Fly's autostop only sees inbound connections, so it cannot tell that a
background job (or the MusicBrainz correction worker) is still running after
the browser has gone. The app therefore stops itself: when no request has
arrived and no job slot or release check has been held for the configured
window, the watchdog sends SIGTERM to the gunicorn master, which shuts down
cleanly with status 0 and leaves the machine stopped until the next request
starts it again.

Enabled only by ``IDLE_EXIT_MINUTES`` (a positive integer); unset means off.
It signals the parent process, so it is a gunicorn-only setting.

Dependency chain (leaf-ward):
    idle_exit <- worker, release_checks
"""

import logging
import os
import signal
import threading
import time

from scrobblescope import release_checks, worker

logger = logging.getLogger(__name__)

IDLE_CHECK_INTERVAL_SECONDS = 30


def has_active_work():
    """Return True while a job slot is held or a release check is pending."""
    return worker.active_job_slots() > 0 or release_checks.has_pending_checks()


def stop_gunicorn():
    """Ask the gunicorn master (our parent process) to shut down gracefully."""
    os.kill(os.getppid(), signal.SIGTERM)


class IdleWatch:
    """Decides when the app has been idle long enough to stop itself."""

    def __init__(
        self,
        idle_seconds,
        *,
        clock=time.monotonic,
        work=has_active_work,
        exit_action=stop_gunicorn,
    ):
        self._idle_seconds = idle_seconds
        self._clock = clock
        self._work = work
        self._exit_action = exit_action
        self._last_activity = clock()
        self._exited = False

    def touch(self):
        """Record "now" as the last activity (one float assignment, no lock)."""
        self._last_activity = self._clock()

    def step(self):
        """Make one decision; return True once the exit action has run."""
        if self._exited:
            return True
        if self._work():
            self.touch()
            return False
        if self._clock() - self._last_activity < self._idle_seconds:
            return False
        logger.info(
            "Idle for %d minutes with no active work; stopping the server",
            self._idle_seconds // 60,
        )
        self._exited = True
        self._exit_action()
        return True

    def run(self, sleep=time.sleep):
        """Step until the exit action has run, sleeping between steps."""
        while not self.step():
            sleep(IDLE_CHECK_INTERVAL_SECONDS)

    def attach(self, app):
        """Count every request on ``app`` (start and end) as activity."""
        app.before_request(self.touch)
        app.teardown_request(lambda _exc: self.touch())

    def start(self):
        """Run the watchdog loop on a daemon thread and return the thread."""
        thread = threading.Thread(target=self.run, name="idle-exit", daemon=True)
        thread.start()
        return thread


def watch_from_env(environ=os.environ):
    """Return an IdleWatch for ``IDLE_EXIT_MINUTES``, or None when it is off."""
    raw = environ.get("IDLE_EXIT_MINUTES", "").strip()
    if not raw:
        return None
    try:
        minutes = int(raw)
    except ValueError:
        minutes = -1
    if minutes < 0:
        logger.warning("IDLE_EXIT_MINUTES is not a positive integer; idle exit is off")
        return None
    if minutes == 0:
        return None
    return IdleWatch(minutes * 60)
