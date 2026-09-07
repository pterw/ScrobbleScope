# Handoff: Batch 21 remediation -- Task 4 implemented, awaiting review (2026-09-05)

Written at session close. The next session's focus: run the pending Task 4
task review, then Tasks 5 and 6, then the plan's Final acceptance.

## Current state

Worktree: `%USERPROFILE%\.config\superpowers\worktrees\ScrobbleScope\batch-21\impeccable-init`

Two branches matter:

- `wip/batch-21` (checked out here) -- local tip carries Task 4's commit
  `e0219b2` plus the handoff commit on top of it; `origin/wip/batch-21` is at
  `ecc2877` (Task 3). The local-ahead state is intentional: Task 4 is published
  under the stacked branch below, keeping PR #225 scoped to Task 3.
- `wip/batch-21-task-4` (origin) -- `e0219b2` plus the handoff commit, opened
  as a stacked PR with base `wip/batch-21`.

Pull requests:

- PR #225 (DRAFT, base `main`, head `wip/batch-21` @ `ecc2877`): Task 3 --
  4:3 split, 28rem base cap, header clamps, both divider tokens raised, hero
  fills its column. Awaiting owner visual review. Do not merge; integration
  needs an explicit owner instruction (the WT004 squash-merge ritual then
  applies, and the stacked branch rebases after).
- The stacked Task 4 PR (base `wip/batch-21`): Task 4 implementation, itself
  awaiting its SDD task review -- see the work order below.

Validation at `e0219b2`: `pytest -q` 902 passed; frontend gate 23 checks in
64 runs across Chromium and Firefox, green; pre-commit all hooks; docsync
check exit 0 (the root BATCH21_DEFINITION.md warning is expected). Task 3's
verified state (894 tests) is recorded in its own Section 4 entries.

The worktree guard exits 0 (WT000); WT010 is expected for the preserved local
artifacts (`.agent/`, `.impeccable/`, `PRODUCT.md`, gitignored `graphify-out/`).

## Where the working context lives

- Canonical plan:
  `docs/superpowers/plans/2026-09-01-batch21-index-scaling-and-review-remediation.md`
  (Tasks 1-3 complete; Task 4 implemented-unreviewed; Tasks 5-6 pending).
- SDD workspace (git-ignored, local to this machine):
  `.superpowers/sdd/2026-09-01-batch21-index-scaling-and-review-remediation/`
  - `progress.md` -- the ledger; read it first after bootstrap.
  - `task-3-brief.md` ... `task-6-brief.md`, `task-4-5-6-prep-notes.md`
    (controller-verified baselines for the remaining tasks).
  - `task-3-report.md` (implementation + both fix-round reports),
    `task-4-report.md` (implementation pass, with RED/GREEN evidence).
  - Review packages from Task 3's chain; Task 4's package is generated at
    review time (range `ecc2877..e0219b2`).
  - `task-3-*.png` + `task-3-evidence.json` -- post-fix rendered evidence,
    both engines x 1080p/1440p x both themes; `capture_task3_evidence.py`
    re-captures it.

## Work order for the next session

1. Bootstrap per `AGENTS.md` "Session Bootstrap", then read the SDD ledger.
2. Task 4 task review (the pending gate): generate the review package for
   `ecc2877..e0219b2`, dispatch ONE reviewer (spec + quality) with the brief,
   the report, and the package. Then the SDD fix loop if findings return:
   resume the implementer for rounds 1-3, separate review-fix commits, no
   amend/squash, scoped re-review each round.
3. Task 4 clean: implement Task 5 (unmatched no-data surface), then Task 6
   (accessibility pass), each test-first in its own commit per the plan.
4. The plan's Final acceptance: branch-wide sweep greps, every gate, owner
   visual acceptance, then integration authorization.

## Session rulings that govern the next session

- All subagents -- implementers and reviewers -- run on `gemini-3.8-flash`
  (owner, 2026-09-05). The controller watches: verify every cited file:line
  and recomputed figure against the diff/source before acting on a finding.
- Task 3's seven parked minors were triaged "defer" by the final review; the
  list lives in the SDD ledger (WP-8-era polish candidates, none blocking).
- Time-box discipline: tight dispatches, straight to validation after green.
- `GH_TOKEN` in `.env` is invalid (401) -- owner to rotate per
  `AGENT_NOTES.md`. `gh` works without it via the keyring account.
- Commit-SHA caution: a commit cannot contain its own SHA. Task 4's docs
  first referenced the pre-amend SHA (`21b5198`, dangling); the handoff
  commit corrected every reference to `e0219b2`. Write SHA references after
  committing, or reference by subject.

## Open findings posture

- F-B21-24 stays reopened until Tasks 4-6 land (its Task 3 portion is done).
- F-B21-33's accuracy prerequisites: resolved by Task 4's commit.
- F-B21-40 (index well divider contrast): resolved in `774e899`.
- Issue #222 keeps its remaining complexity targets open.

## Suggested skills

- `using-superpowers`, `subagent-driven-development`, `executing-plans`
- `scrobblescope-bootstrap`
- `verification-before-completion`, `tdd`
- `graphify` (the MCP index sits at `3ccb176`; verify against current source
  before relying on it for Task 4's edited files)
