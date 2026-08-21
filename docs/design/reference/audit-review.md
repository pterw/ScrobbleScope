# Second pass on the UI audit

A fresh read of `ScrobbleScope UI Audit v3.html` against the code on `main`. Three sections: what the
audit gets right, what reads as generic AI-generated UI, and concrete UX problems for desktop and mobile.
This design system implements the "keep" column and corrects the rest.

## What the audit gets right — keep all of it

- **Warm palette promoted from the heatmap.** Correct diagnosis: `#f8f9fa` / `#121212` / `#333` reads as a
  developer tool. The heatmap frame already proved the warm direction inside the product, so this isn't a
  taste argument — it's consistency.
- **Leaderboard instead of a striped table.** Right-aligned mono values are the reason it scans faster.
  Zebra striping fights the album art.
- **The unmatched page as the product's best idea.** Grouping by reason *category* with a specific,
  numeric fix ("Lower to ≥5 plays to include 14 of these") is genuinely good product thinking.
- **The live bug it found.** `_get_user_friendly_reason()` returns a per-album sentence, so
  `_group_unmatched_by_reason()` produces one group per release year instead of categories. Fix that
  first — the redesigned page can't exist without a reason **code**.
- **Threshold disclosure that expands in place and always shows its current values.** Correct pattern.
- **Tailwind + DaisyUI over React.** Right call for a server-rendered Flask app whose client-side logic is
  a progress poller and two mode switches.
- **Treating the loading screen as a real screen.** It's the longest continuous dwell in the app.

## What reads as AI-generated UI — fix these

1. **The italic-serif-purple accent word on every single headline.** "What *pterw* played", "Find your
   year's *real* top albums", "A year of *listening*". One instance is a signature; ten is a template.
   **Fix:** at most one per screen, and only where the emphasised word is the user's own data (their
   username). Everywhere else, plain serif. The audit itself offers the escape hatch — "if three families
   feels like too many, drop the serif" — and that's worth taking seriously for the form screens.
2. **Numbered mono eyebrows on everything.** "001 · Album filtering", "02 · Results", "09 · Tokens". A
   two-mode utility does not need section numbering; it's portfolio-deck furniture. **Fix:** keep eyebrows
   only where they carry live state ("Top albums · 2025 · play count") and delete the decorative ones.
3. **The two-clause aphorism headline, repeated.** "The index page *does too much, says too little*",
   "A results table is fine. *A leaderboard is better.*", "Already shipped. *Now make it the standard.*"
   The rhythm is identical every time. It's the copy equivalent of the same card component ten times.
4. **The split-screen marketing hero on the index page.** Editorial column left, form right, three
   "→ UPPERCASE MONO" feature marks underneath. That's a generic SaaS landing layout applied to a tool
   whose users arrive to type a username and press go. On a 1280×720 laptop it halves the form column for
   copy nobody reads twice. **Fix:** single centred column — wordmark, mode tabs, form — with the pitch in
   the info modal where it already lives. (The kit ships the split layout because that's what the audit
   specifies; treat it as the thing to challenge first.)
5. **Pastel gradient placeholder covers.** Fine in a mockup, actively wrong shipped: six rotating
   pastel gradients imply meaning that doesn't exist. **Fix:** one neutral tile with the album initial.
6. **Invented KPIs.** "Scrobbles counted · 18,204", "Top play count", "Daily average" on screens that
   don't compute them. Two of the results-sidebar stats restate what's already visible in row 1 of the
   list. **Fix:** show the one number the list doesn't already tell you (albums matched vs albums seen)
   and drop the rest. Numbers that exist to fill a card are data slop.
7. **Four simultaneous progress signals on the loading screen** — pinwheel, determinate bar, rotating
   phase text, live stat counters, parameter tags. **Fix:** pinwheel + phase text always; the bar only
   when the value is real; stats only if they're actually streaming.
8. **9.5px uppercase letterspaced mono carrying real sentences.** The "fix hint" line on unmatched groups
   is the most actionable text in the product and it's set at the smallest, hardest-to-read size in the
   system. **Fix:** 11px sentence case for anything that is a sentence; reserve mono caps for labels.

## Real UX problems, desktop and mobile

**Accessibility**
- **Opacity-as-colour on text.** The heatmap KPI labels use `opacity: 0.5` on `--text-color`. That lands
  under 4.5:1 in both themes. Use a real muted token instead of transparency.
- **Touch targets.** Decade pills (~24px tall), stepper buttons (26×28) and the mono export buttons are all
  under the 44px minimum. On mobile, give the whole row 44px of height even if the visual chip stays small.
- **Mode pills are `span[role="button"]` with `tabindex`** in the shipped `index.html`. Make them real
  `<button>` elements; the design system's `ModeTabs` does.
- **`prefers-reduced-motion` doesn't reach SMIL.** The pinwheel and the logo bars animate via
  `<animate>`, which ignores the CSS media query. Needs an explicit pause (`svg.pauseAnimations()`) when
  the query matches — otherwise the "non-negotiable" asset is also the one accessibility escape hatch that
  doesn't work.

**Mobile**
- **16px inputs, non-negotiable.** The shipped mobile CSS forces `font-size: 16px` on `.form-control` to
  stop iOS auto-zoom. The proposed design specifies 12px inputs. Ship that literally and every focus event
  zooms the page. Keep the 16px mobile override.
- **Sticky export bar** needs bottom padding equal to its height on the scroll container, or it covers the
  last album row.
- **The results header stacks three action buttons** (New search / CSV / image) above the fold on a phone,
  pushing the actual results down. Collapse to the sticky bottom export bar and keep only "New search" at
  the top.
- **Heatmap on mobile** stacks into month blocks rather than scrolling horizontally — good; keep the cell
  size fixed and reduce weeks per row, never shrink cells below ~8px.

**Desktop**
- **Two-column album list breaks reading order.** v3's single column is correct; don't revert.
- **Theme toggle lives in the page footer** on every shipped page — below a long results list, effectively
  undiscoverable. Move it to the header (this system does).
- **The results sidebar is sticky, the export bar is not.** Pick one; sticky sidebar plus inline export
  buttons is enough on desktop.
- **Export coupling.** The CSV exporter walks `.table tbody tr` and the JPEG capture uses `html2canvas` on
  the table wrapper. Replacing the table with a div-based leaderboard breaks both. The audit flagged it;
  make it a work-package precondition, not a footnote.

**Flow**
- **"No matches" should not be a link to a modal.** If nothing cleared the filters, the unmatched breakdown
  *is* the result. Render it inline.
- **`limit_results` is collected on the form but the results header never states it.** Either show it in
  the filter tags or drop the control.

## Verdict

The audit's direction is sound and the diagnosis is accurate; the problem is that its *presentation
language* — numbered eyebrows, italic accent words, aphorism headlines, KPI cards — has leaked into the
product design it proposes. Strip the editorial-essay furniture, keep the warm palette, the leaderboard,
the reason-grouped unmatched page and the disclosure pattern, and fix the mobile input size and touch
targets before anything ships.
