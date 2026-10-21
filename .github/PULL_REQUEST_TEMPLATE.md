## Summary

<!-- What changed and why. For a tranche or batch PR, name the plan file. -->

## State

<!-- For a PR of more than one task; delete this section otherwise. -->
<!-- Keep the table true at every push: update the row when a commit lands. -->

| Task | What | Commits | Review |
|---|---|---|---|
| 1 | <one line> | <short SHAs> | <approved, or approved after N fix rounds> |

## Validation at this head

<!-- The head SHA, the gates run on it and their results (test count, browser gates, pre-commit, docsync), and the CI run once it is green. -->

## Checklist

<!-- Tick a gate box only once CI and the final gate run pass at the head that leaves draft. -->

- [ ] `pytest -q` passes (update SESSION_CONTEXT Section 1 if test count changed)
- [ ] `pre-commit run --all-files` passes (all hooks)
- [ ] `python scripts/doc_state_sync.py --check` exits 0
- [ ] PLAYBOOK Section 3 reflects current WP/task state
- [ ] PLAYBOOK Section 4 has a dated log entry:
      - Batch WP: inside `DOCSYNC:CURRENT-BATCH-START/END` markers
      - Side task: after `DOCSYNC:CURRENT-BATCH-END` marker
- [ ] Changes are within scope of the active batch definition
      (or deviation is logged in the Section 4 entry)

<!-- No attribution line (no "Generated with" footer, no `Co-authored-by`) -- see `AGENTS.md` "Co-author prohibition". -->
