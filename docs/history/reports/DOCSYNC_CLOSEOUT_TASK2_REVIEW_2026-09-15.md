# Docsync close-out plan: Task 2 review findings (2026-09-15)

Source: `docs/superpowers/plans/2026-09-15-docsync-closeout-archives.md`,
executed via `superpowers:subagent-driven-development`. Ledger:
`.superpowers/sdd/2026-09-15-docsync-closeout-archives/progress.md` (not
committed -- git-ignored SDD workspace; this report is the durable summary).

## Status

- **Task 1** (shared Markdown scanner, `scripts/docsync/markdown.py`, plus
  DOC010-DOC012 repairs to `declarations.py`/`integrity.py`/`parser.py`):
  complete. Reviewed clean after one fix round (a DOC012 gap where a
  full-suite pass count wrapped onto its own line after an HTML comment, and
  a separate false-exemption from an unrelated bold count in the same log
  entry). 258/258 focused docsync tests, Ruff clean.
- **Task 2** (finding lifecycle + bounded archives + recoverable
  transactional publish: `scripts/docsync/findings.py`, `archives.py`,
  `transaction.py`, six new diagnostic codes DOC013-DOC018): **complete**.
  Fix round 1 (resumed 2026-09-15, a fresh implementer since the original
  handle was unavailable) addressed all 3 Important findings below with
  regression tests that reproduce each defect before the fix, per their own
  docstrings. A controller-authored scoped re-review (2026-09-16, disclosed
  deviation -- no subagent-dispatch tool available in that session) verified
  each fix against this report's findings and the design spec's own
  language, confirmed no sibling instance of the same defect class
  elsewhere in the module, and ran the 4 named regression tests
  individually plus the full docsync suite fresh: 355/355 passed, Ruff
  clean. Verdict: all 3 Important findings ADDRESSED, no new
  Critical/Important breakage. 7 Minor findings remain deferred to the
  final whole-branch review, unchanged. Full detail:
  `.superpowers/sdd/2026-09-15-docsync-closeout-archives/progress.md`.
- **Tasks 3-4** (CLI close-out composition, commit preflight/hook
  installation): not started.

This is a control-plane side-task, not Batch 22 work. Nothing here touches
live `FINDINGS.md`, the archive files, or the docsync CLI; all work stays
in the working tree per the plan's own discipline (no commits, no staging,
no live migration until final validation).

## Task 2 review: Important findings (must fix)

All three are in `scripts/docsync/archives.py` and share one shape: a path
through the pagination/index logic that loses or misplaces archive content
with no diagnostic, which is the exact property this module exists to
guarantee (`docs/superpowers/specs/2026-09-15-docsync-closeout-archives-design.md`:
"Never delete history"; "Indexes enumerate every page and its ... location").

1. **A missing index deletes every managed page, hot and cold.**
   `_load` returns an empty layout when the entry-point file is absent,
   without calling `_reject_orphans` -- that call exists only on the
   monolith branch. `_diff` then sees every existing managed page as
   undesired and schedules it for `DELETE`. Same data-loss class as a
   self-review fix already made elsewhere in the module, reached through a
   different door. No regression test covers this branch.
2. **Page content before the first entry heading is silently discarded.**
   `_read_page` keeps only the second half of `_split(...)`, dropping any
   prologue text (and the whole header if the `DOCSYNC:ARCHIVE-PAGE` marker
   is missing) with no `SyncError`. The next `plan()`/`publish()` cycle
   writes back the truncated version permanently.
3. **`page_path` ignores where the index actually lives.** It always builds
   `root/pages/...`, while `_render_index` writes root-relative `pages/<name>`
   links -- correct only when the index sits directly in `self.root`. The
   two live archives (`docs/history/findings/FINDINGS_ARCHIVE.md` and
   `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`) are in different
   directories, so this breaks as soon as Task 3 instantiates a real store
   per archive rather than a temp-root test fixture.

## Task 2 review: Minor findings (deferred, non-blocking)

4. `transaction.py`'s `_atomic_write`/`_restore` share one failure seam, so
   the rollback fault-injection tests don't exercise a genuine disk-full
   case during restore.
5. `findings.py` DOC017 (`no action` needs an explanation) false-positives
   when the explanation lives only inside a fenced block or HTML comment,
   since `prose_lines` excludes both.
6. `findings.py` DOC014-vs-DOC015 selection keys off literal words
   (`deploy`/`pending`/`accepted`) and can misattribute the diagnostic code
   on a non-terminal outcome; both remain blocking errors either way, so
   behavior is correct and only the code/remediation text can mislead.
7. `test_undated_entries_keep_their_page_hot` asserts `any(...)` instead of
   naming the specific page under test -- would pass under a masking
   failure.
8. `normalize()` collapses multi-blank-line spacing between entries to one
   blank line. Conservation claims hold modulo this normalization, not
   byte-for-byte; Task 3's first live migration commit will contain
   whitespace-only changes beyond pure repagination.
9. `publish(root, {}, {})` with both maps empty never validates `root`,
   surfacing a raw `FileNotFoundError` instead of a `SyncError`.
10. No archive-layer test pins that a fenced `### ` heading is not treated
    as a page/entry boundary (the equivalent exists for `findings.py`, not
    for `archives.py`).

## Next step

Task 2 is complete (see Status above); do not re-litigate findings 1-3 or
re-dispatch its fix loop. Minor findings 4-10 stay deferred, unchanged, to
the final whole-branch review's triage. Proceed to Task 3 (CLI integration
and multi-signal close-out) per the plan's progress checkboxes. Full detail
and the running ledger are in
`.superpowers/sdd/2026-09-15-docsync-closeout-archives/progress.md`.
