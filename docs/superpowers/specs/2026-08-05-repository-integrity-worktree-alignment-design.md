# Repository Integrity and Worktree Alignment Guard Design

**Status:** Implemented and verified 2026-08-05. Canonical current state is
owned by `PLAYBOOK.md` Section 3 and `.claude/SESSION_CONTEXT.md` Section 1.

## Problem

Two independent safeguards are missing.

First, `doc_state_sync.py --check` can return success while live operational
documentation is internally stale. PR #168 exposed both forms: the side-task
archive prologue retained an obsolete PLAYBOOK section number and dead paths,
and the active Batch 21 definition pinned a superseded commit SHA. The
archive renderer preserves its prefix as opaque text, the cross-validator
only checks a narrow set of PLAYBOOK links, and cross-validation warnings do
not affect the exit code. A green pre-commit and CI result therefore did not
mean that the canonical handoff corpus was sound.

Second, a GitHub rebase merge replaces the PR commits on `main` with new
commit identities but does not move the linked worktree's source branch.
The old branch can then be both ahead of and behind `origin/main` even when
the two trees are byte-identical. This happened after PRs #163, #165, and
#168. The stale branch can produce a phantom reverse-direction PR or cause an
agent to merge or reapply content that is already on `main`.

The same linked-worktree boundary affects the local Python environment.
`.venv/` is gitignored and exists only in the primary checkout, so a relative
`.venv` command from the linked worktree fails unless that shared environment
was already activated. The design-validation run reproduced this with a
missing bare `pytest` command. The safe fallback was the qualified pytest
executable under the primary checkout. Without explicit worktree-aware
guidance, an agent could instead create the forbidden second environment or
install with bare pip, repeating the dependency-drift class already recorded
in `AGENTS.md`.

The first failure is deterministic repository-content drift and belongs in
the existing local/CI gate. The second is local Git topology and cannot be
meaningfully enforced in GitHub Actions' detached checkout. Combining them
would make CI behavior environment-dependent and would blur safe content
repair with destructive branch repair.

## Goals

- Make deterministic defects in the live operational documentation fail
  both pre-commit and CI.
- Detect linked-worktree and ordinary-checkout lineage problems before new
  work or a new PR begins.
- Resolve the repository's sole local virtualenv from a linked worktree
  without creating, copying, or modifying an environment.
- Distinguish the common content-identical rebase-merge artifact from a true
  content divergence.
- Produce vendor-neutral diagnostics with a stable code, exact location,
  violated invariant, and concrete remediation.
- Keep the guard read-only: it never fetches, resets, rebases, switches, or
  pushes. Destructive history repair remains an explicit owner-authorized
  operation.
- Preserve the document-role contract: `AGENTS.md` owns agent rules,
  `PLAYBOOK.md` owns live work state, and `DEVELOPMENT.md` explains the
  methodology to humans without directing agents.

## Non-goals

- Automatically fetch, reset, rebase, switch, push, or delete a branch or
  worktree.
- Infer GitHub PR state or replace GitHub review and CI inspection.
- Rewrite semantic prose automatically when more than one correction could
  be valid.
- Validate immutable dated history as though it described current state.
- Replace the pending full software-engineering sweep tracked by F-SWE-1.
- Add a dependency; both safeguards use the Python standard library and Git.

## Architecture

### 1. Blocking repository-content integrity

Add `scripts/docsync/integrity.py` as the single-purpose validation layer for
live operational documentation. It returns typed issues instead of printing
directly. Each issue contains:

- a stable code;
- `error` or `warning` severity;
- repository-relative file and line, when applicable;
- the violated invariant; and
- an exact remediation message.

`docsync.cli` remains responsible for rendering issues and choosing an exit
code. The behavior is:

- exit 0 when sync output is clean and no integrity errors exist;
- exit 1 for deterministic drift or integrity errors; and
- exit 2 for malformed input or an invocation error.

Warnings remain visible but non-blocking only when repository state cannot
prove a defect. Existing expected active-root batch notices stay warnings.
When `.claude/SESSION_CONTEXT.md` exists, a stale managed status block or a
contradictory current test count is provable and becomes an error. Its
documented optional behavior remains unchanged: checks that require the file
are skipped when the file is absent.

The integrity layer operates on a deliberately small live corpus:

- `AGENTS.md`, `HANDOFF_PROMPT.md`, `AGENT_NOTES.md`, `PLAYBOOK.md`,
  `FINDINGS.md`, and `.claude/SESSION_CONTEXT.md` when present;
- the active root batch definition derived from PLAYBOOK Section 3; and
- the prologue of `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` before
  its first dated entry.

Historical definitions, batch logs, archive entries, and dated PLAYBOOK
records are excluded. Their old paths, SHAs, and statements are intentional
point-in-time evidence.

Initial blocking invariants are narrow and tied to the observed failure
class:

1. Concrete repository-relative Markdown document references in the live
   corpus must resolve to tracked files. Clearly schematic paths containing
   glob syntax, `<placeholder>` tokens, or the canonical `BATCHN_*` template
   form are excluded rather than misreported as dead links.
2. PLAYBOOK's active-definition reference must be the sole tracked matching
   root candidate: `BATCH<batch>.md` or `BATCH<batch>_*.md`. Other batch
   tokens, generic templates, and subdirectory files are not candidates.
3. The active definition's `**Branch:**` field may name the stable working
   branch but may not pin a 7-40 character hexadecimal commit identity.
   Volatile lineage belongs only in dated PLAYBOOK records.
4. The side-task archive has one renderer-owned canonical prologue. It must
   point at PLAYBOOK Section 4 and the current `docs/logarchive/` paths.
5. When SESSION_CONTEXT is present, its managed status block and current test
   count must agree with PLAYBOOK truth.

The archive prologue is the only newly auto-fixable content. `--fix` replaces
that prefix with a constant canonical template before preserving and
rendering the dated entries. Broken links, branch metadata, and semantic
contradictions fail closed with remediation; the tool does not guess how to
rewrite them.

The existing always-run `doc-state-sync-check` pre-commit hook already runs
in the GitHub Actions Quality Gate. Integrating the blocking layer into that
command gives local and CI enforcement without adding a duplicate workflow
step.

### 2. Read-only worktree alignment guard

Add `scripts/dev/check_worktree_alignment.py`. It is a separate bootstrap
diagnostic, not a pre-commit hook. Pre-commit necessarily runs in a dirty
working tree, and GitHub Actions normally checks out a detached commit;
neither environment represents the local post-merge worktree state that the
guard protects.

The guard derives the expected active branch from PLAYBOOK Section 3 and
uses `git rev-parse`, `git status`, `git rev-list`, and tree-object IDs. It
detects both an ordinary checkout and a linked worktree through Git's own
`--git-dir` and `--git-common-dir` results; no filesystem path convention is
assumed.

For a linked worktree, the resolved common Git directory also identifies the
primary checkout. The guard reports the platform-appropriate pytest and
pre-commit executables under that checkout's `.venv` when the linked root has
no local `.venv`. It does not activate, create, install into, or repair the
environment. If neither location contains the required executables, it fails
with the existing `AGENTS.md` setup guidance rather than falling back to bare
pip. An ordinary checkout continues to use its root `.venv`.

The default comparison base is `origin/main`. The guard never fetches and
never claims that a local remote-tracking ref is current. `AGENTS.md` will
require a successful `git fetch --prune origin` immediately before the guard
when network access is available. A missing base ref is an error with that
remediation. An offline run labels its conclusion as local-ref-only.

The state decisions are deterministic:

| State | Result |
|---|---|
| Between batches, no expected work branch | Pass after basic repository diagnostics |
| Expected branch, 0 behind, 0 or more ahead | Pass |
| Expected branch, behind only | Error: branch must be advanced before new work |
| Both ahead and behind, identical trees | Error: rebase-merge artifact; request owner-authorized realignment |
| Both ahead and behind, different trees | Error: true divergence; inspect history, never auto-reset |
| Actual branch differs from PLAYBOOK | Error: wrong checkout/worktree |
| Detached HEAD in recognized CI | Explicit skip with exit 0 |
| Detached HEAD outside CI | Error |
| Missing repository | Error |
| Missing base ref while a batch is active | Error |
| Missing base ref between batches | Not consulted; ancestry is not enforced |
| Dirty worktree | Warning normally; remediation is forbidden until reconciled |
| Linked root lacks `.venv`, primary checkout has it | Pass with shared executable paths |
| Ordinary checkout lacks `.venv` | Warning; Environment Setup is the documented next step |
| Linked worktree lacks the primary `.venv` | Error; a second environment here is forbidden |
| A required tool is absent, or present without POSIX execute permission | Error; never install automatically |

For the identical-tree case, the diagnostic states the safe sequence without
executing it: verify the exact branch and clean tree, obtain the owner approval
required by `AGENTS.md`, reset to the refreshed base, then use
`--force-with-lease`. For true divergence it does not suggest a reset. This
distinction prevents a model from applying the familiar rebase-merge remedy
to unrelated commits.

Stable diagnostic codes and explicit prose are the cross-agent interface.
No behavior depends on a vendor-specific prompt, plugin, or hidden local
skill. A less capable agent can stop safely based only on the nonzero exit
status and remediation text.

### 3. Documentation ownership

Implementation updates the documents without duplicating rules:

- `AGENTS.md` owns the mandatory fetch/check point, stop conditions, and the
  owner-authorization requirement for branch realignment.
- `HANDOFF_PROMPT.md` points to that canonical guard as part of post-read
  reality verification; it does not restate the decision table.
- `DEVELOPMENT.md` retains the human-readable incident history and explains
  why content integrity and worktree topology use separate safeguards.
- `FINDINGS.md` tracks F-DOCSYNC-5, F-WORKTREE-1, and F-WORKTREE-2 as open
  P0 items until tests, hooks, documentation, and CI validation prove each
  recurrence class is blocked.
- `PLAYBOOK.md` records the side-task and keeps the remediation gate ahead of
  Batch 21 WP-1.

## Data Flow

For documentation, the CLI reads the current files, computes the existing
sync result, passes both source and rendered state to the integrity layer,
and renders all issues once. In `--check` mode, any changed managed output or
integrity error fails. In `--fix` mode, deterministic repairs are written,
the files are re-read, and integrity is evaluated again so a successful exit
describes the final on-disk state.

For worktrees, the guard reads PLAYBOOK, asks Git for the actual branch,
common directory, base relationship, worktree status, and tree IDs, then
classifies the state. No Git-writing subprocess is reachable from the guard.

## Error Handling

Diagnostics use one record per issue, for example:

```text
ERROR DOC003 BATCH21_DEFINITION.md:5 -- volatile commit SHA in Branch metadata.
Remediation: keep only the stable branch name and record lineage in PLAYBOOK Section 4.
```

```text
ERROR WT004 wip/batch-21 -- branch and origin/main are 3/3 diverged but tree-identical.
Remediation: stop; after owner approval, realign the clean branch to refreshed origin/main and force-push with lease.
```

Repository diagnostics remain stable across linked worktrees, ordinary
clones, Windows, Linux, and CI. Unexpected runner, collector, metadata-parse,
and CLI failures render ERROR WT014 without the original command, stderr,
traceback, credentials, or environment values. Explicit offline results append
informational WT013 last even on that failure path.
Tracked-file discovery failures in docsync likewise use one fixed invocation
message and expose no subprocess stderr, command, path, or credential text.

## Testing

Use test-driven development and keep the new concerns out of the already
oversized `tests/test_docsync_logic.py` tracked by F-MAS-3.

`tests/test_docsync_integrity.py` covers:

- stale and canonical archive prologues;
- a dead live-document path and an intentionally historical dead path;
- absent, duplicate, untracked, and mismatched active definitions, including
  exact-token and between-batches boundaries;
- a volatile SHA and a stable branch-only definition;
- dead references plus present/stale and absent SESSION_CONTEXT states;
- `--check` failure and post-`--fix` revalidation; and
- deterministic issue ordering and remediation text.

The peer-sized `tests/scripts/dev/test_worktree_guard*.py` modules isolate Git
command results behind the shared `worktree_guard_fakes.py` runner boundary.
They cover parsing and lineage, selected refs, CLI rendering and real
inspection-through-CLI exits, collector order, sanitized runner failures,
exact WT000-WT014 severities, detached/linked topology, and virtualenv
resolution. Cases include between-batch operation; aligned, ahead-only, and
behind-only active branches; both divergence forms; wrong branches; ordinary
and linked checkouts; detached CI and local checkouts; missing repositories,
base refs, and tools; dirty state; and the prohibition on install fallback.
Every test asserts behavior or state that fails when the relevant path is
deleted or mutated.

Repository validation remains:

```text
pytest -q
pre-commit run --all-files
python scripts/doc_state_sync.py --check
```

The implementation is complete only after the local guard is also exercised
against an aligned linked worktree and the GitHub Quality Gate passes with a
deliberately stale fixture proven to fail in tests.

## Rollout and Completion

This remediation is a P0 side-task before Batch 21 WP-1. It does not become a
new Batch 21 work package. The implementation commit will include code,
adversarial tests, canonical rule changes, human methodology documentation,
FINDINGS status updates, PLAYBOOK logging, and refreshed SESSION_CONTEXT
state as one coherent change.

F-DOCSYNC-5 closes only when the content failures above are blocking in the
existing pre-commit/CI path. F-WORKTREE-1 closes only when the local guard
classifies the post-rebase identical-tree state and `AGENTS.md` makes the
guard mandatory at bootstrap and after a rebase merge. F-WORKTREE-2 closes
only when the guard reports the sole allowed virtualenv correctly from both
ordinary and linked worktrees and the canonical environment instructions
cover that path. F-SWE-1 remains open; the full software-engineering sweep
follows this remediation rather than being treated as satisfied by it.
