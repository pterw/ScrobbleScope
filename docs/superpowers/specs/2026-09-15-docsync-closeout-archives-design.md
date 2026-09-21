# Docsync close-out and bounded archives design

Date: 2026-09-15

Status: written specification approved by the owner on 2026-09-15.

## Purpose and scope

Make formal batch close-out a checked, multi-document transition, rotate
explicitly completed findings, and retain history in bounded, searchable
Markdown files. Run the documentation preflight before other commit checks.

This is a control-plane side-task, not an additional Batch 22 work package.
It must preserve the existing enrichment implementation and unfinished work.
The mutation runner and frontend tools remain audit-only in this change.
Their defects do not become silently authorized implementation tasks.

The existing rules remain owned by [AGENTS.md](../../../AGENTS.md).
The tooling architecture remains owned by
[documentation-tooling.md](../../architecture/documentation-tooling.md).
This specification records the approved change, not a second ruleset.

## Enforcement boundary

The guarantee is about documented lifecycle invariants, not proof that every
implementation requirement works. Checked boxes do not substitute for tests,
code review, or owner acceptance.

Normal `--check`, the commit preflight, and CI must reject an incomplete or
contradictory close-out. A special close-out invocation alone is insufficient:
manual edits that bypass it must still be detected.

Local hooks can be bypassed or disabled. CI is the backstop; making its check
required through remote branch protection is a separate owner action. This
change must not alter GitHub settings or claim local hooks are unbypassable.

## Finding lifecycle

Keep each existing `### F-ID: title` heading unchanged so references remain
stable. A canonical lifecycle record has one checkbox-bearing status line:

```markdown
- [ ] **Status:** open
```

An archive-eligible record has a reviewed terminal outcome and ISO date:

```markdown
- [x] **Status:** resolved
**Completed:** 2026-09-15
```

Accepted terminal outcomes are `resolved` and `no action`; the latter requires
an explanation in the finding body. The checkbox, outcome, and completion
date must agree. Duplicate lifecycle records, invalid dates, checked open
findings, or checked findings still qualified by pending deployment or
acceptance are blocking errors, not guessed repairs.

`--fix` rotates eligible findings even between batch close-outs. `--check`
reports eligible findings that remain in the active file. Open and standing
findings from an older batch remain active; their batch number is not a
completion signal.

Rotation preserves the entire body, comments, ID, title, and lifecycle record.
Archive headings gain the existing archive outcome suffix without changing
the ID. Active/archive duplicate IDs and duplicate archived IDs are errors.

Migration must distinguish unqualified completion from local fixes awaiting
deployment, commit, or owner acceptance. Historical prose alone must not
automatically check a box. Record the evidence used to reconcile each legacy
terminal finding; leave ambiguous records active and explain the blocker.

## Batch close-out

Evaluate these independent signals together:

1. PLAYBOOK Section 3 identifies the closing batch and its completed state.
2. Its definition has an explicit completion state for every declared WP.
3. SESSION_CONTEXT Section 1 agrees on the batch and completed state.
4. PLAYBOOK's batch index points at the archived definition and batch log.
5. The definition exists at the archived location and no conflicting root
   definition remains for that closed batch.
6. Eligible completed findings have been rotated and all archive references
   resolve.

The WP parser must distinguish completion from active, pending, deferred, or
absorbed work. An absorbed WP needs an explicit disposition and reference;
an unfinished WP cannot disappear merely because it was omitted from a tally.
Do not infer closure from a single prose sentence or the absence of a root
file. Starting another batch must not conceal an incomplete prior transition.

Add an explicit close-out mode to the existing CLI for the coordinated
transition. Before writing, it must validate the intended batch, all WP
dispositions, owner-authored completion evidence, and candidate final corpus.
It then archives the definition, updates existing index references, rotates
eligible findings and logs, and refreshes the managed dashboard. It must not
invent completion evidence or mark WPs complete.

An ordinary fix may repair deterministic rendering and eligible rotation,
but must not silently close a batch or rewrite semantic completion claims.
Preserve the existing active-root reminder during ordinary mid-batch work.

## Bounded archive storage

Retain existing findings, side-task archive, and per-batch log paths as stable
entry points. When pagination is needed, those files become indexes pointing
to deterministic numbered Markdown pages. Logical batch ownership remains
separate from physical page size: even a single batch log may need pages.

Default page target: **500 lines**, configurable through `.docsync.toml`.
Count the rendered page, including headers. Split only between complete
finding or dated log entries; never split a body or fenced code block.
An entry exceeding the target occupies a dedicated oversized page whose
exception is explicit in the index. No truncation is permitted.

Use deterministic ordering and stable numbered names. Finalized pages must
not be renumbered merely because new entries arrive. An existing writable
tail may receive entries up to the configured target.

Indexes enumerate every page and its hot/cold location. Corpus discovery,
deduplication, lifecycle validation, link resolution, and test-count authority
must inspect all referenced pages. Changing retention or pagination must not
change which test result is authoritative.

Migration must compare pre/post entry IDs, content fingerprints, and counts.
Legacy monoliths remain supported until migration succeeds. Repeated fix or
migration runs must produce no further changes. Never leave both a legacy
body and a paginated copy as independent authoritative entries.

## Cold storage

Keep cold pages as searchable Markdown tracked in this repository, beneath
the relevant archive's `cold/` directory. Never delete history or move it
outside the repository.

Default eligibility age: **365 days**, configurable through `.docsync.toml`.
Cold migration is an explicit maintenance operation with an explicit ISO
as-of date. Ordinary checks and commits do not age files using today's clock.

A finalized page becomes eligible only when every entry has a known date
older than the configured cutoff. Mixed-age, undated, oversized, and writable
pages remain discoverable; undated entries must not be assigned invented
dates. Moving an eligible finalized page updates its index references and
preserves all content and IDs.

## Shared parsing and integrity repairs

Introduce a source-line-preserving Markdown scan that distinguishes real
headings, list items, fences, and declared boundary markers. Preserve public
facades and existing diagnostics; add lifecycle diagnostics without reusing
existing codes for different invariants.

Repair the reproduced docsync false negatives:

- Validate each explicit full-suite pass claim rather than exempting an
  entire log entry because a different count is bold.
- Do not resolve citation headings or numbered items from fenced examples.
- Require an entire matched retired claim to lie inside a struck span before
  exempting it.
- Match an exemption boundary as its real heading or marker, not a substring
  appearing earlier in prose or an example.

The worktree guard's related parsing weakness stays an audit finding unless
the implementation plan identifies a necessary shared-parser integration and
the owner explicitly includes that guard change. Do not refactor unrelated
guard inspection, subprocess, or environment logic.

## Commit preflight

Move the existing always-run docsync check before formatting and other hooks.
Provide a Git preflight wrapper and explicit installation procedure that
resolve the primary checkout's qualified `.venv` interpreter rather than the
retired environment or an arbitrary PATH interpreter.

The wrapper checks documentation first and then delegates to the configured
pre-commit runner without recursion. Missing tools, failed checks, and unsafe
installation targets fail closed with actionable diagnostics. It must inspect
the commit candidate, not validate unstaged changes that will not be committed.

Installation must disclose the resolved hook directory and affected linked
worktrees, preserve existing hooks, and refuse unknown wrappers rather than
overwrite them. Do not silently change `core.hooksPath`, replace the owner's
Graphify hooks, or mutate shared Git configuration during implementation tests.
Use temporary Git repositories for installation and delegation tests.

CI must run the docsync preflight explicitly before its remaining pre-commit
checks, including when local hooks were skipped. Keep the other CI policies.

## Failure handling and verification

Compute and validate the full candidate output before moving or rewriting
documents. Multi-file transitions require writer exclusion, containment
checks, staged temporary output, and a recoverable journal or equivalent
rollback. Reject changed source fingerprints before publication. A failed or
interrupted operation must not lose entries or report a completed close-out.

Regression tests must demonstrate failure on the reproduced defects before
the corresponding fix. Include conflicting batch signals, missing WPs,
pending-deploy findings, duplicate IDs, fenced examples, partial strikes,
mixed pass counts, broken indexes, oversized entries, cold discovery,
idempotence, source changes, and interrupted multi-file publication.

Test archive migration using temporary corpora and compare preserved bodies,
IDs, and latest full-suite authority. Test hooks with missing interpreters,
preflight failure, successful delegation, existing hooks, staged/unstaged
differences, and linked-worktree scope disclosure.

Before handoff, run focused tests, the full repository pytest suite,
pre-commit, and final docsync check through the primary environment. Report
actual completed commands and remaining blockers. Mutation testing is not a
gate and must not use the currently defective runner as acceptance evidence.

Update the implementation plan's progress task by task, and update the
canonical work-order/rules documents when their behavior changes. Stage only
explicitly owned paths; preserve all pre-existing changes. Do not push.
