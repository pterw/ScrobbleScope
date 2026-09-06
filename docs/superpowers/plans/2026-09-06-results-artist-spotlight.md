# Results Artist Spotlight Rotation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development or superpowers:executing-plans to
> implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Rotate five stable random artists selected from the aggregate top ten.

**Architecture:** Build the candidate set while rendering a completed Results
job. Hydrate its five members after first paint through the existing artist
endpoint, then rotate the in-page records without changing album enrichment or
Heatmap polling.

**Tech Stack:** Flask, Jinja2, vanilla JavaScript, Tailwind CSS v4, Playwright,
pytest.

## Global Constraints

- Stay on branch `test`.
- Add no dependencies, database migration, or CSS rules.
- Keep album and Heatmap job lifecycles unchanged.
- Preserve a static first candidate under reduced motion.
- Discard stale hydration and image completions.

### Task 1: Select the rotation candidates

**Files:** `scrobblescope/routes.py`, `templates/results.html`,
`tests/test_routes.py`

- [x] Add a failing route test for a stable five-artist sample drawn from the
  aggregate top ten.
- [x] Aggregate artist totals, rank the top ten, and sample five with the job
  ID as the deterministic seed.
- [x] Expose the candidates through `window.APP_DATA` and render candidate zero
  as the fallback.
- [x] Run the focused route tests green.

### Task 2: Hydrate and rotate after render

**Files:** `static/js/results.js`, `templates/results.html`,
`scripts/dev/frontend_gate.py`

- [x] Remove the metric toggle's single-top-album spotlight mutation.
- [x] Hydrate all five candidates concurrently through the existing endpoint.
- [x] Add candidate-slot, active-index, and image-revision race guards.
- [x] Rotate every seven seconds and skip the timer under reduced motion.
- [x] Hide unresolved artist links and show `01 / 05` position copy.
- [x] Prove the browser assertion fails with rotation disabled and passes in
  Chromium and Firefox after restoration.

### Task 3: Record and validate

**Files:** `FINDINGS.md`, `PLAYBOOK.md`, `.claude/SESSION_CONTEXT.md`

- [x] Record F-B21-47 and align the feature spec and plan.
- [ ] Update the execution log and managed dashboard.
- [ ] Run Tailwind generation, targeted tests, the complete browser gate, full
  pytest, pre-commit, and docsync check.
- [ ] Review the cumulative diff and leave the branch uncommitted for owner
  review.
