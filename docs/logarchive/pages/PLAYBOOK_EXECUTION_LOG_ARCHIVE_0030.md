<!-- DOCSYNC:ARCHIVE-PAGE v1 -->
# PLAYBOOK_EXECUTION_LOG_ARCHIVE -- page 0030

### 2026-10-20 - The production image no longer installs requests

Side task, no batch tag: `requests` and its three private dependencies moved from `requirements.txt` to `requirements-dev.txt`, on `chore/pre-batch23-hygiene`, a branch off `main`.

Owner intent: the Dockerfile installs `requirements.txt` only, so the image should hold only what the app imports (owner, 2026-10-20: "Sure, if it's cheap and you think it would be wise.").

What changed: `requests` is imported only by `scripts/testing/` (`_http_client.py`, `concurrent_users_test.py`, `smoke_cache_check.py`), and among production packages `urllib3`, `charset-normalizer` and `certifi` are required by `requests` alone (`importlib.metadata.requires`). All four pins moved, unchanged, to `requirements-dev.txt`. `idna` stays: `yarl`, which `aiohttp` needs, requires it. CI's pip-audit still reads both files, so the moved pins stay audited. New `tests/test_requirements_split.py` parses every runtime file (`app.py`, `run.py`, `init_db.py`, `scrobblescope/`) and asserts each third-party import resolves to a distribution `requirements.txt` pins.

Mutation evidence: in a scratch copy, adding `import requests` to `scrobblescope/config.py` and removing the four pins failed the test with `scrobblescope\config.py imports requests`; on the real tree it passes.

Deviations: none. No existing test was edited.

Validation: `pytest -q` -- **2543 passed**.

### 2026-10-20 - Python 3.13 spellings for UTC and timeouts

Side task, no batch tag: the UP017 and UP041 alias fixes, on `chore/pre-batch23-hygiene`, a branch off `main`.

Owner intent: the Dockerfile and CI run Python 3.13, so the code should use its spellings (tranche design, PR #2).

What changed: `ruff check --target-version py313 --select UP017,UP041 --fix` rewrote 21 `timezone.utc` uses to `datetime.UTC` and one `asyncio.TimeoutError` to the builtin `TimeoutError` (the same class since 3.11), in `scrobblescope/heatmap.py`, `lastfm.py`, `orchestrator/__init__.py`, `routes/__init__.py`, `spotify.py`, `scripts/dev/graphify_refresh.py`, `tests/services/test_lastfm_logic.py` and `tests/test_heatmap.py`. No behaviour changes; the ruff target itself is the next commit.

Deviations: the `timezone` imports the rewrite left unused were removed (F401, by the ruff hook and two by hand), and ruff-format re-wrapped lines the shorter spelling freed. The UP041 fix also reordered the `except` tuple in `scrobblescope/spotify.py` from `(aiohttp.ClientError, asyncio.TimeoutError)` to `(TimeoutError, aiohttp.ClientError)`; it catches the same two classes, so behaviour is unchanged. The two test files changed only by the alias spelling and that wrapping; no assertion was edited. Existing tests edited by name (spelling or wrapping only): in `tests/test_heatmap.py` `test_boundary_timestamps`, `test_out_of_range_excluded`, `test_midnight_boundary_attribution`, `test_utc_decode_invariant_against_local_tz_drift`, `test_happy_path_stores_correct_result_dict`, `test_success_is_readable_through_repository_at_100_percent`, `test_progress_callback_sends_correct_percentages` and `test_heatmap_lastfm_phase_and_cleared_at_completion`, plus the `_make_track` helper; in `tests/services/test_lastfm_logic.py` the `_track` helper.

Validation: `pytest -q` -- **2542 passed**.

### 2026-10-20 - Spell the empty top-artist dash as an escape

Side task, no batch tag: the empty top-artist dash is spelled as an escape, on the include-unmatched branch (a small PR off main after the cover-washes PR).

Owner intent: keep hand-written files pure ASCII, as the middle-dot commit did.

The previous commit left a literal em dash in `static/js/results.js` and `scripts/dev/results_behavior_tests.py`, which were pure ASCII before it; both now spell it `\u2014` (the scoped review's one Minor). The rendered value is unchanged.

Deviations: none. Edited existing tests: none (the two assertion strings in `scripts/dev/results_behavior_tests.py` changed spelling only).

Validation: `pytest -q` -- **2581 passed**.

### 2026-10-20 - File the Listening Time toggle's durationless rows

Side task, no batch tag: F-B23-46 is filed for the Listening Time toggle's durationless rows, on the include-unmatched branch (a small PR off main after the cover-washes PR).

Owner intent: a real inconsistency Codex found is recorded, not smuggled into this PR.

After Hide, or on any play-count run switched to Listening Time in the browser, matched albums with no Spotify duration rank last and show a dash, while a run that starts in playtime mode drops them server-side. `main` behaves the same for play-count runs, so it is not this PR's change; the finding (Codex comment 4330862249) leaves the one-rule decision to the UI-consistency PR.

Deviations: none. Edited existing tests: none. New: none.

Validation: `pytest -q` -- **2581 passed**.

### 2026-10-20 - Clear the top artist when Hide leaves no rows

Side task, no batch tag: the Top Artist stat clears when Hide leaves no rows, on the include-unmatched branch (a small PR off main after the cover-washes PR).

Owner intent: the stats under Hide describe only the rows still on the page.

On an include run whose rows are all unmatched (every lookup unavailable), Hide left Total Albums and Scrobbles at 0 while Top Artist still named the artist of a hidden row (Codex review on PR #256, comment 4330862255). `setUnmatchedHidden` in static/js/results.js now writes the template's empty-state dash into the Top Artist text and title when no row is visible; with rows left it is unchanged. The other Codex comment of that review (4330862249) is not material to this PR and is filed as F-B23-46.

Deviations: `include_run` in scripts/dev/results_behavior_tests.py takes an optional row list. Edited existing tests: none. New: test_hiding_every_row_clears_the_top_artist_and_including_restores_it (results-behavior script).

Validation: `pytest -q` -- **2581 passed**.

### 2026-10-20 - Say when an unmatched release reads unknown

Side task, no batch tag: three live docs say when an unmatched row's release reads "unknown", on the include-unmatched branch (a small PR off main after the cover-washes PR).

Owner intent: the docs follow the code, so a date MusicBrainz finds is not described as always unknown.

README.md, DESIGN.md (Results Row: Unmatched Variant) and the RECONCILIATION ledger row "Results: unmatched albums" said the release cell simply reads "unknown"; it does so only until a found original release replaces it (YYYY-MM). New RECONCILIATION section 25 records the found-date rule, that the server and results-release-checks.js render the same text, the Codex finding on PR #256, and that the moved-out note is still script-only (F-B23-45). Section 21's wording is left as a dated record.

Deviations: none. Edited existing tests: none. New: none.

Validation: `pytest -q` -- **2581 passed**.

### 2026-10-20 - page-motion.js is named like the other scripts

Side task, no batch tag: `static/js/page_motion.js` renamed `page-motion.js`, on `chore/pre-batch23-hygiene`, a branch off `main`.

Owner intent: files served as URLs conventionally use hyphens, and `page_motion.js` was the only script name in `static/js/` with an underscore (owner, 2026-10-20: "What is best practice here?" -> hyphens).

What changed: `git mv` of the script; `templates/base.html` names `js/page-motion.js` in its one `url_for`; `.claude/SESSION_CONTEXT.md` Section 3 lists `page-motion` in the `js/` line. Run before the template was updated, the Task 1 guard failed all 8 parametrised cases naming `/static/js/page_motion.js`; after it, all 8 pass. The frontend gate reports 45 checks passed in 71 runs across chromium and firefox, with no load fault naming `page-motion.js`. `docs/design/designsystemaudit.md` and dated plans and logs keep the old name as point-in-time records.

Deviations: none. No existing test was edited.

Validation: `pytest -q` -- **2542 passed**.

### 2026-10-20 - A page never loads a static file the repository lacks

Side task, no batch tag: a guard test that every local script and stylesheet a rendered page loads exists, on `chore/pre-batch23-hygiene`, a branch off `main`.

Owner intent: nothing fails today when a template names a static file that is not shipped, and the next commit renames `page_motion.js`, so the guard comes first.

What changed: `test_every_local_script_and_stylesheet_a_page_loads_exists` in `tests/test_template_shell.py` renders each template in `TEMPLATE_CONTEXT`, collects every `/static/` script and stylesheet reference (query strings dropped), and asserts each file exists under `static/`. It also asserts a page loads at least one, so a wrong pattern cannot pass vacuously. A missing file otherwise 404s silently in the browser and the frontend gate prints it only as an advisory beside a FAIL.

Mutation evidence: renaming `templates/base.html`'s `filename='js/page_motion.js'` to `page_motionX.js` failed all 8 parametrised cases, for example `index.html loads files the repository lacks: ['/static/js/page_motionX.js']`; restored, all 8 pass.

Deviations: none. No existing test was edited.

Validation: `pytest -q` -- **2542 passed**.

### 2026-10-20 - The pre-Batch-23 tranche plans are recorded

Side task, no batch tag: the master plan and the hygiene plan for the side-task PRs before Batch 23 WP-1, on `chore/pre-batch23-hygiene`.

Owner intent: plans written before any code, sliced for parallel subagents, and kept in the repository for the record (owner, 2026-10-20: "All plans should stay for archival purposes").

What changed: `docs/superpowers/plans/2026-10-20-pre-batch23-tranche.md` orders the eight PRs in waves so no two edit the same lines at once, and defines how each remaining PR's plan is written and reviewed before its code. `docs/superpowers/plans/2026-10-20-pre-batch23-hygiene.md` is this branch's own plan: a test that every static file a page loads exists, `page_motion.js` renamed `page-motion.js`, ruff targeting Python 3.13, and `requests` with its own dependencies moved to the development requirements. Measured for the plans: `pytest -q` collects 2534 tests, 59 of them browser-marked, so the pinned count includes the browser tests that CI runs in its frontend-gate step; pre-commit takes about 9 seconds on this tree.

Deviations: the spec's hygiene item "a check that the pinned test count includes browser-marked tests" is answered by the measurement above rather than a new mechanism; the documentation PR states it where tests are explained.

Validation: `pytest -q` -- **2534 passed**.

### 2026-10-20 - The pre-Batch-23 tranche design is recorded

Side task, no batch tag: the design for the side-task PRs that run before Batch 23 WP-1, on `chore/pre-batch23-hygiene`, a branch off `main`.

Owner intent: before the Spotify export import, make the documentation describe the system as it is, check every diagram against the source, make the interface consistent, clear backend hygiene items, and build four of the seams the 2026-09-30 architecture review proposed -- each as its own PR with atomic commits.

What changed: `docs/superpowers/specs/2026-10-20-pre-batch23-tranche-design.md` records the design the owner approved section by section on 2026-10-20: the eight PRs and their order, the rules every PR follows (a Section 4 entry per commit, Batch 23 definition amendments when a seam changes what a work package may assume, parity tests before a refactor, tests that assert intended behaviour), the review policy that keeps fix rounds from looping, the documentation PR's content, the UI loop, and the hosting cost ceiling that keeps job persistence out of this tranche. The implementation plans follow in later commits on this branch. PLAYBOOK Section 3 gains its pointer to this spec once the include-unmatched PR, which adds the Section 3 bullet for this tranche, has merged.

Deviations: none. No code change, no test edited.

Validation: `pytest -q` -- **2534 passed**.

### 2026-10-20 - File the release note that a reload drops

Side task, no batch tag: finding F-B23-45 filed for the moved-out release note a reload drops, on the include-unmatched branch (a small PR off main after the cover-washes PR).

Owner intent: a verified Codex review finding that is real but outside this PR is filed, not fixed in passing.

The "first released" note on a Results row is added only by the polling script, so a page rendered after the check ended shows none for a moved-out row. It predates this PR for matched rows; the previous commit made the date itself render server-side for unmatched rows. F-B23-45 records the close: render the note from the stored row, sharing its text with the script.

Deviations: none. Edited existing tests: none. New: none.

Validation: `pytest -q` -- **2581 passed**.

### 2026-10-20 - A release date found for an unmatched row survives a reload

Side task, no batch tag: the Results page renders the release date MusicBrainz found for an included unmatched album, on the include-unmatched branch (a small PR off main after the cover-washes PR).

Owner intent: judge the Codex review finding on PR #256 and fix it if material; it was ruled material.

The release cell of an unmatched row was always "unknown" with an empty export value, and only results-release-checks.js filled the date in, while its bar renders only until the check ends. A page rendered after the pass finished (reload, back-navigation, or a cached pass that ended first) therefore hid a date already stored on the row. templates/results.html now renders the first seven characters of original_release_date, with the full date as its export value, when release_check is confirmed or moved_out, the rule the script applies; any other state keeps "unknown". The script sets the same text on a row already filled, so nothing doubles. The "first released" note for a moved-out row is not rendered server-side; that is filed as the next finding.

Deviations: none. Edited existing tests: none. New: test_results_page_renders_a_found_date_on_an_unmatched_row (four cases; mutation: the old unconditional unknown cell fails the confirmed and moved_out cases, a rule ignoring release_check fails the unavailable case that carries a stale date).

Validation: `pytest -q` -- **2581 passed**.

### 2026-10-20 - The new count-line tests spell the middle dot as an escape

Side task, no batch tag: the count-line tests in tests/test_routes.py spell the middle dot as an escape, on the include-unmatched branch (a small PR off main after the cover-washes PR).

Owner intent: "One small commit would be worthwhile."

The scoped review (Minor 3) found the six count-line assertions added with the Unmatched page split used a literal middle dot, against the ASCII-only rule for hand-written files. They now write `·` inside the same plain strings, so each compared value is unchanged; the older hits in the frontend gate files predate this PR and stay.

Deviations: none. Edited existing tests: none. New: none.

Validation: `pytest -q` -- **2577 passed**.

### 2026-10-20 - The Unmatched page says which albums the results list

Side task, no batch tag: the Unmatched page tells an include run which of its albums the results already list, on the include-unmatched branch (a small PR off main after the cover-washes PR).

Owner intent: "Split the count (Recommended)" -- the count line names both groups, and the No match found and Could not be checked sections say their albums are in the results.

An include run lists its No match found and Could not be checked albums as unmatched rows, yet the page said "N albums left out of your results". `_listed_unmatched_counts` in `scrobblescope/routes/album_flow.py` marks a report entry as listed only when a result row carrying `unmatched_reason` has the entry's report key (a Show limit can cut rows, so the reason code alone is never trusted). `templates/unmatched.html` then reads "L albums listed in your results without a match, K left out" (", K left out" dropped at zero; the old line when nothing is listed) and adds `unmatched-listed-note` under each group description holding listed albums. README names the new line, and `docs/design/RECONCILIATION.md` records it as Section 24 plus a ledger row (note text 14.78:1 light, 15.21:1 dark).

Deviations: none. Edited existing tests: none. New: `test_unmatched_page_count_line_names_listed_and_left_out` and `test_unmatched_page_sections_say_which_albums_the_results_list`.

Validation: `pytest -q` -- **2577 passed**.

### 2026-10-20 - Listening time is promised only when it is there

Side task, no batch tag: the Results Unmatched albums control promises listening time only when the run has durations, on the include-unmatched branch (a small PR off main after the cover-washes PR).

Owner intent: the Play count / Listening Time control must reflect an include run accurately.

On a run with no Spotify durations, choosing Hide toasted "Unmatched albums hidden; listening time is available." while Listening Time stayed disabled, and the help line under the control promised the same. `setUnmatchedHidden` in `static/js/results.js` now uses the `available` value it already computes: the long toast only when Listening Time really became available, otherwise "Unmatched albums hidden."; `templates/results.html` renders "Hide removes the unmatched listens from the leaderboard." when `has_durations` is false and keeps the old line otherwise. `docs/design/RECONCILIATION.md` records it as Section 23 plus a ledger row.

Deviations: none. Edited existing tests: `test_matched_only_without_durations_leaves_listening_time_off` (gains the toast assertion). New: `test_results_include_run_help_promises_listening_time_only_with_durations`.

Validation: `pytest -q` -- **2570 passed**.

### 2026-10-20 - The dashboard names the tranche and its date

Side task, no batch tag: the session dashboard names the side-task tranche and carries today's date, on the include-unmatched branch (a small PR off main after the cover-washes PR).

Owner intent: the dashboard must say what PLAYBOOK Section 3 says, so a new session is not misled about what comes before WP-1.

A freshness audit found `.claude/SESSION_CONTEXT.md` still reading `Last updated: 2026-09-30` although this branch changed it on 2026-10-20, and its `Batch 23 status` row silent on the tranche of side-task PRs that PLAYBOOK Section 3 describes. The date is now 2026-10-20 and the row gains one sentence naming the tranche. Nothing else in the row changed; the Tests row and DOCSYNC STATUS block are untouched. No deviations; no existing test edited.

Validation: `pytest -q` -- **2568 passed**.

### 2026-10-20 - The gate keeps the index card centred at 1080p

Side task, no batch tag: the frontend gate fails when the index card is pinned under the header at 1080p, on the include-unmatched branch (a small PR off main after the cover-washes PR).

Owner intent: the owner saw the index card stop being centred once the separate Albums field made it taller ("the index card isn't properly centered"); the gate should catch that.

What changed: `_form_centring_failures` in `scripts/dev/_frontend_gate_layout.py`, called from `check_large_display_scale_parity` for the 1080p window (1920x945, default state). `positionForm` places the card at `max(0.25rem, (available - height) / 2 - 2.5rem)`, so while the centring term governs the space below the card exceeds the space above by 2 x 2.5rem = 5rem; the check holds that to 2px (rect rounding) and names a card sitting on the 0.25rem clamp as pinned. `_wide_layout_failures` could not see it because it mirrors the clamp in its expected value. Three unit tests in `tests/scripts/dev/test_frontend_gate_layout.py` cover the healthy, pinned and off-centre cases.

Deviations: the brief said the two spaces should be "within one 2.5rem lift of each other"; the rule makes the correct difference 5rem (the lift applies once above and the centring halves the rest), so the tolerance is derived from that. No existing test edited.

Validation: `pytest -q` -- **2568 passed**.

### 2026-10-20 - The Results control is named as on the index card

Side task, no batch tag: the Results page's unmatched control takes the index card's wording, on the include-unmatched branch (a small PR off main after the cover-washes PR).

Owner intent: the two controls should read the same ("Yes that looks good to me", 2026-10-20, on renaming the Results control to match).

What changed: in `templates/results.html` the Sort leaderboard card's control reads "Unmatched albums" with "Hide" then "Include" (Include selected on an include run) and the help "Hide removes the unmatched listens so the leaderboard can be ranked by listening time."; ids, name and values (`results_albums_all` = all, `results_albums_matched` = matched) are unchanged, so `results.js` is untouched apart from three comments. The include gate check, the results-behavior fixture, three comments in `results.js` and `results.css`, README, DESIGN.md, F-B23-43's prose and RECONCILIATION (section 22, ledger rows) follow.

Deviations: none. Edited existing tests: `test_results_include_run_marks_unmatched_rows_and_locks_listening_time`, `test_results_include_run_offers_the_albums_control_for_one_album` and `test_results_plain_run_renders_none_of_the_include_elements` (new copy; the first also asserts the Hide-then-Include order).

Validation: `pytest -q` -- **2564 passed**.

### 2026-10-20 - The unmatched choice joins the Show row

Side task, no batch tag: the index card's unmatched choice moves into the Show row and is renamed, on the include-unmatched branch (a small PR off main after the cover-washes PR).

Owner intent: the separate Albums field made the index card tall and pinned it under the header, so tuck the choice under Show, split the row evenly and make the toggle clearer (rulings 2026-10-20, verbatim in `docs/design/RECONCILIATION.md` section 22).

What changed: `templates/index.html` puts the Show select and the unmatched choice in one `.field-pair` (equal halves from 860px, stacked below, `static/css/index.css`). The label reads "Unmatched albums", the options "Hide" (value 0, default) and "Include" (value 1); ids, name and values are unchanged. The help "Albums Spotify and Deezer can't find, ranked by play count." is rendered `hidden` and `syncUnmatchedLock` in `static/js/index.js` shows it only while Include is chosen. At 1920x945 the default card measures 611px (it was 719px, pinned under the header). The forms gate asserts the help is hidden under Hide and on screen with its exact text under Include, and measures its 7:1 contrast with Include chosen. README, DESIGN.md, three docstrings, a test comment and RECONCILIATION (new section 22, ledger row) follow the code. The Results control keeps its wording until the next commit.

Deviations: none. Edited existing tests: `test_index_albums_control_is_a_pair_of_native_radios` (new copy, hidden help, the shared row) and the docstring of `test_results_loading_passes_the_include_flag_to_the_job_thread`.

Validation: `pytest -q` -- **2564 passed**.

### 2026-10-20 - The tooling diagram draws the include check's imports

Side task, no batch tag: the tooling diagram draws the include check's imports and the hover note is made true, on the include-unmatched branch (a small PR off main after the cover-washes PR).

Owner intent: the records must say what the code and the probes showed.

What changed: in `docs/architecture/documentation-tooling.md` the node `FGINC[_frontend_gate_include]` had no import edges and was missing from the `tool` class list; it now has `FGINC --> FGC` and `FGINC --> FGS` and is in the list. SESSION_CONTEXT Section 4 already lists both imports for the module. The entry "Hover selectors use one :not() list" said the hover check "exercises both selectors"; its probe showed otherwise, so that sentence now says the check guards the hovered ink's contrast, not that the hover rule applies. The Mermaid validator was not run; the controller validates the diagram.

Deviations: none. Documentation only; no test edited.

Validation: `pytest -q` -- **2564 passed**.

### 2026-10-20 - Retry keeps the listener's Albums choice

Side task, no batch tag: Retry on the loading page keeps the Albums choice, on the include-unmatched branch (a small PR off main after the cover-washes PR).

Owner intent: a retried search must repeat the listener's search exactly (owner ruling 2026-09-30: fix a found defect now rather than later).

What changed: an "All albums" run that failed retryably offered Retry, and `retryCurrentSearch()` in `static/js/loading.js` rebuilt the POST from `window.SCROBBLE`, which `templates/loading.html` fills from a hand-written `scrobble-config` block. Neither carried `include_unmatched`, so Retry silently re-ran the search as "Matched only". The block now has `"include_unmatched": include_unmatched|default(false)` (the route already passed it; the default keeps templates rendered without it working) and the script posts `include_unmatched=1` when it is true, nothing otherwise, as the index form does. New `tests/test_loading_retry_contract.py` derives the fields `results_loading` reads from `request.form` (an `ast` walk) and asserts each is a key of the config block and is posted by `retryCurrentSearch()`; it failed on the old tree naming `include_unmatched`, and deleting another field's `createHiddenInput` line makes it fail naming that field.

Deviations: none. No existing test edited.

Validation: `pytest -q` -- **2564 passed**.

### 2026-10-20 - The hover checks wait for transitions, not a timer

Side task, no batch tag: the segmented-control colour checks wait for the browser to finish their transitions instead of sleeping, on the include-unmatched branch (a small PR off main after the cover-washes PR).

Owner intent: no fixed-timer guesses in the frontend gate (PR #252 removed the others).

What changed: `seg_contrast_failures` and `seg_hover_failures` in `scripts/dev/_frontend_gate_colour.py` each did `page.wait_for_timeout(350)` before reading a colour that takes a 0.2s transition. Both now call `wait_for_settled` from `scripts/dev/_frontend_gate_shared.py`: the theme switch waits on the control's track, the hover waits on the hovered option. That adds an import of `_frontend_gate_shared` into `_frontend_gate_colour`, so the diagram in `docs/architecture/documentation-tooling.md` gains `FGC --> FGS` and its node label no longer says "pure maths, no page"; SESSION_CONTEXT Section 4's dependency graph gains the same edge and its file note; the module docstring and the DEVELOPMENT.md sentence that called the module pure colour maths now say it also holds the segmented-control checks. The Mermaid validator was not run; the controller validates the diagram.

Deviations: none. No test edited. Probe: a hover rule planted at `#999` fails the gate ("hovered unselected option text on track is 2.66:1, under 7.0:1"); breaking the selector alone (`.seg__optionX`) does not, because the unhovered ink already clears 7:1, so the check guards the hover ink, not the selector.

Validation: `pytest -q` -- **2561 passed**.

### 2026-10-20 - Hover selectors use one :not() list

Side task, no batch tag: the two chained `:not()` hover selectors in `static/css/shell.css` become one `:not()` list each, on the include-unmatched branch (a small PR off main after the cover-washes PR).

Owner intent: clear the Codacy findings on PR #256 at the cause.

What changed: Codacy (Stylelint `selector-not-notation`, "Expected complex :not() pseudo-class notation", 2 minor) flagged `.seg__radio:not(:disabled):not(:checked) + .seg__option:hover` and `.metric-toggle-btn:not(:disabled):not([aria-pressed="true"]):hover`, the only chained `:not()` selectors in the app's own stylesheets. They are now `.seg__radio:not(:disabled, :checked) + .seg__option:hover` and `.metric-toggle-btn:not(:disabled, [aria-pressed="true"]):hover`. In Selectors Level 4 `:not(A, B)` matches exactly what `:not(A):not(B)` matches, so behaviour is unchanged (Chromium 88+, Firefox 84+, Safari 9+). The frontend gate's segmented-control hover check (`seg_hover_failures` in `scripts/dev/_frontend_gate_colour.py`) guards the hovered ink's contrast, not that the hover rule applies: with the selector broken the gate still passed, because the unhovered ink already clears 7:1, while a planted low-contrast hover colour fails it ("hovered unselected option text on track is 2.66:1, under 7.0:1"). No test, gate module or document quoted the old text.

Deviations: none. No test edited.

Validation: `pytest -q` -- **2561 passed**.

### 2026-10-20 - The Albums help no longer sits on a line break

Side task, no batch tag: the index card's Albums help is reworded so it sits clear of a line break, on the include-unmatched branch (a small PR off main after the cover-washes PR).

Owner intent: PR #256 must pass CI at the root cause, not by loosening the gate.

What changed: CI run 39482227535 (Linux Chromium) failed the large display scale parity check on the index page: "form composition height is 961.6px at 1440p, expected proportional 984.1px" and "form height is 873.3px at 1440p, expected proportional 895.8px". The old help, "All albums keeps the ones Spotify and Deezer can't find, ranked by play count only.", overflowed one line by about 6%: measured locally it wraps to 2 lines at 1080p (last-line slack 407.3px of 432.3px) and 2 lines at 1440p (496px of 526.4px). Font size and column both scale with `--index-scale`, but rasterization differs by pixel size and platform, so in CI the sentence fit one line at 1440p and stayed at two at 1080p; the 1440p form was one help line (21.97px) shorter, and the check correctly reported it. The help now reads "Adds the albums Spotify and Deezer can't find, ranked by play count.": one line with 69.7px slack of 432.3px at 1080p and 85.4px of 526.4px at 1440p (about 16% both). `templates/index.html`, the pinned sentence in `scripts/dev/_frontend_gate_forms.py` and the quoted copy in `docs/design/RECONCILIATION.md` follow. The hazard class is filed as F-B23-44 (a gate check for wrap-boundary slack).

Deviations: the frontend gate and results-behavior script were not run here (another browser gate may be running; the controller runs them and CI verifies).

Edited existing check: the `UNMATCHED_HELP` constant read by the Albums help check in `scripts/dev/_frontend_gate_forms.py`.

Validation: `pytest -q` -- **2561 passed**.

### 2026-10-20 - The redundant tr[hidden] rule is filed

Side task, no batch tag: the `tr[hidden]` rule in `static/css/results.css` is filed as F-B23-43, on the include-unmatched branch (a small PR off main after the cover-washes PR).

Owner intent: keep the findings list true to what the earlier entry promised.

What changed: the 2026-09-30 entry "MusicBrainz dates the unmatched rows on Results" said the rule "is filed as a finding by the controller", and it was not. F-B23-43 now names both rules (the one in `results.css` and the `[hidden]` rule with `!important` in the compiled `tailwind.css`) and says deleting the first needs a gate or behaviour assertion first.

Deviations: none. No code change, no test edited.

Validation: `pytest -q` -- **2561 passed**.

### 2026-10-20 - The production database sleeps after an idle hour again

Side task, no batch tag: the production database (`scrobblescope-db`) is set to stop after an idle hour again, and PLAYBOOK Section 3 names the work before WP-1, on the include-unmatched branch (a small PR off main after the cover-washes PR).

Owner intent: keep the Fly bill inside the $5 a month Fly waives for a personal organisation.

What changed: on 2026-10-01 `FLY_SCALE_TO_ZERO` was removed from the `scrobblescope-db` machine so the database stayed on. On 2026-10-20 the owner's Fly cost explorer showed $4.90 for 1-20 October ($0.24 a day), which projects past the waiver, so the controller restored `FLY_SCALE_TO_ZERO=1h` with `fly machine update` (machine healthy 3/3, app answered 200). The app holds no connection pool -- `cache.py` opens and closes a connection per use -- so the database can reach zero connections and stop. The release-command retry in `init_db.py` (PR #255) covers a deploy that finds it asleep, and the cache is optional at runtime, so a cold database costs the first job its cache, not its result. No repository file states the always-on setting, so none changes. Section 3 gains a bullet naming the side-task tranche before WP-1 and why job persistence waits: a database-backed job store would keep the database awake, which the hosting cost ceiling does not allow.

Deviations: none. No code change, no test edited.

Validation: `pytest -q` -- **2561 passed**.

### 2026-10-20 - Batch 23 planned scope accounts for the include-unmatched control

Side task, no batch tag: Batch 23 planned scope accounts for the include-unmatched control, on the include-unmatched branch (a small PR off main after the cover-washes PR).

Owner intent: keep the Batch 23 planned scope current, so WP-3, WP-5 and WP-6 plan for the include-unmatched control that shipped before WP-1.

What changed: `BATCH23_DEFINITION.md` gains a "Scope amended 2026-10-20" header paragraph, a WP-3 checkbox (the export path honours `include_unmatched`), a WP-5 checkbox (the source control and the include-unmatched control share the album form), and a sentence in WP-6's statistics contract (whether unmatched albums count in each summary). PLAYBOOK Section 3 no longer says to run the guard with `--base-ref origin/test`: that branch merged into `main` as PR #245 on 2026-09-30 and `origin/test` is deleted, so side-task PRs branch from `main`. The `Branch:` line is unchanged. SESSION_CONTEXT Section 1's Batch 23 row notes the amendment.

Deviations: none. No code change, no test edited. Review fix: PR #245's merge date reads 2026-09-30; the first version gave 2026-09-24, the date the PR was opened.

Validation: `pytest -q` -- **2561 passed**.

### 2026-10-01 - The release command waits for a waking database

Side task, no batch tag: `init_db.py`, the Fly release command, retries its schema step while the database wakes, instead of aborting the deploy on the first dropped connection. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

Problem: release v143 failed with "Schema init failed -- connection was closed in the middle of operation" and exit 1. The Postgres app had stopped; the release command's connection woke it, its proxy restarted mid-boot, and the script died on its first statement. Postgres reported ready 4 s later and a plain redeploy passed.

Change: `init_db.py` runs connect plus every statement as `_apply_schema` and retries it up to 6 attempts (sleeps 1, 2, 4, 8, 8 s, about 23 s) on `OSError`, `asyncio.TimeoutError` and asyncpg's `ConnectionDoesNotExistError`, `InterfaceError`, `CannotConnectNowError` and `ConnectionFailureError` only. A SQL error still fails at once. `asyncpg.connect` now has a 10 s timeout. Each retry prints one line naming the attempt and the exception type, never its text (global-rules Rule 6). The final failure keeps the single ERROR line and exit 1; that line also names only the exception type (plus the SQLSTATE code of a Postgres error), never its text. README's Deployment section says so.

Evidence: new `tests/test_init_db.py` (6 tests, no network, sleeps patched): two transient failures then success, a connection that opens then drops on its first statement (the v143 shape), a non-transient error after one attempt, a SQLSTATE suffix for a Postgres error, exhaustion with one ERROR line, and a DSN planted in the exception text absent from the retry and ERROR lines. Each fails under its own mutation in a scratch copy (no retry: 3 failed; OSError not transient; asyncpg error not transient; everything transient; message in the line; no connect timeout; no raise on the last attempt; no SQLSTATE in the ERROR line; retry wrapping only the connect, which fails only the first-statement test).

Validation: `pytest -q` -- **2534 passed**.

### 2026-10-01 - The ring check waits out animations before reading pixels

Side task, no batch tag: the heatmap focus-ring check waits for running animations to finish before it reads the cell's geometry and takes its screenshot, a fix from the third review of PR #245, on the review-fix branch that fast-forwards into PR #245's branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

Problem: the previous step's reproduction showed 8 of 20 last-cell screenshots landing while `#heatmap-result` was still crossfading in (opacity changed between the read before and the read after the shot), and a reading taken mid-animation is invalid by construction. PR #252 applied the same reasoning to every other check that slept through a transition; the ring check still waited only for fonts and two frames.

Change: `_ring_shot` in `scripts/dev/_frontend_gate_heatmap_access.py` calls `wait_for_settled` (`scripts/dev/_frontend_gate_shared.py`, bounded, raises when the page never settles) at the start of each attempt, after the tooltip nudge and before `_LAYOUT_SETTLED_JS` and the geometry read. This removes a confounder; it is not claimed as the fix for F-B23-39, whose status stays open.

Evidence: a new test records the order of the wait and the geometry reads over a two-attempt run; with the call removed it fails (`assert 0 == 2` on the wait count). The existing ring-page helper answers the settle script with an empty result so the real `wait_for_settled` can run against it. The 20-run reproduction (the check alone, fresh desktop context each, `reduced_motion="no-preference"`) passed 20 of 20, with `container.opacity` 1 and nothing changed during the shot on all 80 shots read (4 per run). A ring forced to `visibility=hidden` still fails with `ring.visibility=hidden` in the evidence.

Validation: `pytest -q` -- **2528 passed**.

### 2026-10-01 - The ring check also reads opacity and animations

Side task, no batch tag: the heatmap focus-ring check also reads the result's opacity and running animations when it fails, a test of the crossfade hypothesis for F-B23-39, a fix from the third review of PR #245, on the review-fix branch that fast-forwards into PR #245's branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

Problem: CI run 36808671140 (Linux, desktop, 043368eb) failed the ring check with the ring visible, 1.6px outside the cell, stroke the accent, `:focus-visible` held, tooltip clear of the ring and nothing moved: the DOM said painted, the pixels said not. The one state the evidence line did not read is opacity. `static/js/heatmap.js` `revealHeatmapResult` crossfades `#heatmap-result` in (`heatmap-fade`, `fading-out`, `is-handing-off`, 180 ms handoff) unless `prefers-reduced-motion: reduce` matches, and `_LAYOUT_SETTLED_JS` waits for fonts and frames, not animations.

Change: `_RING_EVIDENCE_JS` in `scripts/dev/_frontend_gate_heatmap_access.py` also reads the result container's and the SVG's computed `opacity`, the container's three crossfade flags, how many `document.getAnimations()` are `running`, and the page's `prefers-reduced-motion` match, in the same evaluation as the geometry (so on both sides of the shot, the suffix from the read after it). The suffix gains `container.opacity`, `svg.opacity`, `container.heatmap_fade`, `container.fading_out`, `container.is_handing_off`, `animations.running` and `prefers_reduced_motion`, and `changed_during_shot=` names them when they differ between the two reads. Three tests (38 in the file).

Reproduction, no fix: the check alone, 20 times in one desktop Chromium, with `reduced_motion="no-preference"`: 20 of 20 passed, twice; 20 of 20 with no emulation. The page reports `prefers-reduced-motion: reduce` matches False in the ordinary local run, so the premise that a local run skips the fade is false on this machine. With the evidence read on every shot of one `no-preference` run, 8 of its 20 last-cell shots had a different container opacity before and after the screenshot (so a shot can land inside the fade, on the very cell that failed on CI), and the ring still painted each time; the no-emulation run showed none. No iteration failed, so by the rule for this task the crossfade hypothesis is not confirmed and `_ring_coverage` does not wait for animations. F-B23-39 records the lead. The next CI failure's line will show it.

Validation: `pytest -q` -- **2527 passed**.

### 2026-10-01 - The heatmap ring check says why a ring is unpainted

Side task, no batch tag: the heatmap focus-ring check names its cause when it fails, an evidence-first step for F-B23-39. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

Problem: `heatmap cells keyboard access` fails now and then with "paints no rgb(106, 75, 175) pixel ... (samples painted: top 0%, right 0%, bottom 0%, left 0%)" and passes on a re-run (ccc2c921 [mobile], dce6f148 [mobile], CI run 36726578353, and CI run 36803075335 on PR #253 [desktop], which had no failed app resources). The line said only that nothing was painted, so a ring that was never shown, a ring in the wrong place, another stroke and a tooltip over the ring all looked the same.

Change: a ring failure in `scripts/dev/_frontend_gate_heatmap_access.py` now ends with one `[evidence: key=value ...]` suffix (`_RING_EVIDENCE_JS`), read in the page in the same evaluation as the geometry, before and after the screenshot; the suffix is built from the read after it, and `changed_during_shot=` names the evidence fields that differed between the two reads (reported, never judged): the ring's `visibility` and box, the cell's box, `document.activeElement` and whether it matches `:focus-visible`, `document.hasFocus()`, the ring's computed stroke, `data-theme`, the tooltip's box, whether it is shown and whether it covers the ring, the scroll offset, `devicePixelRatio`, how many cells paint after the ring, and how long the settle wait took (`settle_slow` past one second). `_ring_shot` returns the coverage and the evidence; `_ring_coverage` keeps its old return. Probe: with `showFocusRing` forced to `hidden` in a scratch copy of `static/js/heatmap.js`, the check failed on all three cells with `ring.visibility=hidden`; restored, it passed. Eleven tests in `tests/scripts/dev/test_frontend_gate_heatmap_access.py` cover the line, the slow-settle flag and the two-sided read; those that read the suffix fail without it.

Root cause not found, so no fix to the check: every check in a group and profile shares one context (`frontend_gate.py` `open_page` makes one per group and profile), but nothing earlier in the `layout & pipeline` group writes `darkMode`, emulates a colour scheme or forced colours on that page (the pipeline check's init script runs on a probe page; the spotlight rotation check's stays on the desktop page but only shortens a 7000 ms interval and passes other fetches through, and the mobile failures have no such script), and 20 runs of the check in one desktop Chromium under a concurrent `pytest -q` all passed. F-B23-39 records what was ruled out; the next failure's evidence line names the cause.

Validation: `pytest -q` -- **2524 passed**.

### 2026-09-30 - MusicBrainz dates the unmatched rows on Results

Side task, no batch tag: MusicBrainz dates the unmatched rows on Results, on the include-unmatched branch (a small PR off main after the cover-washes PR). The commit landed on 2026-10-01; the entry keeps the day of the work.

Owner intent: an included unmatched album gets its release year once MusicBrainz finds it, without the list moving.

What changed: the page script (`static/js/results-release-checks.js`) fills the "unknown" cell of an unmatched row with YYYY-MM and puts the full date in the cell's `data-export` for a confirmed or moved-out finding; a moved-out row also gets the note. The worker and `/api/release_checks` already stored and served the outcome and the date for an unmatched row; new tests pin that, and the rank order. A new frontend-gate check, "include results page" (`scripts/dev/_frontend_gate_include.py`, desktop and mobile), seeds a real include job and asserts the marker and "unknown" text at 7:1 in both themes, the Albums control's option and selected text at 7:1 and its selected boundary at 3:1 against the track and against the card, Matched only (unmatched rows hidden, ranks 01..03, Listening Time enabled), the Sort leaderboard's unselected hover at 7:1, the selected option's forced-colours border equal to `Highlight`, and no horizontal overflow at 390 and 1280. A new behaviour-script test pins the fill. DESIGN.md's segmented-control track line now states the code: the page canvas fill, a 1px hairline border, the 8px radius and 3px padding at scale 1 (the old line also said a 999px pill and 4px padding, which the code never had). The architecture pages name the new gate module and the fill.

Fix (review fold-in, Minor 1): a cached finding and a fresh lookup now reach the same outcome for a result row. `_resolve_cached` stored confirmed for any cached date on the premise that a result is in the list because of that date, which does not hold for an included unmatched row; it would have shown a 1999 date as confirmed in a 2025 run. One function, `_result_outcome(original_release, params)` (unavailable, confirmed or moved out through `_matches_window`), now serves `_check_candidate` and `_resolve_cached`; a cached moved-out row raises the moved-out count as a fresh one does. Mutation: making `_resolve_cached` store confirmed unconditionally again fails `test_a_cached_finding_gives_an_unmatched_row_the_outcome_a_lookup_would[out_of_window]` (`assert 'confirmed' == 'moved_out'`); restored, 55 passed. No exception text reaches a log line. The architecture page's `_frontend_gate_layout` line was reflowed (Minor 4).

Deviations: DESIGN.md also corrected the track's radius and padding, as above. The `tr[hidden]` rule in `static/css/results.css` looks redundant (the rows are hidden by the `[hidden]` rule in the compiled sheet); it is not touched here and is filed as a finding by the controller.

Known limits: this entry replaces the wording Task B's entry carries. The Albums control's option and selected text and the Sort leaderboard's unselected hover at 7:1 in both themes, and the selected option's forced-colours `Highlight` border, are now asserted on the rendered include page by the gate. The remaining limit: the gate seeds the page and does not render a live MusicBrainz pass (the behaviour script and pytest cover the fill and the worker).

Edited existing tests: test_run_release_checks_records_the_date_from_a_cached_finding (its cached date moved from 1977-02-04 to 2025-01-15, inside the job's 2025 window, so the cached finding is still confirmed under the one outcome rule).

Validation: `pytest -q` -- **2555 passed**.

### 2026-09-30 - Results list unmatched albums when the listener asks

Side task, no batch tag: unmatched albums on the Results page, an "Albums" control that hides them and one lifted look for every segmented control, on the include-unmatched branch (a small PR off main after the cover-washes PR). The commit landed on 2026-10-01; the entry keeps the day of the work.

Owner intent: an include run shows the albums Spotify and Deezer could not match, marked, and the listener can hide them to rank by listening time.

What changed: an include run merges the job's unmatched entries into the results (`merge_unmatched_rows`); each row has plain rank and title, the cover wash, a Not Found or Unavailable marker, an "unknown" release (the page script's `??` fallback was needed by that empty cell) and a play-count metric. Total Albums reads "listed" and Scrobbles sums every row. The Sort leaderboard card gains an "Albums" segmented control (All / Matched only, `name="results_albums"`) that hides the rows, renumbers, recounts and enables Listening Time. `.seg` and `.seg__option` moved to `static/css/shell.css`. The shared look is lifted per the owner rulings "The 4.5 is a floor not a goal" and "Precisely use what exists; segmented control": option text takes the body token (8.71 light, 10.61 dark on the track), the selected chip keeps its soft fill, gains a 1px primary border (6.06 / 8.14) and takes base-content text (14.81 / 13.04), and an unselected option deepens to base-content on hover (review fold-in, was primary at 6.06). Results' Sort leaderboard buttons take the same tokens through `aria-pressed`, which the template now renders. The frontend gate gains `seg_contrast_*` (text 7:1, boundary 3:1, both themes, four controls) and `seg_hover_failures` (hovered unselected option and the chip, 7:1, on the index Rank by control). `static/css/tailwind.css` was rebuilt by the drift hook. RECONCILIATION Section 21 and two ledger rows record the overrides; Section 20 notes that Section 21 moves the Results help to the same token; DESIGN.md and README follow.

Deviations: the behaviour script loads no stylesheet, so Results colour ratios are held in the frontend gate and the script holds the JS state; the marker and "unknown" facts are pinned by the route tests against the real template. The dating of "unknown" releases is not shipped here.

Known limits: the behaviour script's `include_run` fixture seeds a Top Artist the real page would not start with, and the toast text, the restored title after un-hide and the Top Artist update have assertions but no planted defect; the Results "Albums" control's contrast and the forced-colours `Highlight` border are not gated; no frontend-gate check renders a real include Results page yet.

Edited existing tests: test_results_include_run_marks_unmatched_rows_and_locks_listening_time (assertions).

Validation: `pytest -q` -- **2547 passed**.

### 2026-09-30 - The index card can include unmatched albums

Side task, no batch tag: the index card's "Include unmatched albums" switch and the sort lock, on the include-unmatched branch (a small PR off main after the cover-washes PR).

Owner intent: a quick toggle on the index card for the Last.fm albums Spotify and Deezer could not match, which blocks switching between play time and play count.

What changed: a native checkbox Switch between "Rank by" and "Show"; while it is on, Play time is disabled (dimmed, visible) and Play count is selected. The form field `include_unmatched=1` is stored as a job param (default False); an include run posted with `sort_by=playtime` is stored as play count, the same rule without scripts. The loading page lists "unmatched albums included". The off track is outlined in the muted text colour and the knob has a dark edge (`rgba(20, 16, 24, 0.75)`), because the kit's border-toned track measured 1.3:1 against the card. A frontend-gate check drives the switch by keyboard, reads its name and description, checks the track border under forced colours, and holds the track border and knob boundary at 3:1 in both themes, on and off (measured: track border 5.39:1 to 7.54:1 against the card; knob boundary, the stronger of edge and knob against the track, 4.98:1 at the lowest, dark on).

Deviations: the brief edited `docs/design/README.md` and two component prompts; the design-snapshot test forbids that, so the overrides are `docs/design/RECONCILIATION.md` Section 20 (after the cover-washes Section 19) and a ledger row, and DESIGN.md. Help text keeps the card's `.field__help` colour (5.5:1), pending the owner's design-system ruling. F-B23-39 gains one evidence sentence (three overlapping gate runs on this machine hit `ERR_NO_BUFFER_SPACE`).

Edited existing tests: none (four new tests in tests/test_routes.py).

Validation: `pytest -q` -- **2532 passed**.

### 2026-09-30 - Coverless albums get a deterministic two-tone wash

Side task, no batch tag: a missing album cover is drawn as a muted two-tone wash instead of a flat bordered box. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

Why: owner, 2026-09-30, on the Unmatched page's empty cover boxes: "it should have some sort of gradient pattern". The design system already says covers are "muted two-tone washes" (`docs/design/README.md`, `AlbumRow.prompt.md`); the code never drew them. Owner ruling, same day: Last.fm images are not trusted, so there is no image fallback of any kind.

What: eight pairs of `--ss-wash-N-a`/`-b` tokens in both themes of `static/css/tailwind.src.css` (compiled `tailwind.css` rebuilt), painted by `.cover-wash-N` in `static/css/results.css` (one shared rule set, forced colours drop the gradient and keep the border). `cover_wash_index` in `scrobblescope/domain.py` picks the pair from `zlib.crc32` of the normalised artist and album, so it is the same in every process (`hash()` is salted); the `cover_wash` template filter in `scrobblescope/routes/__init__.py` writes the classes. All four Unmatched placeholders and the Results image fallback use it; a portrait slot drops its wash once the photograph loads. No network call is added. A cover still loading wears its wash too: the cover `<img>` carries the same classes, so the wash shows until the picture paints and behind transparent pixels. The initials stay, in `--color-base-content`: 10.12:1 to 13.41:1 on every light stop and 10.72:1 to 14.04:1 on every dark stop (owner, 2026-09-30: "The 4.5 is a floor not a goal", so 7:1 is the line). RECONCILIATION section 19 records the palette and supersedes the snapshot README's sentence about Last.fm art replacing the washes (the snapshot is guarded and cannot be edited).

A test ties `COVER_WASH_COUNT` to the `.cover-wash-N` rules in `results.css` and to both stops in both theme blocks of `tailwind.src.css`.

Gate: `_cover_wash_page_failures` in `scripts/dev/_frontend_gate_unmatched.py` reads the coverless placeholders in both themes (two different gradient colours) and under forced colours (a painted border), and reads the tokens of all `COVER_WASH_COUNT` pairs in each theme, not the nodes on the page (the initials at 7:1 or better on both stops of every pair, whether or not the pair is on the fixture page, the failure naming the wash, the stop and the ratio; a colour it cannot parse fails loudly). Its fixture's Deezer row now has no cover so a coverless other-provider row is on the page. Live probe: a planted flat background, a planted `border: 0` and a planted pale light-theme stop on wash 0, a pair that is not on the fixture page, each failed the gate; restored, it passed.

Validation: `pytest -q` -- **2513 passed**.

### 2026-09-30 - Frontend-gate checks wait for transitions instead of sleeping

Side task, no batch tag: frontend-gate checks wait for the browser to finish a transition instead of sleeping a fixed time, a fix for the gate flakes seen after PR #245 and PR #251 merged, on its own branch off `main`. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

Cause: `index design tokens` added `is-valid`, slept a fixed 250 ms and read `borderColor`, while `static/css/index.css` gives the field a 200 ms border-color transition (PR #251 CI: `rgb(113, 207, 152)`, expected `rgb(111, 207, 151)`). That left 50 ms of slack, so a loaded runner read mid-transition. The heatmap-access checks had the same shape in 16 fixed sleeps.

Fix: `scripts/dev/_frontend_gate_shared.py` gains `wait_for_settled` (two frames, then every running finite CSS transition and animation under the element or document finishes, then two frames; a bounded wait that raises, so the check fails with a message) and `wait_for_scroll_past`. Every sleep that waited for a transition, paint, scroll or focus to settle now calls one of them: 1 in `_frontend_gate_layout.py`, 1 in `_frontend_gate_results.py`, 3 in `_frontend_gate_theme.py` and 16 in `_frontend_gate_heatmap_access.py` (a debounce-bound resize wait passes `after_timer_ms=100`, which outlasts the page's 100 ms resize timer). Fixed waits that remain each carry a comment: the negative waits (nothing more may happen) and the poll intervals of bounded wait-for-state loops. Each converted check still fails on its planted defect, and three tests in `tests/scripts/dev/test_frontend_gate_shared.py` drive the helper in a real Chromium page: a 60 s animation fails at the 300 ms bound with its message, a 150 ms one returns, a missing element is named.

One more flake the load runs exposed: `pipeline state machines` read `window.__scrobbleGateFastRedirect` on a loading page the gate's own timers redirect within about 100 ms of load, so a loaded machine could destroy the evaluate mid-call ("Execution context was destroyed"). The read now follows the redirect; the init script runs on every document, so the flag is set there too. The cause is by elimination (the only evaluate in that check on a page that navigates itself), not reproduced.

Validation: `pytest -q` -- **2496 passed**.

### 2026-09-30 - A flaky spotlight height test made deterministic

Side task, no batch tag: a test-only fix after PR #245 merged, on its own branch off `main`. `scripts/dev/results_behavior_tests.py::test_a_remeasure_under_focus_ignores_a_link_the_candidate_lacks` failed on Linux CI in 3 of about 6 runs (including the push to `main` after the merge) with `'116px' != '134px'`, and never in local whole-file runs.

Root cause: the test page aborts every request, and the test's own markup gives the spotlight `<img>` no size, so the aborted load fails at a moment no test controls; a failed image with alt text is an 18px line, so a height read that lands after the failure measures 134px and one that lands before measures 116px. Reproduced locally in fresh browser processes with the same message (8 of 100 runs, and 6 of 60 in a second count; 0 of 200 and 0 of 60 with the fix); the image's `offsetHeight` was 18 exactly in the reads that gave 134px. Test defect, not product: the production card holds its photo in the fixed-size `.spotlight-image-box`, so a failed photo adds no line.

Fix: the test's `LINK_LAYOUT_MARKUP` takes the photo out of the layout (`#spotlight-artist-img{display:none}`), with a comment saying why; the test is about the link's layout, not the photo. No product code changed, no test added or removed.

Validation: `pytest -q` -- **2493 passed**.

### 2026-09-30 - A rejected Spotify token is refreshed once, not once per call

Side task, no batch tag: single-flight Spotify token replacement, a fix from the third review of PR #245, on the review-fix branch that fast-forwards into PR #245's branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

Source: Codex comment 4146610714 on #245. N concurrent 401s (or concurrent fetches on an expired cache) each expired the cache and requested a token, up to one request per in-flight call. `fetch_spotify_access_token` now takes a lock held per running event loop (jobs run one loop per thread) and re-checks the cache inside it, so one expiry or rejection costs one token request per loop. The limit the Task 30 entry records as accepted (concurrent first 401s refetch) is now fixed; that dated entry is untouched.

Review fixes in the same commit: the per-loop dict is a `WeakKeyDictionary`, but a contended `asyncio.Lock` holds its loop strongly, so weak keys alone kept every contended loop alive (confirmed on Python 3.13); the getter now drops entries of closed loops, under one module-level `threading.Lock` held only for the prune, lookup and insert (never across an await), because every job thread shares that dict and an unguarded prune could raise `RuntimeError` or `KeyError` into a token fetch. A failed token request is shared: calls already waiting when it failed return no token instead of each issuing a request in turn (a per-loop failure count, so another job's failure cannot poison this one); a call that starts later tries again.

Files: `scrobblescope/spotify.py`, `tests/services/test_spotify_service.py`, `docs/architecture/top-albums-sequence.md`. No new module or import outside stdlib `weakref`; the dependency graph is unchanged.

Validation: `pytest -q` -- **2493 passed**.

### 2026-09-30 - Findings, dashboards and README made true for the merge

Side task, no batch tag: findings, dashboards and README made true for the merge, a fix from the third review of PR #245, on the review-fix branch that fast-forwards into PR #245's branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

Findings: F-B22-3, F-B21-61, F-MAS-5 and F-B18-2 named the removed job store (`repositories.py`, `create_job`, `cleanup_expired_jobs`, the `JOBS` dict); they now name `scrobblescope/jobs.py` (`jobs.create`, `jobs.expire_stale`, `MemoryJobStore`) by function. F-SWE-3 was already archived by the Task 30 landing; its archived body now says the one-try loop was how it stood when filed, and that a 5xx is retried now. `BATCH23_DEFINITION.md` WP-3 maps `ExportError` to a classified code through `jobs.fail` (the `set_job_results` at line 220 is a done, dated item and stays). F-B23-41 now records that the Results partial-notice link's ring and 44px are asserted only by a CSS-text test and the gate measures no such link.

Merge cut: PLAYBOOK Section 3 has a bullet stating what PR #245 ships and what moved to the follow-up PR (owner ruling 2026-09-29); the "next action" sentence that pointed at a finished review wave is reworded, and the seams bullet names only the work package each seam gates and points at that bullet for what ships. `**Next action:** WP-0 is next.` and the `**Branch:**` line are untouched. SESSION_CONTEXT Section 1 agrees.

Dashboards: SESSION_CONTEXT Section 3 no longer lists `global.css` (10 css files), and lists `results-release-checks.js`, the empty-state and two partial templates, and four `scripts/dev` files, with their edges in Section 4. `docs/architecture/top-albums-sequence.md` says once that every partial-data warning (token, search, details, Deezer fallback) also records its source through `jobs.record_partial_source`, and draws it at the token and Last.fm sites, and `runtime-system.md` lists it in the `jobs.py` interface. README: the `BATCH23_DEFINITION.md` link is gone (the rule is said in a sentence), the commit figure is the measured one (about 130 commits, 24 to 30 September), and the paragraph is rewrapped to 80 columns.

Code: the `heatmap_task` and `_report_album_failure` docstrings now say the album backstop always publishes `internal_error` while the heatmap classifies first. `.results-partial-notice__link` drops `white-space: nowrap` so the link wraps at 320px; confirmed at 320px by a Playwright measure of the notice with the shipped markup (page scrollWidth 320, no horizontal overflow), since the frontend gate renders no partial notice; the frontend gate and `results_behavior_tests.py` pass.

Known limit: an album-details 404 between Spotify refusals does not reset the per-job "three consecutive refusals" count; only a 200 does.

Validation: `pytest -q` -- **2487 passed**.
