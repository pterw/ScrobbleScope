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
  update). No production-code changes. Branch: `file-hygeine`.
- **Batch 21 (placeholder, renumbered from Batch 20).** Definition:
  `BATCH21_DEFINITION.md` (repo root). Scope TBD -- global UI overhaul
  (font stack, palette integration, index card rework, Bootstrap CDN
  consolidation) driven by an owner audit PDF. No WP work begins until
  scope lands.
- **Next action:** Batch 20 WP-5 (DEVELOPMENT.md: skills subsection).
- Batch 20 WP status: WP-0 through WP-4 done. WP-5 through WP-8 not yet started.
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
- Deviations: none.
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

<!-- DOCSYNC:CURRENT-BATCH-END -->

### 2026-07-24 - Copilot comment-job bootstrap trim (side-task)

- Scope: reduce unnecessary bootstrap for Copilot PR comment/review-comment
  jobs after the `copilot` Actions run failed in request processing with a
  monthly-quota error before reaching the linked review thread.
- Plan vs implementation:
  - `AGENTS.md`: added a targeted review-comment fast-path for prompts that
    link to a single `discussion_r...` thread, limiting reads to the linked
    file/lines plus only the bootstrap context that thread actually needs.
  - `HANDOFF_PROMPT.md`: removed the unconditional "read all bootstrap
    files" mandate for comment jobs and aligned the startup procedure with
    the lighter fast-path in `AGENTS.md`.
- Deviations: none -- this is a side-task CI reliability fix outside Batch 20;
  Batch 20 WP status and next action are unchanged.
- Validation: `python scripts/doc_state_sync.py --fix` -- no changes.
  `python scripts/doc_state_sync.py --check` -- pass, with the two expected
  active-root-BATCH warnings. `pytest -q` and `pre-commit run --all-files`
  could not run in this sandbox because the repo-local `.venv` and those
  executables are not present here.
- Forward guidance: if future comment jobs still hit quota, inspect whether
  the prompt is fetching full PR comment lists when a direct review-comment
  URL is already supplied.

### 2026-07-22 - Link-preview image + Open Graph meta tags (side-task)

- Scope: LinkedIn (and Slack/Discord/etc.) show no image when the app URL
  is shared, since no og:image or companion meta tags existed.
- Plan vs implementation:
  - New `static/images/social-card.png` (1200x630, standard OG/Twitter
    card size): dark gradient background, the real favicon.svg pinwheel
    mark, wordmark, and tagline. Generated by rendering an HTML page that
    embeds the actual favicon.svg markup (not a hand-approximated
    redraw) and screenshotting it at 2x via the Chrome DevTools Protocol
    browser tool, then downsampled with Pillow (already pinned in
    requirements.txt; no new dependency).
  - `templates/base.html`: added `og:type`, `og:site_name`, `og:title`,
    `og:description`, `og:image` (+width/height), `og:url`, and the
    `twitter:card`/`title`/`description`/`image` equivalents. Title and
    description are Jinja blocks (`og_title`, `og_description`) so child
    templates can override per-page; default to the existing site title
    and meta-description text. `og:image` uses
    `url_for(..., _external=True)` so it resolves to an absolute URL
    against whatever host serves the request (required -- OG scrapers
    reject relative image URLs).
- Deviations: none. Out of scope for the active Batch 20 (file-hygiene,
  no production-code changes per `BATCH20_DEFINITION.md`), so logged as
  a side-task per `AGENTS.md` Side-Task Handling rather than a Batch 20 WP.
- Validation: `pytest -q` -- **389 passed**, no change (docs/template/asset
  only, no Python logic touched). `pre-commit run --files templates/base.html
  static/images/social-card.png` -- doc-state-sync-check passed (only
  applicable hook). Verified rendered output via Flask test client: all
  12 meta tags present, `og:image` resolves to an absolute URL.
- Forward guidance: none pending. Owner should verify the card renders
  correctly on LinkedIn's actual link-preview (some platforms cache
  previews aggressively per-URL; may need LinkedIn's Post Inspector to
  force a re-scrape after first deploy).

### 2026-05-19 - Batch 19 close-out (Batch 19 close-out)

- Scope: archived the Batch 19 definition, refreshed README for the PR to
  main, and finalized PLAYBOOK + SESSION_CONTEXT to reflect Batch 19 complete.
- Plan vs implementation:
  - `git mv BATCH19_DEFINITION.md docs/history/definitions/BATCH19_DEFINITION.md`.
  - PLAYBOOK Section 2 table now links to the archived definition.
  - PLAYBOOK Section 3 marks Batch 19 complete; next action is the
    `feat/heatmap` PR to `main`.
  - SESSION_CONTEXT Batch 19 row flipped to **Complete**.
  - README bumped to 387 tests, "Top Albums" mode rename in the intro,
    framed heatmap result + KPIs + desktop calendar vs. mobile activity
    strip described, `.venv/` venv guidance aligned with AGENTS.md, and
    heatmap roadmap line updated to cover both Batch 18 and Batch 19.
- Deviations: owner kept screenshots as "coming soon" placeholders since
  the saved ones in `docs/images/` no longer reflect the current UI.
  Owner will refresh them out of band.
- Validation: `pytest -q` passed with **387 passed** and 3 existing
  aiohttp/Python 3.13 warnings. `pre-commit run --all-files` passed all 10
  hooks. `python scripts/doc_state_sync.py --check` exited 0 with the
  expected root warning gone after archiving the definition.
- Forward guidance: open the PR for `feat/heatmap` -> `main`, address any
  reviewer comments, merge, and deploy. Batch 20 (heavy UI refactor) is
  to be scoped later and is explicitly out of this PR.

### 2026-05-19 - PR #152 Gemini Code Review fixes (side-task)

- Scope: addressed three substantive Gemini Code Review comments on the
  open `feat/heatmap` PR.  Deferred three "broad except Exception"
  comments to the future error-handling batch (already tracked as
  FINDINGS.md P1 item 9).
- Plan vs implementation:
  - **Commit `ccb000f`** -- `fix(heatmap): use UTC for scrobble
    timestamps and fetch window`. Brought `heatmap.py` in line with
    `lastfm.py:31`'s established UTC convention. Updated every UTS-
    building call site in `tests/test_heatmap.py` to `tzinfo=timezone.utc`
    so the boundary tests are not vacuous against tz bugs. Added a new
    adversarial test (`test_utc_decode_invariant_against_local_tz_drift`)
    that pins a UTS at 23:30 UTC and asserts the bucket lands on the UTC
    day, not the local-tz day.
  - **Commit `01a7904`** -- `fix(repositories): isolate nested
    daily_counts in get_job_context`. Explicit
    `dict(results["daily_counts"])` after the outer shallow copy.
    Chosen over `copy.deepcopy` for the polling hot path. Closes
    F-B18-8. New regression test in `test_repositories.py`.
  - **Commit `53919c2`** -- `fix(heatmap): keep streak alive when today
    has no scrobble yet`. Stepping back one day when today is zero
    matches GitHub-contributions/Duolingo convention and was the
    pattern Gemini suggested.
  - FINDINGS.md gained F-B19-6 (naive-tz vacuous-test anti-pattern,
    forward-TODO for AGENTS.md update) and a resolved entry for F-B18-8.
- Deviations: declined Gemini's three "narrow the bare
  `except Exception`" comments. Those are all instances of FINDINGS.md
  P1 item 9 (14 sites total); narrowing 3 of 14 piecemeal without a
  test matrix per error class is a regression risk that violates
  AGENTS.md scope discipline. Belongs in the dedicated error-handling
  batch the FINDINGS entry already calls for.
- Validation: `pytest -q` passes with **389 passed** and 3 existing
  aiohttp/Python 3.13 warnings (387 -> 389; +1 UTC adversarial test,
  +1 nested-copy regression test). `pre-commit run --all-files` passes
  all 10 hooks. `node --check static/js/heatmap.js` clean.
- Forward guidance: push the three fix commits + this log entry,
  reply to Gemini via `gh pr review` declining the broad-Exception
  comments with a FINDINGS-item-9 pointer, and wait for re-review.
