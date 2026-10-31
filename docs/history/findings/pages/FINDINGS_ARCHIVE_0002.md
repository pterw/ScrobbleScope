<!-- DOCSYNC:ARCHIVE-PAGE v1 -->
# FINDINGS_ARCHIVE -- page 0002

### F-B21-5: accessibility defects the design handoff does not resolve -- RESOLVED

Three defects verified against the code while importing the handoff. They are
behaviour, not taste, which is why they are filed apart from F-B21-4. The
design bundle names all three but ships no remedy for any of them.

- **Opacity used as a text colour.** `static/css/heatmap.css:174` and `:188`
  set `opacity: 0.5` on KPI label text. That lands under 4.5:1 in both themes.
  A real muted token fixes it; transparency cannot, because the effective
  contrast depends on whatever sits behind.
- **Mode pills are not buttons.** `templates/index.html:21-22` renders them as
  `span[role="button"][tabindex="0"]`. The bundle's `ModeTabs` uses real
  `<button>` elements. WP-3 rebuilds this element anyway.
- **`prefers-reduced-motion` does not reach SMIL.** The pinwheel and the logo
  bars animate through `<animate>`, which ignores the CSS media query. The
  handoff calls reduced motion non-negotiable and specifies the CSS keyframe
  route for the wordmark.
  **Partly resolved on 2026-08-23, PR #216 review round three.** The header
  lockup took the CSS route the handoff specifies: the SMIL is stripped from
  `templates/inline/scrobble_scope_lockup_inline.svg` and `shell.css`
  animates the bars with a reduced-motion guard. That instance was the
  urgent one, because WP-2 had moved the mark into a fixed header on every
  page where it never scrolls out of view.
  **Still open:** `templates/inline/scrobblescope_pinwheel.svg` and the
  index hero copy of `scrobble_scope_inline.svg` both still carry SMIL.
  Strip them the same way rather than reaching for `svg.pauseAnimations()`;
  the CSS route is what the handoff asks for and it needs no JavaScript.
  WP-3 owns the index page and can close both.
  **Resolved 2026-08-25.** WP-3 stripped the SMIL from both. A test asserts
  no rendered page contains `<animate>` at all, and a second asserts every
  inline mark carries the wrapper class the CSS animation keys on -- an
  unwrapped mark is frozen with no error anywhere.

**Settled, recorded here so it is not re-opened as a conflict.** The mobile
input size looked like a fifth item: `static/css/index.css:158` forces
`font-size: 16px` on `.form-control` to stop iOS auto-zoom, while the README
specifies mono inputs down to 9.5px. It is not a conflict. The canonical
bundle's own `docs/design/components/forms/Input.prompt.md` opens with "On
mobile keep the rendered font-size at 16px or larger to stop iOS auto-zoom."
The README's sizes are desktop values. **Keep the override.**

- [x] **Status:** RESOLVED
**Completed:** 2026-08-25
Was recorded as: resolved 2026-08-25 by WP-3, all three items.

- The KPI labels take `var(--ss-text-muted)` in the rewritten
  `static/css/heatmap.css`; the `opacity: 0.5` text is gone. A real token was
  the prescribed fix and it is what shipped.
- The mode pills are `<button>` elements. A test asserts both, and asserts
  that no `role="button"` survives anywhere on the page -- the class, not the
  instance.
- The SMIL is gone from every mark on every page, animated from CSS keyframes
  with a reduced-motion guard.

Source: design handoff import, 2026-08-21.

### F-B21-7: the toolchain integrity test patches away the code it names -- RESOLVED

Two independent defects in `scripts/dev/tailwind_build.py` and its tests. Both
were verified by running them, not by reading.

**The `bin_dir` plumbing is untested.**
`tests/scripts/dev/test_tailwind_build.py:301-302` patches
`required_artifacts` *and* `ensure_artifact` in the same `with` block, so no
integrity code executes inside the one test that names the property. Its
assertion reads `call.args[0]` only, which is the spec -- the `bin_dir`
keyword is never inspected. Deleting `bin_dir=bin_dir` from
`tailwind_build.py:293` leaves **the whole 633-test suite green**, not merely
the 35 toolchain tests. A mutant that redirects every cached artifact to the
default directory is invisible. The test needs to assert the keyword, or to
stop patching `ensure_artifact` and let a `tmp_path` prove the routing.

**A truncated download is reported as tampering.**
`_download_verified` catches `(OSError, URLError)` at
`tailwind_build.py:242`, and `main` catches
`(TailwindBuildError, subprocess.CalledProcessError, OSError)` at `:334`.
`http.client.IncompleteRead` subclasses `HTTPException`, not `OSError`, so it
passes through both handlers and reaches the user as a raw traceback. Worse
is the quiet case: when a connection closes cleanly mid-body, `response.read`
simply returns empty, the loop ends, and the short file fails the digest
check -- so a network truncation surfaces as `SHA-256 mismatch`, which reads
as a supply-chain compromise. An operator seeing that message will
investigate the wrong thing. Distinguish short reads from digest mismatches
before the message is trusted.

**Resolved by WP-2 on 2026-08-23.** Both halves are fixed. The test now
asserts the `bin_dir` keyword on every call, and the mutation was re-run to
prove it: deleting `bin_dir=bin_dir` fails that one test where it previously
left all 633 green. `_download_verified` counts received bytes, compares them
against `Content-Length` before hashing, and reports a truncated download
rather than a digest mismatch; it also catches `http.client.HTTPException`,
so `IncompleteRead` no longer escapes as a raw traceback. A chunked response
sends no `Content-Length`, and that case skips the comparison rather than
reading the absent header as zero.
- [x] **Status:** RESOLVED
**Completed:** 2026-08-23
Was recorded as: resolved (Batch 21 WP-2, 2026-08-23). Found in the WP-1 review on
2026-08-20 and left unfiled; filed 2026-08-22 after the mutation was run.
Source: WP-1 parallel review.

### F-B21-11: the welcome modal covers the new header theme toggle -- RESOLVED

WP-2 puts a standing header bar on every page at `z-index: 1030`.
`index.html` opens the welcome modal on load, and Bootstrap's
`.modal-backdrop` sits at `z-index: 1050`. The backdrop therefore covers the
header, and the theme toggle cannot be clicked while the modal is open. This
was found by the frontend gate, which timed out trying to click the control;
`document.elementFromPoint` at the toggle's centre returns
`div.modal-backdrop`.

The header z-index is not the defect. A modal should cover a header. The
defect is that this modal opens by itself on page load, so the toggle is
unreachable on first visit.

`docs/history/definitions/BATCH21_DEFINITION.md` owner decision 2 already deletes the welcome modal at
WP-3, which removes the cause. Nothing is needed beyond that, but the
interaction is recorded so the deletion is not treated as cosmetic.

The frontend gate's theme-persistence check runs on a migrated page rather
than the index for this reason, and says so in its docstring.

- [x] **Status:** RESOLVED
**Completed:** 2026-08-25
Was recorded as: resolved 2026-08-25. WP-3 deleted the welcome modal, so nothing
covers the header on the index. The gate's theme-persistence check now runs on
every migrated page including `/`, and passes at both viewports, which is the
evidence rather than the deletion itself.
Source: WP-2 frontend gate run, 2026-08-23.

### F-B21-16: unmatched.html loads a Bootstrap bundle nothing on it uses -- RESOLVED

`templates/unmatched.html` pulls the Bootstrap JS bundle, and no `data-bs-*`
attribute on that page uses it. It may already be dead weight, in which case
WP-7 deletes a script tag rather than migrating a dependency.

Check rather than assume. The quick-view modal was deleted earlier in this
batch's plan and the bundle may simply have outlived it, but a `dropdown` or
`collapse` initialised from `unmatched.js` would not show up in a
`data-bs-` grep.

- [x] **Status:** RESOLVED
**Completed:** 2026-09-10
Was recorded as: resolved in Batch 21 WP-7. Verified no JS dependencies exist, removed
`bootstrap.bundle.min.js`, and enforced via `test_template_shell.py::test_a_migrated_page_loads_no_bootstrap_javascript`.
Source: Batch 21 WP-3 review of the remaining legacy pages, 2026-08-25; verified 2026-09-10.

### F-B21-17: a third of this batch's review comments were one fact written twice -- RESOLVED

By the review point that opened this finding, Codex had raised nineteen
comments across PR #216 and PR #218. Six of that first set -- 32 percent --
were not logic defects at all. They were a single fact recorded in more than
one place, where the copies had drifted:

- the mobile breakpoint, 860px in `heatmap.css` and 768 in `heatmap.js`;
- the `limit_results` reversal, recorded as a deviation in the plan while
  five normative copies still prescribed the old placement;
- the WP-3 checkpoint, stale in PLAYBOOK Section 3 and SESSION_CONTEXT;
- the test count in the FINDINGS header;
- the batch definition's next-work-package line;
- a cross-reference naming the units rule by the AGENTS.md section it used
  to sit in, which broke in the same commit that moved it to a new one.

The last one is the argument for a mechanical check rather than a better
rule. `F-STYLE-1` already says to cite by name and not by line number, and
that citation *was* by name -- the name itself moved. A written rule cannot
catch this class; only something that resolves the reference can.

**Proposal, owner-approved 2026-08-25 to build after WP-3 closes.** Three
checks beside the existing DOC001 to DOC008, driven by a declarations file so
the mechanism carries to another repository unchanged:

1. **value** -- a canonical source and the mirrors that must agree with it.
   Catches a constant duplicated across a stylesheet and a script.
2. **anchor** -- a cross-reference must resolve to a heading or list item
   that exists. Catches the broken citation above.
3. **retired** -- a phrase that is no longer true, plus the regions where it
   may still appear. Point-in-time log entries are exempt by design; one
   declaration finds every normative copy.

Stdlib only, and it inherits the pre-commit wiring the docsync package
already has.

- [x] **Status:** RESOLVED
**Completed:** 2026-08-25
Was recorded as: resolved 2026-08-25. Built as DOC009, DOC010 and DOC011 in
`scripts/docsync/declarations.py`, declared in `.docsync.toml`, stdlib
only. Each check was proved against the real defect it was built for by
restoring that defect and watching the check name it. On its first run,
before any test existed, it found `static/css/shell.css` stopping at
`max-width: 860px` where every other stylesheet stops at `859.98px` --
so both the mobile and desktop rules applied at exactly 860 -- and
`AGENTS.md` describing the integrity codes as DOC001-DOC006, four checks
after that stopped being true.
Source: Batch 21 WP-3 review analysis, 2026-08-25.

### F-B21-21: the index hero wordmark ignores the theme -- RESOLVED

Measured on the deployed page, both themes, `data-theme` set on `<html>`:

| mark | light | dark |
| --- | --- | --- |
| header `.site-header__mark` | ink `#1a1820`, bars `#6a4baf` | ink `#f1ede4`, bars `#b39dde` |
| hero `.index-hero__mark` | ink `#000000`, bars `#6a4baf` | ink `#000000`, bars `#6a4baf` |

The hero mark is frozen. Its letterforms are pure black in both themes, so on
the dark page background (`#0e0c12`) they are nearly invisible. Owner reported
it as the main visual defect after the PR #218 deploy.

Both wrappers include the same asset, `inline/scrobble_scope_lockup_inline.svg`,
and both carry the shared `ss-mark` class. Only the header is coloured:

```css
/* static/css/shell.css */
.site-header__mark svg .cls-1        { stroke: var(--shell-accent); }
.site-header__mark svg #logo-text path { fill: var(--shell-ink); }
```

Unstyled, the asset falls back to its own embedded `<style>`, which pins
`stroke: #6a4baf`, and the letterforms have no fill rule at all, so the user
agent paints them black.

`global.css` had the equivalent rules unscoped, matching any SVG on the page:

```css
.dark-mode svg .cls-1 { stroke: var(--bars-color); }
.dark-mode svg #logo-text path, .dark-mode svg #tagline path { fill: var(--text-color); }
```

The four unmigrated Bootstrap pages still load `global.css` and still look
right. The migrated index page does not load it, and `shell.css` replaced the
rule at a narrower scope, so the hero fell through the gap. This is the PR #216
round-three lesson in mirror image: there the defect came from deleting a
container without checking what it styled; here it comes from reusing an asset
under a new container without carrying its styling across.

Remedy, four lines: move both declarations from `.site-header__mark` to the
shared `.ss-mark`, which both wrappers already carry. `--shell-ink` and
`--shell-accent` are defined on `:root` and `:root[data-theme="dark"]`, so they
resolve anywhere. Add a frontend-gate check asserting that every `.ss-mark` on
a migrated page changes its computed fill between themes; the existing gate
cannot see this, because no check reads a colour off an inline SVG.

Not animation. Measured `animate`/`animateTransform` count is 0 on all three
index marks; the only CSS animations target `#horizontal_bars` and the
pinwheel. What reads as moving text is the bars pulsing beside it.

- [x] **Status:** RESOLVED
**Completed:** 2026-08-26
Was recorded as: **resolved** 2026-08-26. `.index-hero__mark` joins `.site-header__mark`
on both declarations in `shell.css`, and the hero now measures ink `#1a1820`
light / `#f1ede4` dark, identical to the header. `.ss-mark` is not yet the
selector: `shell.css` loads after `global.css`, so a rule on the shared class
would also win on loading, results and unmatched, whose values differ and
which no gate can render. WP-8 makes that move when `global.css` retires.
`check_mark_follows_theme` in the frontend gate now fails if a migrated
wrapper is missed; reverting the fix reproduces the failure by name.
Source: owner review of the deployed merge, 2026-08-26. Verified in Chromium.

### F-AUDIT-1: dark-mode toggle placement on mobile -- RESOLVED

Fixed-position footer toggle may overlap content on small screens. Batch 21
first moved the toggle into the standing header bar; later mobile review found
that this made it compete with the two-row navigation instead.

**Resolved by WP-2 and owner mobile review.** The fixed footer bar is deleted.
The same theme control sits in the standing header on desktop and moves into
normal flow after page content on mobile, where it cannot cover content or
compete with navigation. It retains a 44px target, keyboard reachability, its
accessible name, and one source of checked state in both positions.
- [x] **Status:** RESOLVED
**Completed:** 2026-09-05
Was recorded as: resolved (Batch 21 WP-2, refined 2026-09-05). Source:
AUDIT_2026-02-11 and owner mobile review.

## Rotated 2026-09-13 (Batch 21 close-out)

28 findings resolved during Batch 21, the UI overhaul. They are kept whole, with their owner rulings, because several record why a
later change must not undo them.

### F-B21-59: Spotify's February 2026 changelog removes an endpoint the pipeline depends on

`fetch_spotify_album_details_batch` in `scrobblescope/spotify.py` calls Get
Several Albums (`GET /v1/albums?ids=`), and `search_for_spotify_album_id`
calls Search. Spotify's February 2026 Web API changelog lists Get Several
Albums as removed and caps Search at 10 results. The changelog also removes
fields: album `label`, `popularity` and `external_ids`. The package reads none
of those fields, and its searches ask for at most 3 results, so only the batch
call is exposed.

A live probe with the app's client credentials on 2026-09-13 returned HTTP 200
for `GET /v1/albums?ids=`, `GET /v1/albums/{id}`, and Search with `limit=20`
(20 items). The app is not broken today.

The cause is known. The owner confirmed on 2026-09-13 that the app is in
Development Mode. Spotify applied the new rules to new Development Mode apps on
2026-02-11. Existing ones got the Premium requirement, the five-user cap and
the one-Client-ID limit on 2026-03-09, but the endpoint removals were
postponed with no new date
(https://developer.spotify.com/blog/2026-02-06-update-on-developer-access-and-platform-security).
The exemption can therefore end at any time, with notice only on Spotify's
developer blog. When it ends, every album search loses its release dates, and
every album lands in the unmatched report.

Two actions keep the exemption and must be avoided: creating a new Spotify app
or Client ID, which gets the new rules at once, and rotating the secret without
cause.

Fix, **required** (owner ruling, 2026-09-13), implemented the same day.
`fetch_spotify_album_details_batch` in `scrobblescope/spotify.py` treats a
status in `BATCH_ENDPOINT_GONE_STATUSES` (403, 404, 410) as the endpoint being
gone. It then fetches each album through the new
`fetch_spotify_album_details_single` (`GET /v1/albums/{id}`, under the same
Spotify limiter, with 429 retry) and calls `on_fallback(status)`.
- A single album that is unavailable is left out; it does not fail the batch.
- `_run_spotify_batch_detail_phase` in `scrobblescope/orchestrator.py` logs the
  fallback once per job.
- 401 and 5xx do not trigger the fallback: single calls would fail on the same
  token, and an outage is no reason to multiply calls.
- Tests in `tests/services/test_spotify_service.py` and
  `tests/services/test_orchestrator_fetch_spotify.py` pin 403 and 404, a
  single-album 429 retry, a missing album, 500 staying one call, and one log
  line per job. Each failed when its guarded behaviour was mutated.
- A live call confirmed that `GET /v1/albums/{id}` returns the same object
  shape as the batch endpoint.

Batch 22 (enrichment providers) removes the single-provider dependency this
finding describes: Deezer answers when Spotify cannot.

Status: resolved 2026-09-13 (fallback implemented). The exemption itself stays
outside the app's control. Source: Batch 23 planning, 2026-09-13.

### F-B21-58: the unmatched section title says "thresholds", which the copy rules forbid

`scrobblescope/unmatched.py` titles the `below_threshold` panel "Below your
thresholds", and the approved WP-7 extension spec specifies that title
(`docs/superpowers/specs/2026-09-11-unmatched-threshold-horizontal-report-design.md`,
Presentation section). The design system's copy rules say the opposite:
`docs/design/reference/design-system-readme.md` rules that the play and track
minimums are "what counts as listened" in the UI, **never** "thresholds".

Two approved documents disagree, and the page ships one side. This is a copy
ruling, not a defect an agent can settle by picking the rule it prefers. The
title is also what the reader sees on the one panel they can act on, so the
wording carries more weight here than anywhere else on the page.

Status: resolved 2026-09-13. The owner renamed the panel "Not enough listening"
in `scrobblescope/unmatched.py` `CATEGORY_METADATA`, so the copy rules win and
the spec now states the new title. Source: Batch 21 documentation audit,
2026-09-12.

### F-B21-56: upstream Spotify failure detection was coupled to written prose reason instead of reason_code

`_detect_spotify_total_failure` in `scrobblescope/orchestrator.py` checked the
English string `"No Spotify match"` instead of the domain contract
`reason_code` (`REASON_NO_SPOTIFY_MATCH`). When the first WP-7 commit
`b3e3e96` introduced `reason_code` to the contract, this detector was missed.
If the prose string varied or changed, Spotify total failure detection would
not fire, preventing the classified `spotify_unavailable` error from being set.

Status: resolved locally in the Batch 21 WP-7 deviation, pending commit;
`_detect_spotify_total_failure` checks
`reason_code == REASON_NO_SPOTIFY_MATCH` with legacy fallback, verified by
mutation testing.
Source: owner review, 2026-09-10.

### F-B21-47: Artist Spotlight rendered one top-album artist and never rotated

The Results side rail described an Artist Spotlight but built no rotation
collection or timer. Both Flask and the metric-toggle client treated the artist
on the highest-ranked single album as the leading artist, so repeated albums by
one artist were not ranked by their aggregate scrobbles. The fallback Spotify
link also labelled an album ID as an artist destination, and its unguarded image
failure handler could apply after a newer portrait request had started.

Status: resolved locally, 2026-09-06. The server aggregates artists by
scrobbles, takes the top ten, and uses the job ID to choose a stable random five
without changing the album or Heatmap pipelines. Results renders the first
fallback immediately, hydrates the five artist records concurrently afterward,
and rotates them every seven seconds. Candidate-slot, active-index, and image
revision checks discard late responses; reduced-motion readers keep one static
spotlight. The browser gate verifies five unique requests and a rendered card
change in Chromium and Firefox.
Source: owner Results review and source/request-flow audit, 2026-09-06.

### F-B21-43: cached Heatmap restoration painted an obsolete loading state

Opening Heatmap from the header after a result was cached called
`fadeIn(heatmapLoading)` before the first progress request. A completed job
therefore painted the loading panel for a fraction of a second, then replaced
it with the cached result. A final DOM assertion could not detect the flash.

Status: resolved, 2026-09-05. Saved-job restoration keeps the loading panel
hidden until the first response proves that work is still running or reports
an error. A ready result fades in directly; a still-running result preserves
the existing Heatmap polling lifecycle and reveals the accurate progress
state. The Chromium and Firefox gate observes loading-panel class mutations
from before production `DOMContentLoaded` listeners run and fails if a cached
result paints that panel.
Source: owner browser review and two-engine rendered state observation,
2026-09-05.

### F-B21-46: the desktop index form stayed top-heavy as the window grew

The fixed index scale correctly grew the form between realistic 1080p and
1440p windows, but the form composition remained anchored to the well's top
padding. At 1920x945, its outer top and bottom space measured 55.9px and
98.2px; at 2560x1305, those values diverged to 74.5px and 193.6px. The 28rem
base cap also left the card slightly wider than the owner's preferred measure.

Status: resolved, 2026-09-05. The owner-refined base cap is `27.5rem`. The
2026-09-09 refinement places the composition up to 2.5rem above centre,
bounded by 0.25rem of header clearance. Expanded content retains natural
scrolling only when it cannot fit. The gate verifies this upward bias
at realistic 1080p, 1440p, and 4K profiles while retaining the
fixed-geometry checks across every reachable form state.
Source: owner 1080p/1440p visual comparison and two-engine rendered
measurements, 2026-09-05.

### F-B21-45: mobile navigation hid report destinations behind scrolling

The mobile header kept all four desktop navigation links in one horizontal
flex row. At 390px its navigation had a 203px visible width but a 345px scroll
width; at 320px only 133px was visible. Results and Unmatched therefore sat
offscreen unless the reader discovered horizontal scrolling.

Status: resolved, 2026-09-05. The first correction put the four destinations
in a two-column, two-row grid beside the compact theme control. Owner review
then found that the control sat across both rows and visually competed with
their buttons. The subsequent owner refinement uses one contained row across
the header width and moves the same Light/Dark input below page content; it
returns to the header at desktop widths without duplicating state. The browser
gate checks both 390px and 320px widths for contained links, no horizontal
overflow, a matching body offset, footer placement, and a retained 44px theme
target. PR #227 review reconciled this description with the current source.
Source: owner mobile review and rendered Chromium/Firefox measurements,
2026-09-05.

### F-B21-44: the desktop Heatmap result retained the prototype's small measure

The result stage remained capped at about 1100px on a realistic 1920x945
content box, occupying only 57.3% of the viewport. Its authored 14px SVG cells
rendered at 16.6px, making the year grid visually slight beside the scaled
index composition. The headline also singled out the username in purple
italics even though it is data rather than an interactive accent.

Status: resolved, 2026-09-05. At widths from 860px, the centred stage now uses
`84vw` with a `120rem` ceiling; the same realistic 1080p content box renders a
1544.8px frame and 23.7px cells. Mobile retains the bounded base measure. The
username inherits the headline's neutral serif colour and normal style. The
two-engine browser gate asserts the frame ratio, centring, rendered cell range,
and headline treatment against a full-year fixture.
Source: owner side-by-side visual review and two-engine rendered measurements,
2026-09-05.

### F-B21-42: index motion used three unrelated timings and blanked mode copy between animations

The index composition entered over 1.2 seconds after a 0.2-second delay,
Heatmap stage changes used 300ms, and `switchModeHero()` ran a sequential
110ms exit followed by a 180ms entrance. Switching modes therefore removed
the current heading before presenting its replacement and made the hero feel
slower than the surrounding page states.

Status: resolved, 2026-09-05. The two mode descriptions now share one grid
track and crossfade concurrently over 180ms, so the taller copy reserves the
same height in both states. Heatmap stage changes retain 180ms; the 2026-09-09
owner refinement gives page navigation a shared 220ms entry and 140ms exit.
The 2026-09-10 delayed-script probe reproduced a first-paint flash in both
engines: DOM readiness restarted already-visible content from zero opacity.
Entry now starts in CSS without waiting for JavaScript; the regression probe
confirms no visible-to-transparent dip.
The reduced-motion media query restores immediate,
fully opaque states.
Source: owner browser review, 2026-09-05.

### F-B21-41: reachable form states rescaled the entire index composition

Task 2's state-sensitive height bounds made the shared `--index-scale`
depend on which form rows were open. At a fixed 1920x945 content box, both
engines measured the 481.6px form shrinking to 390.5px for a decade or custom
release field, 357.8px for open thresholds, and 325.2px when both were open.
Hero padding, wordmark, headline type, card padding, inputs, and mode controls
all changed with it. The gate required the expanded form to avoid document
scrolling, so it enforced the defect.

Status: resolved, 2026-09-05. Reachable states no longer replace the fixed
window's natural-height reference. Additional rows extend the document while
the composition keeps its initial dimensions. The Chromium and Firefox gate
now compares representative dimensions across album, Heatmap, decade,
custom-year, thresholds, and combined states, and requires the combined state
to produce normal document scrolling at the realistic 1080p content box.
`scrollbar-gutter: stable` prevents Firefox from shifting the columns when
that scrollbar first becomes necessary.
Source: owner browser review and two-engine rendered measurements, 2026-09-05.
