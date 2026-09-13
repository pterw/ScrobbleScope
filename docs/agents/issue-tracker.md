# Issue tracker: FINDINGS.md

Issues for this repo are **findings**. They live in `FINDINGS.md` at the repo
root and rotate to `docs/history/findings/FINDINGS_ARCHIVE.md`. Nothing is
deleted; the archive preserves grep history.

`AGENTS.md` -> "Finding-Writing Rules" owns the format. This file says where
the tracker is and how skills use it; it does not restate the rules.

## Locations

- Active: `FINDINGS.md`
- Archive: `docs/history/findings/FINDINGS_ARCHIVE.md`
- Format owner: `AGENTS.md`, "Finding-Writing Rules"

## Severity

| Level | Meaning |
|-------|---------|
| P0 | Fix before next deploy or next batch |
| P1 | Next batch |
| P2 | Scaling roadmap / future consideration |
| Info | Documented design choice, no action needed now |

## Creating a finding

Place it under the matching severity heading. The heading is
`### F-<context>-<N>: <title>`. Context is a batch tag (`B18`, `B19`, `B20`,
...) or one of the source tags (`MAS`, `DOCSYNC`, `AUDIT`, `LOAD`, `SWE`,
`WORKTREE`, `DATA`, `STYLE`, `FEATURE`). That tag list is complete; extend it
in `AGENTS.md` rather than coining a tag here.

Include the problem statement in one sentence, a `Status:` line, and a
`Source:` line when a named audit or session produced the finding.

## Reading a finding

Open `FINDINGS.md` on demand, for one of three reasons: the task names an
`F-*` ID, you are about to raise a defect, or you are reviewing a diff. It is
not part of the bootstrap set. An ID that is no longer active is in the
archive.

## When a skill says "publish to the issue tracker"

Add a new finding to `FINDINGS.md` under the matching severity heading,
following `AGENTS.md`. Do not add one as a side effect of another task.

## When a skill says "fetch the relevant ticket"

Read the named `F-*` entry in `FINDINGS.md`. If it is absent, grep the
archive.

## Rotation

Resolved and no-action items move to the archive with a `-- RESOLVED` or
`-- NO ACTION` suffix and keep their original ID. Standing design-decision
Info items stay active until superseded. A promoted or absorbed finding keeps
a one-line pointer in the "Deferred / future-batch candidates" block so its
old ID stays resolvable.

## Relationship to GitHub

Open findings are mirrored to GitHub issues, which are cheaper to search.
`FINDINGS.md` wins if the two disagree. GitHub pull requests are a **review**
surface, not a request surface: every change in this repo goes through a
reviewed PR, so PRs are not triaged here.
