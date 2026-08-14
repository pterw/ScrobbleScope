# Batch 9 Audit Remediation Plan (2026-02-20)

Owner intent: convert the 2026-02-20 comprehensive repo audit into an execution-ready plan that another agent can follow without additional context.

## 1. Scope and goals

Primary goals:
- Reduce production risk (security + reliability) without behavior regressions.
- Close correctness gaps identified in backend and frontend audit.
- Improve operational safety and maintainability (lint/CI/dependency hygiene).

Out of scope for Batch 9:
- Large UX redesigns.
- Major architecture migration (e.g., full service decomposition).

Execution rules:
- Implement one work package at a time.
- Keep commits small and reversible.
- Run validation after each package:
  - `venv\Scripts\pre-commit run --all-files`
  - `venv\Scripts\python -m pytest tests -q`

## 2. Prioritized work packages

## ~~WP-1 (P0): Bound background job concurrency~~ [DONE - 2026-02-19]

Problem:
- `results_loading` spawns unbounded daemon threads per request, which can exhaust CPU/memory under burst traffic.

Files:
- `scrobblescope/config.py`
- `scrobblescope/repositories.py` or new `scrobblescope/job_limits.py`
- `scrobblescope/routes.py`
- `scrobblescope/orchestrator.py`
- `tests/test_routes.py`

Implementation steps:
1. Add env-tunable capacity (e.g., `MAX_ACTIVE_JOBS`, default conservative value).
2. Track active jobs with thread-safe acquire/release logic.
3. Reject new jobs when capacity is reached with clear, retryable message.
4. Ensure release in all terminal paths (`finally` in background worker).
5. Add route tests for accepted vs capacity-rejected requests.

Acceptance criteria:
- Under synthetic burst, active job count is capped.
- Rejected requests fail gracefully with user-facing guidance.
- No leaked active slots after worker exceptions.

## ~~WP-2 (P0): Make request cache thread-safe~~ [DONE - 2026-02-19]

Problem:
- `REQUEST_CACHE` is shared across threads without locking; cleanup and writes can race.

Files:
- `scrobblescope/utils.py`
- `tests/test_repositories.py` or new `tests/test_utils.py`

Implementation steps:
1. Add a lock around all cache read/write/cleanup operations.
2. Avoid iterating a mutating dict without synchronization.
3. Keep current cache semantics unchanged (TTL + key format).
4. Add tests covering concurrent-like access behavior and cleanup safety.

Acceptance criteria:
- No dict-size-change runtime errors under concurrent paths.
- Cache hit/miss behavior remains unchanged functionally.

## ~~WP-3 (P0): Add CSRF protection for mutating POST routes~~ [DONE - 2026-02-19]

Problem:
- Forms and POST endpoints currently have no CSRF safeguards.

Files:
- `app.py`
- `templates/index.html`
- `templates/results.html`
- `templates/loading.html` (if needed)
- `scrobblescope/routes.py`
- `static/js/loading.js` (for `/reset_progress` POST)
- tests for affected routes

Implementation steps:
1. Integrate CSRF protection (Flask-WTF or equivalent robust middleware).
2. Add CSRF tokens to HTML forms and JS POST requests.
3. Ensure error responses are user-safe on CSRF failure.
4. Update route tests for protected POST behavior.

Acceptance criteria:
- Cross-site POST without valid token fails.
- Normal in-app POST flows continue to work.

## ~~WP-4 (P1): Harden app secret and startup safety~~ [DONE - 2026-02-20]

Problem:
- App falls back to insecure `SECRET_KEY="dev"` when unset.

Files:
- `app.py`
- `.env.example`
- `README.md`
- tests for app factory/startup behavior

Implementation steps:
1. Fail startup in non-dev mode when `SECRET_KEY` is missing or weak default.
2. Keep local-dev ergonomics explicit (documented opt-in dev behavior).
3. Update setup docs and tests accordingly.

Acceptance criteria:
- Production-like startup refuses insecure secret config.
- Local developer instructions remain clear and functional.

## ~~WP-5 (P1): Enforce registration-year validation server-side~~ [DONE - 2026-02-20]

Problem:
- Frontend validates min year from registration, but server currently only enforces `2002..current_year`.

Files:
- `scrobblescope/routes.py`
- possibly `scrobblescope/lastfm.py` (if helper reuse needed)
- `tests/test_routes.py`

Implementation steps:
1. Validate submitted year against Last.fm registration year in backend.
2. Return clear error message on invalid lower year.
3. Keep existing client-side validation as UX enhancement, not source of truth.

Acceptance criteria:
- Submissions below registration year are rejected server-side.
- Existing valid flows remain unchanged.

## ~~WP-6 (P1): Remove or gate artificial orchestration sleeps~~ [DONE - 2026-02-20]

Problem:
- Multiple fixed `asyncio.sleep(0.5)` calls add avoidable latency to all jobs.

Files:
- `scrobblescope/orchestrator.py`
- tests for progress behavior if timing assumptions exist

Implementation steps:
1. Remove fixed sleeps, or gate with a debug-only UX flag.
2. Preserve progress-state ordering/messages.
3. Verify no regression in loading-page UX.

Acceptance criteria:
- End-to-end runtime improves measurably.
- Progress transitions remain coherent for users.

## ~~WP-7 (P2): Frontend safety and resilience polish~~ [DONE - 2026-02-20]

Problem:
- Some UI rendering paths still rely on HTML insertion patterns that are fragile.

Files:
- `static/js/results.js`
- `static/js/loading.js`
- `static/js/index.js`
- relevant templates/tests

Implementation steps:
1. Convert toast rendering to safe DOM/text-node construction.
2. Handle non-200 responses explicitly in unmatched fetch flow.
3. Normalize text/encoding artifacts in user-facing strings.
4. Add focused JS behavior tests where feasible (or route/template assertions + manual checklist).

Acceptance criteria:
- No unsanitized user-derived HTML injection pathways in JS.
- Error states are accurately surfaced (not silently shown as "no data").

## ~~WP-8 (P2): CI, lint, dependency hygiene~~ [DONE - 2026-02-20]

Problem:
- Tooling config has inconsistencies (e.g., ineffective `check-yaml` hook); dependencies are not split by runtime/dev concerns.

Files:
- `.pre-commit-config.yaml`
- `.github/workflows/test.yml`
- `requirements.txt`
- add `requirements-dev.txt` (recommended)
- `.gitignore` (include `.coverage`)
- docs updates

Implementation steps:
1. Fix `pre-commit` hook file selectors (`check-yaml` should target YAML files).
2. Add/adjust coverage gate (initial realistic threshold).
3. Split runtime vs dev/test dependencies.
4. Add `.coverage` ignore rule.

Acceptance criteria:
- CI checks reflect intended policy and run on correct files.
- Dependency install paths are clearer and leaner.

## 3. Suggested execution order

Recommended order:
1. WP-1
2. WP-2
3. WP-3
4. WP-4
5. WP-5
6. WP-6
7. WP-7
8. WP-8

Rationale:
- P0 items reduce immediate security/reliability risk first.
- P1 items close correctness/perf gaps with moderate blast radius.
- P2 items tighten tooling and frontend hardening last.

## 4. Validation checklist for each package

- Unit/integration tests pass:
  - `venv\Scripts\python -m pytest tests -q`
- Style/lint hooks pass:
  - `venv\Scripts\pre-commit run --all-files`
- Docs updated when behavior/config changes:
  - `README.md`
  - `.claude/SESSION_CONTEXT.md`
  - `PLAYBOOK.md`

## 5. Handoff note for next agent

When executing Batch 9:
- Treat this file as the task contract.
- Update `PLAYBOOK.md` execution log after each completed work package.
- Keep changes batch-scoped and avoid combining unrelated remediations in one commit.
