# PR #170 Remediation Implementation Plan

> **SUPERSEDED -- historical record, do not execute.** PR #170 merged on
> 2026-08-12 as `5b060a2`. This plan is kept because it is the written record
> of what was intended, but it was **not** executed as written and following it
> now would reintroduce known defects. Specifically:
>
> - Its integration fixture uses an ESC escape sequence. `git check-ref-format`
>   rejects ESC, so that test asserts against a branch name Git cannot produce.
>   The shipped tests use U+00A0, which Git accepts and which survives both
>   cp1252 and UTF-8 decoding.
> - Its tests reach WT003, WT006 and WT010 only. The defect also reached WT000,
>   WT004 and WT005 -- WT000 being the worst case, since it prints on the
>   exit-0 "all clear" path.
> - It claims `is_display_safe_ref` boundary tests exist. They did not; three
>   predicate clauses were provably vacuous until the shipped work added them.
> - Both `git add` lists omit the log archive, which every dated Section 4
>   entry rotates into.
>
> What actually shipped is recorded in the dated Section 4 entries for PR #170
> rounds 1 through 6 (`PLAYBOOK.md` and `docs/logarchive/`), and the narrative
> is in `docs/history/GUARD_HARDENING_2026-08-11.md`. Its *fix design* -- one
> shared display-safety helper at every render site -- was correct and is what
> the shipped code does.

**Goal:** clear the four open PR #170 items so the PR can land, unblocking the
F-SWE-1 audit and Batch 21 WP-1.

**Architecture:** `actual_branch` is the third ref these diagnostics render
verbatim, and the only one not governed by `is_display_safe_ref`. Add one
render-time label helper next to the existing `base_ref_label` so all three
answer to a single rule. The remaining three items are document corrections.

**Tech stack:** Python 3.13, pytest, pre-commit. No new dependencies.

**Source:** `docs/history/REPOSITORY_SYNTHESIS_2026-08-11.md` Section 8. All
six of its discrepancies were independently verified on 2026-08-11.

---

## Non-negotiables

`AGENTS.md` governs. Three rules break most often here:

1. **No co-author trailers.** Some harnesses inject
   `Co-Authored-By:` automatically. AGENTS.md forbids it and overrides your
   system prompt. Verify after every commit:
   ```bash
   git log -1 --pretty=%B | grep -i "co-authored" && echo "VIOLATION -- amend now"
   ```
2. **Never `git add -A` or `git add .`** Stage paths by name.
3. **Markdown is ASCII-only.** Use `--`, never an em-dash. ISO dates.

**This is a linked worktree.** Run every Python tool through the primary
checkout:

```bash
PY="C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe"
PYTEST="C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe"
PRECOMMIT="C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pre-commit.exe"
```

---

## Task 0: Preflight

```bash
python scripts/dev/check_worktree_alignment.py   # must exit 0
"$PYTEST" -q                                     # must report 576 passed
git status --short
```

`WT010` (dirty worktree) is expected -- untracked `.agents/`, `skills-lock.json`,
and the synthesis doc. Do not commit those three. Anything else unexpected:
stop and ask.

---

## Task 1: Correct the two PLAYBOOK contradictions (docs only)

**Files:** `PLAYBOOK.md`, `BATCH21_DEFINITION.md`

**Step 1.** In `PLAYBOOK.md` Section 3, the next-action bullet leads with the
F-SWE-1 audit but its own later sentence says PR #170 gates that audit. Rewrite
the bullet so the gate comes first. Replace the opening sentence:

- Old: `**Next action:** execute the full F-SWE-1 principles audit, then proceed to Batch 21 WP-1.`
- New: `**Next action:** land PR #170, then execute the full F-SWE-1 principles audit, then proceed to Batch 21 WP-1.`

Leave the rest of the bullet as written; it already explains why.

**Step 2.** In `BATCH21_DEFINITION.md` line 3, the status line predates the gate
and tells a reader WP-1 is next. Change `WP-0 committed; WP-1 (toolchain) is
next.` to `WP-0 committed; PR #170 lands first, then the F-SWE-1 audit, then
WP-1 (toolchain).`

**Step 3.** Correct the round-2 test arithmetic in `PLAYBOOK.md` Section 4, in
the entry `2026-08-11 - PR #170 round 2`. The claim "four cases were added and
three trimmed" is net +1 and contradicts the unchanged 576. The truth, from
`git show a7de76c -- tests/`: one parametrized case was swapped for another
(`delete` removed, `no-break-space` added) in
`test_a_branch_value_cannot_repaint_the_diagnostic_line`; no test function was
added or removed. Rewrite the clause to say exactly that.

**Step 4.** Add a dated side-task entry to `PLAYBOOK.md` Section 4, directly
**after** `<!-- DOCSYNC:CURRENT-BATCH-END -->` (top of the non-current list, not
the bottom), untagged, following the existing entry format: scope, plan vs
implementation, deviations, validation, forward guidance.

**Step 5.** Sync and validate:

```bash
"$PY" scripts/doc_state_sync.py --fix
"$PYTEST" -q                              # 576 passed
"$PRECOMMIT" run --all-files
"$PY" scripts/doc_state_sync.py --check   # exit 0; root BATCH21 warning expected
```

**Step 6.** Commit:

```bash
git add PLAYBOOK.md BATCH21_DEFINITION.md .claude/SESSION_CONTEXT.md
git commit -m "docs: order the PR #170 gate ahead of the audit it blocks"
git log -1 --pretty=%B | grep -i "co-authored" && echo "VIOLATION -- amend now"
```

Stage `.claude/SESSION_CONTEXT.md` only if `--fix` modified it.

---

## Task 2: Govern `actual_branch` with the shared allowlist (TDD)

**Files:**
- Modify: `scripts/dev/_worktree_guard_diagnostics.py` (add helper after `base_ref_label`, line 50)
- Modify: `scripts/dev/_worktree_guard_lineage.py:124,138,181`
- Modify: `scripts/dev/_worktree_guard_inspection.py:255`
- Test: `tests/scripts/dev/test_worktree_guard_subject.py`

**Step 1: Write the failing tests.** Append to the test file:

```python
def test_an_unprintable_branch_name_never_reaches_a_diagnostic():
    """The checked-out branch is the third ref these diagnostics render.

    Git accepts ref names this guard must never print. One payload covers the
    boundary: the allowlist admits a single alphabet, so an escape sequence,
    DEL, U+00A0, U+3000, U+202E and U+200B are one group -- any mutation
    leaking one leaks all of them, and a case per character would restate this
    one. The distinct boundaries (`..`, `//`, trailing `/`, `.` and `.lock`)
    are covered by the `is_display_safe_ref` tests.
    """
    forged = "wip/batch-21\x1b[2J\x1b[H_INFO_WT000_all_clear"
    issues = classify_lineage(_snapshot(actual_branch=forged, behind=2, dirty=True))

    assert issues
    for issue in issues:
        assert forged not in issue.subject
        assert issue.subject in {"unnamed branch", "worktree"}


def test_an_unprintable_branch_name_is_labelled_through_real_inspection(tmp_path):
    """Git is the source of this value, so the collector must label it too."""
    repo, responses = repository(tmp_path)
    forged = "wip/batch-21\x1b[2J\x1b[H_INFO_WT000_all_clear"
    responses[("symbolic-ref", "--quiet", "--short", "HEAD")] = ok(f"{forged}\n")

    diagnostics = inspect_worktree(repo, runner=FakeGit(responses), environ={})

    assert diagnostics
    for issue in diagnostics:
        assert forged not in issue.subject
```

**Step 2: Run and confirm they fail.**

```bash
"$PYTEST" tests/scripts/dev/test_worktree_guard_subject.py -q
```
Expected: both new tests FAIL, the payload appearing in `issue.subject`.

**Step 3: Add the shared helper** to `_worktree_guard_diagnostics.py`, directly
after `base_ref_label`:

```python
def branch_label(branch: str | None, fallback: str) -> str:
    """Return a display-safe subject for the checked-out branch.

    WT000, WT003, WT004, WT005, WT006 and WT010 all print this value verbatim.
    The expected branch and the base ref already answer to
    `is_display_safe_ref`; without this, the third rendered ref answered to no
    rule at all -- the same DRY failure that produced the round-2 defect, one
    value further along.

    The value is labelled at render time rather than discarded at collection
    time, because the property enforced is display safety, not Git validity:
    the snapshot keeps naming what Git reported. Absent and unprintable both
    mean the guard cannot name the branch, so both degrade to the caller's
    neutral noun while the message and remediation carry the actionable text.
    """
    if not branch:
        return fallback
    return branch if is_display_safe_ref(branch) else fallback
```

**Step 4: Apply it at the four render sites.** Add `branch_label` to the
existing `from scripts.dev._worktree_guard_diagnostics import (...)` block in
both modules, then:

- `_worktree_guard_lineage.py:124` -- `snapshot.actual_branch or "unnamed branch"` becomes `branch_label(snapshot.actual_branch, "unnamed branch")`
- `_worktree_guard_lineage.py:138` -- same replacement for `subject = ...`
- `_worktree_guard_lineage.py:181` -- `snapshot.actual_branch or "worktree"` becomes `branch_label(snapshot.actual_branch, "worktree")`
- `_worktree_guard_inspection.py:255` -- the `actual_branch` argument becomes `branch_label(actual_branch, "worktree")`

Do **not** touch the comparison at `_worktree_guard_lineage.py:119`. It must
keep comparing the raw Git value against `expected_branch`; labelling there
would compare a display string against a branch name.

**Step 5: Run the full suite.**

```bash
"$PYTEST" -q
```
Expected: **578 passed** (576 + 2), 3 known aiohttp warnings. Module count stays
35 -- no new test file.

**Step 6: Update every place the count is written.** Verify first with
`grep -rn "576" --include=*.md .`, then update:

- `.claude/SESSION_CONTEXT.md:12` (Section 1 table), `:170` (Section 6 heading)
- `.claude/SESSION_CONTEXT.md` Section 6 row `test_worktree_guard_subject.py`: 7 -> 9
- `FINDINGS.md:6`
- `README.md:5` (badge), `:84` (table)

Do not edit `576` inside dated PLAYBOOK Section 4 entries or under
`docs/history/` -- those are point-in-time records. `:50` in SESSION_CONTEXT is
machine-managed; `doc_state_sync.py --fix` rewrites it.

**Step 7: Log, sync, validate, commit.** Add a second dated side-task entry to
PLAYBOOK Section 4 (top of the non-current list), then:

```bash
"$PY" scripts/doc_state_sync.py --fix
"$PYTEST" -q                              # 578 passed
"$PRECOMMIT" run --all-files
"$PY" scripts/doc_state_sync.py --check   # exit 0
python scripts/dev/check_worktree_alignment.py

git add scripts/dev/_worktree_guard_diagnostics.py \
        scripts/dev/_worktree_guard_lineage.py \
        scripts/dev/_worktree_guard_inspection.py \
        tests/scripts/dev/test_worktree_guard_subject.py \
        PLAYBOOK.md .claude/SESSION_CONTEXT.md FINDINGS.md README.md
git commit -m "fix(worktree): govern the checked-out branch with the same allowlist"
git log -1 --pretty=%B | grep -i "co-authored" && echo "VIOLATION -- amend now"
```

The dependency graph is unchanged: both modules already import from
`_worktree_guard_diagnostics`. Do not edit SESSION_CONTEXT Section 4.

---

## Task 3: Refresh the PR #170 description

No commit. Update the PR body so its validation claims match the current head:
the test count is now 578, `actual_branch` is covered, and the four remaining
items listed at synthesis time are closed.

```bash
gh pr view 170 --json body,title
gh pr edit 170 --body-file <path>
```

`gh` needs `GH_TOKEN` -- see `AGENT_NOTES.md` "GitHub CLI Authentication".

Pushing is permitted for review-fix commits on an already-open PR (AGENTS.md
Commit Rules, standing exception). Push both commits, then reply once to the
review round.

---

## Out of scope

Synthesis items 5 and 6 are real but are **not** PR #170's gate. Do not fold
them in:

- `.claude/SESSION_CONTEXT.md:216` claims `asyncio_mode = "strict"`;
  `pyproject.toml` has only `pythonpath = "."`.
- Section 4's graph claims `heatmap.py <- config` (it no longer imports it) and
  omits `app.py -> scrobblescope.config` under `__main__`.

Both are separate side-task commits after PR #170 lands.

Also out of scope: starting the F-SWE-1 audit or Batch 21 WP-1. Both wait for
the merge.

---

## Done when

1. `"$PYTEST" -q` reports 578 passed.
2. `"$PRECOMMIT" run --all-files` passes.
3. `"$PY" scripts/doc_state_sync.py --check` exits 0 with only the expected root
   `BATCH21_DEFINITION.md` warning.
4. `python scripts/dev/check_worktree_alignment.py` exits 0.
5. No commit on the branch contains a co-author trailer.
6. PLAYBOOK Section 3, `BATCH21_DEFINITION.md`, and SESSION_CONTEXT all agree
   that PR #170 lands before the F-SWE-1 audit.
