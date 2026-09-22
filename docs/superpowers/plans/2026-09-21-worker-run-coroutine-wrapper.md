# Worker run-coroutine wrapper Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the build-run-close-release protocol that both background entry points repeat into one helper in `scrobblescope/worker.py`, behaviour-neutral, so Batch 23's WP-0 builds on it instead of creating a second wrapper.

**Architecture:** `worker.py` gains `run_coroutine_in_new_loop(coroutine, *, make_loop, release_slot, on_run_error)`. The helper owns the protocol -- build the loop inside the `try`, run one coroutine, then in `finally` close the loop and release the slot, with a close failure never swallowed. It does *not* own the failure policy: each entry point injects an `on_run_error` callback, which is what keeps both callers behaviour-identical to today and what the later F-SWE-5 change will use. Callers pass their own module-level collaborators explicitly (`make_loop=new_thread_event_loop`, `release_slot=release_job_slot`) so every existing `mock.patch("scrobblescope.<caller>.<name>")` target keeps intercepting.

**Tech Stack:** Python 3.13 stdlib (`asyncio`, `threading`), pytest, `unittest.mock`. No new dependency.

## Global Constraints

Every task's requirements include this section.

- **Qualified interpreter only.** This is a linked worktree. Use the primary checkout's
  `C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe` and its sibling
  `pytest.exe` / `pre-commit.exe` for every command below. Never bare `pip`, never a second venv.
- **No new dependency, no version change.** `requirements.txt` / `requirements-dev.txt` are out of scope.
- **Every existing test passes unmodified.** This is the point of the change, and it is Batch 23
  WP-0's own acceptance criterion. If a task seems to need a test edited, stop and report: the seam
  is wrong, not the test.
- **Do not touch other agents' uncommitted work.** This worktree holds several untracked paths
  (`scripts/dev/mutation_test.py`, `progress_copy.md`, review HTML files, and others). Never stage,
  revert or delete them; `git status --short` lists the current set.
- **Commit discipline:** Conventional Commits, imperative mood, no trailing period, subject max 72
  chars. Stage paths by name -- `git add -A` and `git add .` are forbidden. Never `--no-verify`. No
  `Co-authored-by` trailer.
- **Documentation lands in the same commit as the work.** Each task's final steps add its dated
  `PLAYBOOK.md` Section 4 entry, then run `doc_state_sync.py --fix`, `pytest -q`,
  `pre-commit run --all-files`, and `doc_state_sync.py --check`, in that order (`AGENTS.md`
  "Commit Rules"): pre-commit runs the docsync check, so it must see the entry already synced.
  The entry is a tagged `(Batch 23 WP-0)` entry inside the current-batch markers once the owner has
  opened Batch 23 by naming its branch in PLAYBOOK Section 3; before that it is an untagged
  side-task entry directly after `<!-- DOCSYNC:CURRENT-BATCH-END -->`.
- **Quote the measured test count.** A Section 4 entry carries the suite result in the one form the
  authority reads (`AGENTS.md` "Which test count is authoritative"), from a literal `pytest -q` run.
  Never copy a count from another document. Baseline when this plan was written: **1,717 passed** (tracked suite only -- an earlier
  figure of 1,763 counted 46 tests from the deliberately uncommitted mutation runner, which is not
  part of the repository's state).
- **ASCII only** in every file this plan touches: no smart quotes, no em dash -- use `--`.
- **Out of scope, deliberately:** the terminal-outcome divergence (F-SWE-5) is a behaviour change and
  is *not* fixed here; the release-check worker's long-lived loop is *not* converted; and
  `_cap_threshold_exclusions`, `_process_filtered_albums` and `_zero_fill_daily_counts` are Batch 23
  WP-0's other extractions, not this plan's.

## File Structure

| File | Responsibility | Change |
| --- | --- | --- |
| `scrobblescope/worker.py` | Owns the thread, loop and slot mechanics for every background job | **Modify**: add `run_coroutine_in_new_loop` beside `new_thread_event_loop` |
| `scrobblescope/orchestrator/__init__.py` | Album pipeline glue | **Modify**: `background_task` delegates its protocol to the helper |
| `scrobblescope/heatmap.py` | Heatmap pipeline | **Modify**: `heatmap_task` delegates its protocol to the helper |
| `tests/test_worker.py` | Unit tests for the mechanics | **Modify**: add the helper's tests |
| `.claude/SESSION_CONTEXT.md`, `docs/architecture/*.md` | Structure and runtime description | **Modify**: name the helper where the protocol is described |

`release_checks.py` is deliberately absent: its `_worker_loop` builds one loop and drains a queue for
the lifetime of the process, so a one-shot wrapper is the wrong shape for it.

---
## Task 1: The helper and its tests

**Files:**
- Modify: `scrobblescope/worker.py` (append at the end of the file, after `new_thread_event_loop`)
- Test: `tests/test_worker.py` (append; the module already imports `pytest`, `patch`, `MagicMock`, `threading` and `logging`)

**Interfaces:**
- Consumes: `new_thread_event_loop()` and `release_job_slot()` from the same module.
- Produces: `run_coroutine_in_new_loop(coroutine, *, make_loop=new_thread_event_loop, release_slot=release_job_slot, on_run_error=None) -> None`, used by Tasks 2 and 3.

- [ ] **Step 1: Write the failing tests**

Each test imports the helper inside itself, on purpose, and matching the in-function imports already
used in this repository's tests (`tests/test_heatmap.py` imports `ERROR_CODES` the same way): a
module-level import would turn the pre-implementation run into one collection error for the file
instead of one failure per test, and the per-test failure is what proves each test is real. Do not
"tidy" these into the module's import block.

Append to `tests/test_worker.py`:

```python
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
```
- [ ] **Step 2: Run the tests to verify they fail**

Run: `C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe tests/test_worker.py -v -k run_coroutine`
Expected: 6 failed, each on `ImportError: cannot import name 'run_coroutine_in_new_loop'` raised
inside the test body (the in-function import makes these failures, not collection errors). If more
than 6 are selected, the earlier tests were disturbed -- fix that before continuing.

- [ ] **Step 3: Write the minimal implementation**

Append to `scrobblescope/worker.py`:

```python
def run_coroutine_in_new_loop(
    coroutine,
    *,
    make_loop=new_thread_event_loop,
    release_slot=release_job_slot,
    on_run_error=None,
):
    """Run one coroutine to completion, then close the loop and release the slot.

    The protocol in one place: the loop is built *inside* the ``try``, so a setup
    failure still reaches the ``finally`` that releases the concurrency slot, and a
    failure to *close* is never swallowed -- a leaked loop must not be reported as a
    failed pipeline.

    The *policy* stays with the caller, through ``on_run_error``. The album and
    heatmap entry points deliberately answer a failed run differently today
    (``F-SWE-5`` records both answers as wrong, and fixing that means changing a
    caller, not this helper), so the helper shares the protocol and takes the
    reaction as a parameter.

    Args:
        coroutine: The coroutine to run, on a loop built for the calling thread. It is
            closed here if the loop is never built, so a setup failure does not leave
            an unstarted coroutine for the garbage collector to complain about.
        make_loop: Builds and installs that thread's event loop. Injected so callers
            keep their own patchable name; defaults to the local helper.
        release_slot: Releases the slot acquired before the job started. Called
            exactly once, even when closing the loop fails.
        on_run_error: Called with the caught exception when loop construction or the
            run itself fails. ``None`` leaves the failure silent, which is what an
            entry point with its own inner handler wants. It is *not* called for a
            close failure, which propagates instead.
    """
    loop = None
    try:
        loop = make_loop()
        loop.run_until_complete(coroutine)
    except Exception as exc:  # noqa: BLE001 - the injected policy decides what to do
        if on_run_error is not None:
            on_run_error(exc)
    finally:
        if loop is None:
            # The loop was never built, so the coroutine never started. Nobody else
            # will close it, and an unstarted coroutine nobody closes raises
            # "RuntimeWarning: coroutine ... was never awaited" on the worker thread.
            coroutine.close()
        try:
            if loop is not None:
                loop.close()
        finally:
            release_slot()
```

Why that `coroutine.close()` is in scope rather than scope creep: the old inline code created the
coroutine *inside* the line that ran it, so a loop-setup failure never produced a coroutine at all.
The new call shape creates it at the call site, before the helper is entered, so without this line
the refactor would *introduce* a leaked-coroutine warning on a path that is silent today. It is what
keeps the change neutral, and the test in Step 1 pins it.


The trailing comment is not optional: this repository gates broad catches, and `pyproject.toml`'s
ruff comment requires a `# noqa: BLE001` to carry a stated reason -- "so the count cannot grow
without a stated reason". `the injected policy decides what to do` is that reason. Keep it, and
rephrase it if the intent reads differently to you.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe tests/test_worker.py -v`
Expected: the six new tests pass, and the nine existing tests (`acquire_job_slot` x2,
`release_job_slot` x2, `start_job_thread` x2, `new_thread_event_loop` x3) still pass. No `RuntimeWarning: coroutine ... was never awaited` may appear in
the output; if one does, the `coroutine.close()` line is missing or unreachable.

- [ ] **Step 5: Prove the tests fail if the helper is deleted**

Replace the helper's body with `raise NotImplementedError` and re-run the six tests. All six must
fail. Restore the body and re-run to green. This is the repository's rule that a test must fail if
the function under test is deleted; a test that passes either way is not accepted.

- [ ] **Step 6: Run the full gates and commit**

```bash
C:/Users/peter/Python\ Projects/ScrobbleScope/.venv/Scripts/python.exe scripts/doc_state_sync.py --fix
C:/Users/peter/Python\ Projects/ScrobbleScope/.venv/Scripts/python.exe -m pytest -q
C:/Users/peter/Python\ Projects/ScrobbleScope/.venv/Scripts/pre-commit.exe run --all-files
C:/Users/peter/Python\ Projects/ScrobbleScope/.venv/Scripts/python.exe scripts/doc_state_sync.py --check
git add scrobblescope/worker.py tests/test_worker.py PLAYBOOK.md
git commit -m "refactor(worker): Add the run-and-release loop helper"
```

Add the dated `PLAYBOOK.md` Section 4 entry first (tagged or side-task, per Global Constraints), carrying scope, deviations, and the measured `**N passed**`
from a `pytest -q` run on the final tree. `doc_state_sync.py --check` must exit 0 before the commit; the only
acceptable output is the expected root-`BATCH23_DEFINITION.md` warning.

---
## Task 2: The album entry point adopts it

**Files:**
- Modify: `scrobblescope/orchestrator/__init__.py` -- the `background_task` function (currently lines 636-679) and the `scrobblescope.worker` import (currently line 60)
- Test: **none written**. The four tests in `tests/services/test_orchestrator_fetch_and_process.py` are the acceptance criterion and pass unmodified.

**Interfaces:**
- Consumes: `run_coroutine_in_new_loop` from Task 1, plus this module's own `new_thread_event_loop`, `release_job_slot` and `_fetch_and_process` names.
- Produces: no interface change. `background_task`'s signature, its log line, and its exception behaviour are identical.

- [ ] **Step 1: Confirm the four guard tests pass before the change**

Run: `C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe tests/services/test_orchestrator_fetch_and_process.py -v -k background_task`
Expected: 4 passed -- `test_background_task_runs_single_event_loop`,
`test_background_task_releases_slot_on_exception`,
`test_background_task_releases_slot_when_event_loop_setup_raises`,
`test_background_task_releases_slot_when_loop_close_raises`.

Read all four now. They are the contract: the first asserts `_fetch_and_process` is awaited exactly
once and the slot released; the second and third assert the slot is released when the pipeline or
loop setup fails; the fourth asserts a failing `loop.close()` **propagates out of
`background_task`** while the slot is still released. That last one is why the helper call must not
sit inside a broad `except`.

- [ ] **Step 2: Extend the worker import**

Replace line 60's import with:

```python
from scrobblescope.worker import (
    new_thread_event_loop,
    release_job_slot,
    run_coroutine_in_new_loop,
)
```

- [ ] **Step 3: Replace the body of `background_task`**

Keep the signature and the docstring's opening. Replace everything after the docstring -- the
`loop = None` block, the `except Exception:` log line, and the nested `finally` -- with:

```python
    run_coroutine_in_new_loop(
        _fetch_and_process(
            job_id,
            username,
            year,
            sort_mode,
            release_scope,
            decade,
            release_year,
            min_plays,
            min_tracks,
            limit_results,
        ),
        # Passed explicitly rather than left to the helper's own defaults: the tests
        # patch ``scrobblescope.orchestrator.release_job_slot``, and a default taken
        # from the helper's module would move that patch target without failing.
        make_loop=new_thread_event_loop,
        release_slot=release_job_slot,
        on_run_error=lambda _exc: logging.exception(
            f"Unhandled error in background task for {username}/{year}"
        ),
    )
```

Then extend the docstring with the two facts a reader now needs:

```
    The build-run-close-release protocol lives in
    ``worker.run_coroutine_in_new_loop``; what stays here is the reaction to a
    failed run, which is to log it. The classification of a pipeline failure into a
    job error happens deeper in, inside ``_fetch_and_process``, so this remains a
    backstop rather than the answer the user sees. ``F-SWE-5`` records that this
    backstop publishes no terminal state at all, unlike the heatmap's.
```

- [ ] **Step 4: Run the four guard tests, unmodified**

Run: `C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe tests/services/test_orchestrator_fetch_and_process.py -v -k background_task`
Expected: 4 passed.

Then prove the tests were untouched:
`git diff --stat tests/services/test_orchestrator_fetch_and_process.py` must print nothing.
If any test needed editing, the seam is wrong -- restore it and report instead of editing the test.

- [ ] **Step 5: Run the entry point's other consumers**

Run: `C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe tests/test_routes.py tests/services -q`
Expected: pass. `tests/test_routes.py:435` asserts the thread target is still the same
`background_task` object, which this task does not move.

- [ ] **Step 6: Run the full gates and commit**

```bash
C:/Users/peter/Python\ Projects/ScrobbleScope/.venv/Scripts/python.exe scripts/doc_state_sync.py --fix
C:/Users/peter/Python\ Projects/ScrobbleScope/.venv/Scripts/python.exe -m pytest -q
C:/Users/peter/Python\ Projects/ScrobbleScope/.venv/Scripts/pre-commit.exe run --all-files
C:/Users/peter/Python\ Projects/ScrobbleScope/.venv/Scripts/python.exe scripts/doc_state_sync.py --check
git add scrobblescope/orchestrator/__init__.py PLAYBOOK.md
git commit -m "refactor(orchestrator): Delegate the loop protocol to worker"
```

Same documentation step as Task 1, with the count from this run.

---
## Task 3: The heatmap entry point adopts it

**Files:**
- Modify: `scrobblescope/heatmap.py` -- the `heatmap_task` function (currently lines 238-259) and the `scrobblescope.worker` import (currently line 31)
- Test: **none written**. The four tests in `tests/test_heatmap.py::TestHeatmapTask` are the acceptance criterion and pass unmodified.

**Interfaces:**
- Consumes: `run_coroutine_in_new_loop` from Task 1, plus this module's own `new_thread_event_loop`, `release_job_slot`, `set_job_error` and `_fetch_and_process_heatmap` names.
- Produces: no interface change to `heatmap_task`, and one new module-private helper, `_report_heatmap_failure(job_id, username)`.

- [ ] **Step 1: Confirm the four guard tests pass before the change**

Run: `C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe tests/test_heatmap.py -v -k TestHeatmapTask`
Expected: 4 passed -- `test_release_job_slot_called_on_success`,
`test_release_job_slot_called_on_exception`,
`test_release_job_slot_called_when_event_loop_setup_raises`,
`test_release_job_slot_called_when_loop_close_raises`.

Read them now. Two properties they pin are easy to lose: `heatmap_task` must **not raise** when the
pipeline fails (it reports instead), and it **must** raise when `loop.close()` fails.

- [ ] **Step 2: Extend the worker import**

Replace line 31's import with:

```python
from scrobblescope.worker import (
    new_thread_event_loop,
    release_job_slot,
    run_coroutine_in_new_loop,
)
```

- [ ] **Step 3: Add the reaction as a named function**

Immediately above `heatmap_task`, add:

```python
def _report_heatmap_failure(job_id, username):
    """Log the crash and publish this pipeline's terminal state.

    Called from inside the helper's ``except`` block, so ``logging.exception`` still
    sees the active exception. The ``lastfm_unavailable`` code is the open defect
    ``F-SWE-5`` records -- it is wrong for a fault that is ours -- and this function
    keeps it deliberately: changing the code is a behaviour change, and it belongs in
    its own commit, which is now a one-line edit here.
    """
    logging.exception(f"Unhandled error in heatmap task for {username}")
    set_job_error(job_id, "lastfm_unavailable", username=username)
```

Naming it matters twice: it gives the later F-SWE-5 change a single place to alter, and it keeps
`set_job_error` resolved as this module's global so `patch("scrobblescope.heatmap.set_job_error")`
still intercepts.

- [ ] **Step 4: Replace the body of `heatmap_task`**

Keep the signature. Replace everything after the docstring with:

```python
    run_coroutine_in_new_loop(
        _fetch_and_process_heatmap(job_id, username),
        # Explicit, for the same reason as the album entry point: these tests patch
        # ``scrobblescope.heatmap.release_job_slot`` and ``...heatmap.set_job_error``.
        make_loop=new_thread_event_loop,
        release_slot=release_job_slot,
        on_run_error=lambda _exc: _report_heatmap_failure(job_id, username),
    )
```

Update the docstring: it currently explains that the loop is built inside the `try` so the slot is
released in the `finally`, "loop setup included". That reasoning now lives in the helper, so the
docstring should say so and keep only what is local -- that a failed run is reported rather than
raised, which is this entry point's answer to F-SWE-5.

- [ ] **Step 5: Run the four guard tests, unmodified**

Run: `C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe tests/test_heatmap.py -v -k TestHeatmapTask`
Expected: 4 passed, and `git diff --stat tests/test_heatmap.py` prints nothing.

- [ ] **Step 6: Confirm both entry points now share exactly one protocol**

Run: `C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe -q tests/test_heatmap.py tests/services/test_orchestrator_fetch_and_process.py tests/test_routes.py tests/test_worker.py`
Expected: pass.

Then read `background_task` and `heatmap_task` side by side. Each should now be a single call, and
the only difference between them should be the injected `on_run_error`. That difference *is* the
remaining half of F-SWE-5, and it should be visible in about ten lines of diff rather than sixty.

- [ ] **Step 7: Run the full gates and commit**

```bash
C:/Users/peter/Python\ Projects/ScrobbleScope/.venv/Scripts/python.exe scripts/doc_state_sync.py --fix
C:/Users/peter/Python\ Projects/ScrobbleScope/.venv/Scripts/python.exe -m pytest -q
C:/Users/peter/Python\ Projects/ScrobbleScope/.venv/Scripts/pre-commit.exe run --all-files
C:/Users/peter/Python\ Projects/ScrobbleScope/.venv/Scripts/python.exe scripts/doc_state_sync.py --check
git add scrobblescope/heatmap.py PLAYBOOK.md
git commit -m "refactor(heatmap): Delegate the loop protocol to worker"
```

Same documentation step, with the count from this run.

---
## Task 4: Name the helper where the protocol is documented

**Files:**
- Modify: `.claude/SESSION_CONTEXT.md` -- Section 3's `worker.py` line. Section 4 needs no change: `worker.py`'s dependencies are unchanged, so the graph is still `worker.py <- config`.
- Modify: `docs/architecture/runtime-system.md` and/or `docs/architecture/top-albums-sequence.md` **only if** they describe this protocol. Read each first; change only what is now inaccurate.
- Test: none. The gates are the check.

**Interfaces:**
- Consumes: the helper from Task 1 and its two callers from Tasks 2 and 3.
- Produces: no code interface.

- [ ] **Step 1: Find every place the protocol is described**

Run: `C:/Users/peter/Python\ Projects/ScrobbleScope/.venv/Scripts/python.exe -c "import pathlib; [print(p.as_posix()) for p in pathlib.Path('.').glob('**/*.md') if 'release_job_slot' in p.read_text(encoding='utf-8', errors='ignore')]"`

Then repeat with `new_thread_event_loop` in place of `release_job_slot`. Read every hit before editing.

Expected: `.claude/SESSION_CONTEXT.md` Section 3 (the structure list) and Section 5 (the runtime
overview), and possibly `docs/architecture/runtime-system.md`. `AGENT_NOTES.md`'s Windows-asyncio
note names `worker.new_thread_event_loop` as the single seam both pipelines build their loop
through, which this change strengthens -- if its wording still holds, leave it alone.

- [ ] **Step 2: Update the structure line**

In `.claude/SESSION_CONTEXT.md` Section 3, the `worker.py` comment currently reads:

```
  worker.py                 # semaphore, acquire/release_job_slot, start_job_thread
```

Change it to name the new helper:

```
  worker.py                 # semaphore, acquire/release_job_slot, start_job_thread, run_coroutine_in_new_loop
```

- [ ] **Step 3: Update the runtime description only where it is now inaccurate**

If a hit from Step 1 says where the build-run-close-release protocol lives, update that sentence to
say both background entry points run their pipeline through `worker.run_coroutine_in_new_loop` and
that the reaction to a failed run is injected per entry point. Add no second description anywhere:
one document owns the protocol, `.claude/SESSION_CONTEXT.md` links to `docs/ARCHITECTURE.md`, and
that links to the focused owner files.

- [ ] **Step 4: Run the gates and commit**

```bash
C:/Users/peter/Python\ Projects/ScrobbleScope/.venv/Scripts/python.exe scripts/doc_state_sync.py --fix
C:/Users/peter/Python\ Projects/ScrobbleScope/.venv/Scripts/python.exe -m pytest -q
C:/Users/peter/Python\ Projects/ScrobbleScope/.venv/Scripts/pre-commit.exe run --all-files
C:/Users/peter/Python\ Projects/ScrobbleScope/.venv/Scripts/python.exe scripts/doc_state_sync.py --check
git add .claude/SESSION_CONTEXT.md PLAYBOOK.md
git commit -m "docs(runtime): Record the shared thread-loop protocol"
```

Stage only the paths this task actually changed. If a documentation file turned out to need no edit,
leave it out of `git add` -- do not stage a file to make the commit look complete.

---

## Acceptance

- `worker.run_coroutine_in_new_loop` exists, is unit-tested, and its six tests fail if its body is removed.
- Both background entry points call it, each passing `make_loop`, `release_slot` and `on_run_error` explicitly.
- **No existing test is modified by any task.** Across the branch, `git diff --stat tests/` shows only
  the additions in `tests/test_worker.py`.
- The full suite passes, and the newest `PLAYBOOK.md` Section 4 entry carries `**N passed**` measured
  by a real `pytest -q`.
- `pre-commit run --all-files` exits 0 and `doc_state_sync.py --check` exits 0 (the root
  `BATCH23_DEFINITION.md` warning is the one expected line).
- The behaviour the guard tests pin is unchanged, including both asymmetries: a failing `loop.close()`
  propagates out of both entry points, and the heatmap path still reports `lastfm_unavailable` for a
  failed run.

## Deliberately out of scope

- **The second half of F-SWE-5.** Unifying the terminal outcome is a behaviour change. After this plan
  it is small -- one `_report_*` function per entry point, plus the `ERROR_CODES` entry for an
  unclassified internal fault -- and it should be its own commit with its own findings update, not a
  rider on a refactor that promised tests would pass unmodified.
- **`release_checks._worker_loop`.** It builds one loop and drains a queue for the lifetime of the
  process, so a one-shot wrapper is the wrong shape. Leaving it alone is the answer, not an omission,
  and Task 4 should not claim it shares the protocol.
- **Batch 23 WP-0's other extractions** -- `_cap_threshold_exclusions`, `_process_filtered_albums`,
  `_zero_fill_daily_counts`. This plan covers only the run-and-close wrapper, the piece WP-0 would
  otherwise place in `orchestrator/` while the heatmap path kept its own copy.
