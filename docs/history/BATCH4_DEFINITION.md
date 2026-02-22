# Batch 4: Expand test coverage significantly

Status: **Complete**
Archived from `PLAYBOOK.md` Section 4 on 2026-02-22.

---

Purpose:
- Lock down correctness before larger refactor.

Test additions:
- Service-level tests:
  - Last.fm retry classification and error mapping.
  - Spotify 429 retry path.
  - User not found path.
- Route tests:
  - Structured progress errors.
  - Retry endpoint behavior.
  - Registration-year validation.
- Concurrency/state tests:
  - Multiple job isolation.
  - Expired job handling.
- Frontend-focused tests (where feasible):
  - Escaping for unmatched modal content.
  - Presence of `tojson` bridges in templates.

Docstring requirement for tests:
- Use the existing format style seen in `test_home_page(client)`.

Acceptance:
- Coverage materially increased around async paths and failure states.
- No regressions in approval suite.
