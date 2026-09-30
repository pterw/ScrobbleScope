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

### Batch index (completed batches archived; the active batch, if any, is listed last)

| Batch | Title | Definition | Log |
|-------|-------|------------|-----|
| 0 | Baseline freeze + approval parity suite | `docs/history/definitions/BATCH0_DEFINITION.md` | -- |
| 1 | Proper upstream failure state + retry UX | `docs/history/definitions/BATCH1_DEFINITION.md` | -- |
| 2 | Personalized minimum listening year | `docs/history/definitions/BATCH2_DEFINITION.md` | -- |
| 3 | Remove nested thread pattern | `docs/history/definitions/BATCH3_DEFINITION.md` | `docs/history/logs/BATCH3_LOG.md` |
| 4 | Expand test coverage significantly | `docs/history/definitions/BATCH4_DEFINITION.md` | `docs/history/logs/BATCH4_LOG.md` |
| 5 | Docstring + comment normalization | `docs/history/definitions/BATCH5_DEFINITION.md` | `docs/history/logs/BATCH5_LOG.md` |
| 6 | Frontend refinement/tweaks | `docs/history/definitions/BATCH6_DEFINITION.md` | `docs/history/logs/BATCH6_LOG.md` |
| 7 | Persistent metadata layer (Postgres) | `docs/history/definitions/BATCH7_DEFINITION.md` | `docs/history/logs/BATCH7_LOG.md` |
| 8 | Modular refactor (app factory + blueprints) | `docs/history/definitions/BATCH8_DEFINITION.md` | `docs/history/logs/BATCH8_LOG.md` |
| 9 | Audit remediation (WP-1 through WP-8) | `docs/history/definitions/BATCH9_DEFINITION.md` | `docs/history/logs/BATCH9_LOG.md` |
| 10 | Gemini audit remediation (WP-1 through WP-9) | `docs/history/definitions/BATCH10_DEFINITION_2026-02-21.md` | `docs/history/logs/BATCH10_LOG.md` |
| 11 | Gemini Priority 2 audit remediation (SoC, DRY, architecture) | `docs/history/definitions/BATCH11_DEFINITION.md` | `docs/history/logs/BATCH11_LOG.md` |
| 12 | Polish and observability (CSS, formatting, SoC, progress) | `docs/history/definitions/BATCH12_DEFINITION.md` | `docs/history/logs/BATCH12_LOG.md` |
| 13 | Internal decomposition and coverage hardening | `docs/history/definitions/BATCH13_DEFINITION.md` | `docs/history/logs/BATCH13_LOG.md` |
| 14 | Doc hygiene (archive restructure, docsync package, per-batch routing) | `docs/history/definitions/BATCH14_DEFINITION.md` | `docs/history/logs/BATCH14_LOG.md` |
| 15 | Alignment, hardening, and handoff | `docs/history/definitions/BATCH15_DEFINITION.md` | `docs/history/logs/BATCH15_LOG.md` |
| 16 | Script hygiene, local dev hardening, and integration testing | `docs/history/definitions/BATCH16_DEFINITION.md` | `docs/history/logs/BATCH16_LOG.md` |
| 17 | Agent bootstrap hardening, CI/CD improvements, and dep pinning | `docs/history/definitions/BATCH17_DEFINITION.md` | `docs/history/logs/BATCH17_LOG.md` |
| 18 | Scrobble heatmap -- iteration 1 | `docs/history/definitions/BATCH18_DEFINITION.md` | `docs/history/logs/BATCH18_LOG.md` |
| 19 | Heatmap polish -- frame, KPIs, mobile layout | `docs/history/definitions/BATCH19_DEFINITION.md` | `docs/history/logs/BATCH19_LOG.md` |
| 20 | File-hygiene + docs methodology refresh | `docs/history/definitions/BATCH20_DEFINITION.md` | `docs/history/logs/BATCH20_LOG.md` |
| 21 | UI overhaul -- Tailwind + daisyUI migration | `docs/history/definitions/BATCH21_DEFINITION.md` | `docs/history/logs/BATCH21_LOG.md` |
| 22 | Enrichment providers and original release years | `docs/history/definitions/BATCH22_DEFINITION.md` | `docs/history/logs/BATCH22_LOG.md` |
| 23 | Spotify Extended Streaming History import | `BATCH23_DEFINITION.md` | active -- Section 4 |

A batch's close-out entry sits in its per-batch log only when the heading
carried a `(Batch N WP-X)` tag (as Batch 18's did). Close-outs tagged
`(Batch N close-out)` are not parser-recognized and were routed to the
monolith archive instead -- Batches 19 and 20 are the current examples.
See FINDINGS F-DOCSYNC-3.

### Open decisions (owner confirmation needed)

1. Persistent store choice: Postgres only or Postgres + Redis.
2. Retry UX policy: immediate retry button only, or retry + cooldown messaging.
3. Error copy style and user-facing tone for upstream failures.

---

## 3. Active batch + next action

- **Batch 23 is active.** Definition: `BATCH23_DEFINITION.md`.
  Branch: `feat/batch23-wp0-hygiene`. The branch was cut from `test`; run the
  worktree guard with `--base-ref origin/test`.
- **Next action:** WP-0 is next.
  Part A and Part B are complete. Part C continues through the three
  follow-on plans in the order recorded under "After this plan" in
  `docs/superpowers/plans/2026-09-23-batch23-wp0-reconcile-and-clear.md`:
  control-plane, frontend, then test infrastructure and dependencies.
  The control-plane plan is written and reviewed:
  `docs/superpowers/plans/2026-09-25-batch23-wp0-control-plane.md`. Its eight
  tasks are all complete (Task 7 landed `8cf5fd4`..`c39da3c`). The frontend
  and test-infrastructure/dependencies plans are now written and reviewed:
  `docs/superpowers/plans/2026-09-26-batch23-wp0-frontend.md` and
  `docs/superpowers/plans/2026-09-26-batch23-wp0-test-infra-deps.md`. The
  frontend plan and the test-infrastructure/dependencies plan are both fully
  executed (every task in each has landed). The three plans' carried items
  are closed out, and their final code review of the whole branch ran on
  2026-09-27; its one fix wave has landed and passed a scoped re-review
  (see Section 4). Next action: the WP-0 close-out below. The
  definition owns WP-0 scope and acceptance; `docs/agents/FINDINGS.md`
  owns open finding status.
- **WP-0 close-out:** Re-review `e7e076b` independently, review the whole
  branch, verify Part C's listed findings member by member, and run the
  final gates in the definition. Then write one tagged `(Batch 23 WP-0)`
  Section 4 entry, carrying an explicit `**Status:** WP-0 complete` line
  (DOC007 requires it before the package reads done). Earlier WP-0 commits
  remain untagged by the owner's 2026-09-23 ruling in the definition.
- **Batch 23 close-out obligation:** WP-7 includes the deferred Batch 21
  frontend and accessibility audit; the batch cannot close without it.
- **Architecture seams before the Spotify import (owner ruling 2026-09-29):**
  "If any seams from architechture deepening are worth doing now before
  further feeat implements, thats the time." The seams and the work package
  each one gates are in
  `docs/history/reports/architecture-review-20260930-0040.html`: a job
  module with a storage seam, typed provider failures and job persistence
  (before WP-3), an album request module (before WP-4), normalized Last.fm
  scrobbles with one typed album aggregate (before WP-2), one album-metadata
  encoding (before WP-3), a statistics module (before WP-6), and provider
  failure logs that carry no listener data. WP-1 does not start until they
  are scheduled.

---

## 4. Execution log (for agent handoff)

Keep only the active window here: current batch entries plus the latest 4
non-current operational logs. Older dated entries live in
`docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`.

**How to read dated entries:**
- Each heading `YYYY-MM-DD - ...` is a completion/addendum log.
- Untagged side-task history: `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`.
- Tagged batch history: per-batch logs under `docs/history/logs/`.
- Batch scope/acceptance criteria: definitions under `docs/history/definitions/`.
- Current-batch boundaries are machine-managed (do not move entries manually):
  - `<!-- DOCSYNC:CURRENT-BATCH-START -->`
  - `<!-- DOCSYNC:CURRENT-BATCH-END -->

<!-- DOCSYNC:CURRENT-BATCH-START -->

<!-- DOCSYNC:CURRENT-BATCH-END -->

### 2026-09-29 - Repo Assist removed; CI job holds no provider secrets

Side task, no batch tag: removing the Repo Assist workflow and CI's provider secrets, a fix from the third review of PR #245, on the review-fix branch that fast-forwards into PR #245's branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

Owner ruling (2026-09-29): Repo Assist is not configured properly and is dropped; CI is robust without it. `repo-assist.md`, `repo-assist.lock.yml`, the README sentence and the Repo Assist assertions in `tests/test_ci_workflows.py` are gone, and the S6-2 hardening (a docsync.toml guard for its PRs) is not built. S6-1 stays: `test.yml` no longer passes LASTFM_API_KEY, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET or SECRET_KEY at job level. No step reads a real key: `conftest.py` and `frontend_gate.py` supply placeholders, and a step that ever needs one takes it in its own `env:`. Proved by running the suite and the frontend gate with the four variables unset. The two comments that said CI passes the keys from repository secrets are corrected.

Edited tests: every test in `tests/test_ci_workflows.py` asserted on the Repo Assist workflow, so the module is rewritten around `test.yml`: `test_test_job_env_passes_no_secret` (job-level env carries no secrets reference) and `test_env_reader_flags_a_secret_and_a_missing_block`. Filed F-B23-32, F-B23-33 and F-B23-34 (P3, S6-3, S6-4, S6-5). Owner action: delete the Repo Assist repository secrets (for example CODEX_API_KEY, COPILOT_GITHUB_TOKEN) in GitHub settings if nothing else uses them.

Validation: `pytest -q` -- **2238 passed**.

### 2026-09-29 - Provider-failure docstring made true; async-thread traceback kept at DEBUG

Side task, no batch tag: the `RedactingFormatter` docstring corrected and `run_async_in_thread`'s traceback moved to DEBUG, a fix from the third review of PR #245, on the review-fix branch that fast-forwards into PR #245's branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

The land review found the docstring still said `run_async_in_thread` writes the api_key in its message; it now names its DEBUG traceback and `get_cached_response`'s debug line as the two remaining sites. Per the owner's Q5 ruling (2026-09-29, "At ERROR, log the exception type only; the full traceback goes to DEBUG"), `run_async_in_thread` keeps its class-only ERROR line and adds a DEBUG line with `exc_info=True`. The caplog test `test_run_async_in_thread_error_line_carries_the_class_never_the_message` now asserts the ERROR record has no exception info or message and a DEBUG record carries the traceback; proven red with the DEBUG line removed.

Validation: `pytest -q` -- **2242 passed**.

### 2026-09-29 - Provider failure lines name the operation, never album, artist or track

Side task, no batch tag: provider failure log lines carry an operation key and an exception class, not names, a fix from the third review of PR #245, on the review-fix branch that fast-forwards into PR #245's branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

Architecture pass 2, B-2: `retry_with_semaphore` was handed a free `error_label` built from album and artist, and logged it and the exception message at ERROR, so Spotify, Deezer and MusicBrainz failures wrote the listener's names (and aiohttp's request URL) into the logs. The helper now owns what a failure line may say: callers pass an operation key (`spotify.search`, `deezer.album_tracks`, `musicbrainz.lookup`, `lastfm.page <n>`) and each line reads `Error in <key>: <ExceptionClass>`, the message dropped. The Spotify 429 warning, both artist-spotlight warnings (`spotify.py`, `routes/api.py`), the registration-year warning in `routes/album_flow.py` and the `_results.py` skip debug line follow the same rule. `api_logging.py`'s docstring names the helper as the enforcement point.

Same class, found on landing: `lastfm.py` logged `body[:200]` on an unexpected status and on invalid JSON, and a recenttracks body carries track, artist and album names; both lines now give status, byte length and content type only. `run_async_in_thread` logged `str(e)` with a traceback at ERROR; it now logs the class only, at ERROR without a traceback.

One caplog test per provider, per helper, per Last.fm line, for `run_async_in_thread`, the `_results` line and the two route lines, each proven red with the old line restored. Edited existing tests, all of which asserted leaked content: the Last.fm page-failure label (`test_lastfm_service.py`), the Last.fm invalid-JSON body quote (same file), the Spotify spotlight network-error message (`test_spotify_service.py`), and the `run_async_in_thread` redaction test (`test_api_logging.py`, which no longer sees a message to redact and now asserts the class line and the absent key).

Known, not fixed: `spotify.py` logs the provider response body on a batch failure (neither a name nor an exception message); the `logging.exception` sites that format only a Last.fm username still write tracebacks that carry `str(exc)` (owner question pending: extend the rule to tracebacks?).

Validation: `pytest -q` -- **2242 passed**.

### 2026-09-29 - Spotify attribution holds in exports and forced colours; each link names its own provider

Side task, no batch tag: keeping the Spotify icon in the saved image and in forced colours, and naming each provider on its own link, a fix from the third review of PR #245, on the review-fix branch that fast-forwards into PR #245's branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

S2-4 and S2-19: the "Save image" JPEG carried the Spotify icon at about 12px in Firefox (html2canvas paints a raster `<img>` in the clone at half size there; the raster itself was right). `results.js` now awaits `icon.decode()` on each shown icon, draws a raster at three times the box, and in `onclone` swaps the `<img>` for a `<canvas>` at the on-page box size; a failed decode aborts the export with an error toast, so there is no silent success without attribution. S2-11: `results.css` picks the icon file from `prefers-color-scheme` under `forced-colors: active`, not from the saved theme. S2-26: both icon `<img>` tags carry `width="236" height="225"` (the file's viewBox), so the line does not shift when the SVG arrives. S2-15: `results.js` builds one album-link tooltip per provider from the row's `data-provider` (Spotify keeps `album-link-tooltip`, others get `album-link-tooltip-<provider>`), and each link's `aria-describedby` names its own provider. S2-5: `unmatched.html` gives a coverless row with a non-Spotify provider the plain placeholder, with no artist-portrait slot, and the page attribution no longer counts such a row as Spotify content.

Two new frontend-gate checks, `export keeps spotify icon size` (Chromium and Firefox; measures the icon in the exported image at >= 21px) and `spotify icon follows system under forced colors` (Chromium). The gate is now 45 checks (measured after Task 10's check landed). Live probes: with the old `results.js` the export check is red in Firefox (`JPEG export shows the Spotify icon at 12.0x12.3px, below the 21px minimum`) and green in Chromium; with the old `results.css` the forced-colours check is red for both the system-light and system-dark cases; restored, both are green. One new `results_behavior_tests.py` test (`test_tooltip_names_the_provider_each_link_opens`) fails on the old JS, and 3 new tests in `tests/test_routes.py` fail on the old templates. No existing test edited.

Known limits: the Firefox canary now also runs the results-page export check (about 5s more). Forced colours is checked in Chromium only. Legacy unmatched rows with an empty provider still show a Spotify portrait, because they have no provider to exclude; only rows naming another provider get the placeholder.

Validation: `pytest -q` -- **2233 passed**.
