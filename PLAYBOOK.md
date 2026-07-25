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
| 19 | Heatmap polish -- frame, KPIs, mobile layout | `docs/history/definitions/BATCH19_DEFINITION.md` |
| 20 | File-hygiene + docs methodology refresh | `BATCH20_DEFINITION.md` |
| 21 | UI overhaul -- TBD | `BATCH21_DEFINITION.md` |

### Open decisions (owner confirmation needed)

1. Persistent store choice: Postgres only or Postgres + Redis.
2. Retry UX policy: immediate retry button only, or retry + cooldown messaging.
3. Error copy style and user-facing tone for upstream failures.

---

## 3. Active batch + next action

- **Batch 18 is complete.** All 5 WPs done. Definition archived:
  `docs/history/definitions/BATCH18_DEFINITION.md`.
- **Batch 19 is complete.** All 5 WPs done plus owner-review follow-up.
  Definition archived: `docs/history/definitions/BATCH19_DEFINITION.md`.
  PR #152 (Batches 18 + 19) merged to `main`.
- **Batch 20 is active.** Definition: `BATCH20_DEFINITION.md` (repo root).
  Scope: file-hygiene + docs methodology refresh (README, DEVELOPMENT.md,
  FINDINGS.md rotation, AGENTS.md finding-writing rules, bootstrap skill
  update). No production-code changes. Branch: `wip/batch-20`
  (WP-0 through WP-5 landed via `file-hygeine`, merged in PR #159).
- **Batch 21 (placeholder, renumbered from Batch 20).** Definition:
  `BATCH21_DEFINITION.md` (repo root). Scope TBD -- global UI overhaul
  (font stack, palette integration, index card rework, Bootstrap CDN
  consolidation) driven by an owner audit PDF. No WP work begins until
  scope lands.
- **Next action:** Batch 20 WP-8 (close-out: archive definition, purge
  log, mark batch complete).
- Batch 20 WP status: WP-0 through WP-7 done. WP-8 not yet started.
- **Perf note (measured 2026-05-16):** Heatmap fetch for `flounder14`
  (103 pages) took 10.9s. `lastfm.py` already uses `limit=200` and concurrent
  `as_completed` fetching. 10.9s is the rate-limit floor (103 pages /
  10 req/s = 10.3s minimum). No further optimization without heatmap-specific
  caching or rate-limit risk. Documented in FINDINGS.md F-B18-11.
- **Last.timer note (checked 2026-05-19):** the referenced project uses
  aggregate `user.gettopartists`/`user.gettoptracks` calls with page fan-out,
  not exact per-scrobble recent-track timestamps. Useful for future perf
  research, but not a drop-in heatmap speedup. See FINDINGS.md F-B19-3.
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

### 2026-05-22 - Batch scaffolding (Batch 20 WP-0)

- Scope: opened Batch 20 (file-hygiene + docs methodology refresh) and
  renumbered the UI-overhaul placeholder to Batch 21, since that
  placeholder had no started WPs.
- Plan vs implementation:
  - `git mv BATCH20_DEFINITION.md BATCH21_DEFINITION.md`, header updated
    to `# BATCH21: UI overhaul -- TBD`, status note records the rename
    reason and date.
  - Wrote new `BATCH20_DEFINITION.md` -- 9 WPs (WP-0 through WP-8) covering README, DEVELOPMENT.md,
    FINDINGS.md rotation + archive, AGENTS.md finding-writing rules,
    HANDOFF_PROMPT.md pointer, and the `scrobblescope-bootstrap` skill
    update. No production-code changes; baseline is 389 tests throughout.
  - PLAYBOOK Section 2: added Batch 20 and Batch 21 rows. Section 3:
    Batch 20 marked active, Batch 21 marked placeholder pending owner's
    audit PDF, next action set to Batch 20 WP-1.
- Deviations: none -- this session found the rename staged/edited but
  uncommitted from a prior session (owner confirmed via `HANDOFF_PROMPT.md`
  handoff) and completed the WP-0 commit per the definition file's own
  instructions.
- Validation: `pytest -q` -- **389 passed**, 3 existing aiohttp/Python 3.13
  warnings (no code touched). `pre-commit run --all-files` -- all 10 hooks
  pass. `doc_state_sync.py --check` -- exit 0, two expected root-BATCH-file
  warnings (Batch 20 active + Batch 21 placeholder, both intentional).
- Forward guidance: WP-1 starts the README pass (test-file count, project
  structure, mermaid diagram refresh).

### 2026-07-24 - README counts/structure/mermaid refresh (Batch 20 WP-1)

- Scope: completed Batch 20 WP-1 in `README.md` (test-count wording, project
  structure refresh, and Mermaid flow update).
- Plan vs implementation:
  - Updated test-count references to 22 test modules.
  - Refreshed the root project-structure block with the requested
    orchestration/documentation files.
  - Replaced the older architecture mermaid with the current two-pipeline
    diagram and removed the doc-state-sync bullet from key highlights.
- Deviations: none.
- Validation: `pytest -q` -- **389 passed**. `pre-commit run --all-files` --
  all hooks pass.
- Forward guidance: continue with WP-2 roadmap trimming.

### 2026-07-24 - README roadmap trim (Batch 20 WP-2)

- Scope: completed Batch 20 WP-2 roadmap cleanup in `README.md`.
- Plan vs implementation:
  - Removed completed/scaffolding roadmap items and duplicate heatmap entries.
  - Preserved required unchecked roadmap items and converted the quality-track
    checklist into a concise reminder paragraph.
  - Added concrete forward items for orchestrator decomposition, integration
    testing, CDN consolidation, and regex hardening.
- Deviations: none.
- Validation: `pytest -q` -- **389 passed**. `pre-commit run --all-files` --
  all hooks pass.
- Forward guidance: continue with WP-3 Getting Started compression.

### 2026-07-24 - README getting-started compression (Batch 20 WP-3)

- Scope: completed Batch 20 WP-3 Getting Started tightening in `README.md`.
- Plan vs implementation:
  - Compressed the venv/setup instructions while retaining Linux + Windows
    coverage.
  - Reduced `.env` optional-tuning examples and pointed readers to
    `scrobblescope/config.py` for the full option set.
  - Tightened local DB-cache development prose while preserving prerequisites,
    one-command startup, and smoke/concurrency checks.
- Deviations: initial commit left the full 8-var optional-tuning list and the
  `load_dotenv()` trivia line in place; both corrections were applied in
  follow-up commits after reviewer feedback (`BATCH20_DEFINITION.md:107-108`).
- Validation: `pytest -q` -- **389 passed**. `pre-commit run --all-files` --
  all hooks pass.
- Forward guidance: continue with WP-4 DEVELOPMENT.md cleanup.

### 2026-07-24 - DEVELOPMENT.md path/timeline/prose cleanup (Batch 20 WP-4)

- Scope: completed Batch 20 WP-4 in `DEVELOPMENT.md`.
- Plan vs implementation:
  - Corrected the archive-definition path references to
    `docs/history/definitions/...`.
  - Updated the development-timeline framing to reflect concentrated
    Feb-March work plus lighter later follow-up.
  - Trimmed identified AI-prose padding while preserving technical intent.
- Deviations: none.
- Validation: `pytest -q` -- **389 passed**. `pre-commit run --all-files` --
  all hooks pass.
- Forward guidance: WP-5 adds the Claude Code skills subsection in
  `DEVELOPMENT.md`.

### 2026-07-24 - DEVELOPMENT.md skills subsection (Batch 20 WP-5)

- Scope: completed Batch 20 WP-5 -- added the "Claude Code Skills (tightly
  scoped tooling)" subsection to `DEVELOPMENT.md`.
- Plan vs implementation:
  - Added subsection documenting `scrobblescope-bootstrap` and
    `gemini-pr-triage` skills with their single-agent scope.
  - Placed between the doc-sync tooling section and the batch-structure section
    as specified by the definition.
- Deviations: small functional docsync fix bundled with this commit (flagged
  at PR #159 discussion_r3645236188). `scripts/docsync/logic.py` and
  `scripts/docsync/renderer.py`: corrected entry scan order from forward
  (oldest-first) to reverse so `_latest_test_count_from_entries` and
  `_build_status_block` both read the most recent entry's test count instead
  of the oldest's. Updated existing tests to reflect correct behavior. Under
  20 lines of production code; treated as an in-WP deviation per AGENTS.md
  scope-discipline rules. Raises pytest baseline from 389 to 390 (one new
  renderer regression test added).
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files` --
  all hooks pass.
- Forward guidance: WP-6 cleans up and archives `FINDINGS.md`.

### 2026-07-24 - FINDINGS.md cleanup and archive (Batch 20 WP-6)

- Scope: completed Batch 20 WP-6 -- one-time FINDINGS.md cleanup, created
  `docs/history/findings/FINDINGS_ARCHIVE.md`, standardized all remaining
  items to `F-<context>-<N>:` headings, added the rotation-policy header.
- Plan vs implementation:
  - Archived: "Resolved since last update (2026-03-02)" block, F-B18-8,
    F-B19-1, F-B19-2, F-B19-5, the F-B19-6 code-fix portion, and F-B20-1
    (written directly to the archive per the definition).
  - `BATCH21_DEFINITION.md`: F-B19-5 source reference now points to the
    archive.
  - Consolidated deferred Batch 18/19 findings into a one-line
    "Deferred / future-batch candidates" block; promoted F-B18-1 to the
    fully scoped P1 item F-B20-2; added F-B20-3 and F-B20-4.
  - Bare-number to F-ID mapping: 2 -> F-LOAD-1, 3 -> F-AUDIT-1,
    4 -> F-LOAD-2, 5 -> F-MAS-1, 6 -> F-MAS-2, 7 -> F-DOCSYNC-1,
    8 -> F-MAS-3, 9 -> F-MAS-4, 10-13 -> F-MAS-5 through F-MAS-8,
    14-16 -> F-LOAD-3 through F-LOAD-5, 18/19 -> F-FEATURE-1/2.
- Deviations (all to meet the under-200-line target while keeping
  PLAYBOOK cross-references to F-B18-11 and F-B19-3 valid):
  - Also archived F-B18-6 and F-B18-9 (both resolved; F-B18-9 verified
    against `heatmap.js`, which renders user strings via `textContent`
    and cites the finding in its header comment) though neither was on
    the definition's archive list.
  - Added F-B18-2, F-B18-12 (verified still open: no `min-width` on
    `.mode-pill`), F-B19-3, and F-B19-4 to the deferred one-liner block
    beyond the six listed in the definition.
  - Moved the 2026-03-04 load-test data table to the archive with a
    pointer left in FINDINGS.md.
  - Folded Info item 17 (orchestrator split deferral) into F-B20-2
    rather than assigning it an ID, since it duplicated F-B18-1.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
  `FINDINGS.md` is 199 physical lines (down from 418) -- meets the
  under-200 acceptance criterion; the 150-180 stretch target was not
  reachable without cutting content the definition says to keep.
- Forward guidance: WP-7 adds the FINDINGS read-on-demand pointer and
  finding-writing rules to AGENTS.md + HANDOFF_PROMPT.md + the bootstrap
  skill; F-B19-6 (naive-tz anti-pattern registration) is a natural WP-7
  companion since it also edits the AGENTS.md anti-pattern registry.

### 2026-07-24 - FINDINGS on-demand rule + finding-writing standard (Batch 20 WP-7)

- Scope: completed Batch 20 WP-7 across `AGENTS.md`, `HANDOFF_PROMPT.md`,
  and the local `scrobblescope-bootstrap` Claude Code skill.
- Plan vs implementation:
  - `AGENTS.md` Session Bootstrap: added `FINDINGS.md` as an explicit
    read-on-demand step (only when Section 4 or the task references an
    F-* ID or an open P0/P1 item).
  - `AGENTS.md`: new "Finding-Writing Rules" section after the
    Anti-Pattern Registry (F-ID format, required fields, no bare numbers,
    rotation to `docs/history/findings/FINDINGS_ARCHIVE.md`,
    cross-reference pointers for promoted/absorbed findings).
  - `HANDOFF_PROMPT.md` Section 1: symmetric on-demand FINDINGS pointer
    as new item 6; "read all five files" wording adjusted to "five core
    files" so the on-demand item is not read as mandatory.
  - Skill: finding-related cues added to the frontmatter description
    (which drives invocation) and the "When to invoke" list, plus an
    on-demand FINDINGS note in the read order. The skill file lives
    outside the repo (`~/.claude/skills/`), so it is not part of this
    commit; recorded here for traceability.
- Deviations:
  - Folded in F-B19-6 as owner-approved: registered the naive-tz
    vacuous-datetime-test anti-pattern as Anti-Pattern Registry item 6,
    citing the canonical regression test from PR #152. Since that closes
    the finding, F-B19-6 was removed from FINDINGS.md P1 and rotated to
    the archive in the same commit (avoids the silent-doc-staleness
    anti-pattern rather than waiting for WP-8).
  - Aligned the `AGENTS.md` Session Bootstrap numbered list with the
    canonical HANDOFF_PROMPT.md order (PLAYBOOK -> batch definition ->
    SESSION_CONTEXT -> AGENT_NOTES). The two files previously disagreed
    (SESSION_CONTEXT-first vs PLAYBOOK-first, missing definition step),
    a divergence flagged during this session's bootstrap; HANDOFF_PROMPT
    owns the session-start procedure per the SoC contract, so AGENTS.md
    now matches it.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: WP-8 close-out remains -- archive the definition via
  `git mv`, update PLAYBOOK Sections 2/3, purge non-current log entries
  with `--keep-non-current 0`, and refresh SESSION_CONTEXT.

<!-- DOCSYNC:CURRENT-BATCH-END -->

### 2026-07-24 - Post-merge audit gap fixes (Batch 20 audit follow-up)

- Scope: close gaps found by the owner-requested audit of PR #159 (WP-1
  through WP-5 were executed via Copilot + PR reviews; audit compared the
  merged result against `BATCH20_DEFINITION.md` acceptance criteria).
  Work continues in a `wip/batch-20` worktree off `main` for isolation.
- Plan vs implementation:
  - `README.md`: deleted the "Doc-State Sync Tooling" bullet from Key
    Implementation Highlights (WP-1 acceptance item; the WP-1 log entry
    claimed removal but no commit ever removed it). Fixed the Project
    Structure tree so the agent-docs cluster is a comment row instead of
    a fake directory nesting five root-level files, and moved `AGENTS.md`
    and `PLAYBOOK.md` into that cluster. Added the missing prose note that
    `BATCHN_DEFINITION.md` sits at the root only while a batch is active.
  - `DEVELOPMENT.md`: corrected the `scrobblescope-bootstrap` description
    to the skill's actual read order (AGENTS.md -> PLAYBOOK 3-4 -> active
    batch definition -> SESSION_CONTEXT 1-2 -> AGENT_NOTES, then git/test
    verification) replacing the inaccurate SESSION_CONTEXT-first
    early-stop description.
  - `BATCH20_DEFINITION.md` header: refreshed stale status ("awaiting
    owner audit"), branch, and 389 baseline (390 since the WP-5 deviation).
  - `PLAYBOOK.md` Section 3 + `.claude/SESSION_CONTEXT.md` Section 1:
    branch updated from merged `file-hygeine` to `wip/batch-20`.
- Deviations: Getting Started length (WP-3 target ~95-100 lines, actual
  155 after review iterations added a full `docker run` block and 3-OS
  schema-init instructions) left as-is pending owner decision:
  re-compress vs accept the expanded setup detail.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: WP-6 (FINDINGS.md cleanup and archive) is next.

### 2026-07-24 - README CSRF and UX cleanup (side-task)

- Scope: PR-review-comment-driven fixes to `README.md` and `AGENTS.md`.
- Plan vs implementation:
  - `README.md`: updated CSRF description to document three distinct injection
    mechanisms -- form-submit body token (`/results_loading`, `/results_complete`,
    `/unmatched_view`), header-only fetch (`/reset_progress`), and both body and
    header (`/heatmap_loading`). Added `/unmatched_view` to the form-submit route
    list after reviewer confirmed the hidden `csrf_token` input at
    `templates/results.html:177-178`.
  - `README.md`: removed three duplicate UX entries from the Styling & UX details
    block (rotating messages, personalized stats, onboarding) that were already
    covered in the Features section above.
  - `AGENTS.md`: removed a non-ASCII section symbol (replaced with plain text
    "Section") to comply with the ASCII-only markdown authoring rule.
- Deviations: none -- all changes are documentation-only PR review responses
  outside Batch 20 WPs; Batch 20 WP status and next action are unchanged.
- Validation: `python scripts/doc_state_sync.py --check` -- exit 0.
- Forward guidance: Batch 20 WP-6 (FINDINGS.md cleanup) is still the next
  work package.

### 2026-07-24 - DEVELOPMENT.md file-count follow-up

- Scope: side-task follow-up to close the missed Batch 20 WP-5 documentation
  requirement in `DEVELOPMENT.md` by acknowledging `FINDINGS.md` as the sixth
  advisory, read-on-demand file in the external-memory description.
- Plan vs implementation:
  - Reworded the file-count paragraph to distinguish the five core tracked
    files from advisory `FINDINGS.md`, while keeping the archive-directory
    count unchanged.
  - Kept the wording explicit so IDE-based agents (for example Claude Code
    and Codex in VS Code) do not misread `FINDINGS.md` as part of the
    mandatory bootstrap set.
- Deviations: none -- this closes a missed WP-5 acceptance item flagged in PR
  review and leaves Batch 20 WP-6 as the next unstarted work package.
- Validation: `.venv/bin/pytest -q` -- **390 passed**. `.venv/bin/pre-commit
  run --all-files` -- all hooks pass. `.venv/bin/python scripts/doc_state_sync.py
  --check` -- exit 0 with the two expected root-BATCH warnings.
- Forward guidance: WP-6 still cleans up and archives `FINDINGS.md`.

### 2026-07-24 - Restore out-of-scope README edits (side-task)

- Scope: revert the Features-section rewrite and the Acknowledgements removal
  made in PR #159 outside Batch 20 WP-1 through WP-3; keep Screenshots removal
  as intentional.
- Plan vs implementation:
  - `README.md`: restored the original flat-list Features section (removed the
    "As mentioned above" intro and the `<details>` wrapper added out-of-scope).
  - `README.md`: restored the Acknowledgements section before Author & Contact.
  - `README.md`: updated Table of Contents to re-include only the
    Acknowledgements link.
- Deviations: none -- pure restoration of pre-PR content flagged by code review
  at PR #159 discussion_r3644787390.
- Validation: `pre-commit run --all-files` -- pass. `pytest -q` -- not
  applicable (documentation-only change). `python scripts/doc_state_sync.py
  --check` -- pass.
- Forward guidance: Features and Acknowledgements now match the intended PR
  state, with Screenshots intentionally removed; any future changes to those
  sections require an explicit batch WP or deviation log entry.
