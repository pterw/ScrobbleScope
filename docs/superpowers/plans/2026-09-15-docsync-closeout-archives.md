# Docsync close-out and bounded archives implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** enforce multi-signal batch closure, rotate completed findings, bound
archive pages, and validate documentation before commit checks.

**Architecture:** shared Markdown scanning underpins integrity and lifecycle
checks. Pure planners produce a candidate corpus; a locked, recoverable
publisher writes it only after validation. Archive indexes preserve entry-point
paths, while an opt-in Git preflight and CI validate the commit candidate.

**Tech Stack:** Python 3.13 stdlib, existing pytest and pre-commit; no new dependencies.

## Global constraints

- Specification: `docs/superpowers/specs/2026-09-15-docsync-closeout-archives-design.md`.
- Default archive page target: 500 rendered lines. Never split or truncate an entry.
- Default cold eligibility: 365 days, only on explicit ISO as-of maintenance.
- Cold Markdown stays tracked in Git, under each archive's `cold/` directory.
- Keep finding IDs and existing archive entry-point paths stable.
- Preserve complete finding bodies and comments; pending acceptance is not completion.
- Normal check must detect bypassed close-out steps; ordinary fix must not invent closure.
- Preserve existing public facades and diagnostics; use new codes for new invariants.
- Mutation runner, frontend tools and unrelated guard logic remain audit-only.
- Test publication, migration and hook installation with temporary corpora/repositories.
- Only one implementation writer at a time. Do not revert other agents or owner edits.
- Primary tools: `C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/`.
- Use qualified Python, pytest, Ruff and pre-commit; do not install packages.
- No live hook installation, cold moves, archive migration or commits until final validation.
- Existing mixed documentation edits must not be staged as if owned by this task.
- Maintain this Progress section after each reviewed task; no push.

## Progress

- [x] Task 1: shared Markdown scanner and reproduced integrity repairs.
- [x] Task 2: finding lifecycle, bounded archives and recoverable publication.
- [x] Task 3: CLI integration and multi-signal close-out.
- [ ] Task 4: commit-candidate preflight, opt-in installer, CI and operational docs.
      Split into a code half (4a) and a documentation half (4b), run in that
      order so `AGENTS.md` is edited once by a writer that can see the finished
      tooling.
  - [x] Task 4a: preflight, installer, pre-commit ordering and the CI step.
        Reviewed 2026-09-19: Needs fixes (2 Important). Fix round 1 addressed
        all five findings and the scoped re-review was clean. The owner ruled on the
        `--no-verify` conflict the same day: control-plane commits are refused
        on every local path, with `SKIP=doc-state-sync-check` as the one named
        escape, so `--no-verify` stays forbidden without exception.
  - [ ] Task 4b: the documentation pass. Brief written at
        `.superpowers/sdd/.../task-4b-brief.md`; implementer dispatched
        2026-09-19. Its deliverable 6 (documenting the preflight and installer)
        is gated on Task 4a's review verdict.
- [ ] Final review and full validation.

Ledger: `.superpowers/sdd/2026-09-15-docsync-closeout-archives/progress.md`.
It is the authoritative progress record; a stale copy exists at the repository
root as `progress_copy.md` and must not be read as current.

Deviations so far, with reasons:

- Tasks 1 and 2 had fix rounds applied and re-reviewed by the controller
  session rather than by dispatched subagents, because those sessions had no
  subagent-dispatch tool. Disclosed, not silent.
- Task 3 was executed in six slices (3.1 config tables, 3.2 the definition-side
  close-out record, 3.3 gate wiring, 3.4 `--close-batch`, 3.5 archive
  maintenance modes, 3.6 DOC020 and subprocess tests) across three sessions,
  rather than as one dispatch. The scope was too large for one implementer
  context.
- Task 3 fix round 1 went to a fresh implementer instead of resuming the
  original, because the owner barred Opus subagents and the original
  implementer was an Opus agent. The task report file carried the context
  across, which is the documented fallback.
- Task 3's Minor findings are deferred by ruling, not fixed: `--cold-storage`
  can paginate an oversized legacy monolith as a side effect, and a deleted
  archive index with surviving pages reports no DOC020. Both are recorded in
  the ledger for the final review's triage list.
- Task 4 was split into a code half and a documentation half rather than run as
  one dispatch. Two reasons: the owner ruled mid-plan that `AGENTS.md` must come
  under 500 lines, which enlarged the documentation side well past what fits
  beside the code work, and editing `AGENTS.md` once, after the tooling is
  final, avoids a second pass contradicting the first.
- Task 4a's review was dispatched, stopped at a session close-out before
  returning a verdict, and re-dispatched on 2026-09-19 against a freshly built
  scoped diff package. Recorded because the code sat green-but-unreviewed
  across a session boundary, which is exactly the state that invites a later
  reader to assume it was accepted.
- The `UI and Accessibility Rules` section that an unrelated in-flight Batch 22
  edit deleted from `AGENTS.md` is relocated by this plan to
  `docs/agents/ui-accessibility.md` rather than restored or dropped. It is the
  single root cause of all three live gate errors, and relocation is the only
  repair consistent with the no-revert constraint and the 500-line cap. The
  full reasoning and the two rejected alternatives are in the ledger.
- New codes consumed: DOC019 (close-out) and DOC020 (archive structure). This
  exhausts DOC001-DOC020. The deferred plan
  `2026-09-12-repository-agnostic-plan-spec-guards.md` still claims DOC013 and
  DOC014 for different invariants and must renumber to DOC021/DOC022 before it
  is executed; open finding F-B21-53 proposes a third conflicting DOC013.

## File map

- `scripts/docsync/markdown.py`: fence/comment-aware, line-preserving scan.
- `scripts/docsync/declarations.py`, `integrity.py`, `parser.py`: integrate scanner and repair existing false negatives.
- `scripts/docsync/findings.py`: finding parsing, lifecycle validation and pure rotation.
- `scripts/docsync/archives.py`: index/page planning and flattened history reads.
- `scripts/docsync/transaction.py`: exclusive, fingerprint-checked, journaled publication.
- `scripts/docsync/closeout.py`: closure signals and candidate transition.
- `scripts/docsync/cli.py`: compose planning, validation and publication.
- `scripts/dev/docsync_preflight.py`, `install_docsync_hook.py`: staged snapshot and opt-in installation.
- `.pre-commit-config.yaml`, `.github/workflows/test.yml`: first-position preflight and CI backstop.
- `.docsync.toml`: strict archive configuration, separate from declaration tables.
- `tests/test_docsync_*.py`, `tests/scripts/dev/test_docsync_*.py`: regression, conservation and temporary-Git tests.
- `AGENTS.md`, `docs/agents/issue-tracker.md`, `docs/architecture/documentation-tooling.md`: canonical procedure updates.

### Task 1: shared Markdown scanner and integrity repairs

**Files:** create `scripts/docsync/markdown.py`, `tests/test_docsync_markdown.py`;
modify `scripts/docsync/declarations.py`, `integrity.py`, `parser.py`, the
full-suite authority helper in `logic.py`, and the
corresponding existing tests. Do not change guard or runtime application code.

**Interfaces:** export `prose_lines(lines: Sequence[str]) -> list[tuple[int, str]]`
with zero-based original indices; exclude fenced and HTML-comment example
content without reindexing. Export `fully_struck(line: str, start: int, end: int) -> bool`.
Preserve exact standalone DOCSYNC markers for marker parsing, not as prose.

- [ ] Write failing tests for backtick/tilde fences, fence length matching,
  commented headings, real headings after fences, and source line preservation.

```python
def test_fenced_headings_are_not_prose():
    assert prose_lines(["~~~markdown", "## Fake", "~~~", "## Real"]) == [(3, "## Real")]

def test_partial_strike_is_not_full_exemption():
    assert not fully_struck("~~old~~ still prescribed", 2, 23)
```

- [ ] Reproduce actual declaration defects with in-memory document overrides:
  citation to a fenced-only heading/list item, a boundary mentioned in prose,
  and a retired regex whose start but not end is struck. Reproduce DOC012
  with newest unbolded full-suite claim plus a bold focused result and an
  older bold full-suite authority. Preserve the legitimate inverse case.
- [ ] Run new tests and existing declaration/integrity/parser suites RED.
- [ ] Implement scanner state: opener character and length, valid matching
  closer, multiline comment suppression, original index retention. Integrate
  real-heading/list scans and complete-match strikethrough containment.

```python
for index, line in prose_lines(lines):
    if heading_pattern.match(line):
        headings.append((index, line))
# Retired exemptions use both offsets, never match.start() alone.
exempt = fully_struck(line, match.start(), match.end())
```

- [ ] Validate each explicit full-suite claim's own count formatting; a bold
  unrelated count does not exempt it. Resolve authority without publishing a
  focused count as a full-suite result.
- [ ] Run qualified pytest over all existing docsync modules plus new scanner
  tests GREEN; Ruff only owned Python files. Report exact commands, RED/GREEN
  evidence and file list in the task report. Do not commit mixed worktree files.

### Task 2: findings, bounded archives and recoverable publication

**Files:** create `scripts/docsync/findings.py`, `archives.py`, `transaction.py`,
`tests/test_docsync_findings.py`, `test_docsync_archives.py`,
`test_docsync_transaction.py`. Add runtime journal/lock ignores to `.gitignore`.
Do not modify CLI or live findings/archives in this task.

**Interfaces:** use Task 1 `prose_lines` for finding/entry boundaries.

```python
@dataclass(frozen=True)
class FindingRotation:
    active_text: str
    archive_text: str
    rotated_ids: tuple[str, ...]
    issues: tuple[IntegrityIssue, ...]

def plan_findings(active_text: str, archive_text: str) -> FindingRotation: ...

class ArchiveStore:
    def __init__(self, root: Path, max_lines: int = 500): ...
    def read(self, path: Path) -> str: ...
    def plan(self, path: Path, text: str, *, as_of: date | None = None,
             cold_days: int = 365) -> dict[Path, bytes | None]: ...

def publish(root: Path, updates: dict[Path, bytes | None],
            expected: dict[Path, bytes | None]) -> None: ...
```

Ellipses above declare signatures, not implementation placeholders: implement
all behavior in the following acceptance steps, preserving these interfaces.

- [ ] Write RED tests for valid checked rotation, unchecked open retention,
  invalid dates, duplicated statuses/IDs, checked pending-deploy records,
  checked nonterminal records and no-action explanation. Legacy prose stays
  unchanged unless explicitly reconciled; archived records without new metadata
  remain readable. Preserve comments and body exactly during rotation.
- [ ] Implement finding boundary parsing, canonical status/completion records,
  lifecycle errors, archive suffix selection and whole-body conservation.
  Invalid lifecycle state blocks rotation; eligible IDs are deterministic.
- [ ] Write RED archive tests: 500-line boundary including headers; one
  oversized indivisible entry; stable names on append; flattened same bodies;
  malformed/missing/duplicate/escaping page references; repeated planning;
  mixed dates; explicit cutoff; hot/cold authority parity.
- [ ] Implement indexes at the existing entry paths with a versioned machine
  manifest and human-readable page links. Number pages deterministically;
  retain finalized names, replace only a writable tail, mark oversized pages.
  Read legacy monoliths or all indexed pages into the same logical text.
  Preserve canonical legacy prologues in flattened text. Reject orphaned or
  multiply referenced managed pages, path escapes and symlink targets.
- [ ] Cold planning uses explicit `as_of`, all-entry dates and strict cutoff;
  move only finalized eligible pages beneath the archive's `cold/` directory.
  Index discovery includes both locations; no wall clock or deletion policy.
- [ ] Write RED transaction tests for containment/symlinks, missing-vs-existing
  preimages, concurrent writer rejection, changed read inputs, publication
  failure, interruption, rollback and recovery after a stale journal. Include
  bytes preservation and absence of partial completed transitions.
- [ ] Implement exclusive lock, expected-preimage verification, durable
  before-image journal and staged same-filesystem writes. Catch interruptions,
  restore exact bytes, recover interrupted journal before accepting new work,
  and never overwrite an externally changed source during recovery.

```python
# Compare every read input, not only the files receiving writes.
for path, before in expected.items():
    current = path.read_bytes() if path.exists() else None
    if current != before:
        raise SyncError(f"Source changed before publication: {path}")
```

- [ ] Run focused new suites GREEN and owned-file Ruff. Report measured
  conservation/idempotence and interruption behavior; no live migration.

### Task 3: CLI composition and multi-signal batch closure

**Files:** create `scripts/docsync/closeout.py`, `tests/test_docsync_closeout.py`;
modify `scripts/docsync/cli.py`, `integrity.py`, `declarations.py` strict table
recognition, `.docsync.toml`, and CLI/integrity tests.

**Consumes:** Task 2 `FindingRotation`, `ArchiveStore`, `publish`; existing
`_sync`, `collect_integrity_issues`, finite definition WP discovery.
**Produces:** existing CLI modes plus `--close-batch N`, `--paginate-archives`,
and `--cold-storage --as-of YYYY-MM-DD`, explicit write operations.
Finding lifecycle diagnostics retain DOC013-DOC018. New structural errors
use DOC019 (batch close-out) and DOC020 (archive structure); maintain all
existing diagnostic meanings.
The deferred repository-agnostic intent plan also anticipates DOC013/DOC014.
It is not opened by this work: its eventual lifecycle/authority extensions
must preserve the diagnostic meanings implemented here rather than reuse
numbers for incompatible invariants.

- [ ] Write RED temporary-corpus tests for manual closed claims with root
  definitions, incomplete/missing WP dispositions, absent/conflicting dashboard,
  wrong index/log links, opening another batch to mask closure, checked
  unrotated findings and complete valid closure. Legacy already-closed batches
  need a nonretroactive admission boundary; record the managed batch set so
  future closures cannot silently opt out. Do not require historical batches
  to be rewritten or fabricate their evidence.
- [ ] Implement closure validation from all six specification signals. A
  managed definition's explicit per-WP terminal record must cover exactly its
  declared finite WP set; absorbed items need a disposition reference.
  Admission of active Batch 22 records its incomplete states accurately and
  must not close it. Snapshot this record so deleting a WP cannot hide it.
- [ ] Close-out mode requires author-authored completion evidence before
  archiving; generate final PLAYBOOK index/status/log and dashboard references
  without checking boxes or inventing completion. Ordinary fix must not make
  this transition. Validate full candidate corpus before `publish`.
- [ ] Strict configuration adds `[archives]` with `max_lines = 500` and
  `cold_days = 365`; reject unknown keys, booleans, nonpositive limits and
  malformed values. Declaration checks continue to execute all existing tables.
- [ ] Compose read/plan/check/publish for findings and archives. Read flattened
  hot/cold history before `_sync` and integrity authority evaluation. Indexed
  stores stay indexed on append; unpaginated legacy stores migrate only with
  explicit pagination. Cold mode requires an explicit as-of date.
- [ ] `--check` does no writes and flags deterministic drift plus lifecycle,
  closure and archive errors. `--fix` plans eligible rotation and rendering,
  validates semantic candidate output and publishes as one transaction.
  Preserve documented nonzero semantics; never report success after errors.
- [ ] Test actual CLI via subprocess in temporary tracked Git corpora, including
  failed modes leaving exact preimages, successful closure, repeated check/fix,
  declaration scans of candidate paths, source-change rejection, latest-count
  authority after pagination/cold moves, and ordinary mid-batch compatibility.
- [ ] Run all docsync suites GREEN; check this worktree read-only. Do not run
  live pagination or rewrite ambiguous historical findings.

### Task 4: staged preflight, opt-in hook installation and handoff

**Files:** create `scripts/dev/docsync_preflight.py`, `install_docsync_hook.py`,
`tests/scripts/dev/test_docsync_preflight.py`, `test_docsync_hook.py`; modify
`.pre-commit-config.yaml`, `.github/workflows/test.yml`, `AGENTS.md`,
`docs/agents/issue-tracker.md`, `docs/architecture/documentation-tooling.md`.

**Consumes:** existing worktree environment resolution and new docsync CLI.
**Produces:** `docsync_preflight.py --staged` commit-candidate check,
`docsync_preflight.py --worktree` CI check, installer `--check` inspection and
explicit `--install` that requires acceptance of disclosed common-hook scope.

- [ ] Write RED temporary-Git tests for staged good/unstaged bad and staged
  bad/unstaged good documents, deleted/renamed paths, unresolved index, missing
  interpreter, tool failures and cleanup. Build a temporary candidate from
  index bytes; preserve tracked-path semantics rather than checking unrelated
  unstaged documents. Reject unresolved conflict stages before execution.
- [ ] Implement staged snapshot with Git list arguments and qualified tool
  resolution; do not copy credentials or untracked files. Run candidate's
  docsync check only after rejecting changed staged control-plane code unless
  the chosen trusted execution policy is documented and tested. Worktree mode
  uses qualified current tool paths. Return actual diagnostic failure codes.
- [ ] Write RED installer tests for primary/linked checkouts, existing unknown
  hook refusal, idempotence, missing tools, shared scope disclosure, safe target
  containment, docsync-first ordering, nonrecursive delegation and preflight
  failure preventing pre-commit invocation.
- [ ] Implement a small generated Git wrapper invoking qualified Python and
  the preflight, then qualified `python -m pre_commit hook-impl`. Inspection is
  default/read-only; no live installation. Preserve owner Graphify hooks and
  `core.hooksPath`; disclose all linked worktrees affected before explicit apply.
- [ ] Put the always-run docsync hook first; CI runs explicit preflight before
  remaining pre-commit checks. Preserve existing browser/advisory policies.
- [ ] Update canonical procedures and architecture with commands, admission,
  lifecycle format, archive discovery, recovery and hook bypass limitations.
  Keep defaults owned in configuration, linking rather than duplicating facts.
- [ ] Run new hook/preflight tests and all docsync suites GREEN. Request final
  read-only review of this control-plane diff against specification. Fix all
  material findings through one implementation writer and scoped review.
- [ ] Run qualified full pytest, pre-commit and final docsync check; only run
  a live deterministic fix after reviewing its planned changes. Update the
  PLAYBOOK side-task log with actual validation and deviations; preserve mixed
  owner edits and leave changes uncommitted. Report commands still pending,
  live installation/migrations not applied, and CI protection owner action.
