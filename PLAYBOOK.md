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
- **Batch 22 is active.** Definition: `BATCH22_DEFINITION.md` (repo root).
  Branch: `feat/batch22-enrichment` (worktree off `test`). Scope: album
  enrichment moves behind a provider contract, Deezer answers when Spotify
  cannot, and MusicBrainz corrects a reissue year to the album's original
  while the results page is open. Plan of record:
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
- **WP-4 is in progress.** Task 10 landed
  `GET /api/release_checks?job_id=`, which serves the correction worker's
  findings to an open results page. Task 11 remains.
- **Next action:** Task 11, WP-4's live disclosure -- poll that endpoint from
  the results page, mark corrected rows in place without moving them, and
  announce moved-in albums with a reload action. WP-4 closes with it, and
  **WP-5 is next** after that: docs and close-out. (Section 4's WP-4 entry
  advances the derived pointer to WP-5 as soon as a WP-4 entry exists; the
  work package itself is not finished until Task 11 is.)
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

### 2026-09-14 - MusicBrainz client (Batch 22 WP-3)

Scope: `docs/superpowers/plans/2026-09-13-batch22-enrichment-providers.md`
Task 7, the first task of Phase 3. New module, no caller wired yet (Task 8
consumes it).

`scrobblescope/musicbrainz.py` (new): `lookup_original_release(session,
artist, album)` returns `(mb_release_group_id, "YYYY-MM-DD")` on a trusted
match or `(None, None)` -- both cacheable, matching
`original_release_cache`'s null-`mb_release_group` "checked, nothing
found" row from Task 2. A candidate is accepted only when its MusicBrainz
`score` is at least 90 **and** its normalized artist-credit/title match the
searched key (`scrobblescope.domain.normalize_name`, already used by
`deezer.py`); score alone is rejected because it ranks text similarity, not
identity -- a high-scoring tribute act or same-titled album by a different
artist must not silently mis-date a real one. The Lucene release-group
query (`releasegroup:"..." AND artist:"..."`) escapes quotes and Lucene
operators in both fields rather than passing them through raw. With no
`MUSICBRAINZ_CONTACT` configured, or `MUSICBRAINZ_ENABLED=False`, the
client returns `(None, None)` without making a request: MusicBrainz blocks
anonymous clients, so an unconfigured contact would only guarantee a
rejected request against the shared 1-request/second budget. A 503 waits
and retries via the existing `retry_with_semaphore`, asking the limiter
again on every attempt.

`scrobblescope/utils.py`: `get_musicbrainz_limiter()`, same
`_ThrottledLimiter` pattern as `get_deezer_limiter` (a global cross-thread
throttle plus a per-loop `AsyncLimiter`) -- this is what makes the 1
request/second limit process-wide rather than per-loop, ahead of Task 9's
dedicated worker thread. `scrobblescope/config.py`: `MUSICBRAINZ_CONTACT`,
`MUSICBRAINZ_ENABLED` (default True), `MUSICBRAINZ_REQUESTS_PER_SECOND`
(default 1), `MUSICBRAINZ_SEARCH_RETRIES` (default 3, mirrors
`DEEZER_SEARCH_RETRIES`), and `MUSICBRAINZ_CHECKS_PER_JOB` (default 60,
unused until Task 9). `MUSICBRAINZ_REQUESTS_PER_SECOND` and
`MUSICBRAINZ_SEARCH_RETRIES` are not in the plan's own file list for this
task but follow the existing per-provider rate/retry constant pattern
(`DEEZER_REQUESTS_PER_SECOND`, `DEEZER_SEARCH_RETRIES`) rather than a
magic number inside `utils.py`/`musicbrainz.py`.

`tests/services/test_musicbrainz_service.py` (new, 10 tests): query
building and Lucene escaping, the score-floor-and-name-match rule
(including a high-scoring wrong-artist rejection), the return shape on a
match and on no candidates, a 503-then-success retry asserting the limiter
is entered on every attempt, the User-Agent contents, and the two
no-contact/disabled-by-flag paths asserting zero requests.

Validation: `pytest -q` -- **1079 passed** (was 1069; +10 new). No frontend
change, so the frontend gate is unaffected; its last measurement (29/29)
still stands. `doc_state_sync.py --check` passes clean (the root
`BATCH22_DEFINITION.md` warning is expected while the batch is active).

### 2026-09-14 - README architecture, tech stack, and diagram refresh (Batch 22 WP-2)

Scope: owner follow-up to the README pass below, given mid-session
(2026-09-14) -- overrides that entry's "deliberately not touched" call.
The owner wants the Mermaid diagram redrawn now (it named modules that
predate WP-0's split -- `routes.py`, `orchestrator.py` -- and never
mentioned Deezer), the Architecture prose and Tech Stack row enhanced, and
new writing to avoid pointers to actual code in favour of self-contained
prose. This still does not duplicate WP-5's own pass: WP-5 owns the
dependency graph and pipeline-sequence detail in
`docs/architecture/runtime-system.md`, which this diagram does not
attempt -- the owner's brief was "keep it simple," a conceptual diagram
(Browser, Flask, background job, Last.fm, Spotify, Deezer, PostgreSQL
cache) rather than a module map.

Changed: the Architecture section's prose and Mermaid diagram (no
filenames, Spotify-then-Deezer fallback shown as a dotted edge), the
`docs/ARCHITECTURE.md` pointer sentence removed (the section is now
self-contained), the APIs tech-stack row reworded to state the fallback
inline, a Deezer clause added to the Prerequisites line ("needs no key"),
and the two Key Implementation Highlights bullets that still said
"Spotify metadata" corrected to name both providers -- left stale by the
entry below, they would have directly contradicted the rewritten
Architecture section above them.

Validation: doc-only; `doc_state_sync.py --check` passes clean. No code
changed, so the Task 6 entry's **1069 passed**, 29/29 still stands.

### 2026-09-14 - README pass for the Deezer fallback (Batch 22 WP-2)

Scope: owner-requested, after Task 6 landed and before a `/handoff`
close-out -- not one of Task 6's own files, but small (under 20 lines) and
directly tied to WP-2's own work, so treated as an in-WP deviation rather
than a separate side-task entry (AGENTS.md Proposal and Design Rules,
item 2). `README.md`'s Unmatched-report paragraph named `no_spotify_match`
as "albums Spotify could not identify" -- true before Task 5, false after
it (the reason now fires only when neither provider matches); fixed as a
stale-claim correction, not new scope. Also added: one Features bullet on
the Deezer fallback and per-row provider attribution, a Deezer clause on
the APIs tech-stack row, a one-line pointer from the Roadmap section to
PLAYBOOK's Section 3 for the fallback and the original-release-year work
that follows it, and a Deezer line in Acknowledgements.

Deliberately not touched: the architecture Mermaid diagram and the fuller
provider data-flow prose. PLAYBOOK Section 3's WP-0 entry already commits
those to WP-5's own README/`docs/architecture/runtime-system.md` pass, so
redoing them here would be exactly the double effort that entry ruled out.

Also fixed `CLAUDE.md`'s graphify section, which restated
`.claude/CLAUDE.md`'s rules inline instead of pointing to
`.claude/skills/graphify/SKILL.md` -- a duplication against the file's own
stated "holds no project facts of its own" rule. `CLAUDE.md` is
git-ignored (confirmed via `git check-ignore`), so this has no commit of
its own.

Validation: no code changed, so `pytest -q` and the frontend gate are
unaffected -- Task 6's own entry above has the current measurement,
**1069 passed**, 29/29; confirmed `doc_state_sync.py --check` still
passes clean.

### 2026-09-13 - Show the album's own provider in the UI (Batch 22 WP-2)

Scope: `docs/superpowers/plans/2026-09-13-batch22-enrichment-providers.md`
Task 6, the last task of Phase 2. Real behaviour change: results and
unmatched rows now link to the album's own provider instead of always
building a Spotify URL.

Read the task's hard blocker first: `developers.deezer.com/guidelines`
(plus its linked `/guidelines/logo` page; `deezerbrand.com`, where the
detailed logo spec lives, did not render -- JS-only page, no image-fetch
tool available this session). Two facts recorded here per the task's own
instruction to write them "next to the artwork and the link":
"Local Storage/Offline Storage of audio data is strictly forbidden" is
scoped to audio only, and says nothing about metadata or artwork --
confirms the owner's own reading and means nothing here changes about
caching Deezer's release dates, cover art, or track durations in
`spotify_cache`. Separately, "Each application using Deezer API/SDKs must
have to include a clearly visible Deezer Logo" is a real, unmet
requirement: no tool available could fetch either provider's actual logo
asset (no image-fetch tool; hotlinking a guessed brand-CDN URL was ruled
out as unsafe). Put to the owner directly (F-B21-60 already made the same
call for Spotify -- "Use Spotify's asset as supplied, not a redrawn
glyph"), the ruling was to ship a text attribution badge now and swap in
each provider's real logo later, filed as F-B22-4. F-B21-60 itself gets a
short addendum recording this partial progress; its own scope (the artist
spotlight card's crop/overlay/animation) is unchanged and still open --
Task 6's file list never named the spotlight card.

Plan vs implementation: `orchestrator/_results.py`'s release-scope-miss
branch (in `_build_results`) did not carry `provider`/`album_url` even
though the matched-result branch has since Task 5 -- an album Deezer
matched but the release filter then excluded would have shown no
attribution and no link on `/unmatched`. Added `_album_provider(cached)`/
`_album_url(cached)` (the same Task 5 helpers) to that dict; not in the
plan's own Task 6 file list, but a direct consequence of wiring
`album_url` through the one place it was still missing.

`templates/results.html` and `templates/unmatched.html`: both album-rank
and album-title links switch from `https://open.spotify.com/album/{{
spotify_id }}` to `{{ album_url }}` (guarded on truthiness, so a row with
neither renders plain text as before); a new `.provider-badge` text link
sits beside the artist name, guarded on `provider and album_url` together
so it never appears without something to link to. Both templates carry an
inline comment citing the two Deezer facts above, next to the badge markup
itself. `static/js/results.js`'s CSV export reads a new `data-provider`
attribute and appends a `"Provider"` column.

`scripts/dev/_frontend_gate_results.py` gains
`check_results_provider_attribution`: one Spotify-sourced and one
Deezer-sourced row, asserting each links to its own host
(`open.spotify.com` / `deezer.com`), each shows a visible provider badge
naming its provider and linking to the same URL, and the CSV export
carries both provider values. Switching the link source from `spotify_id`
to `album_url` broke two existing fixtures that set `spotify_id` directly
without `album_url`: `check_unmatched_report`'s release-scope rows (fixed
by adding matching `provider`/`album_url` fields) and
`check_results_interactions`'s pinned CSV row string (fixed by appending
the new column's empty value, since that fixture sets neither field).
`tests/test_routes.py` gains two tests: a results-page row-by-provider
link/badge check, and an unmatched-page release-scope-miss check for the
same thing.

Validation: `pytest -q` from the worktree cwd -- **1069 passed** (1067 +
2). Frontend gate: **29 checks passed in 51 runs** (28/50 + the new
check). Task 7 (MusicBrainz client, Phase 3) is next.

### 2026-09-13 - Deezer fallback wired into the orchestrator (Batch 22 WP-2)

Scope: `docs/superpowers/plans/2026-09-13-batch22-enrichment-providers.md`
Phase 2 Task 5. Real behaviour change: album enrichment no longer depends
on Spotify alone.

Plan vs implementation: kept the phase order (Spotify search, Spotify
details, then one Deezer pass over what is left), but the plan's "does not
rewrite them" line from Task 3 applied only to Task 3 -- Task 5 had to
touch `orchestrator/_search.py` itself, because deferring the
unmatched-or-not decision to after Deezer's turn means a search miss can
no longer be written to job unmatched immediately. `_run_spotify_search_phase`
now returns a third value, `search_miss_keys`, instead of calling
`add_job_unmatched`; its own two tests (`test_run_spotify_search_phase_all_misses_returns_empty_maps`,
`test_run_spotify_batch_detail_phase_empty_id_list_skips_api_call`) are
updated to match, and a new `orchestrator/_deezer_fallback.py` phase file
(mirroring `_search.py`/`_details.py`'s per-phase convention) owns the
Deezer pass and the now-deferred unmatched write, with reason text "No
match on Spotify or Deezer" (`reason_code` unchanged: `no_spotify_match`).
"Still missing after Spotify" is computed as `cache_misses.keys() -
cache_hits.keys()` post-detail-phase, which uniformly catches both a
search miss and a detail-fetch failure (the latter was already silently
dropped before this task, not newly introduced).

`_detect_spotify_total_failure` is renamed `_detect_enrichment_total_failure`
(swept: tests/services/test_orchestrator_helpers.py's four tests and their
own names). `_fetch_spotify_misses` snapshots `cache_hits` emptiness before
any mutation (`had_cache_hits`) so the post-Deezer `SpotifyUnavailableError`
check reads the pre-run state, not cache_hits after Deezer has already
promoted its own matches into it -- item 4's "Deezer enriches everything
and the job succeeds" only holds if that snapshot is taken first.

`orchestrator/_results.py`'s `_build_results` gains `provider` and
`album_url` per result (`_album_provider`/`_album_url` helpers), reading
the provider columns Task 2 added with a fallback to the classic
`open.spotify.com` URL built from `spotify_id` for rows or live fetches
that predate the provider columns -- Task 6 wires these two fields into
templates/CSV, but the plan's own Task 5 test list asks for them at the
`process_albums` output, so they land here. `unmatched.py`'s
`CATEGORY_METADATA` for `REASON_NO_SPOTIFY_MATCH` is reworded ("No Match
Found" / "Not Found" / mentions Deezer) to match; its one pinned test
(`tests/test_unmatched.py`) is updated in the same commit.

Job progress: the Deezer phase reports 60-75%; the two fixed
post-`process_albums` markers ("Adding album art...", "Compiling...")
move from 60/80 to 80/85 so progress never runs backward when Deezer's
phase ran up to 75%. No test pinned the old 60/80 values.

Validation: `pytest -q` from the worktree cwd -- **1067 passed** (1061 +
6 new integration tests in `tests/services/test_orchestrator_process_albums.py`,
covering the plan's five Step 1 scenarios: Spotify-matches-everything
skips Deezer, a Spotify miss falls through to a Deezer match with
`provider`/`album_url` set, neither provider matching registers one
unmatched entry with the new reason text, a Deezer-only run with no
Spotify token succeeds, that same no-token run raises
`SpotifyUnavailableError` only when Deezer also fails, and a Deezer match's
persisted row carries `provider`/`provider_album_id`/`provider_url` with
`spotify_id` left `None`). Fixed two pre-existing tests
(`test_process_albums_partial_cache_token_failure_uses_cached_results`,
`test_process_albums_all_misses_token_failure_raises`) that would
otherwise have made real, unmocked network calls to Deezer once this task
landed -- both now mock `search_deezer_album` explicitly. Frontend gate:
28 checks passed in 50 runs (unchanged from WP-0's baseline; `unmatched.py`'s
reworded copy did not regress the gate's rendered-page assertions). Task 6
(show the album's own provider in the UI) is next; note its own blocker:
read Deezer's attribution guidelines before shipping any Deezer-sourced
result.

### 2026-09-13 - Spotify calls behind spotify.enrich_albums (Batch 22 WP-1)

Scope: `docs/superpowers/plans/2026-09-13-batch22-enrichment-providers.md`
Phase 1 Task 3. No behaviour change to any running job -- `enrich_albums`
is a new, additional entry point; `process_albums`'s real path still calls
`_run_spotify_search_phase` and `_run_spotify_batch_detail_phase` directly,
unchanged, per Phase 2's Task 5 owning the wiring.

Plan vs implementation, one deliberate reading: `scrobblescope/orchestrator.py`
is a package since WP-0, so "Modify: scrobblescope/orchestrator.py" is read as
"expose the new seam on the facade" rather than touching the phase functions
the plan explicitly says to leave alone ("this task adds a seam, it does not
rewrite them"). `scrobblescope/spotify.py` adds `enrich_albums(session,
misses, token)`: concurrent per-key search via `search_for_spotify_album_id`,
then one `fetch_spotify_album_details_batch` call for every match, returning
`({key: AlbumMetadata}, unmatched_keys)`. `misses` reads the same
`{key: original_data}` shape `process_albums`'s `cache_misses` already uses
(only the keys matter here), so Task 5 can pass it through unchanged.
`scrobblescope/orchestrator/__init__.py` imports `enrich_albums` into the
facade and `__all__`, alongside the other `spotify.py` dependencies, so
`mock.patch("scrobblescope.orchestrator.enrich_albums")` reaches it once a
later task wires it in.

**Fix folded in, caught by Pylance during this task (owner):**
`AlbumMetadata.image_url` (`scrobblescope/enrichment.py`, Task 1) was typed
`str`, but a Spotify album can have no cover art -- `images[0].get("url")`
returns `str | None`, so the type was wrong from Task 1's commit, not
something Task 3 introduced. Widened to `str | None`; behaviour was already
correct at every call site (`image_url or None`-shaped fallbacks exist
elsewhere), only the declared type was too narrow. Added a boundary test
(`test_enrich_albums_handles_missing_cover_art`) pinning the no-images case.

Validation: `pytest -q` from the worktree cwd -- **1054 passed** (1049 + 5
new: 4 `enrich_albums` tests in `tests/services/test_spotify_service.py`,
1 facade-exposure test in `tests/services/test_orchestrator_fetch_spotify.py`).
The frontend gate -- 28 checks passed in 50 runs, matching WP-0's baseline
exactly, confirming the facade import didn't disturb `process_albums`'s real
path. Phase 1 (the provider contract) is now complete; Phase 2 Task 4
(Deezer client) is next.

### 2026-09-13 - Cache columns for any provider (Batch 22 WP-1)

Scope: `docs/superpowers/plans/2026-09-13-batch22-enrichment-providers.md`
Phase 1 Task 2. No behaviour change -- the new columns and table are unused
until Task 3+ wires a caller to them.

Plan vs implementation: matched. `init_db.py` adds
`ALTER TABLE spotify_cache ADD COLUMN IF NOT EXISTS provider/provider_album_id/
provider_url` plus `ALTER COLUMN spotify_id DROP NOT NULL` (a Deezer-only row
cannot satisfy the old constraint), backfills `provider='spotify'`,
`provider_album_id=spotify_id` for existing rows, and creates
`original_release_cache` (`artist_norm`, `album_norm`, `mb_release_group`,
`original_release`, `checked_at`, PK on the norm pair) exactly as specified.

`scrobblescope/cache.py`: `_batch_lookup_metadata` and `_batch_persist_metadata`
now read/write the three new columns. **Deviation, deliberate:**
`_batch_persist_metadata`'s row tuple grows from 6 to up to 9 elements
(`+provider, provider_album_id, provider_url`), but the extra three are
optional -- a 6-element row (today's only caller,
`orchestrator/_details.py:137`, unchanged in this task) defaults to
`provider="spotify"`, `provider_album_id=spotify_id`, `provider_url=None`.
This keeps Phase 1's "no behaviour change" for that caller while still
tagging its writes correctly, so jobs run after this commit don't need the
one-time backfill to be re-run. Added
`_batch_lookup_original_release`/`_batch_persist_original_release` against
the new table, TTL'd on `ORIGINAL_RELEASE_TTL_DAYS` (`config.py`, default
365 -- an original release date does not change, so the TTL only guards a
bad match). A cached row with a null `mb_release_group` is a valid "checked,
nothing found" cache hit, distinct from no row (uncached).

Validation: `pytest -q` from the worktree cwd -- **1049 passed** (1037 +
12 new: 4 schema tests in `tests/test_cache_schema.py`, 8 cache-layer tests
in `tests/services/test_cache.py`). The 6-tuple-legacy-default behaviour and
the pre-existing `tests/test_repositories.py` cache tests are covered
without modification, confirming the defaulting path preserves today's
persisted rows.

**Owner-verified against real Postgres, 2026-09-13:** owner ran the app on
localhost against the Docker `ss-postgres` container (mirrors the deploy
target, not a mock), which re-runs `init_db.py`'s migration on startup.
No regressions observed. This is real evidence the `ALTER TABLE` statements
apply cleanly to a live database, beyond the unit tests' string assertions
on `init_db.py`'s source -- partial coverage of the plan's own Verification
item 5 ("run `init_db.py` against a copy of the production schema"); the
Deezer-round-trip half of that item waits on Phase 2. Task 3 (Spotify calls
behind `spotify.enrich_albums`) is next.

### 2026-09-13 - Provider contract, AlbumMetadata value object (Batch 22 WP-1)

Scope: `docs/superpowers/plans/2026-09-13-batch22-enrichment-providers.md`
Phase 1 Task 1. No behaviour change yet -- `AlbumMetadata` is not wired into
any caller.

Plan vs implementation: matched exactly. `scrobblescope/enrichment.py` adds
`AlbumMetadata`, a frozen dataclass (`provider`, `album_id`, `url`,
`release_date`, `image_url`, `track_durations`) with `as_cache_row_fields()`
returning the six fields as a tuple in cache-column order.
`track_durations` holds seconds keyed by `normalize_track_name`, the shape
`_build_results` already reads -- documented on the class rather than
duplicated at each call site.

Validation: `pytest -q` from the worktree cwd (not the primary checkout,
which collects its own stale tree and undercounts) -- **1037 passed**
(1036 baseline + 1 new). Task 2 (cache columns) and Task 3 (Spotify calls
behind `spotify.enrich_albums`) are next; see
`docs/superpowers/plans/2026-09-13-batch22-enrichment-providers.md` for
progress notes per task.

### 2026-09-13 - Module split, behaviour-neutral (Batch 22 WP-0)

Scope: split `scrobblescope/routes.py` (985 lines) into a `routes/` package
and `scrobblescope/orchestrator.py` (1035 lines) into an `orchestrator/`
package, per `BATCH22_DEFINITION.md` WP-0. No behaviour change; the
acceptance criterion was every existing test passing unmodified.

Plan vs implementation: matched the definition's four named phases for
`orchestrator/` (`_search`, `_details`, `_cache`, `_results`) and the four
named concerns for `routes/` (`pages`, `album_flow`, `heatmap_flow`, `api`),
each behind a facade `__init__.py` that keeps the pipeline glue
(`process_albums`, `_fetch_and_process`, `background_task`,
`fetch_top_albums_async`) or shared job-context helpers respectively. One
`Blueprint` (`bp`, name `"main"`) is still shared across the four route
files, so every endpoint name and `url_for()` call is byte-identical --
`routes/` is a package of route files sharing one blueprint, not four
separate blueprints, which is the narrower reading of "package of
blueprints" that kept templates and endpoint names untouched.

The load-bearing discovery: roughly 24 names across both modules are
`mock.patch`/`monkeypatch.setattr` targets in the existing test suite,
addressed as `scrobblescope.orchestrator.<name>` or
`scrobblescope.routes.<name>`. A name imported directly into a phase
submodule stops being reachable by that patch once the code that calls it
moves out of the facade file, because the patch only replaces the
attribute on the facade module's own namespace. Every submodule therefore
imports its parent package (`from scrobblescope import orchestrator as
_orchestrator` / `... routes as _routes`) and reads cross-cutting
dependencies through that live reference at call time, not through its own
`from x import y`. The facade files keep every original top-level import
unchanged, even where their own code no longer calls it directly, so the
attribute still exists for a submodule or a test to reach. Both `__init__.py`
files carry an explicit `__all__` documenting that contract and satisfying
ruff's unused-import check (`ruff-check --fix` would otherwise delete an
import kept only for re-export).

Deviation: `docs/architecture/*.md`, `README.md` and `AGENT_NOTES.md` still
cite a few pre-split `orchestrator.py`/`routes.py` paths. The two
load-bearing ones in `AGENT_NOTES.md` (the Windows-asyncio ProactorEventLoop
note, cited from two places) are fixed in this commit; the rest are left for
WP-5's already-scoped README and `docs/architecture/runtime-system.md` pass
rather than swept twice. `docs/superpowers/plans/` citations are dated
plan documents and are not touched, per the dated-entry exemption.

Validation: `pytest -q` -- **1034 passed**, unmodified from every test file
in the suite. `scripts/dev/frontend_gate.py` -- 28 checks passed in 50 runs
across chromium and firefox, matching the batch-open baseline. `ruff check`
and `ruff format` clean on both new packages. `scripts/doc_state_sync.py
--check` passes (the root `BATCH22_DEFINITION.md` warning is expected while
the batch is active).

Forward guidance: WP-1 (the provider contract) adds `scrobblescope/
enrichment.py` and moves the Spotify calls behind `spotify.enrich_albums`,
which lands inside `orchestrator/_search.py`'s and `_details.py`'s existing
phase boundaries rather than requiring another restructure.

### 2026-09-14 - Apply cached original-release corrections (Batch 22 WP-3)

Scope: `docs/superpowers/plans/2026-09-13-batch22-enrichment-providers.md`
Task 8, the second task of Phase 3. Applies a MusicBrainz finding already
sitting in `original_release_cache` -- populated by Task 9's worker, not
yet built -- so this task is display-only wiring with no live MusicBrainz
call of its own.

Plan drift, expected: the plan's file list still names
`scrobblescope/orchestrator.py`, which the WP-0 module split above turned
into a package before this task ran. The real targets are
`scrobblescope/orchestrator/_results.py` (`_build_results`,
`_get_user_friendly_reason`), `scrobblescope/orchestrator/_cache.py` (new
`_lookup_cached_original_release`), and `scrobblescope/orchestrator/__init__.py`
(`process_albums` wiring). The owner flagged this drift before the task
started; no separate deviation write-up needed beyond this note.

`scrobblescope/orchestrator/_cache.py`: `_lookup_cached_original_release(conn,
keys)` mirrors `_lookup_cached_metadata` -- returns `{}` without raising if
`conn` is falsy or the query fails, since a missing correction must only
skip the display upgrade, never block a job. `scrobblescope/orchestrator/__init__.py`:
`process_albums` calls it inside the same try block that already holds
`conn` open for Phase 1-4 (right after `_persist_new_metadata`, before the
`finally: conn.close()`), keyed on `list(cache_hits.keys())` -- these are
already `(artist_norm, album_norm)` tuples, the same shape
`original_release_cache`'s primary key uses, so no new key derivation was
needed. The result feeds into `_build_results` as a new trailing
`original_release_hits` parameter.

`scrobblescope/orchestrator/_results.py`: `_build_results` now looks up
each album's key in `original_release_hits`; a finding with a non-null
`original_release` becomes the `release_date` used for both
`_matches_release_criteria` and the displayed date, and the provider's own
date survives as a new `provider_release_date` field on the result (or the
unmatched entry, if the correction excludes the album). No finding, or a
cached "checked, nothing found" row (both fields null), leaves the result
shape identical to before this task -- `provider_release_date` is only
added when a correction actually applied. `_get_user_friendly_reason`
gained a `corrected` flag: when true, the wording changes from "Released
X instead of Y" to "First released in X, not Y" (and the decade/custom
equivalents) so a MusicBrainz-corrected exclusion reads as "this is the
true original year," not "the app misread the provider's date."

`tests/services/test_orchestrator_helpers.py` (4 new tests): a correction
that excludes an album from its filter year (reason text asserted
verbatim), the same correction under the original year keeping the album
with `provider_release_date` preserved, the no-correction/nothing-found
case proving behaviour is unchanged (both the omitted-kwarg case and the
explicit-null-row case), and an adversarial sweep of `_get_user_friendly_reason`'s
`corrected=True` wording across all four scopes (same/previous/decade/custom),
not just the one scope the plan's own example uses -- per AGENTS.md Test
Quality Rules, a new branch needs its own test, not just integration
coverage through `_build_results`.

Audit reconciliation, 2026-09-14: commit `f971991` implements Task 8's
runtime behavior once, at the intended seams; no duplicate implementation or
non-working path was found. Its tests did not prove that the normal
`process_albums` run forwarded cached corrections into `_build_results`, and
the new cache wrapper lacked direct no-connection and failure coverage. Three
focused tests now close those gaps. The process seam test was also run with
the forwarding argument temporarily disconnected and failed on the expected
2011-vs-1977 result, then passed again after restoration. The root definition,
plan Progress section, Section 3 and SESSION_CONTEXT now agree that WP-0
through WP-2 are complete, WP-3 owns Tasks 7-9, and Task 9 is next. This
entry's heading was left tagged WP-1 at the time, as a historical commit
record rather than the canonical work-package mapping. **Superseded
2026-09-20:** the untagged side-task entry below the end marker retags this
heading and five others, because `ENTRY_BATCH_RE` parses that tag into the
managed STATUS block, so a wrong tag is a wrong dashboard rather than a
harmless label.

**Docsync gotcha found while landing this entry -- two layers, one
already filed:** (1) this section of Section 4 is append-ordered (oldest
entry on top, new entries added at the bottom, then the tool reverses the
list internally) -- `scripts/docsync/logic.py`'s `_monotonic_dates` says
so explicitly ("current-batch entries are appended and then
reversed... position, not the heading date, is the authority on
recency"). Every current-batch entry so far, including the MusicBrainz
entry above and this task's own first draft, was inserted at the *top*
instead -- the untagged side-task convention, not this section's. Moved
here, to the true bottom, to follow the tool's actual model; the
pre-existing MusicBrainz/README entries above are left as written rather
than reordered, since that is a multi-entry change outside this task's
scope. (2) Fixing the position was not enough: `latest_test_count_authority`
still resolves to 1081, not this entry's 1085, because the DB-connect-timeout
side-task entry below the end marker is *also* dated 2026-09-14 and
explicitly claims 1081 -- on a same-date tie, source precedence ranks a
side-task entry above any current-batch entry regardless of which was
actually written later that day. This is **F-DOCSYNC-11** (open, P1,
filed 2026-09-12, same mechanism, different day), not a new finding.
Tried publishing 1085 into SESSION_CONTEXT/FINDINGS by hand to match
reality; `--check` rejected it (DOC005/DOC006/DOC008), because those
checks independently recompute the same stuck-at-1081 authority and
compare against it, rather than trusting a hand-written number -- the
prior session's F-DOCSYNC-12 fix (a genuinely unmanaged, never-recomputed
field) does not generalize to this one (a managed field recomputed every
run). Reverted to 1081 everywhere docsync validates it, per F-DOCSYNC-11's
own stated remedy ("publish a superseded number"); this entry's own
Validation line below is the accurate record of the true count until
F-DOCSYNC-11 is fixed.

Validation: `pytest -q` -- **1085 passed** (was 1081; +4 new). Frontend
gate -- 29/29, unaffected (backend-only change). `doc_state_sync.py
--check` passes clean (SESSION_CONTEXT/FINDINGS test-count fields read
1081, the tool's current authoritative-but-superseded figure, per
F-DOCSYNC-11 above; the root `BATCH22_DEFINITION.md` warning is expected
while the batch is active).

Audit validation: `pytest -q` -- **1088 passed** (was 1085; +3 focused
tests). The frontend gate was not rerun because the audit changed tests and
documentation only; Task 8's prior backend-only 29/29 result remains the
latest frontend evidence.

### 2026-09-15 - The correction worker (Batch 22 WP-3)

Scope: `docs/superpowers/plans/2026-09-13-batch22-enrichment-providers.md`
Task 9, which closes the loop Task 7 and Task 8 left open. Task 7 built the
MusicBrainz client and Task 8 applied findings that were already cached;
until now nothing wrote a new one, so `lookup_original_release`,
`_batch_lookup_original_release` and `_batch_persist_original_release` had no
production caller at all.

`scrobblescope/release_checks.py` (new): one process-wide daemon thread with
its own event loop (`ProactorEventLoop` on Windows, for the reason
`orchestrator.background_task` already documents) draining a FIFO
`queue.Queue` of job ids. One thread, not a pool: MusicBrainz allows one
request per second per IP and `utils.get_musicbrainz_limiter()` enforces that
process-wide, so extra threads would queue behind the same limiter while
multiplying DB connections and the ways a job's state can be raced. The
thread starts lazily, on the first job that can use it, so a process that
never runs one -- a test session, a CLI script -- never grows it.

Candidates per job, in the plan's order: the results in rank order (a
correction can move one out), then the release-scope exclusions whose
provider year is **later** than the target window's last year (a correction
can move one in). Nothing else can change, because an original release date
is never later than the provider's own. `_select_candidates`, `_window_end`
and `_release_year` are pure and tested directly. Each result gains a
`release_check` field -- `unchecked`, `confirmed`, `moved_out` or
`unavailable` -- and `progress.stats.release_check` holds `{status, checked,
total, moved_out, moved_in}` with `status` one of `running`, `done`,
`skipped`. A move-out marks the result in place and is counted; a move-in is
counted only, never inserted, so a results list somebody is reading is not
reordered underneath them.

Three design points the plan left open, decided here. **Cache hits cost no
request and still settle the result:** a cached row carrying an original date
is why the album passed the filter at all (Task 8 filtered on it), so the
result is `confirmed`; a cached null row is a recorded "checked, nothing
found", so it is `unavailable`. The cap therefore applies to what is left
after the cache short-circuit, because the cap exists to bound requests.
**Findings are persisted one row per check, not batched at the end:** the
worker spends about a second per candidate and a job lives two hours, so a
finding held in memory until the end is a request nobody gets back if the
process restarts. **No cache DB means no run:** the pass is marked `skipped`
without requesting anything, since a finding that cannot be persisted buys
one job's display and nothing for the next, at the shared budget's expense.
The worker also re-reads the job before every candidate and stops when it is
gone (`JOB_TTL_SECONDS`), and returns without raising in every failure mode:
a correction pass is an enhancement over results the user can already read.

`scrobblescope/repositories.py`: `set_job_release_check(job_id, state)`
replaces the whole stats payload rather than merging (the worker owns the key
and always knows the full state, so a merge could only preserve a stale
count) and copies on write; `update_job_result(job_id, album_key, fields)`
merges into the one result whose `normalize_name(artist, album)` matches
`album_key`, returning False when the job is gone, has no results list yet,
or holds no such album. Result dicts carry no pre-normalized key, which is
why the key is derived per entry rather than looked up.

`scrobblescope/orchestrator/__init__.py`: `_fetch_and_process` calls
`enqueue_release_check(job_id)` immediately after `set_job_results` on the
happy path only. The worker picks its candidates out of the stored results,
so an earlier hand-off would find nothing, and the error paths publish an
empty list, which has nothing to correct. `enqueue_release_check` is imported
at the top of the facade, and `release_checks` reaches
`_matches_release_criteria` through a function-local import: the two modules
would otherwise form an import cycle whose behaviour depends on which one is
imported first.

`scrobblescope/orchestrator/_results.py`: `provider_release_date` is now
attached to every release-scope unmatched entry, not only a corrected one. It
was half-wired in Task 8 (corrected entries only); the worker reads it back
off the unmatched entry to decide which exclusions a lookup could still move
in, and an *uncorrected* exclusion is exactly the case it exists to resolve,
so without this it could not build that candidate list at all.

Tests (31 new): `tests/services/test_release_checks.py` (22) covers the
candidate list and its order, the four exclusion rules that make an unmatched
album unmovable, the cap, the cache short-circuit including a null row,
`moved_out` marking a result without removing it from the list, the full
stats shape with a counted-not-inserted move-in, a job deleted mid-run
stopping the worker, `MUSICBRAINZ_ENABLED=False` and an unreachable DB both
marking `skipped` with no request, a "nothing found" row still being
persisted, connection close on a raising lookup, and the queue/thread
lifecycle. `tests/test_repositories.py` (+6) and
`tests/services/test_orchestrator_fetch_and_process.py` (+2, including the
error path *not* queueing) assert on the shared `JOBS` state rather than mock
calls. `tests/services/test_orchestrator_process_albums.py` (+1) covers the
uncorrected `provider_release_date`. The cap and the job-gone guard were each
disconnected in turn and the matching test failed, then passed again on
restoration.

Validation: `pytest -q` -- **1298 passed**. That figure is measured in a
worktree that also carries a concurrent, uncommitted docsync work package
from another session, so it is not comparable to the 1088 the entry above
records. Task 9's own contribution is +31 (22 + 6 + 2 + 1, per the file list
above). No frontend change, so the frontend gate is unaffected and its last
29/29 measurement stands.

Deviation, logged rather than swept: `pre-commit run --all-files` reports
`ruff` failures in `scripts/docsync/`, files this task does not touch and
does not stage. They belong to that concurrent docsync work package. The
staged-path hook run for this commit passes.

### 2026-09-20 - The release-check JSON endpoint (Batch 22 WP-4)

Scope: `docs/superpowers/plans/2026-09-13-batch22-enrichment-providers.md`
Task 10, the first task of WP-4. `GET /api/release_checks?job_id=` serves the
correction worker's findings to a results page that is already open. Task 11
consumes it; nothing renders these yet.

`scrobblescope/routes/api.py`: the endpoint returns `{status, checked, total,
moved_in, albums}`, where each album carries `key`, `state` and
`original_release_date`. It lists only results the worker has ruled on --
a result still `unchecked` is omitted, because the page has already rendered
every row and the only thing it needs back is what changed.

`scrobblescope/domain.py`: `format_album_key` returns the `artist|album` wire
form of a normalized key. The endpoint and Task 11's `data-album-key` must
name an album identically, so the join lives in one function rather than
being spelled the same way in two places. The separator is safe by
construction: `normalize_name` replaces every ASCII punctuation character
with a space, so neither half can contain a pipe.

**Deviation 1 -- the plan says the endpoint "reuses
`_get_validated_job_context` for ownership and mode checks". It does not.**
That helper renders `error.html` and returns HTML on both its failure paths,
which a polling client cannot read. The endpoint does the same two checks
(unknown job, wrong mode) and answers in JSON, as `/progress` and
`/api/unmatched` beside it already do. Ownership is unchanged from every
other job endpoint: the 128-bit job ID is the capability and there is no
session check. F-B22-3 holds that open question for the owner; this task
did not decide it one way or the other.

**Deviation 2 -- an error body carries `"status": "error"`.** The plan
specifies no error shape. The word is deliberately not one of the worker's
own four, so Task 11's poller stops on it by the same rule that stops it on
any status it does not recognise.

**`pending` is the fifth status, and the worker never writes it.**
`BATCH22_DEFINITION.md` WP-3 lists `pending` among the states to expose, but
the worker publishes `running`, `done` or `skipped` and publishes nothing at
all before it starts. `pending` is what the endpoint reports while
`progress.stats.release_check` is absent -- the gap between a job publishing
results and the worker first reporting on them. `STATUS_PENDING` is declared
in `scrobblescope/release_checks.py` with the other three so the vocabulary
stays in one module.

**Task 9 extended, under this task.** The worker wrote only
`{"release_check": outcome}`, so no corrected date ever reached the result
and the endpoint had nothing to serve: a moved-out row would have shown the
provider's reissue date while claiming to be a correction of it. Both
settling paths in `scrobblescope/release_checks.py` now write
`original_release_date` alongside the outcome -- the live one in
`_check_candidate`, the cached one in `_resolve_cached` -- and an
`unavailable` result records None rather than keeping a value the new
outcome contradicts. Seven lines, inside WP-4's own dependency, so it is an
in-WP deviation under AGENTS.md Proposal and Design Rules item 2 rather than
a new work package.

Tests (+9): seven in `tests/test_routes.py` covering the missing-ID 400, the
unknown-job and heatmap-job 404s in JSON rather than HTML, the `pending`
default, the filtering of unchecked results, the normalized key on an album
whose title is all punctuation and metadata words, and a result with no
`_normalized_key` being skipped instead of crashing the endpoint. Two in
`tests/services/test_release_checks.py` assert the date behind each of the
three outcomes and the same field written from a cache hit without spending
a request.

Validation: `pytest -q` -- **1506 passed** (was 1497; +9 new). The managed
STATUS block and the three hand-written count fields still read 1497, and
that is not drift: the untagged side-task entry below the end marker is also
dated 2026-09-20 and claims 1497, and on a same-date tie source precedence
ranks a side-task entry above any current-batch entry regardless of which
was written later. This is **F-DOCSYNC-11** (open, P1), not a new defect,
and its own stated remedy is to publish the superseded number and let the
entry carry the true one -- the Task 8 entry above did the same thing on the
same mechanism. DOC005/DOC006/DOC008 recompute that authority and reject a
hand-written 1506. `ruff check` and `ruff format` clean. The frontend gate was not rerun: nothing under
`templates/` or `static/` changed, so Task 11 is where it next earns its
run. `doc_state_sync.py --check` exit 0 (the root `BATCH22_DEFINITION.md`
warning is expected while the batch is active).

Forward guidance: Task 11 renders this. It needs `data-album-key` on each
results row carrying `format_album_key`'s output, a status line reading
"Checking original release years: N of M" from `checked`/`total`, per-row
markers that do not move a row, and the moved-in announcement from
`moved_in` with a reload action. Polling stops on `done`, on `skipped`, on
any unrecognised status, and on a failed request.

<!-- DOCSYNC:CURRENT-BATCH-END -->

### 2026-09-20 - Batch 22 work-package tags, and the docsync side task closed

Side task, no batch tag: bookkeeping repair found while orienting for WP-4,
plus the close-out of the docsync work the entry below tracks. No code
changed and no batch scope moved. The unrelated in-flight Batch 22 edits in
this worktree (the mutation runner, `graphify_refresh.py`, `AGENT_NOTES.md`,
`requirements-dev.txt`) were neither staged nor reverted.

**PR #234 merged** as `88f6e27` into `test`, so the docsync close-out side
task is finished and `feat/batch22-enrichment` is now fully contained in
`origin/test`. The gitignored `CLAUDE.md` section that tracked it asked to be
deleted on that merge, and was.

**The defect: six current-batch entries carried the wrong work-package tag.**
Every entry from Task 5 onward was headed `(Batch 22 WP-1)`, including the
Task 6 work that belongs to WP-2 and the Tasks 7-8 work that belongs to WP-3.
That tag is not decoration: `ENTRY_BATCH_RE` in `scripts/docsync/parser.py`
parses it, and the managed STATUS block in `.claude/SESSION_CONTEXT.md` is
derived from what it finds. The dashboard therefore read "WP-0, WP-1, WP-3"
and never named WP-2 at all -- a cold-resume reader would have seen the
Deezer fallback as work nobody had done. Retagged against the definition's
own task-to-WP map: Tasks 5-6 and both README passes to WP-2, Tasks 7-8 to
WP-3. Tasks 1-3 were already correct.

**Why this overrides the note that left the tags alone.** The Task 8 entry
above recorded a decision to keep its WP-1 heading as "its historical commit
record". That reasoning treats the tag as prose. It is an index key, and the
scope to fix it across six entries is exactly what that session said it
lacked. The superseding note now sits in that entry. The declines recorded in
F-DOCSYNC-3 are a different case and still stand: they cover content the tool
has already rotated into an archive, not live entries that have not rotated
yet.

**Also repaired:** `BATCH22_DEFINITION.md` still showed Task 9 unchecked while
its own header and Section 3 both said Tasks 7-9 were complete; the WP-3
heading now carries the struck-through DONE form its three siblings use.
F-B21-60 and F-B22-4 cited "Batch 22 WP-1 Task 6" in three places and now cite
WP-2.

**Known remaining instance, recorded rather than fixed:** F-DOCSYNC-12's
`Source:` line reads "Batch 22 WP-1, DB-connect-timeout side task". A side
task has no work package, so the right correction is not a different number,
and inventing one would trade a visible error for an invisible one.

**Two findings filed.** F-SWE-8 records the mutation-test runner's
disposition -- built, never adopted, four defects on first use, uncommitted,
its own future work package. It lived only in the gitignored `CLAUDE.md`, so
deleting that section would have erased it from the corpus entirely.
F-DOCSYNC-3 gains a second instance: Batch 22's Task 4 entry was headed
`(Batch 22 WP-1, Phase 2 begins)`, and the trailing clause inside the
parentheses made the heading unparseable as batch-tagged, so rotation sent it
to the monolith archive instead of a per-batch log. The defect is wider than
the `(Batch N close-out)` suffix the finding first described, and the tool
says nothing when it happens.

Validation: `pytest -q` -- **1497 passed**, unchanged (documentation only).
`doc_state_sync.py --check` exit 0, with the expected DOC023 grandfather
warning and the root `BATCH22_DEFINITION.md` warning. The frontend gate was
not rerun: nothing under `templates/` or `static/` changed, so the last
recorded result stands.

Forward guidance: Batch 22 WP-4 is next -- Task 10, the job-scoped
`GET /api/release_checks` endpoint, then Task 11's live disclosure. Two gaps
between the plan text and the code as built land on Task 10. The plan says
the endpoint reuses `_get_validated_job_context`, which renders `error.html`
and returns HTML; its JSON neighbours return JSON error bodies, so a
JSON-shaped validation path is needed. The plan's payload also carries
`original_release_date` per album, but Task 9's worker writes only
`{"release_check": ...}` through `update_job_result`, so the corrected date
never reaches the result and the worker has to write it.

### 2026-09-20 - Docsync review round, DOC023, and PR #234

Side task, no batch tag: close-out of
`docs/superpowers/plans/2026-09-15-docsync-closeout-archives.md`. Not Batch 22
scope. The unrelated in-flight Batch 22 edits in this worktree were neither
staged nor reverted. Ledger:
`.superpowers/sdd/2026-09-15-docsync-closeout-archives/progress.md`.

The whole-branch review had to be split: `/ultrareview` caps at 500 files and
8,000 lines against the working tree, and this work package was 52 files and
12,403 lines. The engine commit was reviewed alone from a temporary branch.
Every reported finding across ultrareview, Codacy, Graphify and qlty was
reproduced or refuted before being acted on -- roughly twenty reports produced
eight real defects. Refutations included a "high" that was an artifact of
where the review scope was cut and healed by the next commit, and three qlty
correctness items that were analyzer flow-model false positives.

Defects fixed, each with a regression test proven to fail without its fix:
archive pages were packed in reading order while every producer prepends, so
one rotated entry repacked the whole archive and returned cold pages to hot;
`--close-batch` restated the closure date from the clock; findings rotated to
the bottom of an archive whose prologue says newest first; the hook installer
resolved a relative `core.hooksPath` against cwd and wrote through a
pre-existing symlink onto its target; close-out `assert`s guarded a publish
and vanish under `python -O`; the preflight re-encoded a text-mode tar payload
and extracted unfiltered below Python 3.12.

DOC023 closes the finding-rot hole: all 83 findings lacked the canonical
`- [ ] **Status:**` record, so DOC013-DOC018 had never fired once. It blocks a
finding whose prose claims a terminal outcome without that record. The
boundary is an explicit id allowlist in `[findings] grandfathered`, not the
batch number the plan specified -- 32 of 83 ids are source-tagged and carry no
batch to compare, so a boundary would grandfather them by accident and let a
new finding escape by choosing a tag. 23 ids are grandfathered and reported as
one warning carrying a count derived from the file on every run.
`docs/agents/global-rules.md` was also added to Session Bootstrap, which it was
missing from despite being binding.

Validation: `pytest -q` -- **1497 passed**; `doc_state_sync.py --check` exit 0;
`frontend_gate.py` exit 0; `AGENTS.md` 473 lines against its 500 cap. Eighteen
commits on `feat/batch22-enrichment`, nothing unpushed, open as PR #234 into
`test`.

### 2026-09-19 - Docsync close-out plan Tasks 3 and 4, and a control-plane code review

Side task, no batch tag: continuation of the entries below on
`docs/superpowers/plans/2026-09-15-docsync-closeout-archives.md`, executed
via `superpowers:subagent-driven-development`. Not Batch 22 scope. Nothing
is committed; the whole plan remains working-tree-only by owner constraint,
and the unrelated in-flight Batch 22 edits in this worktree were neither
staged nor reverted.

Task 3 (CLI integration and multi-signal close-out) landed in six slices:
the two strict configuration tables, the definition-side close-out record,
the gate wiring, `--close-batch`, the archive maintenance modes, and DOC020.
Its review found one Important defect -- the `expected` map passed to
`transaction.publish` did not cover every path the plan had READ, so a
concurrent edit by another agent could publish a decision made about
different content. Fix round 1 made `_Corpus.read_paths()` the single source
of truth for that, so a document added to the corpus later inherits the
protection instead of needing a second hand-maintained list.

Task 4 was split into a code half and a documentation half. The code half
added `scripts/dev/docsync_preflight.py` and
`scripts/dev/install_docsync_hook.py`, moved the docsync hook to first
position in `.pre-commit-config.yaml`, and added an explicit CI preflight
step. Its review found that the control-plane refusal existed only in
`--staged` while the pre-commit entry runs `--worktree`, which is the path
that actually executes on every local commit; fix round 1 closed that.
The documentation half brought `AGENTS.md` from 728 to 498 lines by
compressing, relocating the DOC catalogue to
`docs/architecture/documentation-tooling.md` and the bootstrap edge cases to
`HANDOFF_PROMPT.md`, and relocating the `UI and Accessibility Rules` that an
in-flight Batch 22 edit had deleted into `docs/agents/ui-accessibility.md`.
That single deletion was the root cause of all three live gate errors, which
are now repaired.

Owner rulings taken during the session, both recorded in the plan ledger: the
commit preflight refuses any commit that modifies the docsync control plane,
and the one named escape is `SKIP=doc-state-sync-check git commit` rather
than `--no-verify`, so the absolute prohibition on `--no-verify` in
`AGENTS.md` anti-pattern 7 stands unchanged; and the architectural invariants
the owner supplied are now a binding document at
`docs/agents/global-rules.md`, carrying an explicit precedence order for when
two rules conflict.

An owner-requested code review of the control plane followed, and its
findings were fixed rather than filed. `--split-archive` had been writing
directly to disk with no lock, no journal and no staleness check, which
contradicted the atomicity guarantee every other writing mode honours; it now
publishes through the same transaction. The batch-definition regex that had
been constructed five times across three modules is now
`parser.root_definition_pattern`. The live-document path list, which the tool
had duplicated between `cli.py` and `integrity.py` without the declaration it
would demand of any other repository, now has one owner. On the application
side, `update_job_result` no longer normalizes every result inside the
process-global lock -- the key is attached once where results are built --
and `run_release_checks` was decomposed into three named units with its
existing tests passing unmodified as parity evidence.

Validation, run fresh in the controller session rather than taken from any
subagent's report: the two preflight and hook suites were 76 passing, the
release-check suite 23 passing unmodified before and after its refactor, and
`ruff check` plus `ruff format --check` were clean across the touched files.
`scripts/doc_state_sync.py --check` now exits 0, leaving only the expected
root `BATCH22_DEFINITION.md` warning. Validation: `pytest -q` -- **1470 passed**.

Deviations worth the next reader's attention. `AGENTS.md` landed at 498 lines
rather than the ~420 target: every remaining line is a distinct rule or
procedure, and further cuts would have removed prohibitions rather than
narrative. Two documents under `docs/agents/` were staged, against the
plan's own no-staging rule and at the owner's explicit instruction, because
DOC001 reads `git ls-files` and an untracked file can never satisfy a
reference to it.

Forward guidance, in the owner's stated order: build the DOC023 invariant
that stops resolved findings rotting in free prose, then run the final
whole-branch review, then land the work as a sequence of atomic commits
rather than one large one. The triage list for that review is every finding
marked deferred in
`.superpowers/sdd/2026-09-15-docsync-closeout-archives/progress.md`, which
remains the authoritative ledger for this plan.

### 2026-09-16 - Docsync close-out plan Task 2 closed out

Side task, no batch tag: continuation of the 2026-09-15 entry below on
`docs/superpowers/plans/2026-09-15-docsync-closeout-archives.md`, executed
via `superpowers:subagent-driven-development`. Not Batch 22 scope; nothing
here touches live `FINDINGS.md`, the archive files, or the docsync CLI.

Task 2's fix round 1 (resumed 2026-09-15 with a fresh implementer, since
the original handle was unavailable) addressed all 3 Important findings
recorded in `docs/history/reports/DOCSYNC_CLOSEOUT_TASK2_REVIEW_2026-09-15.md`:
a missing index no longer deletes existing pages (`_load` now rejects
orphans before returning an empty layout); a page's silently-discarded
prologue/missing header now raises `SyncError` instead of being dropped;
`page_path` now resolves beside `index_path` instead of always under the
store root. Each fix is covered by a regression test whose own docstring
names the finding it reproduces.

This session had no subagent-dispatch tool available, so the required
scoped re-review was performed by the controller directly instead of a
dispatched reviewer -- a disclosed deviation from
`superpowers:subagent-driven-development`, consistent with how Task 1's
own fix round 1 was handled for the same reason. The re-review checked
each fix against the review report's findings and the design spec's own
language (not just that tests pass), and swept for the same defect class
elsewhere in the module (`_diff`, the other `_reject_orphans` call site)
before concluding no sibling instance existed. Full re-review detail is in
`.superpowers/sdd/2026-09-15-docsync-closeout-archives/progress.md`.

Validation, run fresh: the archive suite alone was 43 passing, and the
full docsync suite (markdown/declarations/integrity/logic/parser/findings/
archives/transaction) was 355 passing; `ruff check` on all Task 1/2-owned
files was clean. Validation: `pytest -q` -- **1302 passed** (up from 1298;
the delta is this shared worktree's own concurrent, uncommitted growth in
`archives.py`/`test_docsync_archives.py`, not a regression -- see the
out-of-band fix entries above for the same observation applied to
`logic.py`).

Task 2 is complete: 3/3 Important findings addressed, 0 new
Critical/Important breakage. 7 Minor findings (recorded in the review
report) remain deferred, unchanged, to the final whole-branch review's
triage. Next step: Task 3 (CLI integration and multi-signal close-out).
