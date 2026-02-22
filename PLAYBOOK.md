# ScrobbleScope Execution Playbook (Post-Compact Handoff)

Date: 2026-02-11
Owner context: This playbook defines the implementation order, standards, and guardrails for the next major batches.
Primary goal: Improve reliability, UX, and maintainability without behavior regressions, then refactor monolithic `app.py` safely.

## 1. Why this document exists
- Provide a single source of truth for work sequencing.
- Enable continuation by another agent with minimal context loss.
- Prevent risky refactor-first changes before parity tests exist.

## 1b. Document roles (anti-drift contract)
- `PLAYBOOK.md`: active execution contract (batch order, standards, active log window, next actions).
- `.claude/SESSION_CONTEXT.md`: concise current-state snapshot (status, architecture, risks, environment notes).
- `README.md`: product and setup reference for users/developers, not batch execution history.
- `AGENTS.md`: agent behavior rules (bootstrap order, commit style, markdown and update duties).

## 2. Current status snapshot
- `app.py` is a minimal factory (~142 lines): `create_app()` + logging setup + `CSRFProtect` init + secret-key startup guard + `app = create_app()` for Gunicorn compat.
- All application logic lives in the `scrobblescope/` package (11 modules including package marker, acyclic dependency graph).
- Routes use a Flask Blueprint (`scrobblescope/routes.py`).
- Per-job in-memory state in `scrobblescope/repositories.py` (`JOBS` dict).
- Orphan job on thread-start failure: resolved 2026-02-20. `delete_job(job_id)` added to `repositories.py` and called in `routes.results_loading` except block.
- No app-level keep-alive thread is present; `results_loading` spawns one daemon worker per job and `background_task` owns a single event loop on that worker thread.
- Persistent Spotify metadata cache (Postgres via asyncpg, `scrobblescope/cache.py`):
  - `spotify_cache` table with 30-day TTL, batched reads/writes via `unnest()`.
  - DB connection wake-up hardening: `_get_db_connection()` retries with exponential backoff before cache bypass.
  - Graceful fallback: if `DATABASE_URL` is unset, `asyncpg` is unavailable, or DB is unreachable, full Spotify flow runs.
  - `_get_db_connection()` emits classified fallback logs for `missing-env-var`, `asyncpg-missing`, and `db-down`.
  - Full DB cache hits can complete without Spotify availability.
  - If Spotify is unavailable while cache hits exist, cached results still return with `partial_data_warning`.
  - Schema automated via `init_db.py` release_command on Fly deploys.
- Fly cold-start recovery was validated on 2026-02-19 by manually stopping both app and DB machines, then triggering one end-to-end smoke run that auto-started both and completed successfully (`elapsed=18.75s`, `db_cache_lookup_hits=247`).
- `tojson` JS data bridge is in place in templates.
- Unmatched modal has escaping in `static/js/results.js`.
- Nested thread pattern removed:
  - Outer worker thread remains in `results_loading`.
  - `background_task` now owns one event loop directly (no inner thread).
- Dark-mode toggle now uses a compact fixed bottom placement across pages; label auto-hides on extra-small screens.
- `index.html` now renders server-side validation errors (Batch 6).
- Historical audit/changelog/refactor docs are archived under `docs/history/` to reduce repo-root clutter.
- Comprehensive repo audit completed on 2026-02-20; remediation execution plan is documented at `docs/history/BATCH9_AUDIT_REMEDIATION_PLAN_2026-02-20.md`.
- Test suite: **121 tests** across 9 files (`test_app_factory.py`, `test_domain.py`, `test_repositories.py`, `test_utils.py`, `test_routes.py`, `tests/services/test_lastfm_service.py`, `tests/services/test_lastfm_logic.py`, `tests/services/test_spotify_service.py`, `tests/services/test_orchestrator_service.py`) covering job lifecycle, routes (including unmatched_view + 404/500 handlers + CSRF enforcement on all 4 POST routes + registration-year validation), normalization (including non-Latin character preservation and artist-name integrity), error classification, template safety, background task structure, reset flow, async service retry paths, DB helpers, cache integration, orchestrator correctness, DB connect retry/backoff behavior, thread-safe cache operations, concurrency slot lifecycle, app-factory secret-key startup guard, and fetch_top_albums_async aggregation/filter/timestamp logic.
- **Product roadmap (confirmed 2026-02-20):** Two new background task types are planned:
  - **Top songs:** Rank user's most-played tracks for a year (Last.fm + possibly Spotify enrichment). Separate background task type, separate loading/results flow.
  - **Listening heatmap:** Calendar-style scrobble density map for the last 365 days. Last.fm API only (no Spotify), lighter background task.
- `scrobblescope/worker.py` (leaf module, imports `config` only) owns `_active_jobs_semaphore`, `acquire_job_slot()`, `release_job_slot()`, and `start_job_thread()`. `repositories.py` is pure job state CRUD. See architectural rationale in `.claude/SESSION_CONTEXT.md` Section 7b.

## 3. Non-negotiable implementation principles
1. Approval tests before structural refactor.
2. No behavior-breaking refactors without parity checks.
3. Add observability before optimization where possible.
4. Keep changes batch-scoped and reversible.
5. Keep security-safe rendering (`tojson`, escaping) as baseline.

## 4. High-level batch order (strict sequence)

Completed batch definitions are archived individually under `docs/history/`.

### Completed batches (definitions archived)

| Batch | Title | Definition |
|-------|-------|------------|
| 0 | Baseline freeze + approval parity suite | `docs/history/BATCH0_DEFINITION.md` |
| 1 | Proper upstream failure state + retry UX | `docs/history/BATCH1_DEFINITION.md` |
| 2 | Personalized minimum listening year | `docs/history/BATCH2_DEFINITION.md` |
| 3 | Remove nested thread pattern | `docs/history/BATCH3_DEFINITION.md` |
| 4 | Expand test coverage significantly | `docs/history/BATCH4_DEFINITION.md` |
| 5 | Docstring + comment normalization | `docs/history/BATCH5_DEFINITION.md` |
| 6 | Frontend refinement/tweaks | `docs/history/BATCH6_DEFINITION.md` |
| 7 | Persistent metadata layer (Postgres) | `docs/history/BATCH7_DEFINITION.md` |
| 8 | Modular refactor (app factory + blueprints) | `docs/history/BATCH8_DEFINITION.md` |
| 9 | Audit remediation (WP-1 through WP-8) | `docs/history/BATCH9_DEFINITION.md` |
| 10 | Gemini audit remediation (WP-1 through WP-9) | `docs/history/BATCH10_DEFINITION_2026-02-21.md` |

## 5. Suggested implementation granularity
- Keep PRs or commits small per batch.
- Do not mix architecture refactor with behavior changes in one step.
- Re-run:
  - `pre-commit run --all-files`
  - `pytest -q`
after each batch.

### Commit message standard
All commits must follow the Conventional Commits + imperative-mood convention:

```
<type>(<optional scope>): <subject>   <- max 72 chars, imperative mood

<body>                                 <- wrap at 72 chars; explain WHY
                                         not just what
```

**Types:** `feat`, `fix`, `refactor`, `test`, `chore`, `docs`, `style`, `perf`

**Subject rules (enforced):**
- Imperative mood: "Add", "Fix", "Remove", "Extract" -- NOT "Added", "Fixes", "Introducing"
- No period at the end
- No project-management metadata in the subject (`WP-1 (P0):` belongs in the body)
- Max 72 characters on the subject line

**Body rules:**
- Separated from subject by a blank line
- Explain the motivation and what changed, not just a file list
- File-level bullet lists are acceptable for specificity
- Wrap lines at 72 characters

**Examples:**
```
feat: bound background job concurrency and extract worker module

Introduce MAX_ACTIVE_JOBS (default 10, env-tunable) to cap concurrent
background jobs. Extract concurrency lifecycle into worker.py ahead of
planned top-songs and listening-heatmap features.
```
```
fix: release job slot when Thread.start() raises in results_loading

If Thread.__init__ or Thread.start() raises after acquire_job_slot()
succeeds, the slot was permanently consumed. Wrap thread creation in
try/except and call release_job_slot() before returning the error page.
```

## 6. Open decisions (owner confirmation needed)
1. Persistent store choice now: Postgres only or Postgres + Redis.
2. Retry UX policy:
   - immediate retry button only,
   - or retry + cooldown messaging.
3. ~~Whether to keep `results_loading` progress spoof sleeps or remove once UX states improve.~~ Resolved in WP-6: all 5 `asyncio.sleep(0.5)` calls removed.
4. Error copy style and user-facing tone for upstream failures.

## 7. Agent handoff checklist before starting a batch
1. Read:
   - `.claude/SESSION_CONTEXT.md`
   - `PLAYBOOK.md` (this file)
   - `docs/history/AUDIT_2026-02-11_IMPLEMENTATION_REPORT.md` (historical snapshot; may lag latest batch log in this file)
   - `docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` (when active-window history is insufficient)
   - `README.md` (product expectations, deployment context, known limitations)
2. Inspect current implementation hotspots in modular files before editing:
   - `scrobblescope/repositories.py` (job state lifecycle: `JOBS`, TTL cleanup)
   - `scrobblescope/routes.py` (`/progress`, `/results_complete`, `/unmatched_view`, error handlers)
   - `scrobblescope/orchestrator.py` (`background_task`, async pipeline, cache-hit/miss flow)
   - `scrobblescope/lastfm.py`, `scrobblescope/spotify.py`, `scrobblescope/cache.py` (API/cache path)
3. Confirm latest completed batches in this playbook before trusting older docs.
4. Confirm repo is green:
   - `pre-commit run --all-files`
   - `pytest -q`
5. Confirm no unrelated local edits are reverted.
6. Implement one batch only.
7. Provide post-batch summary:
   - behavior change
   - files touched
   - tests added/updated
   - verification results

## 8. Batch completion logging standard
After each completed batch, update this playbook immediately.
All commits must comply with the commit message standard in Section 5.
1. Status update:
   - Strike through the completed batch title in Section 4.
   - Update "Immediate next batch to execute."
2. Snapshot update:
   - Update Section 2 only for material architecture/runtime state changes.
3. Required cross-doc sync after behavior/config/process changes:
   - Update `.claude/SESSION_CONTEXT.md` for current-state accuracy and risk notes.
   - Update `README.md` for setup, runtime, or user-visible behavior changes.
   - Keep `PLAYBOOK.md` as the active execution contract and log source.
4. Add one dated entry under "Batch execution log" with:
   - scope
   - plan vs implementation
   - deviations and why they were taken
   - additions beyond plan
   - struggles/constraints and unresolved risks
   - validation performed
   - forward guidance for the next agent
5. Document stale references:
   - Keep historical docs; do not delete.
   - Mark here whether a doc is historical baseline vs current source of truth.

### Markdown authoring rules (agent-facing)
- Use ASCII-only characters in markdown files. Replace smart punctuation with plain ASCII (`--`, `->`, `<-`, quotes).
- Use ISO dates: `YYYY-MM-DD`.
- Batch/execution log entries must include: scope, plan vs implementation, deviations (if any), validation, and forward guidance.
- If requirements are ambiguous, ask clarifying questions before writing docs that change process/state contracts.
- When adding new dated entries, archive-rotate old non-active entries into `docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` to maintain the active-window policy in Section 10.
- After any Section 10 update, run `python scripts/doc_state_sync.py --fix`, then re-run checks.

## 9. Immediate next batch to execute
- **Batch 10 is complete.** All 9 WPs done, 121 tests passing.
  Definition and completion record: `docs/history/BATCH10_DEFINITION_2026-02-21.md`.
  Execution logs: `docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`.
- **Batch 11 is in progress** (Gemini 3.1 Pro Priority 2 audit remediation --
  SoC, DRY, and architectural findings).
  - WP-1 (Low): CSS/JS theme consolidation. Done. (Created `global.css` +
    `theme.js`; stripped ~250 lines of duplicate CSS from 5 per-page files;
    removed dark-mode toggle JS from 5 JS files; fixed html2canvas mobile
    export; added back-to-top button on results page. 121 tests passing.)
  - WP-2 (Medium): Decompose `process_albums` in `orchestrator.py`. Pending.
  - WP-3 (Low): CSS/JS DRY violations, toggle markup bug, and UX polish.
    Done. (Promoted `--info-bg` to `global.css`, removing split `:root`/
    `.dark-mode` blocks from `results.css` and hard-coded rgba from
    `loading.css`; moved duplicate modal dark-mode block from `index.css`
    and `results.css` to `global.css`; stripped Bootstrap `form-check
    form-switch` classes from toggle markup that conflicted with custom CSS
    via Bootstrap's injected SVG background-image knob; added `text-align:
    center` to loading-page `.step-text`/`.step-details`; removed redundant
    mobile release-date shortening JS from `results.js`; `var`->`const` for
    `darkSwitch`/`backToTop` in `theme.js`; dark-mode toggle track changed
    from `var(--bars-color)` to `var(--bg-color)` when checked. 121 tests
    passing.)
- Future batch feature candidates (confirmed by owner roadmap, batch number TBD):
  - **Top songs**: rank most-played tracks for a year (Last.fm + possibly Spotify enrichment, separate background task + loading/results flow).
  - **Listening heatmap**: scrobble density calendar for last 365 days (Last.fm-only, lighter background task).
- Do not start feature work (top songs, heatmap) until owner defines scope and assigns a batch number.


## 10. Batch execution log (for agent handoff)
Source-of-truth note:
- For current status, prefer Section 2 and this execution log.
- Keep only the active window here: current batch entries plus the latest 4 non-current operational logs.
- Older dated entries live in `docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`.

### How to read dated entries
- Each heading in the form `YYYY-MM-DD - Batch X ...` is a historical completion/addendum log.
- Active-window policy: this section keeps current-batch logs (inside the CURRENT-BATCH markers) and only 4 non-current historical logs. Between batches the current-batch block may be empty.
- Archive location: `docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` (reverse-chronological order, newest first).
- Open/archive search commands:
  - `Get-Content docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`
  - `rg -n "^### 20" docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`
  - `rg -n "<keyword>" docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`
- If current context is insufficient, agents must follow archive links and read relevant dated entries before changing code/docs.
- New entries must use ISO dates (`YYYY-MM-DD`) and include scope, deviations, validation, and forward guidance.
- Current-batch boundaries are explicit and machine-managed:
  - `<!-- DOCSYNC:CURRENT-BATCH-START -->`
  - `<!-- DOCSYNC:CURRENT-BATCH-END -->`
- Do not manually move entries across these markers; run `python scripts/doc_state_sync.py --fix`.

<!-- DOCSYNC:CURRENT-BATCH-START -->

### 2026-02-21 - refactor(static): theme CSS/JS consolidation + results UX (Batch 11 WP-1)

- Scope: `static/css/global.css` (new), `static/js/theme.js` (new),
  `templates/base.html`, `templates/results.html`,
  `static/css/index.css`, `static/css/results.css`, `static/css/loading.css`,
  `static/css/error.css`, `static/css/unmatched.css`,
  `static/js/index.js`, `static/js/results.js`, `static/js/loading.js`,
  `static/js/error.js`, `static/js/unmatched.js`.
- Problem: Four verified findings from a Gemini 3.1 Pro Priority 2 audit:
  CSS finding -- `:root` vars, `.dark-mode` overrides, `#darkModeToggle` block,
  `#darkSwitch` block, SVG color rules, and media queries duplicated verbatim
  across all five per-page CSS files (~250 lines, 5×). JS finding -- dark-mode
  toggle logic (`localStorage` read, class toggle, `addEventListener`) duplicated
  in all five JS files; `updateSvgColors` in four files redundant because
  `global.css` `.dark-mode svg .cls-1` already handles SVG color via CSS.
  UX finding (owner addition) -- html2canvas JPEG export on mobile captured only
  the visible viewport of the horizontally-overflowed table, not the full table.
  UX finding (owner addition) -- no "Back to top" button on results page.
- Plan vs implementation: implemented as planned. No scope additions.
  `#darkModeToggle { position: fixed; }` preserved in `global.css`; verified
  toggle stays pinned at bottom center on all pages. `error.js` and `unmatched.js`
  reduced to comment stubs (all their logic was dark-mode only). `loading.js`
  module-level dark-mode block removed; progress-polling logic unchanged.
- Deviations: none.
- Validation:
  - `pytest -q`: **121 passed** (no Python changes; suite unchanged).
  - `pre-commit run --all-files`: all 8 hooks passed.
  - html2canvas fix: added `width: el.scrollWidth`, `height: el.scrollHeight`,
    `windowWidth: el.scrollWidth`, `scrollX: 0`, `scrollY: 0` to capture full
    table width on mobile.
  - Back-to-top: fixed bottom-right button, visible after 300px scroll,
    smooth-scrolls to top on click. JS in `results.js`; HTML in `results.html`.
- Forward guidance: WP-2 pending -- decompose `process_albums` in
  `orchestrator.py` (extract closure helpers + `_fetch_spotify_misses` +
  `_build_results`; add 4 adversarial tests). No production behavior change from
  WP-1; pure CSS/JS reorganization.

### 2026-02-21 - style/fix(static): CSS/JS DRY violations, toggle bug, UX polish (Batch 11 WP-3)

- Scope: `static/css/global.css`, `static/css/results.css`,
  `static/css/index.css`, `static/css/loading.css`,
  `static/js/results.js`, `static/js/theme.js`,
  `templates/base.html`.
- Problem: Five findings from a post-WP-1 owner code review:
  (1) DRY/SoC -- `--info-bg` was defined in `results.css` `:root`/
  `.dark-mode` blocks while `loading.css` hard-coded the identical rgba
  values inline; neither could share the variable because loading.css does
  not import results.css. Promoted `--info-bg` to `global.css` and replaced
  loading.css hard-codes with `var(--info-bg)`.
  (2) DRY -- Three `.dark-mode .modal-content/.modal-header/.modal-footer/
  .btn-close` rules were byte-for-byte duplicated in both `index.css` and
  `results.css`. Moved once to `global.css` and removed from both files.
  (3) Bug -- Dark-mode toggle markup used Bootstrap `form-check form-switch`/
  `form-check-input`/`form-check-label` classes while the widget was 100%
  custom-styled with `appearance: none` + `::before`. Bootstrap's
  `.form-switch .form-check-input` injected a conflicting SVG `background-
  image` knob and a `margin-left: -2.5em`, fighting the custom layout.
  Stripped Bootstrap classes from HTML markup in `base.html`; updated CSS
  selectors from `.form-check-input`/`.form-check-label` to bare
  `input`/`label`; added `cursor: pointer` to label (previously inherited
  from Bootstrap). Also fixed dark-mode toggle track color: was purple
  (`var(--bars-color)`); added `.dark-mode #darkSwitch:checked` override
  using `var(--bg-color)` so it blends with the dark background instead.
  (4) UX -- `.step-text` and `.step-details` on the loading page lacked
  `text-align: center`; text was left-aligned inside the centered card.
  (5) Redundant JS -- Mobile release-date shortening block in `results.js`
  (`window.innerWidth < 768` regex-replace on `.release-badge` text)
  duplicated logic already handled server-side by Bootstrap `d-none d-md-
  inline`/`d-md-none` spans in `results.html`. Removed.
  Additionally: `var` -> `const` for `darkSwitch` and `backToTop` in
  `theme.js` (neither is reassigned).
- Plan vs implementation: all findings addressed in-session. No scope
  additions beyond owner-requested dark-mode track color fix.
- Deviations: none.
- Validation:
  - `pytest -q`: **121 passed** (no Python changes; suite unchanged).
  - `pre-commit run --all-files`: all hooks passed.
  - No Python behavior change. Pure CSS/JS/template hygiene.
- Forward guidance: WP-2 (decompose `process_albums` in `orchestrator.py`)
  remains the next pending Batch 11 work package. Claim 3 from the review
  (toggle desync -- hardcoded `#1e1e1e` and `#333` spread across files
  instead of semantic `--surface-color`/`--border-color` variables) is a
  valid architectural observation but is a larger refactor; the current
  values are consistent and functional. Deferred.

<!-- DOCSYNC:CURRENT-BATCH-END -->
