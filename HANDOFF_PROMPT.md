# Agent Hand-Off Prompt

You are continuing work on ScrobbleScope. Read ALL bootstrap files below
before doing anything else. Do not skip any step.

---

## 1) Bootstrap (required -- read in this order)

1. `AGENTS.md` -- rules, commit format, docsync policy, anti-patterns.
2. `PLAYBOOK.md` Section 3 (active batch + next WP) + Section 4 (log).
3. The batch definition file named in PLAYBOOK Section 3.
   Active batch: definition file is at repo root (`BATCHN_DEFINITION.md`).
   Between batches: no definition file exists yet -- skip this step.
   Completed batches: file is under `docs/history/definitions/`.
4. `.claude/SESSION_CONTEXT.md` -- **required**, not optional.
   Read Section 1 (current state + test count) and Section 2 (status block)
   at minimum. Sections 3-4 if you need architecture or dependency detail.
5. `MEMORY.md` (repo root) -- user preferences, workflow conventions, local
   dev setup, discovered constraints. This is the only persistent cross-agent
   memory; non-Claude-Code agents do not have access to any other memory layer.
   Read it even if it appears similar to `AGENTS.md`; it contains facts that
   `AGENTS.md` explicitly does not duplicate.

After reading all five files, run:

```bash
git status
git log --oneline -5
```

Verify the branch, last commits, and any staged/modified files match what
PLAYBOOK Section 3 describes. If they do not match, resolve the discrepancy
before doing any work.

If PLAYBOOK Section 3, the definition file, and SESSION_CONTEXT Section 2
all agree on what is done and what is next, you have enough context to start.

---

## 2) Validation gates (run before every commit)

```bash
pytest -q
pre-commit run --all-files
python scripts/doc_state_sync.py --check
```

After editing PLAYBOOK Section 4:

```bash
python scripts/doc_state_sync.py --fix
```

---

## 3) Commit discipline

- Conventional Commits, imperative mood, max 72 chars. No co-author trailers.
- Stage files by name only. Never `git add -A` or `git add .`.
- One commit per WP.
- **Do NOT push without explicit owner instruction.** Pause after each commit.
- Update PLAYBOOK Section 3 + Section 4 BEFORE committing.
- Batch log entries use `(Batch N WP-X)` tag in the heading.
- `.claude/SESSION_CONTEXT.md` is committed and shared across all agents.
  Stage and commit it whenever it changes -- do not leave it modified and unstaged.

---

## 4) Anti-patterns (do not do these)

1. **SoC/DRY violations:** Each module has one responsibility. Extract shared
   logic rather than duplicating it. File size is not the constraint -- SoC/DRY
   is. All functions require comprehensive docstrings and inline comments on
   non-obvious logic.
2. **Vacuous tests:** Every test must fail if the function under test is deleted.
3. **Bulk staging:** Never `git add -A` or `git add .`. Stage specific files only.
4. **Skipping hooks:** Never `--no-verify`. Fix the hook failure instead.
5. **Stale Section 3:** PLAYBOOK Section 3 must reflect true WP state at all times.
6. **Missing log entries:** Every WP commit needs a dated Section 4 entry inside
   the `DOCSYNC:CURRENT-BATCH-START/END` markers.

---

## 5) Handoff when you are done or interrupted

After your code changes are committed (following AGENTS.md commit rules
and side-task handling), document completion:

1. Update PLAYBOOK Section 3 (mark WP done or note interruption point).
2. Add dated entry to PLAYBOOK Section 4 (inside current-batch markers).
3. Run `python scripts/doc_state_sync.py --fix`.
4. Verify `python scripts/doc_state_sync.py --check` exits 0.
5. Stage and commit PLAYBOOK.md + `.claude/SESSION_CONTEXT.md` together.
6. State clearly what remains for the next agent.
