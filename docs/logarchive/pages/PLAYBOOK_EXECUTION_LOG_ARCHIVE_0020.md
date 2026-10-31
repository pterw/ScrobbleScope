<!-- DOCSYNC:ARCHIVE-PAGE v1 -->
# PLAYBOOK_EXECUTION_LOG_ARCHIVE -- page 0020

### 2026-09-21 - Docsync renders an opened batch before its first entry

Side task, no batch tag: Task 3 of the Batch 23 WP-0 foundation plan, the
fix for audit defect D1 and its sibling D2, plus O1. Commit made with
`SKIP=doc-state-sync-check`, because it changes `scripts/docsync/`; the
checker was run directly at exit 0 first.

- D1: `_build_status_block` now branches on the batch Section 3 declares,
  not on whether entries exist, and `_computed_next_wp` no longer returns
  nothing for an empty current-batch block. An opened batch with nothing
  logged renders as that batch, and a false next-package claim raises
  DOC007. The between-batches block now carries the count line too.
- D2: under a finite plan, WP-0 is a real package (owner ruling), so a
  plan with nothing done names WP-0. The no-plan rule is unchanged.
- O1: DOC012 names an entry whose `pytest -q` and bold count are not
  directly paired, since the authority skips it. The pattern is shared
  as `logic.FULL_SUITE_RESULT_RE`. The pairing is bounded at 80
  characters so prose citing another entry's count is not a claim.
  `AGENTS.md` now states the one readable form and both plans point there.

Deviation: two lines of the shared CLI fixture in
`tests/test_docsync_cli.py` wrote the colon form, which the authority read
only through its legacy fallback; they now use the canonical form. No
other existing test changed. 44 archived entries use an unpaired form;
DOC012 reads only live entries, so they are left as written.

Live probe (throwaway corpus from HEAD plus the changed modules):

| Probe | Expected | Observed |
| --- | --- | --- |
| opened batch, no entries: block | Batch 23, WP-0 next | Batch 23, WP-0 next |
| opened batch, Section 3 claims WP-3 | DOC007 | exit 1, DOC007 |
| opened batch, dashboard claims WP-3 | DOC007 | exit 1, DOC007 |
| `pytest -q` (qualifier) -- bold count | DOC012 | exit 1, DOC012 |
| `pytest -q`: bold count | DOC012 | exit 1, DOC012 |
| opened batch, true "WP-0 is next" | green | exit 0 |
| real corpus between batches | green, count shown | exit 0, count shown |
| targeted `pytest -q tests/...` run | no DOC012 | no DOC012 |
| prose citing another entry's count | no DOC012 | no DOC012 |
| canonical form | no DOC012 | no DOC012 |

The original 18 planted-defect probes were re-run on the changed code:
18 of 18 red.

Validation: `pytest -q` -- **1729 passed**, 12 of them new; the untracked
mutation-runner tests were excluded, since they are not repository state.

### 2026-09-21 - Batch 23 WP-0 foundation plan committed

Side task, no batch tag. Scope: commit
`docs/superpowers/plans/2026-09-21-batch23-wp0-foundation.md`, which
replaces an earlier draft that put 22 tasks and two behaviour changes under
WP-0. WP-0 keeps its definition's scope: the loop-protocol plan plus the
three original extractions. Control-plane fixes run as side tasks, led by
the fix for audit defect D1, which must land before the batch opens.
F-SWE-5 follows WP-0 as its own commit. Every change to a check is
accepted only on a live probe: red on the planted defect, green on its
near miss.

Owner rulings, 2026-09-21, recorded in the plan: Batch 23's branch is
`feat/batch23-wp0-hygiene`, opened by the plan's Task 3b after the D1 fix;
no worker-count guard (delegated, declined: the Dockerfile pins one worker
and a partial guard is its own wrong green); WP-0 counts as "next" under a
finite plan; job admission is folded into Batch 23 WP-4. Section 3 is
deliberately unchanged here: opening the batch before the D1 fix would
produce the defect's state.

Validation: `pytest -q` -- **1717 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-21 - Docsync live-probe audit recorded

Side task, no batch tag. Scope: record the formal conclusion of the live
probe run earlier today as
`docs/history/reports/DOCSYNC_LIVE_PROBE_AUDIT_2026-09-21.md`. No code
changed.

Verdict: conditionally fit. All 21 implemented codes fired on their own
planted defect (26 of 26 red probes), all 8 near-miss controls stayed
green, and `--fix`, the exit codes and the preflight behaved as documented.
Blocking defect D1: a batch declared open with no logged work package reads
as "between batches" and DOC007 is silent on a false next-package claim; it
must be fixed before Batch 23 opens. D2: WP-0 is never "next" under a finite
plan; the owner ruled that it counts. The report states what was not probed.

Validation: `pytest -q` -- **1717 passed**; the untracked mutation-runner
tests were excluded, since they are not repository state.

### 2026-09-21 - Worker loop-protocol plan committed; docsync probed live

Side task, no batch tag. Scope: commit the plan of record for Batch 23
WP-0's loop-protocol extraction,
`docs/superpowers/plans/2026-09-21-worker-run-coroutine-wrapper.md`, and
verify the docsync gate by live probe rather than by its unit tests.

The plan was checked against source before committing and four statements
were corrected: `tests/test_worker.py` has nine existing tests, not four;
its in-function imports make six failures, not six errors; the untracked
set is larger than the eight paths it named; and its commit blocks now run
`--fix` before pytest and pre-commit, as "Commit Rules" orders. Its code,
tests and parity argument are unchanged. The expanded WP-0 foundation plan
was rewritten in the working tree and is deliberately not in this commit.

Live probe: a throwaway corpus built from `git archive HEAD` plus a scratch
`git init`, with one planted defect per code, run through the real CLI.
Every implemented code (DOC001-DOC020, DOC023) went red on its own defect
and raised only that code; six near misses (struck-through or fenced
retired claims, a fenced missing path, `Status: not closed.`, a canonical
resolved finding, a valid citation) stayed green. `--fix` repaired a
tampered managed block and rotated a resolved finding, and refused to write
a rotting finding's record or a hand-authored count. The preflight returned
3 on a staged `scripts/docsync/` edit, 0 on an ordinary one, and passed the
checker's 1 through.

One defect found: in a batch Section 3 declares active but with no tagged
Section 4 entry yet, the status block renders "none (between batches)" and
DOC007 is silent on a false next-work-package claim. Both are correct once
one entry exists. That is the state Batch 23 enters when its branch is
named, so the fix is scheduled to land first; it is not yet filed in
`FINDINGS.md`.

Validation: `pytest -q` -- **1717 passed**, across 66 tracked test modules;
the untracked mutation-runner tests were excluded, since they are not
repository state. The dashboard and the findings header are updated from
1555 across 58 to match.

### 2026-09-21 - Frontend gate split complete (F-B21-51)

Side task, no batch tag. Task 11 closes out the split: `frontend_gate.py`
measures 535 lines, under the plan's 700-line threshold and above its
roughly-450 estimate. The ten `_frontend_gate_*` siblings measure
`_frontend_gate_assets` 49, `_frontend_gate_colour` 191,
`_frontend_gate_forms` 434, `_frontend_gate_layout` 1,176,
`_frontend_gate_pipeline` 854, `_frontend_gate_results` 497,
`_frontend_gate_runtime` 156, `_frontend_gate_shared` 71,
`_frontend_gate_theme` 749, `_frontend_gate_unmatched` 490. The gate
summary is unchanged: `[frontend_gate] 30 checks passed in 52 runs across
chromium, firefox`. F-B21-51 is resolved; `docs/architecture/
documentation-tooling.md`, `DEVELOPMENT.md`, `FINDINGS.md` and this file
are reconciled to the measured end state. The `frontend_gate_checks.toml`
registry stays a deferred candidate.

### 2026-09-21 - Frontend gate split: runtime slice (F-B21-51)

Side task, no batch tag, last of the split. `_frontend_gate_runtime.py` now
owns `SETUP_COMMAND`, `install_cdn_routes`, `_SERVE_APP_LOCK`,
`FrontendGateError`, `_load_playwright`, `_launch_browser` and `serve_app`,
moved verbatim with the `app`, `werkzeug.serving` and
`scrobblescope.repositories` imports they need. The facade no longer imports
`create_app`, `make_server` or the repository job functions directly; it
re-exports the six public names through the new sibling instead.
`REPO_ROOT`, the `sys.path` insert, `GATE_SECRET_KEY` and the environment
bootstrap stay in the facade, above every sibling import, because
`scrobblescope.config` reads the provider keys once at first import and the
gate boots in CI's production mode with no secrets set. The facade's
bootstrap comment now says so explicitly.

Seven tests moved out of `test_frontend_gate.py` into
`test_frontend_gate_runtime.py`, retargeting their `make_server` and
`create_app` patches to `_frontend_gate_runtime`, and their
`frontend_gate.install_cdn_routes` attribute calls to
`_frontend_gate_runtime.install_cdn_routes`. `test_headed_reaches_the_browser_launch`,
`test_launch_is_headless_by_default` and the tests that call `main(` or
`run_checks(` stayed in `test_frontend_gate.py`, unchanged, because they
reach `_launch_browser` and `serve_app` through the facade's re-export or
`patch.object(frontend_gate, ...)`, which still resolves.

Removing the facade's `create_job`/`delete_job` import broke two tests in
`test_frontend_gate_pipeline.py` (an earlier slice) that called
`frontend_gate.create_job`/`frontend_gate.delete_job` by attribute access --
a name the facade no longer defines. `_frontend_gate_pipeline` already
imports both from `scrobblescope.repositories` for its own checks, so those
four call sites were retargeted to `_frontend_gate_pipeline.create_job`/
`_frontend_gate_pipeline.delete_job` rather than restoring the facade
import.

### 2026-09-21 - Frontend gate split: pipeline slice (F-B21-51)

Side task, no batch tag. `_frontend_gate_pipeline.py` now owns the three
checks that write real job state through `scrobblescope.repositories` and
watch the page follow it -- `check_loading_composition`,
`check_pipeline_state_machines`, `check_artist_spotlight_rotation` -- plus
their nine helpers (`_parse_matrix_scalex`, `_assert_loading_progress_state`,
`_exercise_loading_progress_phases`, `_check_phase_repository_isolation`,
`_exercise_counted_progress`, `_exercise_album_progress`,
`_exercise_heatmap_progress`, `_exercise_replaced_job_progress`,
`_exercise_pipeline_state_machines`) and the ten progress constants
(`ALBUM_PROGRESS_TRACK`, `ALBUM_PROGRESS_BAR`, `ALBUM_PROGRESS_TEXT`,
`HEATMAP_PROGRESS_TRACK`, `HEATMAP_PROGRESS_BAR`, `HEATMAP_PROGRESS_TEXT`,
`FETCHING_SCROBBLES`, `COUNTING_SCROBBLES`, `PAGE_23_OF_102`,
`PAGE_90_OF_100`), moved verbatim. `serve_app` stays behind in the facade, so
the facade keeps `create_job`, `delete_job` and `set_job_progress`; the other
six repository imports (`get_job_context`, `get_job_progress`,
`reset_job_state`, `set_job_error`, `set_job_results`, `set_job_stat`) moved
with the code that reads them.

Six tests moved out of `test_frontend_gate.py`, retargeting their patches of
`reset_job_state`, `set_job_progress`, `create_job`, `delete_job`,
`get_job_progress` and `get_job_context`, and of
`_exercise_pipeline_state_machines`, to `_frontend_gate_pipeline`. Two moved
tests also called `_check_phase_repository_isolation`,
`_exercise_replaced_job_progress`, `_exercise_counted_progress` and
`get_job_progress` through `frontend_gate.<name>` attribute access -- names
the facade no longer defines -- and were retargeted the same way.
`serve_app`'s own tests kept patching `frontend_gate.create_job`,
`frontend_gate.set_job_progress` and `frontend_gate.delete_job`, since those
three still resolve there.

### 2026-09-21 - Frontend gate split: layout slice (F-B21-51)

Side task, no batch tag. `_frontend_gate_layout.py` now owns the six checks
that measure fonts, text scaling, touch targets and large-display
composition -- `check_touch_targets`, `check_fonts`, `check_body_font`,
`check_shell_scales_with_text`, `check_large_display_scale_parity`,
`check_destination_empty_states` -- plus their eighteen measurement and
judgement helpers and the `FONTS_READY_EXPRESSION`, `REQUIRED_FONT_FAMILIES`,
`MIN_TOUCH_TARGET_PX`, `INTERACTIVE_SELECTOR`, `TOUCH_TARGET_STATES` and
`DEFAULT_STATES` constants, moved verbatim and importing `_clamp_px` from the
colour slice and the page inventories and `_reach_state` from the shared
module. It is the largest slice at roughly 1,150 lines; the split isolates it
rather than shrinking it, and `check_large_display_scale_parity`'s own
complexity is a separate question. The definitions were not contiguous in the
facade: `check_loading_composition` stayed behind between
`check_shell_scales_with_text` and the scale-parity measurement helpers.

Sixteen tests and the `_healthy_mobile_header` helper moved out of
`test_frontend_gate.py`. Several of the moved tests called private helpers
through `frontend_gate._mobile_header_failures`, `frontend_gate.
_expected_scaled_dimension`, `frontend_gate._scale_dimension_failures`,
`frontend_gate._wide_layout_failures`, `frontend_gate._header_geometry_failures`,
`frontend_gate._scale_mechanism_failures`, `frontend_gate._measure_enlarged_root`
and `frontend_gate._composition_bounds_failures` -- private names the facade
never re-exports, so those references were retargeted to
`_frontend_gate_layout` alongside the patch-target guard's own findings.
`test_the_touch_profiles_really_carry_a_coarse_pointer` stayed in
`test_frontend_gate.py`: it tests `VIEWPORTS`, which remains in the facade.

### 2026-09-21 - Frontend gate split: theme slice (F-B21-51)

Side task, no batch tag. `_frontend_gate_theme.py` now owns the nine checks
that read computed theme values -- `check_divider_contrast`,
`check_theme_tokens`, `check_index_design_tokens`, `check_theme_persistence`,
`check_index_entrance_motion`, `check_mark_follows_theme`,
`check_theme_survives_blocked_storage`, `check_heatmap_zero_cells_follow_theme`,
`check_heatmap_export_header_matches_page` -- plus their private helper
`_computed_colour`, the `_BLOCK_STORAGE` init script, and the
`THEME_EXPRESSION`, `SET_THEME_EXPRESSION` and `FORBIDDEN_SURFACES`
constants, moved verbatim and importing the divider-contrast helpers from
the colour slice and the page inventories from the shared module. The
definitions were not contiguous in the facade; `check_touch_targets`,
`_small_targets`, `check_fonts`, `check_body_font`,
`check_shell_scales_with_text` and `check_loading_composition` stayed behind
between them.

This is the first slice to move existing tests rather than write new ones
against moved code alone: `test_blocked_storage_probe_closes_context_when_page_creation_fails`
and `test_theme_persistence_check_restores_the_saved_preference` moved out of
`test_frontend_gate.py`. The persistence test's `MIGRATED_PAGES` patch is an
instance of trap 2 (constraints.md): it targeted
`scripts.dev.frontend_gate.MIGRATED_PAGES`, which rebinds the facade's name,
not the theme module's own `from ... import MIGRATED_PAGES` binding that
`check_theme_persistence` actually reads. Pointing the patch back at the
facade to check whether the retarget is load-bearing showed the test still
passes: the mocked page is not path-aware, so the check silently runs
against the real `MIGRATED_PAGES` tuple instead of `("/",)` and reports no
failures either way. The retarget to `scripts.dev._frontend_gate_theme.MIGRATED_PAGES`
is still correct -- it is what makes the test actually exercise a single
page the way its docstring describes -- but it is not what makes the test
fail if omitted; the patch-target guard is what would have caught the
mis-target here, not this test's own assertions.

A mutation probe returning `["mutation probe"]` first in
`check_mark_follows_theme` produced the expected
`FAIL chromium: mark follows theme [desktop]: mutation probe` and the
matching `[firefox]` line, because that check is in the static-assets
canary group that runs on both browsers, then was reverted. The gate's
summary line is unchanged at 30 checks across both browsers.

### 2026-09-21 - Frontend gate split: forms slice (F-B21-51)

Side task, no batch tag. `_frontend_gate_forms.py` now owns the index form's
seven checks -- `check_validation_feedback`, `check_private_profile_is_blocked`,
`check_validator_outage_is_recoverable`, `check_stale_validator_failure_is_discarded`,
`check_current_validator_failure_replaces_old_verdict`,
`check_true_warning_survives`, `check_initial_visibility` -- plus their
private helpers `_collecting_handler` and `_year_warning`, and the
`HIDDEN_ON_LOAD` constant, moved verbatim and importing `_reach_state` from
the shared module. The definitions were not contiguous in the facade;
`check_index_entrance_motion`, `check_mark_follows_theme` and
`check_theme_survives_blocked_storage` stayed behind between them.
`_collecting_handler` gains the regression test its docstring describes: a
one-parameter handler so Playwright cannot overwrite its sink with the
request object, and that two handlers do not share one. A mutation probe
that added `"#year"` to `HIDDEN_ON_LOAD`'s `"/"` tuple produced the expected
`FAIL chromium: initial visibility [desktop]: /: #year should start hidden
but computes display: block` line (and the matching `[mobile]` line), then
was reverted. The gate's summary line is unchanged at 30 checks across both
browsers.

### 2026-09-21 - Frontend gate split: unmatched slice (F-B21-51)

Side task, no batch tag. `_frontend_gate_unmatched.py` now owns the largest
single check, `check_unmatched_report` (422 lines), its breakpoint sweep
`_unmatched_panel_width_sweep`, and their constants
(`UNMATCHED_TWO_PANEL_MIN`, `UNMATCHED_SWEEP_WIDTHS`,
`UNMATCHED_MIN_TITLE_WIDTH`), moved verbatim and importing
`add_job_unmatched`, `create_job` and `delete_job` from
`scrobblescope.repositories`. The sweep gains its first unit tests: that it
reports a wrong column count and a starved album title at each swept width,
and that it restores the viewport through its `finally` block both on a
normal return and when a page measurement raises. A mutation probe that
widened `UNMATCHED_MIN_TITLE_WIDTH` to 960 produced the expected FAIL lines
on chromium at all three profiles. The gate's summary line is unchanged at
30 checks across both browsers.

### 2026-09-21 - Frontend gate split: assets slice (F-B21-51)

Side task, no batch tag. `_frontend_gate_assets.py` now owns stylesheet
isolation: `BOOTSTRAP_MARKER`, `TAILWIND_MARKER`, `_stylesheet_hrefs` and
`check_stylesheet_isolation`, moved verbatim and importing `ALL_PAGES` from
the shared module. This is the first browser-coupled slice, so it sets the
pattern the rest of the split follows: move verbatim, re-export through the
facade, and prove the gate still reaches the moved code. A mutation probe in
`check_stylesheet_isolation` produced the expected FAIL on both chromium and
firefox, confirming the Firefox canary group also reaches the moved module.
The gate's summary line is unchanged at 30 checks across both browsers.

### 2026-09-21 - Frontend gate split: shared slice (F-B21-51)

Side task, no batch tag. `_frontend_gate_shared.py` now owns the page
inventories (`MIGRATED_PAGES`, `LEGACY_PAGES`, `ALL_PAGES`,
`ERROR_PAGE_PATH`), `GATE_JOB_IDS` and `_reach_state`, moved verbatim so every
later slice can import them without importing the facade that imports them.
`serve_app` still lives in the facade but now mutates the shared module's
`MIGRATED_PAGES`, `ALL_PAGES` and `GATE_JOB_IDS` in place through a `from ...
import` binding, never rebinding them; a new parity test pins that every
module holding one of those names holds the same object. A mutation probe in
`_reach_state` produced the expected FAIL on both the touch-target and
form-validation checks, confirming both reach the shared code through the
facade's re-export.

### 2026-09-21 - Frontend gate: dead code removed before the split (F-B21-51)

Side task, no batch tag. `_computed_shadow` had no caller anywhere and is
deleted rather than moved. The cdnjs Bootstrap fixture is removed: no template
requests Bootstrap, and the isolation check reads hrefs, so it still catches a
regression; `install_cdn_routes` keeps only the Impeccable Live overlay abort.
Eight colour tests moved verbatim into the colour test file.

### 2026-09-21 - Frontend gate split: invariants pinned first (F-B21-51)

Side task, no batch tag, owner-approved 2026-09-21. F-B21-51 is rescoped from
a batch work package to a side task with a written plan, and amended: a shared
module is added and the TOML registry is deferred. Before any code moves,
`tests/scripts/dev/test_frontend_gate_split.py` pins three invariants that
would otherwise fail silently: every defined check is registered, every test
patch targets a module that reads the name, and the facade's environment
bootstrap precedes any `scrobblescope` import. Each guard was shown to fail on
a deliberate defect before being kept.

### 2026-09-21 - No `assert` guards runtime code any more (F-B22-2)

Side task, no batch tag. Preparation for closing PR #235's review threads,
which the owner named as the next step: two of its Codacy threads (HIGH
RISK) are this finding, and the honest reply is the fix, not a pointer.
Control-plane change (`scripts/docsync/findings.py`), committed with
`SKIP=doc-state-sync-check` and `doc_state_sync.py --check` run directly.

**Plan vs implementation.** The finding's fix shape was a conditional raise
at each of six sites. Applied as written, three of those raises could never
fire, so each invariant was placed where it actually holds instead:

- **`routes/album_flow.py`, three `assert job_context is not None`:
  deleted.** `_get_validated_job_context` returns an error before it can
  return a missing context, so they only narrowed types. Three copies of an
  unreachable raise is dead code, and Rule 3 says the third copy is where
  the invariant belongs in one place -- which it already is.
- **`scripts/docsync/findings.py` `_build`: invariant by construction.**
  `_parse` already has each heading's match; it now passes it in instead of
  `_build` re-matching `block[0]` and asserting.
- **`spotify.py` token fetch: a behaviour change, deliberately.** Missing or
  empty credentials now log and return None, which is the function's
  existing failure answer, so the album pipeline falls back to Deezer and
  the spotlight keeps its artwork. The `assert` raised past that fallback
  and failed the whole job; an empty string also slipped past `is not None`.
  The old test expected `AssertionError`; it is replaced by three cases
  (id missing, secret missing, id empty) asserting None, no HTTP call and
  an error log. Red before the change.

**The gate.** Ruff `S101` is selected, with `tests/**` exempt (all 2,630
current hits are there). Proven red on a probe file. Production code now
holds zero `assert` statements, and the affected suites pass under
`python -O`.

**Validation:** `pytest -q` -- **1555 passed**. `pre-commit run --all-files`
with `SKIP=doc-state-sync-check` -- every other hook passes.
`doc_state_sync.py --check` run directly -- exit 0.

**Forward guidance:** PR #235's threads can now be answered with fixes for
every true claim. The fixes live on this branch, so they reach `main` in the
follow-up PR the owner plans after #235 merges.

### 2026-09-21 - DOC023 reads a legacy "Status: closed" as a claim

Side task, no batch tag, owner-approved on 2026-09-21 with one condition:
it must not start flagging findings that merely mention a closed batch, work
package or PR. Control-plane change, committed with the documented escape
`SKIP=doc-state-sync-check` and `doc_state_sync.py --check` run by hand on
the final tree.

**Why.** F-B21-13's prose said "Status: closed." for four weeks while the
finding sat active. DOC023 recognises only `resolved` and `no action`, the
rotation vocabulary, so the word the author actually used was invisible to
it. That is the one real pattern miss the morning's findings pass found.

**Plan vs implementation.** Measured before designing: matching "closed" on
any body line fired on two findings, one of them F-B21-25, whose status is
"partly closed" -- a false positive even on the status line. So the rule is
narrow: `_LEGACY_CLOSED_STATUS_RE` in `scripts/docsync/findings.py` matches a
capitalised `Status` label (plain, bold, or after a sentence ends) whose value
*opens* with "closed". Rotation vocabulary is unchanged: "closed" is a way to
detect the claim, not an outcome a record may state, so the remedy is still a
`resolved` record. `docs/architecture/documentation-tooling.md` records the
rule beside DOC023.

**Tests.** Ten in `tests/test_docsync_findings.py`. Four claim shapes, red
before the pattern existed. Six non-claims, which pass before and after:
"partly closed", "not closed", "closes at", and "closed" in ordinary prose
about a batch, a work package and a PR. On the live corpus the check stays
clean: F-B21-25 is not flagged.

**Validation:** `pytest -q` -- **1553 passed**. `pre-commit run --all-files`
with `SKIP=doc-state-sync-check` -- every other hook passes.
`doc_state_sync.py --check` run directly -- exit 0.

**Forward guidance:** other pre-lifecycle spellings ("fixed", "done") were
measured and left out: on status lines they appeared only qualified ("the
scope itself is fixed", "closes at WP-8"). Add one only with a measured
instance, the same way.

### 2026-09-21 - Broad catches judged one by one, then gated (F-MAS-4)

Side task, no batch tag, owner-approved on 2026-09-21 because the count only
grows: F-MAS-4 recorded 14, then 17; it was 25.

**Plan vs implementation.** The finding offered "narrow or add structured
logging". Narrowing all 25 was rejected after reading them: most guard the
optional DB cache or decorative enrichment, where fail-open is the
documented design (`docs/agents/global-rules.md` Rule 6), and swapping
`Exception` for guessed asyncpg or aiohttp types would turn a failure the job
tolerates today into a crashed job. So each site was judged, and the growth
was made impossible to miss instead:

- **Narrowed (1):** `lastfm.py`'s JSON guard, to `aiohttp.ContentTypeError`
  and `ValueError`. It wrapped the cache write too and labelled *every*
  failure "Invalid JSON". Anything else now reaches `retry_with_semaphore`,
  which retries it exactly as before. Tests first: two pin the parse
  failures that must stay handled, and one red test showed a non-parse
  error being misreported.
- **Logged with a traceback (12):** eleven already re-raised or called
  `logging.exception`; `run_async_in_thread` hand-built the same output with
  `traceback.format_exc()` and now calls `logging.exception`.
- **Justified (12):** the DB-cache, correction-cache, close-in-finally and
  optional-enrichment catches each carry a one-line reason above the
  `except` and `# noqa: BLE001`. The three degradation warnings and the
  retry helper now log the exception's class, which they omitted, so a
  programming error cannot pass for a network blip.
- **The gate:** Ruff's `BLE` rules are on in `pyproject.toml`. A handler
  catching bare `Exception` must re-raise, log a traceback, or say why.
  Proven red with a probe file. The five hits outside `scrobblescope/`
  (`init_db.py`, two scripts, two thread-collecting tests) are deliberate
  report-everything boundaries and carry reasons too.

**Deviation: one stale docstring.** `run_async_in_thread` said it was "used
only by `/validate_user`"; it also serves both start routes' Last.fm checks
and `/api/artist_spotlight`. Corrected while the function was open.

**Validation:** `pytest -q` -- **1543 passed**. `pre-commit run --all-files` --
all hooks pass, including the new rule. `doc_state_sync.py --check` exit 0.

**Forward guidance:** a new broad catch now needs a reason in the diff, which
is where a reviewer can disagree with it. `docs/SWE_AUDIT_CHARTER.md` notes
that F-MAS-4 counted catches without judging them; this pass judged them.
