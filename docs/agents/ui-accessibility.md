# UI and Accessibility Rules

Relocated verbatim from `AGENTS.md` on 2026-09-19 as part of the docsync
close-out and bounded archives plan, following the `docs/agents/` pattern
`AGENTS.md` "Agent skills" already uses for `issue-tracker.md` and
`domain.md`. The heading text and the item numbers below are unchanged from
the original section, because `docs/design/RECONCILIATION.md` and
`docs/superpowers/plans/2026-09-01-batch21-index-scaling-and-review-remediation.md`
cite specific items by number.

Every rule here was written after the defect it prevents had already shipped.
None of it is theory. Where a rule names a work package, that is the
evidence, not the scope -- the rule outlives the batch.

1. **Units: rem for type and space, px for fine detail.** A reader who raises
   their browser font size should get a layout that grows with the text. Font
   size, line height, padding, margin, gap, and any width or height that
   holds text take rem -- divide the design's px figure by 16. Borders,
   outlines, radii, shadows and anything 2px or under stay px: a hairline is
   a hairline at any text size, and 1px is also the visually-hidden clip.
   Media query breakpoints stay px, because the design states them in px.
   The type scale is already rem (`--text-body: 1rem` in
   `static/css/tailwind.src.css`), and rem text inside px boxes is the
   mismatch that crowds and clips when a reader scales up. WCAG technique C14
   makes relative font sizes a sufficient technique for 1.4.4 Resize Text;
   the spacing half is this repository's own choice, for the same reason. The
   design snapshot under `docs/design/tokens/` states its ladders in px and is
   overridden here, which `docs/design/RECONCILIATION.md` section 11 records.
   Prove a conversion neutral by measuring the rendered page before and
   after, not by reading the diff.
2. **Size for the finger, not for the window.** A control a person can touch
   is at least 44px on its smaller side, and a text input is at least 1rem so
   iOS does not zoom the page when it takes focus. Key both on the pointer --
   `@media (any-pointer: coarse)` -- never on a max-width. A tablet in
   landscape and a touch laptop are wide and touched, and a width-scoped rule
   misses them completely; `any-pointer` rather than `pointer`, because a
   laptop with a mouse and a touchscreen reports the mouse as primary and is
   still touched. Both mistakes shipped in WP-3, and neither was visible to a
   gate that only ever measured a phone.
3. **Every control works without a mouse.** A hint that opens on hover alone
   is unreachable by keyboard and by touch, so removing a popover library
   quietly removes the explanation for some readers. Use `details`/`summary`
   or a real button. Every interactive element keeps a visible focus state
   and a programmatic label. Prove it by tab traversal: a scripted `.focus()`
   stops matching `:focus-visible` once the page has seen a click, so it will
   report a missing focus ring that is not missing.
4. **Replacing a framework control means inheriting what it did silently.**
   Bootstrap's `.invalid-feedback` was hidden unless a sibling carried
   `.is-invalid`, so dropping that class cleared stale text for free. Its
   replacement hides only while empty, and nothing emptied it -- a rejected
   username stayed on screen beside a green, valid field. Before swapping a
   framework class for one of ours, list what the old one did that no markup
   states, and give each of those behaviours a new home.
5. **Motion must be stoppable by CSS.** No SMIL: `prefers-reduced-motion`
   cannot pause an `<animate>` element at all, and `svg.pauseAnimations()` is
   not the answer. Animate from CSS keyframes and cancel them under the media
   query. When cancelling an animation that fades in from zero, restore the
   end state as well, or the control stays invisible for exactly the readers
   who asked for less motion.
6. **Check what the browser computed, in every state a script can reach.**
   A class name is not evidence: a page stylesheet loads after the framework
   and beats a utility of equal specificity, so an element can carry `hidden`
   and still be on screen. Assert computed style. And check the states a
   reader can reach, not only the one that loads -- the first touch-target
   pass measured almost nothing, because the decade pills, the release-year
   field and the whole heatmap form all start hidden.
