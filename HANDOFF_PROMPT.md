# Agent Hand-Off Prompt

You are continuing work on ScrobbleScope. Follow the comment-job fast-paths
in `AGENTS.md` (Session Bootstrap) when the task is a PR comment or
review-comment fix. Otherwise bootstrap first.

Every rule lives in `AGENTS.md`: the canonical read order, document roles,
token discipline, the sufficiency gate, bootstrap-conflict handling, the
validation gates, commit discipline, side-task handling, and the
Anti-Pattern Registry. Follow them there; this file restates none of them.
It carries the post-read verification check, the worktree guard's bootstrap
edge cases, and the handoff checklist -- nothing else lives here.

---

## Bootstrap verification

After reading the bootstrap files, complete the canonical worktree gate in
`AGENTS.md` ("Session Bootstrap"), then retain this human-readable evidence
that reality matches the docs:

```bash
git status
git log --oneline -5
```

Confirm the last commits and any staged/modified files match what PLAYBOOK
Section 3 describes, and that `pytest -q` matches the test count in
SESSION_CONTEXT Section 1. If anything does not match, resolve the discrepancy
before doing any work.

---

## Bootstrap edge cases

**WT004 after a merge is expected.** `main` requires linear history and
accepts only squash and rebase merges, so merging a PR rewrites its commits
and leaves the source branch diverged from `origin/main` with an identical
tree. The guard is right to stop -- a diverged branch is normally serious --
but here the remediation is routine: confirm `git rev-parse HEAD^{tree}`
matches `origin/main^{tree}` and that `git diff HEAD origin/main` is empty,
then reset the branch onto `origin/main` and force-push with lease. If the
trees differ, stop; that is a real divergence and not this case.

Three states are expected rather than faults, so the guard does not block
on them:

- **Between batches**, there is no expected work branch and therefore no
  ancestry contract. The guard reports the checkout and skips the base
  comparison, including when `origin/main` is absent.
- **A fresh clone with no `.venv`** reports WT009 as a warning, because
  creating that environment is the next documented step (Environment Setup).
  Inside a linked worktree the same state is an error, since a second
  environment there is forbidden and only the owner can resolve it.
- **Offline**, the base result is local-ref-only and WT013 says so; the
  guard never fetches.

The initial guard launch is the sole stdlib-only bootstrap exception to the
qualified-tool rule: the primary checkout paths are not known until the
guard prints them, so bare `python` is permitted only for that launch.
After it succeeds, every subsequent Python, pytest, and pre-commit command
from a linked worktree uses the qualified primary-checkout path it printed.

**How the commands in this repository's documents are written.** Every
literal command shown in these documents -- `pytest -q`,
`pre-commit run --all-files`, `python scripts/doc_state_sync.py`,
`python app.py`, and the rest -- is written in its primary-checkout form for
readability. From a linked worktree, run each one through the qualified
path the guard printed. The commands are not repeated in qualified form at
every site; this paragraph is the single conversion rule.

---

## Handoff when you are done or interrupted

Documentation lands *in* the commit, not after it: the documentation step
of AGENTS.md Commit Rules, plus "Missing log entries" in the Anti-Pattern
Registry, require the dated Section 4 entry to
be part of the same commit as the work it describes. So before you commit:

1. Update PLAYBOOK Section 3 (mark WP done or note interruption point).
2. Add a dated entry to PLAYBOOK Section 4 (inside current-batch markers
   for batch work; directly after the end marker for side-tasks).
3. Run the validation gates in `AGENTS.md` Commit Rules ("Procedure before
   every commit"), which own the doc-sync steps and their ordering.
4. State clearly what remains for the next agent.
