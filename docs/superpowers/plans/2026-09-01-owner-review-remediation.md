# Owner Review Remediation Implementation Plan

> **Historical plan -- superseded; do not execute.** Tracked on 2026-09-04
> to preserve the original owner-review intent. The canonical execution plan is
> [Batch 21 index scaling and review remediation](2026-09-01-batch21-index-scaling-and-review-remediation.md),
> subject to the owner's later rulings and the active `BATCH21_DEFINITION.md`.
> Its "Owner decisions governing Task 2 and Task 3" and Task 4 record the
> accepted scale/header and accurate-count requirements. `PLAYBOOK.md` owns
> execution status; `AGENTS.md` owns repository rules.
>
> The original text below is historical evidence, including its former claim
> to be canonical. Its zoom examples, new-worktree instructions, panel-sized
> browser profiles, and unresolved header decision are superseded. Its loading
> intent survives through the active plan, with accurate polling required and
> separate album/heatmap pipeline lifecycles. Unchecked boxes below describe
> the old proposal, not today's work status.

## Original proposal (historical text)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the owner-review features that PR #220 did not fully ship: a viewport-proportional, usable wide index composition with legible structural boundaries, phase-accurate loading progress, and a first-class unmatched no-data page.

**Architecture:** Treat the current `origin/main` tree as the baseline. The work is three independently reviewable changes: first diagnose and implement Firefox-proven viewport-proportional desktop scaling while applying the intended 3:4 index split, wider form cap, shared landing-brand scale, and stronger semantic boundaries; then make the server own structured progress phases and make both loading clients render the same displayed fraction; finally give the Unmatched route the same borderless empty-state system as Results and Heatmap. The existing browser-session latest-job contract remains in place throughout.

**Tech Stack:** Flask, Python 3.13, Jinja2, in-memory job repository, vanilla browser JavaScript, Tailwind v4 generated CSS, pytest, Playwright frontend gate.

**Spec:** `BATCH21_DEFINITION.md` WP-4 and the owner-approved PR #220 Owner-Review Refinement Plan supplied on 2026-09-01. This remediation must deliver viewport-proportional scaling from 1080p through 4K rather than fixed sizing. The current source formula is not evidence that the behavior has shipped: owner Firefox captures show that the composition does not visibly scale. Update the live definition and reconciliation records to distinguish source intent from rendered behavior; leave dated log archives as historical records.

## Implementation status and owner decision ledger

This is the single comprehensive source for the owner-review remediation. The
active Batch 21 records describe present source behavior and link here for
pending work; they must not present any item below as already shipped.

- **Source attempt, not accepted behavior:** `static/js/index.js` sets
  `--index-wide-scale` and `static/css/index.css` consumes it through `zoom`.
  Chromium measurements show that path growing; the owner's Firefox captures
  show the intended hero/form composition is not visibly scaling. Treat
  proportional scaling as unimplemented until Firefox at 1080p and 1440p
  proves the complete composition grows as specified.
- **Pending implementation:** Firefox-proven viewport scaling, the `3fr 4fr`
  wide split, `28rem` form cap, shared landing-brand multiplier, wide-profile
  headline no-wrap guard, measured divider contrast, structured progress
  phases, and unmatched empty state.
- **Decision checkpoint before implementation:** render the 1440p header
  density and height at the 1920x1080 profile with the wider form and its
  expanded controls. Adopt that density globally only if the comparison keeps
  the task path clear and improves footer space; otherwise retain the current
  shell geometry. In either outcome, the shell must remain independent of the
  index composition zoom.
- **Deferred pending a later owner review:** slider-only nested-card controls
  and any form expansion beyond `28rem`.

## Global Constraints

- Start from a new worktree at the current `origin/main` tree. Do not reset, force-push, or reuse the diverged `wip/batch-21` branch as an execution target.
- Preserve the untracked Impeccable files in `impeccable-init` (`.impeccable/`, `PRODUCT.md`, and `graphify-out/`). Do not stage or delete them.
- Do not create a linked-worktree virtual environment. Use the qualified primary-checkout Python, pytest, and pre-commit executables printed by `scripts/dev/check_worktree_alignment.py`.
- At viewport widths of 1200px and above, use a `3fr 4fr` index split and a `28rem` form cap. First identify why the existing `--index-wide-scale`/`zoom` path is not producing the owner-observed Firefox result. Then implement a browser-safe mechanism that makes hero, wordmark, form, type, and controls grow together by the intended factor from 1080p through the 4K cap; larger displays provide both proportionate components and more usable placement.
- Use one modest landing-scale multiplier (initial target: `1.05`) for the desktop hero wordmark and H1. It composes with `--index-wide-scale`, preserving their measured relationship rather than enlarging the wordmark in isolation. At 1920px-wide viewports and above, the H1 must remain one visible line without clipping; normal wrapping remains available below that wide profile.
- On Home, place the `ALBUM FILTERING` eyebrow directly below the H1, matching
  the established Heatmap-result hierarchy. Do not change the copy, wordmark
  position, or navigation placement as part of that hierarchy correction.
- Treat the current 1440p header navigation density and height as a candidate, not a shipped global target. Compare it at 1920x1080 alongside the widened, expanded form before deciding whether it earns global adoption. In either outcome, the header must not inherit the index composition zoom; its page pills and theme control remain readable, reachable, and on one row at the supported desktop profiles.
- At desktop heights of 900px or less, reduce only the form column's outer vertical padding to `2rem`. Do not shrink text, controls, or touch targets. Preserve existing tablet and mobile behavior.
- Keep the existing 12px small-label floor, `0.04em` phrase-mark tracking, and `#6c6676` light muted token. They already exist on `main`; test and document them rather than replacing them with parallel values.
- Strengthen the semantic divider tokens in both light and dark themes. The shell's lower border and the desktop form-well divider must provide at least 3:1 non-text contrast against each adjacent surface; keep duplicated shell and Tailwind tokens synchronized. Do not use shadows to manufacture this separation.
- `/progress` remains backward compatible: top-level `progress` is still the overall 0-100 completion signal. Add `phase` only when a structured phase exists.
- A counted phase uses `{key, label, unit, current, total}`. The visible hairline and `aria-valuenow` equal `current / total * 100` exactly. An uncounted phase explicitly clears `phase`; an omitted `phase` argument leaves its prior value unchanged.
- Keep the pinwheel, one slim hairline, Home return behavior, no Loading navigation pill, reduced-motion completion state, cached result routes, and approved dark theme.
- Treat the suggested slider-only treatment for nested cards, and any expansion beyond the planned `28rem` form cap, as a visual-review checkpoint. Do not implement either without a fresh owner decision after the 1080p and 1440p comparison.
- The plan does not add cancellation, broad anti-pattern cleanup, a new design system, or WP-5 leaderboard work.
- Each implementation commit updates the relevant live Batch 21 record first, then runs `doc_state_sync.py --fix`, tests, pre-commit, and `doc_state_sync.py --check`. Stage exact paths only. Do not push, open a PR, or merge without a new explicit owner instruction.

---

## Baseline and file map

| Area | Current source | Required outcome |
| --- | --- | --- |
| Desktop index layout | `static/css/index.css`, `static/js/index.js` | Replace the current `3fr 5fr` and `23.75rem` form cap with `3fr 4fr` and `28rem`; diagnose and replace or repair the unproven viewport-scaling path so Firefox renders the intended `1.075` to `2.15` composition. |
| Wide visual gate | `scripts/dev/frontend_gate.py`, owner Firefox comparison | Add 1920x1080, 2560x1440, and 3840x2160 index measurements. Prove the 3:4 split, the shared proportional scale in Firefox as well as Chromium, and the 900px-height reachability rule. |
| Landing hierarchy and shell boundaries | `templates/index.html`, `static/css/index.css`, `static/css/shell.css`, `static/css/tailwind.src.css` | Apply one shared landing-brand multiplier, place the Home eyebrow under the H1, keep the wide-profile H1 unwrapped, evaluate the 1440p header density at 1080p before adopting it, and raise light/dark divider contrast without changing the approved card hierarchy. |
| Job progress contract | `scrobblescope/repositories.py`, `scrobblescope/routes.py` | Add an optional copied `phase` payload without changing existing top-level callers. |
| Album and Heatmap workers | `scrobblescope/orchestrator.py`, `scrobblescope/heatmap.py` | Supply page counts for Last.fm and search/detail counts for album Spotify work; clear phase for uncounted work. |
| Loading rendering | `static/js/loading.js`, `static/js/heatmap.js`, `templates/loading.html`, `templates/index.html` | Use one small shared browser helper for phase formatting, phase-local fractions, accessibility values, and opacity-only entrance motion. |
| Unmatched no-data route | `scrobblescope/routes.py`, `templates/unmatched_empty.html` (new), `templates/unmatched.html` | Route absent or expired album jobs to a borderless empty state without changing valid unmatched reports. |
| Existing empty component | `templates/results_empty.html`, `templates/heatmap_empty.html`, `static/css/empty.css` | Reuse it unchanged for the new unmatched empty page. |
| Live documentation | `BATCH21_DEFINITION.md`, `FINDINGS.md`, `docs/design/RECONCILIATION.md`, `PLAYBOOK.md`, `.claude/SESSION_CONTEXT.md` | Replace current claims that conflict with this owner-approved remediation. Do not edit `docs/logarchive/` history. |

## Execution setup

- [ ] **Step 1: Create a clean execution worktree after owner authorization**

Run the worktree guard from the primary checkout, record the qualified tool paths it prints, and confirm `origin/main` is the base. Create a new branch such as `codex/owner-review-remediation` from `origin/main`; do not alter `wip/batch-21` or its untracked annotation files.

```powershell
& "C:\Users\peter\Python Projects\ScrobbleScope\.venv\Scripts\python.exe" scripts\dev\check_worktree_alignment.py
git fetch --prune origin
git worktree add -b codex/owner-review-remediation <new-worktree-path> origin/main
```

- [ ] **Step 2: Establish a measured baseline before edits**

Run the frontend gate and capture the computed dimensions of `.index-hero__mark`, `.index-hero__headline`, `.index-form__inner`, the form card, a field, the submit button, one header navigation pill, and the theme control at 1920x1080, 2560x1440, and 3840x2160. Record the mark-to-H1 and field-to-submit ratios, plus the expected scale factors. At 1920x1080, repeat the measurement with the 1440p header-density candidate and the decade selector plus thresholds expanded; record footer space, one-row navigation, and action reachability as an explicit owner decision comparison. Record the baseline measurements in the first commit's PLAYBOOK entry so proportional-growth and header-density regressions are reproducible.

```powershell
& "<qualified-python>" scripts\dev\frontend_gate.py
```

Expected baseline: the current `3fr 5fr` and `23.75rem` cap demonstrate why the source does not meet this plan. The source declares a dynamic `--index-wide-scale`, but the owner Firefox evidence shows that the complete visual result has not shipped; do not preserve the implementation mechanism by assumption.

## Task 1: Restore and calibrate the viewport-proportional wide index composition

**Files:**
- Modify: `static/css/index.css:122-130, 230-234`
- Modify after diagnosis: `static/js/index.js:1-20` and/or the browser-safe replacement
- Modify: `static/css/shell.css:15-23, 34-41, 50-64, 133-175, 425-476`
- Modify: `static/css/tailwind.src.css` and regenerate `static/css/tailwind.css`
- Modify: `scripts/dev/frontend_gate.py` viewport matrix and index-layout checks
- Modify: `tests/test_template_shell.py`
- Modify: `BATCH21_DEFINITION.md`, `FINDINGS.md`, `docs/design/RECONCILIATION.md`, `PLAYBOOK.md`, `.claude/SESSION_CONTEXT.md`

**Interfaces:**
- Consumes: the existing desktop breakpoint (`min-width: 1200px`), mobile breakpoint (`859.98px`), the present `--index-wide-scale` attempt, the owner Firefox captures, and the current compiled Tailwind token values.
- Produces: a Firefox-proven responsive desktop composition: `grid-template-columns: 3fr 4fr`, `max-width: 28rem`, a shared landing-brand multiplier for the wordmark/H1 pair, and one browser-safe shared scale mechanism for the two composition wrappers at every desktop display profile.

- [ ] **Step 1: Reproduce the Firefox scaling failure and write the rendered-layout checks**

Before choosing a fix, reproduce the owner's Firefox comparison at 1920x1080 and 2560x1440 with the same browser zoom and device-pixel-ratio conditions recorded in the owner pass. Capture computed scale values, element rectangles, root font size, CSS `zoom` support, and the effective stylesheet asset identities. Compare that evidence with the existing Chromium gate; do not infer Firefox behavior from computed CSS alone.

Add three desktop profiles to the gate: `1920x1080`, `2560x1440`, and `3840x2160`. Add `check_index_proportional_wide_composition` to measure the same visible elements in every available engine. Derive `expected_scale` from the approved formula and assert all of the following:

```python
assert abs(metrics["grid_right"] / metrics["grid_left"] - (4 / 3)) < 0.02
assert abs(metrics["form_inner_width"] - (28 * 16 * expected_scale)) < 2
assert abs(metrics["wordmark_width"] / baseline["wordmark_width"] - scale_ratio) < 0.02
assert abs(metrics["field_height"] / baseline["field_height"] - scale_ratio) < 0.02
assert abs(metrics["submit_height"] / baseline["submit_height"] - scale_ratio) < 0.02
assert abs(metrics["field_height"] / metrics["submit_height"] - baseline["field_submit_ratio"]) < 0.02
assert abs(metrics["wordmark_to_h1"] - baseline["wordmark_to_h1"]) < 0.02
assert metrics["headline_line_count"] == 1
assert metrics["nav_link_height"] == selected_shell["nav_link_height"]
assert metrics["theme_toggle_height"] == selected_shell["theme_toggle_height"]
```

Use the 1920x1080 measurement as `baseline`. For each profile, calculate `expected_scale = min(2.15, 1.075 * max(1, min(width / 1920, height / 1080)))` and `scale_ratio = expected_scale / baseline_scale`; compare 2560x1440 and 3840x2160 to the baseline through that ratio. Assert that the header navigation and theme-control measurements do not inherit that factor. If the automated runner cannot launch the owner's Firefox, keep the same measurements as an owner Firefox acceptance gate and do not mark scaling complete from Chromium alone. Before setting `selected_shell`, render the 1440p density candidate at 1920x1080 with the wider, expanded form and record the owner's accept/reject decision plus the selected dimensions. Measure the dark and light shell/form divider colors against their adjacent surfaces and require 3:1 non-text contrast. Drive the decade selector and open the thresholds disclosure at `1920x900`; assert the submit button's bottom edge is at or above the viewport bottom without document scrolling at default zoom. Add a mobile assertion that `#index-grid` remains one column below `860px` and that coarse-pointer targets keep their existing 44px minimum.

- [ ] **Step 2: Run the new check and confirm current source fails**

Run:

```powershell
& "<qualified-python>" scripts\dev\frontend_gate.py
```

Expected: the current check exposes the 5:3 ratio and `23.75rem` form cap. The Firefox comparison must also fail until the hero, form, and their descendants visibly follow the scale ratio; a Chromium-only pass is insufficient.

- [ ] **Step 3: Implement one Firefox-safe proportional-scale mechanism**

Do not pick a CSS or JavaScript mechanism until Step 1 identifies the failure boundary. Replace or repair the current `--index-wide-scale`/`zoom` implementation with one browser-safe, layout-aware mechanism that grows the entire hero and form composition together in Firefox and Chromium. Do not use a visual-only transform that leaves layout boxes, focus geometry, scroll reachability, or hit targets at the old size. Then change the wide split, form cap, shared landing-brand scale, and Home eyebrow order. Apply the landing multiplier to the wordmark and H1 from one semantic declaration; do not give them separate hand-tuned desktop sizes. In `templates/index.html`, move `ALBUM FILTERING` to directly after the H1 without changing its text. At `min-width: 1920px`, prevent a headline newline only when the full text remains visible. In `static/css/shell.css` and the Tailwind source, change only the semantic border tokens needed to meet the measured boundary contrast in both themes; regenerate the compiled sheet through the repository's existing frontend build.

```css
@media (min-width: 1200px) {
  .index-grid {
    grid-template-columns: 3fr 4fr;
  }

  .index-hero__inner,
  .index-form__inner {
    zoom: var(--index-wide-scale, 1.075);
  }
}

.index-form__inner {
  width: 100%;
  max-width: 28rem;
  margin: 0 auto;
}

@media (min-width: 1200px) and (max-height: 900px) {
  .index-form {
    padding-block: 2rem;
  }
}
```

Keep the existing `@media (max-width: 859.98px)` rule that removes the form cap on mobile. Do not change the 12px label token, the already-correct `0.04em` marks, or `#6c6676` in either Tailwind source path; retain and exercise their existing checks. Preserve productive editorial whitespace rather than filling it with extra content. The planned wider form and 3:4 split are the only approved density change; re-evaluate residual large-screen space during the owner visual pass before expanding any card further.

- [ ] **Step 4: Reconcile the live design records**

Update the active text only. In `BATCH21_DEFINITION.md`, replace the source-intent 3:5/`23.75rem` description with the Firefox-proven 3:4/`28rem` result, shared landing-brand scale, selected header density, and browser-safe proportional mechanism. In `FINDINGS.md`, retain the evidence that owner Firefox rendering made scaling an open defect until verified. In `docs/design/RECONCILIATION.md`, change the wide-index override table to the rendered rule, including semantic divider contrast. Do not change `docs/logarchive/` entries: they are dated records of what was believed and implemented at that time.

Add a dated `PLAYBOOK.md` Section 4 entry describing the source mismatch, fixed result, exact display profiles, and targeted validation. Update `.claude/SESSION_CONTEXT.md` Section 1 only with current project facts affected by this task.

- [ ] **Step 5: Run focused checks and commit the complete task**

Run:

```powershell
& "<qualified-python>" -m pytest tests/test_template_shell.py -q
& "<qualified-python>" scripts/dev/frontend_gate.py
& "<qualified-python>" scripts/doc_state_sync.py --fix
& "<qualified-python>" -m pytest -q
& "<qualified-pre-commit>" run --all-files
& "<qualified-python>" scripts/doc_state_sync.py --check
git diff --check
```

Stage only the files listed for this task plus regenerated managed documentation, inspect `git diff --cached`, then commit:

```powershell
git add static/css/index.css static/css/shell.css static/css/tailwind.src.css static/css/tailwind.css scripts/dev/frontend_gate.py tests/test_template_shell.py BATCH21_DEFINITION.md FINDINGS.md docs/design/RECONCILIATION.md PLAYBOOK.md .claude/SESSION_CONTEXT.md docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md
git commit -m "refactor(ui): widen and calibrate the index layout"
```

Stop for owner review. Do not push this commit yet.

## Task 2: Align visible loading progress with pipeline phases

**Files:**
- Modify: `scrobblescope/repositories.py:12-18, 56-91, 157-166`
- Modify: `scrobblescope/routes.py:313-344`
- Modify: `scrobblescope/orchestrator.py` Last.fm, Spotify search, Spotify detail, uncounted, and terminal progress calls
- Modify: `scrobblescope/heatmap.py:114-217`
- Create: `static/js/loading-progress.js`
- Modify: `static/js/loading.js`, `static/js/heatmap.js`
- Modify: `templates/loading.html`, `templates/index.html`
- Modify: `static/css/loading.css`, `static/css/heatmap.css`
- Modify: `tests/test_repositories.py`, `tests/test_routes.py`, `tests/services/test_orchestrator_fetch_and_process.py`, `tests/services/test_orchestrator_fetch_spotify.py`, `tests/test_heatmap.py`, `scripts/dev/frontend_gate.py`
- Modify: `BATCH21_DEFINITION.md`, `PLAYBOOK.md`, `.claude/SESSION_CONTEXT.md`

**Interfaces:**
- Consumes: `set_job_progress(job_id, progress=None, message=None, ...)`, `GET /progress?job_id=...`, and the two independent loading clients.
- Produces: `GET /progress` may include this additive field:

```json
{
  "progress": 20,
  "message": "Fetching scrobbles",
  "phase": {
    "key": "lastfm_fetch",
    "label": "Fetching scrobbles",
    "unit": "page",
    "current": 23,
    "total": 102
  }
}
```

- [ ] **Step 1: Write failing repository and route contract tests**

Add tests that prove `phase` is copied, not aliased, and has three distinct update modes:

```python
phase = {"key": "lastfm_fetch", "label": "Fetching scrobbles", "unit": "page", "current": 23, "total": 102}
set_job_progress(job_id, progress=20, message="Fetching scrobbles", phase=phase)
phase["current"] = 99
assert get_job_progress(job_id)["phase"]["current"] == 23

set_job_progress(job_id, message="Still fetching")
assert get_job_progress(job_id)["phase"]["key"] == "lastfm_fetch"

set_job_progress(job_id, phase=None)
assert "phase" not in get_job_progress(job_id)
```

Add a `/progress` test that asserts the exact JSON phase payload survives the route, and that existing no-job and error responses remain compatible without a `phase` requirement.

- [ ] **Step 2: Run the contract tests and confirm they fail**

Run:

```powershell
& "<qualified-python>" -m pytest tests/test_repositories.py tests/test_routes.py -q
```

Expected: `set_job_progress()` rejects the unknown `phase` keyword and `/progress` has no structured phase field.

- [ ] **Step 3: Add additive repository support with an explicit sentinel**

Add a private sentinel next to `_initial_progress` so omitted and explicit `None` do different things:

```python
_UNSET = object()

def set_job_progress(..., phase=_UNSET):
    ...
    if phase is not _UNSET:
        if phase is None:
            job["progress"].pop("phase", None)
        else:
            job["progress"]["phase"] = dict(phase)
```

In `get_job_progress`, copy `progress["phase"]` when present, just as `stats` is copied. Do not put `phase: null` into every payload: absent phase keeps current clients and error responses unchanged.

- [ ] **Step 4: Populate only counted worker phases and clear uncounted phases**

Make these calls use the exact phase keys and units:

```python
# Both Last.fm callbacks
phase={
    "key": "lastfm_fetch",
    "label": "Fetching scrobbles",
    "unit": "page",
    "current": pages_done,
    "total": total_pages,
}

# Album Spotify search callback
phase={
    "key": "spotify_search",
    "label": "Searching Spotify",
    "unit": "album",
    "current": searches_done,
    "total": total_searches,
}

# Album Spotify detail-batch callback
phase={
    "key": "spotify_details",
    "label": "Fetching Spotify details",
    "unit": "batch",
    "current": batches_done,
    "total": num_batches,
}
```

When the workers move to initialization, aggregation, filtering, result assembly, error, or completion, pass `phase=None` explicitly. A plain message-only update must not accidentally clear the phase. Keep the top-level percent mappings unchanged for completion and existing redirect logic.

Extend the existing service tests to assert the exact phase dictionaries for Last.fm `(23, 102)`, Spotify search, and Spotify detail paths. Keep their state-side-effect assertions; do not replace them with mock-call-only checks.

- [ ] **Step 5: Create one browser helper and move both clients onto it**

Create `static/js/loading-progress.js` as a small non-module global, loaded before `loading.js` and `heatmap.js`:

```js
window.ScrobbleProgress = {
  displayPercent(payload) {
    const phase = payload.phase;
    if (Number.isFinite(phase?.current) && Number.isFinite(phase?.total) && phase.total > 0) {
      return Math.max(0, Math.min(100, (phase.current / phase.total) * 100));
    }
    return Math.max(0, Math.min(100, Number(payload.progress) || 0));
  },
  label(payload) {
    const phase = payload.phase;
    if (!phase) return payload.message || "Initializing...";
    const prefix = phase.label.toUpperCase();
    return Number.isFinite(phase.current) && Number.isFinite(phase.total)
      ? `${prefix} \u00b7 ${phase.unit.toUpperCase()} ${phase.current} / ${phase.total}`
      : prefix;
  },
};
```

Add one helper that takes `{track, bar, phaseText, payload, previousPhaseKey}`. If the phase key changes, remove the CSS transition, set `scaleX(0)`, and restore the transition on the second `requestAnimationFrame` before applying the new phase-local fraction. This makes the reset instant rather than visibly animating backward. For every update, set `transform: scaleX(displayPercent / 100)`, `aria-valuenow` to the same rounded displayed percentage, and `aria-valuetext` to `label(payload)`.

Both clients call this shared helper. Do not use `width`, `height`, `padding`, `margin`, or `max-width` transitions. Keep the current top-level percent fallback when no counted phase is present.

- [ ] **Step 6: Add one opacity-only loading entrance and reduced-motion behavior**

Apply the same short entrance animation to the shared loading composition in both `loading.css` and `heatmap.css`: pinwheel, track, phase line, and visible stats start and finish through opacity only. The final state must be visible in `@media (prefers-reduced-motion: reduce)`. Keep existing heatmap cached-result opacity handoff and album loading behavior; do not add a heading, navigation pill, cancellation, or a second percentage.

- [ ] **Step 7: Add real-browser progress checks**

Extend `frontend_gate.py` with a fixture job that returns at least these sequential payloads to each loading client:

```python
{"progress": 20, "phase": {"key": "lastfm_fetch", "label": "Fetching scrobbles", "unit": "page", "current": 23, "total": 102}}
{"progress": 90, "phase": {"key": "lastfm_fetch", "label": "Fetching scrobbles", "unit": "page", "current": 90, "total": 100}}
{"progress": 92, "message": "Counting daily scrobbles"}
```

For the counted frames, assert the bar's computed transform matrix and `aria-valuenow` correspond to `23 / 102` and `90 / 100`, and that `aria-valuetext` contains the exact phase label and fraction. For the uncounted frame, assert the bar falls back to top-level 92 and the phase text no longer presents a stale page count. Run equivalent checks against album `/loading` and Heatmap's in-page loader. Add a reduced-motion check that the shared composition is visible without waiting for an entrance animation.

- [ ] **Step 8: Update live documentation, validate, and commit**

Update the active WP-4 text in `BATCH21_DEFINITION.md` so the current owner decision is unambiguous: counted phases display their count in the phase line and drive the hairline; uncounted work clears phase and uses overall progress. Correct any live statement that says `/heatmap_data` is polled as progress; the client polls `/progress` and requests heatmap data only after completion. Add a dated PLAYBOOK entry and update the dashboard if changed module relationships or test counts require it.

Run:

```powershell
& "<qualified-python>" -m pytest tests/test_repositories.py tests/test_routes.py tests/services/test_orchestrator_fetch_and_process.py tests/services/test_orchestrator_fetch_spotify.py tests/test_heatmap.py -q
& "<qualified-python>" scripts/dev/frontend_gate.py
rg -n 'transition:\s*(width|height|padding|margin|max-width)' static\css static\js
& "<qualified-python>" scripts/doc_state_sync.py --fix
& "<qualified-python>" -m pytest -q
& "<qualified-pre-commit>" run --all-files
& "<qualified-python>" scripts/doc_state_sync.py --check
git diff --check
```

The transition grep must return no production animation of the prohibited layout properties. Stage only the explicit Task 2 files and generated managed documentation, then commit:

```powershell
git commit -m "fix(progress): align loading signals with pipeline phases"
```

Stop for owner review. Do not push this commit yet.

## Task 3: Add the unmatched no-data surface

**Files:**
- Modify: `scrobblescope/routes.py`
- Create: `templates/unmatched_empty.html`
- Modify: `tests/test_routes.py`
- Modify: `scripts/dev/frontend_gate.py`
- Modify: `PLAYBOOK.md`, `.claude/SESSION_CONTEXT.md`

**Interfaces:**
- Consumes: the existing latest album job resolver, `GET /unmatched`, and the shared `.empty-page` / `.empty-state` styles.
- Produces: `GET /unmatched` with no resumable album job or an expired session pointer renders `unmatched_empty.html`; populated unmatched data continues to render `unmatched.html` unchanged.

- [ ] **Step 1: Write failing route tests for absent and expired album jobs**

Replace the current generic-error assertions with exact unmatched-empty assertions:

```python
response = client.get("/unmatched")
assert response.status_code == 200
assert b'data-empty-state="unmatched"' in response.data
assert b"No unmatched albums yet" in response.data
assert b'href="/"' in response.data
assert b"Search albums" in response.data
assert b"error-code" not in response.data
assert b"card shadow" not in response.data
```

Create an expired `latest_album_job_id` in the client session, request `/unmatched`, and assert the pointer is removed and the same template is returned. Keep the existing populated-unmatched route test and zero-row valid-job test; they prove the report route and its semantics did not change.

- [ ] **Step 2: Run the focused tests and confirm current behavior fails**

Run:

```powershell
& "<qualified-python>" -m pytest tests/test_routes.py -q
```

Expected: no-job Unmatched currently renders `error.html` and the valid zero-row route renders its Bootstrap report template.

- [ ] **Step 3: Create the dedicated template and route to it**

Create `templates/unmatched_empty.html` by following `results_empty.html`, loading only `tailwind.css` and `empty.css`:

```html
<main class="empty-page" data-empty-state="unmatched">
  <section class="empty-state" aria-labelledby="unmatched-empty-title">
    <span class="empty-state__signal" aria-hidden="true"></span>
    <h1 id="unmatched-empty-title">No unmatched albums yet</h1>
    <p>Run an album search to find albums that need a review.</p>
    <a class="empty-state__action" href="/">Search albums</a>
  </section>
</main>
```

In the no-valid-album-job and expired-pointer branch of `unmatched_page`, render this template instead of calling the generic `_render_no_job_state`. Keep `unmatched.html` for valid album jobs, including a valid run with zero unmatched rows. Do not add an outline, shadow, icon, error status, Bootstrap dependency, or a duplicate unmatched stylesheet to the new template.

- [ ] **Step 4: Extend the browser gate and run focused checks**

Add `/unmatched` to the empty-state visual checks. Assert that the page has no `.card`, no box shadow on `.empty-state`, a usable Home action, and that the action target is `/`. Re-run the populated route checks to confirm report navigation still returns to `/results`.

Run:

```powershell
& "<qualified-python>" -m pytest tests/test_routes.py -q
& "<qualified-python>" scripts/dev/frontend_gate.py
```

- [ ] **Step 5: Document, validate, and commit**

Add a dated PLAYBOOK entry that explains this is a normal no-data condition, not an error treatment, and that valid unmatched reports remain unchanged. Update `.claude/SESSION_CONTEXT.md` only if its page inventory or validation count changes.

Run:

```powershell
& "<qualified-python>" scripts/doc_state_sync.py --fix
& "<qualified-python>" -m pytest -q
& "<qualified-pre-commit>" run --all-files
& "<qualified-python>" scripts/doc_state_sync.py --check
git diff --check
```

Stage only the Task 3 paths and generated managed documentation, inspect the staged diff, then commit:

```powershell
git commit -m "refactor(ui): unify the unmatched empty state"
```

Stop for owner review. Do not push this commit yet.

## Final acceptance and handoff

- [ ] **Step 1: Perform source and test sweep**

Read every changed file in full. Search the live documentation for stale claims about `3fr 5fr`, `23.75rem`, fixed desktop scale, a form that fills its well, the old phase-count prohibition, and the old unmatched generic-error route. Keep hits in dated archives as historical evidence; correct every active affirmative claim. Retain correct references to the `2.15` scale cap, the header's independent density, and the pending nested-card decision.

```powershell
rg -n -i '3fr 5fr|23\.75rem|fixed.*desktop.*scale|fills its well|does not repeat.*page count|Start from Home' BATCH21_DEFINITION.md FINDINGS.md PLAYBOOK.md .claude\SESSION_CONTEXT.md docs\design
```

- [ ] **Step 2: Run all automated gates from the new worktree**

```powershell
& "<qualified-python>" -m pytest -q
& "<qualified-python>" scripts/dev/frontend_gate.py
& "<qualified-pre-commit>" run --all-files
& "<qualified-python>" scripts/doc_state_sync.py --check
git diff --check
git status --short
```

Expected: all commands pass, the frontend gate covers desktop 1080p, 1440p, 4K, mobile, wide-touch, compact desktop height, both loading clients, and the unmatched empty state. Status shows only intentional task files; no Impeccable annotation files are staged.

- [ ] **Step 3: Obtain owner visual acceptance before any integration action**

In Firefox at 1920x1080 and 2560x1440, verify:

1. Wordmark, H1, type, controls, and form grow together from 1080p through 1440p and 4K according to the approved scale formula; the wordmark/H1 relationship remains constant, neither headline wraps or clips at the 1920px-wide desktop profiles, and the application column gains usable placement.
2. The documented 1920x1080 comparison decides whether the 1440p header-density candidate is adopted. The selected header keeps its page pills and theme control on one readable row, remains independent of the index zoom, and leaves the wider expanded form's action and footer space productive. The header bottom rule, desktop form-well divider, cards, and fields remain legible in both themes without shadows.
3. With decade selection and thresholds open at 1920x900, the submit action and filter tags stay reachable without document scrolling at default zoom.
4. The album and Heatmap loaders show a single pinwheel, one hairline matching `23 / 102` and `90 / 100`, correct accessibility values, no backward animation at a phase switch, and reduced-motion final visibility.
5. Home mode switching remains a short, interruptible fade; cached navigation, fresh Home Heatmap mode, Results, Heatmap, and valid Unmatched routes keep their current semantics.
6. `/unmatched` before a search and after an expired album pointer uses the borderless no-data page; a real unmatched report still renders its reason groups.
7. Treat any post-change desire to widen the nested card beyond `28rem` or turn its controls into sliders as a new reviewed decision, not a silent refinement.

- [ ] **Step 4: Request explicit integration authorization**

Only after the owner accepts the Firefox pass, ask whether to push the three commits and open a new PR from the new branch. PR #220 is already merged and must not be reopened, rebased, force-pushed, or treated as an active review target. Rebase-merge any new PR only after an explicit owner instruction; stop before worktree cleanup or WT004 realignment unless separately authorized.

## Plan self-review

- **Spec coverage:** Task 1 covers proportional cross-monitor scale, proportional landing hierarchy, form width, stable header density, light/dark divider contrast, 900px height, label/tracking verification, mobile preservation, and live document reconciliation. Task 2 covers the additive `/progress` phase contract, worker phase data, exact hairline math, accessibility, motion, Heatmap retrieval behavior, and both client paths. Task 3 covers a dedicated unmatched empty template without altering valid reports. Final acceptance covers automated and owner-run Firefox gates.
- **Intentional exclusions:** No change is proposed for current navigation grouping, the wordmark asset or copy, the approved dark-mode palette beyond divider contrast, server-side cancellation, WP-5, or archive history. The nested-card slider proposal and any form expansion beyond `28rem` remain owner-review decisions.
- **Consistency checks:** `phase` is the same name in repository state, `/progress`, both workers, both JavaScript clients, the gate, and tests. The display percentage is phase-local only when `current` and `total` are both finite and positive; otherwise it is the existing top-level percentage.
