# Frontend gate CDN fixtures

This directory holds fixtures for external resources the frontend gate is
allowed to serve locally. Spec: `docs/superpowers/specs/2026-09-07-frontend-gate-isolation-design.md`,
amended by owner ruling 2026-09-07 (see below).

## What is served from here

- `bootstrap_fixture.css` -- stands in for cdnjs Bootstrap 5.1.3. It is a
  generic framework file, safe to serve locally so CI never waits on the
  CDN. The stylesheet-isolation check reads link hrefs, not contents, and
  the body-font check reads the cascade where shell.css wins, so a minimal
  valid rule is enough.

## What is NEVER served from here

**The Adobe Fonts kit (`use.typekit.net/rwy8ghw.css`).** Its families are
licensed web fonts (Gotham and Akzidenz-Grotesk Next Pro are commercial
licenses worth thousands per year; re-hosting or embedding them anywhere --
including a git repo, a test fixture, or a synthesized stand-in -- would
misdeclare licensed typefaces). Owner ruling 2026-09-07: the kit always
loads from the real origin, with no per-family exceptions, because the kit
composition can change and a blanket rule cannot drift.

Consequence: the gate is not fully hermetic. Kit fetches can still stall a
navigation; the fail-fast 10s timeout bounds that to one failed check, and
`check_fonts` reports missing faces as advisory WARN lines, never gate
failures. This is the accepted trade-off for license safety.

## Calibration history

No font fixture exists, so there is nothing to calibrate. The earlier
metric-pinned-fixture design was abandoned at the owner ruling above;
`docs/superpowers/specs/2026-09-07-frontend-gate-isolation-design.md`
sections 2 and 6 are superseded by this file.
