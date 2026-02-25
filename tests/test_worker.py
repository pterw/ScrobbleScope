import logging
import threading
from unittest.mock import patch

import pytest

from scrobblescope.worker import acquire_job_slot, release_job_slot, start_job_thread


def test_acquire_job_slot_succeeds_when_capacity_available():
    """GIVEN a semaphore with available capacity
    WHEN acquire_job_slot is called
    THEN it returns True.
    """
    with patch(
        "scrobblescope.worker._active_jobs_semaphore",
        threading.BoundedSemaphore(2),
    ):
        assert acquire_job_slot() is True


def test_acquire_job_slot_fails_when_at_capacity():
    """GIVEN a semaphore at capacity
    WHEN acquire_job_slot is called
    THEN it returns False without blocking.
    """
    sem = threading.BoundedSemaphore(1)
    sem.acquire(blocking=False)  # exhaust the single slot
    with patch("scrobblescope.worker._active_jobs_semaphore", sem):
        assert acquire_job_slot() is False


def test_release_job_slot_restores_capacity():
    """GIVEN a slot has been acquired
    WHEN release_job_slot is called
    THEN a subsequent acquire succeeds.
    """
    sem = threading.BoundedSemaphore(1)
    with patch("scrobblescope.worker._active_jobs_semaphore", sem):
        assert acquire_job_slot() is True
        assert acquire_job_slot() is False  # exhausted
        release_job_slot()
        assert acquire_job_slot() is True  # restored


def test_release_job_slot_logs_warning_on_double_release(caplog):
    """GIVEN no slot has been acquired
    WHEN release_job_slot is called
    THEN a WARNING is logged.
    """
    sem = threading.BoundedSemaphore(1)
    with patch("scrobblescope.worker._active_jobs_semaphore", sem):
        with caplog.at_level(logging.WARNING):
            release_job_slot()  # no matching acquire -- triggers ValueError
        assert "release_job_slot called with no matching acquire" in caplog.text


def test_start_job_thread_creates_daemon_thread():
    """GIVEN a callable target
    WHEN start_job_thread is called
    THEN threading.Thread is constructed with daemon=True and the target is invoked.
    """
    called = threading.Event()
    created_threads = []

    def target_fn():
        called.set()

    class DummyThread:
        def __init__(self, **kwargs):
            self._target = kwargs.get("target")
            self.daemon = kwargs.get("daemon")
            created_threads.append(self)

        def start(self):
            if self._target is not None:
                self._target()

    # Use a fresh semaphore so releasing in the finally path doesn't error
    sem = threading.BoundedSemaphore(1)
    sem.acquire(blocking=False)
    with (
        patch("scrobblescope.worker._active_jobs_semaphore", sem),
        patch("scrobblescope.worker.threading.Thread", DummyThread),
    ):
        start_job_thread(target_fn)

    assert called.is_set()
    assert len(created_threads) == 1
    assert created_threads[0].daemon is True


def test_start_job_thread_releases_slot_on_thread_construction_failure():
    """Patch Thread to raise RuntimeError; verify slot released."""
    sem = threading.BoundedSemaphore(1)
    sem.acquire(blocking=False)  # simulate a previously acquired slot

    with (
        patch("scrobblescope.worker._active_jobs_semaphore", sem),
        patch(
            "scrobblescope.worker.threading.Thread", side_effect=RuntimeError("boom")
        ),
    ):
        with pytest.raises(RuntimeError, match="boom"):
            start_job_thread(lambda: None)

        # Slot should have been released despite the failure
        assert sem.acquire(blocking=False) is True
