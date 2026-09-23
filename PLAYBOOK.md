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
- **Session handoff, 2026-09-23:** `docs/history/reports/HANDOFF_2026-09-23.md`
  is the entry point for a new agent. It covers WP-0's state, the next steps
  in order, the untracked artifacts and the traps. For the environment, the
  gates and the schema-migration trap, it defers to
  `docs/history/reports/HANDOFF_2026-09-20.md`.
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
     added to Part A on 2026-09-23 -- also done 2026-09-23.
  2. This plan's Stage 1, then Stage 2, then Stage 3. Stage 1 Task 1 (the
     six stale "pending deploy" records) landed 2026-09-23. Stage 2 includes
     Task 11 (F-B22-8), which the owner added on 2026-09-23.
  3. The foundation plan's Tasks 4-10.
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

- **Queued after Batch 22 -- Batch 23, Spotify export import:** approved by the
  owner on 2026-09-13 and not started. Spotify listeners upload the Extended
  Streaming History zip; there is no Spotify login, because Spotify caps apps
  without extended access at 5 allowlisted users. The plan is
  `docs/superpowers/plans/2026-09-13-batch23-spotify-export-import.md`.
  Neither batch starts on `test`: each opens on its own branch, named here
  first, or the worktree guard raises WT003. F-B21-59 records the Spotify API
  risk they raise, and F-B21-60 the artwork rules Batch 22's provider work
  must satisfy.

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

### 2026-09-23 - Close six stale pending-deploy findings

Side task, no batch tag: close the six finding records that still said "resolved locally, pending
deploy", part of Batch 23 WP-0 Part B. Untagged by owner ruling 2026-09-23 until the whole of WP-0
lands.

- **Scope: the reconcile plan's Stage 1 Task 1.** F-B20-3, F-B21-10, F-B21-26, F-B21-27, F-B21-28 and
  F-B21-29 all said "resolved locally, pending deploy" although their fixes were already on
  `origin/main`. `git fetch origin` ran first, then `git merge-base --is-ancestor` confirmed all seven
  named fix commits (`85e7511`, `079c2b0c`, `b1fdb121`, `ee5ee4eb`, `47321b23`, `df28c06d`, `8b37566a`)
  are ancestors of `origin/main`; none printed STOP, so all six records were written.
- **Plan vs implementation: one deviation, forced by the gate.** The brief's canonical Status line put
  the "fixed by \`<sha>\` ... confirmed an ancestor of \`origin/main\`" text on the checked `**Status:**`
  line itself. `scripts/docsync/findings.py`'s DOC014/DOC015 checks require that line's value to
  normalize to the bare word `resolved` (or `no action`); anything else is rejected, and the word
  "deployed" inside the brief's sentence also trips DOC014's pending-qualifier scan, which is why the
  first `--fix` run failed with six errors naming exactly these findings. Every already-archived finding
  in `docs/history/findings/FINDINGS_ARCHIVE.md` uses the bare form for the same reason. Each of the six
  now reads `- [x] **Status:** resolved` / `**Completed:** <date>`, followed immediately by a new prose
  line carrying the brief's exact sentence (the sha(s), "deployed with it", "confirmed an ancestor of
  \`origin/main\` on 2026-09-23") -- that line sits outside the lifecycle record the gate parses, so its
  wording is unconstrained. The rest of each body (the "Was recorded as" and "Source" lines) was kept
  unchanged, per the brief. F-B21-28 and F-B21-29 each have two fix commits in the brief's table, so
  their new prose line names both ("fixed by \`X\`, completed by \`Y\`, and deployed with it"); the
  completion date used is the later commit's date in both cases, as directed. F-B20-3's new prose line
  uses the brief's supplied reason text (Bootstrap and both CDN providers retired by \`85e7511\`, Batch 21
  WP-8) in place of the generic "fixed by" clause. Completion dates came from
  `git log --ancestry-path --merges --reverse --format=%cs "<sha>..origin/main"`, falling back to the fix
  commit's own date when no merge commit exists on that path: 2026-09-19 (F-B20-3), 2026-09-10 (F-B21-10,
  using `079c2b0c`), 2026-09-10 (F-B21-26 and F-B21-28, using `b1fdb121`), and 2026-09-07 (F-B21-27 and
  F-B21-29, using `ee5ee4eb` and `8b37566a` respectively).
  `doc_state_sync.py --fix` then rotated all six resolved records into
  `docs/history/findings/FINDINGS_ARCHIVE.md`, which emptied the `## P0 -- Fix before next deploy`
  section (F-B21-26, F-B21-27, F-B21-28 and F-B21-29 were its only members); a line was added under
  that heading, rather than deleting it, because other documents cite the severity levels.
  `BATCH23_DEFINITION.md` WP-0 Part B's "Stale finding records" checkbox and the reconcile plan's Task 1
  step boxes are ticked, and Section 3's numbered order list now notes Stage 1 Task 1 landed, keeping
  "WP-0 is next." exactly.
- **No test changed.** The task is documentation only; `git diff --stat tests/` is empty, so the test
  count stays at the baseline.

Validation: `pytest -q` -- **1735 passed**; the untracked mutation-runner tests were excluded, since
they are not repository state.

Forward guidance: the reconcile plan's Stage 1 Task 1 (Part B) has landed; Stage 1 Task 2 (the docsync
work-package gap) is still open. The next steps are the rest of Stage 1, then Stage 2 (Part C, including
Task 11 for F-B22-8), then Stage 3, then the foundation plan's Tasks 4-10, per Section 3's order list.

### 2026-09-23 - The release-window rule gets a leaf home

Side task, no batch tag: move `_matches_release_criteria` into `scrobblescope/domain.py`, part of
Batch 23 WP-0 Part A. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

- **Scope: the foundation plan's Task 12** (review A card 3, added to Part A on 2026-09-23). The rule
  had two consumers -- the album filter in `orchestrator/_results.py` and the correction worker's
  `release_checks._matches_window` -- and lived in `orchestrator`, which imports `release_checks` at
  module level, so the worker could only reach the rule through a function-local import. That was the
  one documented exception in the SESSION_CONTEXT Section 4 dependency graph.
- **Plan vs implementation: matched exactly, no deviation.** `domain.py` gained the function verbatim
  (body and docstring unchanged) plus `import logging`, placed after `normalize_track_name`.
  `orchestrator/_results.py` deletes the definition and extends its existing `from scrobblescope.domain
  import normalize_name` line to also import `_matches_release_criteria`, so the facade's re-export
  (`scrobblescope.orchestrator._matches_release_criteria`) and `orchestrator/_results
  ._matches_release_criteria` both still resolve unchanged. `release_checks.py` imports the rule from
  `domain` at module level, next to `normalize_name`, and `_matches_window` lost its function-local
  import and cycle-explaining docstring in favour of one sentence naming the shared home. Both import
  orders (`release_checks` before `orchestrator` and the reverse) were run directly and succeeded, since
  the change is specifically about import order. `.claude/SESSION_CONTEXT.md` Section 4 dropped the
  `; orchestrator (facade, DEFERRED -- see note)` qualifier from the `release_checks.py` line and the
  "The one deferred edge" paragraph; a repo-wide check confirmed nothing else cited it. No new edge was
  added: both consumers already import `domain`. `docs/architecture/runtime-system.md`'s
  correction-worker bullet now says the worker and the album filter both read the rule from
  `domain.py`, instead of describing the function-local import.
  `BATCH23_DEFINITION.md` WP-0 Part A and the foundation plan's Task 12 checkboxes are ticked, and
  Section 3's numbered order list marks this step done, keeping "WP-0 is next." exactly.
- **No test changed.** `git diff --stat tests/` is empty; the task is behaviour-neutral and adds no
  test, so the test count stays at the baseline.
- **Fix round 1 (review finding, Important).** The Mermaid diagram in
  `docs/architecture/runtime-system.md` still drew `ReleaseChecks -.->|imported inside a function|
  Album`, an edge the move made false: `release_checks.py` no longer imports anything from
  `orchestrator` at all. Deleted that one line; `ReleaseChecks --> Domain` already carries the real
  dependency, so nothing replaces it. `Album` stays referenced by several other edges, so no node was
  orphaned. A repo-wide grep for the same edge in any other wording found none. The diagram was
  validated with the Mermaid Chart MCP tool (`valid: true`, `diagramType: flowchart`) after the edit.

Validation: `pytest -q` -- **1735 passed**; the untracked mutation-runner tests were excluded, since
they are not repository state.

Forward guidance: WP-0 Part A's foundation-plan tasks (2 and 12) are both done. The next steps are the
reconcile plan's Stage 1 through Stage 3 (Task 11 included), then the foundation plan's Tasks 4-10, per
Section 3's order list.

### 2026-09-23 - Owner rulings: the release-window leaf and F-B22-8

Side task, no batch tag: records three owner rulings, part of Batch 23 WP-0.
Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands. No code
changed.

- **Q0 is settled: the Batch 22 MusicBrainz check is done.** The worker logs
  nothing on success, so the logs could not answer it. `original_release_cache`
  could. It held 121 rows, and 60 were written within a minute of each of the
  owner's two runs with Postgres up (06:04 and 16:34 local). Section 3's
  Batch 22 bullet and the definition's Part B box now record both owner items
  as done. The reconcile plan's Task 1 Step 5 is marked as taken over by this
  commit, because Section 3 must stay true at every commit.
- **Review A card 3 joins Part A** as the foundation plan's Task 12. It moves
  `_matches_release_criteria` into `domain.py`, which deletes the one deferred
  edge in the import graph. It is numbered 12, not 2b, because `task-brief`
  would pull a "Task 2b" heading into Task 2's brief. The rest of the
  2026-09-21 review was already dispositioned in the foundation plan's DoD.
- **F-B22-8 is filed and joins Part C at P2.** With the cache DB down,
  `run_release_checks` skips the whole job. The owner ruled that checks run
  regardless, with only persistence skipped. It is P2 because only local
  development reaches the branch: on Fly.io the database wakes with the app.
  The reconcile plan's Task 11 fixes it; one existing test that asserts the
  skip is replaced there, as Part C allows.

Validation: `pytest -q` -- **1735 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-23 - The remaining shared extractions

Side task, no batch tag: extract the three remaining shared steps, part of
Batch 23 WP-0 Part A. Untagged by owner ruling 2026-09-23 until the whole
of WP-0 lands.

- **What moved, verbatim (controller ruling R12).** In
  `scrobblescope/orchestrator/__init__.py`: `_cap_threshold_exclusions(threshold_exclusions)`
  is the tie-break-commented cap block from `fetch_top_albums_async`, returning the
  (possibly capped) dict; `total_below_threshold` is still computed from the
  uncapped dict before the call. `_process_filtered_albums(job_id, filtered_albums,
  year, sort_mode, release_scope, decade, release_year, limit_results,
  overall_start_time)` is the tail of `_fetch_and_process`, from the
  `_apply_pre_slice` call through `enqueue_release_check` and `return results`;
  `_fetch_and_process` keeps its outer `try`/`except`, `overall_start_time`, and the
  "Processing your albums..." progress call, and now ends with
  `return await _process_filtered_albums(...)`. In `scrobblescope/heatmap.py`:
  `_zero_fill_daily_counts(counts, from_date, to_date)` is Phase 2 of
  `_aggregate_daily_counts`, which now returns its result.
- Each new function's docstring names the Batch 23 Spotify-export path as its
  second caller.
- No test written or modified: `tests/services/test_orchestrator_fetch_and_process.py`
  and `tests/test_heatmap.py` pass unmodified, and `git diff --stat tests/` was
  empty after each of the three moves.

Validation: `pytest -q` -- **1735 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.
