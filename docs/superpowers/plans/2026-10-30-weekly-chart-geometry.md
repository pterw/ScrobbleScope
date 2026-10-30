# Weekly Chart Geometry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. The owner requested one final review after the definition of done; per-commit/task reviews are omitted by that explicit instruction.

**Goal:** Make production drawing, hit selection and composition tests use one weekly chart geometry calculation without changing the chart.

**Architecture:** Follow the approved [geometry design](../specs/2026-10-30-weekly-chart-geometry-design.md). Keep the pure module in `static/js/heatmap.js`; retain DOM rendering and appearance outside its seam.

**Tech Stack:** Existing browser JavaScript, SVG, Python pytest and the repository Playwright gate. Use the primary checkout's qualified environment; install no dependency.

## Global Constraints

- The design document owns the interface, compatibility requirements and owner exceptions. Read it before this task brief; do not broaden those exceptions.
- `AGENTS.md` and `docs/agents/global-rules.md` bind this work. Preserve unrelated owner files and use explicit staging paths.
- Keep the existing payload validation policy, chart behavior, image export and per-week keyboard rows.
- Baseline source is `c1ca5f18`, whose source tree equals `742425eb`, the reviewed snapshot. The branch is `refactor/weekly-chart-geometry` in `C:/ssw/weekly-chart-geometry`.
- The source worktree's unrelated untracked mutation tests are not part of this branch. Measure the suite here; do not adopt their extra count.
- Each task's commit includes its PLAYBOOK state/log and measured docsync update. All hooks and final docsync must pass; WT003 alone is owner-authorized advisory.
- Production/test interface names are `streamGeometry`, `xs`, `haloPath`, `artists`, artist fields `rank` and `path`, and `hitAt` returning `week` and `hoverId`.

## Delivery sequence

- [x] Commit this approved design and plan with a dated side-task record.
- [x] Task 1: protect the production geometry before extraction.
- [ ] Task 2: deepen the calculation and migrate its consumers/tests.
- [ ] Meet the definition of done, run one independent whole-branch review,
      address findings, then create the PR from the repository template.

## Task 1: Protect the existing geometry

**Ownership:** The implementation worker owns only
`scripts/dev/_frontend_gate_stream.py` and
`tests/frontend/test_heatmap_pure_functions.py`. The controller owns plan,
PLAYBOOK, dashboard and validation records. Do not edit runtime JS yet.

**Interfaces:** Consume the existing renderer and guarded mathematical
hooks. Produce stronger checks against the unchanged runtime, without new
test modules or a second composition implementation.

- [x] Extend `test_week_from_x_clamps_and_picks_the_nearest_week` in its
      current test function, adding the exact midpoint to its input/output
      arrays:

  ```python
  xs = [-500, 39, 46, 47, 48, 62.9, 63.1, 39 + 16 * 52, 5000]
  assert got == [0, 0, 0, 1, 1, 1, 2, 52, 52]
  ```

- [x] Extend the existing rendered alignment check with a deterministic
      53-week spike payload and actual path bounding boxes. Use ten artist
      arrays with zero weeks, sharp changes and a large residual spike:

  ```python
  counts = [0] * 53
  counts[25] = 800
  residual = [0] * 53
  residual[27] = 9000
  ```

  Give the other artists distinct shifted nonzero spikes using the same
  shape, keeping the payload valid. Reuse `_seed_job` and `_open_heatmap`.
  Read SVG path extents and the plot's gridline y bounds from the actual
  DOM. Check nonempty paths fit within those bounds, allowing serialization
  rounding. Restore viewport and delete seeded jobs in `finally`. Avoid
  repeating the full viewport matrix for every spike fixture.

- [x] Prove the new containment check detects a deliberately out-of-band
      path in a temporary browser probe; do not retain a runtime mutation.
- [x] Run the focused pure suite and affected browser alignment check in
      Chromium and Firefox. The unchanged production implementation must
      pass before Task 2 moves its calculation.
- [x] Give the controller a report with exact commands/results and any
      coverage concerns. The controller runs the full suite, updates the
      side-task log/docsync, stages named paths and runs all hooks before
      committing `test(heatmap): Protect weekly chart geometry`.

## Task 2: Make the calculation the shared test surface

**Ownership:** A fresh implementation worker owns `static/js/heatmap.js`
and `tests/frontend/test_heatmap_pure_functions.py`. The controller owns
documentation, integration validation and commits. The Task 1 gate changes
must remain intact.

**Interfaces:** Consume the approved design's existing payload. Produce
its exact `streamGeometry` model; use it in drawing, pointer selection and
the composition test.

- [ ] Add the pure `streamGeometry` function beside the geometry helpers.
      Preserve arithmetic, rounding and path command order while moving
      the connected calculation out of `drawStream`:

  ```js
  function streamGeometry(payload) {
    // Move current order/baseline/fit/stack/path calculation verbatim.
    // Keep numeric bands, rank map and centre private to the hit method.
    // Return null at the existing nonpositive-fit exit.
    return { xs: xs, haloPath: haloPath, artists: artistPaths, hitAt: hitAt };
  }
  ```

  `hitAt` converts viewBox y to the current upward-positive band coordinate,
  calls the existing nearest-week and band-selection helpers and returns
  the specified target. Document valid-input, null and coordinate behavior
  in the function's docstring. No options bag or adapter is needed.

- [ ] Replace the calculation inside `drawStream` with one call. The
      renderer creates the same SVG nodes from returned path strings and
      artist ranks. Keep theme, halo visibility, labels and events there.
- [ ] Store the geometry model in stream state. Change pointer selection
      to the model's hit method after the existing browser-to-viewBox
      conversion. Update stream-state consumers of week centres/counts;
      derive initial keyboard identities from the model's artist order.
      Keep week-specific panel row selection unchanged.
- [ ] Expose the new function only through the existing guarded test hook.
      Remove hooks that become unused, while retaining independent
      mathematical tests with distinct regression protection.
- [ ] Replace the reconstruction in
      `test_smoothed_stream_encloses_artists_without_clipping` with the
      geometry model. Read `haloPath` and artist paths from it. Update
      `_stream_path_samples` to track the current point through M/L/C
      commands and pair forward/reverse cubic segments, so endpoint L
      extensions do not invalidate sampling.
- [ ] Extend existing intended-behavior tests to exercise returned artist
      ranks and paths, no-play/residual-only and one-week cases,
      nonmutation, midpoint/clamped weeks and upper-band/zero-band hit
      behavior. Use hand-derived expectations and independent geometric
      assertions. Replace superseded cases instead of adding a parallel
      suite or pinning module layout/constants/wording.
- [ ] Run the focused suite and affected browser checks. Compare the old
      runtime served via browser asset interception with the new runtime
      using the same seeded jobs: artist order/ranks, exact path strings,
      columns and representative hover targets must agree. Keep this
      comparison in the plan workspace, not as a second permanent runtime.
- [ ] Give the controller exact commands/results. The controller runs the
      full suite and full frontend gate, updates docs and measured docsync,
      stages named paths and runs hooks before committing
      `refactor(heatmap): Own weekly chart geometry`.

## Final review and PR

- [ ] Read every changed file whole and sweep the cumulative branch diff
      for sibling stale claims, unused geometry hooks and every asserted
      case. Preserve dated historical entries.
- [ ] Run one independent whole-branch standards/spec review, with the
      design, full cumulative diff and verification reports. Fix material
      findings and recheck affected behavior.
- [ ] Confirm full-suite count, complete frontend gate, all hooks and final
      docsync on the final source. Record any actual limitation.
- [ ] Push this side-task branch and open a PR against `main` using
      `.github/PULL_REQUEST_TEMPLATE.md`. Keep gate checkboxes truthful and
      include task commits and review state. No attribution footer or merge.

## Execution record

- 2026-10-30: Owner approved design, bounded Rule 3 exception, clean worktree
  and WT003 advisory. Owner requested review once the definition of done
  is met, replacing per-commit/task reviewer dispatches.
- 2026-10-30: Three independent read-only design assessments converged on
  the in-file geometry model. Existing source and mathematical/browser
  coverage were inspected before any structural edit.
- 2026-10-30: The tracked-source baseline measured **3113 passed** in 214.73
  seconds, excluding the original checkout's unrelated untracked mutation
  test file. The new worktree begins at the identical source tree and
  does not contain that owner file.
- 2026-10-30: The clean-worktree documentation baseline measured
  **3113 passed** in 198.05 seconds. Baseline hooks passed with only the
  owner-authorized advisory WT003; final documentation sync and hooks run
  before the planning commit.
- 2026-10-30: Task 1 focused checks passed: 147 pure-harness tests and the
  complete affected alignment check in Chromium and Firefox. Both engines
  reject a deliberately out-of-band live halo; restoration passes. The
  full suite measured **3113 passed** in 210.85 seconds. Runtime calculation
  remains unchanged. Final hooks and docsync run before the test commit.
