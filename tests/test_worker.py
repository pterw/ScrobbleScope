import logging
import threading
from unittest.mock import MagicMock, patch

import pytest

from scrobblescope.worker import (
    acquire_job_slot,
    new_thread_event_loop,
    release_job_slot,
    start_job_thread,
)


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


def test_new_thread_event_loop_installs_a_default_loop_off_windows():
    """GIVEN a non-Windows platform
    WHEN new_thread_event_loop is called
    THEN it creates the default loop, installs it as this thread's loop, and
    returns it -- never touching ProactorEventLoop.
    """
    loop = MagicMock()
    proactor = MagicMock()
    with (
        patch("sys.platform", "linux"),
        patch("asyncio.new_event_loop", return_value=loop),
        patch("asyncio.ProactorEventLoop", proactor, create=True),
        patch("asyncio.set_event_loop") as installed,
    ):
        assert new_thread_event_loop() is loop

    installed.assert_called_once_with(loop)
    proactor.assert_not_called()


def test_new_thread_event_loop_uses_a_proactor_loop_on_windows():
    """GIVEN Windows, where Werkzeug's reloader can leave a SelectorEventLoop
        policy in child threads and asyncpg then mis-negotiates Postgres
    WHEN new_thread_event_loop is called
    THEN it builds a ProactorEventLoop explicitly and installs that one.
    """
    loop = MagicMock()
    with (
        patch("sys.platform", "win32"),
        patch("asyncio.ProactorEventLoop", return_value=loop, create=True),
        patch("asyncio.new_event_loop") as default,
        patch("asyncio.set_event_loop") as installed,
    ):
        assert new_thread_event_loop() is loop

    installed.assert_called_once_with(loop)
    default.assert_not_called()


def test_new_thread_event_loop_closes_the_loop_when_installing_it_fails():
    """GIVEN installing the new loop raises
    WHEN new_thread_event_loop is called
    THEN the loop it already created is closed before the error propagates.
        The callers used to own that close in their own finally; the helper
        must keep it, or a failed setup leaks the loop's selector and sockets.
    """
    loop = MagicMock()
    with (
        patch("sys.platform", "linux"),
        patch("asyncio.new_event_loop", return_value=loop),
        patch("asyncio.set_event_loop", side_effect=RuntimeError("install failed")),
    ):
        with pytest.raises(RuntimeError, match="install failed"):
            new_thread_event_loop()

    loop.close.assert_called_once_with()


async def _idle():
    """A real coroutine, so a mocked loop is handed something it could have run."""
    return None


def _closes(coro):
    """Close what a mocked loop was handed, as the real loop's run would have."""
    coro.close()


def _explodes(message):
    """Close the coroutine, then fail the run, as a real loop would have started it."""

    def _side_effect(coro):
        coro.close()
        raise RuntimeError(message)

    return _side_effect


def test_run_coroutine_builds_one_loop_then_closes_and_releases():
    """GIVEN a coroutine and a fake loop
    WHEN run_coroutine_in_new_loop runs it
    THEN one loop is built, run once with that coroutine, closed, and the slot released.
    """
    from scrobblescope.worker import run_coroutine_in_new_loop

    built = []

    def _make_loop():
        loop = MagicMock()
        loop.run_until_complete.side_effect = _closes
        built.append(loop)
        return loop

    released = []
    coro = _idle()
    run_coroutine_in_new_loop(
        coro, make_loop=_make_loop, release_slot=lambda: released.append(True)
    )

    assert len(built) == 1
    built[0].run_until_complete.assert_called_once_with(coro)
    built[0].close.assert_called_once_with()
    assert released == [True]


def test_run_coroutine_shares_the_protocol_but_not_the_failure_policy():
    """GIVEN a run that fails
    WHEN a policy is supplied
    THEN the policy receives the exception, the loop still closes, and nothing propagates.
    """
    from scrobblescope.worker import run_coroutine_in_new_loop

    loop = MagicMock()
    loop.run_until_complete.side_effect = _explodes("pipeline exploded")
    seen = []
    released = []

    run_coroutine_in_new_loop(
        _idle(),
        make_loop=lambda: loop,
        release_slot=lambda: released.append(True),
        on_run_error=seen.append,
    )

    assert len(seen) == 1
    assert isinstance(seen[0], RuntimeError)
    loop.close.assert_called_once_with()
    assert released == [True]


def test_run_coroutine_swallows_a_run_failure_when_no_policy_is_given():
    """GIVEN a run that fails and no policy
    WHEN the helper runs it
    THEN the failure is silent and the slot is still released.
    """
    from scrobblescope.worker import run_coroutine_in_new_loop

    loop = MagicMock()
    loop.run_until_complete.side_effect = _explodes("pipeline exploded")
    released = []

    run_coroutine_in_new_loop(
        _idle(), make_loop=lambda: loop, release_slot=lambda: released.append(True)
    )

    assert released == [True]


def test_run_coroutine_releases_the_slot_when_loop_setup_fails():
    """GIVEN loop construction fails
    WHEN the helper runs
    THEN no loop is closed, because there is none, and the slot is released.
    """
    from scrobblescope.worker import run_coroutine_in_new_loop

    released = []

    def _make_loop():
        raise RuntimeError("loop setup failed")

    run_coroutine_in_new_loop(
        _idle(), make_loop=_make_loop, release_slot=lambda: released.append(True)
    )

    assert released == [True]


def test_run_coroutine_closes_a_coroutine_the_loop_never_started():
    """GIVEN loop construction fails
    WHEN the helper runs
    THEN the coroutine it was handed is closed, not abandoned.

    The call site builds the coroutine before the helper is entered, so this is the
    only thing between a setup failure and a "coroutine was never awaited" warning.
    """
    from scrobblescope.worker import run_coroutine_in_new_loop

    def _make_loop():
        raise RuntimeError("loop setup failed")

    coro = _idle()
    assert coro.cr_frame is not None  # created, not yet started

    run_coroutine_in_new_loop(coro, make_loop=_make_loop, release_slot=lambda: None)

    assert coro.cr_frame is None  # closed, so nothing is left to complain about


def test_run_coroutine_never_hides_a_close_failure():
    """GIVEN loop.close fails
    WHEN the helper runs
    THEN the close failure propagates, the slot is still released, and no policy sees it.

    A leaked loop must never be mistaken for a failed pipeline, which is why this
    failure is not routed through on_run_error.
    """
    from scrobblescope.worker import run_coroutine_in_new_loop

    loop = MagicMock()
    loop.run_until_complete.side_effect = _closes
    loop.close.side_effect = RuntimeError("close failed")
    released = []
    seen = []

    with pytest.raises(RuntimeError, match="close failed"):
        run_coroutine_in_new_loop(
            _idle(),
            make_loop=lambda: loop,
            release_slot=lambda: released.append(True),
            on_run_error=seen.append,
        )

    assert released == [True]
    assert seen == []
