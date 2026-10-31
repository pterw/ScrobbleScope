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

- **CI parallel-jobs side task (owner, 2026-10-31):** PR #285, branch
  `ci/parallel-jobs`, cut from `main` at `7f85bade`. It splits the single CI
  job into `changes`, `checks` and `browser` jobs plus a `quality-gate`
  aggregator that keeps the required check's name, and skips the browser job
  when a pull request changes only documentation. The plan
  `docs/superpowers/plans/2026-10-31-ci-parallel-jobs.md` is executed and its
  Execution record holds the CI evidence (four jobs green, 5 min 32 s). The
  post-merge check (b2) remains: on the first documentation-only pull
  request, `browser` is skipped and `quality-gate` succeeds. The findings
  triage follows this PR.

- **Archive pagination side task:** Complete and merged as PR #284, merge
  commit `7f85bade`. The four archives past the page target are indexes with
  numbered pages. F-B23-35 (page manifests are never checked) is ranked in
  the findings triage.

- **Deezer busy-service side task (owner, 2026-10-31):** branch
  `fix/deezer-service-busy`. A DeepSeek patch, approved by a typed review;
  it closes F-B23-37 (a Deezer HTTP 200 body of error code 700 is retried
  and raised as `deezer_unavailable`, not read as "no match"). The findings
  triage comes next.

- **UI audit Minors side task:** Complete and merged as PR #283, merge commit
  `fe2de3f7`. The spec is
  `docs/superpowers/specs/2026-10-31-ui-audit-minors-design.md` and the
  execution record is in `docs/superpowers/plans/2026-10-31-ui-audit-minors.md`.

- **Spotify artist ID side task:** Complete and merged as PR #282, merge
  commit `708fb48b`; it closed F-B23-33 (a malformed artist ID no longer
  reaches the Spotify artists URL).

- **Weekly chart geometry side task:** Complete and merged as PR #281, merge
  commit `18a4242d`. The execution record is
  `docs/superpowers/plans/2026-10-30-weekly-chart-geometry.md`.

- **Listening view side task:** Complete and merged as PR #280, merge commit
  `c1ca5f18`. Independent F-SWE-8 work stays gated. The execution record is
  `docs/superpowers/plans/2026-10-28-streamgraph-context-halo.md`.

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
  remain untagged by the owner's 2026-09-23 ruling in the definition. It runs
  after the tranche, before WP-1 (owner ruling 2026-10-22).
- **Before WP-1: a tranche of side-task PRs** (owner rulings 2026-10-20).
  Each is its own branch off `main` and its own PR, with atomic commits:
  the include-unmatched control, a documentation refresh (README,
  architecture diagrams), backend hygiene, UI consistency, and four of the
  architecture seams the 2026-09-30 review proposed -- the album request
  module, one album-metadata encoding, the statistics module, and
  normalized Last.fm scrobbles with one album aggregate. The include-unmatched
  control (PR #1) and backend hygiene (PR #2) are done. The album request module
  is done (PR #3, branch refactor/album-request-module, plan
  `docs/superpowers/plans/2026-10-20-album-request-module.md`); normalized
  Last.fm scrobbles with one album aggregate is done (PR #4, branch
  refactor/lastfm-scrobbles, plan
  `docs/superpowers/plans/2026-10-20-lastfm-scrobbles.md`); one album-metadata
  encoding is done (PR #5, branch refactor/metadata-encoding, plan
  `docs/superpowers/plans/2026-10-20-metadata-encoding.md`); the statistics
  module is done (PR #6, branch refactor/statistics-module, plan
  `docs/superpowers/plans/2026-10-20-statistics-module.md`). Job persistence
  waits: a database-backed job store would keep the database awake, which
  the hosting cost ceiling does not allow. The design is
  `docs/superpowers/specs/2026-10-20-pre-batch23-tranche-design.md` and the
  order is `docs/superpowers/plans/2026-10-20-pre-batch23-tranche.md`.
  PR #7, UI consistency, finished round 1 (plan
  `docs/superpowers/plans/2026-10-20-ui-consistency-round-1.md`); further rounds
  wait for the owner's screenshots, each with its own plan. A side-task PR of
  cheap fixes from the 2026-10-21 architecture review and the logging audit
  is done (branch `fix/pre-batch23-side-tasks`, plan
  `docs/superpowers/plans/2026-10-22-pre-batch23-side-tasks.md`), and so is a
  CI change that keeps Playwright's Ubuntu packages in the Actions cache
  (branch `ci/playwright-apt-cache`, plan
  `docs/superpowers/plans/2026-10-22-ci-playwright-apt-cache.md`). UI
  consistency round 2 is done (PR #268, branch `feat/ui-consistency-round-2`,
  plan `docs/superpowers/plans/2026-10-23-ui-consistency-round-2.md`). Its
  backlog runs now on `feat/ui-round-2-backlog`: the owner settles each item
  in a live session and the accepted changes landed as they were made (PR
  #269). All fourteen tasks of the plan
  `docs/superpowers/plans/2026-10-25-ui-round-2-backlog.md` have landed on
  the same branch (the documentation, the gates that hold the accepted
  changes, the F-B23-46 ranking rule and the stale-copy sweep), followed by a
  test consolidation under the owner's lean-suite ruling. PR #269 merged
  into `main` (merge commit `997f7584`) and is deployed. The album-matching,
  cache re-verification and MusicBrainz fixes are on `fix/album-matching`
  (PR #270, plan `docs/superpowers/plans/2026-10-25-album-matching.md`),
  based on `main`: every plan task has landed there and the six findings it
  files are closed. PR #270 merged into `main` (merge commit `4a2d2406`) and is deployed. The documentation refresh merges last.
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
non-current operational logs. Older dated entries live on the numbered pages
listed by `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`; search the
`docs/logarchive/` directory, not that index.

**How to read dated entries:**
- Each heading `YYYY-MM-DD - ...` is a completion/addendum log.
- Untagged side-task history: the pages under `docs/logarchive/`.
- Tagged batch history: per-batch logs under `docs/history/logs/`.
- Batch scope/acceptance criteria: definitions under `docs/history/definitions/`.
- Current-batch boundaries are machine-managed (do not move entries manually):
  - `<!-- DOCSYNC:CURRENT-BATCH-START -->`
  - `<!-- DOCSYNC:CURRENT-BATCH-END -->

<!-- DOCSYNC:CURRENT-BATCH-START -->

<!-- DOCSYNC:CURRENT-BATCH-END -->

### 2026-10-31 - Record the CI parallel jobs execution

Side task, no batch tag, branch `ci/parallel-jobs`: the plan
`docs/superpowers/plans/2026-10-31-ci-parallel-jobs.md` gets an Execution
record and its done boxes ticked. Run 41223708194 at head `3ca1f53b` ran all
four jobs green: `changes` 7 s, `checks` 74 s, `browser` 313 s, `quality-gate`
4 s, 5 min 32 s in all against 6 min 47 s for PR #284's single job. Reviews:
the plan once and then fixed in 2 rounds, the second without its own
re-review, the split after 1 (`fbb6f449`), the docs sweep
approved. Acceptance (b1) passed locally; (b2) stays open for the first
documentation-only pull request after merge, because this PR changes the
workflow and so runs `browser` on every head. Also: `development-cycle.md`,
`documentation-tooling.md` and `README.md` point at `scripts/dev/ci_jobs.py`
as the owner of the docs-only path list instead of paraphrasing it, and the
README wrap around the docs-only note is fixed.

Deviations: none. Docs only; no code or test changed.

Validation: `pytest -q` -- **3157 passed**.

### 2026-10-31 - Describe the parallel CI jobs

Side task, no batch tag, branch `ci/parallel-jobs`: the documentation sweep
for the four-job workflow. `DEVELOPMENT.md` (the `tests/frontend/` paragraph),
`docs/architecture/development-cycle.md` (the CI paragraph) and
`docs/architecture/documentation-tooling.md` (the CI summary near the end)
now name `changes`, `checks`, `browser` and the `quality-gate` aggregator, say
which pull requests skip `browser`, and point at `scripts/dev/ci_jobs.py`. The
run time reads about 1.5 minutes for a docs-only pull request and about 5
minutes for any other. `README.md` notes the skip and the
`tests/scripts/dev/test_frontend_gate.py` docstring says "CI browser job". No
Mermaid node changed: "GitHub Actions Quality Gate" and its edges stay true.
Point-in-time records are untouched.

Validation: `pytest -q` -- **3157 passed**.

### 2026-10-31 - Tighten the CI split tests after review

Side task, no batch tag, branch `ci/parallel-jobs`: fixes from the review of
the split commit, tests only. In `tests/scripts/dev/test_ci_jobs.py` the
192-row `aggregate` table and its `_allowed` oracle are replaced by one test
that loops the full product against a hand-written set of accepted tuples
and lists every mismatch; `test_aggregate_rejects_an_empty_or_unknown_docs_only_value`
and the duplicate `()` row are removed; the misnamed
`test_main_aggregate_accepts_an_empty_docs_only_value` is replaced by
`test_main_aggregate_rejects_an_empty_docs_only_given_as_a_separate_argument`;
`test_main_aggregate_exits_nonzero_when_a_required_flag_is_missing` is added;
the docs-only table gains `.superpowers-old/x.py`, `build.cmd`,
`src/my file.py` and `my notes.md`. In `tests/test_ci_workflows.py` the
parametrized app-jobs test is split into
`test_app_jobs_set_flask_env` and
`test_the_workflow_passes_no_secret_outside_a_step_env`, so the whole-file
secret scan runs once. No script or workflow change.

Validation: `pytest -q` -- **3157 passed**.

### 2026-10-31 - Run the quality gate as parallel jobs

Side task, no batch tag, branch `ci/parallel-jobs`. The one CI job took about
7 minutes, 4.5 of them in the browser gate. `.github/workflows/test.yml` now
has four jobs: `changes` (is the pull request docs-only), `checks` (install,
preflight, pre-commit, pytest with coverage, pip-audit), `browser` (Playwright
and the frontend gate) and `quality-gate`, the one required context, which
aggregates the other three. `scripts/dev/ci_jobs.py` holds the two decisions
(`docs-only` path classification and `aggregate`), with truth-table tests in
`tests/scripts/dev/test_ci_jobs.py`; `tests/test_ci_workflows.py` reads
per-job blocks. A docs-only pull request skips `browser`; any other skip, or
a failed or cancelled job, turns `quality-gate` red.

Deviations: an empty or unrecognised `--docs-only` value fails the
aggregator even when all three jobs succeeded (fail closed). `browser` has
no Tailwind asset cache: nothing it runs reads `scripts/bin`.

Validation: `pytest -q` -- **3347 passed**.
