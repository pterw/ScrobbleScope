# Pre-Batch-23 tranche -- master plan

> **For agentic workers:** this file orders the tranche and defines how each PR's own plan is produced. Execute a PR from its own plan, never from this file. REQUIRED SUB-SKILL for every PR plan: superpowers:subagent-driven-development.

**Goal:** Land the eight side-task PRs of `docs/superpowers/specs/2026-10-20-pre-batch23-tranche-design.md` before Batch 23 WP-1, in an order that never has two PRs editing the same lines at once.

**Architecture:** One branch, one worktree and one SDD workspace per PR. Plans are written and reviewed before code. Code phases run in parallel where their files are disjoint; landings, gate runs and merges are serial. The owner merges every PR.

**Tech Stack:** as each PR's plan states.

## Global Constraints

- Owner rulings and the review policy are the spec's; this plan does not restate them. Read the spec first.
- Every PR plan uses the writing-plans format: header, Global Constraints, tasks with Files, Interfaces, bite-sized steps with real code, and commands with expected output. No placeholders.
- Every PR plan is committed as the first commit of its own branch, before any code commit (owner, 2026-10-20: "All plans should stay for archival purposes"). It lives in `docs/superpowers/plans/` and is cited from PLAYBOOK Section 3 once its PR is under way.
- At most ten subagents at once (owner, 2026-10-20: "Since I am not having issues you can extend the cap to 10 subagents."); one browser gate at a time on the owner's machine.
- Every push is followed by a background CI watch for that head; the next landing, push or merge waits for its verdict.
- Each PR's SDD workspace holds `constraints.md` with `Gates`, `CI` and `Shared files` sections and a `progress.md` ledger whose `## RESUME HERE` block is rewritten after every dispatch, landing, verdict or ruling.

## The PRs and their plans

| # | Branch | Plan file (committed on that branch) | Plan written from | Branches from |
|---|--------|--------------------------------------|-------------------|---------------|
| 1 | `feat/include-unmatched` | (its own SDD workspace; PR #256) | -- | done |
| 2 | `chore/pre-batch23-hygiene` | `2026-10-20-pre-batch23-hygiene.md` (this branch) | this session | `main` at a7bf909 |
| 3 | `refactor/album-request-module` | `2026-10-2x-album-request-module.md` | Task 26 brief, review card B-1 | `main` after #1 and #2 merge |
| 4 | `refactor/lastfm-scrobbles` | `2026-10-2x-lastfm-scrobbles.md` | Task 23 design (23a-d), card B-3 | `main` after #1 and #2; 23b-d rebuilt on #3 |
| 5 | `refactor/metadata-encoding` | `2026-10-2x-metadata-encoding.md` | Task 27 brief, card B-5 | `main` after #4 |
| 6 | `refactor/statistics-module` | `2026-10-2x-statistics-module.md` | Task 28 brief, card B-4 | `main` after #4 |
| 7 | `feat/ui-consistency` | `2026-10-2x-ui-consistency-round-1.md`, then one plan per round | spec "UI PR (#7)" | `main` after #1 |
| 8 | `docs/pre-batch23-refresh` | `2026-10-2x-pre-batch23-docs-refresh.md` | spec "Documentation PR (#8)", Task 21 brief | `main` after #1; rebased last |

`2026-10-2x` is the date each plan is written. The pre-merge sources are local SDD workspace files (the 2026-09-29 PR #245 fixes workspace: `task-23-design.md`, `task-26-brief.md`, `task-27-brief.md`, `task-28-brief.md`, `task-21-brief.md`) and the tracked review `docs/history/reports/architecture-review-20260930-0040.html`.

## Waves

**Wave 0 (now).** #1 waits on CI and the owner's merge. #2 executes its plan in `C:/ssw/hyg` (Tasks 1-4), pushing after Task 5's merge of `main`. In parallel, the plan-writing tasks P3, P4, P6, P7 and P8 below run against the include-unmatched head (what `main` becomes); P5 starts when P4's plan is approved, because it builds on #4's names.

**Wave 1 (after #1 and #2 merge).** #3 code (Task 26). #4's 23a (parity tests only; it touches no file #3 edits). #7 round 1 (CSS only). #8 drafting into its workspace (no tracked edits yet).

**Wave 2.** #4's 23b-d once #3 has merged (both change `orchestrator/__init__.py`). #7 further rounds as the owner sends screenshots, template edits held until #6 merges.

**Wave 3.** #5 and #6 after #4 merges. Their code phases may overlap, and they touch disjoint files: #6's approved plan does not edit `scrobblescope/orchestrator/_results.py` (verified by #5's plan review, 2026-10-20). If #6 later needs `_results.py`, #5 lands first and #6 rebuilds on it.

**Wave 4.** #8 rebases on the final `main`, re-verifies every claim and diagram against it, and merges last.

## Plan-writing tasks

Each is one Sonnet agent following the writing-plans skill, writing its plan into the PR's SDD workspace, then one brief review by `sdd-reviewer` (the plan as a new-file diff). Approved plans are committed as their branch's first commit.

### P3: album request module (#3)

- Sources: the Task 26 brief; review card B-1; current `scrobblescope/routes/album_flow.py`, `routes/heatmap_flow.py`, `routes/api.py`, `routes/__init__.py`, `orchestrator.background_task`, `heatmap.heatmap_task`, including the `include_unmatched` parameter PR #1 added.
- Must cover: a form becomes a validated album request or a typed refusal (`sort_mode`, `release_scope`, `decade`, `limit_results`, `include_unmatched`); one Last.fm pre-check answer shared by the album and heatmap routes, with a short timeout of its own (owner Q4, 2026-10-20) so a slow Last.fm cannot hold one of gunicorn's four request threads for the session's 30-second total; an outage refuses retryably and never starts a job; one admission path; the thread reads parameters from the job record. Parity tests for today's route behaviour first. The `BATCH23_DEFINITION.md` WP-4 amendment naming the module the export route reuses.

### P4: Last.fm scrobbles and one album aggregate (#4)

- Sources: the Task 23 design (four commits 23a-d) and card B-3. The design was written against Tasks 22 and 18 as briefed; both merged in PR #245. Re-verify each of its assumptions (its section 1 table) against current code and record which held.
- Must cover: 23a parity tests; 23b public names across modules; 23c scrobbles not pages; 23d one typed album selection and one publish step. Last.fm usernames leave every log line (F-B23-40: `heatmap.py`'s fetch-timing line, `lastfm.py`'s private-profile line, and `heatmap._report_heatmap_failure`), replaced by the job id where a line needs correlation. The `BATCH23_DEFINITION.md` WP-2 amendment naming the record shape the export parser emits.

### P5: one album-metadata encoding (#5)

- Sources: the Task 27 brief; card B-5; #4's plan for the names it introduces.
- Must cover: the cache takes and returns `AlbumMetadata` and owns its connection lifetime and failure policy; `_album_provider` / `_album_url` and the six-tuple branch go; the "shared cache rows hold no listening facts" contract has one write path. No new database traffic (the cost ceiling). The WP-3 amendment.

### P6: statistics module (#6)

- Sources: the Task 28 brief; card B-4.
- Must cover: a Python statistics module, UTC by construction, each figure with its population stated (including whether include-unmatched rows count, per the 2026-10-20 WP-6 amendment); facts published on the job result; `static/js/heatmap.js` and `templates/results.html` render only. Pure-function tests with tz-aware timestamps. The WP-6 amendment.

### P7: UI consistency, round 1 (#7)

- Sources: the spec's UI section; `static/css/heatmap.css` `.heatmap-kpi-value` (the figure face, weight 400); `static/css/results.css` and `templates/results.html` `.metric-value`; the frontend gate's check registry `config/frontend_gate_checks.toml` and its `_frontend_gate_*` modules; `docs/agents/ui-accessibility.md`.
- Must cover: the results play count in `--font-figure` at weight 400; a frontend-gate check that the computed font family of a results play count equals that of a heatmap KPI value at every profile; contrast unchanged (7:1 target). CSS only.

### P8: documentation refresh (#8)

- Sources: the spec's Documentation section; the Task 21 brief; `.github/instructions/mermaid.instructions.md`; the `anthropic-skills:writing-skills` skill for prose standards; the 2026-10-20 codebase notes (local) for drift found during mapping.
- Must cover: one task per README topic drafted into the workspace, one integrator task landing them; one task per diagram file, each validated with the Mermaid validator; DEVELOPMENT.md history; the drift fixes; any fact newly stated in two documents declared in `config/docsync.toml` in its own commit through the documented escape. README rules: human prose, no task or finding ids, no internal links, no machine-checked figures.

## Done when

All eight PRs are merged, PLAYBOOK Section 3 names WP-1 as the next action with nothing ahead of it, SESSION_CONTEXT Section 1 agrees, and every amended `BATCH23_DEFINITION.md` work package reads true against `main`.
