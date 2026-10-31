"""Admission: expire, take a slot, create the job, start its thread."""

from unittest.mock import MagicMock, patch

import pytest

from scrobblescope import jobs
from scrobblescope.routes.admission import Refused, admit


def _target(job_id):  # pragma: no cover - never run, only passed along
    raise AssertionError("the thread is stubbed in these tests")


PARAMS = {"username": "someone", "mode": "album"}


def test_an_admitted_job_holds_its_params_and_its_thread_gets_only_the_id():
    with (
        patch("scrobblescope.routes.acquire_job_slot", return_value=True),
        patch("scrobblescope.routes.start_job_thread") as start,
    ):
        job_id = admit(PARAMS, _target, label="album task")

    assert jobs.context(job_id)["params"] == PARAMS
    start.assert_called_once_with(_target, args=(job_id,))


def test_a_full_house_refuses_and_creates_nothing(fresh_job_store):
    """Mutation: create the job before taking the slot and the store is not empty."""
    with (
        patch("scrobblescope.routes.acquire_job_slot", return_value=False),
        patch("scrobblescope.routes.start_job_thread") as start,
    ):
        result = admit(PARAMS, _target, label="album task")

    assert result is Refused.CAPACITY
    assert fresh_job_store.ids() == []
    start.assert_not_called()


def test_a_thread_that_will_not_start_leaves_no_orphan_job(fresh_job_store):
    """Mutation: remove the `jobs.delete` in the failure branch and the job stays."""
    with (
        patch("scrobblescope.routes.acquire_job_slot", return_value=True),
        patch(
            "scrobblescope.routes.start_job_thread", side_effect=OSError("no threads")
        ),
    ):
        result = admit(PARAMS, _target, label="album task")

    assert result is Refused.START_FAILED
    assert fresh_job_store.ids() == []


def test_a_real_thread_start_failure_frees_the_slot_once_and_removes_the_job(
    fresh_job_store,
):
    """
    GIVEN every real piece of the path (the facade's acquire_job_slot and
    worker.start_job_thread are not patched) and a Thread that cannot start
    WHEN a job is admitted
    THEN admission answers START_FAILED, the store is empty, and the slot taken
    is released exactly once: by worker.start_job_thread, not again by admit.

    The semaphore is replaced by a counting double so a second release (which
    the real BoundedSemaphore would turn into a swallowed ValueError) is seen.

    Mutation: add `_routes.release_job_slot()` to admit's failure branch and
    the release count is 2; remove `jobs.delete(job_id)` and the store is not
    empty.
    """
    semaphore = MagicMock()
    semaphore.acquire.return_value = True
    with (
        patch("scrobblescope.worker._active_jobs_semaphore", semaphore),
        patch("scrobblescope.worker.threading.Thread") as thread_class,
    ):
        thread_class.return_value.start.side_effect = RuntimeError("cannot start")
        result = admit(PARAMS, _target, label="album task")

    assert result is Refused.START_FAILED
    assert fresh_job_store.ids() == []
    semaphore.acquire.assert_called_once()
    semaphore.release.assert_called_once()


def test_a_create_failure_frees_the_slot_once_and_propagates(fresh_job_store):
    """
    GIVEN a slot already taken and a job store whose create raises
    WHEN a job is admitted
    THEN the very same error reaches the caller and the
    slot is released exactly once instead of being held until a restart.

    Mutation: remove the release around `jobs.create` and the release count is
    0, so every failed create keeps one slot for the life of the process.
    """
    error = RuntimeError("store is down")
    semaphore = MagicMock()
    semaphore.acquire.return_value = True
    with (
        patch("scrobblescope.worker._active_jobs_semaphore", semaphore),
        patch("scrobblescope.routes.admission.jobs.create", side_effect=error),
    ):
        with pytest.raises(RuntimeError) as excinfo:
            admit(PARAMS, _target, label="album task")

    assert excinfo.value is error
    semaphore.acquire.assert_called_once()
    semaphore.release.assert_called_once()


def test_admission_drops_expired_jobs_first(fresh_job_store):
    """Mutation: remove `jobs.expire_stale()` from admit and the stale job survives."""
    stale = jobs.create({"username": "old", "mode": "album"})
    fresh_job_store.modify(stale, lambda record: record.update(updated_at=0))

    with (
        patch("scrobblescope.routes.acquire_job_slot", return_value=True),
        patch("scrobblescope.routes.start_job_thread"),
    ):
        admit(PARAMS, _target, label="album task")

    assert stale not in fresh_job_store.ids()
