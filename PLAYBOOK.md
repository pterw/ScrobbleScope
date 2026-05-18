# ScrobbleScope Execution Playbook

Date: 2026-02-22
Purpose: Single source of truth for work sequencing and execution history.
Rules for agent behaviour live in `AGENTS.md`; current-state snapshot in
`.claude/SESSION_CONTEXT.md`.

## 1. Why this document exists

- Provide a single source of truth for work sequencing.
- Enable continuation by another agent with minimal context loss.
- Prevent risky refactor-first changes before parity tests exist.

**Implementation principles:**
1. Approval tests before structural refactor.
2. No behavior-breaking refactors without parity checks.
3. Add observability before optimization where possible.
4. Keep changes batch-scoped and reversible.
5. Keep security-safe rendering (`tojson`, escaping) as baseline.

---

## 2. Batch order (strict sequence)

Completed batch definitions are archived individually under `docs/history/`.

### Completed batches (definitions archived)

| Batch | Title | Definition |
|-------|-------|------------|
| 0 | Baseline freeze + approval parity suite | `docs/history/definitions/BATCH0_DEFINITION.md` |
| 1 | Proper upstream failure state + retry UX | `docs/history/definitions/BATCH1_DEFINITION.md` |
| 2 | Personalized minimum listening year | `docs/history/definitions/BATCH2_DEFINITION.md` |
| 3 | Remove nested thread pattern | `docs/history/definitions/BATCH3_DEFINITION.md` |
| 4 | Expand test coverage significantly | `docs/history/definitions/BATCH4_DEFINITION.md` |
| 5 | Docstring + comment normalization | `docs/history/definitions/BATCH5_DEFINITION.md` |
| 6 | Frontend refinement/tweaks | `docs/history/definitions/BATCH6_DEFINITION.md` |
| 7 | Persistent metadata layer (Postgres) | `docs/history/definitions/BATCH7_DEFINITION.md` |
| 8 | Modular refactor (app factory + blueprints) | `docs/history/definitions/BATCH8_DEFINITION.md` |
| 9 | Audit remediation (WP-1 through WP-8) | `docs/history/definitions/BATCH9_DEFINITION.md` |
| 10 | Gemini audit remediation (WP-1 through WP-9) | `docs/history/definitions/BATCH10_DEFINITION_2026-02-21.md` |
| 11 | Gemini Priority 2 audit remediation (SoC, DRY, architecture) | `docs/history/definitions/BATCH11_DEFINITION.md` |
| 12 | Polish and observability (CSS, formatting, SoC, progress) | `docs/history/definitions/BATCH12_DEFINITION.md` |
| 13 | Internal decomposition and coverage hardening | `docs/history/definitions/BATCH13_DEFINITION.md` |
| 14 | Doc hygiene (archive restructure, docsync package, per-batch routing) | `docs/history/definitions/BATCH14_DEFINITION.md` |
| 15 | Alignment, hardening, and handoff | `docs/history/definitions/BATCH15_DEFINITION.md` |
| 16 | Script hygiene, local dev hardening, and integration testing | `docs/history/definitions/BATCH16_DEFINITION.md` |
| 17 | Agent bootstrap hardening, CI/CD improvements, and dep pinning | `docs/history/definitions/BATCH17_DEFINITION.md` |
| 18 | Scrobble heatmap -- iteration 1 | `docs/history/definitions/BATCH18_DEFINITION.md` |
| 19 | Heatmap polish -- frame, KPIs, mobile layout | `BATCH19_DEFINITION.md` |

### Open decisions (owner confirmation needed)

1. Persistent store choice: Postgres only or Postgres + Redis.
2. Retry UX policy: immediate retry button only, or retry + cooldown messaging.
3. Error copy style and user-facing tone for upstream failures.

---

## 3. Active batch + next action

- **Batch 18 complete.** All 5 WPs done. Definition archived:
  `docs/history/definitions/BATCH18_DEFINITION.md`.
- **Batch 19 is active.** Branch: `feat/heatmap`. Definition: `BATCH19_DEFINITION.md`.
- **Next action:** WP-3 -- pill rename to "Top Albums" + subtitle removal.
- WP status:
  - WP-1: Correct stale perf docs + update FINDINGS.md -- **done**
  - WP-2: Heatmap result redesign (frame, headline, KPIs, legend) -- **done**
  - WP-3: Pill rename to "Top Albums" + subtitle removal -- **pending**
  - WP-4: Pinwheel SVG clipping fix -- **pending**
  - WP-5: Mobile vertical heatmap layout -- **pending**
- **Perf note (measured 2026-05-16):** Heatmap fetch for `flounder14`
  (103 pages) took 10.9s. `lastfm.py` already uses `limit=200` and concurrent
  `as_completed` fetching. 10.9s is the rate-limit floor (103 pages /
  10 req/s = 10.3s minimum). No further optimization without heatmap-specific
  caching or rate-limit risk. Documented in FINDINGS.md F-B18-11.
- Future feature candidates (confirmed by owner roadmap):
  - **Top songs** (future): rank most-played tracks for a year (Last.fm + possibly
    Spotify enrichment, separate background task + loading/results flow).

---

## 4. Execution log (for agent handoff)

Keep only the active window here: current batch entries plus the latest 4
non-current operational logs. Older dated entries live in
`docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`.

**How to read dated entries:**
- Each heading `YYYY-MM-DD - ...` is a completion/addendum log.
- Untagged side-task history: `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`.
- Tagged batch history: per-batch logs under `docs/history/logs/`.
- Batch scope/acceptance criteria: definitions under `docs/history/definitions/`.
- Current-batch boundaries are machine-managed (do not move entries manually):
  - `<!-- DOCSYNC:CURRENT-BATCH-START -->`
  - `<!-- DOCSYNC:CURRENT-BATCH-END -->`
- After any edit here, run `python scripts/doc_state_sync.py --fix`.
- Archive search: `rg -n "^### 20" docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`

<!-- DOCSYNC:CURRENT-BATCH-START -->

### 2026-05-17 - Batch 19 WP-2: heatmap frame, headline, KPIs, and legend (Batch 19 WP-2)

- Scope: redesigned the heatmap result surface into a shareable artifact with
  a custom frame, accent username headline, four KPI stats, and a frame-top
  legend.
- Plan vs implementation:
  - Replaced the Bootstrap result `.card` wrapper with `heatmap-headline`,
    `heatmap-frame`, `heatmap-frame-top`, `heatmap-kpi-row`, and the existing
    grid/legend elements.
  - Added heatmap-scoped surface tokens and responsive frame/KPI/legend CSS
    without touching `global.css`, `base.html`, or Python files.
  - Added JS helpers for headline building, KPI rendering, best-day/active-day
    counts, current streak, and safe DOM clearing.
  - Kept user-provided username rendering on `textContent` plus
    `createTextNode`; no user data is written through HTML parsing.
  - Applied monospaced font attributes directly to SVG month/day labels.
- Deviations: clarified `BATCH19_DEFINITION.md` wording for the mobile legend.
  The original line contradicted the provided WP-2 markup and WP-5 dependency;
  the canonical behavior is now legend top-right on desktop and stacked below
  KPIs above the grid on mobile.
- Validation: `.venv\Scripts\python.exe -m pytest -q` passed with
  **385 passed** and 3 existing aiohttp/Python 3.13 warnings.
  `node --check static/js/heatmap.js` exited 0. Headless Chrome rendered a
  temporary local light/dark fixture using the actual heatmap CSS at desktop
  and mobile widths; the temporary fixture was removed before commit.
  `pre-commit run --all-files` passed with all 10 hooks green.
- Forward guidance: WP-3 can remove the old subtitle references next. Keep
  `formatDateLong` unless a fresh search proves it is unused, because tooltip
  copy still depends on it after WP-2.

### 2026-05-17 - Batch 19 WP-1: stale perf docs and bootstrap drift controls (Batch 19 WP-1)

- Scope: corrected stale heatmap performance documentation and tightened
  cross-agent bootstrap rules before UI polish begins.
- Plan vs implementation: kept the WP doc-only intent, then folded in
  owner-requested drift-control fixes discovered during audit:
  - `AGENT_NOTES.md` now points to archived Batch 18 and active Batch 19
    definitions, removes the obsolete sequential-fetch diagnosis, and records
    the measured 10.9s rate-limit floor.
  - `FINDINGS.md` is now current for Batch 19, tracks 385 tests, and reframes
    F-B18-11 as rate-limit bound rather than sequential.
  - `.gitignore` no longer ignores `FINDINGS.md`; it is shared cross-agent
    context because PLAYBOOK and Batch 19 reference it.
  - `AGENTS.md` and `HANDOFF_PROMPT.md` now align on the no-push rule and
    document the expected non-blocking root batch-definition warning while a
    batch is active.
  - `BATCH19_DEFINITION.md` acceptance criteria now distinguish active docs
    from historical archives, and WP-2/WP-5 wording was clarified.
- Deviations: added `AGENTS.md`, `HANDOFF_PROMPT.md`, `.gitignore`, and
  `BATCH19_DEFINITION.md` to WP-1 because the audit found they directly
  affected turn-one orientation and cross-agent drift mitigation.
- Validation: `.venv\Scripts\python.exe -m pytest -q` initially hit sandboxed
  Windows temp permissions, then passed with approval: **385 passed**.
  `pre-commit run --all-files` passed with all 10 hooks green after using the
  per-command Git safe-directory override required by this workspace.
- Forward guidance: WP-2 can start next. Browser visual verification will be
  most useful after WP-2, WP-4, and WP-5 if the local app is running.

### 2026-05-17 - Batch 19 WP-0: definition committed (Batch 19 WP-0)

- **Batch 19 started.** Branch `feat/heatmap` continued from Batch 18.
- Definition committed: `BATCH19_DEFINITION.md` (5 WPs: perf doc corrections,
  heatmap frame/headline/KPIs redesign, pill rename + subtitle removal,
  pinwheel clipping fix, mobile vertical layout).
- Batch 18 closed out: definition archived to
  `docs/history/definitions/BATCH18_DEFINITION.md`, Section 2 table updated,
  Section 3 updated to Batch 19 active, perf note corrected.
- Scope constraint: all Batch 19 changes confined to `heatmap.css`,
  `heatmap.js`, `templates/index.html`, pinwheel SVG, and doc files.
  No global.css, no Python changes. Full app palette/font rebrand deferred.
- **385 tests passing**, all 10 pre-commit hooks green.
- Next: WP-1 -- correct stale perf docs + update FINDINGS.md.

<!-- DOCSYNC:CURRENT-BATCH-END -->
