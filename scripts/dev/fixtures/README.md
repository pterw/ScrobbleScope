# Frontend gate CDN fixtures

These files replace the two external stylesheets every page loads so the
frontend gate runs hermetically: no CI navigation waits on
use.typekit.net or cdnjs.cloudflare.com before the load event. Spec:
`docs/superpowers/specs/2026-09-07-frontend-gate-isolation-design.md`.

## What each fixture replaces

- `typekit_fixture.css` -- the Adobe Fonts kit
  (`https://use.typekit.net/rwy8ghw.css`). Declares the five families in
  `frontend_gate.REQUIRED_FONT_FAMILIES` as `@font-face` blocks with
  data-URI woff2 sources and metric overrides.
- `bootstrap_fixture.css` -- cdnjs Bootstrap 5.1.3. The
  stylesheet-isolation check reads link hrefs, not contents, and the
  body-font check reads the cascade where shell.css wins, so a minimal
  valid rule is enough.

## Why metric-pinned faces

Faces differ in ascent/em ratio (Instrument Serif is tall; Ogg is
wide), so identical `font-size` values produce different line boxes and
wrap points. The fixture pins `size-adjust`, `ascent-override` and
`descent-override` per family to the real kit's metrics, so
text-dependent gate assertions measure stable values instead of runner
fallback weather.

## Calibration and re-calibration

The metric values are verified, not guessed. To calibrate:

1. Run the gate with the live kit:
   `python scripts/dev/frontend_gate.py --live-fonts`
2. In Chromium DevTools, load each family at 16px via
   `document.fonts.load('16px "<family>"')` and read the computed
   line-box metrics.
3. Update each family's `size-adjust`, `ascent-override` and
   `descent-override` in `typekit_fixture.css` toward the live values.
4. Run the gate hermetically:
   `python scripts/dev/frontend_gate.py`
   All checks must pass inside their existing tolerances. Tolerances are
   never changed to admit the fixture -- only fixture metrics move.
5. Record the outcome below.

Re-calibrate whenever the owner changes families in the Adobe Fonts
project. The gate cannot detect kit-metric drift by construction; this
README line is the only record.

## Calibration log

- 2026-09-07: initial fixture created. Metric pins taken from the
  spec's calibration targets; Task 5 of
  `docs/superpowers/plans/2026-09-07-frontend-gate-isolation.md`
  verifies them against the live kit and records adjustments here.
