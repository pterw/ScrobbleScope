# Batch 0: Baseline freeze + approval parity suite

Status: **Complete**
Archived from `PLAYBOOK.md` Section 4 on 2026-02-22.

---

Purpose:
- Freeze externally visible behavior before risky internal changes.

Deliverables:
- Golden-path approval tests for:
  - `results_loading` -> polling -> `results_complete`.
  - No-match flow.
  - Invalid username flow.
  - Unmatched quick-view flow.
- Stable fixtures/mocks for Last.fm + Spotify responses.
- Snapshot or assertions for key response fields/messages.

Acceptance:
- Approval tests pass consistently in CI/local.
- Documented baseline outputs and constraints.

Risk:
- Flaky network-coupled tests. Mitigation: mock all external APIs.
