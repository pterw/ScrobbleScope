# BATCH20: File-hygiene + docs methodology refresh

**Status:** Definition awaiting owner audit. Plan reference: `C:\Users\peter\.claude\plans\wondrous-moseying-glacier.md`.
**Branch:** `file-hygeine` (off `main` after committing `.gitignore` exclusion of `CLAUDE.md` and pushing).
**Baseline:** 389 tests passing (post PR #152 merge to main; no code changes in this batch should move the count).

---

## Context

Three repo-root markdown files have drifted from current reality:

- `README.md` -- stale "24 test files" claim (actual: 22 pytest modules), missing five tracked root-level `.md` files in the Project Structure block, roadmap full of long-completed scaffolding ticks, heatmap listed three times, a strikethrough+immediate-tick artifact, an agent-orchestration bullet in the Key Implementation Highlights section that does not belong there, and a Mermaid diagram that pre-dates the heatmap pipeline.
- `DEVELOPMENT.md` -- three wrong archive-path references (`docs/history/BATCHN_DEFINITION.md` instead of `docs/history/definitions/BATCHN_DEFINITION.md`), an unrefined "7-10 days of active development" framing, no mention of the two project-scoped Claude Code skills, and several patches of AI-prose padding.
- `FINDINGS.md` -- no rotation policy; resolved items accumulate (418 lines, ~70-75% no-action). Inconsistent finding-ID conventions across the file. Not referenced in `AGENTS.md` / `HANDOFF_PROMPT.md` bootstrap order.

This batch settles all three files, adds a finding-writing standard to `AGENTS.md`, adds a read-on-demand FINDINGS pointer to `AGENTS.md` + `HANDOFF_PROMPT.md`, creates `docs/history/findings/FINDINGS_ARCHIVE.md`, and updates the `scrobblescope-bootstrap` Claude Code skill to surface FINDINGS on relevant cues. UI overhaul (previously slotted as Batch 20) renumbered to Batch 21 because that placeholder had no started WPs.

No production code changes. Pytest baseline must remain 389 across every WP.

---

## Acceptance criteria

**Per-WP (must hold for every commit):**

```
pytest -q                                # 389 passed
pre-commit run --all-files               # all 10 hooks pass
python scripts/doc_state_sync.py --check # exit 0 (Root BATCH file warning expected while batch active)
```

**Batch-level:**

1. `README.md` -- test count correct; Project Structure includes `AGENT_NOTES.md`, `HANDOFF_PROMPT.md`, `FINDINGS.md`, `DEVELOPMENT.md`, `DEPLOY.md`; roadmap shrunk to ~25-30 lines of signal; Mermaid diagram shows both album and heatmap pipelines; "Doc-State Sync Tooling" bullet removed from Key Implementation Highlights; "Getting Started" compressed without losing any subsection and without pointing readers to AGENT_NOTES.md.
2. `DEVELOPMENT.md` -- all three wrong archive-path references fixed; timeline rephrased honestly without abandoning the rapid-dev signal; new "Claude Code Skills" subsection in place; AI-prose tightenings applied.
3. `FINDINGS.md` -- under 200 lines; resolved items rotated to `docs/history/findings/FINDINGS_ARCHIVE.md`; deferred Batch 18 findings consolidated; all remaining items use `F-<context>-<N>:` headings; header note describes the rotation policy.
4. `AGENTS.md` -- new "Finding-writing rules" section; one-line read-on-demand FINDINGS pointer in "Session Bootstrap".
5. `HANDOFF_PROMPT.md` -- one-line read-on-demand FINDINGS pointer added to Section 1.
6. `scrobblescope-bootstrap` Claude Code skill -- "When to invoke" updated to include finding-related cues.
7. `.claude/SESSION_CONTEXT.md` -- Section 1 reads "22 test modules"; Batch 20 close-out row present; STATUS block regenerated.
8. New `docs/history/findings/FINDINGS_ARCHIVE.md` exists and is committed.

---

## Work Packages

### WP-0 -- Batch scaffolding (one commit, before audit commits)

- `git mv BATCH20_DEFINITION.md BATCH21_DEFINITION.md` (already done in the scaffolding turn -- staged but not committed pending owner audit of this file).
- Update renamed file header to BATCH21 (already done; awaiting batch-open commit).
- Write the new `BATCH20_DEFINITION.md` (this file).
- PLAYBOOK Section 2: add Batch 20 row (with batch link). PLAYBOOK Section 3: active batch = Batch 20, next WP = WP-1. PLAYBOOK Section 4: kickoff entry inside CURRENT-BATCH markers tagged `(Batch 20 WP-0)`.
- `python scripts/doc_state_sync.py --fix`.
- Stage `BATCH20_DEFINITION.md`, `BATCH21_DEFINITION.md`, `PLAYBOOK.md`, `.claude/SESSION_CONTEXT.md`.
- Commit: `chore(batch): open Batch 20 (file-hygiene); renumber UI overhaul to Batch 21`

### WP-1 -- README: counts, structure, mermaid

`docs(readme): correct test file count, refresh project structure, refresh mermaid diagram`

- `README.md` lines 5, 111, 517: "24 test files" -> "22 test modules" (or equivalent phrasing).
- Project Structure tree: add rows for `AGENT_NOTES.md`, `HANDOFF_PROMPT.md`, `FINDINGS.md`, `DEVELOPMENT.md`, `DEPLOY.md` under a small "agent orchestration / docs" sub-cluster comment. `CLAUDE.md` and `MEMORY.md` are gitignored -- stay off the tree. `BATCH20_DEFINITION.md` is transient -- mention in prose, not as a tree row.
- Replace the Mermaid diagram with the two-pipeline version that includes `heatmap.py` and the second polling endpoint. Confirm `routes.py` imports support the edge set (`orchestrator.background_task`, `heatmap.heatmap_task`).
- Delete the "Doc-State Sync Tooling" bullet from Key Implementation Highlights (DEVELOPMENT.md already covers it in detail; the README's "Development Methodology" section links to DEVELOPMENT.md).

### WP-2 -- README: roadmap trim

`docs(readme): trim and tighten roadmap`

Delete (long-completed scaffolding ticks, signal is elsewhere in the README):

- Persistent metadata layer (Postgres) bullet.
- All "modularize" bullets (5).
- DB wake-up retry/backoff hardening.
- Thread-safe in-memory request cache.
- CSS variable consolidation.
- orchestrator.py decomposition into named helpers (misleading given current 916-line state; covered as a new forward item in WP-6).
- Theme CSS/JS consolidation.
- Backend SoC lastfm.py purity.
- Route helper extraction.
- Global rate throttle / playtime album cap / bounded job concurrency (already implied by other items).
- The three doc-tooling ticks at lines 518-520 (modular docsync, parser hardening, AGENTS consolidation).
- `[x] Scrobble heatmap` from "Confirmed upcoming features" (it's done; described twice already above).
- Strikethrough+immediate-tick artifact at lines 483-484.
- Line 480 (`Conduct thorough QA testing ...`).

Convert (no longer checkboxes, but kept as reminders):

- Lines 529-534 "Ongoing code quality track" -> single italicized "Things to keep in mind" paragraph at the end of the roadmap section.

Add (concrete, measurable):

- `[ ] Decompose scrobblescope/orchestrator.py (916 lines) into pipeline / processing / result-shaping modules.`
- `[ ] Add at least one integration test that exercises /results_loading -> /progress -> /results_complete against the in-process Flask client.`
- `[ ] Consolidate Bootstrap CDN sources (cdnjs vs jsdelivr) to a single provider across all templates.`
- `[ ] Tighten ENTRY_BATCH_RE in scripts/docsync/parser.py to prevent misrouting of entries whose titles contain "Batch N" substrings.`
- `[ ] UI overhaul (Batch 21 candidate -- scope from owner audit PDF).`

Keep existing unchecked items: improved unmatched page, top songs feature, top header logo replacement.

### WP-3 -- README: getting started compression

`docs(readme): compress getting-started, drop powershell footgun line`

- Tighten the venv-creation block (lines 211-219). Drop the `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned` line (footgun warning that does not belong in primary setup).
- `.env` example block: shrink the trailing "Optional tuning" commented-out list (8 lines) to 2-3 representative examples + a one-line pointer to `scrobblescope/config.py` for the full set.
- "Local Development with DB Cache" subsection (lines 278-320): keep all four sub-sections (Prerequisites, One-command startup, Smoke test, Concurrent users test) but tighten prose; drop the `load_dotenv() ... automatically` trivia line. Do NOT link out to `AGENT_NOTES.md` -- the README must stand alone for setup.

Target: Getting Started shrinks from ~130 lines to ~95-100.

### WP-4 -- DEVELOPMENT.md: paths, timeline, prose

`docs(development): fix archive paths, refine timeline framing, trim ai-prose`

- Replace `docs/history/BATCHN_DEFINITION.md` with `docs/history/definitions/BATCHN_DEFINITION.md` on lines 92, 200, 277.
- Rephrase line 14 "7-10 days of active development" to honestly acknowledge the Feb-March sprint (prototype -> Fly.io deploy) + lighter tapering work across subsequent months. Preserve the rapid-dev signal -- that is the section's whole point. Suggested target wording: "The bulk of the work was compressed into roughly 10-17 days of active development across a Feb-March sprint, with lighter follow-up work in subsequent months."
- Tighten the four AI-prose patches: line 21-30 framing redundancy; line 213 "Two patterns emerged" meta-prose; line 269 "after a dedicated batch definition was written" trailing clause; the "In practice ..." / "The short answer ... The long answer follows" qualifier phrases.

### WP-5 -- DEVELOPMENT.md: skills subsection

`docs(development): add claude-code skills subsection`

New ~30-line subsection titled **"Claude Code Skills (tightly scoped tooling)"** placed after the `doc_state_sync.py` section:

1. One-paragraph note that the skills are CC-specific; the portable form lives in `AGENTS.md`.
2. `scrobblescope-bootstrap` -- what it does, canonical read order, when to invoke vs when to skip (use the "tweak the heatmap pill padding" anti-example from the skill itself).
3. `gemini-pr-triage` -- what problem it solves; how it classifies Act/Defer/Decline; where the standard lives.
4. Closing line acknowledging the deliberate single-agent scope.

Also update the line-39 paragraph ("Five tracked files and two archive directories") to acknowledge FINDINGS.md as a sixth, advisory, read-on-demand file.

### WP-6 -- FINDINGS.md: cleanup and archive

`docs(findings): one-time cleanup; archive resolved items`

- Create `docs/history/findings/FINDINGS_ARCHIVE.md` with a one-paragraph header explaining its purpose (resolved items rotated here at batch close-out; kept for grep history).
- Move to archive:
  - "Resolved since last update (2026-03-02)" entire block.
  - F-B18-8 (RESOLVED).
  - F-B19-1, F-B19-2 (both RESOLVED in Batch 19 follow-up).
  - F-B19-5 (visual-verification tooling, no action); update `BATCH21_DEFINITION.md` to point this item's source reference to `docs/history/findings/FINDINGS_ARCHIVE.md`.
  - F-B19-6 archive portion (the code-fix; keep the AGENTS.md anti-pattern-addition follow-up as an open P1 line in FINDINGS).
- Consolidate the deferred Batch 18 findings (F-B18-1, F-B18-3, F-B18-4, F-B18-5, F-B18-7, F-B18-10) into a short "Deferred / future-batch candidates" block near the bottom of `FINDINGS.md` -- one-line cross-reference summaries each.
- Promote `F-B18-1` to a fully scoped P1 item ("orchestrator.py decomposition") -- this is the same item now also in the README roadmap.
- Standardize remaining items to `F-<context>-<N>:` headings:
  - P1 items currently bare-numbered (2, 3, 4, 5, 6, 7, 8, 9) get IDs derived from their source audit (`F-LOAD-N`, `F-MAS-N` for MULTI_AGENT_SWEEP, `F-DOCSYNC-N` for DOCSYNC_AUDIT, `F-AUDIT-N` for AUDIT_2026-02-11).
  - P2 items (10-13) same treatment.
  - Info items (14-17) same.
  - Feature prep notes (18-19) keep prose-style, no F-ID needed.
- Header note at the top of FINDINGS.md describing the rotation policy + archive link.
- Add forward-FINDINGS entries:
  - `F-B20-1: README/SESSION_CONTEXT test-file count drift -- resolved in Batch 20.` (For audit completeness; archive immediately.)
  - `F-B20-2: orchestrator.py second-pass decomposition` (open P1; promoted from F-B18-1).
  - `F-B20-3: Bootstrap CDN source consolidation` (open P1; concrete companion to README roadmap item).
  - `F-B20-4: UI overhaul (driven by owner's audit PDF)` (open P1; Batch 21 main + possible Batch 22 contingency).

Target: `wc -l FINDINGS.md` reads 150-180.

### WP-7 -- AGENTS + HANDOFF_PROMPT + skill

`docs(agents,handoff): document FINDINGS on-demand rule + finding-writing standard`

- `AGENTS.md` "Session Bootstrap (in order)" section: add a callout step (or sub-bullet under step 2 or 3) -- "Read `FINDINGS.md` only when PLAYBOOK Section 4 or your task explicitly references an F-* finding ID or a P0/P1 item."
- `AGENTS.md` new short section after "Anti-Pattern Registry" titled **"Finding-writing rules"** defining:
  - F-ID format `F-<context>-<N>:` (context examples: B18, B19, B20 batches; MAS, DOCSYNC, AUDIT, LOAD source audits).
  - Required fields: heading with F-ID, one-sentence problem, `Status:` line, `Source:` line (when applicable).
  - No bare-numbered items in FINDINGS.md.
  - Resolved items rotate to `docs/history/findings/FINDINGS_ARCHIVE.md` at batch close-out.
- `HANDOFF_PROMPT.md` Section 1: add the same one-line read-on-demand pointer for symmetry.
- `~/.claude/skills/scrobblescope-bootstrap/SKILL.md` (project-scoped skill): update "When to invoke" to include cues like "finding", "F-B18-*", "F-B19-*", "P1 item", "what's pending audit-wise".

### WP-8 -- Close-out

`chore(close-out): Batch 20 complete; archive definition and purge log`

- `.claude/SESSION_CONTEXT.md` Section 1: literal "24 test files" -> "22 test modules" (last literal touch; the STATUS block has been regenerated per-WP throughout).
- `python scripts/doc_state_sync.py --fix --keep-non-current 0` (purge old non-current rotated entries from PLAYBOOK Section 4).
- `git mv BATCH20_DEFINITION.md docs/history/definitions/BATCH20_DEFINITION.md`.
- PLAYBOOK Section 2: add Batch 20 row linking to archived definition.
- PLAYBOOK Section 3: mark Batch 20 complete; flag Batch 21 (UI overhaul) as next batch awaiting owner scope from the audit PDF.
- `.claude/SESSION_CONTEXT.md` Section 1: add row "Batch 20 status | **Complete**. All 8 WPs done. Definition: docs/history/definitions/BATCH20_DEFINITION.md."
- Verify `python scripts/doc_state_sync.py --check` exits 0 with no Root BATCH file warnings.

---

## Validation gate (every WP)

```
pytest -q
pre-commit run --all-files
python scripts/doc_state_sync.py --check
```

Plus a per-WP doc-state sync after PLAYBOOK Section 4 edits:

```
python scripts/doc_state_sync.py --fix
```

---

## Out of scope

- Any production-code changes (`scrobblescope/**.py`, `templates/`, `static/`). If a doc-update reveals a real bug, log a forward-FINDING; do not fix in this batch.
- The UI overhaul itself (Batch 21).
- Any new Python or JS dependencies.
- Scriptified FINDINGS rotation (Option C in the plan) -- deferred indefinitely as over-engineering for the change frequency.
