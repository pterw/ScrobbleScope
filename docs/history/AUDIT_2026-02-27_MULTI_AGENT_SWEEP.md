# Multi-Agent Quality Sweep - 2026-02-27

## Scope

Comprehensive sweep across orchestration docs, modular docsync implementation,
CI behavior, runtime architecture, and test suite quality with focus on:

- drift resistance
- token discipline
- SoC/DRY boundaries
- horizontal scaling constraints
- static-quality/Pylance-style issues
- docsync correctness and test fit

## Executive summary

Overall architecture is strong and useful. The repo has a solid external-memory
contract (`AGENTS.md` rules, `PLAYBOOK.md` work order, `SESSION_CONTEXT.md`
dashboard), and modular docsync is implemented correctly (`scripts/docsync/*`
plus thin wrapper entrypoint).

Main risks are no longer conceptual -- they are operational and scale-bound:

1. Long, dense docs and oversized modules are starting to re-introduce token drag.
2. In-memory job state (`JOBS`) constrains true horizontal scale.
3. Exception handling is intentionally fail-open in places, but broad catches
   reduce diagnosability.
4. Docsync tests are strong but one file (`test_docsync_logic.py`) is becoming
   a maintenance hotspot by size.

## State alignment check

### Good

- Branch/state is effectively between batches with side-task patching.
- Test baseline is aligned at 310 passing.
- `doc_state_sync --check` behavior is healthy and non-blocking warnings are
  functioning.
- `scripts/doc_state_sync.py` is a thin entrypoint delegating to the modular
  package (`scripts/docsync`).

### Drift/mismatch found

- `PLAYBOOK.md` Section 3 previously had redundant completion wording and did
  not explicitly call out between-batch patch mode.
- `SESSION_CONTEXT.md` had stale "Last updated" date and "Known open risk: None"
  despite root BATCH-file warning currently emitted by docsync checks.
- `AGENTS.md` had good bootstrap order but lacked explicit token-budget guardrails
  in that section.

### Cleanup applied in this sweep

- Added token-discipline bootstrap bullets to `AGENTS.md`.
- Updated `SESSION_CONTEXT.md` date and open-risk row.
- Tightened `PLAYBOOK.md` Section 3 language to explicitly describe
  between-batches patch mode.

## docsync deep-dive (modularization quality)

## Architecture quality

The refactor is real and correctly shaped:

- `scripts/docsync/models.py`: dataclasses and `SyncError`
- `scripts/docsync/parser.py`: regex/marker/entry parsing
- `scripts/docsync/renderer.py`: markdown rendering and status block creation
- `scripts/docsync/logic.py`: pure sync/cross-validate/core transforms
- `scripts/docsync/cli.py`: argparse, path constants, file I/O, mode orchestration
- `scripts/doc_state_sync.py`: wrapper-only entrypoint

This is an appropriate SoC split and a strong improvement over monolith behavior.

## Behavioral correctness observations

- `--check`, `--fix`, and `--split-archive` mode separation is clear.
- Missing `.claude/SESSION_CONTEXT.md` is handled via optional reads,
  supporting CI environments where it is absent.
- Tagged entries route to per-batch logs; untagged entries remain in monolith
  archive. This is the right policy for token control and archive retrieval.
- Duplicate marker detection exists and fails fast (good safety).

## Remaining docsync risks

1. `_latest_test_count_from_entries` depends on entry file order being newest-first.
   If entry order is manually reversed, count extraction can be stale.
2. Root `BATCH*.md` warning is useful, but warning-only means root drift can persist
   if not acted on.
3. Several internal helpers are prefixed private (`_name`) but form de facto API
   for tests; this is acceptable but should be acknowledged as intentional.

## Test suite fitness and duplication

## Strengths

- docsync test coverage is broad and adversarial (marker duplication, malformed
  headings, split-archive, missing session file, mismatch checks).
- docsync test suite currently passes fully (103 docsync-focused tests in this sweep).
- Tests generally validate behavior/state effects, not only mock calls.

## Consolidation opportunities

1. `tests/test_docsync_logic.py` is large (782 lines) and now covers many concerns
   (_sync integration, cross-validate, split/merge helpers, count extraction).
   Suggested split:
   - `test_docsync_sync_integration.py`
   - `test_docsync_cross_validate.py`
   - `test_docsync_archive_routing.py`
2. Some scenario setup blocks repeat long inlined PLAYBOOK strings; small factory
   helpers could reduce noise without reducing test depth.
3. Duplicate fixture-like content appears across parser/logic tests; centralizing
   tiny builders in `tests/helpers.py` would improve maintainability.

## Runtime SoC/DRY/code-smell findings

## High impact

1. `scrobblescope/orchestrator.py` (~906 lines) remains an oversized orchestration
   hub with mixed responsibilities (workflow control, business rules,
   result shaping, error classification).
2. Global mutable state for job handling in `scrobblescope/repositories.py`
   (`JOBS`, `jobs_lock`) limits scale-out and introduces single-process coupling.
3. `app.py` performs side-effectful logging/config setup at import time,
   reducing app-factory purity and potentially complicating multi-worker runtime
   behavior.

## Medium impact

4. Broad exception catches in runtime paths (`routes.py`, `orchestrator.py`,
   `lastfm.py`, `utils.py`, `worker.py`, `cache.py`) protect UX but can mask
   root-cause classes and reduce observability granularity.
5. `run.py` contains duplicated startup/browser-open behavior and is mostly
   developer convenience; ensure it is never used as production entrypoint.
6. `spotify_token_cache` global dict in `config.py` is process-local; across
   workers/instances this causes redundant token refreshes (acceptable now,
   but not ideal at higher scale).

## Horizontal scaling assessment

Current model is robust for single-instance / modest concurrency, but constraints
for true horizontal scaling are clear:

1. In-memory `JOBS` cannot be shared across instances; progress polling and
   results retrieval break if requests land on different nodes.
2. In-memory request cache and per-process throttles are not globally coherent.
3. Thread + per-job event loop model is bounded and workable, but increases
   operational complexity as concurrency rises.

Recommended migration path:

- move job state/progress/results to Redis or Postgres-backed job table
- pin progress polling via shared store (remove process affinity)
- consider worker queue model (RQ/Celery/Arq) once top-songs/heatmap add load

## Pylance/static quality sweep

- Workspace diagnostics currently report no active errors.
- No immediate typing breakages detected in this sweep.
- Main static-quality pressure is architectural (module size, broad catches)
  rather than type-system breakage.

## CI and .gitignore behavior

CI uses `pre-commit`, `flake8`, and `pytest --cov` on pull requests and main.
Given current modular docsync implementation and optional session-context read,
CI should remain stable even when `.claude/SESSION_CONTEXT.md` is absent.

One operational note:

- CI uses Python 3.11 while local target/runtime notes include Python 3.13.
  This is not currently breaking tests, but version drift can hide edge-case
  behavior. Consider aligning or explicitly documenting this intentional split.

## Token-bloat and drift prevention verdict

Your orchestration system is useful and well-implemented. It is not "ceremonial"
documentation; it is operational control-plane documentation.

What is working well:

- deterministic state regeneration via docsync
- strict source-of-truth boundaries
- active-window log rotation
- archive partitioning by batch

Main next-step to preserve quality over time:

- keep active docs short and current
- keep Section 3/4 focused on immediate execution only
- split oversized code/test files before they become hidden drift sources

## Priority action list

### P0 (do now)

1. Keep `PLAYBOOK` Section 3 explicitly in between-batch patch mode until next
   batch is defined.
2. Maintain `SESSION_CONTEXT` current-state rows immediately after patch side-tasks.

### P1 (next maintenance batch)

4. Split `tests/test_docsync_logic.py` into narrower files by concern.
5. Extract another logical slice from `scrobblescope/orchestrator.py`
   (result shaping or exception classification would be low-risk first targets).
6. Add a short "operator mode" flag in docsync (`between-batches`, `active-batch`)
   if you want stricter checks tied to mode.

### P2 (scaling roadmap)

7. Design migration of `JOBS` from in-memory dict to shared store.
8. Evaluate distributed rate-limit strategy if multi-instance API pressure grows.
9. Align CI Python version with production/runtime target or document rationale.

## Revalidation addendum - 2026-02-27

Post-audit follow-through completed for archive topology:

- Canonical untagged archive path is now
   `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`.
- Legacy monolith files at `docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`
   and `docs/history/logs/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` were converted to
   pointer documents to avoid broken references.
- `scripts/docsync/cli.py` now routes archive reads/writes to
   `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`.
- Cross-validation archive-link checks now support both `docs/history/*.md`
   and `docs/logarchive/*.md` links.
- Stale `SESSION_CONTEXT.md` drift is now warning-only and treated as
   local-only dashboard state (do not commit stale session state).

Audit finding status after this revalidation:

- **Resolved:** monolith archive path ambiguity and mixed-location confusion.
- **Resolved:** root `BATCH14_PROPOSAL_AUDIT1.md` archival follow-up is complete
   (`docs/history/BATCH14_PROPOSAL_AUDIT1.md` exists, no root copy remains).
- **Still valid:** token-discipline, oversized-module, in-memory-job-state,
   and broad-exception handling findings.
- **Still valid:** test-maintenance hotspot observation for
   `tests/test_docsync_logic.py` size.

Verification rerun (post-change):

- `python scripts/doc_state_sync.py --fix` -> clean
- `python scripts/doc_state_sync.py --check` -> pass
- `pytest -q tests/test_docsync_cli.py tests/test_docsync_logic.py`
   `tests/test_docsync_parser.py tests/test_docsync_renderer.py` ->
   **103 passed**
- `pre-commit run --all-files` -> pass (all hooks)
- `pytest -q` -> **310 passed** (3 warnings)

## Next-agent implementation packet

Use this ordered queue for the next handoff; each item is scoped to a
single commit-sized change.

1. **Split docsync logic tests by concern**
    - Target: break `tests/test_docsync_logic.py` into integration vs
       cross-validation vs archive-routing modules.
    - Acceptance: zero behavior change; test count unchanged; full suite green.

2. **Extract one low-risk orchestrator slice**
    - Target: pull either result-shaping or exception-classification helpers
       from `scrobblescope/orchestrator.py` into a dedicated module.
    - Acceptance: no route/API behavior changes; equivalent progress and
       error semantics; existing orchestrator/service tests remain green.

3. **Write explicit CI/session policy note**
    - Target: document the intended contract that `SESSION_CONTEXT.md` may be
       stale/local-only while PLAYBOOK/docsync remain enforceable in CI.
    - Acceptance: policy wording aligned across AGENTS/DEVELOPMENT/PLAYBOOK;
       no contradiction about what CI must enforce.
