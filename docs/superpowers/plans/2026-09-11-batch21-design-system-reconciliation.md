# Implementation Plan

**Scope of this document:** make the repository, its plans and its design
records agree with `docs/design/designsystemaudit.md`, in the audit's own
revised remediation order. Derived 2026-09-11 from branch `test` at `3f59380`.

**Source read order used:** `AGENTS.md` (full), `docs/design/designsystemaudit.md`
(sequentially, all 1048 lines, twice, including every truncated span),
`PLAYBOOK.md` Sections 2-4, `BATCH21_DEFINITION.md`, `.claude/SESSION_CONTEXT.md`
Sections 1-4, `docs/AGENT_DOC_MAP.md`, `docs/design/README.md` (snapshot),
`docs/design/RECONCILIATION.md`, `DESIGN.md`, `tests/test_design_snapshot.py`,
`.docsync.toml`, `FINDINGS.md` (F-B21-4, -5, -19, -21..-24), both 2026-09-11
WP-7 documents, and the live `static/js` and `static/css` sources each audit
claim names.

---

## Progress -- where this plan stands, and where to pick it up

**Owner of this status: this section. Do not restate it in [Implementation
Order]; update it here.** Last updated 2026-09-11 by the session that drafted
the plan and executed Phase 1.

**State: Phase 1 complete and committed. Phases 2-5 not started. No work is
uncommitted: the architecture-diagram rebuild landed as `cc987f5`, the F-B21-51
slice-1 refactor as `95e0896`, and this plan's own move as `c277728`.**
Nothing is pushed.

| Phase | State | Evidence |
| --- | --- | --- |
| 0 Baseline | **Done** | guard exit 0; `pytest -q` 990 at open, 1020 now; docsync exit 0 |
| 1 WP-7 refinement | **Done, committed** | `57d1474`; frontend gate 26 checks in 47 runs, chromium + firefox |
| 2 Document reconciliation | **Not started** | the two live conflicts are listed below |
| 3 Audit incidental defects | **Not started** | 5 items, all still present in the code |
| 4 WP-8 core | **Not started** | includes the `heatmap.js` observer trap |
| 5 WP-8 close-out | **Not started** | needs the mandated frontend/a11y audit |

### Commits landed during this plan

| Commit | Subject |
| --- | --- |
| `72615ed` | `feat(unmatched): Align report with Results and cap album fetch` -- the prior session's work, committed as a checkpoint |
| `c2f14fa` | `chore(agents): Record the issue tracker and domain docs for agent skills` |
| `57d1474` | `fix(ui): Refine the unmatched report disclosure` -- this plan's Phase 1 |

### Uncommitted work at handoff, in the order it should be committed

1. **Staged, all four gates observed green on it:** the F-B21-51 slice-1 gate
   refactor. `scripts/dev/_frontend_gate_colour.py`,
   `tests/scripts/dev/test_frontend_gate_colour.py`, `scripts/dev/frontend_gate.py`,
   `FINDINGS.md`, `PLAYBOOK.md`, `.claude/SESSION_CONTEXT.md`, and the rotated
   archive. 480 insertions, 140 deletions.
2. **Unstaged:** the architecture-diagram rebuild -- `docs/ARCHITECTURE.md` and
   the five owners under `docs/architecture/`. Its PLAYBOOK entry is already
   written but sits unstaged, so `PLAYBOOK.md` reads `MM`; re-stage it with the
   diagrams.
3. **Unstaged:** this plan's move into `docs/superpowers/plans/` and the
   progress section you are reading.

### Where to pick up

1. Commit the staged set. Its PLAYBOOK entry and every gate result are recorded.
   **Discharged 2026-09-11 as `95e0896`.** Its documentation half had already
   landed in `c277728`, because docsync's count checks force those files into
   any commit that adds a log entry claiming a test count.
2. Commit the diagram rebuild, re-staging `PLAYBOOK.md`. **Discharged 2026-09-11
   as `cc987f5`.** The rebuilt `docs/architecture/documentation-tooling.md` also
   carried a stale docsync range, corrected in the same commit.
3. Commit this plan's move. **Discharged 2026-09-11 as `c277728`.** The fate of
   `docs/superpowers/plans/gemini_implementation_plan_unverified.md` is still
   open: it remains untracked, superseded, and in the directory.
4. Start **Phase 2** with the conflict that actively misleads: the approved spec
   `docs/superpowers/specs/2026-09-11-unmatched-threshold-horizontal-report-design.md`
   still says "stacked, full-width reason sections" while the owner ruled
   side-by-side and the shipped page is side-by-side. `PLAYBOOK.md` Section 3
   already carries the correction, so the spec is the last stale voice.

### What Phase 1 actually did, and how it diverged from the plan

Four deviations, recorded because the plan above still reads as written and a
future executor should not treat it as a faithful record of what happened:

1. **The layout was not rebuilt.** The plan's Phase 1 step 5 said to restructure
   the report into stacked full-width sections. The owner's 2026-09-11 ruling is
   side-by-side, the shipped page is side-by-side, and three frontend-gate
   assertions defend it. Phase 1 therefore refined the existing layout instead.
   The plan text was corrected the same day, and this note records why.
2. **Three refinements arrived from skills, not from the plan.** The `daisyui`
   skill's colour rule 10 moved the panel count off `primary` to `base-content`;
   its usage rules 2 and 7 justified Results' scale-aware panel padding; and the
   `frontend-design` pass justified letting the reason detail wrap in the
   narrower side-by-side column.
3. **The step size was chosen, not specified.** The owner allowed "20 or 25".
   The plan uses 25 and records it as a decision, not an oversight.
4. **A pre-existing data-integrity defect was found and fixed in passing.**
   `static/css/tailwind.css` carried a stale `.collapse` utility no source
   produces; the rebuild dropped it. It entered with `72615ed`, not with Phase 1.

### Open owner decisions carried into the handoff

1. Whether `docs/superpowers/plans/gemini_implementation_plan_unverified.md`
   should be deleted or kept.
2. The unmatched expander step (20 vs 25) -- 25 is live.
3. Whether Results' serif figure face is restated in `DESIGN.md` or the Role
   Segregation Rule narrows. Phase 2 must pick one.
4. Whether the theme gains a third "System" state (F-B21-22).
5. The F-B21-20 staging-order contract.

---

## [Overview]

Bring the repository into agreement with the shipped design system the audit
derives, and bring the repository's own documents into agreement with each
other and with the audit, without editing the byte-frozen `docs/design/`
snapshot.

The audit is self-correcting: four later sections supersede earlier claims
(the D-17 mischaracterisation, D-25 understating the breakpoint count, D-26's
tooltip retraction, the `.dark-mode` "dead" claim reversed, D-34 voided by the
completed migration). This plan follows the **final** state -- the
"Reframing", "The four unread JS files" and "Revised remediation order"
sections -- not the first-pass register.

Four facts shape the whole plan:

1. **`docs/design/` is a byte-frozen snapshot.** `tests/test_design_snapshot.py`
   pins a 61-file digest and exempts only `RECONCILIATION.md` and
   `designsystemaudit.md`. The audit's D-1..D-34 remediation targets the
   external Claude Design project and **cannot land here**; the corrected facts
   must land in the repository-owned `DESIGN.md` and
   `docs/design/RECONCILIATION.md`, which is also what the audit's step 4 says.
2. **The audit's repo-side list is already WP-8's shape.** The audit says so
   itself ("WP-8 can start today"). WP-8's premise ("once no Bootstrap page is
   left") is now satisfied: all eight page templates override `legacy_css` with
   an empty block, so nothing loads Bootstrap or `global.css`.
3. **One audit instruction is a trap, and one is mechanically wrong.** The
   trap: retiring `global.css` and the `.dark-mode` write together silently
   breaks the heatmap's zero-count cells, because `heatmap.js`
   `initDarkModeObserver()` observes `document.body` for `class` and nothing
   else watches a theme toggle. The mechanically wrong one: F-B21-23's
   `stroke: var(--bars-color)` cannot be a presentation attribute, because the
   audit's own section 4 proves an SVG presentation attribute does not resolve
   a custom property. Both are handled explicitly below.
4. **The unmatched-report layout is the owner's ruling, not the spec's.** The
   approved spec `2026-09-11-unmatched-threshold-horizontal-report-design.md`
   says "stacked, full-width reason sections". The owner overruled that in
   favour of side-by-side reason panels ("They should not be stacked, but
   side-by-side"), and both the shipped `templates/unmatched.html` and the
   frontend gate implement side-by-side. Phase 1 therefore **refines** that
   layout and must not rebuild it; Phase 2 records the override so the spec and
   `PLAYBOOK.md` Section 3 stop contradicting it.

Ordering chosen by the owner: **WP-7 refinement first, then document
reconciliation, then the audit-derived code defects and WP-8.** WP-7's
remaining UI work is uncommitted in this worktree and must be finished and
validated before any audit work starts, so the tree the audit items land on is
the tree owner review has already seen.

Two measured corrections to the audit were found during this investigation and
are carried into the plan:

| Audit states | Measured 2026-09-11 | Consequence |
| --- | --- | --- |
| `--index-scale` has 102 consumers | **111** `var(--index-scale` occurrences in `static/css/index.css` alone | Do not publish a count. Re-measure across every sheet before quoting one, or describe the mechanism without a number (Anti-Pattern Registry item 10). |
| `--results-scale` has 58 consumers | **58** in `static/css/results.css`, plus **20** `results-scale` occurrences in `templates/results.html` | Quote as "58 in `results.css` plus arbitrary Tailwind values in `results.html`", which is what the audit's prose already says. |
| Incidental defect 3, `--shell-accent-ink`, "stands and is genuinely live" | Its **only** consumers are `static/css/global.css:164,171,178,192`, a file no page loads | The value is not live. Resolve it by deletion with `global.css`, not by re-pointing it. Verify with a repo-wide grep before editing. |

## [Types]

No new or changed Python type definitions. Task 1 of the WP-7 extension already
landed its contract at `3f59380`; this plan consumes it and does not reshape it.

**Already landed, treated as fixed interfaces (do not change):**

- `scrobblescope/unmatched.py`: `REASON_BELOW_THRESHOLD = "below_threshold"`,
  the three-entry category order, and
  `partition_albums_by_threshold(albums, min_plays, min_tracks) -> tuple[dict, dict]`
  returning eligible albums and threshold exclusions.
- `scrobblescope/orchestrator.py`:
  `fetch_top_albums_async(...) -> tuple[dict, dict, dict]` (eligible,
  threshold exclusions, fetch metadata), with `albums_below_threshold` added to
  the stats mapping.
- The persisted unmatched payload per album: `artist`, `album`,
  `play_count`, `track_count`, `failed_thresholds`, `min_plays`, `min_tracks`,
  `reason_code`, `reason`.

**New or changed declaration types (`.docsync.toml` only):**

- `[[value]]` with `name`, `[[value.sites]]` (`file`, `pattern`, `expect`) --
  for each fact the audit shows living in two places that must agree.
- `[[retired]]` with `name`, `reason`, `pattern`, `scan`, `allow_files`,
  optional `[retired.allow_after]` -- for each claim the audit shows is no
  longer true in a document that still prescribes behaviour.
- `[[anchor]]` -- already covers `docs/design/README.md` citations; no new one
  is needed unless a new citation shape appears.

**New or changed DOM/data contracts in `templates/unmatched.html`:**

- `data-step` on `.unmatched-expander-btn` becomes `"25"` (was `"50"`).
- `data-initial` stays `"10"`; `data-total-count` stays the group's album count.
- `aria-expanded` and `aria-controls` must stay correct through the new
  collapse path taken by the back-to-top control.
- `.unmatched-groups` stays the responsive grid it is: three columns when three
  reasons are present, two when two, one below 1024px. The owner's layout
  ruling preserves this branch, so it is not removed.

**New or changed CSS custom-property contracts:**

- `--ss-shadow-chip` gains its first real consumer (the active theme-choice
  pill), which is the selected-segment case it was drawn for.
- `--ss-shadow-card` is removed (never defined; is the dead-declaration case).
- `--shell-accent-ink` is removed with `global.css` (its only consumers).
- The 140 ms page-exit duration gains a single named owner that the JavaScript
  reads instead of hardcoding, because `shell.css:70` and `page_motion.js:30`
  currently hold two halves of one timing with no link between them.

**Retired names that must not survive in a prescriptive document:**

- `--radius-pill` (the shipped name is `--radius-full`).
- `--shadow-modal`, `--overlay-scrim`, `--blur-sticky` (no such tokens ship).
- `--surface-page`, `--text-strong`, `--accent`, `--border-default`,
  `--space-1..12`, `--card-padding`, `--page-gutter`, `--content-max`,
  `--form-max`, `--leading-*`, `--tracking-*`, `--text-data-*`, `--weight-*`,
  `--logo-bar`, `--button-solid-*`, `--rocket-0..6`, `--rocket-ramp`,
  `--heatmap-cell-radius`, `--heatmap-cell-gap`, `--duration-*`, `--ease-*`,
  `--pinwheel-cycle`, `--ss-warn`, `--duration-logo`.
  Where one of these still appears, the shipped name is the `--ss-*` name or
  daisyUI slot the audit's sections 2.2-2.5 record.
- `--text-body` and `--text-muted` **as colours**: `--text-body: 1rem` is
  Tailwind v4's own font-size namespace, so a colour at that name wins on
  specificity and silently breaks the `.text-body` utility. This is D-2, and
  it is the one collision rule an agent must not be allowed to re-derive.

**New frontend-gate observation contracts** (see [Testing]):

- Visible-row count per `.unmatched-group` after the expander and after the
  back-to-top control.
- Computed `font-weight` on every element of every migrated page in both
  themes (must never be 500 or 600).
- Zero-count heatmap cell `fill` before and after a theme toggle, read back
  from the DOM.

## [Files]

### Phase 1 -- finish the WP-7 extension (uncommitted work in this worktree)

| File | Change |
| --- | --- |
| `templates/unmatched.html` | Keep the side-by-side `.unmatched-groups` grid (`grid-cols-1 lg:grid-cols-2|3`) and its `items-start` top alignment. Change `data-step` from `"50"` to `"25"` (line 174). Let the reason detail wrap rather than truncate at the narrower panel width. Keep `data-initial="10"`, `data-total-count`, the four-column table, the 10-row `.unmatched-overflow hidden` rhythm, `.unmatched-expander-btn`, `.unmatched-back-to-top-btn`, `[data-artist-image]`, and the `results-page unmatched-page` main element. |
| `static/js/unmatched.js` | Change the `step` fallback at line 85 from `\|\| 50` to `\|\| 25`. Extract the expander's collapse branch (lines 91-106) into one named function and call it from both the expander click and the back-to-top click (lines 127-131), so back-to-top collapses the group as well as scrolling. |
| `static/css/unmatched.css` | Own only page-specific behaviour: panel gaps and vertical rhythm, the narrower four-column budget, the threshold metric style, the reason-detail wrap, the 2.5rem/2.75rem artwork override, narrow-screen row containment, and the coarse-pointer 44px targets. Keep `max-width: 90rem`, `var(--unmatched-surface)`, `var(--radius-sm)`, `box-shadow: none`. Keep the `min-width: 1024px` rule (lines 10-13) -- it gives the side-by-side grid its width, so verify it rather than deleting it. |
| `static/css/tailwind.css` | Regenerated output, only if a utility class changes. Produced by `scripts/dev/tailwind_build.py`; never hand-edited. |
| `scripts/dev/frontend_gate.py` | Extend the unmatched checks: side-by-side parity at desktop (panels share a top offset and the grid computes to the expected column count) and a single column below 1024px, no eyebrow element before `h1`, neutral username (no italic and no primary-colour class), reason order `below_threshold` -> `release_scope` -> `no_spotify_match`, expander progress 10 -> 35 -> ... -> total, back-to-top collapses back to 10 with `aria-expanded="false"`, artwork 40px mobile / 44px desktop, and no horizontal overflow at the narrow profile. |
| `tests/test_routes.py` | Assert the rendered group order, the `below_threshold` section's title and copy, and the threshold metric text for an item failing both minimums. |
| `tests/test_template_shell.py` | Assert `data-step="25"` and `data-initial="10"` survive, so the owner ruling is pinned rather than spelled in a review comment. |
| `docs/superpowers/plans/2026-09-11-batch21-wp7-threshold-horizontal-report-extension.md` | Tick Task 2 steps 1-7, record the 50-to-25 deviation, and record that the owner's side-by-side ruling supersedes the stacked layout its Step 4 describes. |
| `PLAYBOOK.md` | Section 3: WP-7 extension complete. Section 4: dated `(Batch 21 WP-7)` entry. |
| `.claude/SESSION_CONTEXT.md` | Section 1 batch-status row and test count. |

### Phase 2 -- document reconciliation to the audit

| File | Change |
| --- | --- |
| `DESIGN.md` | Correct the four claims the audit names (Modal Shadow row, `var(--border-default)` -> `var(--ss-border-default)`, both index grid bands, `--rocket-5`'s real consumers) and add the mechanisms the audit says no document records: the `--ss-*` name-collision rule; dynamic spacing off; the two scaling systems; the eight real breakpoints; the mark-recolour requirement; the gate-pinned geometry; "disabled is not hidden"; one framework stylesheet per page; framework-neutral shared partials and their `.hidden` dependency; the stale-async-response convention; the ramp's single source; motion's real values and its status as the weakest area; the heatmap's mobile strip, its log10 mapping and its three SVG-attribute constraints; the two export architectures; the seven-step type ladder; `--radius-full`; the five surfaces and the absence of a warn colour; the theme marker's dual write and its retirement path. |
| `docs/design/RECONCILIATION.md` | Correct the stale geometry row in section 7 (D-15: the gap is 2px, not 3px) and the override table's "Current source declares `3fr 4fr`" (D-16: `1.1fr 1fr` holds for 860-1199px). Append numbered sections (never reuse or renumber) recording: the 2026-09-11 owner frame that the design system is not the aesthetic authority for a migrated page; the mobile heatmap strip as an explicit override, which answers the first half of F-B21-19; a pointer to `docs/design/designsystemaudit.md` as the code-derived reference; and the unmatched-report layout override, since the approved spec still states the superseded stacked layout. |
| `docs/superpowers/specs/2026-09-11-unmatched-threshold-horizontal-report-design.md` | Record that the owner superseded its "stacked, full-width reason sections" line with the side-by-side ruling, so the approved spec stops contradicting the shipped layout. Add the override line to the spec, or point `RECONCILIATION.md` at it; the rest of the spec is still accurate. |
| `PLAYBOOK.md` Section 3 | The next-action bullet tells the next agent to "Follow what is specified in `2026-09-11-unmatched-threshold-report-design.md`", which is the document the side-by-side ruling overrode. Repoint it at the ruling, or an agent following Section 3 literally rebuilds the rejected layout and the frontend gate fights it. |
| `docs/AGENT_DOC_MAP.md` | Section 3's Design row names only `docs/design/README.md`. Add `RECONCILIATION.md` (overrides), `DESIGN.md` (code-derived summary) and `docs/design/designsystemaudit.md` (audit of the handoff against the code), or the map sends the next agent to the frozen snapshot alone. |
| `.docsync.toml` | Add `[[value]]` declarations for the facts the audit proves live in two places (`--ss-surface-card`, `--heatmap-empty` in both themes, the `--results-surface` formula shared by `results.css` and `unmatched.css`, the radius ladder, the light page background). Add `[[retired]]` declarations for `--radius-pill`, the Modal Shadow, and the pre-1970s decade floor. **Edge case:** the `[[retired]]` scan covers `docs/**/*.md`, and the frozen snapshot legitimately still states these, so add `docs/design/*` to that declaration's `allow_files` with a comment saying why a byte-frozen import is exempt. Without that, the new declaration turns a correct snapshot red and the only fix would be editing history. |
| `docs/design/designsystemaudit.md` | **Do not edit.** It is a dated, self-correcting record whose later sections supersede its earlier ones. Corrections belong in `DESIGN.md` and `RECONCILIATION.md`. |
| `PLAYBOOK.md` | Section 3: record the audit as the design-system source and the D-15/D-16 corrections. Section 4: dated entry for this documentation pass. |

### Phase 3 -- the audit's incidental code defects

| File | Change |
| --- | --- |
| `static/css/shell.css` | Lines 575 and 610: `font-weight: 500` -> `400` (or delete the declaration; the active pill already carries a border, a background and a shadow, which is the audit's own reasoning). Lines 574 and 609: adopt `var(--ss-shadow-chip)` for the active-choice shadow, so the token gains the consumer the gate already asserts. Add a comment at line 70 naming `page_motion.js` as the other half of the 140 ms contract. |
| `static/css/heatmap.css` | Line 189: remove `box-shadow: var(--ss-shadow-card, none);` -- the token is never declared, so the fallback always wins and the declaration is dead. |
| `static/js/page_motion.js` | Line 10: remove `document.body.classList.add('is-ready')` unless a stylesheet is given a reason to read it; nothing does today. Line 30: read the exit duration from its single owner instead of hardcoding 140, or comment the coupling in both files. |
| `static/js/results-spotlight.js` + `static/css/results.css` | The spotlight swaps at 150 ms while `.spotlight-card-content` transitions opacity over 0.25s, so the fade-out is cut mid-transition. Give the pair one owner and one cross-reference. |
| `static/css/results.css` | `.metric-toggle-btn:focus-visible` uses `outline-offset: 1px` against the system's 2px. Align it, or record it in `DESIGN.md` as the one deliberate exception. |
| `tests/test_template_shell.py` | Pin the token table as it now stands, and add the "no `font-weight: 500` or `600` in `static/css/*.css`" guard. |

### Phase 4 -- WP-8 core: retire the legacy layer

| File | Change |
| --- | --- |
| `static/js/heatmap.js` | `initDarkModeObserver()` (lines 1375-1385): observe `document.documentElement` with `attributeFilter: ['data-theme']` instead of `document.body` with `['class']`. **This must land in the same commit as the `.dark-mode` removal**, or a theme toggle silently leaves every zero-count cell painted in the previous theme's colour and no gate notices. |
| `static/js/theme.js` | Remove the `document.body.classList.toggle('dark-mode', isDark)` write (line 13) and rewrite the stale comment block (lines 5-9) that justifies it with "the seven legacy stylesheets still key on it". Keep `data-theme` on `<html>` and the read-back at line 41. |
| `templates/base.html` | Remove the Bootstrap 5.1.3 stylesheet link (line 69) and the `global.css` link (line 70). Delete the `legacy_css` block (line 68) and its eight child overrides (`error.html`, `heatmap_empty.html`, `index.html`, `loading.html`, `results.html`, `results_empty.html`, `unmatched.html`, `unmatched_empty.html`), because the block's only purpose was to default Bootstrap ON for pages that no longer exist; leaving it is a default that can silently lose a page's theme. |
| `static/css/global.css` | **Delete** (486 lines; no page loads it). |
| `static/css/shell.css` | Delete `--shell-accent-ink` (lines 22 and 43) with its only consumers. Update the comments at lines 6, 165-170 and 494 that explain the file in terms of `global.css` and unmigrated pages. |
| `static/css/error.css`, `static/css/heatmap.css`, `static/css/tailwind.src.css` | Update every comment that references `global.css` or an unmigrated page (`heatmap.css:8` and `error.css:4` are the recorded ones). |
| `scripts/dev/frontend_gate.py` | Update the `shell.css` cascade comment (line ~1694) that still reasons about load order against Bootstrap and `global.css`. Keep `check_mark_follows_theme`; it becomes the regression guard for the new asset contract. |
| `templates/inline/scrobble_scope_inline.svg`, `templates/inline/scrobble_scope_lockup_inline.svg` | Give the letterforms `fill="currentColor"` and move the bars' colour into an SVG **`<style>` element** as `stroke: var(--bars-color)`, so any wrapper that sets `color` and defines the token gets a correct mark with no selector naming it. This is F-B21-23's contract with the audit's own mechanical constraint applied: a presentation attribute does not resolve `var()`, so the literal `stroke="var(--bars-color)"` that FINDINGS prescribes would fail silently. Then delete the per-wrapper recolour list in `shell.css`. Keep the `0 0 453 74` viewBox and the bar feet at 63.50, which three tests in `tests/test_template_shell.py` pin. |
| `FINDINGS.md` | Close F-B21-23 (the asset contract now holds), correct the audit-voided D-34 `::selection`/`scrollbar-color` item rather than implementing it, and record that `.dark-mode` was load-bearing for the heatmap rather than dead. |

### Phase 5 -- WP-8 sweep and close-out

| File | Change |
| --- | --- |
| Repository-wide | `git grep -nE "bootstrap\|data-bs-\|bs-(toggle\|target\|dismiss)" -- templates static` must return nothing (WP-8's deterministic check). |
| `docs/history/reports/<TOPIC>_2026-09-11.md` | The frontend and accessibility audit WP-8 mandates, over the migrated `static/js/`, templates and `tailwind.src.css`; file results as `F-SWE-N` or `F-AUDIT-N`. Batch 21 does not close without it. |
| `BATCH21_DEFINITION.md` | WP-8 gains the audit-derived item list and the `.dark-mode` observer trap in writing, plus the explicit HTML/CSS/JS linting disposition the WP owes. |
| `AGENT_NOTES.md` | Repoint the linting gap entry at that disposition, so the gap closes by a decision rather than by silence. |
| `README.md`, `DEVELOPMENT.md`, `.claude/SESSION_CONTEXT.md` Sections 1/3 | Tech stack, project structure, build step, test count. |
| `BATCH21_DEFINITION.md` -> `docs/history/definitions/` | Archive at close-out, update PLAYBOOK Section 2, purge the log, mark the batch complete per the AGENTS.md close-out procedure. |

### Root artifact

| File | Note |
| --- | --- |
| `docs/superpowers/plans/2026-09-11-batch21-design-system-reconciliation.md` (this file) | Kept, and moved here from the repository root on 2026-09-11. It is a working plan, not a governed document, so it needs no doc-map entry; its move is the commit owed under "Where to pick up" above. `docs/superpowers/plans/gemini_implementation_plan_unverified.md` is already untracked in this worktree and is a prior, unverified attempt at the WP-7 extension; resolve its fate in the same decision. |

## [Functions]

### Modified -- Phase 1

| Function | File | Change |
| --- | --- | --- |
| group expander click handler (anonymous, lines 89-125) | `static/js/unmatched.js` | Split the collapse branch into a named `collapseGroup()` so two callers share one state transition; keep `visibleCount`, the `hidden` class toggles, the `aria-expanded` write and the button label logic in one place. |
| group back-to-top click handler (lines 127-131) | `static/js/unmatched.js` | Call `collapseGroup()` before `scrollIntoView`. Today it only scrolls, which is the owner-reported defect. |
| `syncResultsScale()` | `static/js/unmatched.js` | Unchanged; it already applies the Results scale variables the panel layout depends on. Verify it still runs after the Phase 1 edits. |
| `observeArtistImages()`, `hydrateArtistImage()` | `static/js/unmatched.js` | Unchanged. Preserve `[data-artist-image]`, the `rootMargin: 100px` observer, and the initials fallback. |

### Modified -- Phase 3

| Function | File | Change |
| --- | --- | --- |
| `revealPage()` | `static/js/page_motion.js` | Drop the `is-ready` class write; keep the `is-leaving` removal, which is the only class any stylesheet reads. |
| `followLink()` | `static/js/page_motion.js` | Read the exit duration from its single owner instead of the hardcoded `140`. |
| spotlight rotation and swap (cross-fade pair) | `static/js/results-spotlight.js` | Align the JS swap delay with the CSS transition duration, and comment the coupling in both files. |
| `initDarkModeObserver()` | `static/js/heatmap.js` | **Phase 4**: observe `document.documentElement` for `data-theme`. Same commit as the `.dark-mode` removal. |
| `updateZeroFills()`, `zeroFill()` | `static/js/heatmap.js` | Unchanged signatures. `updateZeroFills` is the observer's callback and is the reason the observer must survive the retirement. |
| `applyTheme(isDark)` | `static/js/theme.js` | **Phase 4**: stop writing `.dark-mode` on `<body>`; keep the `data-theme` attribute write. |

### New -- server side

None. Task 1 of the WP-7 extension already added
`partition_albums_by_threshold` and the three-value
`fetch_top_albums_async`; this plan adds no production Python.

### New -- gate helpers

| Function | File | Purpose |
| --- | --- | --- |
| unmatched group-row helper (working name) | `scripts/dev/frontend_gate.py` | Count visible rows inside a `.unmatched-group` so the expander step and the back-to-top collapse can both be asserted from one measurement. |
| font-weight sweep helper (working name) | `scripts/dev/frontend_gate.py` | Assert no element on a migrated page computes to weight 500 or 600, in both themes. This is the check that would have caught the two `font-weight: 500`s. |
| heatmap theme-fill helper (working name) | `scripts/dev/frontend_gate.py` | Read a zero-count cell's `fill` before and after a theme toggle. This is the check that catches the `.dark-mode` retirement trap. |

## [Classes]

No Python class is added, removed, renamed or moved. `scrobblescope/` is
untouched by this plan; only `static/`, `templates/`, `tests/`, `scripts/`,
`docs/` and the root documents change.

**CSS class changes.**

| Class | File | Change |
| --- | --- | --- |
| `.unmatched-groups` | `templates/unmatched.html` | Unchanged. The responsive grid branch and `items-start` are the owner-ruled layout and are preserved. |
| `.unmatched-group` | `templates/unmatched.html`, `static/css/unmatched.css` | Keeps its panel width inside the grid, its `--results-surface`, 1px hairline, `--radius-sm` and `box-shadow: none`. Only the reason-detail wrap changes. |
| `.site-header__theme-choice--light`, `.site-header__theme-choice--dark` | `static/css/shell.css` | Lose `font-weight: 500` in their active states; gain `var(--ss-shadow-chip)` as the active-state shadow. |
| `.metric-toggle-btn` | `static/css/results.css` | Its `:focus-visible` offset aligns with the 2px system rule, or is documented as the single exception. |
| `.ss-mark` and the per-wrapper mark recolour rules | `static/css/shell.css` | The per-wrapper list is deleted once the inline assets carry `fill="currentColor"` and a `<style>`-scoped `stroke: var(--bars-color)`. |
| `.hm-preview` | `static/css/heatmap.css` | Loses the dead `var(--ss-shadow-card, none)` declaration; keeps its existing border and surface. |

**Container-class contract this change depends on.** An SVG presentation
attribute does not resolve a CSS custom property, so an SVG `<style>` element
is the only correct home for `stroke: var(--bars-color)`. `fill="currentColor"`
is a keyword rather than a custom property, so it remains valid as an
attribute. Get this backwards and the mark ships with a fixed colour in one
theme and no error anywhere, which is exactly how F-B21-21 shipped.

## [Dependencies]

**No dependency changes.** This plan adds none, removes none, and changes no
version.

- `requirements.txt` and `requirements-dev.txt` are untouched. Every package
  stays pinned with `==` as `AGENTS.md` requires.
- `playwright==1.62.0` is already pinned and already drives
  `scripts/dev/frontend_gate.py`; the new gate helpers use it and add no
  package, no `package.json` and no Node project.
- The pinned Tailwind and daisyUI versions in `scripts/dev/tailwind_build.py`
  are unchanged. `static/css/tailwind.css` is rebuilt with the same toolchain,
  so no drift baseline moves.
- No new integration and no new environment variable.
- The only dependency-like thing removed is the Bootstrap 5.1.3 CDN stylesheet
  in `templates/base.html`, which no page has loaded since the last page
  template opted out of `legacy_css`.

## [Testing]

### Test-quality constraints (AGENTS.md "Test Quality Rules")

Every new test must challenge behaviour rather than confirm that a mock was
called. Three concrete obligations for this plan:

1. **Prove each guard fails when the fix is reverted, and say so.** State the
   mutation in the test docstring or the WP log entry: restore
   `font-weight: 500` and the weight sweep must fail; revert `attributeFilter`
   to `['class']` on `document.body` and the heatmap fill check must fail; set
   `data-step="50"` and the expander-step assertion must fail. A guard whose
   failure mode was never observed is an assumption, not a test.
2. **Assert computed style and DOM state, not class names.** A page stylesheet
   loads after the framework and beats a utility of equal specificity, so an
   element can carry `hidden` and still be on screen. Read `getComputedStyle`
   and the DOM.
3. **Cover every state a reader can reach, not the one that loads.** The
   unmatched expander has three observable states (10 rows, 10+step rows, fully
   expanded) plus the back-to-top collapse; the theme toggle has two themes and
   a persisted preference; the decade pills have an impossible-decade state.

### New and modified Python tests

| File | Test work |
| --- | --- |
| `tests/test_unmatched.py` | Already covers the partition contract from Task 1. No change expected; re-run to prove the Phase 1 edits did not disturb it. |
| `tests/test_routes.py` | Assert the `below_threshold` group reaches HTML with its title, description and the `plays`/`tracks` metric, and that group order is `below_threshold`, `release_scope`, `no_spotify_match`. |
| `tests/test_template_shell.py` | Assert `data-step="25"` and `data-initial="10"`; keep the three lockup facts (`0 0 453 74`, bar feet at 63.50, the wrapper class) green through the Phase 4 asset change; add the "no `font-weight: 500` or `600` in `static/css/*.css`" guard. |
| `tests/test_design_snapshot.py` | No change. `designsystemaudit.md` is already in `REPOSITORY_OWNED_PATHS`, and the digest must stay identical through every phase -- that test is what proves no phase edited the frozen snapshot. |
| `tests/scripts/dev/` (existing gate-helper modules) | Add unit coverage for each new gate helper. A helper that cannot fail is not a guard. |
| `tests/test_heatmap.py` | Unchanged unless `updateZeroFills`'s read path is refactored. The theme-toggle behaviour is DOM-only, so it belongs in the browser gate. |

### Browser gate coverage (`scripts/dev/frontend_gate.py`, Chromium + Firefox)

| Check | Phase | Proves |
| --- | --- | --- |
| Unmatched panels sit side by side at desktop and collapse to one column below 1024px | 1 | The owner-ruled layout, otherwise eye-only. |
| Expander progress 10 -> 35 -> ... -> total, then collapse to 10 | 1 | The 25-row step and the collapse state machine. |
| Back-to-top collapses the group and resets `aria-expanded` | 1 | The owner-reported defect. |
| No eyebrow before `h1`; the username is neither italic nor primary-coloured | 1 | The extension's masthead ruling. |
| Artwork 40px mobile / 44px desktop; no horizontal overflow | 1 | The Results-mirrored rhythm at both profiles. |
| No computed `font-weight` of 500 or 600 on any migrated page, both themes | 3 | The No-Medium Rule, structurally. |
| Zero-count heatmap cell `fill` changes on theme toggle to the new theme's empty colour | 4 | The `.dark-mode` retirement trap. Nothing watches this today. |
| Every wrapper of every inline mark renders theme-correct colours | 4 | The new `currentColor` / `<style>` asset contract, which keeps `check_mark_follows_theme` meaningful. |
| The Bootstrap grep returns nothing | 5 | WP-8's deterministic criterion 1. |

### Validation sequence per phase

Run in order and do not advance on a failure:

```
pytest -q
pre-commit run --all-files
python scripts/dev/tailwind_build.py
python scripts/dev/frontend_gate.py
node --check static/js/unmatched.js
python scripts/doc_state_sync.py --fix
python scripts/doc_state_sync.py --check
```

Then confirm `git diff --exit-code -- static/css/tailwind.css` is clean. Per
F-B21-20 the documented order (hooks before staging) and the Tailwind drift
hook disagree; stage the named paths, run the hooks, verify the named paths are
unchanged, and record the order actually used in the WP log entry rather than
silently reordering the repository procedure.

**Documentation validation.** `doc_state_sync.py --check` must exit 0 with no
`DOC` integrity error after every phase. New `[[value]]` and `[[retired]]`
declarations are exactly the change that turns a green corpus red, so run
`--check` immediately after editing `.docsync.toml`, before any other work in
that phase. Root `BATCH21_DEFINITION.md` warnings are expected while the batch
is active and are not failures.

## Phase 1 design annex -- the unmatched report (frontend-design pass)

A design pass under the `frontend-design` skill, applied to Phase 1. This
brief has two hard constraints that outrank the skill's defaults: the shipped
code is the aesthetic authority (the audit's 2026-09-11 reframing), and the
extension spec requires the page to mirror Results. So this pass decides
*composition*, not identity. It introduces no new colour, no new typeface and
no new token.

### Brief

An archival field-notebook report. Its job: tell a reader why each album was
excluded, and -- for the one reason they can act on -- exactly what to change.
The audience has just run a search and is looking at a shorter list than they
expected. The primary job is comprehension plus one clear next action.

### Colour

No new hexes; every value is a shipped token.

| Role | Token |
| --- | --- |
| Section surface | `--results-surface` (the Results midpoint) |
| Hairline and section border | `--ss-border-default` |
| Headings, values | `--color-base-content` |
| Prose and row detail | `--ss-text-body`, `--ss-text-muted` |
| The single primary action | `--color-primary` fill |
| Secondary actions | `--ss-surface-card` on a hairline |

### Type

Roles only, from the shipped system.

| Element | Role |
| --- | --- |
| Page `h1` | `--font-serif` (Instrument Serif) |
| Section title, description, row identity | `--font-sans` (Akzidenz), weight 400 |
| Rank, metric, reason detail | `--font-mono` (Input Mono) |
| Section album count | `--font-figure` (Gotham) |

### Layout

Reason panels sit **side by side**, sorted by reason, in the fixed order
`below_threshold`, `release_scope`, `no_spotify_match`.

The owner ruled this layout explicitly -- "They should not be stacked, but
side-by-side" -- superseding the spec's earlier "stacked, full-width" wording.
Three reasons give three columns, two give two, and below 1024px the grid
collapses to a single column.

```
Desktop, 90rem measure -- panels share a top offset, keep natural height
+--------------------------------+  +--------------------------------+
| Below your thresholds 12 albums |  | Nothing Fits the Filter     8  |  counts: Gotham, right
| Played in 2019, but below 10    |  | Released outside your          |
| plays or 3 unique tracks.       |  | selected release scope.        |
| Lower either minimum and run    |  | Widen the release window.      |
| the search again.               |  |                                |
+--------------------------------+  +--------------------------------+
| RANK | ALBUM / ARTIST | M  | D  |  | RANK | ALBUM / ARTIST | M  | D  |
|  01  | [art] Title    |7/2 | ..  |  |  01  | [art] Title    |9/3 | ..  |
+--------------------------------+  +--------------------------------+
|         Show next 25 (37 left)  |  |         Show next 25 (11 left)  |
+--------------------------------+  +--------------------------------+

Mobile (below 1024px): one column, full width, no horizontal page scroll.
+---------------------------+
| Below your thresholds     |
| 12 albums                 |
| Played in 2019, but       |
| below 10 plays or 3 ...   |
+---------------------------+
| [art] Title               |  artwork 40px
|       Artist              |
| 7 plays / 2 tracks        |
+---------------------------+
```

Alignment: left for prose and identity; right for every numeric column, so the
eye scans down a column rather than across a row. Panels keep their natural
height (`items-start`) instead of stretching to a common bottom, so a short
panel does not fill with empty space.

One consequence of side-by-side that a stacked layout would not have: each
panel is narrower than a full-width row, so the four-column budget compresses
and the reason detail may wrap to a second line. Design for the wrap rather
than reaching for `truncate`, which would hide the very text that explains the
exclusion.

### Principles

1. **The structure is the information.** Albums are grouped by *why* they were
   excluded, and the groups are ordered so the actionable reason comes first.
   The grouping is the design; the panel chrome stays out of its way.
2. **Spend boldness in one place.** The threshold numbers are the only
   emphasised element, because they are the only thing the reader can act on.
   Everything around them stays quiet.
3. **No numbered section markers.** The reason order is priority, not
   sequence, and Results does not number its sections.
4. **Disabled is not hidden.** The fold hides rows but never removes them; the
   control is a real button carrying `aria-expanded`.

### Self-critique -- generic defaults rejected

| Generic default | Replacement, and why |
| --- | --- |
| Three-column card grid with reason badges and an oversized coloured count | Replaced by reason panels at the Results surface and density: one panel per reason, sorted, sharing a top offset. **Recorded correction:** the owner did not reject side-by-side panels -- you asked for them. What the spec rejected was the original badge-and-span card grid. |
| Panels stretched to equal height | Panels keep their natural height (`items-start`). Stretching a short panel leaves dead space that reads as a rendering fault. |
| Eyebrow label above the heading | Removed. The spec requires it, and the audit shows the house section-mark idiom used where it does not belong. |
| Purple italic username for emphasis | Neutral ink. The headline carries the name; the accent is reserved for the one action. |
| Hover-lift on rows | Background tint only, per the Border-Over-Shadow Rule and the State-Only Elevation Rule. |
| Fade-and-slide entrance on each section | One orchestrated page-load moment (`ss-page-enter`, 220 ms, opacity-only), stopped under `prefers-reduced-motion`. |
| `01 / 02 / 03` section markers | None. Recorded because the archival idiom makes them tempting here, and the content is not a sequence. |
| `truncate` on the reason detail | Let it wrap. The panel is narrower side-by-side, and truncation would hide the text that explains the exclusion. |

### What this annex changes in Phase 1

The layout is **not** one of them: side-by-side panels stay. Phase 1 changes
three things only -- the expansion step (50 to 25), the back-to-top control
collapsing its panel, and the page's space, rhythm and sizing once the step and
the collapse behave. The panel header composition (title and description left,
Gotham count right), the four-column budget, and the single-emphasised-metric
rule are already the target; verify them rather than rebuild them.

## [Implementation Order]

Each numbered step is one validated unit. Commit after the step, do not batch
steps into one commit, and pause after each commit for owner review.

**Step status is not tracked here. The Progress section above owns it** -- one
place, so the two cannot disagree.

### Phase 0 -- baseline (no edits)

1. Run the bootstrap guard and record the qualified Python, pytest and
   pre-commit paths it prints.
2. Confirm the pre-work baseline: `pytest -q` (expect 990 passed),
   `pre-commit run --all-files`, `doc_state_sync.py --check`. Record the exact
   counts; do not quote SESSION_CONTEXT's number without re-measuring.
3. Confirm the worktree state matches `git status --short`: the WP-7 UI changes
   are uncommitted and belong to Phase 1. Nothing else may ride along.

### Phase 1 -- finish the WP-7 extension

4. Write the failing assertions first: template tests for the `data-step="25"`
   value, and the frontend-gate checks for expander progress, back-to-top
   collapse and the masthead. Run them and see them fail.
5. Set `data-step="25"` in `templates/unmatched.html` and let the reason detail
   wrap at panel width. Keep the side-by-side grid, the four-column table, the
   10-row initial state, the expander and the portrait markup.
6. Extract the collapse path in `static/js/unmatched.js` into one function,
   call it from the back-to-top handler, and fix the `50` fallback to `25`.
7. Adjust `static/css/unmatched.css` for panel gaps, vertical rhythm, the
   narrower four-column budget and the reason-detail wrap; verify the desktop
   width rule instead of removing it.
8. Rebuild `static/css/tailwind.css` through `tailwind_build.py` if a utility
   changed, and confirm no drift.
9. Run `node --check static/js/unmatched.js`, the focused tests, then the
   two-engine frontend gate. Inspect computed panel width and alignment,
   artwork size, both expander states and the collapse state.
10. Update the extension plan's checkboxes, PLAYBOOK Sections 3-4 and
    SESSION_CONTEXT Section 1; run `doc_state_sync.py --fix`; run the full
    validation sequence.
    Commit: `fix(ui): Align unmatched report with Results`

### Phase 2 -- document reconciliation

11. Edit `DESIGN.md`: the four corrections first, then the added mechanisms,
    one section at a time, re-reading the whole file rather than the diff.
    Re-measure every number before it lands (see the correction table in
    [Overview]); prefer describing a mechanism to quoting a count.
12. Edit `docs/design/RECONCILIATION.md`: correct the stale section 7 row and
    the override-table cell, then append new numbered sections for the
    2026-09-11 frame, the mobile-strip override, and the audit pointer.
13. Update `docs/AGENT_DOC_MAP.md` Section 3 so the Design row names all four
    design documents.
14. Edit `.docsync.toml`: add the `[[value]]` and `[[retired]]` declarations,
    including the `docs/design/*` exemption for the frozen snapshot. Run
    `doc_state_sync.py --check` immediately and fix every `DOC` diagnostic it
    reports, including the siblings of each one -- grep the whole corpus for
    the vocabulary of the property being changed, not the words of the new
    text.
15. Update PLAYBOOK Sections 3-4 and SESSION_CONTEXT for the documentation
    pass; run the full validation sequence.
    Commit: `docs(design): Reconcile the design record with the shipped system`

### Phase 3 -- the audit's incidental code defects

16. Add the failing guards: the `font-weight` sweep in
    `tests/test_template_shell.py`, the `--ss-shadow-chip` consumer assertion,
    and the gate-side weight check. Confirm each fails today.
17. Fix `static/css/shell.css`: the two `font-weight: 500` declarations, the
    `--ss-shadow-chip` adoption on the active pill, and the 140 ms comment.
18. Remove the dead `--ss-shadow-card` declaration in `static/css/heatmap.css`.
19. Remove the dead `is-ready` write and give the 140 ms pair one owner across
    `page_motion.js` and `shell.css`.
20. Align the spotlight cross-fade pair and resolve the 1px focus offset.
21. Rebuild Tailwind CSS if needed, run the full validation sequence.
    Commit: `fix(ui): Remove dead and non-resolving style declarations`
    (split into two commits if the cross-fade and focus items grow.)

### Phase 4 -- WP-8 core: retire the legacy layer

22. Write the failing guard first: the frontend-gate check that a zero-count
    heatmap cell's `fill` follows a theme toggle. Confirm it passes today, then
    fails once `attributeFilter` is reverted -- that is the mutation proof.
23. In one commit: move `initDarkModeObserver()` to `data-theme` on
    `documentElement`; remove the `.dark-mode` write in `theme.js`; remove the
    Bootstrap and `global.css` links and the `legacy_css` block from
    `base.html`; delete the eight child overrides; delete
    `static/css/global.css`; delete `--shell-accent-ink`; update every stale
    comment that reasons about `global.css` or an unmigrated page.
24. Apply the F-B21-23 asset contract in both inline SVGs using an SVG
    `<style>` element for the stroke, delete the per-wrapper recolour list in
    `shell.css`, and keep the three lockup tests green.
25. Update `FINDINGS.md` (close F-B21-23, correct the voided D-34 item, record
    that `.dark-mode` was load-bearing), rebuild Tailwind CSS, and run the full
    validation sequence including both browsers.
    Commit: `refactor(ui): Retire the legacy Bootstrap layer and the dual theme write`

### Phase 5 -- sweep and close-out

26. Run WP-8's deterministic Bootstrap grep; it must return nothing.
27. Run the mandated frontend and accessibility audit over the migrated
    frontend and file its results; Batch 21 does not close without it.
28. Write the HTML/CSS/JS linting disposition into `BATCH21_DEFINITION.md` WP-8
    and repoint the `AGENT_NOTES.md` gap entry at it.
29. Update `README.md`, `DEVELOPMENT.md` and SESSION_CONTEXT Sections 1/3.
30. Owner E2E in Firefox including the downloaded save-as-image file in both
    themes, then the standard close-out: archive the definition, update PLAYBOOK
    Section 2, purge the log, mark the batch complete, and run `--check` to
    confirm the root `BATCH21_DEFINITION.md` warning disappears.
    Commit: `chore(close-out): Batch 21 complete; archive definition and purge log`

## Audit disposition -- what this plan does with each audit item

Not every audit item is actionable here, and saying so is part of the work.
The `docs/design/` snapshot is frozen, so D-1 through D-34 cannot be applied to
it.

| Audit item | Disposition |
| --- | --- |
| D-1, D-2 (token families, `--text-body` collision) | Recorded in `DESIGN.md` and declared in `.docsync.toml`. The external project rewrite is out of repository scope. |
| D-3..D-8, D-12, D-14, D-22, D-23, D-27, D-31 (values, measures, copy) | The code wins by the 2026-09-11 frame. `DESIGN.md` and `RECONCILIATION.md` are updated to the shipped values; no code change. |
| D-13 (scaling system), D-20 (dynamic spacing off), D-25 (eight breakpoints), D-28 (mark recolour), D-30 (gate-pinned geometry) | Recorded in `DESIGN.md` as first-class mechanisms. D-28 additionally drives the Phase 4 asset change. |
| D-15, D-16 (stale repo document) | Fixed in `RECONCILIATION.md` (Phase 2). |
| D-17, D-33, and the section C eyebrow divergence | Withdrawn or cosmetic by the 2026-09-11 frame; recorded as intentional aesthetic choices, not as defects. |
| D-26 (component inventory), D-32 (Artist Spotlight) | Recorded as an inventory correction in `DESIGN.md`; no code change. |
| D-34 (`::selection`, scrollbars) | Void: both sides of the divergence live in a file no page loads. Corrected in `FINDINGS.md`, not implemented. |
| The decade-pill rule direction and "disabled is not hidden" | Recorded in `DESIGN.md` as a named principle; the shipped code is already correct and must not be changed back. |
| The five incidental defects | Phases 3 and 4. |
| The six architectural facts (one framework sheet per page, framework-neutral partials, the `.hidden` dependency, the 140 ms coupling, the stale-response convention, the ramp's single source) | Recorded in `DESIGN.md`; the 140 ms coupling also gets a code fix. |
| The seven unread root tooling files, and `app.py` / `scrobblescope/` | **Out of scope and explicitly not claimed.** The audit states these were never read; no document written under this plan may assert anything about them. |

## Assumptions, limitations, and open owner decisions

**Assumptions.**

1. The owner's 2026-09-11 reframing stands: on a migrated page the code is the
   aesthetic authority and the design documents are behind it. Every value
   correction therefore runs code -> document with no ruling required.
2. `docs/design/` stays a byte-frozen import. If it is ever re-imported, the
   digest in `tests/test_design_snapshot.py` updates in that same commit and
   this plan's document corrections are re-checked against the new snapshot.
3. The WP-7 extension's Task 1 contract (`3f59380`) is final. Reopening it
   would invalidate the route and orchestrator test work in Phase 1.
4. WP-8 keeps its number and its position last. `DOC007` in
   `scripts/docsync/integrity.py` reads the WP headings, and renumbering WP-7
   or WP-8 breaks citations in `PLAYBOOK.md`, `FINDINGS.md` and
   `AGENT_NOTES.md`.
5. The audit remains the reference for the *shape* of the design system while
   the shipped code remains the reference for its *values*. Where they
   conflict, the code wins and the audit sentence is corrected in
   `DESIGN.md` rather than followed.
6. The owner's side-by-side layout ruling outranks the approved spec's stacked
   wording. If that is wrong, Phase 1 changes shape entirely and should be
   stopped before it starts: rebuilding the layout the owner asked for would
   fail three existing frontend-gate assertions.

**Limitations.**

- The audit's `--index-scale` count did not reproduce (111 occurrences in
  `index.css` against the stated 102). Any count that reaches a document must
  be measured in that session or replaced by a description of the mechanism.
- Two audit claims were corrected by this investigation rather than followed:
  `--shell-accent-ink` is not live (its only consumers are in the dead
  `global.css`), and F-B21-23's `stroke: var(--bars-color)` must sit in an SVG
  `<style>` element rather than a presentation attribute. Both are recorded
  above with the evidence that corrected them.
- The heatmap fill behaviour has no automated coverage today. Phase 4 creates
  the first check for it; until that check exists, the retirement is unsafe to
  ship.
- `app.py` and `scrobblescope/` were read only where the audit names them.
  Claims about server-authored copy, KPI payloads, phase labels and
  `page_navigation` remain unverified here, as the audit itself says.

**Open owner decisions this plan deliberately does not make.**

1. **Would `implementation_plan.md` be kept or removed?** Settled 2026-09-11:
   kept, and moved to
   `docs/superpowers/plans/2026-09-11-batch21-design-system-reconciliation.md`.
   It is a working artifact, not a governed document, so it needs no doc-map
   entry. Recorded here rather than deleted and renumbered, so the numbering of
   the decisions below stays stable for anything that cites them.
2. **The fate of `docs/superpowers/plans/gemini_implementation_plan_unverified.md`**
   (untracked, a prior unverified attempt at the same WP-7 ground).
3. **The unmatched expander step: 20 or 25?** The owner said "20 or 25"; this
   plan uses 25 and records it as a deviation, because neither WP-7 document
   states a step size.
4. **Does the serif figure face on Results stay?** The 2026-09-11 frame answers
   this (yes, deliberate), but `DESIGN.md`'s Role Segregation Rule must be
   restated to match, or the two documents contradict each other.
5. **Does the theme gain a third "System" state?** The audit says F-B21-22 is
   really asking for that; the current two-state logic is correct as written.
6. **Is the F-B21-20 staging-order contract settled?** Every phase depends on
   which answer the owner picks, so the plan records the order actually used
   rather than silently reordering the repository procedure.

## Verification of this plan document

- Every file path above was checked against the working tree on 2026-09-11.
  Line numbers refer to branch `test` at `3f59380` plus the uncommitted WP-7
  changes described in Phase 1.
- Every code claim was verified by grep or by reading the file, not inferred
  from the audit: the two `font-weight: 500`s (`static/css/shell.css:575,610`),
  `is-ready` (`static/js/page_motion.js:10`), `--ss-shadow-card`
  (`static/css/heatmap.css:189`), the `--ss-shadow-chip` consumer count (zero),
  `--shell-accent-ink`'s consumers (`global.css` only), the `legacy_css`
  overrides (all eight page templates override an empty block),
  `initDarkModeObserver`'s target (`static/js/heatmap.js:1375-1385`), the
  140 ms pair (`static/css/shell.css:70`, `static/js/page_motion.js:30`),
  `data-step="50"` (`templates/unmatched.html:174`) and the back-to-top handler
  (`static/js/unmatched.js:127-131`).
- No production file, test, or governed document was edited while producing
  this plan. The only file created was `implementation_plan.md`, which was
  moved to
  `docs/superpowers/plans/2026-09-11-batch21-design-system-reconciliation.md`
  on 2026-09-11.

