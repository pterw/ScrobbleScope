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
  `docs/history/logs/BATCH22_LOG.md`. Branch: `feat/batch22-enrichment`
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
- **Session handoff, 2026-09-20:** `docs/history/reports/HANDOFF_2026-09-20.md`
  is the entry point for a new agent -- reading order, environment, the gates
  and why they refuse, the schema-migration trap, and the open items.
- **PR #236 merged into `test`** at `fc9098d3` (2026-09-20 21:12). It carried
  the eight commits that landed after PR #234, which had merged the branch as
  it stood at `f6d5926` (2026-09-20 05:06) while the first of those eight was
  05:50 -- a chronological gap, not a rebase. So `test` now holds WP-4, the
  Batch 22 close-out and the Batch 23 definition; before #236 it held none of
  the three.
- **PR #235 (`test` -> `main`) is open and no longer a draft**, mergeable.
  `main` remains the stable Fly.io deployment and still predates Batch 22;
  advancing it is the owner's call, and its review threads are adjudicated in
  `docs/history/reports/ADVISORY_VERIFICATION_2026-09-20.md`.
- **Outbound request identity, fixed 2026-09-20.** `config.APP_USER_AGENT` is
  now the single owner of the application's own name, and
  `create_optimized_session` sends it on every provider session. Until this
  change every Last.fm, Spotify and Deezer request went out as aiohttp's
  default `Python/3.x aiohttp/3.y`, which identifies nobody -- Last.fm asks
  for an identifiable User-Agent on all requests and warns that an anonymous
  client risks suspension. `musicbrainz.py` composes its contact-bearing
  User-Agent on the same identity, so the application cannot disagree with
  itself about its own name.
- **`MUSICBRAINZ_CONTACT` is unset**, so the correction pass is inert: a
  read-only probe on 2026-09-20 confirmed `lookup_original_release` returns
  `(None, None)` with zero HTTP calls. It is **not a secret** -- the value is a
  contact address that travels in the User-Agent header, and nothing
  authenticates with it -- so enabling it is a config change, not a credential
  decision. `DEPLOY.md` named no way to set it, which is why the deployed app
  runs with the pass off; that gap is now documented there.
- **The code defect is closed.** `_musicbrainz_headers` raises instead of
  interpolating the literal string `None` as a contact address, which is what
  it did when called outside the gate that guards it.
- **Next action: the owner opens Batch 23 by naming its branch here.**
  `BATCH23_DEFINITION.md` is written and sits at the repository root, derived
  from
  `docs/superpowers/plans/2026-09-13-batch23-spotify-export-import.md`: eight
  work packages, WP-0 through WP-7, with the deferred Batch 21 frontend and
  accessibility audit inside WP-7, which the batch cannot close without.
  What remains is the branch. It is not `test`, it is named in this section
  before the first commit, or the worktree guard raises WT003, and choosing
  it is an owner decision.
- **Batch 23 is not yet defined**, in the sense the parser reads: no batch is
  open and none is being worked. That phrase has to sit on one line, because
  the scanner reads Section 3 line by line and a wrapped copy of it matches
  nothing. The definition file itself does exist, at the repository root. The
  tool's vocabulary has "not yet defined" and "active" and no word for
  "written, not started", so the sentence is kept and qualified rather than
  removed.
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
- **Owner-facing verification still owed from Batch 22**, neither blocking the
  close-out: a run with `MUSICBRAINZ_CONTACT` configured, to watch corrections
  land against the real service, and restoring the Spotify credentials that
  were disabled to live-test the Deezer fallback.
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

### 2026-09-20 - Architecture diagrams reconciled against the import graph

Side task, no batch tag. Two of the five architecture diagrams were stale, and
verifying them produced a scope problem for the deferred SWE audit that is
worth recording before anyone starts it.

**How the staleness was found.** Not by reading the diagrams against memory,
which is how they went stale, but by extracting the real module-level import
graph with `ast` and comparing edge by edge. That is the check F-B21-61 says
does not exist, and it took one script to demonstrate the need for it.

**`runtime-system.md` had seven missing edges and a wrong count.** Ground truth:
`Routes -> SpotifyClient` (`routes/api.py:22`, `routes/__init__.py:31`),
`Routes -> Domain` (`api.py:15`, `__init__.py:28`), `ReleaseChecks -> Utils`
(`release_checks.py:62`), `Spotlight -> Utils` (`spotlight.py:5`), and
`SpotifyClient -> Domain` (`spotify.py:14`), `DeezerClient -> Domain`
(`deezer.py:17`), `MusicBrainzClient -> Domain` (`musicbrainz.py:23`) were all
real imports absent from the drawing. The prose claimed eight nodes import
`config.py`; the true count is ten, and the list omitted `deezer.py`,
`musicbrainz.py` and `release_checks.py` -- the three modules Batch 22 added.
`App --> Routes` was drawn solid but is deferred inside `create_app`
(`app.py:143`), and the entrypoint's `config` import (`app.py:155`) is deferred
inside `__main__`. Fixed, with import lines cited so the list can be re-checked
rather than trusted.

**A second defect in the same file:** five bullets sat under the heading "Three
things this view deliberately makes visible". Batch 22 added three bullets and
nobody moved the count.

**`top-albums-sequence.md` was materially wrong, not merely incomplete.** A
search for `Deezer|MusicBrainz|release_check|provider|enrich` matched only its
own title: the entire Batch 22 enrichment path was undocumented. Worse, the
existing branch was incorrect independent of that omission -- it drew the
no-cache-hits case as an immediate `raise SpotifyUnavailableError`, while
`_fetch_spotify_misses` (`orchestrator/__init__.py:162`) tries Deezer for every
remaining miss first and raises only on three conditions together: no token,
nothing cached beforehand, and Deezer matching nothing. Persistence was drawn
inside the Spotify branch when it actually happens in the caller after the
Deezer pass returns, which is one row set for both providers rather than one per
provider. The correction worker -- enqueued at
`orchestrator/__init__.py:612`, immediately after `set_job_results` at `:600`
and only on the happy path -- was absent entirely, so it now has its own
lifeline and block.

**Validated structurally, not by eye.** A checker counts `alt`/`opt`/`loop`/
`par`/`subgraph`/`box` against `end` per fence and reports the final depth; all
six mermaid blocks in the repository return to zero, so the edits parse.
`docs/ARCHITECTURE.md`'s "Last verified" date moved to 2026-09-20 and its
section 3 description now names the Deezer fallback and the correction pass.

**Forward guidance, and the reason this matters more than two diagrams.** The
deferred SWE audit's charter (`docs/SWE_AUDIT_CHARTER.md`, retired after its
2026-08-20 execution) is no longer executable as written, because its closed
scope table names thirteen modules that no longer exist in that shape:

- It lists `scrobblescope/orchestrator.py` and `scrobblescope/routes.py`, which
  are packages since Batch 22 WP-0 -- 6 and 5 files respectively.
- It omits `deezer.py`, `enrichment.py`, `musicbrainz.py`, `release_checks.py`,
  `spotlight.py` and `unmatched.py` entirely. `git ls-files 'scrobblescope/*.py'
  app.py` returns **29** files, not the charter's 14.
- Its stated hotspots have moved. It names `_fetch_and_process` (was 151 lines)
  and `results_loading` (was 112). The largest function now is
  **`_render_results_page` at `routes/album_flow.py:126`, 142 lines**, which
  postdates the charter and is in neither list; `_fetch_and_process_heatmap`
  (141) and `_fetch_and_process` (133, now `orchestrator/__init__.py:502`)
  follow it.

The principle count is unchanged at ten (DRY, SoC, SRP, KISS, Dependency
Inversion, Composition over Inheritance, Clean Architecture, Boy Scout Rule,
Law of Demeter, Fail Fast), so the matrix is ten principles against the real
module list -- roughly 280 cells, not the charter's 130. A re-audit therefore
needs its own charter with a current, closed scope table before grading starts;
the retired one is evidence, not a work order. The charter's own Section 2a also
requires a clean worktree, and `AGENT_NOTES.md` plus `requirements-dev.txt` are
currently modified with untracked tooling alongside them, so that is a
precondition rather than a formality.

### 2026-09-20 - README engineering depth and the control-plane narrative

Side task, no batch tag, following the earlier reconciliation in this session.
That pass fixed stale *facts*; this one fixed a missing *argument*. The
architecture's real depth was documented nowhere, and DEVELOPMENT.md had been
stale for weeks about a control plane that is now the largest body of code in
the repository.

**README gained the engineering case, because its audience is developers and
recruiters rather than end users.** Two new pieces:

- **"A search is an ETL pass over an event stream, not a query."** Last.fm
  stores scrobbles -- an unbounded stream of track timestamps -- and has no
  concept of the album a listener played. An album is *produced* by grouping on
  a normalized key and threshold-gating on user criteria, so it is a function
  of the query, not a row. That is why the codebase does not look like CRUD,
  and it is the frame the rest of the architecture reads against.
- **"Owned Interface Components."** The heatmap as a hand-built SVG
  (`createElementNS`, Monday-first via `mondayIndex`, 7 rows against 53 week
  columns, a separate sequential mobile grid because 880px cannot fit a phone
  column), and the log-normalised intensity
  `Math.log10(count + 1) / Math.log10(maxCount + 1)` that keeps a heavy
  listener's mid-range visible on a linear ramp. Plus the theme-resolved
  zero-count cells (an SVG `fill` presentation attribute does not resolve a
  custom property), the 2x cloned-SVG export, the owned pinwheel, the
  deliberately desktop-faithful results export, and the sampled spotlight.

**DEVELOPMENT.md gained two arguments it was missing.** First, *why* the
rotation is a mechanism: it was done by hand three times and failed three
distinct ways -- an entry archived that should have stayed, an entry duplicated
across the boundary, a stale remark left behind -- all silent, because the
document still renders. The parser, renderer and rotation exist because that
task is one an LLM is not reliable at across sessions. Second, the ACID framing
stated honestly: atomicity is real, consistency is real (the invariant checks
are the C), isolation is partial (filesystem-scoped lock, no cross-machine
coordination, readers not serialised), durability is within filesystem
semantics. The precise description is an atomic file-transaction and invariant
enforcement system; the acronym is useful shorthand and stops being useful the
moment it is read as a database guarantee.

**The `.docsync.toml` extraction story is now written down**, which was the
largest gap. The declaration layer exists specifically so a second repository
supplies its own config without touching the mechanism -- and `declarations.py`
carries no ScrobbleScope value at all. What remains tied is enumerated as a
table rather than asserted: document paths, the scanned corpus and its
`allow_files` list, `[retired.allow_after] "PLAYBOOK.md"`, `[closeout]
admit_from_batch = 22`, the design-token `[[value]]` entries, and
`_LIVE_DOCUMENT_PATHS` in `integrity.py` (verified at line 100). The section
also records why finishing it now would cost more than it saves: the remaining
modules are the largest in the package, and making them generic before there is
a second consumer buys indirection rather than reuse.

**Also added:** the three pieces that make the package a workflow rather than
a mechanism -- the commit preflight, the opt-in hook installer (not installed
here), and the CLI surface. README's methodology section now says the tooling
is larger than the application on purpose and points at DEVELOPMENT.md for the
honest extraction state.

**Deviations:** one, self-inflicted and caught. Authoring the console section
introduced a zero-width space (U+200B) into DEVELOPMENT.md, violating the
ASCII-only authoring rule. Found by scanning for non-ASCII code points rather
than by eye, removed with a targeted rewrite, and re-verified clean. No other
document or file carried one.

**Validation:** `pytest -q` -- **1532 passed**. `pre-commit run --all-files` --
all ten hooks pass. `doc_state_sync.py --check` exit 0. Non-ASCII scan of
README.md and DEVELOPMENT.md: none.

**Forward guidance:** DEVELOPMENT.md is still the narrative and
`docs/architecture/documentation-tooling.md` still owns the DOC001-DOC023
catalogue; the split was preserved rather than duplicated. The deferred plans
are unchanged and stay deferred.

### 2026-09-20 - DEVELOPMENT.md and README.md reconciled with the control plane

Side task, no batch tag. Two documents described a repository that no longer
exists, and one gate comment described a migration that had already finished.

**DEVELOPMENT.md was materially stale.** Its docsync section said the package
had "Six focused modules" and listed six test files. It has **twelve** modules
(`declarations`, `closeout`, `archives`, `findings`, `transaction`, `markdown`
were added by Batch 22) and twelve matching test files in `tests/`. The
worktree section named only `check_worktree_alignment.py` and a spec document,
omitting the seven `_worktree_guard_*.py` modules and the `WT000`-`WT014`
codes. The gate section stopped at "starts and stops its own loopback server"
and never named `port 0`, the `finally`, the 44px touch target, the 3:1
composited-contrast check, the viewport profiles or stylesheet isolation. Two
lines were also written in the present tense of a batch that has closed
("Batch 21 uses...", "The active batch definition owns...").

**README lacked four architectural facts** it should carry at product level:
the cache talks to Postgres in arrays via `unnest($1::text[], ...)` rather than
row by row; a stale schema identifies itself by SQLSTATE (`42703`, `42P01`)
instead of being mistaken for network turbulence; Spotify's removed batch
endpoint answers `403`/`404`/`410` and degrades to one request per album; and
the opening prose said the badge "is the live state", which read awkwardly.

**A new DEVELOPMENT.md section records the extraction intent** owner-stated
2026-08-25 and owned by `AGENT_NOTES.md`: this repository is also a template
being extracted, and the three control-plane components are at very different
maturity. The section states that honestly rather than aspirationally -- the
worktree guard is structurally complete, docsync is close, and the frontend
gate is the least extracted, with its decomposition plan deliberately parked.
It also records the standing constraint: do not start the extraction as a side
task; write new tooling so it stays cheap.

**A real defect was found and fixed in the process.**
`frontend_gate.py:209-215` carried a comment describing "the job-backed
Results and Unmatched templates" as still on Bootstrap, directly above an
already-empty `LEGACY_PAGES`. There is no residual Bootstrap: every template
carries an opt-out note, `static/css/` has no Bootstrap file, and README
already said "Bootstrap is gone". The only Bootstrap left is a test fixture
that proves a page *would* collide if it loaded both frameworks. A reader
trusting the comment would have concluded two page families were unmigrated.
This is anti-pattern 15 in miniature -- the comment had drifted from the code
beneath it, and only reading the source surfaced it.

**Deviations: none.** No production behaviour changed beyond the comment fix.
`docs/architecture/documentation-tooling.md` remains the owner of the control
plane; DEVELOPMENT.md links to it rather than restating the DOC catalogue, per
Rule 1.

**Validation:** `pytest -q` -- **1532 passed**. `pre-commit run --all-files` --
all ten hooks pass. `doc_state_sync.py --check` exit 0. `ruff check` clean.

**Forward guidance:** the extraction plans
(`docs/superpowers/plans/2026-09-12-repository-agnostic-plan-spec-guards.md`
and `.../2026-09-12-reusable-frontend-ci-verification-components.md`) both
carry "do not execute until" conditions and neither is scheduled. The frontend
plan's stated line count for `frontend_gate.py` (4,008) is now 4,353, so
re-measure before relying on its inventory. PR #235's summary was completed in
the same session and its review threads are adjudicated in
`docs/history/reports/ADVISORY_VERIFICATION_2026-09-20.md`.

### 2026-09-20 - PR #234 advisory verification

Side task, no batch tag. PRs #233 and #234 merged with their review threads
deliberately unaddressed, so adjudicating them was the other half of the
pre-integration task. The question was not "are they open" but "are they
true".

**Method.** Read all threads from the GitHub API (35 review comments on #233,
22 on #234, plus issue comments and reviews), then checked each substantive
claim against on-disk code by grepping the tree, reading the cited function,
or running the cited gate. Nothing was accepted on the strength of a bot's own
summary.

**Result: four refuted, one partly true, one by design, one out of scope.**
Refuted: the DOC023 negation false positive (already handled by
`_NEGATED_OUTCOME_RE`); the `_TERMINAL_SUFFIXES` escaping gap (`re.escape` is
already there, line 354); the `newest == 0` blank-line nitpick (the guard is
deliberate, and `495e9c2` already fixed the real case); and the claim that
DOC023 is documented as both blocking and non-blocking (the catalogue states
the blocking and grandfathered-warning roles as two populations, and the code
implements exactly that). By design: hard-failing a stale archive index
(`DOC020`) is Rule 7's refusal to guess which side of a disagreement is the
history worth keeping. Out of scope by owner ruling: complexity and coupling
advisories, recorded in the report so nobody re-adjudicates them.

**One refuted claim surfaced a real defect.** Graphify rated
"`AlbumMetadata` cache-row method renamed and now requires extra arguments" as
high risk. Nothing calls the method, so nothing broke -- but a repo-wide search
found `as_cache_row` at its definition and in its own test only, while both
production sites build the row tuple inline (`_details.py:137` as six elements,
`_deezer_fallback.py:83` as nine). The persistence order therefore has two
owners, and a test asserts the copy nothing writes. Filed as F-B22-7 rather
than fixed: retiring the method or rerouting a builder is a choice between two
working shapes with a Batch 22 test contract around one of them.

**A vacuity guard earned its place.** The first run of the DOC023 probe used an
`##` heading, which `FINDING_HEADING_RE` does not match, so no finding parsed
and every case read "blocks = False". The output looked like a clean refutation
of the whole claim. Adding a guard that reports `VACUOUS PROBE` when no case
parses caught it; the corrected run is live on 6 of 14 cases with every
expectation met. Recorded because "the gate stayed silent" and "the gate was
never reached" are the same output and different facts.

**Deviations: none.** No production behaviour changed. The two findings are
records, not repairs, and the report is
`docs/history/reports/ADVISORY_VERIFICATION_2026-09-20.md`.

**Validation:** `pytest -q` -- **1532 passed**, unchanged (no runtime code
touched). `doc_state_sync.py --check` exit 0.

**Forward guidance:** the residual DOC023 false positive ("No action needed
yet." blocks) is deliberate and filed as F-DOCSYNC-14; widening the negation
window would buy silence on two phrases and pay for it by missing real
completion claims, which is the failure the gate exists to prevent. Do not
"fix" it without reading that entry.
