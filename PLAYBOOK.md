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
| 0 | Baseline freeze + approval parity suite | `docs/history/BATCH0_DEFINITION.md` |
| 1 | Proper upstream failure state + retry UX | `docs/history/BATCH1_DEFINITION.md` |
| 2 | Personalized minimum listening year | `docs/history/BATCH2_DEFINITION.md` |
| 3 | Remove nested thread pattern | `docs/history/BATCH3_DEFINITION.md` |
| 4 | Expand test coverage significantly | `docs/history/BATCH4_DEFINITION.md` |
| 5 | Docstring + comment normalization | `docs/history/BATCH5_DEFINITION.md` |
| 6 | Frontend refinement/tweaks | `docs/history/BATCH6_DEFINITION.md` |
| 7 | Persistent metadata layer (Postgres) | `docs/history/BATCH7_DEFINITION.md` |
| 8 | Modular refactor (app factory + blueprints) | `docs/history/BATCH8_DEFINITION.md` |
| 9 | Audit remediation (WP-1 through WP-8) | `docs/history/BATCH9_DEFINITION.md` |
| 10 | Gemini audit remediation (WP-1 through WP-9) | `docs/history/BATCH10_DEFINITION_2026-02-21.md` |

### Open decisions (owner confirmation needed)

1. Persistent store choice: Postgres only or Postgres + Redis.
2. Retry UX policy: immediate retry button only, or retry + cooldown messaging.
3. Error copy style and user-facing tone for upstream failures.

---

## 3. Active batch + next action

- **Batch 10 is complete.** Definition: `docs/history/BATCH10_DEFINITION_2026-02-21.md`.
- **Batch 11 is complete.** Definition was inline (Gemini 3.1 Pro Priority 2
  audit remediation -- SoC, DRY, and architectural findings).
  - WP-1 (Low): CSS/JS theme consolidation. Done. (Created `global.css` +
    `theme.js`; stripped ~250 lines of duplicate CSS from 5 per-page files;
    removed dark-mode toggle JS from 5 JS files; fixed html2canvas mobile
    export; added back-to-top button on results page. 121 tests passing.)
  - WP-2 (Medium): Decompose `process_albums` in `orchestrator.py`. Done.
    (Extracted 2 closures to module-level pure functions, extracted
    `_fetch_spotify_misses` and `_build_results` helpers, added 8
    adversarial test cases. 210 tests passing.)
  - WP-3 (Low): CSS/JS DRY violations, toggle markup bug, and UX polish.
    Done. (Promoted `--info-bg` to `global.css`, removing split `:root`/
    `.dark-mode` blocks from `results.css` and hard-coded rgba from
    `loading.css`; moved duplicate modal dark-mode block from `index.css`
    and `results.css` to `global.css`; stripped Bootstrap `form-check
    form-switch` classes from toggle markup that conflicted with custom CSS
    via Bootstrap's injected SVG background-image knob; added `text-align:
    center` to loading-page `.step-text`/`.step-details`; removed redundant
    mobile release-date shortening JS from `results.js`; `var`->`const` for
    `darkSwitch`/`backToTop` in `theme.js`; dark-mode toggle track changed
    from `var(--bars-color)` to `var(--bg-color)` when checked. 121 tests
    passing.)
- Future batch feature candidates (confirmed by owner roadmap, batch number TBD):
  - **Top songs**: rank most-played tracks for a year (Last.fm + possibly
    Spotify enrichment, separate background task + loading/results flow).
  - **Listening heatmap**: scrobble density calendar for last 365 days
    (Last.fm-only, lighter background task).
- Do not start feature work (top songs, heatmap) until owner defines scope
  and assigns a batch number.

---

## 4. Execution log (for agent handoff)

Keep only the active window here: current batch entries plus the latest 4
non-current operational logs. Older dated entries live in
`docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`.

**How to read dated entries:**
- Each heading `YYYY-MM-DD - ...` is a completion/addendum log.
- Current-batch boundaries are machine-managed (do not move entries manually):
  - `<!-- DOCSYNC:CURRENT-BATCH-START -->`
  - `<!-- DOCSYNC:CURRENT-BATCH-END -->`
- After any edit here, run `python scripts/doc_state_sync.py --fix`.
- Archive search: `rg -n "^### 20" docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`

<!-- DOCSYNC:CURRENT-BATCH-START -->

<!-- DOCSYNC:CURRENT-BATCH-END -->
