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

- **Batch 23 is active.** Definition: `BATCH23_DEFINITION.md`.
  Branch: `feat/batch23-wp0-hygiene`. The branch was cut from `test`; run the
  worktree guard with `--base-ref origin/test`.
- **Next action:** WP-0 is next.
  Part A and Part B are complete. Part C continues through the three
  follow-on plans in the order recorded under "After this plan" in
  `docs/superpowers/plans/2026-09-23-batch23-wp0-reconcile-and-clear.md`:
  control-plane, frontend, then test infrastructure and dependencies.
  The control-plane plan is written and reviewed:
  `docs/superpowers/plans/2026-09-25-batch23-wp0-control-plane.md`. Its eight
  tasks are all complete (Task 7 landed `8cf5fd4`..`c39da3c`). The frontend
  and test-infrastructure/dependencies plans are now written and reviewed:
  `docs/superpowers/plans/2026-09-26-batch23-wp0-frontend.md` and
  `docs/superpowers/plans/2026-09-26-batch23-wp0-test-infra-deps.md`. The
  frontend plan: Tasks 1 and 5 have landed. Test-infrastructure plan: Tasks 1
  and 2 have landed. Next
  action: execute these two plans, then the WP-0 close-out. The
  definition owns WP-0 scope and acceptance; `docs/agents/FINDINGS.md`
  owns open finding status.
- **WP-0 close-out:** Re-review `e7e076b` independently, review the whole
  branch, verify Part C's listed findings member by member, and run the
  final gates in the definition. Then write one tagged `(Batch 23 WP-0)`
  Section 4 entry, carrying an explicit `**Status:** WP-0 complete` line
  (DOC007 requires it before the package reads done). Earlier WP-0 commits
  remain untagged by the owner's 2026-09-23 ruling in the definition.
- **Batch 23 close-out obligation:** WP-7 includes the deferred Batch 21
  frontend and accessibility audit; the batch cannot close without it.

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

### 2026-09-26 - Stop cropping, overlaying and faking the artist spotlight photo

Side task, no batch tag: stop the artist spotlight photo from being cropped, overlaid,
animated or faked with an unconfirmed album cover, part of Batch 23 WP-0 Part C. Untagged
by owner ruling 2026-09-23 until the whole of WP-0 lands. `results.css`/`results.html`
now show the photo whole and square (4px corners at small sizes, 8px at large), with the
name, rank, playtime and summary beside or below it, never on top; the scrim overlay is
gone. `results-spotlight.js` swaps candidates instantly, with no fade. The server- and
client-side album-art fallback is gone: `scrobblescope/spotlight.py` no longer seeds
`image_url` from an album cover, and `results-spotlight.js` waits for every candidate's
photo to be confirmed by `/api/artist_spotlight` before revealing the card, dropping any
candidate whose photo is never confirmed; if none is confirmed, the card stays hidden.
`scripts/dev/_frontend_gate_spotlight_photo.py` adds two checks (`artist spotlight photo
has no crop overlay or animation`, `artist spotlight card hidden with no photo`) and
`scripts/dev/_frontend_gate_pipeline.py`'s `check_artist_spotlight_rotation` is
rewritten to capture its rotation baseline after the (now deferred) reveal instead of at
page load. `scripts/dev/results_behavior_tests.py` gains updated Chromium behaviour
tests for the same design: the card stays hidden until every hydration settles, a
candidate without a confirmed photo is dropped, and reduced motion keeps the surviving
confirmed artist still.

**Fix round 1, 2026-09-26:** two of the `results_behavior_tests.py` rewrites above
could not fail if the rotation's `c => c.image_url` filter were deleted --
`test_card_hidden_until_settle_then_drops_unconfirmed_candidates`'s 30s/7s-tick math
happened to land back on the same artist either way, and
`test_reduced_motion_keeps_first_confirmed_artist_after_failed_hydration`'s confirmed
candidate was already the one shown regardless of filtering. Both now assert the
filtered-list rank (`01 / 01`) and put the failing hydration on the first candidate so
the surviving, filtered name ("Second") only appears if the filter runs; R14 proof
in `task-5-report.md`. Also names the third existing test this task edited,
`test_spotlight_rotation_wraps_and_preserves_input` (`tests/test_routes.py`'s two
edits were already named in 699bec2's body), which the original commit omitted.

**Polish round, 2026-09-26:** a design review plus the controller's own read of
every screenshot found the compliant-but-plain spotlight card needed five more
fixes to match its sibling rail blocks: `.spotlight-image-box`
(`static/css/results.css`) gains the same `1px solid var(--ss-border-default)`
border every other thumbnail on the page already carries, so a dark photo
never melts into a dark card; `.spotlight-card-bleed`'s bespoke padding is
dropped in favour of the sibling cards' own `p-4
md:p-[calc(1.25rem*var(--results-scale))]` classes on `#artist-spotlight-card`
(`templates/results.html`), matching their rhythm exactly; "Artist Spotlight"
moves from a muted inline label into its own `<h3 class="results-rail-title">`
heading row at the top of the card, the same shared class and position the
"Sort leaderboard" and "Albums outside your filters" headings use; the photo
stays beside the text below 768px too, at a proportionate ~112px (was full
rail width), keeping 4px corners under 768px and 8px at/above; and the
artist's name drops `truncate` so a long name wraps instead of clipping. The
Spotify link's tap target grows from 16x16 to 44x44 via padding and a
matching negative margin, with no change to the glyph. The one-time card
reveal's layout shift stays parked (owner ruling: no fade/reserve, since the
card must stay hidden until a photo confirms and Spotify forbids animating
artwork), as does the interim Spotify link's icon/attribution work (F-B21-60
part 2). AFTER screenshots and measurements confirming all five fixes are in
`design-fe5/after-*.png` and `after-measurements.json` in the SDD workspace.

**Polish round 2, 2026-09-26:** a scoped re-review found the polish round's own
`truncate` removal let a long artist name wrap without bounding the details
column, so the card's height changed on every rotation tick between a short-
and a long-named candidate and jumped the rail below -- the same jank the
parked reveal item names, now recurring on every tick, not just the first
load. Fixed: `#spotlight-artist-name` gains Tailwind's `line-clamp-2` (two
lines, ellipsis, full name still in `title`; `renderText` in
`static/js/results-spotlight.js` already set both), and `.spotlight-details`
(`static/css/results.css`) gains a `min-height` sized to the clamped worst
case (2 name lines + a 2-line play-time/scrobble allowance + the rank line +
gaps, in rem units scaled by `--results-scale`, per breakpoint) so the card
is the same height for every candidate at a given width; the photo stays
112px/144px, top-aligned. Measured `#artist-spotlight-card` height across a
rotation between "A" and "The Bloomington Municipal Philharmonic Marching
Ensemble": identical at both 390x844 (185.59px) and 1280x800 (218.14px).
Folded in two deferred minors: `#spotlight-artist-name` is now a `<p>`, not
a second `<h3>` sharing a heading level with the card's own "Artist
Spotlight" title (grepped `tests/`/`scripts/` first -- nothing keys on its
tag). The suggested `p-3.5 -m-3.5` swap for the Spotify link's tap-target
padding was tried and reverted: this theme's spacing-scale reset (the same
one `templates/unmatched.html`'s own comment documents for `w-24`/`w-28`)
means `--spacing-3.5` is never emitted, so those classes compiled to
nothing and silently dropped the 44x44 tap target back to 16x16; kept the
working `p-[14px] -m-[14px]` arbitrary values instead. Evidence, including
the height measurements and `after-card-clamped-{short,long}-mobile.png`,
is in `task-5-report.md`.

**Casing fix, 2026-09-26:** the card's `<h3 class="results-rail-title">` heading read
"Artist Spotlight", but its sibling rail headings ("Sort leaderboard", "Albums outside
your filters") are sentence case in source -- `.results-rail-title` uppercases them
visually, but screen readers read the source text. Changed to "Artist spotlight" in
`templates/results.html`; grepped `tests/`/`scripts/` first, nothing keys on the old text.

Validation: `pytest -q` -- **1958 passed**.

### 2026-09-26 - Doc-transcribed provider fixtures plus shape tests

Side task, no batch tag: added Spotify and Last.fm fixtures transcribed from each
provider's published reference plus shape tests, part of Batch 23 WP-0 Part C. Untagged
by owner ruling 2026-09-23 until the whole of WP-0 lands. `tests/fixtures/` holds Spotify
and Last.fm response shapes transcribed from each provider's published reference;
`tests/test_provider_fixtures.py` pins the app's own field reads against them and checks
one existing mock for drift -- a weaker guarantee than a live contract test, recorded as
such (Q7 answer a).

**Fix round 1, 2026-09-26:** the Last.fm shape test only re-asserted the fixture's own
field literals, so no app code reading a field the docs don't promise could ever fail it.
Replaced it with two tests that run the fixture through the app's real consumers:
`scrobblescope.heatmap._aggregate_daily_counts`, which keys off `date.uts`, and
`scrobblescope.orchestrator.fetch_top_albums_async` (with only
`fetch_all_recent_tracks_async` patched), which reads `artist.#text`, `album.#text` and
`name`. Verified in a scratch copy: renaming `uts` to `ts` fails both new tests; renaming
`album.#text` fails the orchestrator one.

Validation: `pytest -q` -- **1959 passed**.

### 2026-09-26 - A real thread runs the album pipeline end to end

Side task, no batch tag: a real thread runs the album pipeline end to end, part of
Batch 23 WP-0 Part C. Untagged by owner ruling 2026-09-23 until the whole of WP-0
lands. `tests/test_pipeline_integration.py` drives the real `/results_loading ->
/progress -> /results_complete` route sequence through the Flask test client, joins
the real `worker.start_job_thread` background thread before trusting anything past
its terminal `/progress` state (an owner-requested review found the prior version
raced ahead of the MusicBrainz hand-off and never joined the thread, so a leftover
job slot or a live MusicBrainz call could survive the test), and asserts the
MusicBrainz hand-off ran under mock, the job's concurrency slot is fully released,
and `/results_complete` renders the album that survived the Spotify phase.

Validation: `pytest -q` -- **1943 passed**.

### 2026-09-26 - A Chromium harness for heatmap.js's pure-function seam

Side task, no batch tag: added a Chromium harness for heatmap.js's pure-function seam, part of
Batch 23 WP-0 Part C. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

rocketColor, countToNorm and the export header layout are exercised by a Chromium harness
(tests/frontend/test_heatmap_pure_functions.py) through window.__scrobbleHeatmapTestHooks,
exposed at the module's top level only when window.__scrobbleHeatmapTestMode is set before the
script runs -- the guarded seam F-B21-18 asked for, so no production page load exposes the hook;
computeStreak is WP-6's per Q14 answer a; the harness carries a browser pytest marker so CI's
pre-browser coverage step deselects it and the post-browser frontend-gate step runs it instead.

Fix round 1 (code review): added interior countToNorm cases so a linear count/maxCount cannot
pass; a negative exportHeaderModel case (no text-transform leaves the text as written) with the
model tests cleaning up their own DOM inserts; a test that a second page never setting the flag
never sees the hooks; reused _launch_browser for the setup-guidance path; and corrected the
seam's stale "these four functions are pure" comment (exportHeaderModel reads the DOM). Filed the
harness scope's two residual F-B21-18 items (the 53x7 export contract deviation, the duplicated
username validators) as F-B23-9, joining WP-0 Part C's set by controller ruling 2026-09-26
(BATCH23_DEFINITION.md Part C); F-B21-18's archived record now points to it.

Validation: `pytest -q` -- **1963 passed**.
