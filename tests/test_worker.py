import logging
import threading
from unittest.mock import patch

import pytest

from scrobblescope.worker import acquire_job_slot, release_job_slot, start_job_thread


def test_acquire_job_slot_succeeds_when_capacity_available():
    """Fresh semaphore with capacity: acquire returns True."""
    with patch(
        "scrobblescope.worker._active_jobs_semaphore",
        threading.BoundedSemaphore(2),
    ):
        assert acquire_job_slot() is True


def test_acquire_job_slot_fails_when_at_capacity():
    """Semaphore fully consumed: returns False, does not block."""
    sem = threading.BoundedSemaphore(1)
    sem.acquire(blocking=False)  # exhaust the single slot
    with patch("scrobblescope.worker._active_jobs_semaphore", sem):
        assert acquire_job_slot() is False


def test_release_job_slot_restores_capacity():
    """Acquire then release: subsequent acquire succeeds."""
    sem = threading.BoundedSemaphore(1)
    with patch("scrobblescope.worker._active_jobs_semaphore", sem):
        assert acquire_job_slot() is True
        assert acquire_job_slot() is False  # exhausted
        release_job_slot()
        assert acquire_job_slot() is True  # restored


def test_release_job_slot_logs_warning_on_double_release(caplog):
    """Release without prior acquire: caplog captures WARNING."""
    sem = threading.BoundedSemaphore(1)
    with patch("scrobblescope.worker._active_jobs_semaphore", sem):
        with caplog.at_level(logging.WARNING):
            release_job_slot()  # no matching acquire -- triggers ValueError
        assert "release_job_slot called with no matching acquire" in caplog.text


def test_start_job_thread_creates_daemon_thread():
    """Thread is alive, daemon=True, target called."""
    called = threading.Event()

    def target_fn():
        called.set()

    # Use a fresh semaphore so releasing in the finally path doesn't error
    sem = threading.BoundedSemaphore(1)
    sem.acquire(blocking=False)
    with patch("scrobblescope.worker._active_jobs_semaphore", sem):
        start_job_thread(target_fn)
        called.wait(timeout=2)
        assert called.is_set()


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
