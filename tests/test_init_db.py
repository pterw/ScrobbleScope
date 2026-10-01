"""init_db.py retries a waking database and fails fast on SQL errors."""

import asyncio

import asyncpg
import pytest

import init_db

SECRET_DSN = "postgresql://user:hunter2@db.internal:5432/app"


class FakeConn:
    def __init__(self, log, drops):
        self.log = log
        self.drops = drops

    async def execute(self, sql):
        if self.drops:
            raise self.drops.pop(0)
        self.log.append(sql)

    async def close(self):
        self.log.append("closed")


def _install(monkeypatch, outcomes, drops=()):
    """Patch connect: each call pops an outcome (exception or None=ok).

    drops are raised by the next execute calls, one per call.
    """
    state = {"connects": 0, "log": [], "sleeps": [], "kwargs": []}
    pending_drops = list(drops)

    async def fake_connect(dsn, **kwargs):
        state["connects"] += 1
        state["kwargs"].append(kwargs)
        outcome = outcomes.pop(0)
        if outcome is not None:
            raise outcome
        return FakeConn(state["log"], pending_drops)

    async def fake_sleep(seconds):
        state["sleeps"].append(seconds)

    monkeypatch.setenv("DATABASE_URL", SECRET_DSN)
    monkeypatch.setattr(asyncpg, "connect", fake_connect)
    monkeypatch.setattr(init_db.asyncio, "sleep", fake_sleep)
    return state


def _run():
    with pytest.raises(SystemExit) as info:
        asyncio.run(_main_exit())
    return info.value.code


async def _main_exit():
    await init_db.main()
    raise SystemExit(0)


def test_transient_failures_then_success_exits_zero(monkeypatch, capsys):
    state = _install(
        monkeypatch,
        [
            asyncpg.exceptions.ConnectionDoesNotExistError("closed"),
            ConnectionRefusedError("refused"),
            None,
        ],
    )

    assert _run() == 0

    assert state["connects"] == 3
    assert state["sleeps"] == [1, 2]
    statements = [e for e in state["log"] if e != "closed"]
    assert len(statements) == 4
    assert state["log"][-1] == "closed"
    assert "Schema initialized successfully" in capsys.readouterr().out
    assert all(k.get("timeout") for k in state["kwargs"])


def test_drop_on_first_statement_retries_whole_step(monkeypatch, capsys):
    # The v143 shape: the connection opens, then dies on the first statement.
    state = _install(
        monkeypatch,
        [None, None],
        drops=[asyncpg.exceptions.ConnectionDoesNotExistError("closed mid-op")],
    )

    assert _run() == 0

    assert state["connects"] == 2
    assert state["sleeps"] == [1]
    # The dropped connection was closed before the retry, then the whole
    # step ran again on a fresh connection and closed it too.
    assert state["log"][0] == "closed"
    assert state["log"][-1] == "closed"
    statements = [e for e in state["log"] if e != "closed"]
    assert len(statements) == 4
    assert "ConnectionDoesNotExistError" in capsys.readouterr().err


def test_non_transient_error_fails_after_one_attempt(monkeypatch, capsys):
    state = _install(monkeypatch, [ValueError(f"bad value in {SECRET_DSN}")])

    assert _run() == 1

    assert state["connects"] == 1
    assert state["sleeps"] == []
    err = capsys.readouterr().err
    assert "ERROR: Schema init failed (ValueError)" in err
    assert "hunter2" not in err
    assert "bad value" not in err


def test_sql_error_line_adds_sqlstate_never_the_message(monkeypatch, capsys):
    _install(
        monkeypatch,
        [asyncpg.exceptions.InsufficientPrivilegeError(f"denied {SECRET_DSN}")],
    )

    assert _run() == 1

    err = capsys.readouterr().err
    assert (
        "ERROR: Schema init failed (InsufficientPrivilegeError, SQLSTATE 42501)" in err
    )
    assert "hunter2" not in err
    assert "denied" not in err


def test_exhausted_attempts_exit_one_with_error_line(monkeypatch, capsys):
    outcomes = [
        OSError(f"cannot reach {SECRET_DSN}") for _ in range(init_db.SCHEMA_ATTEMPTS)
    ]
    state = _install(monkeypatch, outcomes)

    assert _run() == 1

    assert state["connects"] == init_db.SCHEMA_ATTEMPTS
    assert state["sleeps"] == [1, 2, 4, 8, 8]
    err = capsys.readouterr().err
    assert err.count("ERROR: Schema init failed (OSError)") == 1
    assert "hunter2" not in err
    assert "cannot reach" not in err
    assert "attempt 6/6" not in err
    assert "IndexError" not in err


def test_retry_line_names_type_never_the_message(monkeypatch, capsys):
    _install(
        monkeypatch,
        [OSError(f"could not connect to {SECRET_DSN}"), None],
    )

    assert _run() == 0

    err = capsys.readouterr().err
    assert "attempt 1/6" in err
    assert "OSError" in err
    assert "hunter2" not in err
    assert SECRET_DSN not in err
