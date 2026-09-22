# Batch 23 WP-0 and the between-batch control-plane hygiene

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land Batch 23 WP-0 exactly as its definition scopes it, and separately close the control-plane
gaps that the 2026-09-21 reviews and a live probe of docsync found -- without widening WP-0 and without
shipping a gate change whose only evidence is a unit test.

**Architecture:** Three tracks with different authority.

- **Track 1 -- WP-0 proper** (Tasks 1-2). Behaviour-neutral, and bound by `BATCH23_DEFINITION.md` WP-0's
  acceptance: every existing test passes unmodified. It starts once Task 3b has opened the batch.
  The owner ruled on 2026-09-21 that Batch 23's branch is `feat/batch23-wp0-hygiene`.
- **Track 2 -- side tasks** (Tasks 3-10). Control-plane and documentation fixes that Batch 23 does not
  depend on, plus one that it does (Task 3). Untagged Section 4 entries. They may land before or after
  the batch opens, except Task 3, which must land first, and Task 3b, which opens the batch.
- **Track 3 -- one approved behaviour change** (Task 11). F-SWE-5's terminal outcome, after Track 1,
  as its own commit.

Everything else the reviews proposed is a recorded disposition in the DoD, not a task.

**Tech Stack:** Python 3.13 stdlib, pytest, `unittest.mock`, playwright (frontend gate), tomllib. No new
dependency.

**This file replaces an earlier draft** that put 22 tasks, two behaviour changes and a batch-definition
rewrite under WP-0. Its errors are recorded in the DoD's last section so they are not reintroduced.

## Global Constraints

Every task's requirements include this section.

- **Qualified interpreter only.** This is a linked worktree. Use
  `C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe` and its sibling `pytest.exe` /
  `pre-commit.exe`. Never bare `pip`, never a second venv.
- **No new dependency, no version change.** `requirements.txt` and `requirements-dev.txt` are out of scope.
- **Nothing may break the repository.** No task may leave `pytest -q` red, `doc_state_sync.py --check`
  non-zero, `pre-commit run --all-files` failing, or the frontend gate failing.
- **No existing test is modified, except where a task says so and says why.** Track 1: none, ever.
- **Do not touch other agents' uncommitted work.** `git status --short` lists the untracked set (the
  mutation runner and its scope file, `progress_copy.md`, audit and review documents, `plan.md`). Never
  stage, revert or delete them.
- **Commit procedure, in this order** (`AGENTS.md` "Commit Rules"): the dated `PLAYBOOK.md` Section 4
  entry; `doc_state_sync.py --fix`; `pytest -q`; `pre-commit run --all-files`;
  `doc_state_sync.py --check`. Pre-commit runs the docsync check, so it must see the synced entry.
- **A commit that changes the docsync control plane is refused by design.** Any task touching
  `scripts/docsync/`, `scripts/doc_state_sync.py`, `scripts/dev/docsync_preflight.py` or `.docsync.toml`
  exits 3 at the preflight. Run `doc_state_sync.py --check` directly at exit 0 first, then commit with
  `SKIP=doc-state-sync-check git commit ...`. Never `--no-verify`. CI's preflight step is the backstop.
- **Commit discipline:** Conventional Commits, imperative, no trailing period, subject max 72 chars.
  Stage paths by name; `git add -A` and `git add .` are forbidden. No `Co-authored-by` trailer.
- **Quote a measured count.** A Section 4 entry that claims a suite result writes it in the one form
  the authority reads (`AGENTS.md` "Which test count is authoritative"), measured by a literal
  `pytest -q` on the final tree. Re-measure; never copy a count from this file or another.
- **`AGENTS.md` stays under 500 lines.** Every edit to it is a replacement or a pointer.
- **ASCII only**: no smart quotes, no em dash -- use `--`.

## The verification standard for control-plane tasks

A failing green is worse than a red. A unit test over an invented fixture is not evidence that a gate
works: the uncommitted mutation runner had 46 green tests while reporting 100 per cent unknown. So every
task that changes a check (Tasks 3-5, 8) is accepted only on a **live probe**:

1. Build a throwaway corpus from the committed tree, at a short path (the scratchpad path exceeds
   Windows' MAX_PATH once `git add` runs):
   ```bash
   mkdir -p /c/ssprobe && cd /c/ssprobe && rm -rf corpus && mkdir corpus
   git -C "<worktree>" archive HEAD | tar -x -C corpus
   cd corpus && git init -q && git config core.longpaths true && git add -A
   git -c user.email=p@l -c user.name=p commit -qm base && git tag base
   ```
   `git init` matters: DOC001 resolves paths through `git ls-files`.
2. Confirm the copy is faithful: `--check` there prints the same summary as in the worktree.
3. **Red:** plant the defect the task targets and run the real CLI. The expected code must print and
   the exit must be nonzero (or zero, for a warning-severity code, with the warning printed).
4. **Near-miss green:** plant the closest *valid* variant and confirm silence. A check that fires on
   its near miss is a false red, and the next agent learns to ignore it.
5. Reset with `git reset -q --hard base && git clean -qfd` between probes. Anchor edits on whole marker
   lines: PLAYBOOK repeats the `DOCSYNC` marker text inside a backticked list, and a bare string replace
   hits that copy first.
6. Paste the probe table (probe, expected, exit, codes) into the task report and the Section 4 entry.
   Delete `/c/ssprobe` afterwards.

A task's own unit tests are still written, first. They are the regression guard; the probe is the proof.

### What the 2026-09-21 live probe established

The probe was run against HEAD `e6ce9d7`, and its results are the baseline this plan builds on:

- **Every implemented code fires on its own planted defect.** DOC001-DOC020 and DOC023 (both the
  `Status: closed.` label and the `resolved` prose form) each went red and raised only its own code.
  DOC002, DOC003 and DOC007 were probed in a simulated active batch.
- **Near misses stayed green:** a struck-through retired claim, a retired claim or missing path inside a
  code fence, `Status: not closed.`, a canonical resolved finding, and a valid `AGENTS.md` citation.
- **`--fix` repairs only what it derives.** It restores a tampered managed block and rotates a canonical
  resolved finding. It never writes a rotting finding's record or a hand-authored count: after a new
  `**1717 passed**` entry, `--fix` exits 1 with DOC006 and DOC008 still red.
- **Exit codes hold:** 2 for `--cold-storage` without `--as-of` and for an impossible date. The preflight
  returns 3 on a staged `scripts/docsync/` edit, 0 on an ordinary one, and passes the checker's 1 through.
- **`--paginate-archives` and DOC020 agree:** a deleted indexed page and an unindexed managed page each
  go red.
- **One defect -- the opening state is invisible.** In a batch that Section 3 declares active but that
  has no tagged Section 4 entry yet, docsync behaves as if no batch were open:
  - the status block renders `Current batch: none (between batches)`, because `_build_status_block`
    branches on `current_entries` rather than on `section_3_state.current_batch`;
  - DOC007 is silent on a false `WP-3 is next` claim, because `_computed_next_wp` returns `None` when
    there are no current entries.

  With one `(Batch 23 WP-0)` entry, both behave correctly. This is the exact state Batch 23 enters when
  its branch is named, and the dashboard is what a cold-resume agent reads first. Task 3 fixes it.

---
## Definition of Done

Every suggestion from the three architecture reviews, the two model consultations and the live probe
appears once, with its disposition. A **task** row is done when its acceptance passes. Any other row is
done when its reason is on disk in the document it names.

| # | Suggestion | Source | Disposition |
| --- | --- | --- | --- |
| 1 | Both entry points share one build-run-close-release protocol | review 2026-09-21 A c5, B card 3 | **Task 1** |
| 2 | WP-0's three original extractions | `BATCH23_DEFINITION.md` WP-0 | **Task 2** |
| 3 | Opening state renders "between batches" and silences DOC007 | live probe | **Task 3** |
| 4 | The status block omits the count between batches | `renderer._build_status_block` | **Task 3** (same branch) |
| 5 | The authored count is behind the tree | review A, measured | **Task 3 Step 6**: an authored Section 4 entry with a measured count |
| 6 | An 8,589-line archive passes `--check`; the page target has no reader | review A, executed | **Task 4** |
| 7 | Cold eligibility needs wholly dated pages; the doc says age alone | review A, executed | **Task 4** |
| 8 | Four live statements claim `DOC001-DOC023` while DOC021/DOC022 do not exist | review A c6, verified | **Task 5** |
| 9 | The `FINDINGS.md` note says a new invariant "starts at DOC023" | review A c6 | **Task 5** |
| 10 | Findings cite pre-split `orchestrator.py:NNN` lines | review A | **Task 6** |
| 11 | File the opening-state defect and the archive defects as findings | live probe, review A | **Task 6** |
| 12 | The deferred docsync close-out plan's Progress block is stale | ledger | **Task 7** |
| 13 | `frontend_gate_checks.toml`, deferred by the gate decomposition | gate plan, owner | **Task 8** |
| 14 | `AGENTS.md` lists three of the six docsync modes and three of four `docs/agents/` files | review A | **Task 9** |
| 15 | Record the docsync hook-installer decision, with correct evidence | owner | **Task 9** |
| 16 | Diagrams must match the moved protocol | owner, `AGENTS.md` item 15 | **Task 10** |
| 17 | F-SWE-5: one honest terminal outcome for both entry points | review A c5, owner | **Task 11** |
| 18 | Measure the count in CI and compare it | earlier draft | **Declined.** `pytest ... \| tee` under the default `bash -e` (no `pipefail`) masks pytest's exit code, so CI goes green on failing tests. The preflight also runs before pytest, so the file would not exist when it is read. Row 5 closes the gap by authorship instead. |
| 19 | Refuse to boot under more than one worker | review A | **Declined** (owner delegated the call, 2026-09-21). The Dockerfile pins `--workers 1`, no incident has occurred, and a guard reading `argv`/`WEB_CONCURRENCY` misses `--workers=4`, `GUNICORN_CMD_ARGS` and a config file -- a partial guard is its own wrong green. For the extraction a single-worker assertion would have to be an n-worker policy, which is a niche need. Revisit only if job state leaves the process. |
| 20 | Job record: one transition seam | review A c1 | **Future batch.** Overlaps row 23. |
| 21 | Pipeline parameters read from the record, not passed twice | review A c2 | **Future batch.** Depends on row 20. |
| 22 | Release window as a leaf module | review A c3 | **Future batch.** Cheapest structural item; a good first task for the next hygiene batch. |
| 23 | Make job retention explicit (observation renews `updated_at`) | review B card 4, F-SWE-6 | **Owner-gated.** Absolute vs sliding TTL is a product decision; F-SWE-6 owns it. |
| 24 | Make the provider adapter real (live path bypasses `enrich_albums`) | review B card 1, F-B22-7 | **Future batch, ahead of Batch 23 WP-3 if possible.** The export path reuses album processing; F-B22-7 owns the detail. |
| 25 | Job admission as one transaction (slot, state, thread) | review B card 2 | **Folded into Batch 23 WP-4** (owner ruling, 2026-09-21). The export route is the third caller, so the rule of three is met there. Task 3b writes it into the definition before execution. |
| 26 | Browser layer seam | review A c4, F-B21-18 | **F-B21-18 owns it.** Not re-scoped here. |
| 27 | Section 3 state as delimited fields; WP state from an explicit field | review A, GPT | **Future batch**, with the repository-agnostic plan-spec guards plan, which owns the parser seam. |
| 28 | Extract the control plane: policy/adapters split, second-repository pilot, results bound to the exact tree, one writer per worktree | GPT Sol Max | **Future batch of its own**, per `AGENT_NOTES.md`. Postgres coordination is deferred until a pilot shows a cross-machine need. |
| 29 | `--check` does not report an interrupted publication (journal present) | GPT Sol Max | **Future batch candidate.** Recovery exists on the next writer; a read-only diagnostic is missing. File as a finding in Task 6. |
| 30 | Control-plane AST harness, per-WP journals, JobEngine, Bootstrap cutover | review 2026-09-06 | **Superseded.** Written against the pre-split tree; Bootstrap is already gone. Not committed. |
| 31 | Two username validators; `utils.py` concerns; phase modules via facade; gate layout size | review A held-back | **Declined as recorded there**: Rule 3 buffer; F-SWE-7 owns `utils.py`; a Batch 22 WP-0 patch-target arrangement; not a decomposition goal. |

### Errors in the earlier draft, kept so they are not reintroduced

- It claimed `pre-commit install` "silently" displaces a foreign hook. It does not:
  `pre_commit/commands/hook_impl.py` `_run_legacy` runs `pre-commit.legacy` first. A docsync wrapper
  demoted there would re-enter `hook-impl` under `PRE_COMMIT_RUNNING_LEGACY` and exit with pre-commit's
  "migration mode" error. That is a loud failure, not a wrong green.
- It put two behaviour changes under a WP whose definition says none ships, then rewrote the definition
  after execution. Proposal Rules 1 and 2 forbid both.
- Its commit blocks ran pytest before `--fix`, and the Part B commits omitted the `SKIP` escape.
- It sent Task 14 to finish docsync close-out Task 4b. The ledger shows 4b committed as `3d8a42a` and
  the final review done in the PR #234 round; only the plan's Progress block is stale.

---
## Track 1 -- WP-0 proper

**Precondition:** Tasks 3 and 3b have landed, so Section 3 names `feat/batch23-wp0-hygiene` and the batch reads as active.
Section 4 entries for these tasks are tagged `(Batch 23 WP-0)` and sit inside the current-batch markers.

### Task 1: The shared loop protocol

Execute `docs/superpowers/plans/2026-09-21-worker-run-coroutine-wrapper.md` Tasks 1-4 as written: the
helper and its six tests, `background_task` adopting it, `heatmap_task` adopting it, and the reference docs
naming it. That plan's constraints and acceptance apply unchanged. It also records why
`release_checks._worker_loop` is out of scope.

This file's headings avoid the pattern `Task 1:` etc. for the wrapper's four tasks: `scripts/task-brief`
matches `^#+ Task <n>`, and the controller briefs Task 1 from the wrapper plan itself.

**Acceptance:** the wrapper plan's Acceptance, plus `git diff --stat tests/` showing only additions to
`tests/test_worker.py`.

### Task 2: WP-0's original three extractions

**Files:** `scrobblescope/orchestrator/__init__.py` (`_cap_threshold_exclusions`, `_process_filtered_albums`),
`scrobblescope/heatmap.py` (`_zero_fill_daily_counts`). No test is written: WP-0's acceptance is that
`tests/services/test_orchestrator_fetch_and_process.py` and `tests/test_heatmap.py` pass **unmodified**.

- [ ] **Step 1:** Read each range and write down its invariants. The cap sorts by
  `(-play_count, normalized_key)` and slices to `_MAX_ALBUM_CAP`. The tail of `_fetch_and_process` runs from
  `_apply_pre_slice` to `set_job_results`. The zero-fill puts every date in `[from_date, to_date]` into the
  mapping with `0`. Move each one verbatim: argument order preserved, no rename except the new function name.
- [ ] **Step 2:** Move them one at a time. After each move, run
  `pytest.exe tests/services/test_orchestrator_fetch_and_process.py tests/test_heatmap.py -q`, and confirm
  `git diff --stat tests/` is empty.
- [ ] **Step 3:** Run the commit procedure and commit:
  `git add scrobblescope/orchestrator/__init__.py scrobblescope/heatmap.py PLAYBOOK.md .claude/SESSION_CONTEXT.md`,
  `refactor(batch23-wp0): Extract the remaining shared steps`.

**Acceptance:** `BATCH23_DEFINITION.md` WP-0's own, unchanged.

---
## Track 2 -- between-batch side tasks

Untagged Section 4 entries, directly after `<!-- DOCSYNC:CURRENT-BATCH-END -->`. Tasks 3-5 change
`scripts/docsync/` and use the `SKIP` escape.

### Task 3: Make the opening state visible (must land before Batch 23 opens)

**Files:** `scripts/docsync/renderer.py` (`_build_status_block`), `scripts/docsync/integrity.py`
(`_computed_next_wp`, the Section 3 and SESSION_CONTEXT DOC007 legs), `tests/test_docsync_renderer.py`,
`tests/test_docsync_integrity.py`.

- [x] **Step 1: Failing tests first.**
  - An active batch with zero current entries renders `Current batch: Batch 23.`.
  - With a finite plan and zero completed work packages, the next work package is the lowest planned
    number, **WP-0 included** (owner ruling, 2026-09-21). Today `_next_wp_number` drops WP-0
    (`number > 0`), so a plan of WP-0..WP-7 with nothing done reports WP-1. Pin WP-0 with a test, and
    keep the positive-only rule for the legacy no-plan path, which has no WP-0 to name.
  - A Section 3 `WP-3 is next` claim with zero entries raises DOC007.
  - The between-batches block carries the count line, with the same three wordings as the active branch
    (a resolved count, an ambiguous entry, no count).
- [x] **Step 2: Branch on the declared state.** Branch on `section_3_state.current_batch`, not on
  `current_entries`. Let `_computed_next_wp` return the plan's first open package when there are no
  entries, instead of `None`. Keep one count-line helper, called from both branches.
- [x] **Step 3: Update the assertions that pin the block's exact text.** This is a deliberate change:
  update those assertions, name them in the commit body, and assert the exact list, never `in`.
- [x] **Step 4: Live probe** (the verification standard above):
  - *Red:* an active batch with no entries and a false `WP-3 is next` claim gives DOC007. An active
    batch with no entries renders Batch 23.
  - *Near-miss green:* the true claim, `WP-0 is next`, passes. The unmodified real corpus, which is
    between batches, passes, and its block still reads `none (between batches)` plus the count.
- [x] **Step 5:** Run `--check` directly (exit 0), then the commit procedure, then
  `SKIP=doc-state-sync-check git commit`, subject `fix(docsync): Render an opened batch before its first entry`.
- [x] **Step 6: Author the count.** In the same commit's Section 4 entry, quote the measured
  `**N passed**` from `pytest -q`. `--fix` then carries it into the block. Update SESSION_CONTEXT
  Section 1 and the `FINDINGS.md` header to the same number: DOC006 and DOC008 require it, and `--fix`
  deliberately will not.

**Done 2026-09-21.** Deviations, each for a stated reason:

- **O1 folded in.** DOC012 now also names an entry whose `pytest -q` and bold count are not directly
  paired. That is the audit's O1, and a sibling of D1 in the same count chain. The authority's pattern
  moved to `logic.FULL_SUITE_RESULT_RE`, so the check and the reader cannot disagree. The pairing is
  bounded at 80 characters: Batch 22's log has a sentence citing another entry's count, and flagging it
  would be a false red. `AGENTS.md` "Which test count is authoritative" now states the one readable
  form, and both plans point there instead of paraphrasing it (DeepSeek's observation, 2026-09-21).
- **Step 3 needed no assertion change.** No existing test pinned the between-batches block's exact
  text. Two lines of the shared CLI fixture in `tests/test_docsync_cli.py` changed instead: they wrote
  `` `pytest -q`: **1234 passed** ``, a form the authority reads only through the legacy fallback. An
  archived fixture line in the same file keeps the colon form, so that fallback stays covered.
- **Step 6 was already met** by the 2026-09-21 commit that authored **1717 passed**.
- **Historical reach, measured:** 44 archived entries use an unpaired form. DOC012 reads only live
  PLAYBOOK entries, so they are reported here and not rewritten.

### Task 3b: Open Batch 23 on its branch

Immediately after Task 3, as its own commit. This is the owner's ruling of 2026-09-21 put on disk.
Task 3 has to land first: with the old renderer, an opened batch with no entries reads as
"between batches".

**Files:** `PLAYBOOK.md` (Section 3), `BATCH23_DEFINITION.md`, `.claude/SESSION_CONTEXT.md` (Section 1).

- [ ] **Step 1: Section 3.** Replace the "Next action: the owner opens Batch 23" bullet and the
  "Batch 23 is not yet defined" bullet with one bullet: `**Batch 23 is active.**`, naming
  the definition as ``Definition: `BATCH23_DEFINITION.md` `` and the branch `feat/batch23-wp0-hygiene`. Add a
  `- **Next action:** WP-0 is next.` bullet. Keep each state sentence on one line: the scanner reads
  Section 3 line by line.
- [ ] **Step 2: The definition.** Set the field to ``**Branch:** `feat/batch23-wp0-hygiene` ``, with no commit hash
  (DOC003), and set the Status line to started. In WP-4, add a bullet: one admission module takes the
  job slot, creates the job state and starts the thread, restoring the slot or removing the orphan
  when a start fails, and all three routes (album, heatmap, export) call it. Add an acceptance
  clause: a failed thread start leaves no slot held and no orphan job, tested for every route. Record
  the ruling under the definition's owner rulings, dated 2026-09-21. Proposal Rule 2 requires the
  approval to be on the record before WP-4 begins.
- [ ] **Step 3: The dashboard.** Mark Batch 23 Active in SESSION_CONTEXT Section 1, then run `--fix`.
  The managed block must now read `Current batch: Batch 23.` and `Next expected work package: WP-0.`
  If it does not, Task 3 is incomplete -- stop.
- [ ] **Step 4: Live check on the real tree.** `--check` exits 0. Then, in a throwaway copy, change
  Section 3 to `WP-3 is next` and confirm DOC007 fires.
- [ ] **Step 5:** Commit: `chore(batch23): Open Batch 23 on feat/batch23-wp0-hygiene`. From here on,
  Section 4 entries for WP work are tagged and sit inside the current-batch markers.

### Task 4: Give the archive page target a reader, and correct the cold rule

**Files:** `scripts/docsync/archives.py`, `scripts/docsync/cli.py`, `docs/architecture/documentation-tooling.md`,
`tests/test_docsync_archives.py`.

- [ ] **Step 1: Failing test.** An unpaginated archive over `max_lines` yields one warning that names
  `--paginate-archives` and writes nothing. A paginated page whose entries are not all dated yields one
  warning saying it can never age.
- [ ] **Step 2: Implement at warning severity**, so `--check` still exits 0. Allocate **DOC024**, not
  DOC021 or DOC022: those two are reserved by
  `docs/superpowers/plans/2026-09-12-repository-agnostic-plan-spec-guards.md`.
- [ ] **Step 3: Correct the document.** Replace "become cold-storage eligible after 365 days" with what
  `archives.py` does: a page ages only when it is not the writable tail, is not oversized, and every
  entry on it is dated before the cutoff, so a page of undated entries never ages. Name DOC024 in the
  catalogue, and change the catalogue heading's range in the same edit (Task 5 owns the range wording).
- [ ] **Step 4: Live probe.**
  - *Red:* the real corpus warns once for `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`, exit 0.
  - *Near-miss green:* after `--paginate-archives`, no oversize warning; the undated findings pages
    each warn once.
- [ ] **Step 5:** `--check` directly, the commit procedure, `SKIP=doc-state-sync-check git commit`,
  subject `feat(docsync): Warn when an archive outgrows its page target`.

### Task 5: Make the DOC range true

The drift is four prose sites, so the fix is to the prose. A register that renders the range would add a
mechanism in order to fix a sentence. Prefer deletion to addition (`AGENTS.md` "Commit Rules", pre-push
self-review).

**Files:** `AGENTS.md` (the table row, the "What `doc_state_sync.py` does" paragraph, "Integrity
diagnostics"), `DEVELOPMENT.md`, `docs/architecture/documentation-tooling.md` (the catalogue heading),
`FINDINGS.md` (the "starts at DOC023" note), `.docsync.toml`.

- [ ] **Step 1:** Grep the live corpus for the range:
  `git grep -n "DOC001-DOC02" -- ':!docs/history' ':!docs/logarchive' ':!docs/superpowers'`.
  Expected today: `AGENTS.md` (three hits), `DEVELOPMENT.md`, and `documentation-tooling.md`.
- [ ] **Step 2:** Replace each with a sentence that states no range, e.g. "the typed DOC diagnostics
  (catalogue: ...)", so it cannot drift again. `documentation-tooling.md` keeps the one explicit list,
  "DOC001-DOC020, DOC023 and DOC024", as the owner of the fact.
- [ ] **Step 3:** Repoint the `FINDINGS.md` note at the catalogue: the next free code is read there.
- [ ] **Step 4:** Add a `[[retired]]` declaration to `.docsync.toml` for the claim `DOC001-DOC023`.
  Scan the live corpus and allow `docs/history/*`, `docs/logarchive/*` and `docs/superpowers/*`, so the
  claim cannot come back.
- [ ] **Step 5: Live probe.**
  - *Red:* re-adding "the DOC001-DOC023 catalogue" to `AGENTS.md` gives DOC011.
  - *Near-miss green:* the same text struck through, or in a dated Section 4 entry below the marker,
    passes.
- [ ] **Step 6:** `.docsync.toml` is control plane, so run `--check` directly, then
  `SKIP=doc-state-sync-check git commit`, subject `docs(docsync): Stop stating a code range the catalogue owns`.

### Task 6: Findings hygiene

**Files:** `FINDINGS.md`, `docs/history/findings/FINDINGS_ARCHIVE.md`.

- [ ] **Step 1:** Repoint every pre-split citation by **name**: `F-SWE-5` (`orchestrator.py:912-913`,
  `:851`), `F-SWE-3` (`orchestrator.py:250-262`), and the `scrobblescope/orchestrator.py:70-71` citation.
  Then run `git grep -n "orchestrator\.py:\|routes\.py:"` over the live corpus and handle every hit in the
  same commit.
- [ ] **Step 2:** File each of these with a canonical `- [ ] **Status:**` record, a one-sentence problem
  and a `Source:` line:
  - the opening-state defect (if Task 3 has already landed, file it resolved, with its `**Completed:**` line);
  - the archive page target having no reader, and the cold rule's undocumented all-dated condition
    (resolved by Task 4 if it has landed);
  - `--check` having no diagnostic for an interrupted publication (open; DoD row 29).
- [ ] **Step 3:** Run `--fix`, which rotates what is checked, then `--check`, fixing what it reports
  rather than guessing. Commit: `docs(findings): Repoint pre-split citations and record probe defects`.

### Task 7: Close the docsync close-out plan's Progress block

**Files:** `docs/superpowers/plans/2026-09-15-docsync-closeout-archives.md`.

- [ ] **Step 1:** Read `.superpowers/sdd/2026-09-15-docsync-closeout-archives/progress.md`, the
  authority, not `progress_copy.md`. It records Task 4b as `3d8a42a`, the whole-branch review as done in
  the PR #234 round, and DOC023 as built.
- [ ] **Step 2:** Tick Task 4, 4b and the final review, and cite those commits and that PR. Anything the
  ledger calls genuinely open moves into this plan's DoD with a disposition.
- [ ] **Step 3:** Commit: `docs(plan): Record the docsync close-out plan as complete`.

### Task 8: `frontend_gate_checks.toml`

**Files:** create `frontend_gate_checks.toml`; modify `scripts/dev/frontend_gate.py` (load it, filter `CHECKS`,
derive `PLANNED_RUNS`, print the selection); `docs/architecture/documentation-tooling.md`; test
`tests/scripts/dev/test_frontend_gate_manifest.py`.

- [ ] **Step 1: Failing tests.** Disabling `divider contrast` (one profile) lowers the planned run count
  by one and the name is reported. Disabling a check listed in `required` raises `FrontendGateError`
  naming it. A name not in `CHECKS` is refused, not ignored: a typo must not silently keep a check on.
- [ ] **Step 2: Implement with `tomllib`.**
  - `required = ["stylesheet isolation", "theme tokens", "pipeline state machines", "unmatched report"]`
    (all four names exist in `CHECKS`, verified 2026-09-21), and `disabled = []`.
  - Select by check name only. Groups are an isolation concern, and a second copy of their membership
    would drift from the tuple that owns it.
  - The header states the enabled count and names every disabled check.
- [ ] **Step 3: Live probe.**
  - *Red:* disable a required check in the real manifest and run the gate: it refuses before launching
    a browser.
  - *Near-miss green:* with `disabled = []`, the gate prints the same checks-and-runs count as before
    the change and exits 0.
- [ ] **Step 4:** In `documentation-tooling.md`, replace "stays a deferred candidate" with the fact that
  it landed, and add that the decomposition's goal was isolating what executes, not reducing
  `_frontend_gate_layout.py`'s size.
- [ ] **Step 5:** Commit: `feat(gate): Select checks from a manifest, and never silently`.

### Task 9: `AGENTS.md` pointers and the installer decision

**Files:** `AGENTS.md`, `AGENT_NOTES.md` (Architectural Constraints), `docs/architecture/documentation-tooling.md`.

- [ ] **Step 1:** In "How to run", point at the CLI section of `documentation-tooling.md` for
  `--close-batch`, `--paginate-archives` and `--cold-storage`. Don't restate them.
- [ ] **Step 2:** In "Agent skills", add `docs/agents/global-rules.md` as a pointer.
- [ ] **Step 3:** Record the installer decision in `AGENT_NOTES.md`, with the corrected evidence (see
  "Errors in the earlier draft"): installing the wrapper alongside pre-commit's own hook would fail
  loudly in migration mode. The wired path, `doc-state-sync-check` first in pre-commit plus CI's explicit
  preflight, already runs the checker. The wrapper stays for repositories without pre-commit.
- [ ] **Step 4:** Check the length with `(Get-Content AGENTS.md).Count`: it must stay under 500. Commit:
  `docs(agents): Point at the full docsync CLI and record the installer decision`.

### Task 10: Re-verify the diagrams against source

After Task 1 lands. Walk every file in `docs/architecture/` against the code (`AGENTS.md` item 15),
correct only what is wrong, name the source checked in the commit body, and set `docs/ARCHITECTURE.md`'s
"Last verified" date to the day it was actually checked. Commit:
`docs(architecture): Re-verify the diagrams against the moved protocol`.

---
## Track 3 -- the approved behaviour change

### Task 11: One honest terminal outcome for both entry points (F-SWE-5)

After Task 1. Its own commit, outside WP-0's parity criterion.

**Files:** `scrobblescope/errors.py` (`internal_error`, `source: "internal"`, `retryable: False`),
`scrobblescope/heatmap.py` (`_report_heatmap_failure`), `scrobblescope/orchestrator/__init__.py` (the
`on_run_error` for `background_task`), `FINDINGS.md`, and tests in `tests/test_errors.py`,
`tests/test_heatmap.py` and `tests/services/test_orchestrator_fetch_and_process.py`.

- [ ] **Step 1: Failing tests.** A `ZeroDivisionError` from `_fetch_and_process_heatmap` makes
  `heatmap_task` publish `internal_error`. The mirror case makes `background_task` publish the same
  code rather than only log. Together they are F-SWE-5's contract: two entry points, one answer.
- [ ] **Step 2:** Change both reactions. Only the outer handler changes; the inner Last.fm status path
  keeps `lastfm_unavailable`.
- [ ] **Step 3:** Update only the assertions that pinned the borrowed code from the outer handler, and
  name each in the commit body.
- [ ] **Step 4: Live check.** Run the frontend gate, whose pipeline state machines drive both entry
  points through the real app. It must pass unchanged.
- [ ] **Step 5:** Resolve F-SWE-5 with its `**Completed:**` line. Commit:
  `fix(jobs): Publish one honest terminal state for both pipelines`.

---
## Acceptance

- Track 1: `BATCH23_DEFINITION.md` WP-0's acceptance holds; no existing test modified.
- Every control-plane task (3, 4, 5, 8) has its live-probe table, red and near-miss green, in its
  Section 4 entry.
- `pytest -q`, `pre-commit run --all-files`, `doc_state_sync.py --check` and `frontend_gate.py` all exit 0
  on the final tree, and the newest Section 4 entry carries the measured count.
- Every DoD row is a landed task or has its reason on disk in the document it names.
- No other agent's untracked path is staged, reverted or deleted.

## Owner rulings, 2026-09-21

1. **Batch 23's branch is `feat/batch23-wp0-hygiene`.** Task 3b records it, after Task 3.
2. **No worker-count guard.** Delegated to the implementer and declined; see DoD row 19.
3. **WP-0 counts as "next".** Task 3 Step 1.
4. **Job admission is folded into WP-4.** Task 3b Step 2 writes it into the definition.

No owner decision remains open in this plan.
