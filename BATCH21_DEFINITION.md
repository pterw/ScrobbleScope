# BATCH21: UI overhaul -- TBD

**Status:** Placeholder. Scope to be defined when owner finalizes the audit-PDF-driven plan. Renumbered from Batch 20 on 2026-05-22 so Batch 20 (file-hygiene + docs methodology refresh) could be slotted ahead of the UI work.
**Branch:** to be decided when scope is finalized.
**Baseline:** 389 tests passing (Batch 19 close-out + PR #152 fixes; same number as Batch 20 baseline).

---

## Context

Batch 19 wrapped the heatmap-scoped polish (frame, KPIs, "Top Albums" pill,
breathing pinwheel, mobile activity strip) without touching `global.css`,
`base.html`, or the wider Bootstrap surface. Several front-end concerns
were deliberately deferred to this batch so the heatmap PR could land
cleanly. Owner ideas captured during Batch 19 review:

- **Global font stack.** Adopt a Geist (or similar) family across every
  page, not just the heatmap result, with proper fallback chain and
  consistent line-height/weights.
- **Colour palette integration.** Promote the heatmap-scoped surface
  tokens (`--hm-surface-light`, `--hm-surface-dark`, accent purple, warm
  cream, inky purple-dark) into `global.css` and roll them across results,
  unmatched, error, and the index pages. Replace the remaining
  `.dark-mode .*` overrides where Bootstrap 5.3 colour-modes or shared
  CSS tokens can do the job.
- **Index card rework.** The current index form-card design predates the
  heatmap result frame and looks dated next to it. Rework the form layout,
  spacing, and visual hierarchy so the input experience matches the new
  result aesthetic.
- **Bootstrap CDN consolidation.** `base.html` uses cdnjs for CSS,
  `index.html` uses jsdelivr for the JS bundle, other pages use cdnjs.
  Standardize before considering a Bootstrap 5.1 -> 5.3 upgrade.
- **Bootstrap 5.3 colour-modes upgrade.** Evaluate replacing the
  `.dark-mode` class strategy with the built-in colour-mode API once the
  CDN source is consolidated. Test for component regressions before
  committing.
- **Form density and tooltip sizing review.** Index popovers/tooltips are
  visually heavy relative to form labels; review with mobile tap targets.
- **Scattered dark-mode CSS.** Dark-mode table/export rules live across
  `results.css`, `unmatched.css`, and `results.js`. Consolidate via shared
  tokens or Bootstrap colour-modes.
- **Dark-mode toggle placement on mobile.** F-B18/F-B19 noted the
  fixed-position toggle may overlap content on small screens.

Documented in FINDINGS.md F-B19-4 and F-B19-5.

---

## Scope (to be confirmed)

To be expanded into proper WPs once owner finalizes the scope from the
audit PDF. This file exists so PLAYBOOK Section 2/3 has a Batch 21 target
named after Batch 20 close-out, without committing to specific work
packages prematurely. Possible split into Batch 21 (main UI pass) + Batch
22 (Bootstrap 5.1 -> 5.3 upgrade) if the version upgrade surfaces
component regressions during owner review.

---

## Work Packages

To be defined.

---

## Validation gate (every WP)

```
pytest -q
pre-commit run --all-files
python scripts/doc_state_sync.py --check
```
