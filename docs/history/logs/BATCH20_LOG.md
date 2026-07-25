# Batch 20 Execution Log

Archived entries for Batch 20 work packages.

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
