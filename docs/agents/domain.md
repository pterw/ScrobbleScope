# Domain Docs

How the engineering skills consume this repo's domain documentation.

## Before exploring, read these

This repo does not use a root `CONTEXT*.md` glossary or a `docs/adr/`
directory. The domain documentation is the document set that `AGENTS.md` owns:

- `docs/ARCHITECTURE.md` and `docs/architecture/` -- runtime and the two pipelines
- `.claude/SESSION_CONTEXT.md` Sections 3-4 -- project structure, dependency graph
- `AGENT_NOTES.md` -- owner preferences, local setup, constraints
- `PLAYBOOK.md` -- work order and execution history
- `BATCH21_DEFINITION.md` -- the active batch's scope and acceptance criteria
- `DESIGN.md`, `docs/design/RECONCILIATION.md`, `docs/design/designsystemaudit.md` -- the design system
- `FINDINGS.md` -- issues

If a skill expects a root context glossary, proceed silently. Do not create
one.

## Use the vocabulary the repo uses

The glossary is the repo's own: batch numbers, `WP-N` work packages, `F-*`
finding IDs, the section names in `AGENTS.md`, and the shipped design token
names. Use them as written; do not coin synonyms. Acceptance criteria come
from the active batch definition.

## Flag contradictions

If your output contradicts an existing rule or a recorded owner ruling,
surface it and cite the owner document. Do not silently override.

## Why this file does not seed CONTEXT.md or docs/adr/

The anti-duplication rule in `AGENTS.md` and the `DOC009` declarations exist
because duplicated facts drift. A second rule source would be a defect, not a
convenience. Recorded 2026-09-11.
