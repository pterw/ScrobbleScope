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
  (see Section 4). The WP-0 close-out below is what remains of WP-0. The
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
- **What PR #245 ships (owner ruling 2026-09-29):** the WP-0 foundation and
  every fix from the three reviews, including the job module with its storage
  seam, typed provider failures and provider failure logs that carry no
  listener data. Moved to the follow-up PR: job persistence, the Last.fm
  scrobble seams, the album request module, one album-metadata encoding, the
  statistics module and the tooling package.
- **Architecture seams before the Spotify import (owner ruling 2026-09-29):**
  "If any seams from architechture deepening are worth doing now before
  further feeat implements, thats the time." The seams and the work package
  each one gates are in
  `docs/history/reports/architecture-review-20260930-0040.html`: a job
  module with a storage seam and typed provider failures, job persistence
  (gates WP-3), an album request module (gates WP-4), normalized Last.fm
  scrobbles with one typed album aggregate (gates WP-2), one album-metadata
  encoding (gates WP-3), a statistics module (gates WP-6), and provider
  failure logs that carry no listener data. Which of these #245 ships is
  in the "What PR #245 ships" bullet above; the rest wait for the follow-up
  PR.

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

### 2026-10-20 - Ruff judges the code as Python 3.13

Side task, no batch tag: ruff's `target-version` set to `py313`, on `chore/pre-batch23-hygiene`, a branch off `main`.

Owner intent: the Dockerfile and CI run Python 3.13, so ruff should judge the code against it (tranche design, PR #2).

What changed: `pyproject.toml` `[tool.ruff]` gains `target-version = "py313"`, so the UP rules see 3.13 idioms and the import sorter files `tomllib` as standard library. `ruff check --select I001 --fix` moved that import into the stdlib group in `scripts/dev/docsync_preflight.py`, `scripts/dev/frontend_gate.py`, `scripts/docsync/cli.py` and `scripts/docsync/declarations.py`. UP036 then flagged the `sys.version_info < (3, 12)` block in `docsync_preflight.py`; it is a deliberate refusal for an extracted copy of the control plane run on older Python, so it stays, marked `# noqa: UP036` with the reason in the comment above. The change is lint-only: import order and one comment, no behaviour.

Control plane: the commit stages `scripts/dev/docsync_preflight.py`, `scripts/docsync/cli.py` and `scripts/docsync/declarations.py` (with `scripts/dev/frontend_gate.py`), and the docsync preflight refuses control-plane files outside `[test_count]` by design (exit 3). It was committed through the documented escape, `SKIP=doc-state-sync-check git commit`, and `doc_state_sync.py --check` was run straight after (exit 0). `--no-verify` was not used.

Deviations: the brief's trailing `# noqa: UP036 -- reason` would have pushed the line past 88 characters and ruff-format would have split the tuple, so the reason sits in the comment above and the old `# pragma: no cover - CI pins 3.13` text moved there too, ahead of a shortened `# noqa: UP036  # pragma: no cover`. No existing test was edited.

Validation: `pytest -q` -- **2543 passed**.

### 2026-10-20 - The production image no longer installs requests

Side task, no batch tag: `requests` and its three private dependencies moved from `requirements.txt` to `requirements-dev.txt`, on `chore/pre-batch23-hygiene`, a branch off `main`.

Owner intent: the Dockerfile installs `requirements.txt` only, so the image should hold only what the app imports (owner, 2026-10-20: "Sure, if it's cheap and you think it would be wise.").

What changed: `requests` is imported only by `scripts/testing/` (`_http_client.py`, `concurrent_users_test.py`, `smoke_cache_check.py`), and among production packages `urllib3`, `charset-normalizer` and `certifi` are required by `requests` alone (`importlib.metadata.requires`). All four pins moved, unchanged, to `requirements-dev.txt`. `idna` stays: `yarl`, which `aiohttp` needs, requires it. CI's pip-audit still reads both files, so the moved pins stay audited. New `tests/test_requirements_split.py` parses every runtime file (`app.py`, `run.py`, `init_db.py`, `scrobblescope/`) and asserts each third-party import resolves to a distribution `requirements.txt` pins.

Mutation evidence: in a scratch copy, adding `import requests` to `scrobblescope/config.py` and removing the four pins failed the test with `scrobblescope\config.py imports requests`; on the real tree it passes.

Deviations: none. No existing test was edited.

Validation: `pytest -q` -- **2543 passed**.

### 2026-10-20 - Python 3.13 spellings for UTC and timeouts

Side task, no batch tag: the UP017 and UP041 alias fixes, on `chore/pre-batch23-hygiene`, a branch off `main`.

Owner intent: the Dockerfile and CI run Python 3.13, so the code should use its spellings (tranche design, PR #2).

What changed: `ruff check --target-version py313 --select UP017,UP041 --fix` rewrote 21 `timezone.utc` uses to `datetime.UTC` and one `asyncio.TimeoutError` to the builtin `TimeoutError` (the same class since 3.11), in `scrobblescope/heatmap.py`, `lastfm.py`, `orchestrator/__init__.py`, `routes/__init__.py`, `spotify.py`, `scripts/dev/graphify_refresh.py`, `tests/services/test_lastfm_logic.py` and `tests/test_heatmap.py`. No behaviour changes; the ruff target itself is the next commit.

Deviations: the `timezone` imports the rewrite left unused were removed (F401, by the ruff hook and two by hand), and ruff-format re-wrapped lines the shorter spelling freed. The two test files changed only by the alias spelling and that wrapping; no assertion was edited.

Validation: `pytest -q` -- **2542 passed**.

### 2026-10-20 - page-motion.js is named like the other scripts

Side task, no batch tag: `static/js/page_motion.js` renamed `page-motion.js`, on `chore/pre-batch23-hygiene`, a branch off `main`.

Owner intent: files served as URLs conventionally use hyphens, and nine of the ten scripts in `static/js/` already do (owner, 2026-10-20: "What is best practice here?" -> hyphens).

What changed: `git mv` of the script; `templates/base.html` names `js/page-motion.js` in its one `url_for`; `.claude/SESSION_CONTEXT.md` Section 3 lists `page-motion` in the `js/` line. Run before the template was updated, the Task 1 guard failed all 8 parametrised cases naming `/static/js/page_motion.js`; after it, all 8 pass. The frontend gate reports 45 checks passed in 71 runs across chromium and firefox, with no load fault naming `page-motion.js`. `docs/design/designsystemaudit.md` and dated plans and logs keep the old name as point-in-time records.

Deviations: none. No existing test was edited.

Validation: `pytest -q` -- **2542 passed**.
