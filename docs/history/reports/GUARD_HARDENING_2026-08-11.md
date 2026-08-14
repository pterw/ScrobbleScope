# Worktree Guard Hardening: A Remediation Narrative

**Date:** 2026-08-11
**Subject:** PR #170, and the four PR #169 findings that preceded it
**Status:** Descriptive. This document records what happened and what it
suggests. It grants no agent authority and creates no rules; operational
rules remain owned by `AGENTS.md`.

---

## 1. What is deployed here

ScrobbleScope is a Flask application that reads a Last.fm listening history,
enriches it with Spotify metadata, caches that metadata in Postgres, and
renders album leaderboards and a scrobble heatmap. That application is not
what this document is about, and nothing described here changes it.

The subject is the **repository's own safety layer** -- the tooling that
exists because this project is built by many short-lived agent sessions that
cannot talk to each other and remember nothing between runs. Two pieces of
that layer matter here.

**`scripts/docsync/`** keeps the handoff documents consistent. It rotates log
entries, deduplicates the archive, rebuilds the machine-managed status block,
and fails the commit when a live document contradicts itself. It runs locally
as a pre-commit hook and again in the GitHub Actions Quality Gate.

**`scripts/dev/worktree_guard.py`** and its private modules answer a narrower
question at session start: is this checkout the one the work is supposed to
happen in? It reads the expected branch from `PLAYBOOK.md` Section 3, asks Git
for the actual branch, ancestry, and tree identities, resolves the sole
allowed virtualenv, and prints stable `WT000`-`WT014` diagnostics. It is
strictly read-only. It never fetches, resets, rebases, switches, pushes, or
installs.

Both shipped in PR #169, merged 2026-08-08. The design is at
`docs/superpowers/specs/2026-08-05-repository-integrity-worktree-alignment-design.md`.

### Why the guard's output is a trust boundary

One sentence in that design carries most of the weight of this document:

> A less capable agent can stop safely based only on the nonzero exit status
> and remediation text.

That is the guard's contract. An agent that understands nothing else about
the repository is supposed to be able to read `ERROR WT003 ...` and halt. The
diagnostic text is therefore not decoration -- it is the interface. Anything
that can write into that text can instruct the reader.

`WT003` interpolates the branch name it parsed out of `PLAYBOOK.md`:

```
ERROR WT003 <actual-branch> -- active Batch <n> requires branch <expected-branch>.
```

`<expected-branch>` comes from a tracked Markdown file that agents edit
routinely. That is the seam.

---

## 2. What happened, in order

### 2026-08-08, before the merge: four findings arrive too late

A Copilot review (`4888134055`) was submitted against PR #169's final head at
04:38 UTC. The PR merged at 07:57 UTC. No commit landed in between, and the
merged head is tree-identical to `main`, so all four of its findings reached
`main` unaddressed.

Nothing malfunctioned. Every remediation round on that PR had been triggered
by a *push* -- someone pushes, reviewers run, findings get swept. A review
submitted after the final push falls outside that loop by construction. It
was not late; there was simply no round left for it to belong to.

### 2026-08-11, commit `c898b2e` and before: fixing the reported instance

The first remediation (commit `ac4e210`, then `4eac0a7`) addressed the four
findings. The substantive one was that `BRANCH_RE` captured `` [^`]+ `` -- a
negated character class that matches newlines -- while Section 3 is parsed as
one newline-joined block. A branch value spanning two lines was captured
whole and printed verbatim, letting PLAYBOOK prose forge a second diagnostic
line.

The fix excluded CR and LF. It was verified: a test was watched failing, then
passing. It was also **too narrow, and the commit message overclaimed it** --
it said PLAYBOOK prose could no longer forge guard output.

Two reviewers disagreed, on the same head, within three minutes of each
other:

- Copilot (`r3754598698`): an escape sequence repaints the line without any
  newline. `ESC[2J ESC[H` clears the screen and redraws a clean verdict.
- Codex (`r3754609766`): Step 3 of the implementation plan still prescribed
  the original permissive class as a *normative instruction*, so the plan
  remained a working recipe for rebuilding the vulnerability.

Commit `c898b2e` widened the class to `` [^\x00-\x20\x7f-\x9f`]+ `` -- control
characters, DEL, the C1 range, and spaces -- and updated the plan snippet.

### 2026-08-11, commit pending: the denylist next door to an allowlist

A dispatched adversarial review found six further items. The blocking one:
`` [^\x00-\x20\x7f-\x9f`]+ `` is an **ASCII** denylist. Everything from U+00A0
upward passed straight through.

Reproduced against the real parser:

| Payload | Round-1 class | Round-2 class | Now |
|---|---|---|---|
| `wip/batch-21\nERROR ...` | admitted | rejected | rejected |
| `wip/batch-21\x1b[2J\x1b[H ...` | admitted | rejected | rejected |
| `wip/batch-21` + ASCII spaces | admitted | rejected | rejected |
| `wip/batch-21` + U+00A0 spaces | admitted | **admitted** | rejected |
| `wip/batch-21` + U+3000 | admitted | **admitted** | rejected |
| `wip/batch-21` + U+202E (bidi) | admitted | **admitted** | rejected |
| `wip/batch-21` + U+200B (zero-width) | admitted | **admitted** | rejected |
| `wip/batch-21` | admitted | admitted | admitted |

A U+00A0-padded value renders on a terminal exactly as an ASCII-padded one
does. The attack the commit message claimed to have closed still worked; only
the codepoint had changed. U+200B is worse than cosmetic -- it renders as
nothing, so `WT003` reports that the branch must be moved to the branch
already checked out, an error with no exit.

**The control that was needed already existed, one module away.**
`_worktree_guard_diagnostics.py` defines
`_SAFE_BASE_REF_RE = ^[A-Za-z0-9][A-Za-z0-9._/-]*$`, and `base_ref_label()`
applies it to the *other* ref these same diagnostics interpolate. It rejects
every payload above. Two values landing on one rendered line were governed by
two different rules, and only one of them had been thought through.

The current fix extracts that rule as `is_display_safe_ref`, used by both
call sites. `BRANCH_RE` goes back to delimiting a candidate;
`parse_batch_branch` discards candidates that fail the predicate. A rejected
value yields no branch, which the classifier already reports as `WT002`.

---

## 3. What was actually wrong

Five distinct failures, worth separating because they have different causes.

**A denylist was written where an allowlist already existed.** Not a style
preference. A denylist must anticipate every vector; this one anticipated
ASCII and shipped a hole the width of Unicode. The allowlist next door needed
no anticipation.

**Each fix addressed the reported instance.** Newline reported, newline
fixed. Escape reported, escape fixed. Each round's patch was correct about
what it was shown and silent about what it was not. Three rounds moved
through one defect class one codepoint at a time.

**Claims outran verification.** "No longer forgeable" was written when only
newlines had been closed. "Restricted to what Git actually permits in a ref
name" was false in both directions -- Git rejects `..`, `^`, `:`, `?`, `*`,
`[`, `\`, `@{`, `.lock` suffixes and trailing `/` which that class accepted,
and Git accepts non-ASCII names it rejected. "All four documented Section 3
branch styles" named a set that does not exist; three are pinned by tests.

**A fix propagated to code but not to the plan that specifies it.** The
implementation plan kept prescribing the vulnerable pattern as a normative
step. Worse, the preceding commit had edited that same file for an unrelated
reason without sweeping it for the pattern being changed.

**Test distinctness silently inverted.** Round 1 shipped three parametrized
line endings that were the same input after normalization. Round 2 fixed that
and mutation-checked the replacements. Then consolidating onto one shared
allowlist made those same replacements indistinguishable again -- when one
control governs every payload, every mutation that leaks one leaks its whole
group. A property established under one design did not survive the next.

---

## 4. What this suggests

Offered as observations, not rules. Three rounds on one PR is a thin
evidence base for amending a ruleset that every agent in this project
follows, and `AGENTS.md` is deliberately hard to change.

**Prefer the allowlist that exists to the denylist you can write.** Before
adding a validation, search the package for one that governs a sibling value.
Two values printed on the same line should answer to the same rule.

**A review can arrive after the last push.** Every remediation round here was
push-triggered, so that review belongs to no round. Whether a pre-merge check
for reviews newer than the head belongs in the canonical procedure is an
owner decision; this document only records that its absence is what let four
findings through.

**State what the code does, not what it resembles.** "Restricted to what Git
permits" was reached for because it sounded authoritative. Describing the
mechanism -- a conservative ref alphabet, deliberately narrower than Git's
rule, enforcing display safety rather than ref validity -- is both true and
more useful.

**Re-derive test distinctness after a design change, not just after writing
the test.** A mutation matrix is cheap and answers the question directly. It
caught two defects here that reading could not: a DEL payload whose spaces
masked what it claimed to isolate, and a line-break payload with no isolating
mutation at all.

**Scope a fix to the class, then check the instance is in it.** Every round
here inverted that order.

---

## 5. Cross-references

- Dated entries: the three `2026-08-11` side-task entries. All three
  (round-2, round-1, and PR #169 round-6) live in
  `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`; the non-current window
  in `PLAYBOOK.md` Section 4 keeps the four newest untagged entries
  positionally, and the round-6 entry below pushed the last of them out.
  The round-6 entry is dated 2026-08-12 and live in Section 4.
- Design: `docs/superpowers/specs/2026-08-05-repository-integrity-worktree-alignment-design.md`
- Plan: `docs/superpowers/plans/2026-08-05-worktree-safety-guard.md`
- Open guard gaps: `FINDINGS.md`, `F-WORKTREE-3`, `F-WORKTREE-4` and
  `F-WORKTREE-5` (the display-safety filter ordering, recorded open in
  `d8d3e0d` after this document was written).
- Rules: `AGENTS.md` -- unchanged by this work, and by this document.
