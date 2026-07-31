# PLAYBOOK Execution Log Archive

Purpose:
- Store dated execution-log entries rotated out of `PLAYBOOK.md` section 10.
- Keep entries in reverse-chronological order (newest first).

Read helpers:
- `Get-Content docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`
- `rg -n "^### 20" docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`
- `rg -n "<keyword>" docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`

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

### 2026-07-24 - PR #162 review response, round 3 (side-task)

- Scope: Copilot round 3 (two comments + one suppressed duplicate).
  One acted on, one declined.
- Plan vs implementation:
  - Acted: both F-B19-6 archive headings moved their portion qualifier
    after the colon to match the `F-<context>-<N>: <title>` format the
    batch itself established (AGENTS.md Finding-Writing Rules).
  - Declined: updating the `BATCH20_DEFINITION.md:107-108` citation
    inside the archived `docs/history/logs/BATCH20_LOG.md` WP-3 entry.
    Rotated log entries are point-in-time records (same principle as
    the round-1 "unpushed" decline, which the reviewer accepted), they
    are machine-rotated content the docsync tooling owns, and the
    filename remains uniquely greppable at its archived location.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: review rounds are now in pure-style territory;
  recommend merging PR #162.

### 2026-07-24 - PR #162 review response, round 4 (side-task)

- Scope: Copilot round 4 -- one comment on PLAYBOOK Section 3 batch-state
  wording. Acted on, with a corrected mechanism note.
- Plan vs implementation:
  - Section 3 now uses the parser-recognized marker "Batch 21 is not yet
    defined"; the Section 3 parse verifiably returns the between-batches
    state with that wording in place.
  - Verified the comment's mechanism was doubly off: `BATCH_NEXT_RE`
    does not match "Batch 21 is next" (the attribution came from the
    `last_completed + 1` fallback at `parser.py:198-199`), and the
    wording fix alone cannot change the rendered STATUS -- with the
    close-out entry still inside the CURRENT-BATCH markers,
    `renderer.py:85-86` applies its own `last_completed + 1` fallback.
    Batch 19 precedent shows this is transient: its identically-tagged
    close-out entry rotated out automatically when Batch 20 WP-0 landed,
    and the same will happen at Batch 21 WP-0.
  - Logged the renderer gap as F-DOCSYNC-2 (open P2) rather than
    hand-moving machine-managed marker content or patching docsync code
    inside a docs-only PR.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: owner is merging PR #162; Batch 21 opens next.

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

### 2026-05-16 - Remove dependabot.yml (side-task)

- Removed `.github/dependabot.yml`: all packages are pinned with `==` so
  dependabot can only open PRs that break the pinning policy. Pure noise for
  this project. No functional change.
- **385 tests passing**, all hooks green.

### 2026-05-16 - README update: heatmap feature + stale data

- Added heatmap feature description to intro paragraph (was album-only).
- Added Scrobble Heatmap bullet to Features section (grid, palette, tooltips,
  dark mode, responsive, pinwheel spinner).
- Updated project structure: heatmap.py, heatmap.css, heatmap.js,
  scrobblescope_pinwheel.svg, test_heatmap.py all added; stale test counts
  corrected (test_repositories.py 18->19, test_routes.py 50->65).
- Updated tech stack table: test count 350/23 -> 385/24; APIs note that
  heatmap uses Last.fm only (no Spotify).
- Roadmap: checked off heatmap (Batch 18 Phase 1 complete, Phase 2 in progress);
  corrected "350 tests / 23 files" to "385 / 24".
- Test badge: 350 -> 385.

### 2026-03-05 - Post-Batch-17 doc staleness fix

- PLAYBOOK Section 3 still said "Batch 17 is active" and listed all WP
  statuses after the close-out commit (743f8ae). Updated to "Between batches"
  with heatmap feature noted as next action on branch `feat/heatmap`.
- SESSION_CONTEXT Section 1 branch updated from `wip/batch-17` to
  `feat/heatmap`; date bumped to 2026-03-05.
- STATUS block refreshed by `doc_state_sync --fix`.
- Batch 17 log entries remain inside CURRENT-BATCH markers per docsync
  design -- they will auto-rotate to `BATCH17_LOG.md` when the next batch
  is declared active in Section 3.
- **350 tests passing**, all hooks green.

### 2026-03-05 - side-task: PR review fixes (CI cache, DEVELOPMENT.md, README, doc tidiness, SDLC table)

- **`.github/workflows/test.yml`**: fixed `cache-dependency-path` from
  `requirements-dev.txt` to `requirements*.txt`. The dev file starts with
  `-r requirements.txt` but pip's cache key computation does not follow
  transitive includes; changes to `requirements.txt` alone would not
  invalidate the cache. Fix ensures both files are hashed for the key.
- **`DEVELOPMENT.md`**: corrected the SESSION_CONTEXT.md CI presence
  claim. Previous text said the file is "absent in GitHub Actions" --
  inaccurate since SESSION_CONTEXT.md is now committed and a standard
  `actions/checkout@v4` includes it. Updated to say "normally present;
  `_read_lines_optional()` is a fallback for edge cases (sparse checkout
  or custom workflow)."
- **`README.md`**: three stale items corrected from Batch 17 changes:
  (1) CI/CD table row updated -- standalone flake8 removed in WP-2; pip-audit
  added in WP-2; description now reads "Quality Gate (pre-commit, pytest +
  coverage gate, pip-audit)"; (2) Code Quality row: added
  check-merge-conflict and detect-private-key (added in WP-2 addendum);
  (3) Local Dev section: SESSION_CONTEXT.md Section 8 ref (broken after
  WP-4 renumbering + Docker setup moved to AGENT_NOTES.md) -> AGENT_NOTES.md.
- **`BATCH17_DEFINITION.md`**: removed duplicate `---` separator between
  "## 6. Deferred" and "## Supplementary Info" (double rule was redundant).
- **`PLAYBOOK.md` WP-4 note**: updated "Candidate for a future cleanup
  pass" -> "Subsequently fixed in a side-task (see logarchive)" so PR
  reviewers do not see the WP-4 note as an open item that is also fixed
  in the same PR diff.
- **`DEVELOPMENT.md` SDLC table**: CI gate row updated from stale
  "GitHub Actions: pre-commit + flake8 + pytest + coverage" to "Quality
  Gate (pre-commit, pytest + coverage gate, pip-audit)" to match the
  README change and the WP-2 workflow rename.
- **350 tests passing**, all hooks green.

### 2026-03-05 - side-task: doc accuracy fixes (AGENTS.md, HANDOFF_PROMPT.md)

- **AGENTS.md**: "these doc files" -> "the doc files listed below" (dangling pronoun
  with no referent; table follows the section break, not the sentence).
- **HANDOFF_PROMPT.md**: SESSION_CONTEXT step 4 now reads "Sections 3-5" instead of
  "Sections 3-4". Section 5 is the dedicated Architecture overview; "Sections 3-4"
  would have left agents one section short when looking for architecture detail.
- **350 tests passing**, all hooks green.

### 2026-03-04 - side-task: requirements pinning + venv/agent safety rules

- **Pin previously unpinned packages**: `asyncpg>=0.29.0` -> `==0.31.0` and
  `Flask-WTF>=1.2.0` -> `==1.2.2` in `requirements.txt`. All five packages in
  `requirements-dev.txt` pinned to exact installed versions (flake8==7.3.0,
  pre-commit==4.5.1, pytest==9.0.2, pytest-asyncio==1.3.0, pytest-cov==7.0.0).
  Eliminates version drift on venv reinstall.
- **Incident root cause (2026-03-04):** Prior agent session ran
  `source venv/Scripts/activate && pip install flask-talisman` targeting the
  wrong `venv/` directory instead of `.venv/`. The `.venv/` was subsequently
  found empty (likely drained by the same session); reinstall from requirements
  files brought packages back at new versions for previously unpinned entries.
  Multiple background `python app.py` processes were also started via Bash tool
  and not cleaned up, blocking the owner terminal. User touched zero code.
- **AGENTS.md updated**: Environment Setup section corrected (`venv/` -> `.venv/`,
  bare `pip` -> `.venv/Scripts/pip`, added pinning requirement). Anti-Pattern
  Registry entries 4 and 5 added (wrong venv / bare pip, background server
  processes).
- **350 tests passing**, all hooks green.

### 2026-03-04 - side-task: gunicorn threading + dark mode browser preference

- **Gunicorn threading**: added `--threads 4` to Dockerfile CMD. Single sync worker
  was serializing all HTTP requests in production; threads allow concurrent request
  handling while keeping JOBS dict in shared process memory.
- **Dark mode fix**: `theme.js` now falls back to `window.matchMedia('(prefers-color-scheme: dark)')`
  when no localStorage preference is saved. First-visit users with browser dark mode
  enabled will see dark theme automatically. Explicit toggle still overrides.
- Load test findings (local, 1-5 concurrent users) documented in agent memory.
  Spotify cache TTL verified correct (ToS compliant). No upstream 429s at 2-5 users.

### 2026-03-04 - side-task: log rotation fix

- **Log rotation**: changed `RotatingFileHandler` to 2MB files / 10 backups (was 1MB / 5).
  Small files stay granular and parseable; 10 backups cover a full load test session.
  No production impact -- file is ephemeral on Fly.io; stdout is the prod log channel.
- **350 tests passing**, all hooks green.

### 2026-03-04 - side-task: PR code review fixes

- **theme.js**: `var` -> `const` for `saved` and `prefersDark` (neither reassigned;
  aligns with `const`/`let` convention in all other JS files).
- **Dockerfile**: added comment explaining `--workers 1 --threads 4` rationale for
  Fly.io deployment (shared-cpu-2x / 512MB, JOBS dict requires single process).
- **350 tests passing**, all hooks green.

### 2026-03-03 - Review-driven fixes: barrier safety, session cleanup, Docker error handling, dev_start tests

**Scope:** Side-task -- address Co-Pilot code review findings from PR #56, add
subprocess timeout guards, and add the deferred `dev_start.py` unit tests (now
warranted by increased error-handling complexity).

**Fixes applied:**
1. `concurrent_users_test.py` -- moved `barrier.wait()` inside `try` block so
   `BrokenBarrierError` is captured and a `ConcurrentResult` is always appended
   (docstring guarantee upheld).
2. `concurrent_users_test.py` -- track sessions in a list, call `session.close()`
   after `join()` to prevent connection/socket leaks.
3. `dev_start.py` -- `check_container_status()` now distinguishes "No such object"
   (returns `None`) from Docker daemon errors (raises `RuntimeError` with actionable
   message) and unexpected errors (raises with stderr details).
4. `dev_start.py` -- added `timeout=10` to `docker inspect` and `timeout=30` to
   `docker start` subprocess calls; catches `subprocess.TimeoutExpired` and raises
   `RuntimeError` with clear messaging.

**New tests:** 11 unit tests in `tests/scripts/dev/test_dev_start.py` covering
`check_container_status` (6 paths: running, absent, docker-not-found, timeout,
daemon-not-running, unexpected error), `start_container` (success, failure, timeout),
`main` (absent container exit, exited container start+exec).

**Validation:** `pytest -q` -- **350 passed**. `pre-commit run --all-files` -- all
hooks pass.

### 2026-03-03 - Fix Windows asyncpg startup packet (ProactorEventLoop) (side-task)

**Scope:** Side-task -- two-stage Windows-only cache fix. No code changes for
the Fly.io (Linux) deployment path.

**Errors encountered and resolved (session log):**

1. `.env` typo `DDATABASE_URL` (double-D prefix) -- cache silently disabled.
   Fixed by correcting the typo in `.env`.

2. `os.environ.get("DATABASE_URL")` returned `None` in background worker threads
   on Windows. Werkzeug debug reloader spawns a child process; `load_dotenv()`
   ran in the parent but environment variables were not reliably inherited.
   Fixed in `468b519`: capture `_DATABASE_URL = os.environ.get("DATABASE_URL")`
   at module import time in `cache.py` (runs once after `app.py` calls
   `load_dotenv()`). Also path-anchored `load_dotenv()` in `app.py` so it
   finds `.env` regardless of working directory.

3. `_DATABASE_URL` confirmed set (len=59) but asyncpg still failed silently.
   Docker logs revealed: `invalid length of startup packet` (10 rapid rejections
   -- matching 3 retries x multiple test runs). Root cause: `asyncio.new_event_loop()`
   in a daemon thread under Werkzeug's debug reloader on Windows creates a
   `SelectorEventLoop`, not a `ProactorEventLoop`. asyncpg uses Windows IOCP
   via `ProactorEventLoop`; with `SelectorEventLoop` it sends incorrect startup
   bytes and Postgres rejects the connection immediately.
   Fixed in `97db0c9`: `background_task()` in `orchestrator.py` now calls
   `asyncio.ProactorEventLoop()` when `sys.platform == "win32"`, falling back to
   `asyncio.new_event_loop()` on all other platforms (Linux/Fly.io unchanged).

4. `RotatingFileHandler` fails with `PermissionError: [WinError 32]` when
   multiple Flask processes hold the log file open simultaneously (Werkzeug
   debug reloader + interleaved restarts). Cosmetic only -- Flask continues to
   serve. Not fixed; documented here for future reference.

**Deploy safety:** Fix 3 uses `if sys.platform == "win32":` guard exclusively.
Fly.io (Linux) takes `asyncio.new_event_loop()` unchanged.

**Implementation:**
- `scrobblescope/orchestrator.py` -- `background_task()` updated (`97db0c9`)
- `scrobblescope/cache.py` -- `_DATABASE_URL` captured at module level (`468b519`)
- `app.py` -- path-anchored `load_dotenv()` (`468b519`)
- `tests/test_repositories.py` -- 4 tests updated to patch
  `scrobblescope.cache._DATABASE_URL` directly instead of `os.environ` (`468b519`)

**Validation:** `pytest -q` -- **320 passed**. `pre-commit run --all-files` -- all
hooks pass. Smoke test: `verdict=PASS`, `db_cache_lookup_hits=44`, elapsed ~1.05s
(vs ~6s cold Spotify fetch). Fly.io deploy path confirmed unaffected by guard.

**Forward guidance:** Cache subsystem is fully working locally. WP-2 is next:
13 unit tests for `_http_client` and `smoke_cache_check` in
`tests/test_smoke_cache_check.py`.

### 2026-03-03 - Improve agent orientation docs (side-task)

**Scope:** Side-task -- documentation only, no code changes. Improve agent
bootstrap reliability by fixing stale references and adding missing setup steps.

**Changes:**
- DEVELOPMENT.md: replaced stale "SESSION_CONTEXT is gitignored/ephemeral" text
  (lines 83-93) with accurate description of committed+tracked status, explicit
  `.gitignore` exception, and rationale for sharing across agents.
- AGENTS.md Environment Setup: added venv activation commands (Windows + Linux)
  so agents can run `pytest` and `pre-commit` without trial-and-error.
- AGENTS.md "What to update after a WP": added README deferral exception noting
  that README updates may be batched into a dedicated WP when the batch definition
  specifies one (e.g., Batch 16 WP-5).

**Validation:** `pytest -q` -- **320 passed**. `pre-commit run --all-files` -- all
hooks pass. `python scripts/doc_state_sync.py --check` -- exit 0.

**Forward guidance:** WP-1 is next. README will be stale during intermediate WPs;
updates deferred to WP-5 per batch definition.

### 2026-03-03 - Batch 16 definition written and activated (Batch 16 activation)

**Scope:** Define Batch 16 and activate it in PLAYBOOK + SESSION_CONTEXT.

**Plan:** Write `BATCH16_DEFINITION.md` incorporating audit corrections (stat key
fix, size caps removed, MEMORY.md references clarified as agent-private). Move to
`docs/history/definitions/`. Activate Batch 16 in PLAYBOOK Section 3. Update
SESSION_CONTEXT Section 2. Update HANDOFF_PROMPT.md and MEMORY.md for handoff.

**Implementation:** Definition written; audit findings applied (verdict key
`cache_hits` corrected to `db_cache_lookup_hits`, size caps removed per owner
instruction, `memory/MEMORY.md` removed from formal acceptance criteria). Definition
placed at `BATCH16_DEFINITION.md` (root; moves to archive at batch close-out). PLAYBOOK and
SESSION_CONTEXT activated. HANDOFF_PROMPT and MEMORY updated for clean handoff.

**Deviations:** None.

**Validation:** `pytest -q` -- **320 passed**. `pre-commit run --all-files` -- all
hooks pass. `python scripts/doc_state_sync.py --check` -- exit 0.

**Forward guidance:** WP-0 is next: create `scripts/testing/` and `scripts/dev/`
directories, move `smoke_cache_check.py` via `git mv`, update AGENTS.md and
SESSION_CONTEXT path references. No logic changes in WP-0.

### 2026-03-03 - Fix SESSION_CONTEXT.md commit convention and stage accumulated changes

**Scope:** Side-task -- documentation and gitignore fix, no code changes.

**What:** SESSION_CONTEXT.md was never staged in the two previous side-task commits
(`c4bf737`, `4f1cf6a`) despite commit messages implying it. SESSION_CONTEXT.md has
been git-tracked since before `edee612` (when `.claude/` was added to .gitignore).
The `.gitignore` entry `.claude/` is misleading -- SESSION_CONTEXT.md is grandfathered
in as a tracked file. Fix: update `.gitignore` to `.claude/*` + `!.claude/SESSION_CONTEXT.md`
so the exception is explicit. Fix AGENTS.md: remove incorrect "SESSION_CONTEXT is
gitignored" language. Stage the accumulated SESSION_CONTEXT.md changes (Batch 15 state
update, Section 8 browser MCP note, Section 8 local Postgres note).

**Why:** SESSION_CONTEXT.md is the shared cross-agent dashboard. All agents (Gemini,
Copilot, Codex, Claude Code) bootstrap from it. Leaving it uncommitted means every agent
starts with stale branch, test count, and batch status. The gitignore fix makes the
tracked-exception visible and prevents future agents from falsely concluding the file
is machine-local.

**Validation:** `pytest -q` -- **320 passed**. `pre-commit run --all-files` -- all hooks pass.
`python scripts/doc_state_sync.py --check` -- exit 0.

**Forward guidance:** No batch active. BATCH16_PROPOSAL.md written; awaiting owner review.

### 2026-03-03 - Add local DB setup and init_db.py caveat to env docs

**Scope:** Side-task -- documentation only, no code changes.

**What:** Added local Postgres DB setup details and `init_db.py` load_dotenv caveat
to AGENTS.md Environment Setup and SESSION_CONTEXT Section 8. These facts apply to
all agents (Gemini CLI, Copilot, Codex, Claude Code) running local DB tests.

**Why:** `init_db.py` has no `load_dotenv()` call. Any agent running it will get
"DATABASE_URL not set" unless the env var is set directly in the shell. Absent from
canonical docs, every agent would hit this silently and assume cache is unavailable.

**Validation:** `pytest -q` -- **320 passed**. `pre-commit run --all-files` -- all hooks pass.
`python scripts/doc_state_sync.py --check` -- exit 0.

**Forward guidance:** No batch active. Awaiting owner scope definition for next batch.

### 2026-03-03 - Add browser MCP environment note to SESSION_CONTEXT

**Scope:** Side-task -- documentation only, no code changes.

**What:** Added one line to SESSION_CONTEXT Section 8 (Environment notes) documenting
that the browser MCP accesses the local Flask app via `http://host.docker.internal:5000/`
rather than `localhost`, because the MCP browser runs inside a Docker container.

**Why:** This is a runtime fact that future agent sessions need to reproduce local
browser testing correctly. Absent from SESSION_CONTEXT, an agent would attempt
`localhost` and get a connection refused error with no clear diagnosis path.

**Validation:** `pytest -q` -- **320 passed**. `pre-commit run --all-files` -- all hooks pass.
`python scripts/doc_state_sync.py --check` -- exit 0.

**Forward guidance:** No batch active. Awaiting owner scope definition for next batch.

### 2026-03-02 - Session findings and handoff notes (side-task)

**Scope:** Observations from Batch 15 WP-1 execution session, documented for
next-agent orientation.

**Findings:**
1. **docsync `--fix` SESSION_CONTEXT write bug (fixed):** `cli.py` computed the
   correct STATUS block but never wrote it. Fixed in commit `67fa1dc`. AGENTS.md
   cross-validation section updated to reflect corrected behavior.
2. **Deviation tag routing:** Headings with non-standard tags like
   `(Batch 15 WP-1 deviation)` do NOT match `ENTRY_BATCH_RE` regex
   (`\(Batch\s+(\d+)\s+WP-\d+\)`). They are routed outside CURRENT-BATCH
   markers as untagged entries. This is correct behavior -- use standard
   `(Batch N WP-X)` tags only for entries that should stay inside markers.
3. **Mid-batch handoff discipline (added):** AGENTS.md now requires PLAYBOOK
   Section 3 to reflect true state at all times, not just after commits.
4. **SESSION_CONTEXT Section 7 is stale:** Shows 307 tests across old counts.
   Actual: 311 tests across 18 files. WP-2 will fix this.
5. **README.md is stale:** Says 257 tests, lists incomplete pre-commit hooks,
   project structure test section outdated. WP-2 will fix this.
6. **HANDOFF_PROMPT.md is stale:** References deleted branch, old audit, old
   tasks. WP-5 will replace it; interim handoff written for this transition.

**Forward guidance:**
- Next agent should start with WP-2 per BATCH15_DEFINITION.md execution order.
- Always use standard `(Batch N WP-X)` tags for batch log entries.
- Run `doc_state_sync.py --fix` after every PLAYBOOK Section 4 edit.

### 2026-03-02 - Fix docsync --fix not writing SESSION_CONTEXT STATUS block (Batch 15 WP-1 deviation)

**Scope:** `scripts/docsync/cli.py`, `tests/test_docsync_cli.py`, `AGENTS.md`.

**Plan vs implementation:**
- Planned: during WP-1 execution, discovered that `doc_state_sync.py --fix`
  computes the correct STATUS block for SESSION_CONTEXT but never writes it
  to disk. AGENTS.md line 138-139 claimed the script "Refreshes the
  machine-managed DOCSYNC:STATUS block" but the code only warned on staleness
  without writing. This was a bug, not a design choice.
- Implemented: modified `cli.py` so `--fix` writes the refreshed STATUS block
  to SESSION_CONTEXT when stale. `--check` continues to warn-only (does not
  fail) because SESSION_CONTEXT is gitignored and should not block commits.
  Updated AGENTS.md cross-validation section to reflect corrected behavior.
  Added 1 new test (`test_fix_refreshes_session_context_status_block`) and
  updated the stale-warning assertion text in existing test.

**Deviations:**
- This fix was not in the Batch 15 definition. It was discovered during WP-1
  when the agent attempted to run `--fix` and found SESSION_CONTEXT unchanged.
  The fix is scoped to the bug and does not change any other docsync behavior.

**Validation:**
- `pytest tests/test_docsync_cli.py -v` (**19 passed**)
- `pytest -q` (**311 passed**, 3 deprecation warnings from aiohttp connector)
- `python scripts/doc_state_sync.py --fix` (wrote SESSION_CONTEXT)
- `python scripts/doc_state_sync.py --check` (pass, no stale warning)
- `pre-commit run --all-files` (pass, all 8 hooks)

**Forward guidance:**
- After any PLAYBOOK Section 4 edit, run `doc_state_sync.py --fix` and verify
  SESSION_CONTEXT STATUS block was updated. The script now handles this
  automatically.

### 2026-02-27 - Revalidate audit findings and prepare next-agent packet (side-task)

**Scope:** `docs/history/AUDIT_2026-02-27_MULTI_AGENT_SWEEP.md`,
`tests/test_docsync_logic.py` (format-only), repo-wide quality gates.

**Plan vs implementation:**
- Planned: verify previously reported findings against current branch state,
  refresh stale assertions, and produce implementation-ready guidance for the
  next agent handoff.
- Implemented: re-ran full validations, updated stale test baseline and
  resolved-item status in the audit report, and added a scoped next-agent
  implementation packet with acceptance criteria.

**Deviations:**
- No behavioral code changes were required; only audit/report updates plus
  formatter-normalized whitespace in `tests/test_docsync_logic.py`.

**Validation:**
- `pre-commit run --all-files` (pass)
- `pytest -q` (**310 passed**, 3 deprecation warnings from aiohttp connector)
- `python scripts/doc_state_sync.py --check` (pass)

**Forward guidance:**
- Execute the next-agent packet in commit-sized slices: test-module split,
  low-risk orchestrator extraction, then CI/session policy wording alignment.

### 2026-02-27 - Harden docsync non-happy-path coverage + path guidance (side-task)

**Scope:** `tests/test_docsync_logic.py`, `tests/test_docsync_cli.py`,
`AGENTS.md`, `PLAYBOOK.md`.

**Plan vs implementation:**
- Planned: enforce anti-happy-path discipline for docsync archive-link and
  migration handling, and remove path ambiguity between untagged archive,
  per-batch logs, and definitions.
- Implemented: added adversarial tests for `docs/logarchive` link validation
  (exists/missing) and for `--split-archive` missing-input failure (`exit 2`),
  plus explicit archive/log/definition lookup guidance in AGENTS and PLAYBOOK.

**Deviations:**
- One assertion was adjusted to be path-separator-agnostic on Windows
  (`PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` substring) after first run exposed
  slash-vs-backslash brittleness.

**Validation:**
- `pytest -q tests/test_docsync_logic.py tests/test_docsync_cli.py`
  (**57 passed**)
- `pytest -q` (**310 passed**, 3 deprecation warnings from aiohttp connector)
- `python scripts/doc_state_sync.py --check` (pass)

**Forward guidance:**
- Keep new docsync tests behavior-focused (real inputs + failure paths), not
  mock-call-only checks, when adding future archive-routing rules.

### 2026-02-27 - Migrate monolith archive path to docs/logarchive (side-task)

**Scope:** `scripts/docsync` path canonicalization, pointer compatibility docs,
doc references, regression validation.

**Plan vs implementation:**
- Planned: stop using the legacy history monolith paths
  (`docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` and
  `docs/history/logs/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`) as the
  canonical monolith location and move to a dedicated `docs/logarchive/`
  folder with clear pointers from legacy paths.
- Implemented: switched docsync `ARCHIVE_PATH` to
  `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`, copied canonical
  archive content there, converted both legacy monolith files into pointer
  documents, and added `docs/logarchive/README.md` lookup guidance.

**Deviations:**
- Historical documents under `docs/history/definitions/` and batch logs were
  left unchanged to preserve historical wording; compatibility pointers prevent
  breakage for legacy references.

**Validation:**
- `python scripts/doc_state_sync.py --fix`
- `python scripts/doc_state_sync.py --check`
- `pytest -q tests/test_docsync_cli.py tests/test_docsync_logic.py`
  `tests/test_docsync_parser.py tests/test_docsync_renderer.py` (**103 passed**)
- `pytest -q` (**307 passed**, 3 deprecation warnings from aiohttp connector)

**Forward guidance:**
- Use `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` for untagged archive
  search and keep per-batch logs under `docs/history/logs/` as the tagged route.

### 2026-02-27 - Branch hygiene cleanup after main diff review (side-task)

**Scope:** orchestration hygiene (`.gitignore`, PLAYBOOK state consistency,
root audit-file placement), docsync warning cleanup.

**Plan vs implementation:**
- Planned: remove non-actionable docsync warning noise and align tracked state
  with the "local-only" `.claude/SESSION_CONTEXT.md` policy.
- Implemented: scoped `BATCH*_AUDIT*.md` ignore rule to repo root only,
  moved `BATCH14_PROPOSAL_AUDIT1.md` from root into `docs/history/`, and
  recorded the side-task in Section 4.

**Deviations:**
- `git mv` could not be used for `BATCH14_PROPOSAL_AUDIT1.md` because the file
  was not under version control; file-system move was used instead.

**Validation:**
- Ran `python scripts/doc_state_sync.py --fix` and
  `python scripts/doc_state_sync.py --check` after edits.

**Forward guidance:**
- Keep root-only draft/audit patterns scoped with leading `/` in `.gitignore`
  so archive destinations under `docs/history/` remain trackable.

### 2026-02-26 - Remediate docsync audit findings (side-task)

**Scope:** `scripts/docsync/` (cli, parser, renderer, logic),
test suite (parser, renderer, logic), `AGENTS.md`.

**Changes:**
- Fixed unconditional PLAYBOOK/ARCHIVE writes in --fix mode (F1).
- Consolidated SyncError import to top-level in cli.py (F11).
- Defined TEST_COUNT_RE once in parser.py (F2).
- Extracted _dedup_sorted() helper in logic.py (F3).
- Tightened ENTRY_BATCH_RE to require (Batch N WP-X) format (F6).
- Added duplicate-marker detection in _find_marker_pair (F7).
- Added sentinel -1 comment (F5).
- Removed dead stale-phrase detection + 3 tests (F8).
- Fixed misleading docstring (9a), weak assertion (9b).
- Added 4 tests: duplicate headings (9c), adversarial regex (9d),
  duplicate markers (F7), file-order dependency (9e).

**Test count:** **307 passed** (net +1: -3 removed, +4 added).
**Validation:** `pytest -q` 307 passed; `pre-commit run --all-files` clean.

### 2026-02-25 - Post-batch test suite audit (doc hygiene)

**Scope:** `tests/test_docsync_logic.py`, `tests/test_docsync_cli.py`,
`tests/test_docsync_parser.py`; deleted `tests/test_docsync_models.py`.

**Changes:**
- Fixed `test_deduplication_across_archive`: was passing vacuously -- tagged
  entry routed to `batch_log_updates`, bypassing monolith dedup entirely;
  rewrite uses untagged entry and asserts `batch_log_updates == {}`.
- Dropped `test_current_entry_count_mismatch_warns`: near-duplicate of
  `test_mismatched_counts_warns` (identical `_cross_validate` code path).
- Rewrote `test_section4_historical_count_ignored`: old version had no
  CURRENT-BATCH markers so `_latest_test_count_from_entries` returned None
  vacuously; new version confirms below-end-marker counts are ignored while
  inside-marker count is used for comparison.
- Removed unused `LOGS_DIR` name import from `test_docsync_cli.py`.
- Merged 5 `_fingerprint`/`_extract_entry_batch` tests from misnamed
  `test_docsync_models.py` into `test_docsync_parser.py`; deleted old file.
- Added `TestSplitArchiveMode.test_split_archive_routes_tagged_entry` for
  the previously uncovered `--split-archive` CLI branch.

**Test count:** **306 passed** (net zero: -6 removed, +6 added).
**Validation:** `pytest -q` 306 passed; `pre-commit run --all-files` clean.

### 2026-02-25 - fix(doc-sync): remediate SESSION_CONTEXT staleness in _cross_validate and _build_status_block (side-task)

- Scope: `scripts/docsync/logic.py`, `scripts/docsync/renderer.py`, `scripts/docsync/cli.py`,
  `tests/test_docsync_logic.py` (+6 tests: 4 TestLatestTestCount + 2 rewritten + 1 renamed),
  `tests/test_docsync_renderer.py` (+2 TestBuildStatusBlock count tests),
  `tests/test_docsync_cli.py` (1 test updated).
- Problem: Two root causes for SESSION_CONTEXT staleness: (1) `_cross_validate` scanned
  PLAYBOOK Section 3 for `**N passed**` counts, but agents write test counts in Section 4
  log entry Validation fields — Section 3 is narrative prose. `playbook_counts` was always
  empty so the mismatch warning never fired. (2) `_build_status_block` did not include the
  test count in the STATUS block output, forcing agents to check stale manual rows.
  Additionally, `_cross_validate` was called with `result.session_lines` (post-sync), which
  already had the correct count injected by `_build_status_block`, laundering mismatch away.
- Fix: Added `_latest_test_count_from_entries(playbook_lines)` to `logic.py` — parses
  Section 4 current-batch entries newest-first and returns the first `**N passed**` count.
  Updated `_cross_validate` to call this function (scalar comparison) instead of scanning
  Section 3. Added `_TEST_COUNT_RE` to `renderer.py`; `_build_status_block` now emits
  `"- Latest validated test count: **N passed**."` using the most-recent entry body count.
  Fixed `cli.py` to call `_cross_validate(playbook_lines, session_lines)` (original, pre-sync
  lines) so the STATUS block update cannot launder a pre-existing mismatch.
- Deviations: None. All changes additive; no logic in `_sync` was touched.
- Validation: **294 passed** (+6 vs WP-2 baseline), all 8 pre-commit hooks passed.

### 2026-02-25 - docs(audit): add BATCH14 pre-approval audit report and apply corrections to proposal (side-task)

- Scope: `BATCH14_PROPOSAL.md`, `docs/history/BATCH14_AUDIT_2026-02-25.md`.
- Purpose: Pre-batch audit of BATCH14_PROPOSAL.md before owner sign-off. Verified
  all five structural checks (WP-1 naming conventions, WP-2 package extraction
  symmetry, WP-3 feature isolation, WP-4 test distribution, WP-5 AGENTS.md
  close-out / MEMORY.md hallucination check). All five checks confirmed correct.
- Correction: "~450-line" description for `doc_state_sync.py` corrected to "~679-line"
  in two places (Current state table and WP-2 goal). Actual measured line count: 679.
- Verdict: APPROVED WITH CORRECTIONS.
- Validation: 288 passed (unchanged -- audit makes no code changes), all 8 pre-commit
  hooks passed.

### 2026-02-25 - test(worker): assert daemon=True via Thread patch, expand docstrings (side-task)

- Scope: `tests/test_worker.py`.
- Problem: `test_start_job_thread_creates_daemon_thread` only asserted the target
  was called; it never verified `threading.Thread` was constructed with `daemon=True`,
  despite the test name and docstring claiming otherwise. Tests 1–4 had minimal
  single-line docstrings inconsistent with the GIVEN/WHEN/THEN standard.
- Fix: Introduced `DummyThread` class, patched at `scrobblescope.worker.threading.Thread`;
  asserts `daemon=True` and target invocation. Dropped `*args` from `DummyThread.__init__`
  (Pylance hint; Thread is called with keyword args only). Expanded tests 1–4 docstrings
  to GIVEN/WHEN/THEN inline format.
- Validation: 288 passed, all 8 pre-commit hooks passed.

### 2026-02-25 - test(retry): use public semaphore API in semaphore-gates test (side-task)

- Scope: `tests/test_retry_with_semaphore.py`.
- Problem: Reviewer flagged `sem._value == 0` as a private implementation detail
  of `asyncio.Semaphore`, suppressed with `# noqa: SLF001`, making the assertion
  brittle across Python versions.
- Fix: Replaced with `sem.locked()`, the public equivalent (stable since Python 3.4).
  Updated comment; noqa suppression removed. Confirmed only occurrence in suite.
- Validation: 288 passed, all 8 pre-commit hooks passed.

### 2026-02-25 - fix(utils): support constant backoff value in retry_with_semaphore (side-task)

- Scope: `scrobblescope/utils.py`, `scrobblescope/spotify.py`,
  `tests/test_retry_with_semaphore.py`.
- Problem: Reviewer 1 flagged that `backoff` only accepted a callable, requiring
  `backoff=lambda _a: 1` for constant delays. Updating call sites to use a plain
  float was not possible without a utility change.
- Fix: Added `callable(backoff)` guard at line 341 of `utils.py`; updated docstring
  type annotation. Simplified `spotify.py` search call site to `backoff=1`. Added
  `test_constant_float_backoff_accepted` to `test_retry_with_semaphore.py`.
- Validation: 288 passed (+1 vs Batch 13 baseline), all 8 pre-commit hooks passed.

### 2026-02-25 - test(orchestrator): use standard asyncio import in fetch_spotify tests (side-task)

- Scope: `tests/services/test_orchestrator_fetch_spotify.py`.
- Problem: Reviewer 2 flagged two `__import__("asyncio").Semaphore(5)` usages
  bypassing Pylance type resolution; root cause was missing top-level `import asyncio`.
- Fix: Added `import asyncio` to stdlib imports block; replaced both
  `__import__("asyncio").Semaphore(5)` occurrences with `asyncio.Semaphore(5)`.
- Validation: 288 passed, all 8 pre-commit hooks passed.

### 2026-02-24 - docs(audit): BATCH13 pre-approval audit report (side-task)

- Scope: `BATCH13_PROPOSAL.md`, `docs/history/BATCH13_AUDIT_2026-02-23.md`.
- Problem: BATCH13 proposal required independent technical verification before
  owner approval. Line references, test coverage claims, retry extraction
  design, and convention compliance needed validation against actual codebase.
- Fix: Completed 4-WP audit. Found 5 discrepancies: `_apply_pre_slice` line
  start off by 2 (L664 -> L666), `_JOB_SEMAPHORE` variable name incorrect
  (actual: `_active_jobs_semaphore`), batch retry missing jitter declaration,
  batch backoff incorrectly stated as fixed 1.0 (actual: `2**attempt`
  exponential). Applied all corrections to the proposal. Created audit report.
- Validation: **260 tests passing**, pre-commit all 8 hooks passed. No source
  code changes -- audit only.

### 2026-02-23 - chore(merge): integrate main into wip/pc-snapshot (side-task)

- Scope: `scripts/doc_state_sync.py`, `tests/test_doc_state_sync.py` (merge
  resolution only -- no net change from branch perspective).
- Problem: `main` had one commit ahead (`05c7b19`) that was already
  cherry-picked into `wip/pc-snapshot` as part of `4e4c9a1`. The branch
  needed to formally integrate `main` before PR #36 could merge cleanly.
- Fix: `git merge origin/main --no-edit`; ort strategy resolved cleanly
  (identical content on both sides for the two touched files). Merge commit
  `d98c90b` amended to conventional format.
- Validation: **260 tests passing**, pre-commit all 8 hooks passed.

### 2026-02-23 - fix/docs: cherry-pick SESSION_CONTEXT optional + DEVELOPMENT.md (side-task)

- Scope: `scripts/doc_state_sync.py`, `tests/test_doc_state_sync.py`,
  `DEVELOPMENT.md`, `docs/history/SESSION_CONTEXT_REFERENCE.md`, `README.md`.
- Problem: (1) CI failed on `main` when `.claude/SESSION_CONTEXT.md` was
  absent (gitignored). The script called `_read_lines()` unconditionally,
  raising `SyncError`. (2) No documentation existed for the multi-agent
  orchestration methodology implemented during this sprint.
- Fix:
  (1) Cherry-picked commit `05c7b19` from `main`: added `_read_lines_optional()`
  returning `None` when the file is absent; gated all SESSION_CONTEXT
  operations in `_sync()`, `_cross_validate()`, and `main()` behind
  presence check; `SyncResult.session_lines` typed as `list[str] | None`;\
  renamed `test_missing_session_context_raises` to `_succeeds`; added
  `TestMissingSessionContext` class (3 regression tests).
  (2) Created `DEVELOPMENT.md` explaining the orchestration architecture,
  why `doc_state_sync.py` is a deterministic script, the batch/WP SDLC
  mapping, review-rejection rationale, and what failed before the current
  system stabilized. Created `docs/history/SESSION_CONTEXT_REFERENCE.md`
  as a tracked reference snapshot of the gitignored live file. Linked
  both from `README.md` (new "Development Methodology" section in ToC).
- Validation: **260 tests passing** (3 new from cherry-pick),
  pre-commit all 8 hooks passed.

### 2026-02-23 - chore/docs: repo hygiene and README rewrite (side-task)

- Scope: root directory, `.gitignore`, `README.md`, `.claude/`.
- Problem: (1) Root directory cluttered with completed batch definitions
  (`BATCH12_PROPOSAL.md`, `BATCH8_REFACTOR_PLAN.md`) and an obsolete
  playbook compatibility shim (`EXECUTION_PLAYBOOK_2026-02-11.md`).
  (2) `.claude/` tracked in git (agent-local state, stale `BATCH3_CONTEXT.md`,
  machine-specific `settings.local.json`). (3) `README.md` outdated --
  "work in progress" status badge, 30+ completed checkbox items, missing
  Architecture/Deployment sections, stale Tech Stack section.
- Fix:
  (1) `git mv` both batch definitions to `docs/history/`. `git rm`
  the playbook shim. Deleted untracked stale files (`backup.py`,
  `Backup_batch`, empty `app/` directory).
  (2) Added `.claude/` to `.gitignore`, `git rm --cached` all 3 tracked files,
  deleted stale `BATCH3_CONTEXT.md` locally.
  (3) Comprehensive README rewrite: active status badge + test count badge,
  new Architecture section with pipeline diagram + design decisions, Tech
  Stack table, Deployment section with Fly.io commands + smoke test,
  condensed Roadmap (upcoming + recent completions only), accurate Project
  Structure tree with per-file annotations and test counts, Running Tests
  section, trimmed Contributing/License/Acknowledgements.
- Validation: **257 tests passing**, pre-commit all 8 hooks passed.

### 2026-02-22 - fix(app): guard sys.stderr.reconfigure with isinstance check

- Scope: `app.py`.
- Problem: Pyright/Pylance reported "Cannot access attribute reconfigure for
  class TextIO" because `sys.stderr` is typed as `TextIO`, which lacks
  `reconfigure`. The method exists at runtime on `io.TextIOWrapper`.
- Fix: Added `import io` and wrapped the call in
  `if isinstance(sys.stderr, io.TextIOWrapper):` -- a type-narrowing guard
  that satisfies both the type checker and runtime safety.
- Validation: `pytest -q`: **210 passed**. `pre-commit`: all hooks passed.

### 2026-02-22 - refactor(routes,lastfm): SoC/DRY cleanup from third-party audit

- Scope: `scrobblescope/routes.py`, `scrobblescope/lastfm.py`,
  `scrobblescope/orchestrator.py`, `tests/services/test_lastfm_logic.py`.
- Problem: Three findings from a third-party structural audit:
  (1) SoC -- `get_filter_description` was a public helper placed between HTTP
  handlers; lacked `_` prefix used by the other private helpers.
  (2) DRY -- `/results_complete` and `/unmatched_view` duplicated ~10 lines
  of identical `job_id`/`job_context` guard logic.
  (3) SoC -- `fetch_top_albums_async` in `lastfm.py` imported `set_job_stat`
  from `repositories.py` and made 5 direct job-state mutations. An API client
  module should return pure data, not mutate application state. `spotify.py`
  already follows this pattern correctly.
- Fix:
  (1) Renamed to `_get_filter_description` and hoisted above HTTP handlers,
  below `_group_unmatched_by_reason`.
  (2) Extracted `_get_validated_job_context(missing_id_message, expired_error,
  expired_message, expired_details)` returning `(job_id, job_context, None)`
  or `(None, None, error_response)`.
  (3) Removed `job_id` param and `set_job_stat` import from
  `fetch_top_albums_async`. Stats now returned in `fetch_metadata["stats"]`
  dict. `orchestrator._fetch_and_process` extracts and records them.
  Partial-data warning also moved to `fetch_metadata` return path.
- Deviations: Audit claimed ~15-20 lines of duplication; actual overlap was
  ~10 lines. Error titles intentionally differ between routes, so
  `expired_error` was parameterized rather than hardcoded.
- Validation: `pytest -q`: **210 passed**. `pre-commit`: all 8 hooks passed.

### 2026-02-22 - fix(types): resolve 10 Pylance type errors in production code

- Scope: `scrobblescope/lastfm.py`, `scrobblescope/spotify.py`,
  `scrobblescope/utils.py`.
- Problem: Pylance reported 10 type errors across 3 production files:
  (1) `lastfm.py` (7): `metadata` dict inferred as `dict[str, str | int]`
  caused arithmetic and nested-dict assignment failures; `albums` defaultdict
  inferred heterogeneous union on all value accesses.
  (2) `spotify.py` (2): `SPOTIFY_CLIENT_ID/SECRET` typed `str | None` from
  `os.getenv()` but `aiohttp.BasicAuth` requires `str`.
  (3) `utils.py` (1): `loop` assigned inside `try:` block, referenced in
  `finally:` -- possibly unbound if `new_event_loop()` raises.
- Fix: Annotated `metadata: dict[str, Any]` and
  `albums: defaultdict[str, dict[str, Any]]` in lastfm.py; added assert
  guards for Spotify credentials in spotify.py; initialized `loop = None`
  with `if loop is not None:` guard in utils.py.
- Test file type errors (25 across 3 files) assessed as low-impact
  mock-related noise -- deferred.
- Validation: `pytest -q`: **210 passed**. `pre-commit`: all 8 hooks passed.

### 2026-02-21 - refactor/fix: Gemini audit remediation (non-normalization track)

- Scope: `scrobblescope/orchestrator.py`, `scrobblescope/cache.py`,
  `scrobblescope/routes.py`, `scrobblescope/domain.py`,
  new `scrobblescope/errors.py`, `scrobblescope/repositories.py`,
  `tests/services/test_orchestrator_service.py` (+4 tests),
  `docs/history/BUGFIX_AUDIT_REMEDIATION_2026-02-21.md` (new doc).
- Problem: A second Gemini Pro audit pass identified four issues beyond the previously
  fixed normalization bugs. Three were confirmed real against the live codebase:
  1. Late slicing: `limit_results` applied after Spotify calls in `_fetch_and_process`.
     For playcount sort the ranking is fully known from Last.fm data; pre-slicing
     to the requested limit eliminates unnecessary Spotify searches on cache misses.
     (Playtime sort cannot be pre-sliced -- ranking requires track duration data.)
  2. Indefinite DB growth: `_batch_lookup_metadata` filtered stale rows at read time
     but no DELETE ever ran. Stale rows accumulated in `spotify_cache` indefinitely.
  3. ERROR_CODES + SpotifyUnavailableError in `domain.py`: a SoC violation -- domain
     logic should not own user-facing message strings or retryability flags.
  A fourth SoC issue not in the original report was also fixed: duplicate release_scope
  -> human-text translation in `routes.py` (inline block in `unmatched_view`
  duplicating `get_filter_description`). A fifth issue (empty-result hallucination)
  was assessed and deferred as near-false-alarm -- the trigger conditions require
  zero cache hits AND every album absent from Spotify, which is extremely unlikely.
- Plan vs implementation: all four confirmed issues fixed as described in
  `docs/history/BUGFIX_AUDIT_REMEDIATION_2026-02-21.md`. No scope additions.
- Deviations: none.
- Validation:
  - `pytest -q`: **114 passed** (110 pre-existing + 4 new tests).
  - `pre-commit run --all-files`: all 8 hooks passed.
  - Import graph: `errors.py` is a leaf module (no package imports). Acyclic structure
    preserved. `domain.py` now contains only normalization logic.
- Forward guidance: next sub-track is "sycophantic test coverage" audit (owner to
  elaborate scope). Feature work (top songs, heatmap) blocked until owner assigns a
  future batch number and defines scope. `_cleanup_stale_metadata` is opportunistic and non-fatal;
  monitor logs for "Stale cache cleanup" entries to confirm it fires in production.
  The playtime late-slicing limitation is documented inline in `_fetch_and_process`.

### 2026-02-21 - fix(domain): fix normalization bugs silently excluding non-Latin albums

- Scope: `scrobblescope/domain.py`, `tests/test_domain.py` (9 new tests),
  `tests/services/test_lastfm_logic.py` (new file, 7 tests),
  `docs/history/BUGFIX_NORMALIZATION_2026-02-21.md` (new doc).
- Problem: A third-party static analysis review (Gemini Pro) identified four
  defects in `domain.py` and a coverage gap in `lastfm.py`. All four were
  confirmed against the live codebase and three had measurable production impact:
  1. `normalize_track_name` used `NFKD + encode("ascii","ignore")`, stripping all
     non-Latin characters to `""`. Any album with Japanese/Cyrillic/etc. track names
     had `len(track_counts) == 1` regardless of distinct tracks played, silently
     failing the `min_tracks` filter and disappearing from results without an
     unmatched entry or any log warning.
  2. `normalize_name` applied its `album_metadata_words` set to the artist string as
     well as the album string, corrupting proper nouns like "New Edition" -> "new"
     and reducing artists named "Special", "Bonus", or "EP" to an empty string.
     Two artists with all-metadata-word names could collide on the same dict key.
  3. `normalize_track_name` used a 13-character hardcoded list while `normalize_name`
     used `str.maketrans(string.punctuation, ...)` covering all 32 ASCII punctuation
     characters. Characters like `&` were inconsistently handled.
  4. `fetch_top_albums_async` (aggregation, timestamp filtering, min_plays/min_tracks)
     had zero test coverage despite being the core business logic function.
- Plan vs implementation: all four defects addressed as described in
  `docs/history/BUGFIX_NORMALIZATION_2026-02-21.md`. No scope additions or removals.
- Deviations: none.
- Validation:
  - `pytest -q`: **110 passed** (94 pre-existing + 9 new domain tests + 7 new logic tests).
  - `pre-commit run --all-files`: all hooks passed (black reformatted test_domain.py
    on first pass; clean on second).
  - Owner live test: Japanese-title 2025 album (betcover!!) now appears in results
    for listening year 2025 with "Same as release year" filter. Previously absent with
    no unmatched entry. Second validation: same artist's 2021 album (10 unique tracks,
    68 plays) also appeared correctly.
  - "New Edition" self-titled album test: artist key now "new edition" (not "new");
    album deduplication with "(Deluxe Edition)" suffix confirmed still working.
- Forward guidance: no schema, API contract, or route changes. No migration needed.
  The new `test_lastfm_logic.py` file should be extended if `fetch_top_albums_async`
  logic changes (e.g., top-songs feature). Pre-Batch-10 housekeeping is ongoing;
  Batch 10 scope remains TBD by owner.

### 2026-02-20 - fix(tooling): remove transient rotated field from SESSION_CONTEXT status block
- Scope: `scripts/doc_state_sync.py`, `AGENTS.md`.
- Problem: `_build_status_block` wrote `rotated=N` into the managed SESSION_CONTEXT
  block based on the current run's rotation count. The subsequent `--check` always
  recomputed `rotated=0` from the now-clean playbook, causing permanent drift after
  any `--fix --keep-non-current N` run. The workaround required a two-pass sequence.
- Fix: Removed the `Rotated to archive in latest sync run` line from `_build_status_block`.
  The count is still reported on stdout; it is no longer written to a file that `--check`
  re-derives. `--fix --keep-non-current 0` is now a single idempotent command.
- Updated `AGENTS.md` to document the one-pass rotation pattern for agent handoff.
- Deviations: none.
- Validation:
  - `pytest -q`: **94 passed**.
  - `pre-commit run --all-files`: all hooks passed.
  - `python scripts/doc_state_sync.py --check`: passed.
- Forward guidance: tooling is stable. WP-8 (CI/lint/dependency hygiene) is next.

### 2026-02-20 - docs: rotate 4 stale non-current Section 10 entries to archive
- Scope: `PLAYBOOK.md`, `docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`, `.claude/SESSION_CONTEXT.md`.
- Problem: Four pre-Batch-9 entries (2026-02-19 x2, 2026-02-14 x2) had accumulated
  below `CURRENT-BATCH-END` as `kept_non_current=4` with `rotated=0`, creating
  visible bloat in Section 10.
- Fix: Ran `python scripts/doc_state_sync.py --fix --keep-non-current 0` to flush
  all non-current entries to the archive. Section 10 now contains only active-batch
  entries.
- Deviations: none (purely mechanical doc maintenance).
- Validation:
  - `python scripts/doc_state_sync.py --check`: passed.
  - `pre-commit run --all-files`: all hooks passed.
- Forward guidance: run `--fix --keep-non-current 0` at each batch boundary to keep
  Section 10 clean.

### 2026-02-20 - WP-7: frontend safety — showToast DOM construction + non-200 fetch guard
- Scope: `static/js/results.js`.
- Problem 1: `showToast` built its HTML via a template-literal string injected with
  `insertAdjacentHTML`. The `message` argument was interpolated without escaping,
  creating an HTML injection pathway if any caller passed server-sourced content.
- Problem 2: `fetchUnmatchedAlbums` piped `fetch()` directly to `.json()` without
  checking `response.ok`. A non-200 response (404, 500, etc.) would be silently
  treated as valid data, surfacing as "No unmatched albums found" instead of an
  error.
- Fix:
  - Rewrote `showToast` to build the toast element tree with `document.createElement`
    / `textContent` / `setAttribute`; eliminated `insertAdjacentHTML` and the unused
    `toastId`. Message content is now set via `.textContent` (XSS-safe).
  - Added `response.ok` guard before `response.json()` in `fetchUnmatchedAlbums`;
    throws `Error("Server error: <status>")` on non-2xx, which the existing `.catch`
    handler surfaces to the user.
- Deviations: none.
- Validation:
  - `pytest -q`: **94 passed**.
  - `pre-commit run --all-files`: all hooks passed.
  - `python scripts/doc_state_sync.py --check`: passed.
- Forward guidance: WP-7 complete. WP-8 (CI/lint/dependency hygiene) is next.

### 2026-02-20 - P1 refactor: extract VALID_FORM_DATA and csrf_app_client fixture
- Scope: `tests/helpers.py`, `tests/conftest.py`, `tests/test_routes.py`.
- Problem: `VALID_FORM_DATA` (the flounder14/2025 form dict for `/results_loading`
  tests) was copy-pasted verbatim 7 times across `test_routes.py`. The 5-line
  CSRF-enabled app + test-client setup was repeated in every CSRF test function.
- Fix:
  - Added `VALID_FORM_DATA` constant to `tests/helpers.py`.
  - Added `csrf_app_client` pytest fixture to `tests/conftest.py`; it creates a
    CSRF-enabled app client (WTF_CSRF_ENABLED not disabled) for CSRF enforcement
    tests.
  - Updated `tests/test_routes.py`: removed `from app import create_app` (now
    unused); imported `VALID_FORM_DATA` from `tests.helpers`; replaced all 7
    inline form dicts with `VALID_FORM_DATA` (or `{**VALID_FORM_DATA, "year": "X"}`
    for year-override cases); replaced all 6 CSRF test inline app setups with the
    `csrf_app_client` fixture parameter.
- Deviations: none.
- Validation:
  - `pytest -q`: **94 passed** (no count change; pure refactor, no behaviour
    change).
  - `pre-commit run --all-files`: all hooks passed.
- Forward guidance: Next is WP-7 (frontend safety and resilience polish).

### 2026-02-20 - P1 perf: remove O(n) cache-size scan from cleanup_expired_cache
- Scope: `scrobblescope/utils.py`.
- Problem: `cache_size_mb = sum(len(str(v)) for v in REQUEST_CACHE.values()) / ...`
  ran inside `_cache_lock` on every cleanup call, even when debug logging was
  disabled. This O(n) string-serialization of all cached values held the lock
  unnecessarily and added CPU overhead proportional to cache size.
- Fix: removed the `cache_size_mb` line and simplified the debug log to
  `f"Cache status: {cache_count} entries"`. Count-only logging is sufficient
  for operational visibility; size estimation is not a runtime requirement.
- Deviations: none.
- Validation:
  - `pytest -q`: **94 passed** (no count change; no test needed for log format).
  - `pre-commit run --all-files`: all hooks passed.
- Forward guidance: Next P1 item is test boilerplate extraction in
  `test_routes.py` (VALID_FORM_DATA + csrf_app_client fixture).

### 2026-02-20 - P0 fix: delete orphan JOBS entry on thread-start failure
- Scope: `scrobblescope/repositories.py`, `scrobblescope/routes.py`,
  `tests/test_repositories.py`, `tests/test_routes.py`.
- Problem: `create_job()` was called before `start_job_thread()`; on thread-start
  failure the semaphore slot was correctly released by `worker.py`, but the
  `JOBS[job_id]` entry persisted as an orphan until the 2-hour TTL cleanup.
- Fix:
  - Added `delete_job(job_id)` to `repositories.py`:
    `with jobs_lock: JOBS.pop(job_id, None)`.
  - Imported `delete_job` in `routes.py`; called it in the `except` block after
    thread-start failure, before returning the error page.
  - Added 2 tests to `test_repositories.py`:
    `test_delete_job_removes_existing_job`,
    `test_delete_job_on_missing_job_is_noop`.
  - Strengthened existing `test_results_loading_thread_start_failure_renders_error`
    to assert `mock_delete_job.assert_called_once()`.
- Validation:
  - `pytest -q`: **94 passed** (92 pre-existing + 2 new).
  - `pre-commit run --all-files`: all hooks passed.
- Forward guidance: The known orphan-job open risk (SESSION_CONTEXT.md Section 2)
  is now closed. Remaining P1 items: cache_size_mb in `cleanup_expired_cache`,
  and test boilerplate extraction in `test_routes.py`. Next required work package
  is WP-7 (frontend safety and resilience polish).

### 2026-02-20 - doc_state_sync maintenance (remove volatile Last sync commit field)
- Scope: `scripts/doc_state_sync.py`, `.claude/SESSION_CONTEXT.md`.
- Issue: `doc-state-sync-check` pre-commit hook was failing on PR merge to main.
  Root cause: `_build_status_block()` called `git rev-parse --short HEAD` to write
  `Last sync commit: <hash>` into SESSION_CONTEXT.md. On `--check`, the command
  returned the NEW merge commit hash, which did not match the stored hash, causing
  drift detection failure on every merge.
- Fix: Removed `_git_head_short()` function, `subprocess` import, and the
  `Last sync commit` line from `_build_status_block`. The `--check` now validates
  only stable content-level fields (batch number, WP numbers, entry count, newest
  heading). Ran `--fix` to drop the stale `Last sync commit` line from
  SESSION_CONTEXT.md.
- Commit: `cdedd65` fix: remove Last sync commit from doc_state_sync status block.
- Forward guidance: The doc-state-sync-check hook will no longer false-positive on
  merge commits. SESSION_CONTEXT DOCSYNC block is validated on content only.

### 2026-02-20 - WP-6 completed (remove artificial orchestration sleeps)
- Scope: `scrobblescope/orchestrator.py`, `tests/services/test_orchestrator_service.py`.
- Plan vs implementation:
  - Removed all 5 `await asyncio.sleep(0.5)` calls from `_fetch_and_process`. The
    calls were added as a progress-pacing mechanism but served no functional purpose
    and added a fixed 2.5 s latency overhead to every job.
  - All `set_job_progress` calls and their messages are preserved at the same
    progress values (0, 5, 20, 30, 40, 60, 80, 90, 100), so the loading-page
    progress sequence is unchanged from the user's perspective.
  - `asyncio` import retained: `asyncio.Semaphore`, `asyncio.gather`,
    `asyncio.new_event_loop`, and `asyncio.set_event_loop` are still used.
  - Removed two dead `patch("asyncio.sleep", new_callable=AsyncMock)` lines from
    `test_fetch_and_process_cache_hit_does_not_precheck_spotify` and
    `test_fetch_and_process_sets_spotify_error_from_process_albums` in
    `tests/services/test_orchestrator_service.py`. Those patches were no-ops after
    the sleep removals.
- Deviations and why: none. "Gate with debug-only UX flag" option was not needed;
  the plain removal is simpler and all test coverage is already progress-message
  based, not timing based.
- Additions beyond plan: none.
- Validation:
  - `pre-commit run --all-files`: all hooks passed (black, isort, autoflake, flake8,
    trim, end-of-file, doc-state-sync-check).
  - `pytest -q`: **92 passed** (no count change; two dead patches removed,
    no new tests needed).
- Forward guidance: Next work package is WP-7 (frontend safety and resilience
  polish).

### 2026-02-20 - WP-5 completed (enforce registration-year validation server-side)
- Scope: `scrobblescope/routes.py`, `tests/test_routes.py`.
- Plan vs implementation:
  - Added a registration-year guard in `results_loading` immediately after the
    `2002..current_year` bounds check. The guard calls `check_user_exists(username)`
    via `run_async_in_thread` (same helper used by `validate_user`). The result is
    already cached from the blur-validation step, so the call is typically free.
  - If `registered_year` is present and `year < registered_year`, the route
    re-renders `index.html` with an explicit error message citing the registration
    year and the earliest valid year.
  - If the check raises (Last.fm unavailable, network error, etc.), a `WARNING`
    is logged and the route proceeds without blocking the user (fail-open policy).
  - If `registered_year` is `None` (not returned by Last.fm), the check is skipped
    and the route proceeds normally.
  - Updated four existing `results_loading` tests that reach the guard to patch
    `scrobblescope.routes.run_async_in_thread` with a neutral result
    (`{"exists": True, "registered_year": None}`) to avoid live network calls.
  - Added four new tests to `tests/test_routes.py`:
    - `test_results_loading_year_below_registration_year_rejected`
    - `test_results_loading_year_at_registration_year_allowed`
    - `test_results_loading_registration_check_unavailable_proceeds`
    - `test_results_loading_no_registered_year_proceeds`
- Deviations and why: none. Fail-open on service unavailability was the intended
  design from the WP-5 spec (client-side validation already covered the common
  case; server-side guard adds defense-in-depth without blocking on transient errors).
- Validation:
  - `pre-commit run --all-files`: all hooks passed (black, isort, autoflake, flake8,
    trim, end-of-file, doc-state-sync-check).
  - `pytest -q`: **92 passed** (88 pre-existing + 4 new).
- Forward guidance: Next work package is WP-6 (remove or gate artificial
  orchestration sleeps).

### 2026-02-20 - WP-4 completed (harden app secret and startup safety)
- Scope: `app.py`, `tests/conftest.py`, `tests/test_app_factory.py` (new), `.env.example`, `README.md`.
- Plan vs implementation:
  - Added `_KNOWN_WEAK_SECRETS = frozenset({"dev", "changeme_in_production", ""})` and `_MIN_SECRET_LENGTH = 16` constants in `app.py`.
  - Added `_validate_secret_key(secret_key: str, is_dev_mode: bool) -> None` in `app.py`. Logic: if key is falsy, in weak set, or shorter than 16 chars -> "weak". In production (`debug_mode=False`): raises `RuntimeError("Refusing to start: ...")`. In dev mode (`DEBUG_MODE=1`): logs `WARNING "SECRET_KEY is missing or insecure. ..."`.
  - Updated `create_app()` to read `_raw_secret = os.getenv("SECRET_KEY", "")`, call `_validate_secret_key(_raw_secret, debug_mode)`, then set `application.secret_key = _raw_secret or "dev"`. "dev" is the dev-mode fallback; in production, `_validate_secret_key` raises before it can be used.
  - `tests/conftest.py` updated: added `import os` + `os.environ.setdefault("SECRET_KEY", "test-only-secret-key-min-16chars!!")` before `from app import create_app`. This seeds the guard before `app.py`'s module-level `create_app()` call (which runs at import time).
  - New `tests/test_app_factory.py` with 7 tests: production-fail on missing/dev/changeme/too-short keys; dev-mode warning; strong-key success in both modes.
  - `.env.example` `SECRET_KEY` comment updated to say "REQUIRED in production. Startup fails if missing or set to placeholder."
  - `README.md` setup step 4 comment updated from "Recommended" to "Required in production" with note that `DEBUG_MODE=1` suppresses the check for local dev.
- Validation:
  - `pre-commit run --all-files`: all hooks passed (black reformatted `app.py` quote style on first run; clean on second).
  - `pytest -q`: **88 passed** (81 pre-existing + 7 new).
- Commit: `eb13a27` feat: refuse startup on weak SECRET_KEY in production.
- Forward guidance: Next work package is WP-5 (enforce registration-year validation server-side).

### 2026-02-20 - WP-1 correctness fix (slot leak on Thread.start failure)
- Scope: `scrobblescope/routes.py`, `tests/test_routes.py`.
- Issue: WP-1 post-audit check found that `acquire_job_slot()` in `results_loading` was not guarded against failure of `Thread.__init__` or `Thread.start()`. If either raises (e.g. `OSError` under OS-level thread exhaustion), the slot is permanently consumed because `background_task`'s `finally` block never runs. This violates WP-1's acceptance criterion "no leaked active slots after worker exceptions."
- Fix:
  - Added `release_job_slot` to imports in `routes.py`.
  - Wrapped `threading.Thread(...)` and `task_thread.start()` in try/except; on exception: `release_job_slot()`, `logging.exception(...)`, return `index.html` with error message.
  - Added `test_results_loading_thread_start_failure_releases_slot`: patches `Thread` to raise `OSError`, asserts slot is released and index re-rendered.
- Validation:
  - `pre-commit run --all-files`: all hooks passed.
  - `pytest -q`: 77 passed.
- Also: added "callers must not mutate" to `get_cached_response` docstring (latent mutable-reference risk; no active bug since no caller mutates the returned object).

### 2026-02-20 - worker.py architectural decision + product roadmap + CSRF coverage expansion

- Scope: Documentation updates only (`.claude/SESSION_CONTEXT.md`, `EXECUTION_PLAYBOOK_2026-02-11.md`). No runtime code changes yet.
- Decisions made:
  - **Product roadmap confirmed:** Two additional background task types are planned -- "top songs" (Last.fm + possibly Spotify, separate background task/results flow) and "listening heatmap" (Last.fm only, last 365 days, lighter task). This means the `results_loading` acquire->Thread->release pattern will be needed by at least 3 routes.
  - **worker.py chosen as home for concurrency lifecycle:** With multiple background task types incoming, keeping the semaphore and thread-start boilerplate in `repositories.py` would require each new route to duplicate the `acquire -> try Thread.start -> except release` block. A new `scrobblescope/worker.py` leaf module (imports `config` only) will own `_active_jobs_semaphore`, `acquire_job_slot()`, `release_job_slot()`, and `start_job_thread(target, args=())`. `repositories.py` becomes pure job state CRUD. `start_job_thread()` encapsulates the full try/start/except/release pattern for all callers.
  - **Refactor must precede the 3-commit save-state:** WP-1 originally placed the semaphore in `repositories.py`. The worker.py refactor corrects this before committing; the WP-1 commit will reflect the final architecture.
- CSRF test coverage expansion (also completed this session, before context compaction):
  - Initial WP-3 implementation added 2 CSRF tests covering only `/results_loading`.
  - Expanded to 6 total CSRF tests covering all 4 POST routes:
    - `test_csrf_rejects_post_without_token` (-> `/results_loading` 400)
    - `test_csrf_accepts_post_with_valid_token` (-> `/results_loading` 200)
    - `test_csrf_rejects_results_complete_without_token` (-> 400)
    - `test_csrf_rejects_unmatched_view_without_token` (-> 400)
    - `test_csrf_rejects_reset_progress_without_token` (-> 400)
    - `test_csrf_accepts_reset_progress_with_header_token` (-> `/reset_progress` XHR path with `X-CSRFToken` header, 200)
  - Total tests after expansion: **81 passing**.
- Pending implementation (next agent actions in order):
  1. Create `scrobblescope/worker.py` with semaphore, `acquire_job_slot()`, `release_job_slot()`, `start_job_thread()`.
  2. Remove semaphore/slot functions from `scrobblescope/repositories.py`.
  3. Update imports in `routes.py` and `orchestrator.py` to use `worker`.
  4. Update patch targets in `test_routes.py` and `test_orchestrator_service.py` from `scrobblescope.routes.acquire_job_slot` / `scrobblescope.orchestrator.release_job_slot` -> `scrobblescope.worker.*`.
  5. Run `pre-commit run --all-files` and `pytest -q` (must stay at 81 passing).
  6. Make 3 separate commits: WP-1, WP-2, WP-3.
- Validation: N/A (doc-only session-end update).
- Forward guidance:
  - worker.py is a leaf module -- it must NOT import from `repositories`, `routes`, `orchestrator`, or any higher module (would create cycles).
  - `start_job_thread()` should release the slot and raise on `Thread.start()` failure so routes get a clean exception to handle (mirrors the current try/except pattern in `routes.py`).
  - After the 3 commits are made, next work package is WP-4 (harden app secret and startup safety).

### 2026-02-19 - Fly cold-start recovery validation completed (app + Postgres DB)
- Scope: operational validation of deployed services and documentation refresh (`.claude/SESSION_CONTEXT.md`, `PLAYBOOK.md`).
- Plan vs implementation:
  - Confirmed both machines were started (`fly status -a scrobblescope`, `fly status -a scrobblescope-db`).
  - Forced cold state by stopping both machines:
    - `fly machine stop 807339f1595248 -a scrobblescope`
    - `fly machine stop 8e7ed9ad205118 -a scrobblescope-db`
  - Verified both reported `State: stopped` via `fly machine status`.
  - Triggered one end-to-end request:
    - `venv\Scripts\python scripts/smoke_cache_check.py --base-url https://scrobblescope.fly.dev --username flounder14 --year 2025 --runs 1 --timeout-seconds 180`
  - Verified smoke run completion and auto-start behavior for both app and DB machines.
  - Rechecked DB health until all checks passed (`pg`, `role`, `vm`).
- Deviations and why:
  - No code changes were required; this was an operational verification step requested by the owner.
- Validation:
  - Smoke output: `elapsed=18.75s`, `db_cache_enabled=True`, `db_cache_lookup_hits=247`, `db_cache_persisted=0`, `spotify_matched=247`, message `Done! Found 57 albums matching your criteria.`
  - Post-run status: app machine `started`, DB machine `started`, DB checks all passing.
- Forward guidance:
  - Keep this cold-start check as a regression smoke pattern after infra/config changes.
  - If cold-start latency grows, tune DB wake-up retry knobs (`DB_CONNECT_MAX_ATTEMPTS`, `DB_CONNECT_BASE_DELAY_SECONDS`) and/or Fly machine warmness settings.

### 2026-02-19 - Context reconciliation completed (docs parity + cache fallback logging classification)
- Scope: `.claude/SESSION_CONTEXT.md`, `PLAYBOOK.md`, `scrobblescope/cache.py`, `tests/test_repositories.py`.
- Plan vs implementation:
  - Re-verified playbook/session claims against the active repo for `init_db.py`, thread model, and cache fallback behavior.
  - Refreshed stale status fields (latest commit snapshot, app.py line count, and current runtime notes).
  - Updated `_get_db_connection()` to log explicit fallback categories:
    - `asyncpg-missing`
    - `missing-env-var`
    - `db-down`
  - Extended DB helper tests to assert those log categories are emitted on each path.
- Deviations and why:
  - No keep-alive thread was added to `app.py`; this is intentional because the current architecture uses per-job daemon worker threads from `results_loading` and avoids additional idle background loops.
- Validation:
  - `venv\Scripts\python -m pytest tests\test_repositories.py -q`: **16 passed**.
  - `venv\Scripts\python -m pytest tests -q`: **66 passed** (2 deprecation warnings from aiohttp connector behavior on Python 3.13.3).
- Forward guidance:
  - Keep Section 2 and `.claude/SESSION_CONTEXT.md` synchronized whenever runtime snapshots (line counts, branch/commit status, logging behavior) change.

### 2026-02-14 - Repository hygiene completed (historical docs archive + README refresh)
- Scope: `docs/history/` (new folder), historical markdown moves, `PLAYBOOK.md`, `README.md`.
- Plan vs implementation:
  - Moved historical docs from repo root into `docs/history/`:
    - `AUDIT_2026-01-10.md`
    - `AUDIT_2026-02-11_IMPLEMENTATION_REPORT.md`
    - `CHANGELOG_2026-01-04.md`
    - `CHANGELOG_2026-02-10.md`
    - `OPTIMIZATION_SUMMARY.md`
    - `PERFORMANCE_TIMING.md`
    - `Refactor_Plan.md`
    - `TEMPLATE_REFACTOR_SUMMARY.md`
  - Updated playbook references to `docs/history/AUDIT_2026-02-11_IMPLEMENTATION_REPORT.md`.
  - Refreshed `README.md`:
    - run instructions now show `python app.py` (recommended) and `python run.py` (optional launcher)
    - project structure updated to current modular layout + `docs/history/`
    - roadmap/status text updated to reflect current post-refactor state
- Deviations and why:
  - Keep a shim at `EXECUTION_PLAYBOOK_2026-02-11.md` to preserve a stable handoff entrypoint.
- Forward guidance:
  - Keep new planning/audit/changelog docs in `docs/history/` unless a document is an active operator runbook.
  - Keep playbook and session-context docs at predictable top-level locations for fast bootstrap.

### 2026-02-14 - Cache wake-up hardening completed (DB connect retry/backoff + docs refresh)
- Scope: `scrobblescope/cache.py`, `tests/test_repositories.py`, `PLAYBOOK.md`, `.claude/SESSION_CONTEXT.md`, `README.md`.
- Plan vs implementation:
  - Added exponential-backoff DB connection retries in `_get_db_connection()` to reduce false cache bypass during Fly Postgres wake-up windows.
  - Added two DB helper tests:
    - retry-then-success path
    - retry-exhaustion path
  - Updated existing connect-failure test to force single-attempt behavior (`DB_CONNECT_MAX_ATTEMPTS=1`) for deterministic assertions.
  - Refreshed handoff docs for the new test count and operational behavior.
- Deviations and why:
  - No orchestration/routing behavior changes were needed; hardening was isolated to cache connection setup and DB helper tests.
- Additions beyond plan:
  - Added env-tunable retry knobs:
    - `DB_CONNECT_MAX_ATTEMPTS` (default `3`)
    - `DB_CONNECT_BASE_DELAY_SECONDS` (default `0.25`)
  - Live Fly verification confirmed:
    - app cache hits persisted after DB stop/start
    - DB app `scrobblescope-db` uses `FLY_SCALE_TO_ZERO=1h`, explaining suspended/stopped state after idle periods.
- Validation:
  - `venv\Scripts\python -m pytest tests\test_repositories.py -q`: **16 passed**.
  - `venv\Scripts\python -m pytest tests -q`: **66 passed**.
  - `venv\Scripts\pre-commit run --all-files`: all hooks passed.
  - `venv\Scripts\python scripts/smoke_cache_check.py --base-url https://scrobblescope.fly.dev --username flounder14 --year 2025 --runs 2`: **PASS** (`db_cache_enabled=True`, `db_cache_lookup_hits=247`).
- Forward guidance:
  - If first-request latency after idle is a concern, either increase retry knobs or adjust/remove DB `FLY_SCALE_TO_ZERO`.
  - Keep periodic smoke checks as operational validation for cache persistence and warm-hit behavior.
  - Resolve DB app staged secrets drift (`fly secrets deploy -a scrobblescope-db`) to avoid config ambiguity.

### 2026-02-14 - Frontend responsiveness polish completed (toggle placement + mobile table scaling)
- Scope: `static/css/index.css`, `static/css/results.css`, `static/css/loading.css`, `static/css/unmatched.css`, `static/css/error.css`, `templates/results.html`.
- Plan vs implementation:
  - Standardized dark-mode toggle to a compact fixed bottom control across all page CSS bundles.
  - Improved `index.html` mobile fit by tightening spacing, typography, and card/logo sizing at mobile breakpoints.
  - Improved `results.html` mobile readability by shrinking table density, making actions stack cleanly, and reducing album-art footprint.
  - Added `results-table` class in template for targeted responsive behavior.
  - Centered decade pills in `index` filter UI.
- Deviations and why:
  - To improve fit on common phones, responsive rules were applied up to `max-width: 767.98px` for index/results rather than only `575.98px`.
- Validation:
  - `venv\Scripts\python -m pytest tests -q`: **66 passed**.
  - `venv\Scripts\pre-commit run --all-files`: all hooks passed.
- Forward guidance:
  - If users still report table crowding on very small devices, next step is card-style row rendering for results instead of a dense 5-column table.
  - Consider extracting shared toggle CSS into one common stylesheet to reduce cross-file duplication.

### 2026-02-14 - Post-Batch-8 hardening completed (low-severity gap closure + test layout split)
- Scope: `tests/test_routes.py`, `tests/conftest.py`, `tests/helpers.py` (new), `tests/services/` (new split files), `EXECUTION_PLAYBOOK_2026-02-11.md`, `.claude/SESSION_CONTEXT.md`, `README.md`.
- Plan vs implementation:
  - Closed previously identified low-severity gaps:
    - Added direct route tests for `/unmatched_view` (missing `job_id`, missing job, success render path).
    - Added explicit tests for app-level 404 and 500 handlers.
  - Reduced test coupling to `conftest.py` internals:
    - Moved shared constants/mock helpers into `tests/helpers.py`.
    - Updated tests to import from `tests.helpers` rather than `conftest`.
  - Split monolithic service test file:
    - Removed `tests/test_services.py`.
    - Added `tests/services/test_lastfm_service.py` (4 tests).
    - Added `tests/services/test_spotify_service.py` (3 tests).
    - Added `tests/services/test_orchestrator_service.py` (10 tests).
- Deviations and why:
  - No runtime code changes were required. This was a test architecture and coverage hardening pass only.
  - Added one extra test category beyond the initial gap list (500 handler integration path) because this was explicitly untested and low effort/high confidence.
- Validation:
  - `venv\Scripts\python -m pytest tests -q`: **64 passed**.
  - `venv\Scripts\pre-commit run --all-files`: all hooks passed.
- Forward guidance:
  - Subpackage migration should be sequenced **after** the next feature-heavy batch set (Batch 9+) stabilizes, not before. Keep current flat module layout while churn is high; cut to subpackages once contracts settle.
  - Keep route-handler coverage and helper-module pattern as baseline for future test additions.

### 2026-02-13 - Operational config fix (Fly machine autostop)
- Scope: `fly.toml`.
- Issue:
  - Fly log showed autostop with `0 out of 1 machines left running` because `min_machines_running` was set to `0`.
- Change:
  - Updated `[http_service] min_machines_running = 1` to keep one machine warm.
- Notes:
  - This log means capacity scaling, not cache overflow.
  - In-memory caches (`REQUEST_CACHE`, `JOBS`) live in RAM on the app VM and are lost on machine stop/restart.
  - Persistent Spotify metadata cache lives in Fly Postgres (`spotify_cache`) via `DATABASE_URL`.
