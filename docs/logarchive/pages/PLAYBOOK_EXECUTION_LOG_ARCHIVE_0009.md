<!-- DOCSYNC:ARCHIVE-PAGE v1 -->
# PLAYBOOK_EXECUTION_LOG_ARCHIVE -- page 0009

### 2026-08-21 - Dependency advisories filed as F-B21-3 (side-task)

- Scope: filed one finding from the first Quality Gate run that exercised the
  Tailwind steps. No runtime code and no dependency changed.
- Plan vs implementation: pushing `bc9ba80` ran the gate for the first time
  since WP-1 landed. It passed, and "Verify committed Tailwind CSS" succeeded
  on Linux, so the committed digest reproduces in CI and the WP-1 platform
  detection works there. The same run's `pip-audit` step reported 115
  advisories across 12 packages and exited 1 without failing the gate, which
  is its documented `continue-on-error` disposition. Investigation found six
  packages in `requirements.txt` that nothing imports, including a
  `pypdf`/`pdf2image`/`pillow` cluster. The owner asked whether those served
  the JPEG export; they do not. That export is client-side `html2canvas` in
  `static/js/results.js:178-266`. All six unimported packages entered in the
  initial `0ea2313` commit rather than with a feature. The owner has poppler
  installed locally, so `pdf2image` can run on the development machine, but
  not in production: the `Dockerfile` is a bare `python:3.13-slim` with no
  system-package installs.
- Deviations: none. No dependency was upgraded or removed. Dependency changes
  are code and belong in a code batch, not a docs commit.
- Validation: `pytest -q` -- **633 passed**, 3 warnings. Quality Gate run
  32444711411 passed in 1m12s.
- Forward guidance: WP-2 is next. `F-B21-3` records a suggested shape --
  split runtime from developer requirements, drop unimported packages, then
  upgrade the outbound HTTP libraries -- but the owner has not ruled on it.

### 2026-08-20 - F-B21-2 deferred to the locked WP-2 remedy (side-task)

- Scope: corrected one finding that prescribed a fix competing with an
  owner-locked decision. No runtime code changed.
- Plan vs implementation: `F-B21-2` was filed from the WP-1 review without
  reading `BATCH21_DEFINITION.md:186-204`, which already prescribes WP-2's
  remedies. It told a reader to layer Bootstrap; the locked decision instead
  moves the Bootstrap link into a per-page block so each template loads
  exactly one framework stylesheet, removing the collision rather than
  re-ordering it. The finding now defers to the definition and says so. Its
  `data-theme` seam likewise points at the locked `theme.js` dual-write. The
  defect descriptions are kept, because they record why those decisions
  matter; only the competing prescription is gone.
- Deviations: none. The batch definition was not edited. A finding must not
  outrank the batch contract, so the finding moved.
- Validation: `pytest -q` -- **633 passed**, 3 warnings.
- Forward guidance: WP-2 is next and closes `F-B21-2`. Check a finding against
  the active batch definition before filing a remedy in it.

### 2026-08-20 - README roadmap reconciled with FINDINGS (side-task)

- Scope: removed one stale roadmap item that contradicted an open finding, and
  retitled the finding it pointed at. No runtime code changed.
- Plan vs implementation: the README roadmap still asked a reader to
  consolidate Bootstrap onto one CDN provider. `F-B20-3` already records that
  remedy as dead, because Batch 21 removes Bootstrap at WP-8 and resolves the
  split by elimination. Two live documents disagreed, and the README is the one
  a newcomer reads first. The roadmap line now names the real disposition.
  `F-B20-3`'s heading described the dead remedy rather than the defect; it now
  reads "Bootstrap loads from two CDN providers". Every citation of it is by
  F-ID, so no reference breaks.
- Deviations: none. Three other roadmap items were checked and left alone.
  The integration test (`F-LOAD-2`) and the `ENTRY_BATCH_RE` tightening
  (`F-DOCSYNC-1`) have not been done, so their unchecked boxes are correct.
  `tests/test_routes.py` reaches the three endpoints only under mocks, and no
  test covers the whole chain. `parser.py:37` is unchanged.
- Validation: `pytest -q` -- **633 passed**, 3 warnings.
- Forward guidance: WP-2 is next. Note `F-DOCSYNC-1` may overstate the problem
  -- the current regex already requires the parenthesised `(Batch N WP-N)`
  form, so a failing test should justify the change before anyone makes it.

### 2026-08-20 - Root hygiene: config verdict recorded, banners withdrawn (side-task)

- Scope: recorded the root config-file verdict in the document that owns
  deploys, and corrected one false self-description. No runtime code changed.
- Plan vs implementation: the owner rejected the audience-banner scheme in the
  local root-hygiene plan. Its two-label vocabulary restated what the
  `AGENTS.md` Document Roles table and `docs/AGENT_DOC_MAP.md` already own,
  and its rule that no file claims both audiences is false for files that are
  both. `DEVELOPMENT.md` was the worked example: it called itself explanatory
  documentation only while owning the Frontend Asset Build commands that other
  documents cite. That sentence is narrowed rather than banner-stamped.
  `DEPLOY.md` gains "Where the config lives"; `fly.toml` gains a pointer
  comment above its empty `[build]`; the README tree names the co-location
  instead of leaving `Dockerfile` uncommented.
- Deviations: the banner steps, the `AGENTS.md` audience rule, and the README
  audience split are **withdrawn, not deferred**. Verification also corrected
  an earlier claim that the banner would strand agents:
  `BATCH21_DEFINITION.md:448-450` already binds WP-2 through WP-7 to run
  `tailwind_build.py`, so no agent depended on `DEVELOPMENT.md` for the
  obligation. Only the fuller procedure, including watch mode and the worktree
  caveat, lives there.
- Validation: `pytest -q` -- **633 passed**, 3 warnings.
- Forward guidance: WP-2 is next. Nothing from this side task blocks it.

### 2026-08-20 - Batch 21 WP-1 test-count authority addendum (side-task)

- Scope: records the post-WP-1 measured suite inventory for docsync's
  same-day source ordering. No runtime implementation changed.
- Plan vs implementation: the new current-batch WP-1 entry remains the owner
  of toolchain evidence. This live addendum supplies its later full-suite
  result because same-date side-task entries take precedence over
  current-batch entries in docsync's authority ordering.
- Deviations: none.
- Validation: `pytest -q` -- **633 passed**, 3 warnings.
- Forward guidance: owner review of the WP-1 commit remains first; the
  root-hygiene side task follows, then WP-2.

### 2026-08-20 - Agent document map added; HANDOFF_PROMPT trimmed (side-task)

- Scope: the owner asked for an instructional that lets an agent other than
  Claude navigate the documentation set -- including the audit and SWE
  documents -- and understand why each document exists. Added
  `docs/AGENT_DOC_MAP.md` and registered it in the `AGENTS.md` Document Roles
  table. Documentation only; no runtime code changed.
- Plan vs implementation: as planned. The map routes rather than summarises.
  It names the owner of each fact and links to it, so it adds no copy that a
  later edit can contradict (`AGENTS.md` Anti-duplication rule). Sections:
  the one-owner rule and why it exists, where to start, the document groups,
  the human-facing documents, how to read an audit, how to read a finding,
  seven navigation traps, the pre-change gates, and the tie-break order when
  two documents disagree. It sits under `docs/` rather than the repository
  root, because a twelfth root Markdown file would worsen the problem the map
  exists to solve, and it is marked optional and outside the bootstrap set so
  it does not inflate the cold-start read. 264 lines, under the 370-line
  largest peer in `docs/`.
- Audit guidance is the part with no prior owner: the charter to report to
  findings to log-entry lifecycle, why a retired charter is kept, why a dated
  report is never edited in place, and that a report is a measurement of one
  day rather than current truth. The SWE report's own "Owner review" section
  is cited as the worked example of an appended correction.
- Owner request mid-task, and the reason it changed shape: delete
  `HANDOFF_PROMPT.md`. That is not a documentation-only delete. The file is
  pinned into the commit gate at `scripts/docsync/cli.py:26` and
  `scripts/docsync/integrity.py:51`. `cli.py:88` loads every
  `LIVE_DOCUMENT_PATHS` entry through `_read_lines`, which raises `SyncError`
  on a missing file and maps to exit 2, and the `doc-state-sync-check` hook
  runs `--check` with `always_run: true`. Deleting the file alone would fail
  every commit in the repository until `cli.py`, `integrity.py`,
  `tests/conftest.py:149` and four assertions in
  `tests/test_docsync_integrity.py` changed with it. The owner chose to trim
  the file instead of deleting it.
- Trim: `HANDOFF_PROMPT.md` went from 66 to 46 lines. Removed three sections
  that carried no requirement of their own and only named an `AGENTS.md`
  section: validation gates, commit discipline, and anti-patterns. Every
  subject those sections named survives in the new opening paragraph, checked
  against the removed text one item at a time per Anti-Pattern 12. The two
  unique parts are untouched: the post-read verification and the handoff
  checklist. Section numbers were replaced with names, so no later edit can
  leave a stale "Section 4)" citation behind. `DEVELOPMENT.md:74-78` already
  claimed the file held only those two things, so the trim closes an existing
  drift rather than creating one.
- Deviations: two stale claims corrected in the same commit, both left behind
  by the 2026-08-20 audit commits. `BATCH21_DEFINITION.md:3` still read that
  the F-SWE-1 audit "comes next" after PR #170; the audit ran on 2026-08-20.
  The `README.md` documentation tree still described
  `docs/SWE_AUDIT_CHARTER.md` as "Standing audit scope and method"; the
  charter is retired. The same tree gained a row for the new map, because it
  enumerates the contents of `docs/`.
- Validation: `pytest -q` **590 passed** (unchanged; no code touched);
  `pre-commit run --all-files` all hooks passed;
  `python scripts/doc_state_sync.py --check` exit 0 with the expected
  active-root `BATCH21_DEFINITION.md` warning. Every tracked Markdown file
  was checksummed before and after the pre-commit run and compared, because
  that hook has twice reverted files nobody edited, once into a commit.
- Forward guidance: unchanged. The F-SWE-2 fix is still the next action. It
  is a code commit and it moves the test count off 590.
- **Later same-day test-count addendum:** the F-SWE-2 current-batch entry above
  records the subsequent code change and owns its implementation details. Its
  full-suite result was `pytest -q` -- **591 passed**. The earlier 590 result
  in this entry remains point-in-time evidence; this pointer supplies the
  later same-date count to docsync's live-side-first authority order.

### 2026-08-20 - F-SWE-1 SWE principles audit executed (side-task)

- Scope: executed `docs/SWE_AUDIT_CHARTER.md` against `1994673`, whose
  runtime code is byte-identical to `main` at `bb187ae` -- the five commits
  between them are documentation only. Read-only audit; all 130 cells
  (13 graded modules x 10 principles) filled in one session. Report:
  `docs/history/reports/SWE_PRINCIPLES_AUDIT_2026-08-20.md`.
- **Verdict: migration blocked by F-SWE-2**, per charter Section 6 -- a
  net-new correctness defect in `orchestrator.py`, which WP-7 modifies.
  `orchestrator.py:70-71` builds the listening-year window from naive
  datetimes, so the window shifts by the local offset of the host: measured
  at five hours on this machine. It is the same defect F-B19-6 fixed in
  `heatmap.py`; `git show --stat ccb000f` confirms that fix touched heatmap
  and its tests only, and the twin was never revisited. Production is
  unaffected because the Fly.io container runs UTC. Every non-UTC host is
  affected, including local dev, so local checks of album results have been
  running against a shifted window.
- **Owner decisions, same day.** F-SWE-2: fix, do not waive -- it lands as
  its own commit before WP-1 and moves the test count. F-SWE-3: rescoped
  from P1 to P2, and the audit was partly wrong. It filed the
  `No Spotify match` reason as a user-facing mislabelling; that framing does
  not hold, because thousands of Last.fm-scrobbled albums genuinely have no
  Spotify release, so the label is accurate for the ordinary case. What
  survives is narrower and independent of labelling: `spotify.py:67-68`
  marks every non-200, non-429 response terminal, so a 500 ends the attempt
  loop after one try while `SPOTIFY_SEARCH_RETRIES` is 3. The related UI
  need -- the unmatched modal and page should say plainly that an album had
  no Spotify match -- is already WP-7 scope
  (`BATCH21_DEFINITION.md:297-308`), not new work.
- Grades: 74 A, 28 B, 8 C, 2 D, 18 N/A. The weakest principle is Fail Fast,
  holding five of the eight C grades and only two A grades across 13
  modules. The failures share one shape: the code catches a problem and
  discards what the problem was.
- Six net-new findings, F-SWE-2 to F-SWE-7. Every one of the ten C and D
  cells carries a disposition; two map to open F-B20-2 rather than becoming
  new entries. Each finding was verified by running the code, not by reading
  it -- the TTL renewal, the Spotify retry bypass, the unreachable API-key
  check and the heatmap misattribution were each reproduced.
- Test vacuity: measured, not judged. Each of the 81 top-level functions in
  the graded modules was replaced in turn with a raise, in a copy of the
  tree outside the repository, and the 237 runtime tests were run against
  each mutation. Every deletion was caught, so there is no vacuity finding.
- Broad catches: all 17 were read in context and judged, which F-MAS-4 never
  did. Fifteen are justified. The two that are not are both in F-SWE-5, and
  both are catches that report a cause they never established.
- F-B21-1 keeps its recorded P1 disposition. The gate covers net-new
  findings only, so the audit did not re-triage it and it does not block
  WP-1.
- Deviations: F-SWE-1 moved from the P1 section to Resolved this batch, and
  F-SWE-3 from P1 to P2 -- the charter asked for neither move, but leaving
  either where it was would have made the section heading false.
- **Tooling hazard hit twice, worth recording.** `pre-commit run --all-files`
  stashes unstaged changes and restores them afterwards. That cycle reverted
  files nobody had edited: first `docs/architecture/development-cycle.md`
  and `top-albums-sequence.md` back to a pre-PR-#171 state, then `PLAYBOOK.md`
  itself back to a pre-PR-#170 state, dropping this very entry. Every hook
  reported `Passed`. The first was caught at staging because AGENTS.md
  requires staging by name; the second reached commit `a34c57f` and was
  repaired in the follow-up commit. Check `git status` before and against
  after every `--all-files` run, and compare file mtimes against the files
  you actually edited.
- Validation: `pytest -q` -- 590 passed, unchanged, as expected for a
  docs-only change. `pre-commit run --all-files` and
  `doc_state_sync.py --check` both pass, the latter with the expected
  active-root `BATCH21_DEFINITION.md` warning.
- Forward guidance: apply the F-SWE-2 fix as its own commit, then WP-1. Root
  hygiene stays deferred until after WP-1.

### 2026-08-19 - Batch 21 preflight: F-SWE-1 charter and WP gates amended (side-task)

- Scope: owner preflight review before WP-1, raised as six criticisms of
  `docs/SWE_AUDIT_CHARTER.md` and an eight-row table of weak WP gates. Two
  verification agents checked every claim against the files before any edit.
  All six charter criticisms held. Two of the batch claims did not.
- Verification of the owner report:
  - Confirmed: the charter named five docsync modules when the directory has
    seven (`integrity.py`, 474 lines, unnamed) and its LOC figure was stale
    for the five it did name; the differential baseline was a closed ID list
    omitting F-B21-1, F-DATA-1, F-WORKTREE-3/4/5, F-DOCSYNC-6/7 and never
    referenced `FINDINGS_ARCHIVE.md`; A/B/C/D was defined nowhere in the
    repository; the matrix was 190-210 cells with explicit permission to cut
    modules; no severity or stop condition existed anywhere, so finishing the
    audit was the same as passing it; and the post-Batch-21 frontend audit
    was permissive ("can"), not required.
  - Corrected: the excluded set is a proper subset of what Batch 21 rewrites,
    not equal to it -- WP-7 modifies `routes.py` and `orchestrator.py`, which
    are in scope, so those grades also expire at WP-7. The charter never
    addressed that; it now does.
  - Refuted: the claimed AGENT_NOTES-versus-definition contradiction over the
    drift hook. `AGENT_NOTES.md` requires the CI-fetch *decision* at WP-1;
    the definition deferred the *hook* to WP-8. Both could hold. The real
    defect was quieter -- no WP-1 criterion required the decision to be
    recorded, so nothing enforced it.
- Root cause neither side had named: the batch validation gate is three
  Python commands, and pre-commit excludes `static/` and `templates/`. A work
  package could rewrite every template and stylesheet with a fully green
  gate, in a batch that is nothing but template and stylesheet rewriting.
- Plan vs implementation:
  - Charter: 13 graded modules enumerated by name (130 cells, `__init__.py`
    excluded by a stated empty-module rule); docsync and `scripts/dev/`
    excluded with reasons rather than left ambiguous; provenance block
    naming branch, SHA and clean state; symbol-based hotspot discovery
    replacing hardcoded line numbers and counts; baseline widened to the
    whole finding corpus plus the archive and every report from 2026-02 on;
    A/B/C/D rubric with the B/C line defined as exception-versus-pattern;
    Boy Scout window fixed at commits since the February audits; a
    resolved-finding branch for C/D cells; a migration-blocking severity
    policy with a one-line verdict required in the report; an instruction to
    retire the charter at close. The budget escape hatch is withdrawn.
  - Batch 21: new `scripts/dev/frontend_gate.py` added as a fourth gate
    command at WP-2 and grown one page per WP, covering stylesheet
    isolation, computed theme tokens in both themes, theme persistence,
    self-hosted font loading, CSV/JPEG export assertions, and headline
    wrapping. The `tailwind-css-drift` hook moved from WP-8 to WP-2, with
    the `always_run` / `pass_filenames` requirement that AGENT_NOTES gap 2
    had already identified and the definition had not carried. Targeted
    criteria added to WP-3 (keyboard and touch reachability for the CSS-only
    hints, label associations, validation parity), WP-4 (both state machines
    including retryable and non-retryable failures), WP-7 (split into a
    backend contract commit and a UI commit), and WP-8 (required frontend
    and accessibility audit, deterministic Bootstrap-removal grep, recorded
    lint disposition). Browser floor documented; `.dark-mode` retirement
    given an owner; criterion 9 reconciled with the per-WP docsync check.
  - FINDINGS.md: F-STYLE-1 (prose legibility, explicitly never a gate) and
    F-STYLE-2 (docstring convention, the black/flake8 line-length
    disagreement, and the unwritten Ruff plan) added. F-SWE-1 corrected --
    it claimed the charter scoped "Python only until Batch 21 ships", a
    commitment the charter never made.
  - AGENTS.md: the F-ID source-tag list named five tags while nine are in
    use. `SWE`, `WORKTREE`, `DATA` and `STYLE` added, and the list is now
    declared complete so the next coined tag gets documented.
- Deviations: the drift hook landed at WP-2 rather than the WP-1 the owner
  proposed. WP-1 changes no template, so nothing consumes the compiled CSS
  until WP-2; WP-2 is the first point where drift can ship.
- Independent review of the amended charter, same day, and the fixes it drove:
  - The migration gate did not say whether it covered existing findings. Read
    the wide way, F-B21-1 blocks WP-1 today -- a resource-release defect in
    `orchestrator.py`, which WP-7 modifies. The gate is now scoped to net-new
    findings in terms, F-B21-1 is named as the case that forces the
    distinction, and an audit that thinks an existing finding should block
    must recommend rather than act.
  - The A/B/C/D rubric graded by frequency ("one place is B, several is C")
    while its own table graded by cost. One leak can be C; five contained
    exceptions can stay B. Rewritten to grade cost, not count. The
    "when torn, over-raise" instruction is deleted -- it contradicted
    Section 4's rule that the audit's value is not volume.
  - Resolved and no-action findings shared one rule. Split: a recurred
    resolved defect earns a new finding; an unchanged no-action rationale
    does not; materially changed assumptions do, explaining the delta.
  - Provenance permitted grading a dirty tree, which no SHA can reproduce.
    A clean worktree is now required before grading starts.
  - The hotspot command was `awk '...{...}'` -- a placeholder that could not
    run, and a poor Python parser besides. Replaced with a tested `ast`
    script in a new Section 5c, deliberately at the left margin: a heredoc
    terminator indented inside the numbered list fails with
    `IndentationError`, which was verified rather than assumed.
  - Boy Scout used `git log`, which lists commits without showing what they
    left behind. Now `git log -p`, with an instruction to read the patches.
  - "Weakest principle repo-wide" overclaimed: the audit excludes the
    frontend, both script directories, and tests as graded subjects. Scoped
    to the audited runtime modules.
  - Cell arithmetic hardcoded 130 in three places while Section 3 allowed the
    principle count to change. All three now derive from the live count.
  - One review point was stale, not wrong: the claim that WP-8 defines no
    frontend principles audit. It does, in this commit's parent -- the
    reviewer was reading `origin/main`, because the amendment is committed
    locally and deliberately unpushed.
- Validation: `pytest -q` -- **590 passed**. `pre-commit run --all-files` --
  all hooks pass. `doc_state_sync.py --check` -- exit 0 with the expected
  root BATCH warning.
- Forward guidance: execute the amended charter against current `main` and
  publish the migration verdict before WP-1 starts. The verified root-hygiene
  plan (audience banners, README tree, DEPLOY.md) is deferred until after
  WP-1 by owner decision; its line numbers will need re-checking.

### 2026-08-19 - PR #171 round-8 thread fixed: push authorization in the cycle diagram (side-task)

- Scope: one unresolved Codex thread on `docs/architecture/development-cycle.md`,
  raised again by an owner-side human peer on the grounds that this diagram
  purports to govern agents. Checked against the ruleset before editing. Valid.
- Verification: the diagram had a single unconditional edge,
  `Authorize -->|Review-fix commit on an open PR| PR`. `AGENTS.md:234-242`
  grants that standing exception to Claude Code and Codex sessions only and
  says in terms that it does not extend to GitHub Copilot task sessions or
  their subagents, Jules, or any other agent. An agent reading the canonical
  diagram would therefore push a review-fix commit that the ruleset requires
  it to pause on.
- Plan vs implementation: the decision node now carries three edges instead of
  two. WP and batch commits pause in any session; the direct path is labelled
  Claude Code or Codex only; every other agent routes to the same pause. Added
  prose naming `AGENTS.md` as the owner of the rule, and recording the three
  actions that always need explicit instruction whatever the session --
  force-pushes, history rewrites, and anything targeting `main` -- plus the
  Copilot platform-tool requirement at `AGENTS.md:243-244`, neither of which
  the diagram had carried.
- Deviations: none. No code changed.
- Validation: the edited diagram was validated before it was written --
  `valid = true`, type `flowchart`. `pytest -q` -- **590 passed**.
  `doc_state_sync.py --check` -- exit 0 with the expected root BATCH warning.
- Forward guidance: next action unchanged -- the F-SWE-1 audit, then WP-1. A
  preflight amendment to the charter and the Batch 21 WP gates is agreed and
  pending; see the owner decisions recorded with it.

### 2026-08-19 - PR #171 round-7 threads fixed (side-task)

- Scope: the three unresolved Codex threads left on `3d15849` after the
  diagram audit. All three are P2 and all three were checked against the
  source before any edit. All three are correct.
- Verification and fixes:
  - `top-albums-sequence.md` drew `Close connection` unconditionally, but
    `process_albums` closes inside `if conn` (`orchestrator.py:603-604`), so
    the no-connection branch never closes anything. Wrapped in an `opt DB
    connected` block.
  - The same diagram claimed the browser never posts `results_complete` on an
    error payload. `loading.js:209-229` shows only the retryable branch stays
    on the page; a non-retryable error waits three seconds and calls
    `redirectToResults()`, which does post. Split the branch by `retryable`
    and routed the non-retryable case to the processing-error page.
  - `FINDINGS.md` F-B21-1 stated `MAX_ACTIVE_JOBS` is 5 as an absolute.
    `config.py:31` reads it from the environment with 5 as the default, and
    the literal contradicted F-LOAD-1 in the same file. Reworded to name 5 as
    the default and tie the failure count to configured capacity.
- Deviations: none. No code changed; F-B21-1 stays open and unfixed, because
  it is a code change for a code batch.
- Validation: `pytest -q` -- **590 passed**. `pre-commit run --files` on both
  edited files -- all hooks pass. `doc_state_sync.py --check` -- exit 0 with
  the expected root BATCH warning. The edited Mermaid diagram was validated
  through the Mermaid Chart validator: `valid = true`, type `sequence`.
- Forward guidance: the next action is unchanged -- the F-SWE-1 audit, then
  Batch 21 WP-1.

### 2026-08-15 - PR #171 round-6 threads fixed and all five diagrams audited (side-task)

- Scope: the two unresolved Codex threads on `00c0adb`, both on the Top Albums
  sequence. A prior GLM-5.2 session had left uncommitted diagram edits and a
  list of findings, then stopped before it finished. I checked the two threads
  and every edit that session made against the code, then audited all five
  diagrams with three independent verification agents.
- Verification of the two threads: both are correct. `fetch_top_albums_async`
  groups, normalizes, and thresholds the albums before it returns
  (`orchestrator.py:112-116`), so all of that runs before the empty-result
  check at `orchestrator.py:784`. `process_albums` writes to the cache only
  under `if conn and new_metadata_rows` (`orchestrator.py:591`).
- Verification of the prior session: three of its six edits were wrong. It put
  the hit/miss partition inside the DB-connected branch, but the code
  partitions with or without a connection (`orchestrator.py:567`). It drew
  `cleanup_expired_cache()` as a call to `repositories.py`, but that helper
  comes from `utils.py` (`orchestrator.py:40`). It put the total Spotify match
  failure after the store step, but the check runs first
  (`orchestrator.py:824` before `orchestrator.py:842`).
- Plan vs implementation:
  - Top Albums sequence: rewrote the background-task block and the browser
    block. Grouping now sits before every downstream branch. Persistence is
    conditional and records `db_cache_persisted`. The partition sits outside
    the DB branch. New: the connection close and its `finally` ordering
    against `SpotifyUnavailableError`, the `get_job_context` read behind the
    total-match-failure check, the six `results_complete` outcomes, the
    `/progress` 404, and the two unhandled-exception states.
  - Heatmap sequence: added the housekeeping calls, the page-count stats, the
    5% and 80% progress writes, and the unhandled-exception path. Rebuilt the
    render block: the client requests `/heatmap_data` only at 100%, so the 202
    is a narrow race that restarts polling, not a peer alternative.
  - Development cycle: split the merged fast path so the actionability stop
    applies to comment jobs only, added the push-authorization gate that
    `AGENTS.md` requires between commit and PR, and dropped the E2E claim that
    no rule file makes.
  - Runtime diagram and `docs/ARCHITECTURE.md`: named the eight nodes that
    import `config.py`, corrected the arrow-semantics paragraph, and repointed
    the module-graph reference to SESSION_CONTEXT Section 4 alone.
  - Both structural diagrams passed their audit with no change to the graphs.
- Deviations: the prior session said the fix needed a full rewrite of the
  parallel block. It did not. The corrections are local, but they reach more
  branches than that session touched. The audit also found a real code gap and
  it is recorded as F-B21-1 rather than fixed here: `background_task` and
  `heatmap_task` build the event loop outside the `try`, so a failure there
  leaks a job slot. No production code changed in this commit.
- Validation: all four changed diagrams pass Mermaid validation, checked
  against the exact text now in the files. `pytest -q` -- **590 passed**, 3
  known warnings. `pre-commit run --all-files` -- all hooks pass.
  `doc_state_sync.py --check` -- exit 0 with the expected active-root
  `BATCH21_DEFINITION.md` warning.
- Forward guidance: push, then reply to the two threads and resolve them.
  PR #171 stays open until the owner says otherwise.

### 2026-08-15 - PR #171 round-5 review threads remediated (side-task)

- Scope: three new Codex threads on `37ca4a9` -- one on the development-cycle
  diagram and two on the Top Albums sequence. All three were verified against
  the code before any edit and all three were valid.
- Verification:
  - `AGENTS.md` L29-44 defines the review-comment fast path (fetch the thread
    first, stop if not actionable, else read only the scoped files), but the
    development-cycle diagram routed every review finding through the full
    bootstrap gates. The diagram and the rules it documents were written in
    the same PR and disagreed.
  - `_fetch_and_process()` stores an empty result, marks progress 100%, and
    returns before pre-slicing, cache access, or Spotify enrichment when
    `filtered_albums` is empty. The Top Albums sequence sent every successful
    page fetch into those stages.
  - `process_albums()` catches `_batch_lookup_metadata()` exceptions, records
    `db_cache_warning`, treats every album as a miss, and continues to Spotify
    (possibly persisting via the open connection). The diagram's connected
    path presented lookup as unconditional and its unavailable path said
    persistence was skipped.
- Plan vs implementation: the development-cycle diagram now branches on
  review-finding/comment-job before full bootstrap (fetch thread, stop if not
  actionable, else read scoped files); the Top Albums sequence now stops after
  an empty filtered set and adds a fail-open cache-lookup-error continuation.
- Deviations: none. No production behavior changed and no tests were added;
  existing tests already cover the empty-filtered-set and fail-open lookup
  paths.
- Validation: both updated diagrams pass Mermaid validation and open in
  preview. `pytest -q` -- **590 passed**, 3 known warnings. `pre-commit run
  --all-files` -- all hooks pass. `doc_state_sync.py --check` -- exit 0 with
  the expected active-root `BATCH21_DEFINITION.md` warning.
- Forward guidance: commit and push this remediation, then resolve the three
  threads. PR #171 remains unmerged pending separate owner instruction.
