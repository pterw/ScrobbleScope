# Frontend Gate Isolation and Determinism -- Design

Date: 2026-09-07
Status: Approved by owner (design conversation 2026-09-07)
Context: PR #227 Quality Gate failed twice with distinct signatures. The
first failure (form centring, toggle height, mobile body offset) was fixed
in `582c5a7`. The second failure is a stall: the gate's own server logged
`Serving index.html`, then `Page.goto` timed out waiting for `load`, and
every later check on that page object inherited the wedged state.

## Problem

The gate runs 21 checks as 29 runs per browser (58 total) inside one
`serve_app()` block, all sharing one browser page per viewport profile.
Every `page.goto(..., wait_until="load")` waits on two external
stylesheets (`use.typekit.net`, `cdnjs.cloudflare.com`). On CI this
creates two coupled failure modes:

1. **Cascade poisoning.** One stalled navigation wedges the shared page
   object; every subsequent check inherits the wedged state and fails or
   times out in turn. Observed in the 2026-09-07 CI run and in local
   runs 2-4 (each failed on exactly one unrelated timeout after an
   earlier stall).
2. **Font weather.** Whether the Typekit stylesheet arrives before
   `load` is a race. When it lands, text-metric checks measure with real
   kit faces; when it stalls, they measure with the runner's fallback
   stack. Same test, two metric worlds, decided by network weather.
   Faces differ in ascent/em ratio (Instrument Serif is tall; Ogg is
   wide), so identical `font-size` values produce different heights and
   wrap points -- a latent geometry-flake source independent of any CSS
   defect.

## Decisions (owner-confirmed)

1. **Logical groups, not per-page or per-check CI jobs.** One workflow
   step, one `serve_app()`, one process; the 21 checks execute as 4
   isolated groups, each with a fresh browser context.
2. **Route-block external CDNs** at the Playwright route layer with
   repo-owned fixture responses. The gate becomes hermetic.
3. **Fail-fast navigation.** 10s per-context navigation timeout, no
   retry. A stall fails its own check; the next group starts clean.
4. **Derived groups.** `CHECKS` remains the single source of truth; each
   entry gains a group field and groups are computed at import. No
   declared duplicate, and therefore no test-of-test for group
   integrity (owner ruling: "redundant to test a test").
5. **Firefox becomes a canary.** Chromium keeps the full 21-check
   acceptance gate; Firefox runs Group A only (~7 runs). This preserves
   the recorded acceptance contract ("realistic window geometry in both
   engines", `docs/superpowers/plans/2026-09-01-batch21-index-scaling-and-review-remediation.md`)
   while cutting Firefox's stall exposure by ~75%. Dropping Firefox
   entirely would overturn that recorded ruling and was rejected.
6. **Metric-pinned font fixture.** The fixture CSS declares the five kit
   families with `size-adjust`, `ascent-override`, and `descent-override`
   calibrated to the real kit's metrics, so text-dependent assertions
   measure pinned values rather than runner fallback weather.

## Architecture

```
serve_app() + sync_playwright()            (unchanged outer block)
+-- for browser_name in BROWSER_NAMES
    +-- for group in derived_groups(browser_name)
        +-- page = browser.new_context(spec, default_navigation_timeout=10_000).new_page()
            +-- install_cdn_routes(page)   (per-context)
            +-- run the group's checks
```

### Groups (by shared fixture and stall profile)

| Group | Checks | Rationale |
|---|---|---|
| A. Static assets & tokens | stylesheet isolation, fonts, body font, theme tokens, divider contrast, index design tokens, mark follows theme | The CDN-touching set; hermetic after route-blocking |
| B. Theme & motion | theme persistence, true warning survives, theme survives blocked storage, index entrance motion | Theme-flip heavy; state isolation matters most |
| C. Forms & validation | validation feedback, private profiles, validator outage, validator race, validator network failure, initial visibility | State-machine family sharing job/validator fixtures |
| D. Layout & pipeline | shell text scaling, loading composition, touch targets, destination empty states, pipeline state machines, artist spotlight rotation, large display scale parity | Measurement-heavy; longest per-run, benefits most from a clean page |

Chromium runs A-D; Firefox runs A only. `PLANNED_RUNS` stays derived
arithmetic so the summary line ("N checks passed in M runs") remains
honest without a second declared number.

### CDN route-blocking

Per-context `page.route()` intercepts both external origins before any
navigation:

- `**use.typekit.net/**` -- fulfilled with
  `scripts/dev/fixtures/typekit_fixture.css`, which declares the five
  `REQUIRED_FONT_FAMILIES` faces with metric overrides and data-URI
  sources. `check_fonts` keeps its real code path (family declared ->
  face loads -> count > 0) against the fixture.
- `**cdnjs.cloudflare.com/**bootstrap*` -- fulfilled with
  `scripts/dev/fixtures/bootstrap_fixture.css` (minimal valid CSS; the
  isolation check reads hrefs, and body-font cascade assertions already
  expect shell.css to win).

The gate asserts at startup that both fixture files exist and that the
Typekit fixture declares every family in `REQUIRED_FONT_FAMILIES`,
failing with a clear message if not.

### Honest trade-offs

- CI no longer proves the *live* Adobe kit serves faces. Local runs with
  `--live-fonts` still can. This was already un-testable-in-CI in
  practice; it is what kept failing.
- The fixture's metric fidelity is only as good as its one-time
  calibration. If the owner changes families in the Adobe project, the
  fixture needs re-calibration. Recorded here as maintenance guidance;
  the gate cannot detect kit-metric drift by construction.

## Testing

- **Unit (new logic only):** the CDN route-blocker -- typekit URLs get
  the fixture fulfill, cdnjs gets the minimal CSS, other URLs pass
  through. Fixture-existence and family-coverage assertions.
- **No group-integrity test** (owner ruling): groups are derived from
  `CHECKS`, so there is no second copy to drift.
- **Existing tests:** `PLANNED_RUNS` arithmetic updates automatically;
  no test asserts a hard-coded run count.

## Acceptance criteria

1. A stalled navigation fails exactly its own check; the remaining
   groups still report.
2. No gate navigation waits on an external origin (verifiable by
   running the gate with external network disabled).
3. All text-metric assertions pass with the fixture inside their
   existing tolerances -- no tolerance is loosened to admit the fixture.
4. One local `--live-fonts` run is compared against the fixture run;
   measurement-sensitive checks agree within existing tolerances.
5. `pytest -q` count change is recorded in PLAYBOOK Section 4 and
   SESSION_CONTEXT per the doc-sync rules.

## Non-goals

- No CI workflow-file change (still one step).
- No per-page split; all-page sweeps stay whole inside Group A.
- No change to `serve_app()` lifetime (one server per run is not the
  stall source; the shared page object was).
- No WebKit addition (never was in the gate; production Safari loads the
  live kit and is unaffected by gate fixtures).
