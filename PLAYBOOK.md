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
| 21 | UI overhaul -- Tailwind + daisyUI migration | `BATCH21_DEFINITION.md` | active -- Section 4 |

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

- **Batch 18 is complete.** All 5 WPs done. Definition archived:
  `docs/history/definitions/BATCH18_DEFINITION.md`.
- **Batch 19 is complete.** All 5 WPs done plus owner-review follow-up.
  Definition archived: `docs/history/definitions/BATCH19_DEFINITION.md`.
  PR #152 (Batches 18 + 19) merged to `main`.
- **Batch 20 is complete.** All 9 WPs done (WP-0 through WP-5 via PR #159
  on `file-hygeine`; audit gap-fix follow-up, WP-6, WP-7, and WP-8 on
  `wip/batch-20`, submitted as PR #162). Definition archived:
  `docs/history/definitions/BATCH20_DEFINITION.md`.
- **Batch 21 is active.** Definition: `BATCH21_DEFINITION.md` (repo
  root). Scope: UI overhaul -- Bootstrap 5.1.3 -> Tailwind v4 (standalone
  CLI) + daisyUI v5, warm heatmap-derived themes propagated app-wide,
  page-by-page strangler migration. Expanded from the owner's Claude
  Design audit (UI Audit v3); four owner decisions locked in the
  definition. Branch: `wip/batch-21` (worktree off `main`).
- **Next action:** execute the full F-SWE-1 principles audit, then proceed to
  Batch 21 WP-1. PR #169 merged to `main` on 2026-08-08 and the Quality Gate
  is green for `5bc6294`, so the canonical repository-integrity gate and
  read-only worktree guard are shipped and
  F-DOCSYNC-5/F-WORKTREE-1/F-WORKTREE-2 are resolved. Three guard files
  exceed their directory peer caps after review remediation -- accepted as a
  deviation and tracked as F-WORKTREE-4 in FINDINGS.md, not silently. Review
  remediation ran to round 6: rounds 2 through 5 landed before the merge, and
  round 6 was reviewed after the final push, so its four findings reached
  `main` unaddressed. **PR #170 remediated them and merged 2026-08-12**
  (`5b060a2`), so the guard and docsync sources the audit reads are settled.
  Three of its review threads remain open, two of them independent reports of
  F-WORKTREE-5.
- Batch 21 WP status: WP-0 done. WP-1 through WP-8 not yet started.
- **Perf note:** heatmap fetch speed is rate-limit bound; measurement and
  rationale live in FINDINGS.md F-B18-11 (single source).
- **Last.timer note (checked 2026-05-19):** the referenced project uses
  aggregate `user.gettopartists`/`user.gettoptracks` calls with page fan-out,
  not exact per-scrobble recent-track timestamps. Useful for future perf
  research, but not a drop-in heatmap speedup. See FINDINGS.md F-B19-3.
- Future feature candidates (confirmed by owner roadmap):
  - **Top songs** (future): rank most-played tracks for a year (Last.fm + possibly
    Spotify enrichment, separate background task + loading/results flow).

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
  - `<!-- DOCSYNC:CURRENT-BATCH-END -->`
- After any edit here, run `python scripts/doc_state_sync.py --fix`.
- Archive search: `rg -n "^### 20" docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`

<!-- DOCSYNC:CURRENT-BATCH-START -->

### 2026-07-24 - Batch 21 opened: UI overhaul definition committed (Batch 21 WP-0)

- Scope: opened Batch 21 (UI overhaul -- Tailwind + daisyUI migration)
  on `wip/batch-21`, a worktree off `main` at the PR #162 merge.
- Plan vs implementation:
  - `BATCH21_DEFINITION.md` expanded from the stub into the full 9-WP
    definition derived from the owner's Claude Design audit (UI Audit
    v3): toolchain (WP-1), base shell + error-page pilot (WP-2), index
    (WP-3), unified loading (WP-4), results leaderboard (WP-5), heatmap
    seam removal (WP-6), unmatched + reason_code backend fix (WP-7),
    sweep + close-out (WP-8). Strangler migration, page by page.
  - Four owner decisions locked in the definition: rotating loading
    messages cut; welcome modal deleted; `limit_results` kept inside the
    thresholds disclosure; fonts self-hosted under `static/fonts/`.
  - Agent verification recorded in the definition: the unmatched
    reason-string grouping bug is live; `--bs-primary` never overridden;
    `bootstrap.Popover` in `index.js` is a third Bootstrap JS consumer
    the audit missed; `--bars-color` must be aliased in both themes.
  - PLAYBOOK Section 2 row title updated; Section 3 marks Batch 21
    active with next action WP-1; SESSION_CONTEXT rows updated.
  - Toolchain mechanics locked after an owner-relayed Opus 5 review:
    CLI binary in gitignored `scripts/bin/` with `.gitkeep`; auto-fetch
    at a pinned version via a new `scripts/dev/tailwind_build.py` (not
    `dev_start.py` -- app startup never needs the toolchain); WP-8 adds
    a rebuild-and-diff pre-commit hook for compiled-CSS drift; WP-8
    owner E2E explicitly opens the downloaded save-as-image file.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0 (expected
  root warning for the now-active `BATCH21_DEFINITION.md`).
- Forward guidance: WP-1 sets up the Tailwind v4 standalone CLI +
  daisyUI v5 bundled plugin, defines both themes from the audit token
  sheet, and commits the compiled CSS. No template changes until WP-2.

<!-- DOCSYNC:CURRENT-BATCH-END -->

### 2026-08-15 - PR #171 post-push review round remediated (side-task)

- Scope: two new visible Codex threads and all five suppressed Copilot
  comments on commit `11c9885`. The seven reports described six distinct
  defects because both reviewers found the omitted heatmap admission check.
  An independent review found one adjacent README polling claim during the
  required sibling sweep.
- Verification and loop check:
  - `routes.py` confirms that heatmap requests reject a missing username,
    unavailable validation service, and unknown user before cleanup or slot
    acquisition. `loading.js` and `heatmap.js` confirm that both browsers poll
    while their background tasks run. `docsync.logic` confirms tagged entries
    rotate to per-batch logs while untagged entries rotate to the side archive.
  - Git blame assigns all three affected diagram owners to the preceding
    review-fix commit. The omitted validation and rotation branch plus both
    serialized pollers are therefore self-inflicted extraction defects, not
    newly reached backlog. The older date headers became stale when this PR
    later changed the live dashboard and findings state without refreshing
    them. README's claim that `heatmap.js` polls `/heatmap_data` predated this
    review round; the script and Batch 18 records show that it polls
    `/progress` and fetches `/heatmap_data` only after completion.
- Plan vs implementation:
  - The tooling graph now distinguishes tagged rotation into
    `docs/history/logs/` from untagged rotation into `docs/logarchive/`.
  - The heatmap sequence now shows required-input and Last.fm user-existence
    validation, including terminal 400, 404, and 503 responses before job
    admission.
  - Both request sequences now use Mermaid parallel blocks for background
    processing and progress polling. SESSION_CONTEXT and FINDINGS carry the
    current 2026-08-15 update date.
  - README now distinguishes heatmap progress polling from the completed-data
    fetch.
- Deviations: no production behavior changed and no tests were added. Existing
  tests already cover heatmap validation responses and task lifecycle behavior.
- Validation: all three edited diagrams passed Mermaid validation and opened
  in preview; each tracked block exactly matches its ignored `.mmd` source.
  `pytest -q` -- **590 passed**, 3 known warnings. `pre-commit run --all-files`
  -- all 10 hooks pass.
- Closure boundary: the pushed remediation commit and its passing Quality Gate
  define done for PR #171. Do not start another patch-review-patch cycle from
  later automated comments; a future agent may scrutinize them during a
  separately scoped deep sweep, but they are not automatic blockers for this
  documentation PR. Do not merge PR #171 without separate owner instruction.
- Forward guidance:
  - Execute the already-chartered Python-only F-SWE-1 audit, then start Batch
    21 WP-1. Keep architecture streamlining found by that audit separate from
    the frontend strangler unless it directly blocks a named WP acceptance
    criterion.
  - At WP-1, decide how CI obtains and caches the pinned, digest-verified
    standalone Tailwind and daisyUI artifacts. At WP-8, make the CSS drift hook
    `always_run` with no filenames or narrow the top-level pre-commit exclude;
    otherwise it cannot see `static/`. Add focused CSS, JS, and HTML checks
    before close-out because those paths currently have no lint coverage.
  - Treat `ruff` as an optional, separately measured Python-tooling migration,
    not a frontend prerequisite. It overlaps Black, isort, autoflake, and
    flake8, would require owner-approved dependency changes, and should land
    only with explicit parity criteria after the F-SWE-1 findings are known.

### 2026-08-15 - PR #171 review findings verified and remediated (side-task)

- Scope: all eight unresolved Codex and Copilot threads on PR #171, checked
  against the current code, tests, repository rules, and sibling documentation
  before any edit. A separate two-axis review found no additional verified
  spec or standards defect in the cumulative `origin/main...HEAD` diff.
- Plan vs implementation:
  - Seven factual comments were confirmed: partial heatmap data is successful
    with a warning; cache hits still write JOBS state; both task entry points
    release their slot unconditionally; `start_job_thread` releases the slot
    before re-raising while the route deletes the new job; README's dotted-edge
    legend omitted dispatch; and `orchestrator.py` was not the import-graph top.
  - The eighth comment was also confirmed against the complete new-file rule:
    the 499-line `docs/ARCHITECTURE.md` exceeded its existing `docs/` peer cap.
    It is now a 49-line index preserving all five section anchors. Five focused
    files under `docs/architecture/` own one diagram each and are 47-101 lines.
  - README, SESSION_CONTEXT, and the Mermaid instruction now point to the
    focused owners without duplicating diagrams. Gitignored `.mmd` sources were
    used for validation and preview only.
- Deviations: no production behavior changed and no tests were added; existing
  regression tests already cover partial-data continuation, startup slot
  release, and unconditional task cleanup.
- Validation: all six published diagrams passed Mermaid validation and opened
  in preview. `pytest -q` -- **590 passed**, 3 known warnings. `pre-commit
  run --all-files` -- all 10 hooks pass. `doc_state_sync.py --check` -- exit 0
  with the expected active-root `BATCH21_DEFINITION.md` warning.
- Forward guidance: commit the review remediation, push only with owner
  authorization, then post one batched reply and resolve the eight threads.

### 2026-08-14 - F-DATA-1 filed under P2; stale skill name corrected (side-task)

- Closes the two items the previous entry left as forward guidance.
- `F-DATA-1` self-labelled `Status: open (P2)` while sitting as the last
  entry under the P1 heading. Fixed by moving the `## P2` heading above it
  rather than relocating a 65-line block -- same result, far less churn, and
  the finding's own text is untouched.
- `DEVELOPMENT.md` still named the PR triage skill `gemini-pr-triage`; it was
  renamed `pr-bot-triage`. Real drift, not a snapshot, so it is corrected
  rather than preserved.
- **Scoping correction from the owner, recorded because an agent got it
  wrong today:** `DEVELOPMENT.md` is not an agent document. It is absent from
  docsync's live-document set and from the AGENTS.md bootstrap reading list,
  and belongs with `README.md` as human-facing methodology writing. A line
  added to `AGENT_NOTES.md` earlier the same day pointed agents at it for the
  skills-are-local decision; that line now states the decision directly
  instead. Batch definitions may still direct an agent to *write* a build
  step into it -- writing to it is in scope, treating it as a source of
  operating rules is not.
- Plan vs implementation: these two were dropped from the Phase 5 scope
  reduction and then reinstated by the owner, since both sit in working
  documents rather than in the archive the reduction was about.
- Deviations: none.
- Validation: `pytest -q` -- **590 passed** with the 3 existing
  aiohttp/Python 3.13 warnings. `pre-commit run --all-files` -- all 10 hooks
  pass. `doc_state_sync.py --check` -- exit 0. `check_worktree_alignment.py`
  -- exit 0. Verified exactly one `## P2` heading remains and that `F-MAS-4`
  is still the last P1 entry.
- Forward guidance: nothing outstanding from the remediation. Next is the
  F-SWE-1 audit, then Batch 21 WP-1.

### 2026-08-14 - Batch 21 tooling mapped to its work packages (side-task)

- Scope: `AGENT_NOTES.md` gains a map from the installed skills and MCP
  servers to WP-1 through WP-8, written before WP-1 rather than discovered
  during it. Every entry was verified against the live machine and repository
  on the day rather than carried forward from the plan's older table.
- Structural fact recorded so nobody hunts for what is not there:
  `BATCH21_DEFINITION.md` has **no per-WP acceptance criteria**. It carries
  one batch-level list of 9 plus a per-WP validation gate that every WP runs
  identically, so the map keys on the WP and names the criteria each serves.
- Four separate skill sources are installed and their names collide -- `tdd`
  and `test-driven-development` are different files from different upstreams,
  as are `diagnosing-bugs` and `systematic-debugging`. The map says which
  source each comes from, because naming the wrong one loads the wrong file.
- Seven gaps recorded, all verified. Three of them converge on WP-8 and one
  of those has to be decided at WP-1: the pre-commit top-level exclude covers
  13 directories including `static/` and `templates/`, so the planned
  `tailwind-css-drift` hook could never fire as a file-scoped hook and must
  use the `always_run` pattern; CI has no Node and no Tailwind binary, so the
  headless-Linux fetch is unsolved; and no CSS, JS or HTML hook exists at all,
  leaving the files eight WPs rewrite unreachable by two mechanisms at once.
- Two plan claims were corrected against the live state. The exclude covers
  **13** directories, not the 12 the plan's Phase 6 still said -- an earlier
  phase had already found 13 and the later section was never updated. And the
  `skills-lock.json` drift (22 locked, 20 present) is bookkeeping only: both
  absent skills are supplied by the superpowers plugin, so it is not the
  capability gap it looks like.
- One claim was verified rather than assumed after a false negative:
  `workflow_dispatch` is on `origin/main` and usable. An initial check
  reported it missing, which turned out to be Git Bash rewriting the
  `rev:path` argument on Windows rather than anything about the repository.
- Plan vs implementation: as planned, with the MCP inventory re-enumerated
  live as the plan instructed rather than copied.
- Deviations: none.
- Validation: `pytest -q` -- **590 passed** with the 3 existing
  aiohttp/Python 3.13 warnings. `pre-commit run --all-files` -- all 10 hooks
  pass. `doc_state_sync.py --check` -- exit 0 (expected root warning for the
  active `BATCH21_DEFINITION.md`). `check_worktree_alignment.py` -- exit 0.
- Forward guidance: this closes the post-merge remediation. Next is the
  F-SWE-1 principles audit per `docs/SWE_AUDIT_CHARTER.md`, whose report
  belongs under `docs/history/reports/`, then Batch 21 WP-1. The three open
  PR #170 review threads and the four ruleset settings remain owner-side.
