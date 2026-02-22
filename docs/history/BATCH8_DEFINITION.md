# Batch 8: Modular refactor (app factory + blueprints + layered structure)

Status: **Complete**
Archived from `PLAYBOOK.md` Section 4 on 2026-02-22.

---

Prerequisite:
- Batches 0-7 complete and green.

Target structure (example):
- `scrobblescope/__init__.py` with `create_app()`
- `scrobblescope/routes/` (web/api blueprints)
- `scrobblescope/services/` (Last.fm, Spotify, orchestration)
- `scrobblescope/repositories/` (job store, metadata store)
- `scrobblescope/domain/` (models/errors)

Refactor method:
- Strangler pattern:
  - Move one slice at a time.
  - Keep route behavior identical.
  - Run approval suite after each slice move.

Acceptance:
- Functional parity preserved.
- No monolithic route/data logic in one file.
- Testability and config management improved.
