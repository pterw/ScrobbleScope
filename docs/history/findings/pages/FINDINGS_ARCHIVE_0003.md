<!-- DOCSYNC:ARCHIVE-PAGE v1 -->
# FINDINGS_ARCHIVE -- page 0003

### F-B21-8: Tailwind scanned the whole repository, and no test would say so -- RESOLVED

`@source` **adds** to Tailwind v4's automatic source detection; it does not
replace it. `static/css/tailwind.src.css` named `templates/` and
`static/js/`, and everyone -- this repository's own documentation included --
read that as the scan boundary. It was not. `@import "tailwindcss"` walks the
project from the root, so `docs/`, `tests/`, `scripts/` and the root Markdown
files were all feeding the extractor.

The extractor treats bare words as class candidates, so ordinary English
prose in Markdown compiled into real utilities. `.contents`, `.isolate`,
`.flex`, `.border`, `.relative`, `.sticky`, `.truncate` and `.italic` were all
in the shipped stylesheet on that basis. Scoping the scan to what the config
already claimed removed **713 of 2,289 lines -- 31% of the file**.

Fixed by `@import "tailwindcss" source(none)`, which turns automatic detection
off and makes the two `@source` directives the whole scan.

**The reason this reached CI.** Nothing local runs the build and compares. The
WP-1 suite tests `tailwind_build.py`'s fetch, verify and platform logic, and
never asserts that the committed CSS is what the pinned toolchain emits. The
only check that can fail is the "Verify committed Tailwind CSS" step in the
Quality Gate, which runs after push. `git diff --exit-code -- static/css/tailwind.css`
was used locally as if it were that check; it only proves the file has not
been edited by hand. This is the same shape as `F-B21-7` -- a gate whose local
tests cannot fail -- and it is the strongest argument for WP-2's
`tailwind-css-drift` pre-commit hook, which closes it.

Two `@source not` directives are now unreachable: `./tailwind.css` and
`../../scripts/bin/*` both sit outside the two scanned directories. They are
harmless, and are left in place as protection in case `source(none)` is ever
removed. Delete them only together with that line.

Resolved. The `@source` scope was fixed first, and the missing local check
landed in `20dfe0d` on 2026-08-23 as the `tailwind-css-drift` pre-commit hook,
which rebuilds the CSS and fails on any difference from the committed file.
- [x] **Status:** resolved
**Completed:** 2026-08-23
Source: PR #173 Quality Gate failure, 2026-08-22.

### F-B21-12: four pinned CI actions target a deprecated Node runtime -- RESOLVED

Every Quality Gate run now annotates: `Node.js 20 is deprecated. The
following actions target Node.js 20 but are being forced to run on Node.js
24: actions/cache@v4, actions/checkout@v4, actions/setup-python@v5,
actions/upload-artifact@v4.` The changelog is
`https://github.blog/changelog/2025-09-19-deprecation-of-node-20-on-github-actions-runners/`.

Nothing is broken. GitHub runs those actions on Node 24 anyway and the gate
passes. The risk is the shape of the fix rather than the fault: all four sit
in one file, `.github/workflows/test.yml`, and they fail together on the day
the forced fallback is withdrawn. That failure would land on whichever work
package happens to be open, would look unrelated to its diff, and would block
every PR at once.

Remedy: bump each of the four to a release that targets Node 24, in one
commit, and confirm the annotation is gone from the next run. Do not guess
the version numbers -- read each action's releases first, because the major
that carries the new runtime differs per action.

Worth doing on its own rather than inside a UI work package. It touches the
gate every other work package depends on, so a bad bump is expensive and a
separate commit is trivial to revert.

Not mirrored to a GitHub issue; `F-B21-9` records that the mirror is manual.

Resolved in `c7bfaec` on 2026-09-07, one commit as the remedy asked:
`.github/workflows/test.yml` now pins `actions/checkout@v7`,
`actions/setup-python@v7`, `actions/cache@v6` and `actions/upload-artifact@v7`.
- [x] **Status:** resolved
**Completed:** 2026-09-07
Source: PR #216 Quality Gate annotation, 2026-08-23.

### F-B21-13: bootstrap state lives in three files and only one is gated -- RESOLVED

`AGENTS.md` makes bootstrap complete only when PLAYBOOK Section 3, the active
batch definition and `.claude/SESSION_CONTEXT.md` Section 1 agree on the
current batch and the next work package. Nothing checks that they do.

`doc_state_sync.py` derives the next work package from PLAYBOOK and writes it
into the managed SESSION_CONTEXT block. It never reads the batch definition.
`scripts/docsync/integrity.py` names `FINDINGS.md` once, in the pinned
root-document list, and its test-count enforcement reads SESSION_CONTEXT
only. So two of the three legs are hand-maintained and unread.

Both drifted in Batch 21 and both were caught by PR review rather than by a
gate:

- `docs/history/definitions/BATCH21_DEFINITION.md` still said WP-2 was next after WP-2 shipped. WP-1's
  plan carried updating that line as an explicit task, WP-2's did not, and
  PR #170 had already made the same correction once for WP-1. Second
  occurrence of the same line going stale.
- The `FINDINGS.md` header still published 666 tests after PLAYBOOK and
  SESSION_CONTEXT moved to 671, in the very commit that was correcting stale
  documentation.

Remedy: extend the integrity gate rather than write another rule. Two checks,
both cheap, because both compare text that already exists:

1. Parse the next-work-package claim out of the active batch definition's
   status line and compare it to the value the renderer already computes from
   PLAYBOOK. Report a diagnostic when they disagree.
2. Apply the existing `latest_test_count_authority()` to the `FINDINGS.md`
   header the same way it is applied to the SESSION_CONTEXT fields.

Written rules have now failed twice on the definition status line, which is
the point at which `AGENTS.md` prefers a mechanical check over a restatement.
Do it in its own commit with tests, not inside a UI work package -- it
changes the gate every other work package depends on.

Not mirrored to a GitHub issue; `F-B21-9` records that the mirror is manual.

Resolved in `8ed1650` on 2026-08-24. DOC007 and the SESSION_CONTEXT renderer now call the same
finite, plan-aware next-WP helper. The CLI supplies the active definition's
planned headings, so absorbed gaps are skipped and an all-complete plan
terminates instead of hanging. DOC007 checks both the definition Status line
and PLAYBOOK's actual Next action bullet; a missing parseable claim remains
silent because it is a different defect. DOC008 applies the shared count
authority to the FINDINGS header with header-specific remediation, including
rotated per-batch logs and deterministic same-date batch ordering. Regression
tests cover agreeing, disagreeing, unparseable, absorbed-gap, all-complete,
header-scope, ambiguity and rotated-authority cases.
- [x] **Status:** resolved
**Completed:** 2026-08-24
Source: PR #216 review round two, 2026-08-23.

### F-B20-4: UI overhaul (driven by owner audit) -- RESOLVED

Scope, locked decisions, and acceptance criteria live entirely in
`docs/history/definitions/BATCH21_DEFINITION.md` -- this entry is a pointer, not a
second copy. Resolved: Batch 21 closed on 2026-09-13 (`9152fd3`) with all
nine work packages done. The frontend and accessibility audit WP-8 chartered
was moved by owner ruling to Batch 23's close-out, where
`BATCH23_DEFINITION.md` WP-7 carries it, so it does not keep this entry open.
- [x] **Status:** resolved
**Completed:** 2026-09-13
Source: owner audit (UI Audit v3) + F-B19-4 owner review.

### F-DOCSYNC-1: ENTRY_BATCH_RE too loose -- RESOLVED

`parser.py` batch-tag regex can misroute entries whose titles contain
"Batch N" substrings; tightening needs backward-compat testing.

Resolved in `fd39c89` on 2026-02-26, whose message cites this audit finding
("F6"): `ENTRY_BATCH_RE` now requires the parenthetical `(Batch N WP-X)` form,
and `tests/test_docsync_parser.py` gained adversarial batch-mention titles.
The finding stayed open for seven months because it was written as prose with
no lifecycle record, so nothing could notice the fix. F-DOCSYNC-3 is a
separate defect: close-out suffixes are still not matched.
- [x] **Status:** resolved
**Completed:** 2026-02-26
Source: DOCSYNC_AUDIT Finding 6.

### F-B21-30: unmatched report describes zero rows as a populated exclusion list -- RESOLVED

The unmatched route passes `total_count=0` correctly, but its template always
states that albums were found and did not match the filter. The following
total of zero contradicts that claim and makes a successful no-unmatched state
look like a backend error.

When the count is zero, render a direct no-unmatched state and retain the
search settings plus existing navigation actions. Do not change the route,
the API, or the job's unmatched payload; this is a presentation condition.

- [x] **Status:** RESOLVED
**Completed:** 2026-09-10
Was recorded as: resolved in Batch 21 WP-7; template renders zero-row state when total_count == 0.
Source: owner browser review, 2026-08-29; verified in templates/unmatched.html 2026-09-10.

---

### F-B22-1: username validation fails open on any transient error -- RESOLVED

- [x] **Status:** RESOLVED
**Completed:** 2026-09-13
Was recorded as: Resolved.
**Source:** owner manual testing, 2026-09-13, after WP-0.

`check_user_exists` (`scrobblescope/lastfm.py`) caught every exception from
its Last.fm `user.getinfo` call -- timeouts, rate limits, malformed bodies,
any non-200/404 status via `raise_for_status()` -- and returned
`{"exists": True, "registered_year": None}` instead of propagating the
failure. `/validate_user`'s blur check and `_validate_heatmap_user` both read
`exists` as a verified account and clear the username field to a green
checkmark, so a transient Last.fm failure (most reachable by rapid
successive checks tripping Last.fm's own rate limit) showed as a confirmed
valid username for arbitrary input, including strings that are not
registered accounts. Last.fm's own privacy check (`check_profile_is_public`)
was not affected; it has no equivalent fail-open branch.

Fixed by letting the exception propagate. Every caller already had a
try/except around the call: `/validate_user` and `_validate_heatmap_user`
now correctly answer 503 "Validation service unavailable. Try again."
instead of a false positive; `results_loading` already treated a failed
registration-year check as non-fatal ("proceeding without it") and is
unaffected. Regression tests:
`tests/services/test_lastfm_service.py::test_check_user_exists_propagates_transient_failure`
and `::test_check_user_exists_rejects_non_404_error_status`.

### F-B21-55: Results scaling left geometry fixed and collapsed in Firefox -- RESOLVED

The unfinished local Results scale changed text tokens but left Tailwind's
named spacing tokens unchanged. At 1200px and 1920px Chromium viewports,
row padding remained 12px and artwork remained 48px while the heading grew.
The CSS length-division expression was also invalid in the installed Firefox:
the desktop heading fell back to 16px and row padding to zero.

Resolved locally on 2026-09-09: a ResizeObserver supplies a numeric scale from
the actual Results width and its 75rem baseline. Named spacing, artwork,
controls and handwritten geometry share that scale; the existing 90rem page
cap bounds growth at 1.2. Narrow layouts retain scale 1. No zoom or visual
transform is used. The header remains independently sized.

Chromium and Firefox now agree: at 1200/1920px, title 48/57.6px, row padding
12/14.4px and artwork 56/67.2px (subpixel rounding allowed). Fourteen browser
samples from 320px through 2560px show no document or table overflow. The
Results interaction gate now compares rendered ratios and mobile recovery.

- [x] **Status:** RESOLVED
**Completed:** 2026-09-09
Was recorded as: resolved in the review follow-up. Source: owner scaling request and
browser measurements, 2026-09-09. Evidence: PLAYBOOK Section 4.

### F-B21-52: fractional Tailwind spacing steps compile to nothing, silently -- RESOLVED

`static/css/tailwind.src.css` sets `--spacing: initial` and `--spacing-*:
initial`, then declares only whole steps: 1, 2, 3, 4, 6, 8, 12. That switches
off Tailwind v4's dynamic spacing scale, so a fractional utility is not a
smaller value -- it is an unknown token that emits no rule at all. `py-2.5`,
`md:py-3.5`, `px-1.5`, `gap-1.5` and `py-0.5` are all absent from the compiled
stylesheet, including in the build deployed to Fly.io.

The failure is silent in every direction. The class stays in the markup, the
Tailwind build reports success, and the drift check passes because the
committed CSS does match a rebuild -- a rebuild that also omits the rule. Only
a computed-style read finds it.

This is what cost the Results KPI rail its padding. The deployed markup used
`p-3` (a real step, 0.75rem on all sides) plus `md:px-4`; the WP-5 rebuild
replaced it with `px-1.5 py-2.5`, and both evaporated, leaving the cells with
**zero vertical padding** and the label 1px from the outline. Restored
2026-09-09 by authoring the deployed geometry in `static/css/results.css`
against the declared scale, which also recovered the dead `gap-1.5` row gap
and `py-0.5` numeral padding.

Two candidate fixes, and the choice is the owner's:

1. Restore Tailwind's dynamic scale by setting `--spacing: 0.25rem` instead of
   `initial`, keeping the named steps as aliases. Fractional utilities then
   work everywhere and the theme keeps its vocabulary.
2. Keep the restricted scale deliberately -- it is a real design constraint --
   and add a check that fails when a template requests a spacing step the
   theme does not declare. This is the option that prevents recurrence rather
   than permitting the syntax.

Until one lands, the same trap is live for every future template edit.

**The remediation grep this finding used to give was incomplete, and following
it leaves most of the damage in place.** The old instruction was "a grep for
`-\d+\.5` across `templates/`". That pattern only finds the fractional shape
(`py-2.5`, `gap-2.5`, `pl-0.5`, `gap-0.5`, `p-1.5`, `pt-0.5`, `-mr-1.5`). Dead
utilities come in a second shape it cannot match at all: whole-number steps the
theme never declares, such as `w-10`, `w-24`, `w-28`, `md:w-28`, `md:w-32`,
`min-w-0` and `inset-0`. Those are exactly as dead as the fractional ones, and
on 2026-09-12 they were 21 of the 37 dead occurrences across the two rebuilt
templates -- so the old grep, followed literally, would have left the majority
of the defect in the tree.

Search for both shapes. The utility classes at risk are every spacing and
sizing step (`p*`, `m*`, `gap*`, `w`, `h`, `min-w`, `min-h`, `max-w`, `max-h`,
`inset`, `top`/`right`/`bottom`/`left`, `space-x`/`space-y`, `size`), fractional
or not, including their responsive and negative variants. A grep alone cannot
decide the question, because whether a step is dead depends on the theme, not on
the class name. The reliable check is to take each such class out of the markup
and confirm that a matching selector exists in the compiled
`static/css/tailwind.css` -- remembering that a responsive variant compiles to
its own prefixed selector (`md:py-3` becomes `.md\:py-3`, not `.py-3`).

**Measured state, 2026-09-12.** The declared ladder is 1, 2, 3, 4, 6, 8, 12.
Against it, `templates/unmatched.html` carried 23 dead occurrences (`py-2.5` x8,
`min-w-0` x5, `w-10` x2, `gap-2.5` x2, `w-24`, `w-28`, `md:w-28`, `md:w-32`,
`gap-0.5`, `pl-0.5`) and `templates/results.html` carried 14 (`min-w-0` x9,
`pt-0.5` x2, `inset-0`, `p-1.5`, `-mr-1.5`). The `unmatched.html` instances were
cleared later the same day by the WP-7 follow-up, which re-authored that page
against the declared ladder. The 14 in `results.html` were then deleted as
markup that lied: they compiled to nothing, so the owner-approved rendering was
already the rendering without them, and computed geometry at 390, 768, 1280 and
1920px was measured identical before and after. Treat
both counts as a dated snapshot, not as a live inventory -- that is precisely
the reason this finding asks for a guard instead of a list.

**Owner decision, 2026-09-12: option 2.** Keep the seven-step ladder. It is a
deliberate design constraint and not a defect. Close the class with a pytest
guard that fails when a template requests any spacing or sizing utility the
theme does not declare, so the next dead class is caught at test time rather
than by a rendered-padding regression.

**Closed by the guard, 2026-09-12.** `tests/test_template_shell.py` gained
`test_no_template_uses_a_spacing_step_the_theme_does_not_declare`, which fails
on any spacing or sizing utility in any template that has no selector in the
compiled sheet, and `test_the_dead_utility_sweep_flags_only_unscaled_spacing_steps`,
its adversarial helper test. The guard was seen to fail on disk: adding
`min-w-0 py-2.5` to `templates/results.html` turned it red naming both tokens.
The frontend gate's unmatched check now also measures row padding, the column
budget and document-level overflow, because a dead utility shows up there as
geometry rather than as a class.

- [x] **Status:** RESOLVED
**Completed:** 2026-09-12
Was recorded as: resolved 2026-09-12. Rotates to the archive at batch close-out. Source:
owner-reported stat-bar padding regression, 2026-09-09; re-measured and ruled
2026-09-12.
/resolved in which batch closeout? is it rotated?

### F-B21-49: four error-page callers painted a 400 badge on a 200 response -- RESOLVED

The missing-ID and unavailable-job branches in `_get_validated_job_context`,
plus the failed and still-processing branches in `_render_results_page`,
omitted both an explicit badge and an HTTP status. Flask returned 200 while
the template displayed its default 400. The earlier description incorrectly
called the fourth site an expired-results branch; it was pending results.

The owner-authorized priority pass now returns matching HTML/status pairs:
400 for a missing identifier, 404 for unavailable or wrong-mode jobs, 202 for
pending results, 503 for retryable processing failure, 404 for an unknown
Last.fm user, and 500 for an unclassified processing failure. The 404 choice
matches the existing JSON APIs: no tombstone distinguishes an expired job
from one that never existed. Saved Results and Unmatched empty states retain
HTTP 200 and clear stale session pointers.

Validation and comment provenance:
[PR 227 priority triage](docs/history/reports/PR227_PRIORITY_TRIAGE_2026-09-09.md).

- [x] **Status:** RESOLVED
**Completed:** 2026-09-09
Was recorded as: resolved in the review follow-up; closes the remaining call-site
half of F-B21-10.
Source: PR #227 TODO verification and owner-authorized priority fix, 2026-09-09.
/so resolved. so it should rotated?

### F-B21-36: heatmap loading repeats context and reserves hidden stat columns -- RESOLVED

The loading detail repeats the active phase, the lone page stat occupies the
left third of a three-column grid, and the parameter summary adds rocket-scale
copy that does not help the current wait.

- [x] **Status:** RESOLVED
**Completed:** 2026-09-05
Was recorded as: resolved 2026-09-05; rotates to the archive at Batch 21 close-out.
Source: annotated owner heatmap-loading screenshot, 2026-09-04.

/batch 21 was closed-out. why is this here?

### F-B21-33: heatmap progress can apply stale responses and mislabel failed pages -- RESOLVED

Heatmap's interval polls can overlap and apply an older response after a newer
one, while its received-page stat temporarily counts failed fetch attempts.

A Node probe executed the current `pollProgress` function with held fetch
responses: two timer ticks created two requests, and resolving the newer
response before the older one left the older phase label visible. The client
also reads mutable `currentJobId` when requesting results, so a response from
an earlier job must be invalidated on replacement. Album polling instead
schedules its next request after the preceding response.

In `lastfm.py`, `completed` increments before checking whether a page result
exists; `_heatmap_progress` writes this count to `pages_received`. Final fetch
metadata corrects it to `len(all_pages)`, so a failed page can make the displayed
received count fall at phase completion. Attempt counts are valid phase work
but must not be presented as successfully received data.

- [x] **Status:** RESOLVED
**Completed:** 2026-09-05
Was recorded as: resolved 2026-09-05; rotates to the archive at Batch 21 close-out.
Source: owner-requested polling audit, 2026-09-04; current Last.fm callback,
heatmap worker and browser polling, plus reversed-response execution probe.

/again batch 21 was closed out, why is this here?

### F-B21-1: a failed event-loop setup leaks a job slot -- RESOLVED

`background_task` (`scrobblescope/orchestrator.py`) and `heatmap_task`
(`scrobblescope/heatmap.py`) build the event loop before the `try` block that
holds the `release_job_slot()` call in its `finally`. If `ProactorEventLoop()`,
`new_event_loop()`, or `set_event_loop()` raises, the function exits without
reaching the `finally`, and the acquired slot is never returned. The semaphore
is a `BoundedSemaphore` in module state, so a leaked slot stays lost until the
process restarts. `MAX_ACTIVE_JOBS` defaults to 5, so the site stops accepting
jobs once that many failures have leaked a slot each. A deployment that
overrides the environment variable exhausts at its own configured capacity, so
read the count from the configured value rather than from the default.

The trigger is rare, which is why this is a candidate and not a P0. The fix is
small: move the loop construction inside the `try`, or acquire the slot after
the loop exists.

Found while checking the Top Albums and heatmap sequence diagrams against the
code. The diagrams record that the release in finally is always reached because
loop setup is inside the try block.
- [x] **Status:** RESOLVED
**Completed:** 2026-09-10
Was recorded as: resolved locally in the Batch 21 WP-7 deviation, pending commit; loop
setup moved inside the try block in both `background_task`
and `heatmap_task`, with defensive cleanup in `finally`.
Source: PR #171 diagram verification, 2026-08-15; verified with TDD mutests 2026-09-10.

/is this confirmed?

### F-B21-2: three dormant Tailwind seams that WP-2 meets at once -- RESOLVED

WP-1 shipped the compiled Tailwind and daisyUI CSS, but no template consumes
it, so three defects sit dormant and the first migrated template hits all
three together.

**Nothing sets `data-theme`.** daisyUI keys both themes on that attribute.
The live control was `body.classList.toggle('dark-mode')` in
`static/js/theme.js`, which no daisyUI rule reads. A migrated template
therefore renders the light theme in both modes. `docs/history/definitions/BATCH21_DEFINITION.md` WP-2
already prescribes the remedy: `theme.js` dual-writes `data-theme` and
`.dark-mode`.

**`prefersdark: true` compiles to an always-on rule.**
`prefersdark: true` in the dark `@plugin "daisyui-theme.mjs"` block of
`static/css/tailwind.src.css` compiles to a `:root:not([data-theme])` rule
inside a dark media query in the generated `static/css/tailwind.css`. While nothing carries
`data-theme`, that selector matches every page, so an OS-dark visitor gets
dark daisyUI colours whatever the in-page toggle says. Setting `data-theme`
settles this seam too, which is why the two are one finding.

**Bootstrap loads unlayered and therefore wins.** `templates/base.html`
loaded Bootstrap 5.1.3 from cdnjs with no `@layer`, while
the generated `static/css/tailwind.css` opens with
`@layer theme, base, components, utilities`. Unlayered styles beat layered ones at any specificity, so
Bootstrap wins every shared class name. The compiled CSS emits ten daisyUI
component classes -- `.alert`, `.btn`, `.card`, `.input`, `.modal`,
`.select`, `.tab`, `.tabs`, `.toast`, `.toggle` -- and Bootstrap defines
several of the same, `.btn`, `.card`, `.modal`, `.alert` and `.toast` among
them. `static/css/global.css`, loaded next to it, is unlayered as well.
The remedy is already locked and this finding defers to it:
`docs/history/definitions/BATCH21_DEFINITION.md` WP-2 moves the Bootstrap link into a per-page block
so each template loads exactly one framework stylesheet. That removes the
collision rather than re-ordering it, and it supersedes the cascade-layering
approach this finding first proposed. This is a cascade-ordering defect,
distinct from the CDN-provider split in F-B20-3, which Batch 21 closes by
removing Bootstrap at WP-8.

Nothing is broken in production today, which is why WP-1's gates passed over
all three.

/so is batch 21 closed out.

**Resolved by WP-2 on 2026-08-23.** All three seams are closed. `theme.js`
dual-writes `data-theme` on `<html>` and `.dark-mode` on `<body>`, and an
inline script in `base.html` sets the attribute before first paint. Setting
it always also stops the `:root:not([data-theme])` rule matching, which
settles the `prefersdark` seam. The Bootstrap link and `global.css` moved
into a per-page `legacy_css` block, so each page loads exactly one framework
stylesheet and the two frameworks never meet. The frontend gate asserts all
three, and `tests/test_template_shell.py` asserts the stylesheet rule for
every page.
- [x] **Status:** RESOLVED
**Completed:** 2026-08-23
Was recorded as: resolved (Batch 21 WP-2, 2026-08-23). Source: WP-1 final review,
2026-08-20.
