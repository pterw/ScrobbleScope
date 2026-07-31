# Agent Hand-Off Prompt

You are continuing work on ScrobbleScope. Follow the comment-job fast-paths
in `AGENTS.md` (Session Bootstrap) when the task is a PR comment or
review-comment fix. Otherwise bootstrap first.

---

## 1) Bootstrap

The canonical read order, document roles, token discipline, and sufficiency
gate are defined once in `AGENTS.md` ("Document Roles" and "Session
Bootstrap") -- follow them exactly; they are not restated here. If two
bootstrap files conflict, follow the stricter safety rule and pause only
when the conflict affects the next action. In particular, never push
without explicit owner instruction.

After reading the bootstrap files, verify reality matches the docs:

```bash
git status
git log --oneline -5
```

Confirm the branch, last commits, and any staged/modified files match what
PLAYBOOK Section 3 describes, and that `pytest -q` matches the test count
in SESSION_CONTEXT Section 1. If anything does not match, resolve the
discrepancy before doing any work.

---

## 2) Validation gates (run before every commit)

The three-command gate (`pytest -q`, `pre-commit run --all-files`,
`python scripts/doc_state_sync.py --check`) is defined in `AGENTS.md`
Commit Rules ("Procedure before every commit"). A `Root BATCH file
detected` warning from `--check` is expected while an active batch
definition is intentionally at repo root and named in PLAYBOOK Section 3;
it disappears at batch close-out.

After editing PLAYBOOK Section 4:

```bash
python scripts/doc_state_sync.py --fix
```

---

## 3) Commit discipline

Owned by `AGENTS.md` (Commit Rules and Side-Task Handling). Do not restate
or re-derive it here -- read it there.

---

## 4) Anti-patterns

Owned by `AGENTS.md` (Anti-Pattern Registry). Check your work against that
list before every commit.

---

## 5) Handoff when you are done or interrupted

After your changes are committed (following AGENTS.md commit rules and
side-task handling), document completion:

1. Update PLAYBOOK Section 3 (mark WP done or note interruption point).
2. Add a dated entry to PLAYBOOK Section 4 (inside current-batch markers
   for batch work; directly after the end marker for side-tasks).
3. Run `python scripts/doc_state_sync.py --fix`.
4. Verify `python scripts/doc_state_sync.py --check` exits 0.
5. Stage and commit PLAYBOOK.md + `.claude/SESSION_CONTEXT.md` together.
6. State clearly what remains for the next agent.
