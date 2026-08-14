# worker.py Architectural Decision Record

Date: 2026-02-20
Source: Archived from `.claude/SESSION_CONTEXT.md` Section 7b on 2026-02-22.

---

## Decision

Extract concurrency lifecycle into `scrobblescope/worker.py`.

## Rationale

The confirmed product roadmap adds at least two new background task types
(top songs, listening heatmap). Without `worker.py`, every new route that
spawns a background task must duplicate the acquire -> try-Thread-start ->
except-release pattern. With `worker.py`, all routes call
`start_job_thread(target_fn, args)` -- one call, no duplication.

## What worker.py owns

- `_active_jobs_semaphore = threading.BoundedSemaphore(MAX_ACTIVE_JOBS)`
- `acquire_job_slot()` -- non-blocking acquire, returns bool; called in
  routes.py before `create_job()` to avoid orphaned jobs on capacity
  rejection
- `release_job_slot()` -- safe release with over-release guard; called in
  orchestrator.py `background_task` finally block
- `start_job_thread(target, args=())` -- starts daemon Thread(target, args),
  releases slot and raises on Thread.start() failure

## What repositories.py keeps

Pure job state CRUD only (`create_job`, `set_job_*`, `get_job_*`,
`add_job_unmatched`, `reset_job_state`, `cleanup_expired_jobs`, `jobs_lock`,
`JOBS`). `jobs_lock` stays in repositories because it guards the JOBS dict
(data concern), whereas the semaphore guards worker slots (concurrency
concern).

## Patch target convention (as-implemented)

Tests patch at the module where the name is looked up. `acquire_job_slot` is
imported into `routes.py` via `from scrobblescope.worker import ...`, so the
patch target is `scrobblescope.routes.acquire_job_slot`. Similarly,
`release_job_slot` is imported into `orchestrator.py`, so the patch target is
`scrobblescope.orchestrator.release_job_slot`. Direct `start_job_thread`
failures are tested by patching `scrobblescope.routes.start_job_thread`.
