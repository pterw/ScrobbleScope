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
  Branch: `feat/batch23-wp0-hygiene`. That branch merged into `main` as PR #245 on 2026-09-30 and `origin/test` is
  deleted, so side-task PRs branch from `main` and run the guard against its default
  base. The owner names the branch WP-1 opens.
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
- **Before WP-1: a tranche of side-task PRs** (owner rulings 2026-10-20).
  Each is its own branch off `main` and its own PR, with atomic commits:
  the include-unmatched control, a documentation refresh (README,
  architecture diagrams), backend hygiene, UI consistency, and four of the
  architecture seams the 2026-09-30 review proposed -- the album request
  module, one album-metadata encoding, the statistics module, and
  normalized Last.fm scrobbles with one album aggregate. Job persistence
  waits: a database-backed job store would keep the database awake, which
  the hosting cost ceiling does not allow. The design is
  `docs/superpowers/specs/2026-10-20-pre-batch23-tranche-design.md` and the
  order is `docs/superpowers/plans/2026-10-20-pre-batch23-tranche.md`.
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

### 2026-10-20 - Section 3 names the pre-Batch-23 tranche's spec and plan

Side task, no batch tag: point PLAYBOOK Section 3 and SESSION_CONTEXT at the tranche's spec and master plan, on `chore/pre-batch23-hygiene`, a branch off `main`.

Owner intent: an agent that reads Section 3's "Before WP-1" bullet should find the design and the PR order without searching.

What changed: PLAYBOOK Section 3's "Before WP-1" bullet gains one sentence naming `docs/superpowers/specs/2026-10-20-pre-batch23-tranche-design.md` and `docs/superpowers/plans/2026-10-20-pre-batch23-tranche.md`. SESSION_CONTEXT's Batch 23 status row names the spec path after the existing "side-task PRs runs" sentence. Both documents come from this branch and are committed on it.

Deviations: none. No test was edited.

Validation: `pytest -q` -- **2590 passed**.

### 2026-10-20 - Hygiene entries corrected after review

Side task, no batch tag: three wording and count fixes to the hygiene commits, on `chore/pre-batch23-hygiene`, a branch off `main`.

Owner intent: the per-task reviews found documentation on this unpushed branch that was loose or false, so correct it before the PR rather than leave it.

What changed: (1) `docs/agents/FINDINGS.md` header said 84 tracked test modules; the requirements-split test added a module, so the measured count is 85 (SESSION_CONTEXT's Tests row already said 85). (2) The Task 2 claim that "nine of the ten scripts in `static/js/` already" use hyphens was wrong, since only three names contain a hyphen; it now says `page_motion.js` was the only script name with an underscore, in the `page-motion.js` entry and in the hygiene plan's Task 2 "Why". (3) The Python 3.13 spellings entry now names the edited existing tests and mentions the `except` tuple reorder in `scrobblescope/spotify.py`.

Deviations: none. No test was edited.

Validation: `pytest -q` -- **2543 passed**.

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
