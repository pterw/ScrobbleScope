"""Tests for the idle watchdog: when the app stops itself and when it must not."""

import logging
import os
import queue
import signal

import pytest
from flask import Flask

from scrobblescope import idle_exit, release_checks, worker
from scrobblescope.idle_exit import (
    IdleWatch,
    has_active_work,
    stop_gunicorn,
    watch_from_env,
)

WINDOW = 600


class FakeClock:
    """A clock the test moves by hand; calling it reads the time."""

    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


def _watch(clock, work=lambda: False):
    exits = []
    watch = IdleWatch(
        WINDOW, clock=clock, work=work, exit_action=lambda: exits.append(1)
    )
    return watch, exits


def test_exits_once_after_the_idle_window_with_no_work():
    clock = FakeClock()
    watch, exits = _watch(clock)
    sleeps = []

    def sleep(seconds):
        sleeps.append(seconds)
        assert len(sleeps) < 100, "the watchdog never exited"
        clock.advance(seconds)

    watch.run(sleep=sleep)

    assert len(exits) == 1
    assert clock.now >= 1000.0 + WINDOW
    assert watch.step() is True
    assert watch.step() is True
    assert len(exits) == 1


def test_active_work_blocks_exit_and_restarts_the_window():
    clock = FakeClock()
    busy = {"on": True}
    watch, exits = _watch(clock, work=lambda: busy["on"])

    clock.advance(WINDOW + 100)
    assert watch.step() is False

    busy["on"] = False
    assert watch.step() is False
    assert exits == []

    clock.advance(WINDOW)
    assert watch.step() is True
    assert len(exits) == 1


def test_a_recent_request_blocks_exit():
    clock = FakeClock()
    watch, exits = _watch(clock)
    app = Flask(__name__)

    @app.route("/ok")
    def ok():
        return "ok"

    @app.route("/slow")
    def slow():
        clock.advance(WINDOW - 10)
        return "slow"

    inside = []

    @app.route("/inside")
    def inside_request():
        inside.append(watch.step())
        return "inside"

    watch.attach(app)
    client = app.test_client()

    clock.advance(WINDOW + 5)
    client.get("/inside")
    assert inside == [False]
    assert exits == []

    clock.advance(WINDOW - 10)
    client.get("/ok")
    assert client.get("/static/missing.css").status_code == 404
    clock.advance(WINDOW - 10)
    assert watch.step() is False

    client.get("/slow")
    clock.advance(WINDOW - 10)
    assert watch.step() is False
    assert exits == []

    clock.advance(WINDOW)
    assert watch.step() is True
    assert len(exits) == 1


@pytest.mark.parametrize(
    "environ, warns",
    [
        ({}, False),
        ({"IDLE_EXIT_MINUTES": ""}, False),
        ({"IDLE_EXIT_MINUTES": "0"}, False),
        ({"IDLE_EXIT_MINUTES": "-5"}, True),
        ({"IDLE_EXIT_MINUTES": "abc"}, True),
    ],
)
def test_unset_or_invalid_idle_minutes_starts_nothing(environ, warns, caplog):
    with caplog.at_level(logging.WARNING, logger="scrobblescope.idle_exit"):
        assert watch_from_env(environ) is None

    assert bool(caplog.records) is warns


def test_idle_minutes_are_minutes_not_seconds():
    clock = FakeClock()
    exits = []
    watch = watch_from_env({"IDLE_EXIT_MINUTES": "20"})
    watch._clock = clock
    watch._work = lambda: False
    watch._exit_action = lambda: exits.append(1)
    watch.touch()

    clock.advance(20 * 60 - 1)
    assert watch.step() is False
    assert exits == []

    clock.advance(1)
    assert watch.step() is True
    assert len(exits) == 1


def test_stop_gunicorn_sends_sigterm_to_the_parent(monkeypatch):
    sent = []
    monkeypatch.setattr(os, "getppid", lambda: 4242)
    monkeypatch.setattr(os, "kill", lambda pid, sig: sent.append((pid, sig)))

    stop_gunicorn()

    assert sent == [(4242, signal.SIGTERM)]


def test_a_dying_watchdog_thread_is_logged(caplog):
    def boom():
        raise RuntimeError("work check failed")

    watch = IdleWatch(WINDOW, clock=FakeClock(), work=boom, exit_action=lambda: None)

    with caplog.at_level(logging.ERROR, logger=idle_exit.logger.name):
        watch.run(sleep=lambda _s: None)

    assert [r.exc_info[0] for r in caplog.records] == [RuntimeError]


def test_start_runs_the_loop_on_a_daemon_thread():
    watch, _ = _watch(FakeClock())
    watch.run = lambda: None

    thread = watch.start()
    thread.join(timeout=5)

    assert thread.daemon is True


def test_an_idle_machine_is_stopped_within_a_minute_of_the_window():
    clock = FakeClock()
    watch, exits = _watch(clock)
    sleeps = []

    def sleep(seconds):
        sleeps.append(seconds)
        clock.advance(seconds)

    watch.run(sleep=sleep)

    assert exits == [1]
    assert sum(sleeps) - WINDOW <= 60


@pytest.mark.parametrize(
    "slot_held, queue_busy, expected",
    [(True, False, True), (False, True, True), (False, False, False)],
)
def test_has_active_work_sees_a_held_slot_and_a_pending_check(
    slot_held, queue_busy, expected, monkeypatch
):
    jobs_queue = queue.Queue()
    if queue_busy:
        jobs_queue.put("job")
    monkeypatch.setattr(release_checks, "_JOB_QUEUE", jobs_queue)

    if slot_held:
        assert worker.acquire_job_slot()
    try:
        assert has_active_work() is expected
    finally:
        if slot_held:
            worker.release_job_slot()
