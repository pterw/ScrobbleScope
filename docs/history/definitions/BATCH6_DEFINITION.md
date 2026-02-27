# Batch 6: Frontend refinement/tweaks

Status: **Complete**
Archived from `PLAYBOOK.md` Section 4 on 2026-02-22.

---

Purpose:
- Close UX debt without major redesign.

Tasks:
- Move fixed dark-mode toggle into mobile-safe header/action region.
- Clean encoding artifacts in JS strings.
- Improve loading-state readability and consistency.
- Ensure retry/error states are visually clear and accessible.
- **Known gap from Batch 4:** `index.html` does not render the `error=` variable passed by `results_loading` on validation failure (missing username, year out of bounds). The index page re-renders but the error message is silently dropped. Add an error alert block to `index.html` that displays `{{ error }}` when set.

Acceptance:
- No overlap with primary content on mobile.
- Clean text rendering.
- Error states understandable and actionable.
