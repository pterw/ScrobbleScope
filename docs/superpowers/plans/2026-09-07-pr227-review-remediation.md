# PR 227 review remediation

Owner-directed side task. Package all verified fixes in one commit.

## Scope and verification

- Review the full paginated PR comment inventory, excluding comment bodies
  containing `bandit` or `assert` (case insensitive). Group repeated reports
  by source location and claim; retain a disposition for every included report.
- Preserve existing owner files and the `test` worktree. Baseline HEAD:
  `a53e412ad2449d12b69324576e495172de775ae9`. The refreshed guard passes;
  baseline `pytest -q`: 938 passed; all pre-commit hooks pass.
- Keep the current layout, font provider, gate tolerances, public route
  contracts, deterministic spotlight selection, and legacy compatibility.
- Do not implement the separate WP-7 reason-code migration or the persistent
  Last.fm cache proposal as review cleanup.

## Implementation tasks

- [x] Gate: separate measurement, comparison and runner responsibilities;
  deduplicate repeated probe strings and cache the generic CDN fixture.
  Verify the live-fonts option survives runner setup. Preserve every check.
  Validate with `pytest tests/scripts/dev/test_frontend_gate.py -q`.
- [x] Backend: share Spotify artist parsing, separate spotlight presentation
  from HTTP routing, simplify heatmap validation, and reconcile stale TODOs
  against existing error and empty-state behavior. Validate route and Spotify
  tests, including failure and fallback paths.
- [x] Results: construct toast and metric content with DOM APIs, separate
  metric and spotlight responsibilities, preserve export and hydration
  behavior, use supported typography weights and computed export colors.
  Validate JavaScript syntax and real-browser sorting, toast and export flows.
- [x] Review: check cumulative changes and findings, record dispositions and
  current document corrections, run full tests, hooks, docsync, and the
  complete frontend gate. Stage named files and make one package commit.
- [ ] Follow-up: compare deployed and local headers in a browser, then
  evaluate a subtle shadow on the white index card against the cream well.
  Use the owner's current design decisions and rendered evidence.
