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

### Batch index (completed batches archived; the active batch, if any, is listed last)

| Batch | Title | Definition | Log |
|-------|-------|------------|-----|
| 0 | Baseline freeze + approval parity suite | `docs/history/definitions/BATCH0_DEFINITION.md` | -- |
| 1 | Proper upstream failure state + retry UX | `docs/history/definitions/BATCH1_DEFINITION.md` | -- |
| 2 | Personalized minimum listening year | `docs/history/definitions/BATCH2_DEFINITION.md` | -- |
| 3 | Remove nested thread pattern | `docs/history/definitions/BATCH3_DEFINITION.md` | `docs/history/logs/BATCH3_LOG.md` |
| 4 | Expand test coverage significantly | `docs/history/definitions/BATCH4_DEFINITION.md` | `docs/history/logs/BATCH4_LOG.md` |
| 5 | Docstring + comment normalization | `docs/history/definitions/BATCH5_DEFINITION.md` | `docs/history/logs/BATCH5_LOG.md` |
| 6 | Frontend refinement/tweaks | `docs/history/definitions/BATCH6_DEFINITION.md` | `docs/history/logs/BATCH6_LOG.md` |
| 7 | Persistent metadata layer (Postgres) | `docs/history/definitions/BATCH7_DEFINITION.md` | `docs/history/logs/BATCH7_LOG.md` |
| 8 | Modular refactor (app factory + blueprints) | `docs/history/definitions/BATCH8_DEFINITION.md` | `docs/history/logs/BATCH8_LOG.md` |
| 9 | Audit remediation (WP-1 through WP-8) | `docs/history/definitions/BATCH9_DEFINITION.md` | `docs/history/logs/BATCH9_LOG.md` |
| 10 | Gemini audit remediation (WP-1 through WP-9) | `docs/history/definitions/BATCH10_DEFINITION_2026-02-21.md` | `docs/history/logs/BATCH10_LOG.md` |
| 11 | Gemini Priority 2 audit remediation (SoC, DRY, architecture) | `docs/history/definitions/BATCH11_DEFINITION.md` | `docs/history/logs/BATCH11_LOG.md` |
| 12 | Polish and observability (CSS, formatting, SoC, progress) | `docs/history/definitions/BATCH12_DEFINITION.md` | `docs/history/logs/BATCH12_LOG.md` |
| 13 | Internal decomposition and coverage hardening | `docs/history/definitions/BATCH13_DEFINITION.md` | `docs/history/logs/BATCH13_LOG.md` |
| 14 | Doc hygiene (archive restructure, docsync package, per-batch routing) | `docs/history/definitions/BATCH14_DEFINITION.md` | `docs/history/logs/BATCH14_LOG.md` |
| 15 | Alignment, hardening, and handoff | `docs/history/definitions/BATCH15_DEFINITION.md` | `docs/history/logs/BATCH15_LOG.md` |
| 16 | Script hygiene, local dev hardening, and integration testing | `docs/history/definitions/BATCH16_DEFINITION.md` | `docs/history/logs/BATCH16_LOG.md` |
| 17 | Agent bootstrap hardening, CI/CD improvements, and dep pinning | `docs/history/definitions/BATCH17_DEFINITION.md` | `docs/history/logs/BATCH17_LOG.md` |
| 18 | Scrobble heatmap -- iteration 1 | `docs/history/definitions/BATCH18_DEFINITION.md` | `docs/history/logs/BATCH18_LOG.md` |
| 19 | Heatmap polish -- frame, KPIs, mobile layout | `docs/history/definitions/BATCH19_DEFINITION.md` | `docs/history/logs/BATCH19_LOG.md` |
| 20 | File-hygiene + docs methodology refresh | `docs/history/definitions/BATCH20_DEFINITION.md` | `docs/history/logs/BATCH20_LOG.md` |
| 21 | UI overhaul -- Tailwind + daisyUI migration | `docs/history/definitions/BATCH21_DEFINITION.md` | `docs/history/logs/BATCH21_LOG.md` |
| 22 | Enrichment providers and original release years | `docs/history/definitions/BATCH22_DEFINITION.md` | `docs/history/logs/BATCH22_LOG.md` |
| 23 | Spotify Extended Streaming History import | `BATCH23_DEFINITION.md` | active -- Section 4 |

A batch's close-out entry sits in its per-batch log only when the heading
carried a `(Batch N WP-X)` tag (as Batch 18's did). Close-outs tagged
`(Batch N close-out)` are not parser-recognized and were routed to the
monolith archive instead -- Batches 19 and 20 are the current examples.
See FINDINGS F-DOCSYNC-3.

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
- **Batch 20 is complete.** All 9 WPs done (WP-0 through WP-5 via PR #159
  on `file-hygeine`; audit gap-fix follow-up, WP-6, WP-7, and WP-8 on
  `wip/batch-20`, submitted as PR #162). Definition archived:
  `docs/history/definitions/BATCH20_DEFINITION.md`.
- **Batch 21 is complete**, closed 2026-09-13. All nine work packages are
  done. Definition archived:
  `docs/history/definitions/BATCH21_DEFINITION.md`; log:
  `docs/history/logs/BATCH21_LOG.md`. Scope was the UI overhaul: Bootstrap
  5.1.3 to Tailwind v4 (standalone CLI) plus daisyUI v5, warm
  heatmap-derived themes app-wide, migrated page by page. The last commit on
  the batch is `4b4965b`, on branch `test`.
- **Batch 22 is complete**, closed 2026-09-20. All six work packages are
  done. Definition archived:
  `docs/history/definitions/BATCH22_DEFINITION.md`; log:
  `docs/history/logs/BATCH22_LOG.md`. It ran on `feat/batch22-enrichment`
  (worktree off `test`). Scope was album enrichment behind a provider
  contract, Deezer answering when Spotify cannot, and MusicBrainz correcting
  a reissue year to the album's original while the results page is open.
  Plan of record:
  `docs/superpowers/plans/2026-09-13-batch22-enrichment-providers.md`.
- **WP-0 is complete.** The behaviour-neutral module split is done.
- **WP-1 is complete.** Tasks 1-3 moved album metadata behind the provider
  contract.
- **WP-2 is complete.** Tasks 4-6 added the Deezer fallback and provider
  attribution.
- **WP-3 is complete.** Tasks 7-9 landed the MusicBrainz client, cached
  original-release corrections applied before filtering and display, and the
  correction worker that populates new `original_release_cache` rows live
  (`scrobblescope/release_checks.py`, one process-wide thread fed a FIFO
  queue of job ids by `_fetch_and_process`).
- **WP-4 is complete.** Task 10 added `GET /api/release_checks?job_id=` and
  Task 11 disclosed its findings live on the results page, without moving a
  row while the page is open.
- **WP-5 is complete**, and with it **all planned work packages for Batch 22
  are complete**. The batch is closed: its definition is archived at
  `docs/history/definitions/BATCH22_DEFINITION.md` and its log at
  `docs/history/logs/BATCH22_LOG.md`.
- **Session handoff, 2026-09-24:** `docs/history/reports/HANDOFF_2026-09-24.md`
  is the entry point for a new agent, written for a cloud session with only
  this repository. It covers WP-0's state, the Linux environment setup, how
  the subagent loop is run, the next steps in order, the rulings in force and
  the traps. `.superpowers/cloud-kit/` holds the workspace constraints and
  the four agent definitions it uses.
- **PR #236 merged into `test`** at `fc9098d3` (2026-09-20 21:12). It carried
  the eight commits that landed after PR #234, which had merged the branch as
  it stood at `f6d5926` (2026-09-20 05:06) while the first of those eight was
  05:50 -- a chronological gap, not a rebase. So `test` now holds WP-4, the
  Batch 22 close-out and the Batch 23 definition; before #236 it held none of
  the three.
- **PR #235 merged `test` into `main`** on 2026-09-21, and **PR #237** then
  carried the eleven between-batch commits into `test`. **PR #238**
  (`test` -> `main`) merged on 2026-09-21, carrying them on to `main`; a
  merge to `main` deploys to Fly.io through Fly's GitHub integration, not a
  repository workflow.
- **PR #241 carried Batch 23 WP-0's work so far, through `1d16e18`, into
  `main`** on 2026-09-24 as a merge commit (`92f7d6a`, parents `49af94f` and
  `1d16e18`). The owner retargeted it from `test` before merging. The branch
  stays an ancestor of `main` with an identical tree, so WP-0 continues on
  `feat/batch23-wp0-hygiene` with no reset. A merge to `main` deploys to
  Fly.io.
- **Outbound request identity, fixed 2026-09-20.** `config.APP_USER_AGENT` is
  now the single owner of the application's own name, and
  `create_optimized_session` sends it on every provider session. Until this
  change every Last.fm, Spotify and Deezer request went out as aiohttp's
  default `Python/3.x aiohttp/3.y`, which identifies nobody -- Last.fm asks
  for an identifiable User-Agent on all requests and warns that an anonymous
  client risks suspension. `musicbrainz.py` composes its contact-bearing
  User-Agent on the same identity, so the application cannot disagree with
  itself about its own name.
- **`MUSICBRAINZ_CONTACT` is set on Fly.io** (2026-09-21, the project's
  GitHub URL), as well as in the local `.env`.
- **Side task complete: the frontend gate split (F-B21-51).** The facade
  measures 535 lines, under the plan's 700-line threshold. Plan of record:
  `docs/superpowers/plans/2026-09-21-frontend-gate-decomposition.md`.
- **The code defect is closed.** `_musicbrainz_headers` raises instead of
  interpolating the literal string `None` as a contact address, which is what
  it did when called outside the gate that guards it.
- **Batch 23 is active.** Definition: `BATCH23_DEFINITION.md`. Branch: `feat/batch23-wp0-hygiene`.
  Opened 2026-09-21 by the owner, who named the branch that day and asked
  for the opening to be explicit rather than silent. It waited for the fix
  to audit defect D1 (`aad26e5`), because before it an opened batch with no
  logged work package rendered as "between batches". Scope: eight work
  packages, WP-0 through WP-7; the deferred Batch 21 frontend and
  accessibility audit is inside WP-7, which the batch cannot close without.
  The branch is cut from `test`, so run the worktree guard with
  `--base-ref origin/test` (`HANDOFF_PROMPT.md` "Bootstrap edge cases").
  The definition's header names WP-0's plans.
- **Next action:** WP-0 is next. The owner widened it on 2026-09-23 into
  three parts, which the definition's WP-0 describes. Part A is the
  behaviour-neutral extractions: the shared loop protocol has landed
  (`ad2d078`..`54ab72b`), and the three original extractions are done
  2026-09-23. Part B reconciles what earlier batches left open. Part C
  clears every finding open at P0 or P1. The rest of Parts B and C run from
  `docs/superpowers/plans/2026-09-23-batch23-wp0-reconcile-and-clear.md`.
  The owner answered its questions, Q0-Q16, on 2026-09-23; the plan
  records the answers. The order from here:
  1. Part A: the foundation plan's Task 2 -- done 2026-09-23. Then its
     Task 12, the release-window rule moved to `domain.py`, which the owner
     added to Part A on 2026-09-23 -- also done 2026-09-23. Part A is
     complete, each task reviewed clean.
  2. This plan's Stage 1, then Stage 2, then Stage 3. Stage 1 (Tasks 1 and 2)
     is complete: Task 1 (the six stale "pending deploy" records) and Task 2
     (the docsync work-package gap, filed as F-DOCSYNC-15) both landed
     2026-09-23. Stage 2's Tasks 3-9 and 11 are complete: Task 3
     (F-SWE-6, reading a job no longer renews its lease), Task 4 (F-B22-7,
     part 1 of 3, the `spotify_id` column), Task 5 (F-B22-7, part 2 of 3,
     the Spotify payload translated once in `spotify.py`), Task 6 (F-B22-7,
     part 3 of 3, retiring the unused `enrich_albums`), Task 7 (F-SWE-5,
     both background entry points now publish `internal_error`), Task 8
     (F-B21-6, every year gate reads `routes._current_year()`, which uses
     `datetime.now(timezone.utc)`), Task 9 (F-LOAD-1, both refusals read
     `routes._capacity_message()`, which states the configured
     `MAX_ACTIVE_JOBS`) and Task 11 (F-B22-8, `run_release_checks` runs its
     candidates without a cache connection and skips only the cache read,
     the persist and the close) all landed 2026-09-23. Stage 2's last task,
     Task 12 (F-B23-5, one owner in `domain.py` for the release-window
     rule), was added by the owner 2026-09-23 and is done: `domain.py` now
     owns `release_window`, and both `_matches_release_criteria` and
     `release_checks._window_end` derive from it. Stage 2 is complete. Stage 3
     (Task 10, writing the owner's rulings into their findings) is also
     complete, 2026-09-23: this plan's tasks are done. Next is the foundation
     plan's Tasks 4-10.
  3. The foundation plan's Tasks 4-10. Task 4 (the archive page target gets
     a reader, DOC024, and the cold rule's documentation is corrected) is
     done, 2026-09-23. The reconcile plan's Task 13, which the owner added
     on 2026-09-24 as its Stage 4 (F-B23-6: log every provider call and the
     release checks), is done, 2026-09-24, including the owner's live check
     (its Step 5). Task 5 (the DOC range the catalogue owns is no longer
     stated as a range anywhere live) is done, 2026-09-24. Next is the
     foundation plan's Task 6.
  4. The follow-on plans.
  Every WP-0
  commit logs an untagged entry directly after the current-batch end marker;
  one tagged `(Batch 23 WP-0)` entry closes WP-0 (owner ruling, 2026-09-23).
  Later work packages log tagged entries inside the markers.
- **The dashboard's test count read 1522 for a while**, and the way it got
  unstuck is
  worth knowing. It read 1497 for most of 2026-09-20: two entries shared that
  date, and on a same-date tie source precedence ranks an untagged side-task
  entry above the batch entries regardless of which was written later
  (F-DOCSYNC-11). A hand-written correction was refused by DOC005, DOC006 and
  DOC008, which recompute the same authority. Writing a *newer* side-task
  entry carrying the measured count is what moved it, because that entry
  outranks the older one in its own source. The count still cannot be
  published directly; F-DOCSYNC-13 proposes letting an authored measurement
  be passed in instead.
- **Owner-facing verification from Batch 22 is done** (2026-09-23). The
  Spotify credentials are restored: the owner's run logged 142 of 146 lookups
  answered by Spotify. MusicBrainz corrections land against the real service:
  the owner's two runs with Postgres up each wrote 60 `original_release_cache`
  rows within a minute of the job finishing. The worker logs nothing on
  success, which is why neither run's log showed it.
- **Owed from Batch 21:** the frontend and accessibility audit WP-8
  chartered. The owner moved it to Batch 23's close-out on 2026-09-13 so it
  covers the final UI once. Batch 23's plan carries the obligation; do not
  close that batch without it.
- **Results refinement:** proportional scaling and the warm shared canvas are
  included in the review follow-up; F-B21-55 and Section 4 record evidence.
  The current owner consistency pass adds midpoint surfaces, matched sidebar
  headings and action buttons, removes redundant Heatmap loading counters,
  and repairs page/handoff motion. The index form sits up to 2.5rem higher;
  the decade-filter state fits shorter desktop windows without changing scale.
  The 2026-09-10 follow-up refines Heatmap contrast and toolbar type, adds
  delayed Spotify link hints and animated ranking changes, and fixes a
  reproduced first-paint flash. The header now scrolls out of view in document
  flow, following the owner's screenshot clarification. Final validation passed;
  owner visual review is approved and the reviewed changes are authorized for PR #227.
- **PR #227 priority triage:** F-B21-49 is resolved in the review follow-up.
  Review comments including assertions and all 15 deleted route TODOs were
  checked; F-B21-54 records remaining scanner noise. Evidence:
  `docs/history/reports/PR227_PRIORITY_TRIAGE_2026-09-09.md`.
  The owner authorized publishing the pending review commits and approved
  refinements on `test`. WP-7 retains scope; Task 6 timing follows the
  canonical remediation plan.
- **PR #227 review remediation:** the owner-requested package is implemented
  and validated. Audit and remaining scope:
  `docs/history/reports/PR227_REVIEW_2026-09-07.md`. The latest Section 4 entry
  records subsequent owner-approved header and surface refinements.
- **PR #223 side-task:** merged as `123b127`; this worktree is synchronized.
  Remaining issue #222 targets stay open.
- **Planning follow-up:** the original owner-review plan remains historical
  evidence; the superseding plan below is canonical. Task 2 now implements
  the two-engine runner and explicit CSS composition dimensions. Its rendered
  expanded-state guard, complete validation, and PR #224 review remediation
  passed.
- **Remediation plan:** **Tasks 1-5 are complete and validated locally.
  Task 6 (accessibility pass) is deferred until Bootstrap is fully removed.** Work from
  `docs/superpowers/plans/2026-09-01-batch21-index-scaling-and-review-remediation.md`.
  Task 1 is complete. Task 2 replaces the engine-independent height-denominator
  defect with layout-aware CSS and a complete real-window gate in Chromium
  and Firefox; it merged as PR #224. Task 3 landed the final `3fr 4fr` split,
  owner-refined `27.5rem` form base cap, raised `--shell-border` contrast to
  >= 3:1 in both themes, and applied the ruled header clamps (`--shell-height`,
  `--shell-control-gap`, nav-link/theme-control sizing). Review remediation pins that
  composition across every reachable form state and uses one fast hero/page
  fade timing (F-B21-41, F-B21-42). Task 4 aligned visible
  loading progress with pipeline phases across Top Albums and Heatmap,
  eliminated overlapping interval polls and stale responses (F-B21-33), decoupled
  received vs attempted Last.fm counts, corrected loading composition
  (F-B21-36), and added real-browser phase checks to the gate. Its review fix
  keeps the loader hidden when a saved Heatmap job is already cached and fades
  the result in directly (F-B21-43). Task 5 added the dedicated unmatched
  no-data surface (`templates/unmatched_empty.html`), wired clean session
  recovery and eviction on `/unmatched`, mutest-verified failure paths, and
  extended `frontend_gate.py` with card, shadow, and action assertions.
  Owner visual refinements bias the desktop form above centre,
  unify single-row mobile navigation with the theme control below page content,
  widen the desktop Heatmap result, and return its username to the neutral headline
  treatment (F-B21-44 through F-B21-46). Task 6 follows Bootstrap removal; see the canonical remediation plan.
  WP-4 migrated `loading.html` to the shared determinate wait panel, completed
  both polling state machines, and added browser-session recovery for the
  latest album and heatmap jobs at clean destination routes.
  The original twelve-round Codex review closed at `77bb001`: all thirty threads
  were resolved, both Quality Gate runs passed, and the Codex connector
  recorded a thumbs-up. Three later Graphify passes produced advisory findings.
  Codex confirmed five defect classes: the root-font and saved-theme checks
  leaked state, declaration paths could escape the repository, and joining
  documents for wrapped regex matches lost the original per-line semantics;
  equivalent spellings of one repository path could also bypass a live
  in-memory document and read stale disk. All five are hardened at shared
  seams with regression tests. The remaining claims were disproved against
  section boundaries, source contracts, tests and live browser execution.
  GitHub remains the source of truth for the PR's integration state.
  `templates/partials/_loading.html` already exists and is framework-neutral
  -- WP-3 built it a work package early -- so WP-4 consumes that partial
  rather than writing one. `GET /loading` supplies the route the gate needs;
  its job fixture, composition check, and two-pipeline state-machine check
  landed in WP-4.
  **WP-3 is complete.** It rebuilt `index.html` on Tailwind, deleted the
  welcome modal and the `bootstrap.Popover` hints, absorbed WP-6, and grew
  the frontend gate from four checks at one desktop viewport into a
  multi-profile regression suite. Codex raised thirty comments across twelve
  rounds; twenty-nine were valid, and one sizing premise was disproved but
  received its conservative remedy. All were actioned.
  Earlier context, still true: WP-2 **merged as PR #216** on 2026-08-24
  (`658bdb2`, rebase merge). It shipped the base shell, the `error.html`
  pilot, the Playwright runtime, the frontend gate and the compiled-CSS
  pre-commit hook, closing F-B21-2, F-B21-7 and F-AUDIT-1 and filing
  F-B21-10, F-B21-11 and F-B21-12. Codex raised seven comments across three
  rounds; every one was valid and all seven were fixed before the merge.
  Round three took the SMIL out of the header wordmark and gave the
  back-to-top control its wrapper back. PR #217 merged the same day
  (`8ed1650`), adding the DOC007 and DOC008 checks that close F-B21-13.
  `pip-audit` still reports its advisories without failing the gate, by
  design (F-B21-3). The root-hygiene side task is **closed**: the owner
  rejected the audience-banner scheme on 2026-08-20, and the config-file
  verdict landed in `DEPLOY.md`.
  Earlier context, still true: **PR #171 merged to `main` on 2026-08-19**
  (`bb187ae`, rebase merge) with zero unresolved review threads after eight
  rounds; `wip/batch-21` was realigned to it. `docs/history/definitions/BATCH21_DEFINITION.md` was
  amended the same day so the batch gate can fail on frontend work.
  PR #169 merged 2026-08-08 shipping the
  repository-integrity gate and read-only worktree guard, resolving
  F-DOCSYNC-5/F-WORKTREE-1/F-WORKTREE-2; three guard files exceed their
  directory peer caps, accepted as a deviation and tracked as F-WORKTREE-4,
  not silently. PR #170 merged 2026-08-12 (`5b060a2`), settling the guard and
  docsync sources the audit reads.
- **Batch 21 closed action:** the WP-7 refinement the owner asked for is implemented and
  verified, so the earlier note that this work was cut off before completion is
  discharged. The disclosure step is 25 (was 50), and the back-to-top control
  now collapses its panel as well as scrolling. `pytest -q` -- **1028 passed**,
  measured 2026-09-12; the two-engine frontend gate -- 26 checks passed in 48
  runs across chromium and firefox.
  The layout conflict this bullet tracked is **closed**. It was wider than the
  bullet said: the spec recorded the side-by-side ruling in its Presentation
  section, but its Outcome paragraph and its validation paragraph still described
  full-width stacking, and the second credited the frontend gate with proving a
  layout the gate asserts against. All three sites now agree, and the disclosure
  paragraph now states the 25-row step and the collapsing back-to-top control.
  WP-8 starts only on owner direction.
  The unmatched table repair is implemented, validated and **committed on
  `test`**; the latest Section 4 entry records it. The owner answered its four
  questions on 2026-09-13: two panels is the maximum, the fix-hint accent stays,
  the cover takes the Results size, and the threshold panel is titled "Not
  enough listening", which resolves F-B21-58.

- **Owner ruling, 2026-09-13 -- backend work starts before WP-8's audit.**
  WP-8's frontend and accessibility audit moves to Batch 23's close-out, and
  Batch 21 closes without it. Batches 22 and 23 change the same pages, so an
  audit run first would be redone. `docs/history/definitions/BATCH21_DEFINITION.md` WP-8 records the
  move; the frontend gate keeps its own accessibility checks running
  meanwhile.

- **Batch 23, Spotify export import**, approved by the owner on 2026-09-13,
  is now the active batch (see its bullet above). Spotify listeners upload
  the Extended Streaming History zip; there is no Spotify login, because
  Spotify caps apps without extended access at 5 allowlisted users.
  `docs/superpowers/plans/2026-09-13-batch23-spotify-export-import.md` is
  its cross-WP export outline; each work package gets its own SDD plan, as
  the definition's "Planning authority" paragraph says. F-B21-59 records
  the Spotify API risk, and F-B21-60 the artwork rules Batch 22's provider
  work had to satisfy.

- **Owed before Phase 2:** none. Every commit this bullet previously named has
  landed: the F-B21-51 slice-1 refactor as `95e0896`, the design-system plan's own
  move as `c277728`, and the architecture-diagram rebuild as `cc987f5`. When a new
  commit becomes owed, name it here and keep the naming rather than a count, so the
  section cannot go silently wrong.
- **Traversal record:** the design-system plan was traversed exhaustively on
  2026-09-11; the findings are
  `docs/history/reports/BATCH21_PLAN_TRAVERSAL_2026-09-11.md`.
- **Results follow-up:** F-B21-47 is implemented on `test`; the full suite and
  focused frontend-gate unit coverage pass. The count lives in the next-action
  bullet above and in SESSION_CONTEXT Section 1; do not restate it here. F-B21-48 records the separate
  persistent Last.fm scrobble-cache candidate; it does not expand this
  frontend change.
- **Perf note:** heatmap fetch speed is rate-limit bound; measurement and
  rationale live in FINDINGS.md F-B18-11 (single source).
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
  - `<!-- DOCSYNC:CURRENT-BATCH-END -->

<!-- DOCSYNC:CURRENT-BATCH-START -->

<!-- DOCSYNC:CURRENT-BATCH-END -->

### 2026-09-24 - Stop stating a DOC code range the catalogue owns

Side task, no batch tag: replace every live prose statement of a `DOC001-DOC0NN`
range with wording that states no range, part of Batch 23 WP-0 Part B.
Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

- **Scope: the foundation plan's Task 5.** Six live sites stated a stale
  contiguous range (`AGENTS.md` x3, `DEVELOPMENT.md`, and
  `docs/architecture/documentation-tooling.md` x2, one of them the heading).
  Both `DOC001-DOC023` and `DOC001-DOC024` are false today: DOC021 and DOC022
  are reserved by
  `docs/superpowers/plans/2026-09-12-repository-agnostic-plan-spec-guards.md`
  but not raised, so no contiguous span from `DOC001` is true. Each site now
  says "the DOC diagnostic catalogue" (owner: `documentation-tooling.md`)
  instead of restating a range; the catalogue's own heading is renamed
  "The DOC code catalogue" and its one explicit list reads "`DOC001`-`DOC020`,
  `DOC023` and `DOC024` issues". `FINDINGS.md`'s F-B21-61 note ("a new
  invariant for this finding starts at DOC023") is repointed at the catalogue,
  since DOC023 is itself now taken (the finding-lifecycle grandfathered-finding
  count, `scripts/docsync/findings.py`).
- **Tests repointed, controller ruling 2026-09-24 (the one sanctioned
  existing-test edit).** `tests/test_docsync_integrity.py::
  test_stated_docsync_range_matches_the_highest_code_raised` and
  `test_stated_range_helper_rejects_a_stale_range` read `AGENTS.md`'s stated
  range, which no longer exists. Both are renamed
  (`test_stated_docsync_catalogue_matches_the_codes_raised`,
  `test_stated_catalogue_helper_rejects_a_mismatched_list`) and repointed at
  `documentation-tooling.md`'s explicit list; their helpers become
  `CATALOGUE_SENTENCE_RE`, `_stated_codes`, `_raised_codes` and
  `_catalogue_matches_raised_codes`. The comparison is now set equality
  (parsing "DOC0AA-DOC0BB" spans and single codes) rather than a maximum, so
  a listed-but-unraised code (DOC021) is caught, which comparing only the
  upper bound could not catch. The proof test mutates the real catalogue
  sentence in place (drop DOC024; add DOC021) rather than a synthetic
  fixture, so it exercises the same parsing the corpus test relies on.
- **`.docsync.toml`** gains a fourth `[[retired]]` declaration, modelled on
  its "the docsync integrity range ends at DOC011" sibling: it matches the
  bare literal `DOC001-DOC023` or `DOC001-DOC024`, either spelling
  (contiguous or backtick-split), needs no verb-prefix guard because the
  valid list never contains either substring, and leaves `DOC001-DOC020`
  alone.
- **Discovered and filed as F-DOCSYNC-16.** The three pre-existing
  `[[retired]]` declarations' `allow_after` marker for `PLAYBOOK.md` was the
  literal string `"## 4. Execution log"`, but `check_retired` compares a raw
  line by exact equality and the real heading is `"## 4. Execution log (for
  agent handoff)"` -- confirmed by reproducing the mismatch directly against
  `check_retired`. Their Section 4 exemption was therefore non-functional
  against the live document, latent only because no dated entry restated one
  of their three retired phrases. This task's own new declaration used the
  full, correct heading text from the start so it was not affected.
- **Live probe** (`/tmp/ssprobe`, `git archive` of `git stash create`,
  deleted after):

  | probe | expected | got |
  | --- | --- | --- |
  | faithful copy `--check` | same summary as the worktree | match, exit 0 |
  | red: add "the DOC001-DOC023 catalogue" to `AGENTS.md` | DOC011, exit 1 | DOC011, exit 1 |
  | red: add `` returns typed `DOC001`-`DOC024` issues `` to `DEVELOPMENT.md` | DOC011, exit 1 | DOC011, exit 1 |
  | near-miss: same text struck through in `AGENTS.md` | silent, exit 0 | silent, exit 0 |
  | near-miss: same text in a dated Section 4 entry below the marker | silent, exit 0 | silent, exit 0 |
  | near-miss: "DOC001-DOC020" in `AGENTS.md` prose | silent, exit 0 | silent, exit 0 |
  | mutate `documentation-tooling.md`'s list to drop DOC024 | corpus test red | red |
  | mutate `documentation-tooling.md`'s list to add DOC021 | corpus test red | red |

- Validation: `pytest -q` -- **1821 passed**. No test added or removed, so
  the three R3 count sites are unchanged.

**Fix round (2026-09-24, review finding).** The review's one Important
issue: the three pre-existing `allow_after` markers were left broken
next to the fourth, freshly-corrected one in the same commit and same
file, instead of being corrected outright (Anti-Pattern 11). Owner ruling:
correct all three in `.docsync.toml` (touching nothing else in those
declarations); reword F-DOCSYNC-16 to name the mechanism gap -- docsync
silently ignores an `allow_after` marker that matches no line, rather than
erroring -- and record that the three markers are corrected in this fix
commit; drop its priority to P2 (the fix shape becomes a future check that
errors on a dead marker, not built here); status stays open.

- **`.docsync.toml`:** all three `[retired.allow_after] "PLAYBOOK.md" =
  "## 4. Execution log"` lines corrected to `"## 4. Execution log (for
  agent handoff)"`, the real heading, matching the fourth declaration this
  task already added. Nothing else in the three declarations changed.
- **`FINDINGS.md`:** F-DOCSYNC-16 retitled "docsync silently ignores an
  `allow_after` marker that matches no line," its body names the general
  mechanism gap ahead of the specific instance, records that the three
  markers are now corrected, keeps the reproduction evidence, and states
  the not-yet-built fix shape (a declaration check erroring on a dead
  marker). Priority dropped P1 -> P2; status line unchanged (`open`).
- **Live probe, reproduced in a fresh `/tmp/ssprobe`** (`git archive
  9ea79f5`, `git init`, deleted after): a dated Section 4 entry quoting
  "limit_results goes inside the thresholds disclosure" gives `ERROR
  DOC011`, exit 1, with the unfixed markers; correcting all three markers on
  that same scratch tree makes it silent, exit 0; and `--check` on the
  unmodified corpus (no injected quote) is byte-identical before and after
  the marker fix -- same four DOC024 + root-BATCH warnings, exit 0.

  | probe | expected | got |
  | --- | --- | --- |
  | unfixed markers, dated entry quoting the retired `limit_results` phrase | DOC011, exit 1 | DOC011, exit 1 |
  | corrected markers, same quote | silent, exit 0 | silent, exit 0 |
  | corrected markers, unmodified corpus vs. before | identical `--check` output | identical |

- Validation: `pytest -q` -- **1821 passed** (unchanged; no test touched
  in the fix round).

**Fix round 2 (2026-09-24, re-review + owner catch).** Two Important issues
and one owner catch, all in the same commit (`aa6a867` -> next): the
`.docsync.toml` comment above the fourth declaration's `allow_after` still
described the three siblings' pre-fix state in the present tense, false as
of `aa6a867` -- rewritten to state only what is true now (the exemption
needs the real heading text; F-DOCSYNC-16 records the silent-ignore
mechanism), with no other live present-tense claim found by corpus grep.
F-DOCSYNC-16 carried its new P2 priority but was still filed under the
`## P1 -- Next batch candidates` heading -- moved, unchanged, to the top of
`## P2 -- Scaling roadmap`. Owner catch: this task's own Step 1-6 checkboxes
in the foundation plan were never ticked in the first commit -- ticked now,
nothing else in the plan changed.

- Validation: `pytest -q` -- **1821 passed** (unchanged; no test touched).

### 2026-09-24 - The loading page looks up its error source label in a Map

Side task, no batch tag: close Codacy's object-injection flag on the loading
page's error source label, part of Batch 23 WP-0 Part C. Untagged by owner
ruling 2026-09-23 until the whole of WP-0 lands.

- **Why.** Codacy's check failed on PR #241 with one high issue, "Variable
  Assigned to Object Injection Sink", at `static/js/loading.js`'s
  `const label = ERROR_SOURCE_LABELS[source];`. It is not exploitable: the
  server sends only `lastfm`, `spotify` or `internal`
  (`scrobblescope/errors.py`), and the label goes into `textContent`. But an
  object-literal lookup resolves inherited keys, so a source of
  `constructor` would have printed `Source: function Object() ...`.
- **Change.** `ERROR_SOURCE_LABELS` is a `Map`, read with `.get(source)`.
  An unknown or inherited key finds nothing, so the source line stays
  hidden. The failure call that passes no source is unchanged:
  `Map.get(undefined)` is `undefined`, as the object lookup was. The JSDoc
  says why it is a Map. Nothing else changed; the reconcile plan's Task 7
  code block keeps the object form it shipped with, as a record.
- **Found by** the cloud session, which could not run the frontend gate
  (no Playwright browsers in its sandbox), so the change was made locally.
- **Also corrected:** the heading of the cloud-handoff entry below carried
  a `WP-<digit>` token, against the untagged-entry rule; it now reads
  without one.
- Validation: `pytest -q` -- **1821 passed**; the untracked mutation-runner
  tests were excluded, since they are not repository state. The frontend
  gate ran, since `static/` changed.

### 2026-09-24 - The Batch 23 foundation work gets a handoff a cloud session can run from

Side task, no batch tag: session handoff for Batch 23 WP-0, which moves to a
cloud session. Untagged by owner ruling 2026-09-23 until the whole of WP-0
lands.

- **Why.** The owner is moving the work to a cloud session, which has only
  the repository. The local sessions kept their working state outside Git:
  the SDD ledgers and workspace constraints (`.superpowers/sdd/`, ignored),
  the four agent definitions (user-level, `~/.claude/agents/`), and the
  owner's working agreements (session memory). The gate commands were also
  Windows paths.
- **Added.** `docs/history/reports/HANDOFF_2026-09-24.md`, the new entry
  point: state, Linux setup, how the subagent loop runs without the plugin
  scripts, next steps with Task 5's owner ruling, rulings in force, open
  items and traps. `.superpowers/cloud-kit/constraints.md` is the Linux form
  of the workspace constraints (gates on `.venv/bin`, Lessons L1-L10).
  `.superpowers/cloud-kit/agents/` holds the four agent definitions,
  copied unchanged. `.superpowers/sdd/.gitignore` is now tracked, so a
  fresh clone keeps new SDD workspaces out of Git.
- **Not added.** The root `CLAUDE.md` stays git-ignored, as `.gitignore`
  records; the cloud session's first prompt names the handoff instead. The
  SDD helper scripts stay out too (vendored skills are local harness state
  per `.gitignore`); the handoff gives their plain `git` and `awk` forms.
- **Section 3** points its handoff bullet at the new file.
- Validation: `pytest -q` -- **1821 passed**; the untracked mutation-runner
  tests were excluded, since they are not repository state. Docs only.

### 2026-09-24 - The owner's live check closes the logging task

Side task, no batch tag: a Section 3 correction, part of Batch 23 WP-0 Part
C. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

- **What.** The reconcile plan's Task 13 (F-B23-6) landed as `433120c` and
  its fix round as `e7e076b`. Its Step 5, the owner's live check against
  the real providers, was left to the owner. The owner ran a job with
  `DEBUG_MODE=1` on 2026-09-24 and confirmed the log: per-call DEBUG lines
  such as `MusicBrainz GET /ws/2/release-group/ -> 200 in 133ms` and
  `Spotify GET /v1/search -> 200 in 241ms`, INFO summaries, and no query
  value. Section 3 and the plan's Step 5 now record it done.
- **Observation for a later task.** The owner's log shows one
  `Spotify: 1 calls` INFO summary per Spotify search, each from its own
  runner thread. So that path builds one session per call, and the
  per-session summary becomes one INFO line per album rather than one per
  job. It may also mean connections are not reused there. Not fixed here.
- **Fix-round note.** The fix-round implementer for `e7e076b` stopped at a
  rate limit after its edits and before its gates. The controller read the
  diff, ran `--fix`, the suite, pre-commit and `--check`, repeated the
  scratch-copy mutation proof, and committed. That fix round has no
  independent re-review yet.
- Validation: `pytest -q` -- **1821 passed**; the untracked mutation-runner
  tests were excluded, since they are not repository state. Docs only.
