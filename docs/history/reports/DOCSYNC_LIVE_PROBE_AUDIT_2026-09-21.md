# Docsync live-probe audit -- 2026-09-21

**Subject:** the document-integrity gate (`scripts/doc_state_sync.py` and `scripts/docsync/`) and the commit
preflight (`scripts/dev/docsync_preflight.py`).
**Tree audited:** `e6ce9d7` (the merge of PR #239).
**Method:** live probe -- the real CLI run against a throwaway copy of the committed corpus, with defects planted.
**Auditor:** a Claude Code session at the owner's request; results re-run and adjudicated by the same session.
**Verdict:** **Conditionally fit.** The gate is sound between batches and in an active batch that has at least one
logged work package. It is **not** sound in the opening state of a batch, where it silently reports the wrong
state. That state is the next one this repository enters, so the defect blocks opening Batch 23 until it is fixed.

---

## 1. Why a live probe

The standard applied is the owner's: a failing green is worse than a red. A gate that stays silent on a real
defect publishes a wrong state as verified, and a cold-resume agent trusts it. Unit tests over invented fixtures
cannot establish that a gate works on the corpus it guards. The uncommitted mutation runner showed why: 46 green
tests, while the tool itself reported 100 per cent unknown. So this audit counts only what the real command did
to real files.

## 2. Method

1. **Corpus.** `git archive e6ce9d7`, extracted to a short path outside the repository, then `git init`,
   `git add -A` and one commit tagged `base`. The `git init` is required: DOC001 resolves references through
   `git ls-files`. The path was short because the session scratchpad exceeded Windows' MAX_PATH during `git add`.
2. **Fidelity.** `doc_state_sync.py --check` on the copy printed the same summary as on the worktree
   (`current_batch_entries=0, kept_non_current=4, rotated=0`, exit 0).
3. **Red probes.** One defect planted per check, the real CLI run, and a pass recorded only if the expected
   code printed **and** the exit was nonzero. Silence counts as a failure.
4. **Near-miss controls.** The closest *valid* variant of a defect, expected to stay green. A check that fires
   on its near miss is a false red.
5. **Isolation.** `git reset --hard base` and `git clean -fd` between probes, so no probe inherits another's state.
6. **Active-batch state.** Section 3 of the copy was edited to declare Batch 23 active with its definition,
   the definition was given a branch, SESSION_CONTEXT was marked Batch 23 active, and `--fix` was run. The
   result was committed and tagged `active`; `--check` on it exited 0.
7. **Adjudication.** Every unexpected result was traced to source before being classed a defect; the harness's own errors are disclosed in Section 4, O3.

The corpus was deleted afterwards. The real repository was never written to by a probe.

## 3. Results

### 3.1 Red probes: every implemented code fires

Each probe raised **only** its own code unless noted.

| Code | Defect planted | Exit | Result |
| --- | --- | --- | --- |
| DOC001 | a backticked reference to a file that does not exist, in `AGENTS.md` | 1 | red |
| DOC002 | a second root definition declared in Section 3 (active state) | 1 | red; DOC001 also fired, correctly, for the same non-existent root path |
| DOC003 | the definition's Branch field carrying a commit hash (active state) | 1 | red |
| DOC003 | two Branch fields (active state) | 1 | red |
| DOC004 | the side-task archive prologue replaced | 1 | red |
| DOC005 | a line inserted into the managed STATUS block | 1 | red |
| DOC006 | the SESSION_CONTEXT test count changed by one | 1 | red |
| DOC007 | SESSION_CONTEXT naming the wrong active batch (active state) | 1 | red |
| DOC007 | Section 3 naming the wrong next work package, one WP entry logged | 1 | red |
| DOC007 | SESSION_CONTEXT naming the wrong next work package, one WP entry logged | 1 | red |
| DOC008 | the `FINDINGS.md` header count changed by one | 1 | red |
| DOC009 | one site of a declared shared value (`static/css/shell.css`) changed | 1 | red |
| DOC010 | a citation of a non-existent `AGENTS.md` section | 1 | red |
| DOC011 | a retired claim restated in `README.md` | 1 | red |
| DOC012 | a full-suite pass claim written without bold | 1 | red |
| DOC013 | a finding with two status lines | 1 | red |
| DOC014 | a checked finding still "pending deploy" | 1 | red |
| DOC015 | a checked finding whose outcome is `open` | 1 | red |
| DOC016 | a checked finding completed on 2026-02-30 | 1 | red |
| DOC017 | a checked `no action` finding with no explanation | 1 | red |
| DOC018 | an existing finding ID reused | 1 | red |
| DOC019 | one work package deleted from Batch 22's archived close-out record | 1 | red |
| DOC020 | an indexed archive page deleted, after `--paginate-archives` | 1 | red |
| DOC020 | an unindexed managed page added beside the index | 1 | red |
| DOC023 | a finding carrying `Status: closed.` with no lifecycle record | 1 | red |
| DOC023 | a finding whose prose says it was resolved, with no record | 1 | red |

**26 of 26 red.** The implemented set is DOC001-DOC020 and DOC023. DOC021 and DOC022 are not raised anywhere in
`scripts/docsync/` (confirmed by search), and every one of the 21 implemented codes appears in at least one test.

### 3.2 Near-miss controls: no false reds

| Control | Exit | Result |
| --- | --- | --- |
| a retired claim struck through | 0 | green |
| a retired claim inside a code fence | 0 | green |
| a missing path inside a code fence | 0 | green |
| a finding reading `Status: not closed.` | 0 | green |
| a valid `AGENTS.md` section-and-item citation | 0 | green |
| a canonical resolved finding (`- [x]`, `resolved`, ISO date) | 1, then 0 | drift reported; `--fix` rotated it to the archive with `-- RESOLVED`; then green |
| the simulated active state, freshly built | 0 | green |
| the corpus after `--paginate-archives` | 0 | green |

**8 of 8 as expected.**

### 3.3 What `--fix` will and will not write

| Situation | Behaviour | Result |
| --- | --- | --- |
| a tampered managed block | restored; `--check` then exits 0 | correct |
| a canonical resolved finding | rotated to the archive | correct |
| a rotting finding (DOC023) | file left byte-identical; `--fix` exits 1 | correct -- it does not invent the record |
| a new `**1717 passed**` entry against a dashboard and header reading 1555 | `--fix` exits 1 with DOC006 and DOC008 still red; neither figure is rewritten | correct -- hand-authored counts stay the author's |

### 3.4 Exit codes and the preflight

| Invocation | Expected | Observed |
| --- | --- | --- |
| `--cold-storage` without `--as-of` | 2 | 2 |
| `--cold-storage --as-of 2026-02-30` | 2 | 2 |
| preflight `--worktree`, `scripts/docsync/cli.py` staged | 3 | 3 |
| preflight `--worktree`, `README.md` staged | 0 | 0 |
| preflight `--worktree`, a DOC001 defect staged | 1 | 1 |

**5 of 5.** The control-plane refusal is keyed on the path, not blanket, and the checker's own verdict passes
through the preflight unchanged.

## 4. Findings

### D1 -- Blocking: the opening state of a batch is reported as "between batches"

**Observed.** Section 3 declares Batch 23 active and names its definition, SESSION_CONTEXT marks it active, and
no tagged Section 4 entry exists yet. In that state:

- `--fix` renders the managed block as `Current batch: none (between batches)` and
  `Next expected work package: n/a (next batch not defined)`, and `--check` passes;
- a Section 3 claim that `WP-3 is next`, false because nothing has been done, passes with exit 0.

With one `(Batch 23 WP-0)` entry logged, the block reads `Current batch: Batch 23.`, and the false claim raises
DOC007. So the defect is confined to the interval between opening a batch and its first logged work package.

**Cause, read at source.**

- `renderer._build_status_block` chooses its branch on `current_entries` being non-empty, not on
  `section_3_state.current_batch`. The parser had correctly returned `current_batch=23`.
- `integrity._computed_next_wp` returns `(None, False)` when there are no current entries, and the Section 3
  DOC007 leg treats `None` as "nothing to compare".

**Consequence.** The dashboard is what a cold-resume agent reads first. In this interval it states the wrong
batch state while the gate reports green. An agent following it would write untagged side-task entries for WP
work. This is the wrong-green class the gate exists to prevent, and Batch 23 enters exactly this state when its
branch is named.

**Disposition.** Fix before opening Batch 23. Task 3 of the Batch 23 WP-0 foundation plan (2026-09-21) carries
the fix, its unit tests and its live probe; Task 3b then opens the batch. File it in `FINDINGS.md` with a
canonical lifecycle record.

### D2 -- Minor, owner ruling taken: WP-0 is never "next" under a finite plan

`renderer._next_wp_number` keeps only positive work-package numbers from a definition's plan
(`number > 0`). A plan of WP-0..WP-7 with nothing done therefore reports WP-1 as next. It was not observed in
isolation, because D1 masks it in the same state, but it follows directly from the code once D1 is fixed. The
owner ruled on 2026-09-21 that WP-0 counts. The fix lands with D1.

### O1 -- Observation: the test-count authority reads one exact phrasing, and says so only indirectly

An explicit full-suite result is recognised only as `` `pytest -q` -- **N passed** `` with nothing between the
command and the count. An entry reading `` `pytest -q` (tracked suite; ...) -- **1717 passed** `` was skipped,
and the authority fell back to an older entry's 1555. The gate did not pass silently: DOC006 and DOC008 went red
against the updated figures. But its remediation points at the dashboard fields rather than at the entry whose
wording was not read. This is not a wrong green. It is a misleading red, and it cost one round. A diagnostic
naming the skipped entry would remove it. Future-batch candidate.

### O2 -- Observation: a stray file beside an archive index is ignored unless it matches the page pattern

A file named outside the managed-page pattern (`..._ARCHIVE-999.md`) beside a paginated index raised nothing.
One named inside it (`..._ARCHIVE_0999.md`) raised DOC020. This is by design -- DOC020 governs managed pages --
and is recorded only so that a reader does not take DOC020 as a general orphan-file check.

### O3 -- Observation: harness errors that were not tool defects

Three first-run failures were the harness's own. They are disclosed so the numbers above can be trusted:

- The `DOCSYNC` marker text appears twice in PLAYBOOK, once inside a backticked list in Section 4. An
  unanchored replace inserted entries at the wrong copy. Anchoring on the marker line fixed it.
- A resolved finding makes `--check` report drift (rotation pending) rather than stay green. That is correct.
- A Section 3 claim phrased `WP-3 of Batch 23` is not a claim the checker reads. The recognised form is
  `WP-N is next`.

## 5. Scope limits -- what this audit did not probe

None of the following is claimed as verified:

- `--close-batch N`, and the transactional publisher's journal replay after an interrupted publish. `--check`
  does not report a journal left behind, and that gap is recorded as a future-batch finding.
- `--cold-storage` with an eligible date on this corpus. It was exercised by the architecture review of the
  same day, not re-run here.
- The preflight's `--staged` mode, which has no live caller (the hook installer has never been run), and the CI
  path.
- DOC010's item-number variant, DOC011's dated-log exemption below the Section 4 marker, and DOC009's
  no-capture-group site form.
- The worktree guard (WT codes) and the frontend gate, beyond the guard's routine bootstrap run (exit 0).

## 6. Conclusion

Twenty-one implemented codes were probed live. All of them fire on their own defect, and none fires on its near
miss. `--fix` repairs only what it can derive and refuses to author a record or a count on anyone's behalf. The
preflight's refusal and pass-through behave as documented. On that evidence the gate is **fit** for the states
it was built for.

It is **not fit** for one state: a batch that is declared open but has no logged work package. There it renders
the wrong state and stays silent on a false next-work-package claim (D1). That is a wrong green in the
dashboard, the document agents trust most. It must be fixed, and proved by the same live probe, before Batch 23
is opened. Until then, the verdict is **conditionally fit**.
