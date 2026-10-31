<!-- DOCSYNC:ARCHIVE-PAGE v1 -->
# PLAYBOOK_EXECUTION_LOG_ARCHIVE -- page 0028

### 2026-09-28 - Heatmap arrow keys follow the layout; document listeners attach once

Side task, no batch tag: the 2026-09-28 /code-review's findings 2 and 4 on the heatmap grid,
part of Batch 23 WP-0 Part C. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

Arrow keys now move spatially: desktop (one column per week) Left/Right -/+7 days, Up/Down -/+1;
mobile strip (row-major) Left/Right -/+1, Up/Down -/+columns; at an edge focus stays put
(`arrowKeyTarget`, on the guarded test seam). Finding 4: only the tooltip's anonymous
capture-phase `scroll` listener on `document` piled up across renders (each held its render's
cellData and detached SVG); the `touchend` listener used one stable function reference, so the
DOM already de-duplicated it and never piled up. Both are now attached once per page and read
the current render's cells, closing the remaining `scroll` accumulation. Harness: step cases
per layout, arrow and edge. Gate: the keyboard check probes all four arrows against the
rendered geometry; new check `heatmap document listeners attach once`. Mutation/live-probe
evidence in the task report.

Validation: `pytest -q` -- **2032 passed**.

### 2026-09-28 - Classify upstream failures before blaming the app

Side task, no batch tag: heatmap and album backstops now share one
exception classifier, and the release-window log line names every input
it received, part of Batch 23 WP-0 Part C. Untagged by owner ruling
2026-09-23 until the whole of WP-0 lands.

`scrobblescope/heatmap.py`'s `_report_heatmap_failure` publishes
`errors.classify_exception_to_error_code`'s answer when the escaped
exception is a known upstream failure (a Last.fm 404 -> `user_not_found`),
else `internal_error`, matching the album pipeline (F-SWE-5). The
classifier moved from `orchestrator/__init__.py` to `errors.py`, its one
owner now; `orchestrator`'s call site and tests import it from there. A
malformed Last.fm first page (valid JSON, no `@attr.totalPages`) now
returns the existing `lastfm_unavailable` metadata instead of raising
`KeyError`. `domain._matches_release_criteria`'s `release_window`
`ValueError` handler now logs the scope and all three inputs it received
instead of always naming `decade`.

Validation: `pytest -q` -- **2004 passed**.

### 2026-09-28 - Stop declaring skills-lock.json an untracked essential

Side task, no batch tag: Stop declaring skills-lock.json an untracked
essential, part of Batch 23 WP-0 Part C. Untagged by owner ruling
2026-09-23 until the whole of WP-0 lands.

Owner ruling 2026-09-28: skills-lock.json "is a file that was briefly
here, but vanished... if it is needed search and let go for what you
think is best." Controller decision: not needed -- it is the `npx skills`
CLI's own lockfile; nothing in this repository, its hooks, CI or agent
workflow reads it. `config/docsync.toml`'s `[untracked_essentials]` now
declares `paths = []` (comment explains why); the mechanism, its schema
and `scripts/dev/_worktree_guard_essentials.py` are unchanged, so WT015
still fires for any future essential that is declared. `.gitignore` keeps
the `skills-lock.json` line since the CLI still writes it. Swept the
now-false claim from the guard module's docstring and
`.superpowers/cloud-kit/constraints.md`'s expected-pre-commit-noise line.

Validation: `pytest -q` -- **2001 passed**.

### 2026-09-27 - Record the follow-on plans' final code review

Side task, no batch tag: record the outcome of the final code review of the
three follow-on plans (control-plane, frontend, test infrastructure and
dependencies), part of Batch 23 WP-0 Part C. Untagged by owner ruling
2026-09-23 until the whole of WP-0 lands. This does not close WP-0.

The review covered `f8fb8e9^..18d95ae` and raised ten findings. The
controller checked each against the code: eight were fixed in one fix wave
(`6d217f4` docsync, `604d815` artist spotlight, `351c5fe` heatmap), one was
already filed (F-DOCSYNC-23, the unchecked module count), and one was already
ruled (WT015 fires in every checkout because `skills-lock.json` is absent;
where that file lives is the owner's decision). The part of the spotlight
finding asking for a text-only card when Spotify is down stays as the
F-B21-60 ruling requires: no card. A scoped re-review approved the wave.

Deviations: `6d217f4` and `604d815` carry subjects without the Conventional
Commits type and scope; they were not rewritten, because history is rewritten
only on the owner's instruction. Deferred minor: the heatmap tooltip follows
the focused cell on scroll even when the mouse hovers a different one.

Validation: `pytest -q` -- **1999 passed**.

### 2026-09-27 - Heatmap keyboard and screen-reader access follow-up

Side task, no batch tag: give the heatmap grid a roving tabindex (one Tab
stop, arrow keys move it) in place of every cell carrying tabindex="0",
change the SVG's role from "img" to "group" so a cell's own role="img" +
aria-label survives in the accessibility tree, and stop a focus-triggered
scroll from hiding the tooltip it just showed, part of Batch 23 WP-0 Part
C. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

Validation: `pytest -q` -- **1999 passed**.

### 2026-09-27 - Artist spotlight photo shown whole, swaps stay in sync, hydrate requests time out

Side task, no batch tag: fixed the artist spotlight card's non-square photo
crop, the stale-photo-under-a-new-name swap on rotation, and the missing
hydrate-request timeout (now covering the image preload too, not just the
fetch), part of Batch 23 WP-0 Part C. Untagged by owner ruling 2026-09-23
until the whole of WP-0 lands.

Validation: `pytest -q` -- **1999 passed**.

### 2026-09-27 - Docsync CLI and declarations edge cases

Side task, no batch tag: fix docsync's `--test-count 0` acceptance, the
pin-rewrite regexes' heading-comment and blank-line misses, and add a
`C:foo` CR5 case plus a control-character rejection for
`[untracked_essentials]` paths, part of Batch 23 WP-0 Part C. Untagged by
owner ruling 2026-09-23 until the whole of WP-0 lands.

Validation: `pytest -q` -- **1999 passed**.

### 2026-09-27 - Bring prose and diagrams in line with the three follow-on plans

Side task, no batch tag: a documentation-only sweep so README.md,
DEVELOPMENT.md, every `docs/architecture/*.md` Mermaid diagram,
`.claude/SESSION_CONTEXT.md` and `docs/agents/PLAYBOOK.md` match the code the
control-plane, frontend and test-infrastructure plans changed
(`f8fb8e9^..HEAD`), part of Batch 23 WP-0 Part C. Untagged by owner ruling
2026-09-23 until the whole of WP-0 lands.

- `docs/architecture/documentation-tooling.md`: added the two new frontend
  gate slices (`_frontend_gate_heatmap_access`, `_frontend_gate_spotlight_photo`)
  to the Mermaid diagram and its facade-sibling count (twelve, ten own a
  concern); added a `_worktree_guard_essentials` node/edges (WT015) and the
  seventh guard-module count; added `config/docsync.toml`'s `[test_count]`
  pin and `[untracked_essentials]` table to the TOML node; documented WT015
  and the `docsync.logic`/`docsync.integrity` deferred-import removal (CO1).
- `docs/architecture/development-cycle.md`: the "Run full validation gates"
  node now names `--test-count N`, the `tests/frontend` browser marker and
  `results_behavior_tests.py`; added a CI paragraph naming the docsync
  preflight, `pytest -m "not browser"`, the browser-marked suite and
  `frontend_gate.py`, and `pip-audit` against both requirements files.
- `README.md`: "Running Tests" now names the `browser` marker and the local
  Chromium requirement.
- `DEVELOPMENT.md`: the frontend-gate facade's sibling count and the
  worktree guard's module/WT-code counts (seven modules, `WT000`-`WT015`);
  named this session's four new gate checks; added the `tests/frontend`
  marker, its CI split and the wider `pip-audit` scope to the Frontend
  Browser Gate section.
- `.claude/SESSION_CONTEXT.md`: added the two new gate slices and
  `_worktree_guard_essentials.py` to Section 3's structure listing and their
  edges to Section 4's dependency graph; noted `tests/frontend/` and
  `tests/fixtures/` in Section 6; bumped the "Last updated" date.
- `docs/agents/PLAYBOOK.md` Section 3: the frontend and test-infrastructure
  plans are both fully executed; the next action is the close-out code
  review, then the WP-0 close-out. `**Next action:** WP-0 is next.` is
  unchanged.
- `docs/ARCHITECTURE.md`: bumped the "last verified" date after checking
  every diagram against the current tree.
- Checked and found already accurate, no change made: `AGENTS.md`,
  `docs/architecture/runtime-system.md` (spotlight fallback prose already
  fixed by Task 5), `docs/architecture/{heatmap,top-albums}-sequence.md`,
  `docs/agents/ui-accessibility.md`, `docs/agents/AGENT_NOTES.md`, the three
  plan files' checkboxes (already all ticked), `docs/design/*.md` (dated
  audit/reconciliation documents, out of the live-prescriptive-doc scope).

Validation: `pytest -q` -- **1993 passed**.

### 2026-09-27 - File the carried close-out findings and amend Part C

Side task, no batch tag: filed two carried findings, amended
`BATCH23_DEFINITION.md`, and fixed three rule/record docs, part of Batch 23
WP-0 Part C. Untagged by owner ruling 2026-09-23 until the whole of WP-0
lands.

- Filed `F-DOCSYNC-23` (the tracked test-module count is hand-maintained and
  unchecked) and `F-B23-10` (three frontend-gate failures were gate defects,
  each green on an immediate rerun), both P2, in `docs/agents/FINDINGS.md`.
  Re-measured the module count now: `git ls-tree -r --name-only HEAD tests |
  grep -c '/test_[^/]*\.py$'` gives 78, matching both `.claude/
  SESSION_CONTEXT.md` and the `FINDINGS.md` header -- both sites are right
  today, so no correction was needed.
- `BATCH23_DEFINITION.md`: recorded the three approved WP-0 follow-on plan
  paths as executed; recorded F-B21-60's Spotify-icon/attribution part as
  remaining, unscheduled work (it stays in Part C's set and open); added
  `scripts/dev/results_behavior_tests.py` to Part C's acceptance gate list.
- `AGENTS.md` Batch Close-Out Procedure step 5 now says to run `pytest -q`
  before `--fix --test-count N`, since no earlier close-out step measured
  the count.
- `.superpowers/cloud-kit/constraints.md` (tracked, generic): brought its R5
  commit procedure, R6 expected warnings and R7 docsync-control-plane
  exemption in line with the control-plane workspace's later rulings.
- `docs/history/findings/FINDINGS_ARCHIVE.md` F-B21-3: reworded the
  pip-audit recount from "found 0 vulnerabilities in 0 packages" to
  "reported no known vulnerabilities".

Validation: `pytest -q` -- **1993 passed**.

### 2026-09-27 - Close out the test-infrastructure plan's carried test minors

Side task, no batch tag: closed the carried test minors from
`docs/superpowers/plans/2026-09-26-batch23-wp0-test-infra-deps.md` Task 1,
part of Batch 23 WP-0 Part C. Untagged by owner ruling 2026-09-23 until the
whole of WP-0 lands.

- `tests/test_pipeline_integration.py`: the /progress poll loop and the
  background-thread join each had their own 10s deadline, so a genuine
  hang could take up to 20s to fail. `_JOB_TIMEOUT_SECONDS` (now 30, still
  bounded) is one `time.monotonic()` deadline computed once; `join()`
  spends only what is left of it. `created_threads[0]` assumed the first
  captured `background_task` thread was this job's; the test now asserts
  `len(created_threads) == 1`, naming the count, before using it.
- `tests/test_provider_fixtures.py`'s
  `test_lastfm_fixture_flows_through_fetch_top_albums` docstring claimed a
  fixture missing `name` would fail the test, but
  `scrobblescope/orchestrator/__init__.py` reads `t.get("name", "...")`, so
  a missing name still yields an eligible album. The docstring now names
  only the fields the test actually catches.

Validation: `pytest -q` -- **1993 passed**.

### 2026-09-27 - Close out the control-plane plan's carried code items

Side task, no batch tag: closed the carried docsync code items from
`docs/superpowers/plans/2026-09-25-batch23-wp0-control-plane.md` (all eight
tasks landed), part of Batch 23 WP-0 Part C. Untagged by owner ruling
2026-09-23 until the whole of WP-0 lands.

- m1: `docsync.logic` and `docsync.integrity` each carried a deferred,
  module-bottom import of one name from the other, guarded by a "would
  deadlock" comment -- a same-module import cycle broken only by import
  order. `SESSION_CURRENT_COUNT_RES` moved to `docsync.parser`, the leaf
  module both already import at top level (still importable from
  `docsync.integrity`, which re-exports it); `integrity.py`'s three names
  from `logic.py` moved to its top imports now that nothing in `logic.py`
  needs anything from `integrity.py`. Both deadlock comments are gone.
- m4: `WP_COMPLETE_STATUS_RE` (`scripts/docsync/parser.py`) had no end
  anchor, so `**Status:** WP-4 complete (pending review)` counted as WP-4
  done. Anchored: the line may close with an optional `.` and trailing
  whitespace only.
- CR5: `[untracked_essentials]` paths were not contained to the repository
  root. `declarations._validate_untracked_essentials` now rejects an
  absolute path (POSIX or Windows drive form) or a `..` segment; the
  worktree guard's directory diagnostic renders the declared path with
  `repr()` rather than echoing it raw.
- CR10: a declared `[untracked_essentials]` path that exists as a directory
  read as "missing". `essentials_diagnostics` now distinguishes missing from
  "exists but is not a file" (a new WT015 WARNING).
- CR9: `_validate_test_count`, `_validate_untracked_essentials` and
  `_validate_closeout` each hand-wrote the same is-a-table-plus-unknown-key
  check. Extracted one `_validated_table` helper (Rule of Three); every
  existing error message stays byte-identical.
- CR4 (ruled, no code change): WT015 fires in every checkout because
  `skills-lock.json` is truly absent; the warning is true, and where the
  file lives is the owner's decision.
- CR6 (ruled, no code change): the import-time `sys.path` insert in
  `_worktree_guard_essentials.py` is the control-plane plan's
  pre-accepted deviation, the same shape as `scripts/doc_state_sync.py`.
- m6 (ruled, no code change): the hand-maintained module count is filed as
  a finding in the close-out docs commit, not built here.

Validation: `pytest -q` -- **1993 passed**.

### 2026-09-27 - Audit the dev requirements too (CI input gap)

Side task, no batch tag: closed the scope item "add requirements-dev.txt
to the CI audit's inputs", part of Batch 23 WP-0 Part C. Untagged by
owner ruling 2026-09-23 until the whole of WP-0 lands.

The "Security audit (pip-audit)" step in `.github/workflows/test.yml`
passed `inputs: requirements.txt` only, so a vulnerable pin anywhere in
`requirements-dev.txt` was never flagged. `pypa/gh-action-pip-audit@v1.1.0`
documents `inputs:` as a whitespace-separated list (its own README example:
`inputs: requirements.txt dev-requirements.txt`), so the step now reads
`inputs: requirements.txt requirements-dev.txt`.

Live probe in a scratch copy: pinning `virtualenv==20.26.5` in a scratch
`requirements-dev.txt` made `pip-audit -r requirements.txt -r <scratch>`
report PYSEC-2024-187 (exit 1); reverting to the real, pinned
`virtualenv==20.36.1` made the advisory disappear (exit 0, "No known
vulnerabilities found"), confirming the dev file is now audited.

Validation: `pytest -q` -- **1978 passed**.

### 2026-09-27 - Let the inline marks colour themselves

Side task, no batch tag: fixed F-B21-23, part of Batch 23 WP-0 Part C.
Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

Both inline mark SVGs now carry fill="currentColor" and stroke: var(--bars-color)
in their own <style> block, so shell.css's five-rule per-wrapper CSS list
(F-B21-21's fix) collapses to one `.ss-mark { color: var(--shell-ink); }`
declaration. `check_inline_marks_need_no_wrapper_list` in
scripts/dev/_frontend_gate_assets.py reads both SVG templates off disk and
fails on a missing fill/stroke rule or any literal hex colour.
`tests/test_template_shell.py::test_migrated_wordmarks_use_theme_ink_for_letterforms`
was rewritten (controller ruling, task-4-context.md, widening this task's
Touches) to assert the new mechanism instead of the deleted per-wrapper
selectors, keeping its name and docstring intent.

Validation: `pytest -q` -- **1978 passed**.

### 2026-09-27 - Heatmap grid cells are keyboard-focusable and labelled

Side task, no batch tag: heatmap grid cells carry tabindex, role=img and an
aria-label built by the same cellAccessibleLabel helper the mouse tooltip
uses, part of Batch 23 WP-0 Part C. Untagged by owner ruling 2026-09-23 until
the whole of WP-0 lands.

Extracted `cellAccessibleLabel` in `static/js/heatmap.js` so the tooltip and
each cell's `aria-label` share one source of truth, made every `.heatmap-cell`
focusable with a visible `:focus-visible` ring, and added
`check_heatmap_cells_are_keyboard_accessible` (its own frontend-gate slice,
`scripts/dev/_frontend_gate_heatmap_access.py`) to prove it live. Resolves
F-B21-14.

Fix round 1: the check now asserts the reached cell's own `tabindex="0"`
attribute and that every `.heatmap-cell` in the grid carries it (naming the
count missing), and asserts the authored focus ring by its four computed
properties -- `outline-width: 2px`, `outline-style: solid`,
`outline-offset: 1px`, and `outline-color` equal to `--shell-accent`'s
computed colour read via a probe element -- rather than the generic
`outlineStyle !== 'none'` a bare UA default outline also satisfied.

Fix round 2: the check is now registered for the desktop AND mobile
profiles in `scripts/dev/frontend_gate.py` (previously desktop only, so a
regression in `renderHeatmapMobile`'s own tabindex/role/aria-label lines
went unseen), and seeds a 14-day range instead of one day, so the
"every `.heatmap-cell` carries tabindex=0" audit sees more than one cell
(it now fails outright on a grid of 1 or fewer, naming the count).

Validation: `pytest -q` -- **1978 passed**.

### 2026-09-27 - Move four dev-only pins out of the production install

Side task, no batch tag: move four dev-only pins out of the production install, part of
Batch 23 WP-0 Part C. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.
`virtualenv==20.36.1`, `distlib==0.3.9`, `filelock==3.20.3` and `platformdirs==4.3.6`
moved from `requirements.txt` to `requirements-dev.txt` (F-B21-3 remainder); nothing in
`scrobblescope/` imports them (`git grep` confirmed no hits). A live `pip-audit` recount
on 2026-09-27 found 0 vulnerabilities in 0 packages against `requirements.txt` alone, 0
against both files together.
Validation: `pytest -q` -- **1965 passed**.

### 2026-09-27 - A two-state toggle that reattaches to the system

Side task, no batch tag: fixed the theme toggle so a choice matching the system preference
clears the stored value and lets the page reattach to the system, part of Batch 23 WP-0
Part C. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands. `theme.js`'s
`darkSwitch` `change` listener now computes the system's preferred scheme via
`matchMedia('(prefers-color-scheme: dark)')` and calls `localStorage.removeItem('darkMode')`
when the chosen state matches it, instead of always writing the choice; `base.html`'s
pre-paint script already treats a missing key as "follow the system", so no change was
needed there. `scripts/dev/_frontend_gate_theme.py` adds
`check_theme_reattaches_to_system` (registered in `frontend_gate.py`'s `CHECKS` tuple,
`THEME_MOTION` group, beside "theme persistence"), which forces the toggle away from an
emulated dark system, confirms the choice persists across a reload, then flips it back to
match the system and confirms `localStorage.getItem('darkMode')` clears immediately and the
page still resolves dark from the system query alone after a reload. Resolves F-B21-22.

Validation: `pytest -q` -- **1965 passed**.

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
