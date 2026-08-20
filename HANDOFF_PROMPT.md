# Agent Hand-Off Prompt

You are continuing work on ScrobbleScope. Follow the comment-job fast-paths
in `AGENTS.md` (Session Bootstrap) when the task is a PR comment or
review-comment fix. Otherwise bootstrap first.

Every rule lives in `AGENTS.md`: the canonical read order, document roles,
token discipline, the sufficiency gate, bootstrap-conflict handling, the
validation gates, commit discipline, side-task handling, and the
Anti-Pattern Registry. Follow them there; this file restates none of them.
It carries only the two things that belong to no other file -- the check
that repository reality matches the documents, and the handoff checklist.

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
