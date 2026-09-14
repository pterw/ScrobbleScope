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
  `docs/superpowers/plans/2026-09-13-batch22-enrichment-providers.md`. It opens
  only when this section declares it active and names its branch: the
  worktree guard fails every commit on a branch this section does not name
  (WT003, an error). The proposed name is `feat/batch22-enrichment`, cut
  from `test`.
- **WP-0 is complete.** `routes.py` (985 lines) is now a `routes/` package:
  a facade `__init__.py` (the shared `Blueprint`, job-context helpers, error
  handlers) plus `pages.py`, `album_flow.py`, `heatmap_flow.py`, `api.py`,
  each decorating the same `bp` so every endpoint name and `url_for()` call
  is unchanged. `orchestrator.py` (1035 lines) is now an `orchestrator/`
  package: a facade `__init__.py` (the pipeline glue -- `process_albums`,
  `_fetch_and_process`, `background_task`, `fetch_top_albums_async`) plus
  `_search.py`, `_details.py`, `_cache.py`, `_results.py` for the four named
  phases. Every submodule that a test suite patch targets at
  `scrobblescope.orchestrator.<name>` or `scrobblescope.routes.<name>` reads
  that dependency through a live reference to its facade module rather than
  its own import, so the existing patches still land after the code moves;
  see the module docstrings on both `__init__.py` files for the mechanism.
  Acceptance held: `pytest -q` -- **1034 passed**, unmodified, and the
  two-engine frontend gate -- 28 checks passed in 50 runs, matching the
  batch-open baseline exactly. Resulting sizes: `orchestrator/__init__.py`
  699 lines, `routes/album_flow.py` (the largest new file) 454 lines --
  smaller than the originals but still above the 361-line largest-peer mark
  AGENTS.md's size-limits rule points at; the split stopped at what the
  behaviour-neutral acceptance criterion could verify rather than forcing a
  deeper cut for its own sake. **Deviation, logged rather than swept:**
  `docs/architecture/*.md`, `README.md` and `AGENT_NOTES.md` still cite a few
  `orchestrator.py`/`routes.py` paths from before this split (two
  load-bearing ones in `AGENT_NOTES.md` are fixed; the rest are deferred).
  WP-5 already owns a README and `docs/architecture/runtime-system.md` pass
  for the new providers, so the remaining citations are swept there rather
  than twice.
- **WP-1 Phase 1 and Phase 2 (Tasks 4-6) complete.** Task 6 (show the
  album's own provider in the UI) landed 2026-09-13: results/unmatched rows
  link to `album_url` and carry a text provider-attribution badge, per the
  2026-09-13 Section 4 entry below. **Next action:** Task 7, the
  MusicBrainz client (Phase 3, original release years).
  `docs/superpowers/plans/2026-09-13-batch22-enrichment-providers.md`,
  executed task by task via `superpowers:executing-plans`; per-task progress
  is also tracked in that plan file's own Progress section.
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
- **Next action:** the WP-7 refinement the owner asked for is implemented and
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

### 2026-09-13 - Show the album's own provider in the UI (Batch 22 WP-1)

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

### 2026-09-13 - Deezer fallback wired into the orchestrator (Batch 22 WP-1)

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

<!-- DOCSYNC:CURRENT-BATCH-END -->

### 2026-09-13 - Deezer client (Batch 22 WP-1, Phase 2 begins)

Scope: `docs/superpowers/plans/2026-09-13-batch22-enrichment-providers.md`
Phase 2 Task 4. No behaviour change -- `scrobblescope/deezer.py` is new and
unused by any caller; Task 5 wires it in as the Spotify-miss fallback.

Plan vs implementation: matched. `search_deezer_album(session, artist,
album)` queries the plain `f"{artist} {album}"` (the filtered
`artist:"..." album:"..."` form favors tribute/cover results per the
plan's probe) and accepts a candidate only when
`normalize_name(candidate_artist, candidate_title)` equals the key built
from the caller's own `artist`/`album` -- never "the first result" as a
guess. `fetch_deezer_album(session, album_id)` calls `/album/{id}` for
metadata and `/album/{id}/tracks?limit=500` for every track's duration,
since `/album/{id}` alone caps at 25 tracks regardless of `nb_tracks`
(pinned with a 30-track fixture). Both share `_fetch_deezer_json`, which
treats Deezer's HTTP-200-with-body errors correctly: code 800 ("no data")
is a terminal miss: `None`; code 4 (quota) retries after a 1s wait via
`retry_with_semaphore`'s existing retry-after path, the same mechanism
Spotify's 429 handling already uses.

`scrobblescope/utils.py` adds `get_deezer_limiter()` (10 req/s, the
existing `_GlobalThrottle` + per-loop `AsyncLimiter` pattern, mirroring
`get_spotify_limiter`); `scrobblescope/config.py` adds
`DEEZER_REQUESTS_PER_SECOND` (default 10 -- Deezer's stated 50 req/5s),
`DEEZER_SEARCH_RETRIES`, `DEEZER_DETAIL_RETRIES` (default 3, matching
Spotify's retry defaults).

Validation: `pytest -q` from the worktree cwd -- **1061 passed** (1054 + 7
new in `tests/services/test_deezer_service.py`: candidate-matching,
no-match, the two HTTP-200-error-code cases, the 25-vs-30-track pagination
case, and two adversarial "the second request never succeeds" cases for
`fetch_deezer_album`, added beyond the plan's own four because a helper
this new needs at least one failure-path test per AGENTS.md's Test
Quality Rules. Task 5 (wire the fallback into the orchestrator) is next.

### 2026-09-13 - PR #232 merged to `test`; branch reset, SHAs remapped

Owner rebase-merged PR #232 into `test` (mergeCommit `812cdde`). GitHub
rebased rather than merge-committed, so every commit on the PR got a new
SHA: `e8de45c`->`d29cc5e`, `85d458f`->`a124b52`, `c5c52fb`->`735c05d`,
`594c705`->`87f3822`, `05a0ff5`->`812cdde`. **Every one of those five old
hashes is quoted earlier in this file, in FINDINGS.md, and in the Claude
project memory for this repo; none of them resolve on this branch
anymore.** Content is unchanged -- `git show <new-sha>` reproduces the
same diff as the corresponding old one -- only the identifier changed.

`feat/batch22-enrichment` (worktree and `origin`) was hard-reset to
`origin/test`'s tip and force-pushed to drop the now-orphaned pre-rebase
commits, per owner direction (reset in place, not a fresh branch --
`AskUserQuestion`, 2026-09-13). PLAYBOOK Section 3's branch name is
unchanged; WP-1 continues on `feat/batch22-enrichment`. Verified after
reset: `pytest -q` -- **1036 passed**; worktree-alignment guard passed (0
behind, 21 ahead of `origin/main`).

A second Graphify review landed on `05a0ff5` (2026-09-14 01:29 UTC, before
the merge) claiming 5 endpoints were "removed" from `scrobblescope/routes.py`
-- a stale-baseline false positive (its own index was "15 commit(s) behind
this PR's base"): the file no longer exists post-WP-0, and all five
endpoints are present, unmoved in content, in `routes/api.py` and
`routes/heatmap_flow.py`. No action taken; not filed as a finding since
it is a bot-indexing artifact, not a repo issue.

### 2026-09-13 - PR #232 bot review triage (Codacy + Graphify)

Triaged both bot reviews on PR #232 (WP-0 + F-B22-1 + AGENTS.md cleanup)
per `/pr-bot-triage`. Codacy (2026-09-13 21:49 UTC, 3 alerts) and Graphify
(2026-09-14 01:08 UTC, 5 inline coupling-delta comments + 5 "worth a look"
escalate findings from the check run) both reviewed the same branch tip.

Acted: `scrobblescope/lastfm.py:68`'s unreachable `return` after
`resp.raise_for_status()` deleted (Codacy, confirmed real -- the call
always raises for any status reaching that branch, so the line never ran).

Deferred, filed as findings: the three `assert job_context is not None`
sites in `album_flow.py` moved verbatim from pre-split `routes.py`
(F-B22-2 -- real hardening gap, `python -O` strips asserts, but out of
WP-0's behaviour-neutral scope); the job-ID-as-bearer-token design across
`/progress`, `/api/unmatched`, and `/heatmap_data` (F-B22-3 -- owner
judgment call, not a demonstrated bug).

Declined, false positives (verified against source, not fixed): Codacy's
XSS claim on `_get_filter_description`'s f-string returns (no `|safe` in
`results.html`/`unmatched.html`; Jinja2 autoescapes regardless of how the
Python string was built). Graphify's two "job slot leak on failed thread
startup" escalate findings (`worker.py`'s `start_job_thread` already calls
`release_job_slot()` in its own `except` before re-raising -- confirmed by
reading `worker.py:31-42`). Graphify's "`check_user_exists` now raises
instead of returning a fallback" escalate finding (that is the PR's own
intentional F-B22-1 fix, not a new regression). Graphify's five inline
"health regression" coupling-delta comments (expected structural churn
from WP-0's module split; the tool's own gate marked the run PASS with no
blocking health regressions).

Verification: `pytest -q` -- **1036 passed**; `doc_state_sync.py --check` and
`pre-commit run` both pass.

### 2026-09-13 - Fixed a broken batch-reference edit; graphify agent sections

Two unrelated uncommitted changes found sitting in the worktree during a
pre-clear sweep, neither written by this session:

1. **`docs/agents/domain.md` had a broken edit**, from an unknown earlier
   process: `BATCH21_DEFINITION.md` had been changed to `BATCH2_DEFINITION.md`
   -- a dropped digit, not a real batch. Fixed to `BATCHN_DEFINITION.md`
   (the file named in PLAYBOOK Section 3), matching the same generalization
   already applied to `docs/architecture/documentation-tooling.md` and
   `docs/ARCHITECTURE.md` earlier today, so it cannot go stale the same way
   again.
2. **Graphify's own tooling had added a `## graphify` section to `AGENTS.md`
   and `.github/copilot-instructions.md`**, matching one already present
   (and already noted, this session) in the gitignored `CLAUDE.md`. Kept:
   the content is operational and non-duplicative with anything already in
   `AGENTS.md`, and reaching every agent's own instructions file (Claude,
   Copilot, and via `AGENTS.md`, everyone else) is exactly the "reach every
   agent" pattern this session's earlier `AGENTS.md` edits argued for. Not
   independently trimmed -- reads as graphify's own multi-agent install
   pattern, not this session's prose.

Validation: `pytest -q` -- **1036 passed** (unchanged).
`python scripts/doc_state_sync.py --check` passes.
