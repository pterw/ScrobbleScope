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

### 2026-08-14 - F-WORKTREE-5 closed: count branch candidates before filtering (side-task)

- Scope: the last open guard defect, reported independently by Codex in PR
  #170 round 5 and by Copilot in round 6, and left open across both.
- Defect: `parse_batch_branch` filtered candidates through
  `is_display_safe_ref` and only then counted them. Because that allowlist is
  deliberately narrower than Git's ref rule, a rejected candidate can still
  name a real branch, so a Section 3 declaring two branches -- one of them
  non-ASCII -- had one side discarded and reported the survivor as expected.
  The predicate decides whether a value may be rendered, not whether it exists.
- TDD: the regression test failed first with `DID NOT RAISE`, using
  `wip/b\xe4tch-21` as the second value -- Git accepts non-ASCII letters in a
  ref name, and the escape keeps the test source ASCII. Then counted distinct
  candidates before any filtering and moved the display-safety filter after
  the conflict check, where it only decides what may be rendered.
- Anti-vacuity: both orderings are load-bearing. Deleting the
  count-before-filter fails the new test; deleting the display-safety filter
  fails three cases of
  `test_a_branch_value_cannot_repaint_the_diagnostic_line`.
- Also corrected the stale justifying comment in the source, and added a
  correction note to `docs/superpowers/plans/2026-08-05-worktree-safety-guard.md`,
  whose Step 3 still prescribed the defective ordering in prose. Leaving that
  in place would have let the plan teach the defect back into the code.
- Plan vs implementation: as planned.
- Deviations: none.
- Validation: `pytest -q` -- **590 passed** with the 3 existing
  aiohttp/Python 3.13 warnings. `pre-commit run --all-files` -- all 10 hooks
  pass. `check_worktree_alignment.py` -- exit 0.
- Forward guidance: F-WORKTREE-5's two PR #170 threads can now be answered and
  resolved. F-WORKTREE-3 and F-WORKTREE-4 remain open by decision.

### 2026-08-14 - architecture diagrams corrected and given one owner (side-task)

- Scope: newly integrated Mermaid material that contradicted the code, plus
  the three older diagram copies that disagreed with it and each other.
- The central defect, in both sequence diagrams: `create_job` was drawn with
  no preceding `acquire_job_slot`. The real order is the reverse
  (`routes.py:460` then `:478`, and `:570` then `:582`) and is a fail-fast:
  the slot is taken first and the request rejected outright if none is free.
  An agent reconciling code to the diagram would allocate a `JOBS` entry and
  then reject, leaking an orphan job on every throttled call until TTL expiry.
  README already stated the correct order, so the repository contradicted
  itself. The same inversion was present in the synthesis document.
- Nine further defects, each verified against source: `worker.py` drawn as
  importing `orchestrator` and `heatmap` when both import *it* (the dispatch
  is real but runtime-only, through a callable `routes.py` injects); a
  `cache.py -> utils.py` edge that does not exist in any form; the cache
  hit/miss partition attributed to `cache.py` when it happens in
  `orchestrator.py:561-578`, and cannot happen in `cache.py`, which never sees
  the full candidate set; expiry cleanup drawn as cache-internal when the
  orchestrator calls it; `start_job_thread` given the wrong signature; the
  heatmap response typed as a rendered page rather than JSON 202; and missing
  `routes -> orchestrator`, `routes -> heatmap`, `routes -> utils` and
  `repositories -> errors` edges.
- Ownership after this change: `README.md` keeps one high-level diagram and
  now declares its arrow semantics, which was the root defect the wrong
  diagrams shared -- a dependency edge and a control-flow edge were drawn
  identically and read as the same claim. `docs/ARCHITECTURE.md` owns every
  detailed diagram. SESSION_CONTEXT Section 5 keeps a corrected compact
  summary and points there for detail. The synthesis Section 5 diagrams were
  removed with a note recording why, and its Section 6 tooling diagram
  migrated with one edge corrected: `doc_state_sync.py` imports only
  `docsync.cli`, so the fan-out had been attributed one level too high.
- Renamed the incoming doc from a dated filename to `docs/ARCHITECTURE.md`.
  It is a living reference, and `docs/` root holds durable documents while
  `docs/history/` holds dated ones; a date in the name would have become
  false at the first correction.
- Every diagram was validated before being written, per
  `.github/instructions/mermaid.instructions.md` Rule 1. This caught a real
  parse failure: a `;` inside a sequence-diagram message terminates the
  statement. The incoming document had escaped it as `&#59;&#59;`, which
  parsed but rendered as visible garbage and dropped a `%`. Removed the
  semicolon rather than escaping it.
- Now tracked, with the disposition rule recorded in the previous entry:
  `docs/ARCHITECTURE.md`, the two `.github` instruction files (converted to
  ASCII, with a ScrobbleScope scoping section reconciling their `.mmd` rule
  against this repository's tracked-Markdown layout), the corrected synthesis,
  and the PR #170 remediation plan under a superseded header naming the four
  ways it must not be executed.
- Plan vs implementation: the plan called for deleting `sequenceDiagram.mmd`
  as a duplicate. Kept instead and moved to `diagrams/`, with `*.mmd`
  gitignored -- deleting the only `.mmd` would contradict Rule 5 of the
  instruction file being tracked in the same change.
- Deviations: none.
- Validation: `pytest -q` -- **590 passed**. All six diagrams return
  `valid: true` from the Mermaid validator. `doc_state_sync.py --check` --
  passed with the expected root-BATCH warning.
- Forward guidance: `docs/history/` still needs an index and its dead
  references repointed, and `AGENT_NOTES.md` still needs the tooling map.

### 2026-08-14 - dependency-graph and pytest-config claims corrected (side-task)

- Scope: four documentation claims that contradict the code, plus the
  ordering statements left stale by the PR #170 merge.
- Dependency graph, SESSION_CONTEXT Section 4. `heatmap.py <- config` was
  false -- `heatmap.py` imports lastfm, repositories, utils and worker, and
  reaches config only transitively through those. The same wrong chain was
  repeated in the `heatmap.py` module docstring, so fixing one source alone
  would have left the other. `app.py <- routes` omitted the `config` edge at
  `app.py:143` (`ensure_api_keys`), which exists only under the `__main__`
  guard; recorded with that scope rather than as an unconditional import.
  Added `dev/dev_start.py`, documented in Section 3 but absent from the
  graph. Every other edge was re-derived from the imports and is correct.
- Pytest config, SESSION_CONTEXT Section 7. The claimed
  `asyncio_mode = "strict"` is not configured anywhere: `pyproject.toml`
  contains only `pythonpath = "."`, and no `pytest.ini`, `setup.cfg` or
  `tox.ini` exists. `git log -S` shows the key was never in the file, so
  this was wrong when written rather than drift. The same sentence appears
  in `docs/history/SESSION_CONTEXT_REFERENCE.md`, which is left as written:
  that file is a labelled 2026-02-23 snapshot of SESSION_CONTEXT.md, and a
  snapshot that silently corrects its original stops being a snapshot.
- Ordering. PR #170 merged, so PLAYBOOK Section 3, BATCH21_DEFINITION,
  SESSION_CONTEXT Section 1 and FINDINGS all still said it must land first.
  All four now name the merge and give the F-SWE-1 audit as the next action.
  The batch-open baseline in BATCH21_DEFINITION gained its date so the 390
  is not misread as current.
- README cross-reference. "See `AGENTS.md` for the full dependency graph"
  pointed at a file that has no graph; repointed to SESSION_CONTEXT
  Section 4, which is where it lives.
- AGENTS.md gained a note that WT004 after a merge is expected and routine,
  with the tree-equality precondition that separates it from a real
  divergence. Without it the guard's stop-and-escalate remediation reads as
  alarming for what is now a per-merge occurrence.
- Plan vs implementation: as planned.
- Deviations: none.
- Validation: `pytest -q` -- **589 passed** with the 3 existing
  aiohttp/Python 3.13 warnings. `check_worktree_alignment.py` -- exit 0.
  `doc_state_sync.py --check` -- passed with the expected root-BATCH warning.
- Forward guidance: the architecture diagrams still contradict the code they
  describe, most seriously by drawing `create_job` with no preceding
  `acquire_job_slot`. That is the next side-task, followed by F-WORKTREE-5.

### 2026-08-14 - post-merge realignment and untracked-artifact disposition (side-task)

- Scope: restore a green bootstrap after PR #170 merged, and give every
  untracked path an explicit disposition. Two gates were failing at once.
- Gate 1, the worktree guard. `main` requires linear history and its ruleset
  permits only squash and rebase merges, so the merge rebased the branch and
  left `wip/batch-21` 9/9 diverged from `origin/main` with byte-identical
  trees (`dedd776` both) -- `ERROR WT004`, exit 1. Verified the two tree
  hashes matched and `git diff HEAD origin/main` was empty, then reset the
  branch onto `origin/main` and force-pushed with lease under the owner
  approval the guard's remediation requires. No file changed; only the
  commit objects the branch points at. This state will recur after every
  merge, since it follows from the ruleset rather than from any mistake.
- Gate 2, the integrity gate. The `setup-matt-pocock-skills` skill had
  appended an `## Agent skills` section to `AGENTS.md` pointing at a new
  untracked `docs/agents/`, which produced three `DOC001` errors and would
  have failed `pre-commit` and CI. Reverted. The skill followed its own
  file-selection rule (no `CLAUDE.md` exists, so `AGENTS.md` was its
  fallback); the mismatch is that it treats `AGENTS.md` as an appendable
  conventions file while this repository treats it as a governed ruleset.
- Disposition: untracked files went from 73 to 5, all five of which are
  slated for tracking in later side-tasks. Ignored with recorded reasons:
  `.agents/` and `skills-lock.json` (vendored from two upstream skill
  repositories, already drifting -- the lock names 22 skills, the tree holds
  20); `docs/agents/` (unedited vendor templates describing a layout this
  repository does not use); and `*.mmd` (Mermaid authoring scratch, kept
  separate so no diagram has a second copy free to drift).
- Note for future audits: `git status` collapses directories, so the set
  read as 8 paths and was actually 73 files. Use `-uall`. Separately,
  `git check-ignore -v <path>/` reports a spurious match against a blank
  `.gitignore` line for any path given a trailing slash -- a nonexistent
  directory and a fully tracked one both "match" it.
- Plan vs implementation: as planned. `sequenceDiagram.mmd` was slated for
  deletion as a duplicate; kept instead and moved to
  `diagrams/top-albums-sequence.mmd`, because
  `.github/instructions/mermaid.instructions.md` requires diagrams be
  written to `.mmd` files. Ignoring the pattern satisfies both that rule and
  single-source-of-truth.
- Deviations: none.
- Validation: `pytest -q` -- **589 passed** with the 3 existing
  aiohttp/Python 3.13 warnings. `check_worktree_alignment.py` -- exit 0
  (WT010 only). `doc_state_sync.py --check` -- passed with the expected
  root-BATCH warning.
- Forward guidance: the four documents still describe PR #170 as pending;
  correcting them is the next side-task. Then the architecture diagrams,
  which contradict the code they describe, and F-WORKTREE-5, which two
  reviewers filed independently and which still has two open threads.
