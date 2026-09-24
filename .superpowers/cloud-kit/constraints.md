# Constraints for every task dispatched from an SDD workspace (cloud kit)

Plans: `docs/superpowers/plans/2026-09-24-batch23-wp0-root-cleanup.md` and
`docs/superpowers/plans/2026-09-21-batch23-wp0-foundation.md`; `docs/agents/PLAYBOOK.md`
Section 3 says which task is next. This is the Linux, cloud-session form of
the local workspace's `constraints.md`, first cut on 2026-09-24 (HEAD
`cae2aa8`) and revised after the first cloud session. To use it, copy it
into a new workspace as `constraints.md` (see
`docs/history/reports/HANDOFF_2026-09-24.md`). It is shared by every implementer
and reviewer. Re-read it at the start of every task: the Lessons section at the
bottom grows as tasks land.

## 1. The plan's own Global Constraints

The plan's "Global Constraints" section binds every task. Read it in the
plan itself. Where section 2 below disagrees, section 2 wins: it records
rulings made after the plan was written. In particular the plan's Windows
interpreter paths are replaced by R10 and section 2b below.

## 2. Controller rulings that override or sharpen the plan

**R1 -- Section 4 entries are UNTAGGED (owner ruling, 2026-09-23).**
docsync counts a work package as *completed* the moment any current-batch
entry heading carries its `WP-N` token (`scripts/docsync/parser.py`
`_collect_wp_numbers`). WP-0 spans many commits, so a tagged entry now would
make the dashboard say WP-1 is next while WP-0 is still in progress.
Therefore:

- Each task's entry is an **untagged side-task entry**, placed **directly
  after** the `<!-- DOCSYNC:CURRENT-BATCH-END -->` marker in `docs/agents/PLAYBOOK.md`
  Section 4 (top of the non-current list; `AGENTS.md` "Side-Task Handling").
  Anchor the insertion on the whole marker *line*: PLAYBOOK repeats the
  marker text inside a backticked list a few lines above, and a bare string
  match hits that copy first.
- The entry **heading must contain no `WP-<digit>` token at all.** The body
  may say "Batch 23 WP-0" -- only headings are scanned.
- Open the body with: `Side task, no batch tag: <what>, part of Batch 23
  WP-0 Part <A|B|C>. Untagged by owner ruling 2026-09-23 until the whole of
  WP-0 lands.`
- Never move entries across the DOCSYNC markers by hand.

**R2 -- PLAYBOOK Section 3 stays true at every commit.** Keep the
`**Next action:** WP-0 is next.` wording exactly (DOC007 reads it). Update
only the progress text inside that bullet, e.g. its numbered order list:
mark the step that landed. Do not write "WP-1" anywhere in Section 3, the
definition or SESSION_CONTEXT.

**R3 -- test count.** The baseline is the `Tests` row of
`.claude/SESSION_CONTEXT.md` Section 1; re-measure it at your BASE, since an
earlier task may have raised it. A task that adds tests must also update the count
sites docsync names (DOC006, DOC008): `.claude/SESSION_CONTEXT.md` Section 1
`Tests` row, its `## 6. Test structure (N tests)` heading, and the
`docs/agents/FINDINGS.md` header count. A task that adds no test changes none of them.

**R4 -- how to measure and quote the count.** Run the full suite with the
`suite` gate's command in section 2b (the one copy of it). Quote the result
in exactly this form, qualifier *after* the count:

```
Validation: `pytest -q` -- **N passed**.
```

Nothing but ` -- ` may sit between `` `pytest -q` `` and the bold count
(DOC012). Quote only one bold count per entry.

**R5 -- procedure before every commit:** write the Section 4 entry, run
`doc_state_sync.py --fix`, then run the gates in section 2b in the order
listed there. Section 2b owns the commands, the order, the frontend gate's
condition and the expected warnings; this rule does not repeat them.

**R6 -- expected pre-commit noise, not a failure.** The `worktree-alignment`
hook runs `--advisory` and prints `ERROR WT005 ... origin/main` (the branch
is cut from `test`), and `WARNING WT010` whenever the tree is dirty. It
still reports Passed. Do not act on it. If it prints `ERROR WT007`, the
clone lacks `origin/main` or `origin/test`: run `git fetch origin main test`.

**R7 -- docsync control plane.** A task that stages anything under
`scripts/docsync/`, `scripts/doc_state_sync.py`,
`scripts/dev/docsync_preflight.py` or `config/docsync.toml` is refused by the
preflight (exit 3) by design: run `doc_state_sync.py --check` at exit 0
first, then commit with `SKIP=doc-state-sync-check git commit ...`. Any
other task must commit with every hook. `--no-verify` is forbidden outright.

**R8 -- commit message:** use the plan's subject line verbatim. Add a short
body explaining why (wrap at 72). **No `Co-authored-by` trailer and no other
attribution line** -- `AGENTS.md` forbids it, whatever your harness suggests.

**R9 -- staging.** Stage paths by name only; `git add -A` and `git add .`
are forbidden. Anything under `.superpowers/` except
`.superpowers/cloud-kit/` is workspace state: never stage it (the
`.superpowers/sdd/.gitignore` keeps SDD workspaces out of git).

**R10 -- environment.** Linux, in a fresh clone. The only virtualenv is
`.venv/` at the repository root (`AGENTS.md` "Environment Setup"), so every
command uses `.venv/bin/python` and `.venv/bin/pre-commit`. There is no
`graphify-out/` graph in a clone; explore code with `git grep` and by reading
the files your brief names. Throwaway probe or scratch copies go under
`/tmp` (the plan's `/c/ssprobe` becomes `/tmp/ssprobe`).

**R11 -- ASCII only** in every file you write, including the PLAYBOOK entry
and the commit message: `--` not an em dash, straight quotes only.

**R12 -- Plan-task specifics (foundation Tasks 4-10, root-cleanup Tasks 0-8).**

- **Live probe for every task its plan's verification standard names**:
  follow the plan's "The verification standard for control-plane tasks"
  exactly -- throwaway corpus at `/tmp/ssprobe` from `git archive HEAD`,
  faithful-copy check, red, near-miss green, reset between probes, the probe
  table in the report and the Section 4 entry, and `/tmp/ssprobe` deleted
  afterwards. Unit tests are written first; the probe is the proof.
- **A new DOC code** is named in `docs/architecture/documentation-tooling.md`'s
  catalogue in the same commit. DOC021 and DOC022 are reserved by
  `docs/superpowers/plans/2026-09-12-repository-agnostic-plan-spec-guards.md`.
- **Filing or resolving a finding** follows Lesson L5 for the record form.
  `--fix` rotates a checked record into
  `docs/history/findings/FINDINGS_ARCHIVE.md`; stage it. Never write
  "resolved" or "no action" about a finding in prose unless its own record is
  checked (DOC023): say "archived", "settled" or "ruled".
- **Tests you add raise the count:** update the three R3 count sites in the
  same commit. A new test module also changes the module count on the
  SESSION_CONTEXT `Tests` row and the FINDINGS header.
- **Existing tests:** the plan's Global Constraints bind -- none is modified
  unless your brief says so and says why; name any such test in the commit
  body.
- **Section 3:** in the "Next action" order list, step 3 is "The foundation
  plan's Tasks 4-10", and the root cleanup's progress sits at that item's
  end; record your task's progress there, keeping
  `WP-0 is next.` exactly (R2).
- **Plan bookkeeping:** tick your task's step checkboxes in its plan, and
  stage the plan.
- **Ledger:** this workspace's `progress.md` is the controller's; do not
  edit it.

## 2b. Gates (machine-read by the gate-runner agent)

The single owner of the gate commands, their order, the frontend gate's
condition and the expected warnings. Implementers run these by hand (R5);
`.superpowers/cloud-kit/agents/gate-runner.md` reads this block. `--fix` writes files, so
it is a step in R5, not a gate here. Edit gates here and nowhere else.

```gates
- name: suite
  run: .venv/bin/python -m pytest -q -p no:cacheprovider
  pass: exit 0
  quote: last line

- name: pre-commit
  run: .venv/bin/pre-commit run --all-files
  pass: exit 0
  quote: last line
  expected: "ERROR WT005 ... origin/main" ; "WARNING WT010"

- name: frontend
  run: .venv/bin/python scripts/dev/frontend_gate.py
  pass: exit 0
  quote: last line
  when: a changed path starts with static/ or templates/ or scripts/dev/_frontend_gate_

- name: docsync-check
  run: .venv/bin/python scripts/doc_state_sync.py --check
  pass: exit 0
  quote: last line
  expected: "WARNING: Root BATCH file detected: BATCH23_DEFINITION.md" ; "WARNING DOC024 docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md" ; "WARNING DOC024 docs/history/findings/FINDINGS_ARCHIVE.md" ; "WARNING DOC024 docs/history/logs/BATCH21_LOG.md" ; "WARNING DOC024 docs/history/logs/BATCH22_LOG.md" (each with its Remediation line; standing since Task 4 until the real archives are paginated)
```

## 3. Lessons

Appended by the controller as tasks land. Carried over from the wrapper
plan's workspace:
- L1: each untagged entry pushes the oldest non-current Section 4 entry into
  `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` on `--fix`
  (`--keep-non-current` 4). That rotation is expected: stage the archive by
  name with the rest.
- L2: a newly written file cited in backticks in a live document fails
  DOC001 until it is staged (`git add` it before `--check`).
- L3 (after Task 2): the Task 2 entry's first heading read "WP-0 Part A Task 2: ..." and took a fix
  round. Write the heading as plain words, e.g. `### 2026-09-23 - The release-window rule moves to
  domain`. Check it with `grep -n "^### .*WP-[0-9]" docs/agents/PLAYBOOK.md` before committing: that must print
  nothing for your entry.
- L5 (after reconcile Task 1) -- OVERRIDES the plan's "Resolving a finding" template. The gate
  accepts only the bare outcome: the status line is exactly `- [x] **Status:** resolved` (or
  `no action`). Any text after it -- `resolved -- fixed by ...` -- fails DOC015, and the words
  deploy/deployed/pending/accepted anywhere on it fail DOC014 (`scripts/docsync/findings.py`,
  `_TERMINAL_SUFFIXES` and `PENDING_QUALIFIER_RE`). Follow the archive's order: the status line, then
  `**Completed:** YYYY-MM-DD`, then the reason on its own prose line. Where a brief says "the
  canonical record's reason: ...", that text goes on the prose line.
- L7 (after foundation Task 4, `d499e3a`): `doc_state_sync.py --check` on the real
  tree now prints four DOC024 warnings (the log archive, FINDINGS_ARCHIVE.md,
  BATCH21_LOG.md, BATCH22_LOG.md are unpaginated and over the 500-line page
  target) and still exits 0. They are expected (section 2b) until the owner
  rules on paginating the real archives. Never run `--paginate-archives` or
  `--cold-storage` on the real worktree unless a brief says so.
- L8 (after foundation Task 4): `tests/test_docsync_integrity.py::
  test_stated_docsync_range_matches_the_highest_code_raised` requires
  `AGENTS.md` to state the DOC range and it must equal the highest code the
  package raises (`_ranges_agree`). Adding a new DOC code therefore forces the
  `AGENTS.md` sentence to move in the same commit; a task that removes the
  stated range must change that test's contract deliberately, not delete it.
- L9 (2026-09-24): a reviewer must never edit, stage or revert anything in the
  working tree -- a gate-runner may be running on it. To prove a test is not
  vacuous, mutate a scratch copy: `git archive HEAD | tar -x -C /tmp/ssreview`,
  or for uncommitted work `git archive $(git stash create) | tar -x -C ...`
  (`git stash create` leaves the shared stash list untouched).
- L10 (2026-09-24): a gate-runner once replied in prose and wrote no logs.
  Record its verdict only after checking that LOG_DIR holds one log per gate.
- L11 (after foundation Task 5): the first Task 5 commit ticked none of its
  plan checkboxes, and neither the review nor the controller noticed; the
  owner did. Before recording a task done, check its `- [x]` boxes in the
  plan and that the plan is staged (R12 "Plan bookkeeping").
- L12 (after foundation Task 5): Task 5 took three review rounds, each finding
  a stale copy of a fact the previous round had changed (a code comment, a
  finding filed under the wrong priority heading, a table row in
  `DEVELOPMENT.md`). Ask the FIRST review to sweep the whole task range
  (`BASE..HEAD`) for every fact the task changes, in every spelling, and
  name the paths it exempts as point-in-time.
- L13 (after foundation Task 5): a gate-runner summary once listed a
  `WARNING WT023` as expected output; no log contained it. Every code a
  summary quotes must be found in LOG_DIR before its verdict is recorded.
