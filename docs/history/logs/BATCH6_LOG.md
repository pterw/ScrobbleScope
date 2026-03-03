# Batch 6 Execution Log

Archived entries for Batch 6 work packages.

### 2026-02-12 - Batch 6 completed (frontend refinement/tweaks)
- Scope: Templates, CSS, JS, and tests -- no app.py changes.
- Implementation:
  - **index.html error alert:** Added `{% if error %}` block with Bootstrap `alert-danger` component above the form card. Errors from `results_loading` (missing username, bad year) now render visibly.
  - **Dark-mode toggle mobile fix:** Added `@media (max-width: 575.98px)` rules to all 5 CSS files (index, loading, results, unmatched, error) repositioning the toggle from `top: 1rem` to `bottom: 1rem` on small screens.
  - **Username submission guard:** Added `setCustomValidity()` to `index.js` so that a username flagged invalid by the AJAX blur check blocks native form submission. An `input` listener clears the block when the user types a new name. Network errors fall through to server-side validation.
  - **Encoding artifacts:** Investigated all JS files -- no artifacts found. `encodeURIComponent()`, `.textContent`, and `escapeHtml()` are used correctly. No action needed.
  - **Test enhancements:** Updated `test_results_loading_missing_username` and `test_results_loading_year_out_of_bounds` to assert error message text is present in the response, confirming the alert block renders.
- Deviations: Username submission guard was not in the original playbook scope but was a clear UX gap identified during Batch 6 work.
- Validation:
  - `pytest -q`: 43 passed
  - `pre-commit run --all-files`: all hooks passed
- Notes:
  - No new tests added (existing tests enhanced with assertions).
  - Next batch is Batch 7 (persistent metadata layer).
