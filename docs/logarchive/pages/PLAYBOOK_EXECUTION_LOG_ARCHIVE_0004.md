<!-- DOCSYNC:ARCHIVE-PAGE v1 -->
# PLAYBOOK_EXECUTION_LOG_ARCHIVE -- page 0004

### 2026-07-31 - PR #165 Copilot review round 1 (side-task)

- Scope: triaged the five comments on PR #165 (four inline, one inside
  the suppressed low-confidence block). All five were valid; none were
  declined. Two themes: an overstated concurrency claim and three
  leftover copies of rules AGENTS.md now owns.
- Plan vs implementation:
  - `config.py`: the MAX_ACTIVE_JOBS rationale claimed a cap of 5 "keeps
    >=2 req/s per job". `_GlobalThrottle.next_wait()` (utils.py) advances
    a single next-allowed timestamp under one lock, serializing callers
    in arrival order with no per-job accounting, so a busy job can take
    more slots than an idle one. Reworded as an average, matching the
    "~10/N req/s" framing already used in AGENT_NOTES.md.
  - `scripts/testing/concurrent_users_test.py`: module docstring and
    `build_parser()` still said the default was 10 and told operators to
    set `--concurrency` above 10. Both now say 5. A repo-wide sweep found
    no other live stale reference; remaining "default 10" hits are all
    under `docs/history/` and stay as written (point-in-time records).
  - `AGENT_NOTES.md`: the Owner Preferences commit-mechanics bullet and
    the Venv "In short:" line each pointed at AGENTS.md and then restated
    its content anyway. Both reduced to pointers after verifying AGENTS.md
    genuinely carries every rule involved.
  - `HANDOFF_PROMPT.md`: Section 2 restated the full three-command gate
    and the root-BATCH warning, contradicting the Document Roles contract
    added by this same PR, which assigns gates to AGENTS.md. Collapsed to
    a pointer matching the wording Sections 3 and 4 already use.
- Deviations: none. No test changes -- all five edits are comment or
  documentation text with no behavior change.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all 10 hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: the suppressed-comment block again held a real
  finding (8/8 across PRs #163/#164/#165), so keep expanding it. Batch 21
  WP-1 remains the next action.

### 2026-07-31 - WP-1 token values pinned in the definition (side-task)

- Scope: make WP-1 executor-agnostic. The definition referenced "the
  audit token sheet" but only carried headline values; the full sheet
  lived in the Claude Design project and one agent's session notes,
  blocking a cold-start executor (e.g. a Codex session) from
  implementing WP-1 faithfully.
- Plan vs implementation: the WP-1 theme bullet now pins the complete
  sheet -- all eight colors (light bg/bg-2/ink/primary, dark
  bg/surface/text/primary), the three-family type system with sizes,
  the 4px spacing ladder, and the radius set. Values transcribed from
  "ScrobbleScope UI Audit v3" section "A starter palette and type
  system you can ship today" (2026-07-28 fetch).
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: WP-1 can now be executed by any agent from the
  definition alone; compiled CSS remains the WP-1 deliverable.

### 2026-07-31 - Owner-preferences commit-rule dedup (side-task)

- Scope: final SSOT sweep found AGENT_NOTES.md Owner Preferences still
  restating three commit-mechanics rules AGENTS.md now owns
  (incremental staging, no co-author trailers, push/pause discipline).
- Plan vs implementation: the four bullets collapsed into one pointer at
  AGENTS.md Commit Rules; preference-only items (concise responses,
  Docker/MCP pause, explain-why, Firefox testing, principles, testing
  pyramid) stay -- they are owner context, not rules.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: hygiene plan complete (6 commits); Batch 21 WP-1 is
  next. SSOT sweep contract now holds: commit-rule keywords, venv rules,
  the heatmap perf figure, and batch state each have exactly one owner.

### 2026-07-31 - SWE-principles audit charter (side-task)

- Scope: charter the owner-requested audit of the ten mandated software
  principles so a dedicated single-purpose session (Claude or Codex) can
  execute it cold, without this session's context.
- Plan vs implementation: new `docs/SWE_AUDIT_CHARTER.md` front-loads
  all judgment -- Python-only scope (JS/templates excluded until
  Batch 21 ships them), a do-not-re-report differential baseline
  (F-MAS-*, F-B20-2, prior 2026-02 audits, standing design decisions),
  pre-identified hotspots (the three ~110-150 line functions and the 17
  `except Exception` sites), a 10-principle x module grading matrix
  with per-cell evidence, and a strict output contract (a dated
  SWE_PRINCIPLES_AUDIT report under the history archive plus net-new
  F-SWE-N findings only; read-only, no code changes). Tracked as
  F-SWE-1.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: execution is decoupled -- run whenever convenient
  (Codex costs no Claude tokens). Batch 21 WP-1 is unblocked and next.

### 2026-07-31 - MAX_ACTIVE_JOBS default 10 -> 5 (side-task)

- Scope: owner decision. The 2026-03-04 load test ran 2/3/5 concurrent
  users clean while the 10-user run never completed; all jobs share the
  global 10 req/s API throttle, so 10 slots starve each job below
  1 req/s on the single small Fly.io machine.
- Plan vs implementation: `scrobblescope/config.py` default changed to
  `"5"` with a rationale comment (still env-overridable); README (three
  mentions), SESSION_CONTEXT key-runtime-facts line, and FINDINGS
  F-LOAD-1 phrasing updated to match. `fly.toml` sets no
  `MAX_ACTIVE_JOBS` override, so the new default takes effect on next
  deploy.
- Deviations: pre-change scouting claimed no test depends on the
  default (capacity tests inject their own semaphores) -- true for
  assertions but not for shared state. Route tests that mock
  start_job_thread acquire a real slot that is never released, and the
  session's accumulated leaks crossed the new cap of 5, failing
  `test_heatmap_loading_json_body` with a real 429. Fixed properly: a
  new autouse `fresh_job_slots` fixture in `tests/conftest.py` resets
  the semaphore per test, removing the hidden inter-test ordering
  coupling the lower cap exposed.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: owner can observe the 5-slot cap locally; the
  "N/5 slots in use" occupancy hint remains open as F-LOAD-1.

### 2026-07-31 - FINDINGS refresh: batch-closure pointers, F-DOCSYNC-4, F-SWE-1 (side-task)

- Scope: owner-flagged staleness in FINDINGS.md -- open P1 items that
  Batch 21's definition already promises to close carried no pointer,
  and F-B20-4 paraphrased the whole definition.
- Plan vs implementation:
  - F-B20-3: remedy rewritten -- the 5.1->5.3 CDN-consolidation path is
    dead; Batch 21 resolves the split by eliminating Bootstrap (closes
    at WP-8). F-AUDIT-1: closes at Batch 21 WP-2 via acceptance
    criterion 8. F-B18-12 deferred-block line marked as in-batch scope
    (WP-6). F-B20-4 compressed to a pointer at `BATCH21_DEFINITION.md`.
    F-FEATURE-2 line reformatted as a greppable cross-ref bullet.
  - New F-DOCSYNC-4 (resolved): per-batch logs were undiscoverable until
    the Section 2 Log column landed; records the tombstone disposition.
  - New F-SWE-1 (open P1): SWE-principles audit chartered via
    `docs/SWE_AUDIT_CHARTER.md` (next commit), executable cold by a
    dedicated Claude or Codex session; closes by pointing at the report.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: F-LOAD-1's "N/10" phrasing updates with the
  MAX_ACTIVE_JOBS default change (next commit); charter follows.

### 2026-07-31 - PLAYBOOK Section 2 log column; tombstone disposition (side-task)

- Scope: the 18 per-batch logs under `docs/history/logs/` were referenced
  from no working doc (Section 2 had no Log column), making batch history
  discoverable only via a directory glob.
- Plan vs implementation: Section 2 table gained a Log column linking
  `BATCH3_LOG.md` through `BATCH20_LOG.md` (batches 0-2 predate per-batch
  logging); a note under the table points close-out-entry seekers at the
  monolith archive per F-DOCSYNC-3. AGENTS.md Batch Close-Out step 3 now
  requires filling the Log column at close-out so the column cannot go
  stale. Investigated the two 300-byte `PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`
  files under `docs/history/` and `docs/history/logs/`: they are
  deliberate "Moved:" tombstones from the Batch 14 restructure kept for
  backward references -- retained, disposition recorded in F-DOCSYNC-4.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: hygiene commits 3-5 follow (FINDINGS refresh,
  MAX_ACTIVE_JOBS 5, SWE audit charter).

### 2026-07-31 - Bootstrap-doc SSOT pass: single-source rules and state (side-task)

- Scope: owner-requested hygiene sweep before Batch 21 WP-1. Exploration
  confirmed AGENTS.md and HANDOFF_PROMPT.md contradicted each other
  (bootstrap order, sufficiency gate, pre-commit gate, ownership map),
  commit discipline existed in 3-4 copies, the heatmap perf measurement
  in 4 copies, and AGENT_NOTES.md carried live batch state under a
  shipped-feature heading plus Batch 19 residue and a pointer to a
  non-repo file.
- Plan vs implementation:
  - AGENTS.md is now the single owner of rules: canonical 7-step
    bootstrap order (AGENTS.md itself is step 1), the stricter 3-way
    sufficiency gate, a 6-step pre-commit procedure including the
    doc_state_sync --check gate, the conflict-resolution rule, and four
    new anti-patterns (never --no-verify; stale Section 3; missing log
    entries; stale dashboard figures -- the ~72% coverage figure
    survived five months while reality was 89%). Docstring mandate moved
    into Proposal and Design Rules.
  - HANDOFF_PROMPT.md reduced to what it uniquely owns: post-read
    verification (git status/log + pytest count reconciliation) and the
    end-of-session handoff checklist; all rule sections now link to
    AGENTS.md instead of restating.
  - AGENT_NOTES.md: batch state moved out (PLAYBOOK Section 3 declared
    the single source); Heatmap section retitled shipped and trimmed of
    Batch 19 residue; venv rules and runtime constants replaced with
    links to their owners; load-test pointer now inlines the conclusion
    (2/3/5 clean, 10 never completed) and flags the raw data as
    agent-side; Talisman note repointed to the archived Batch 17 log;
    orchestrator-split note repointed to F-B20-2; the ten software
    principles expanded from bare acronyms.
  - SESSION_CONTEXT: Section 3 now lists all 7 CSS / 7 JS files and the
    template set (Batch 21 touches exactly these); heatmap perf trimmed
    to an F-B18-11 pointer here and in PLAYBOOK Section 3 -- F-B18-11 is
    the only full copy of the measurement.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: commits 2-5 of the approved hygiene plan follow
  (PLAYBOOK log column, FINDINGS refresh, MAX_ACTIVE_JOBS 5, SWE audit
  charter); then Batch 21 WP-1.

### 2026-07-29 - PR #164 phantom cleanup + review response (side-task)

- Scope: PR #163 was rebase-merged, leaving `wip/batch-21` "8 ahead /
  8 behind" (identical content, different SHAs -- normal rebase-merge
  artifact). The owner opened PR #164 from the stale branch; Copilot
  re-reviewed the phantom diff and left three NEW valid comments that
  four prior rounds missed. PR #164 closed with explanation; branch
  force-pushed to match `main`; all three fixes applied here.
- Plan vs implementation:
  - WP-4: leaving the loading page is now a plain "Back home" link with
    no `/reset_progress` call -- the endpoint clears stored job state
    only (`routes.py:227-238`); the daemon worker keeps its slot and
    rewrites the job afterward, so a "Cancel" label would be misleading
    and the reset racy.
  - WP-1: digest verification extended to cached artifacts (verify on
    every use, refetch once on mismatch, fail closed) -- gitignored
    `scripts/bin/` persists between runs, so download-time-only checks
    leave a bypass.
  - AGENTS.md: rotation note qualified -- bottom-appended entries are
    archived on the next `--fix` only once the non-current window is at
    capacity; placement rule unchanged.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: WP-1 next on the realigned branch; open a fresh PR
  for the next review cycle when WP work lands.

### 2026-07-29 - PR #163 review response, round 4 (side-task)

- Scope: Copilot round 4 -- one suppressed comment. Verified valid and
  acted on.
- Plan vs implementation: the archived coverage-refresh entry cited
  "the CLAUDE.md canonical command", but CLAUDE.md is gitignored
  (`.gitignore:49`) and repo-invisible; the command is documented at
  README.md "Running Tests". Reference corrected in the monolith
  archive entry.
- Deviations: none. Distinction from the PR #162 round-3 decline on
  editing rotated entries: that citation was accurate at write time and
  went stale (point-in-time record, left alone); this one was
  repo-invisible at write time -- a sourcing error that defeats the
  record's verifiability, so it is corrected rather than preserved.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: review rounds have reached citation polish;
  recommend merging or pausing auto-review re-requests. WP-1 next.

### 2026-07-28 - PR #163 review response, round 3 (side-task)

- Scope: Copilot round 3 -- three suppressed low-confidence comments.
  Two acted on, one deferred to FINDINGS with a decline on the PR.
- Plan vs implementation:
  - Acted: `global.css` joins the WP-2 legacy per-page stack -- verified
    it carries Bootstrap-coupled `.card`/`.card-body`/`.modal-*` rules
    (`global.css:141-199`) that would restyle daisyUI components if it
    stayed in `base.html`; token/wordmark/shell concerns redistributed
    (daisyUI themes + `shell.css`).
  - Acted: WP-8 drift hook diff scoped with a pathspec
    (`git diff --exit-code -- static/css/tailwind.css`) so unrelated
    dirty files or rewrites from earlier hooks in the same run cannot
    produce false drift failures.
  - Deferred: retagging the Batch 20 close-out entry in the monolith
    archive. The routing claim is correct, but it is consistent tool
    behavior (`(Batch N close-out)` is not parser-recognized;
    BATCH19_LOG.md lacks its close-out too), and hand-editing
    machine-rotated archive content in a docs PR was declined and
    accepted in PR #162 round 3. Logged as F-DOCSYNC-3 (open P2) for a
    docsync WP alongside F-DOCSYNC-1/2.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: WP-1 remains next; batched reply posted on PR #163.

### 2026-07-28 - PR #163 review response, round 2 (side-task)

- Scope: Copilot round 2 -- no new top-level comments, four suppressed
  low-confidence comments. All four verified valid (same pattern as
  PR #162: the suppression filter is too conservative); all acted on.
- Plan vs implementation:
  - Stale bootstrap docs: AGENT_NOTES.md still called Batch 21 a TBD
    stub with "no WP work until scope lands"; FINDINGS.md header said
    scope pending; README roadmap listed scoping as open. All three now
    reflect the active batch (the definition's own Status line already
    carried Active from WP-0).
  - Compiled-CSS drift window: validation gate now requires any WP
    touching templates or `tailwind.src.css` (WP-2..WP-7) to rebuild
    and commit `tailwind.css` in the same commit; the drift hook
    deliberately stays in WP-8 (moving it to WP-1 would front-load the
    headless-CI fetch problem before any template exists to protect).
  - Stack-restriction conflict: `toast` + `alert` added to the
    permitted daisyUI set for the WP-5 toast rewrite.
  - `--bars-color` inventory corrected: six of seven page CSS files
    (`unmatched.css` hardcodes its own `--header-bg`), pinwheel via
    `var()`; the wordmark hardcodes `#6a4baf` and only the dark-mode
    override (`global.css:49-50`) uses the variable, so light-mode
    wordmark recoloring is explicit migration work.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: WP-1 remains next; batched reply posted on PR #163.

### 2026-07-28 - PR #163 review response (side-task)

- Scope: address the Copilot auto-review on PR #163 (Batch 21 open +
  doc refreshes). Five inline comments, all on `BATCH21_DEFINITION.md`;
  all five verified valid against the code and acted on.
- Plan vs implementation:
  - WP-1: per-platform SHA-256 digests committed alongside pinned
    versions; `tailwind_build.py` must verify every downloaded artifact
    before executing it (pin-only trusts the release asset at fetch
    time, and the WP-8 CI hook executes that binary headless).
  - WP-1: daisyUI standalone needs both `daisyui.mjs` and
    `daisyui-theme.mjs`; the component bundle alone cannot register the
    two custom `@plugin` themes.
  - WP-2: explicit coexistence isolation -- one framework stylesheet
    per template via the per-page block, shared shell styled by a
    framework-neutral `shell.css` absorbed at WP-8. Rejected daisyUI
    prefix alternative (WP-8 removal churn) with reasoning recorded.
  - WP-5: dropped "CSV walker untouched" -- `results.js` exports
    rendered cell text, so `MMM YY` display dates would truncate CSV
    release dates; date cells keep ISO in `data-export`, walker
    prefers it.
  - WP-7 + acceptance criterion 6: `below_min_plays`/`below_min_tracks`
    removed from the reason-code set -- `fetch_top_albums_async` drops
    threshold failures before the pipeline (`orchestrator.py:112-116`),
    and near-miss retention is explicitly Batch 22+. Two reason cards,
    not three; out-of-scope entry cross-references the deferred codes.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: WP-1 implementation must honor the amended digest
  and dual-plugin-file requirements; batched reply posted on PR #163.

### 2026-07-28 - Side-task entry placement rule in AGENTS.md (side-task)

- Scope: document the doc_state_sync rotation gotcha discovered during
  the coverage-figure refresh so any agent places side-task entries
  correctly on the first try.
- Plan vs implementation: AGENTS.md Side-Task Handling step 2 now
  states that new entries must be inserted directly after the
  CURRENT-BATCH-END marker (top of the non-current list). The list is
  ordered newest-first; rotation keeps the first `--keep-non-current`
  entries positionally and rotates the rest, so a bottom-appended entry
  is treated as oldest and archived by the next `--fix` run instead of
  staying in the active window.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: next work remains Batch 21 WP-1 (Tailwind + daisyUI
  toolchain).

### 2026-07-28 - Coverage figure refresh in SESSION_CONTEXT (side-task)

- Scope: replace the stale coverage figure in SESSION_CONTEXT Section 1.
  The row still carried ~72% from the 2026-02-20 audit run; coverage has
  not been re-measured in a canonical doc since.
- Plan vs implementation: ran the canonical coverage command documented
  in README.md "Running Tests"
  (`pytest --cov=scrobblescope --cov-report=term`) on `wip/batch-21`
  (equal to `main` + WP-0, which touched no Python). Result: 89% total
  (1260 stmts, 134 miss). Lowest modules: `lastfm.py` 77%, `utils.py`
  81%, `orchestrator.py` 85%; four modules at 100%. Updated the
  Section 1 Coverage row with the new figure, measurement date, and
  scope (`--cov=scrobblescope`).
- Deviations: none. The owner's `main` checkout keeps the old figure
  until this branch merges; no fix applied there by design.
- Addendum (same day, owner-requested): the README tech-stack Testing
  row also said ~72%; updated to 89% in a follow-up commit.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: next work remains Batch 21 WP-1 (Tailwind + daisyUI
  toolchain). Re-measure coverage at future batch close-outs so the
  Section 1 row does not go stale again.

### 2026-07-24 - Batch 20 complete; definition archived, log purged (Batch 20 close-out)

- Scope: Batch 20 WP-8 close-out per the AGENTS.md procedure.
- Plan vs implementation:
  - `doc_state_sync.py --fix --keep-non-current 0` purged the 4 rotated
    non-current side-task entries into the monolith archive.
  - `git mv BATCH20_DEFINITION.md docs/history/definitions/` and marked
    the archived definition header Complete.
  - PLAYBOOK Section 2: Batch 20 row now links to the archived
    definition. Section 3: Batch 20 marked complete; Batch 21 (UI
    overhaul) flagged as next, awaiting the owner's in-progress UI
    proposal.
  - `.claude/SESSION_CONTEXT.md` Section 1: Batch 20 row set to
    Complete (all 9 WPs); Batch 21 row set to next-batch status. The
    "22 test modules" wording was already correct from earlier WPs.
- Deviations: none. Batch ran WP-0..WP-5 via Copilot PRs (#153/#155/
  #156/#159), then a post-merge audit follow-up commit plus WP-6, WP-7,
  and this close-out on `wip/batch-20` in a worktree.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0 with only the
  expected `BATCH21_DEFINITION.md` root warning remaining.
- Forward guidance: next batch is Batch 21 (UI overhaul); expand
  `BATCH21_DEFINITION.md` into WPs once the owner's proposal lands.
  `wip/batch-20` holds four unpushed commits awaiting owner review and
  push/PR instruction.

### 2026-07-24 - PR #162 review response (side-task)

- Scope: address the Copilot review on PR #162 (Batch 20 completion).
  All six comments (four inline + two suppressed low-confidence) were
  valid doc-consistency catches; five acted on fully, one partially.
- Plan vs implementation:
  - `FINDINGS.md`: header status updated to Batch 20 complete / Batch 21
    next; `Source:` added to F-B20-4 and F-B18-11; `Status:` lines added
    to all P2, Info, and feature items; shipped F-FEATURE-2 rotated to
    the archive with a cross-reference note.
  - `AGENTS.md` Finding-Writing Rules: rotation rule clarified --
    standing design-decision Info items (F-LOAD-3..5) keep their F-IDs
    in the active file and rotate only when superseded. This is the
    partial decline: archiving them would contradict the Batch 20
    definition's WP-6 intent.
  - `docs/history/findings/FINDINGS_ARCHIVE.md`: header claim narrowed
    to ID/history preservation (bodies may be condensed at rotation).
  - `PLAYBOOK.md` Section 3: "unpushed pending owner instruction"
    replaced with "submitted as PR #162" (the Section 4 close-out entry
    keeps the original wording as a point-in-time record).
  - `AGENT_NOTES.md`: stale "Batch 20 is now active" block updated to
    complete/archived status with Batch 21 next.
  - `BATCH21_DEFINITION.md`: baseline refreshed 389 -> 390.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: batched reply posted on PR #162; awaiting merge.
  Batch 21 scope expansion remains next once the owner's UI proposal
  lands.

### 2026-07-24 - PR #162 review response, round 2 (side-task)

- Scope: address Copilot's second review round on PR #162 (four inline
  comments + one suppressed). All five verified valid; all acted on.
- Plan vs implementation:
  - `FINDINGS.md` F-MAS-4: `except Exception` count updated 14 -> 17
    (verified by grep; Copilot's per-file breakdown was exact) with the
    recount date noted.
  - `FINDINGS.md` deferred-block pointer corrected: detailed bodies live
    in pre-Batch-20 FINDINGS.md via git history (before `494f2c7`), not
    under `docs/history/` as previously claimed.
  - `FINDINGS.md` F-FEATURE-2 cross-reference recast as a direct
    sentence (grammar).
  - `docs/history/findings/FINDINGS_ARCHIVE.md`: F-FEATURE-2 heading
    suffix normalized to `-- RESOLVED (shipped in Batches 18/19)` per
    the AGENTS.md suffix rule.
  - Archived `BATCH20_DEFINITION.md` header relabeled `Baseline:` ->
    `Final count:` so it no longer conflicts with the definition's
    unchanged 389-baseline plan text.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: PR #162 ready for merge; Batch 21 definition draft
  sits uncommitted in the worktree awaiting owner approval.
