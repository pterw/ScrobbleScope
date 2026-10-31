<!-- DOCSYNC:ARCHIVE-PAGE v1 -->
# BATCH22_LOG -- page 0003

### 2026-09-20 - The release-check JSON endpoint (Batch 22 WP-4)

Scope: `docs/superpowers/plans/2026-09-13-batch22-enrichment-providers.md`
Task 10, the first task of WP-4. `GET /api/release_checks?job_id=` serves the
correction worker's findings to a results page that is already open. Task 11
consumes it; nothing renders these yet.

`scrobblescope/routes/api.py`: the endpoint returns `{status, checked, total,
moved_in, albums}`, where each album carries `key`, `state` and
`original_release_date`. It lists only results the worker has ruled on --
a result still `unchecked` is omitted, because the page has already rendered
every row and the only thing it needs back is what changed.

`scrobblescope/domain.py`: `format_album_key` returns the `artist|album` wire
form of a normalized key. The endpoint and Task 11's `data-album-key` must
name an album identically, so the join lives in one function rather than
being spelled the same way in two places. The separator is safe by
construction: `normalize_name` replaces every ASCII punctuation character
with a space, so neither half can contain a pipe.

**Deviation 1 -- the plan says the endpoint "reuses
`_get_validated_job_context` for ownership and mode checks". It does not.**
That helper renders `error.html` and returns HTML on both its failure paths,
which a polling client cannot read. The endpoint does the same two checks
(unknown job, wrong mode) and answers in JSON, as `/progress` and
`/api/unmatched` beside it already do. Ownership is unchanged from every
other job endpoint: the 128-bit job ID is the capability and there is no
session check. F-B22-3 holds that open question for the owner; this task
did not decide it one way or the other.

**Deviation 2 -- an error body carries `"status": "error"`.** The plan
specifies no error shape. The word is deliberately not one of the worker's
own four, so Task 11's poller stops on it by the same rule that stops it on
any status it does not recognise.

**`pending` is the fifth status, and the worker never writes it.**
`BATCH22_DEFINITION.md` WP-3 lists `pending` among the states to expose, but
the worker publishes `running`, `done` or `skipped` and publishes nothing at
all before it starts. `pending` is what the endpoint reports while
`progress.stats.release_check` is absent -- the gap between a job publishing
results and the worker first reporting on them. `STATUS_PENDING` is declared
in `scrobblescope/release_checks.py` with the other three so the vocabulary
stays in one module.

**Task 9 extended, under this task.** The worker wrote only
`{"release_check": outcome}`, so no corrected date ever reached the result
and the endpoint had nothing to serve: a moved-out row would have shown the
provider's reissue date while claiming to be a correction of it. Both
settling paths in `scrobblescope/release_checks.py` now write
`original_release_date` alongside the outcome -- the live one in
`_check_candidate`, the cached one in `_resolve_cached` -- and an
`unavailable` result records None rather than keeping a value the new
outcome contradicts. Seven lines, inside WP-4's own dependency, so it is an
in-WP deviation under AGENTS.md Proposal and Design Rules item 2 rather than
a new work package.

Tests (+9): seven in `tests/test_routes.py` covering the missing-ID 400, the
unknown-job and heatmap-job 404s in JSON rather than HTML, the `pending`
default, the filtering of unchecked results, the normalized key on an album
whose title is all punctuation and metadata words, and a result with no
`_normalized_key` being skipped instead of crashing the endpoint. Two in
`tests/services/test_release_checks.py` assert the date behind each of the
three outcomes and the same field written from a cache hit without spending
a request.

Validation: `pytest -q` -- **1506 passed** (was 1497; +9 new). The managed
STATUS block and the three hand-written count fields still read 1497, and
that is not drift: the untagged side-task entry below the end marker is also
dated 2026-09-20 and claims 1497, and on a same-date tie source precedence
ranks a side-task entry above any current-batch entry regardless of which
was written later. This is **F-DOCSYNC-11** (open, P1), not a new defect,
and its own stated remedy is to publish the superseded number and let the
entry carry the true one -- the Task 8 entry above did the same thing on the
same mechanism. DOC005/DOC006/DOC008 recompute that authority and reject a
hand-written 1506. `ruff check` and `ruff format` clean. The frontend gate was not rerun: nothing under
`templates/` or `static/` changed, so Task 11 is where it next earns its
run. `doc_state_sync.py --check` exit 0 (the root `BATCH22_DEFINITION.md`
warning is expected while the batch is active).

Forward guidance: Task 11 renders this. It needs `data-album-key` on each
results row carrying `format_album_key`'s output, a status line reading
"Checking original release years: N of M" from `checked`/`total`, per-row
markers that do not move a row, and the moved-in announcement from
`moved_in` with a reload action. Polling stops on `done`, on `skipped`, on
any unrecognised status, and on a failed request.
