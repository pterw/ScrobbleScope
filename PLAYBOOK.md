# ScrobbleScope Execution Playbook

Date: 2026-02-22
Purpose: Single source of truth for work sequencing and execution history.
Rules for agent behaviour live in `AGENTS.md`; current-state snapshot in
`.claude/SESSION_CONTEXT.md`.

## 1. Why this document exists

- Provide a single source of truth for work sequencing.
- Enable continuation by another agent with minimal context loss.
- Prevent risky refactor-first changes before parity tests exist.

**Implementation principles:**
1. Approval tests before structural refactor.
2. No behavior-breaking refactors without parity checks.
3. Add observability before optimization where possible.
4. Keep changes batch-scoped and reversible.
5. Keep security-safe rendering (`tojson`, escaping) as baseline.

---

## 2. Batch order (strict sequence)

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

### Open decisions (owner confirmation needed)

1. Persistent store choice: Postgres only or Postgres + Redis.
2. Retry UX policy: immediate retry button only, or retry + cooldown messaging.
3. Error copy style and user-facing tone for upstream failures.

---

## 3. Active batch + next action

- **Batch 10 is complete.** Definition: `docs/history/BATCH10_DEFINITION_2026-02-21.md`.
- **Batch 11 is complete.** Definition was inline (Gemini 3.1 Pro Priority 2
  audit remediation -- SoC, DRY, and architectural findings).
  - WP-1 (Low): CSS/JS theme consolidation. Done. (Created `global.css` +
    `theme.js`; stripped ~250 lines of duplicate CSS from 5 per-page files;
    removed dark-mode toggle JS from 5 JS files; fixed html2canvas mobile
    export; added back-to-top button on results page. 121 tests passing.)
  - WP-2 (Medium): Decompose `process_albums` in `orchestrator.py`. Done.
    (Extracted 2 closures to module-level pure functions, extracted
    `_fetch_spotify_misses` and `_build_results` helpers, added 8
    adversarial test cases. 210 tests passing.)
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
- **Batch 12 is active.** Definition: `BATCH12_PROPOSAL.md`.
  Polish and observability: CSS variable enforcement, responsive data
  formatting + export parity, backend SoC extraction, granular progress
  pipeline. 4 WPs. Next action: WP-1.
  - WP-1 (P0): Semantic CSS Variable Enforcement. Done.
  - WP-2 (P1): Responsive Data Formatting & Export Parity. Not started.
  - WP-3 (P1): Backend SoC Extraction. Not started.
  - WP-4 (P2): Granular Backend Progress Pipeline. Not started.
- Future batch feature candidates (confirmed by owner roadmap, batch number TBD):
  - **Top songs**: rank most-played tracks for a year (Last.fm + possibly
    Spotify enrichment, separate background task + loading/results flow).
  - **Listening heatmap**: scrobble density calendar for last 365 days
    (Last.fm-only, lighter background task).
- Do not start feature work (top songs, heatmap) until owner defines scope
  and assigns a batch number.

---

## 4. Execution log (for agent handoff)

Keep only the active window here: current batch entries plus the latest 4
non-current operational logs. Older dated entries live in
`docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`.

**How to read dated entries:**
- Each heading `YYYY-MM-DD - ...` is a completion/addendum log.
- Current-batch boundaries are machine-managed (do not move entries manually):
  - `<!-- DOCSYNC:CURRENT-BATCH-START -->`
  - `<!-- DOCSYNC:CURRENT-BATCH-END -->`
- After any edit here, run `python scripts/doc_state_sync.py --fix`.
- Archive search: `rg -n "^### 20" docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`

<!-- DOCSYNC:CURRENT-BATCH-START -->

### 2026-02-23 - style(css): semantic CSS variable enforcement (Batch 12 WP-1)

- Scope: `static/css/global.css`, `static/css/index.css`, `static/css/results.css`,
  `static/css/loading.css`, `static/css/error.css`, `static/css/unmatched.css`,
  `static/js/results.js`.
- Problem: Structural UI elements (backgrounds, borders, form inputs, error
  accent) duplicated hardcoded hex values across 6 CSS files and 1 JS file,
  violating DRY and breaking the centralized theme architecture.
- Fix: Added 5 semantic CSS variables (`--surface-color`, `--surface-elevated`,
  `--border-color`, `--input-bg`, `--error-accent`) to `:root`/`.dark-mode` in
  `global.css`. Replaced all structural hardcoded hex across 6 CSS files.
  Promoted orphaned `--error-accent` from `error.css` to `global.css`. Fixed
  `results.js` `html2canvas` `backgroundColor` to use `getComputedStyle` for
  `--bg-color` instead of hardcoded `#121212`/`#ffffff` ternary (light-mode
  JPEG export was `#ffffff` vs actual `--bg-color` of `#f8f9fa`).
- Validation: `pytest -q`: **210 passed**. `pre-commit`: all hooks passed.

<!-- DOCSYNC:CURRENT-BATCH-END -->

### 2026-02-22 - fix(app): guard sys.stderr.reconfigure with isinstance check

- Scope: `app.py`.
- Problem: Pyright/Pylance reported "Cannot access attribute reconfigure for
  class TextIO" because `sys.stderr` is typed as `TextIO`, which lacks
  `reconfigure`. The method exists at runtime on `io.TextIOWrapper`.
- Fix: Added `import io` and wrapped the call in
  `if isinstance(sys.stderr, io.TextIOWrapper):` -- a type-narrowing guard
  that satisfies both the type checker and runtime safety.
- Validation: `pytest -q`: **210 passed**. `pre-commit`: all hooks passed.

### 2026-02-22 - refactor(routes,lastfm): SoC/DRY cleanup from third-party audit

- Scope: `scrobblescope/routes.py`, `scrobblescope/lastfm.py`,
  `scrobblescope/orchestrator.py`, `tests/services/test_lastfm_logic.py`.
- Problem: Three findings from a third-party structural audit:
  (1) SoC -- `get_filter_description` was a public helper placed between HTTP
  handlers; lacked `_` prefix used by the other private helpers.
  (2) DRY -- `/results_complete` and `/unmatched_view` duplicated ~10 lines
  of identical `job_id`/`job_context` guard logic.
  (3) SoC -- `fetch_top_albums_async` in `lastfm.py` imported `set_job_stat`
  from `repositories.py` and made 5 direct job-state mutations. An API client
  module should return pure data, not mutate application state. `spotify.py`
  already follows this pattern correctly.
- Fix:
  (1) Renamed to `_get_filter_description` and hoisted above HTTP handlers,
  below `_group_unmatched_by_reason`.
  (2) Extracted `_get_validated_job_context(missing_id_message, expired_error,
  expired_message, expired_details)` returning `(job_id, job_context, None)`
  or `(None, None, error_response)`.
  (3) Removed `job_id` param and `set_job_stat` import from
  `fetch_top_albums_async`. Stats now returned in `fetch_metadata["stats"]`
  dict. `orchestrator._fetch_and_process` extracts and records them.
  Partial-data warning also moved to `fetch_metadata` return path.
- Deviations: Audit claimed ~15-20 lines of duplication; actual overlap was
  ~10 lines. Error titles intentionally differ between routes, so
  `expired_error` was parameterized rather than hardcoded.
- Validation: `pytest -q`: **210 passed**. `pre-commit`: all 8 hooks passed.

### 2026-02-22 - fix(types): resolve 10 Pylance type errors in production code

- Scope: `scrobblescope/lastfm.py`, `scrobblescope/spotify.py`,
  `scrobblescope/utils.py`.
- Problem: Pylance reported 10 type errors across 3 production files:
  (1) `lastfm.py` (7): `metadata` dict inferred as `dict[str, str | int]`
  caused arithmetic and nested-dict assignment failures; `albums` defaultdict
  inferred heterogeneous union on all value accesses.
  (2) `spotify.py` (2): `SPOTIFY_CLIENT_ID/SECRET` typed `str | None` from
  `os.getenv()` but `aiohttp.BasicAuth` requires `str`.
  (3) `utils.py` (1): `loop` assigned inside `try:` block, referenced in
  `finally:` -- possibly unbound if `new_event_loop()` raises.
- Fix: Annotated `metadata: dict[str, Any]` and
  `albums: defaultdict[str, dict[str, Any]]` in lastfm.py; added assert
  guards for Spotify credentials in spotify.py; initialized `loop = None`
  with `if loop is not None:` guard in utils.py.
- Test file type errors (25 across 3 files) assessed as low-impact
  mock-related noise -- deferred.
- Validation: `pytest -q`: **210 passed**. `pre-commit`: all 8 hooks passed.
