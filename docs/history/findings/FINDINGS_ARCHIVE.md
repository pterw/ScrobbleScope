# FINDINGS Archive

Resolved and no-action findings rotate here from `FINDINGS.md` at batch
close-out (or during dedicated findings-cleanup WPs) so the active file
stays short while grep history is preserved. Entries keep their original
F-IDs; bodies may be condensed at rotation (full original text remains in
git history and the source audit documents). Nothing here is deleted.
Newest rotation first.

---

### F-B20-2: orchestrator.py second-pass decomposition (promoted from F-B18-1) -- RESOLVED

`scrobblescope/orchestrator.py` (916 lines) mixes album workflow, Spotify
batch processing, error mapping, progress tracking, and result assembly.
Now that `heatmap.py` provides a second pipeline, extract the shared
patterns (event loop setup including the win32 Proactor guard, progress
mapping, error guards) into a common module and split the orchestrator
into pipeline / processing / result-shaping modules. Also on the README
roadmap; absorbs F-B18-7.

Both halves are done. Batch 22 WP-0 split the orchestrator into the
`scrobblescope/orchestrator/` package by phase. The event-loop setup then
reached a third copy -- `background_task`, `heatmap_task` and the
release-check worker -- which is the point `docs/agents/global-rules.md`
Rule 3 says to extract, so on 2026-09-21 it became
`worker.new_thread_event_loop`, with its own tests and every existing
slot-release test passing unmodified. Progress mapping and error guards
still have two occurrences, album and heatmap, so Rule 3 says leave them;
Batch 23's export pipeline would be the third, and its WP-0 is where that
decision belongs.
- [x] **Status:** resolved
**Completed:** 2026-09-21
Source: Batch 18 audit.

### F-B21-50: reconnaissance TODOs in production code generated eight review rounds -- NO ACTION

Commit `769f0aa` added 15 `# todo:` comments to `scrobblescope/routes.py`,
mostly appended to bare HTTP status literals (`400,  # todo: Consider adding
client-side validation`). Commit `16fbf92` removed all 15. Net change to
`routes.py` is zero: the TODO count runs 0 at `b987e48`, 15 at `a53e412`, 0 at
HEAD.

Between those commits the notes cost eight repeated Qlty rounds. The PR #227
audit records `radarlint-pythonS1135` ("Complete the task associated to this
TODO") on 15 rows, at 15 distinct `routes.py` line numbers, each carrying an
occurrence count of 8 -- 120 comment bodies for one batch of notes.

The later priority pass corrected the first verification's "13 implemented /
two genuine" tally: twelve notes described existing behavior, two retain
deferred work (unmatched redesign and possible retirement of legacy POST),
and the results note exposed the remaining F-B21-49 status defect. Removing a
note did not implement the deferred work. The per-note evidence and refreshed
review counts are in
[PR 227 priority triage](docs/history/reports/PR227_PRIORITY_TRIAGE_2026-09-09.md).
The eight-round count above remains the original audit's snapshot.

The lesson is about where such notes live, not whether to take them. A scratch
file or a findings entry costs one reader; a TODO in a linted production module
is a standing finding that every scanner republishes on every run, and a
reviewer cannot tell an orientation note from a real defect. Keep reading notes
out of production source.

No action, by owner ruling on 2026-09-21. The code half is clean: `git grep`
finds no `TODO` or `FIXME` in `scrobblescope/` or `app.py`. The churn stays in
history, because rewriting it needs owner authorization for a net-zero gain.
What remains is the guidance above, which is a lesson rather than a defect.
- [x] **Status:** no action
**Completed:** 2026-09-21
Source: PR #227 commit-range audit, 2026-09-09.

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

### F-B21-40: Task 3's divider-contrast fix did not cover the index page's own well divider

Task 3 raised `--shell-border` to clear 3:1, but `.index-form`'s
`border-left` draws from the separate, still-opaque `--ss-border-default`
token, which measures roughly 1.12:1 (light) and 1.18:1 (dark) against its
adjoining surfaces -- worse than the 1.27:1 that originally opened
F-B21-24. `check_divider_contrast` (`frontend_gate.py`) read only
`--shell-border`, so the gate stayed green while this divider stayed
unreadable.

Status: resolved in this fix. Added a dedicated `--ss-border-divider` token
(`#858179` light, `#6e6a75` dark) applied only to `.index-form`'s
`border-left`; `--ss-border-default` is untouched everywhere else in
index.css. Measured against both adjoining surfaces in both themes: light
vs page 3.65:1, vs sunken well 3.26:1 (binding); dark vs page 3.69:1, vs
sunken well 3.37:1 (binding). `check_divider_contrast` now also reads
`.index-form`'s rendered `border-left-color` in both engines.
Source: Task 3 specification and standards review.

### F-B21-37: PR #223 understates its refactor scope and omits its execution log

PR #223 describes a loading.js-only refactor, but head a38044b also changes
index filter labels and the shared Python retry helper without a PLAYBOOK entry.

Status: Resolved -- PR #223 merged as 123b127 with corrected scope, a side-task
log, and documented helpers. Validation passed 872 tests and the complete
22-check, 31-run frontend gate in Chromium and Firefox. This was a review and
documentation defect; the inspected diff did not establish a functional
regression. GitHub closed issue #222 on merge despite the partial-scope body;
it was reopened because the remaining complexity targets are not addressed.
Source: Owner-requested PR #223 merge-readiness review, 2026-09-04.

### F-B21-34: one captured snapshot kit URL lacked an explicit expectation

The reference design README's URL capture still participated in live-kit
comparison although its prose capture was pinned as historical evidence.

Added the same snapshot expectation to that URL site. This completes the
capture isolation without changing the Adobe kit, its fonts, or provider.

Status: resolved, 2026-09-04.
Source: late PR #221 review thread 3938613706; owner provider clarification.

### F-B21-38: Task 2's fixed gutters and collapsed height could not protect its boundary states

The proposed minimum alone could not fit the longest headline at 1200px, and
the 673px natural-height guard described the collapsed form rather than the
required decade-plus-open-threshold state.

With fixed hero gutters, both engines measured a one-line album headline at
0.63 and wrapping at 0.64, but the width term already selected 0.671875, so a
lower clamp minimum could not change the rendered result. Scaling the hero
gutters with the composition supports both mode headlines at 0.70; 0.71 wraps
the album headline. This is the largest passing tested hundredth, measured
2026-09-04 in Chromium and Firefox with Adobe Fonts loaded. Readability stays
bounded at 12px; coarse-pointer targets and inputs keep their 44px and 16px
lower bounds. Proportional relationships remain required from 1920px upward.

The 2026-09-05 state sweep measured natural form heights of 673.3px collapsed,
776.8px with decades, 812.3px with thresholds, and 915.8px with both. At the
0.70 lower bound, the fully expanded form measures 769.4px because readable
text wraps in the narrower card. The guard must account for reachable state,
header and gutter space, and the lower bounds; multiplying the available
height by the base factor would overrun it again.

Status: resolved, 2026-09-05. The complete two-engine frontend gate passed in
isolation (22 checks, 62 runs, Chromium and Firefox) after the state-sensitive
height bounds landed. An earlier isolated run failed once in Chromium's
pipeline state-machine check (30s timeout waiting for the heatmap hand-off)
and once in Firefox with NS_ERROR_SOCKET_ADDRESS_IN_USE while unrelated
browser work ran concurrently; neither reproduced in the clean isolated run,
and both are attributed to environment contention, not the scale mechanism.
Source: Task 2 implementation measurements, 2026-09-04 and 2026-09-05.

### F-B21-39: Task 2 review found base-geometry drift and an untested gate helper

The explicit-dimension sweep changed three authored `0.25rem` gaps to
`0.375rem` and removed the mode tabs' `9rem` minimum. Because the scale token
falls back to one outside wide desktop, those edits changed the mobile and
unscaled composition rather than only scaling its existing geometry. The new
desktop-boundary helper also had no adversarial unit test, and current-state
documents retained contradictory pre-implementation wording.

The review remediation restores the original gap and minimum-width bases while
applying the layout factor, adds a wrapped-headline failure-path test for the
helper, and reconciles the live Task 2 and two-engine statements. Qlty's three
production-code comments are addressed in the same pass. Its Bandit B101
reports target pytest assertions and do not describe production code.

Status: resolved, 2026-09-05.
Source: Task 2 specification and standards review; PR #224 Qlty and Graphify
review comments.

### F-B21-35: the proposed scale height guard ignored root-font enlargement

Task 2's fixed 673px natural-height denominator would not follow its rem-sized
content when the reader enlarged the root font.

The production replacement expresses the measured denominator as 42.0625rem.
The complete Chromium and Firefox gate validates a 20px root and restores page
state after the check.

Status: resolved in Task 2, 2026-09-05.
Source: late PR #221 review thread 3938613711; Task 2 implementation.

### F-B21-31: the remediation plan conflicted on counts and omitted a phase-copy reader

Task 4 prescribed counted phase labels while the batch still prescribed
operation-only copy, and its proposed mutable phase dictionary would leave `get_job_context`
returning that nested object by reference.

The owner reaffirmed visible counts on 2026-09-04, conditional on accurate
polling, as the September 1 owner-remediation plan intended. The batch decision
now records that override. The plan requires mutation-isolation assertions for
both repository readers and the F-B21-33 accuracy prerequisites. This corrects
the execution contract; the phase feature has not been implemented. The gaps
predate the latest review fix, rather than being production regressions from it.

Status: resolved in the plan, 2026-09-04; implementation remains Task 4.
Source: PR #221 review threads 3938450404 and 3938450413.

### F-B21-32: repository-authored PR documentation violated the ASCII rule

The batch definition and reconciliation used a multiplication sign, and the
published Graphify report used non-ASCII punctuation on 89 lines.

Normalized those repository-authored files to ASCII without touching any of
the 61 guarded design imports or the preserved Graphify data. The generated
report introduced most violations; the branch-wide scan covers sibling claims.

Status: resolved, 2026-09-04.
Source: PR #221 review thread 3938450418.

### F-WORKTREE-5: display-unsafe branch candidates were dropped before the conflict check

`parse_batch_branch` filtered candidates through `is_display_safe_ref` and only
then counted them, so a Section 3 naming both `wip/batch-21` and a second,
Git-valid branch holding a non-ASCII letter resolved to the ASCII one instead
of failing closed on conflicting metadata. The guard then reported an aligned
checkout even though the document declared two different branches.

The ordering was deliberate in the PR #170 round-2 remediation, on the
reasoning that a candidate failing the predicate "can name no real branch".
That reasoning did not hold: `is_display_safe_ref` is deliberately narrower
than Git's ref rule, so a rejected candidate can still name a real branch.
What the predicate decides is whether a value may be *rendered*, not whether it
may *exist*.

Fixed by counting distinct candidates before any filtering and raising the
existing `GuardError` on a conflict; the display-safety filter now runs
afterwards, only to decide what may be rendered. Both orderings are covered:
removing the count-before-filter fails
`test_a_display_unsafe_branch_still_counts_as_conflicting_metadata`, and
removing the display-safety filter fails three forgery cases in
`test_a_branch_value_cannot_repaint_the_diagnostic_line`. The superseded
prescription in `docs/superpowers/plans/2026-08-05-worktree-safety-guard.md`
carries a correction note so the plan cannot teach the defect again.
Status: resolved 2026-08-14. Source: PR #170 review round 5 (Codex), reported
independently by Copilot in round 6.

### F-WORKTREE-1: Rebase merges leave linked branches history-diverged

GitHub rebase merges rewrite commit identities on `main` without moving the
linked worktree branch, producing a branch that is both ahead and behind even
when its tree is identical; after PRs #163, #165, and #168 this repeatedly
created a risk of phantom PRs, duplicate work, or an incorrect merge.
Status: resolved 2026-08-05. Evidence: the read-only CLI distinguishes
behind-only, identical-tree rebase artifacts, and true divergence; the
canonical bootstrap stops on its errors; and live linked-worktree inspection
reported the expected branch and ancestry without modifying Git. Review
remediation adds final WT013 context to every offline result and keeps
custom-base guidance aligned with the caller-selected ref. Final review
remediation preserves the public facade; WT014 fails closed without traceback or
sensitive runner text, and exact severity plus real CLI tests protect every WT
code. Shared fixtures create host-appropriate tools; host-rendered missing-tool
assertions and simulated POSIX inspection protect the Ubuntu CI boundary.
Source: post-merge lineage investigations for PRs #163, #165, and #168.

### F-WORKTREE-2: Linked worktrees cannot use the relative virtualenv path

The sole `.venv` is gitignored under the primary checkout, so a fresh shell in
a linked worktree cannot run the documented relative activation or test
commands; an uninformed agent may create a forbidden second environment or
fall back to bare pip and reproduce dependency drift.
Status: resolved 2026-08-05. Evidence: the live linked-worktree guard reported
Python, pytest, and pre-commit under the primary checkout's existing `.venv`,
and AGENTS now forbids a second environment and requires those qualified paths.
Source: repository-integrity design validation on 2026-08-05.

### F-DOCSYNC-5: Operational doc metadata drifted across path and branch changes

The live archive prologue and active-definition branch metadata drifted while
`doc_state_sync.py --check` and CI remained green because prefixes were opaque,
live-document references were only narrowly checked, and integrity warnings
did not affect the exit code.
Status: resolved 2026-08-05. Evidence: final-state CLI enforcement rejects
conflicting test fields, dead optional-session references, non-unique tracked
root definitions, and sanitized Git discovery failures; `pytest -q` measured
**521 passed** with 3 existing warnings on the final combined remediation.
Approved design:
`docs/superpowers/specs/2026-08-05-repository-integrity-worktree-alignment-design.md`.
Source: PR #168 pre-merge audit and follow-up root-cause investigation.

### F-DOCSYNC-8: TOML array-of-tables scoping detached declaration sites into adjacent values

In `.docsync.toml`, an intervening `[[value]]` table (`the wide-desktop scale cap`)
inserted on 2026-08-28 after the 5th site of `the single 860px breakpoint`
caused TOML's table-scoping rules to attach the remaining 9 breakpoint sites
to the scale cap declaration instead of the breakpoint declaration. Because the
scale cap lacked an `expect` assertion and those 9 sites did not match the
scale cap's pattern, they silently went unvalidated for 9 days.

Fixed by grouping all 14 breakpoint sites contiguously (including missing frontend
files `loading.css`, `empty.css`, and `theme.js`), adding an explicit
`expect` value to every site (`"860"` or `"859.98"`), separating the wide-desktop
scale baseline and cap declarations, and adding a file-level architectural warning
comment in `.docsync.toml` documenting TOML array-of-tables scoping hazards.
Status: resolved 2026-09-06. Evidence: all 14 breakpoint sites validate under
`the single 860px breakpoint` declaration and `pytest -q` is green.
Source: docsync tooling audit, 2026-09-06.

---

### F-DOCSYNC-9: Mixed expect values in value declarations bypassed consistency checks

In `scripts/docsync/declarations.py:check_values`, sites that declared an `expect`
parameter executed `continue` without appending their values to `captured`. When
a declaration had some sites declaring `expect` and other sites omitting `expect`,
the unannotated sites were cross-checked only against each other, completely
ignoring disagreements with the expected value sites.

Fixed by determining whether all `expect` annotations in a declaration share a
uniform value, and if so, registering `(rel_path, expect)` in `captured` so that
any unannotated site that deviates from the uniform expectation triggers a DOC009
mismatch. Covered by unit tests `test_a_captured_site_that_disagrees_with_a_uniform_expected_site_fails`
and `test_a_captured_site_that_agrees_with_a_uniform_expected_site_passes`.
Status: resolved 2026-09-06. Evidence: 2 new unit tests in `tests/test_docsync_declarations.py`
and all 73 declaration tests pass.
Source: docsync tooling audit, 2026-09-06.

---

### F-DOCSYNC-10: Unlabelled next-action claims bypassed Section 3 integrity enforcement

In `scripts/docsync/integrity.py:_check_section3_next_wp`, if Section 3 did not
contain a bullet matching `SECTION_3_NEXT_ACTION_RE` (`- **Next action:** ...`),
`_section3_next_wp_claim()` returned `None`. The check treated this as absence of a
claim and returned `None`, allowing unlabelled claims (e.g. `- Batch 21 WP status: ... WP-5 is next`)
to silently bypass DOC007 next-action validation against Section 4 execution logs
and the active batch definition.

Fixed with a two-fold remediation:
1. Hardened `_check_section3_next_wp` to inspect Section 3 for unlabelled `NEXT_WP_CLAIM_RE`
   matches when `claimed is None`, raising a blocking DOC007 error requiring the
   `- **Next action:**` bullet label. Covered by `test_doc007_section3_unlabelled_claim_blocks`.
2. Restored the canonical `- **Next action:**` bullet label in `PLAYBOOK.md` Section 3.
Status: resolved 2026-09-06. Evidence: `doc_state_sync.py --check` flagged the unlabelled
claim on `PLAYBOOK.md:167` before remediation and passes cleanly after the label was restored.
Source: docsync tooling audit, 2026-09-06.

---

### F-DOCSYNC-4: per-batch logs were undiscoverable; tombstones retained

Until 2026-07-31 the 18 `docs/history/logs/BATCHN_LOG.md` files were
referenced by no working doc (PLAYBOOK Section 2 had no Log column), so
batch history was reachable only via a directory glob. Fixed: Section 2
gained a Log column and the AGENTS.md close-out procedure fills it per
batch. Related disposition: the two ~300-byte
`docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` and
`docs/history/logs/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` are deliberate Batch 14
"Moved:" tombstones kept
for backward references -- not cruft, do not delete.
Status: resolved 2026-07-31; rotates to the archive at Batch 21
close-out. Source: PR #163 doc-hygiene pass.

### F-SWE-1: SWE-principles audit -- executed 2026-08-20

No differential check of the ten mandated software principles
(AGENT_NOTES.md Owner Preferences) had run since the 2026-02 audits.
`docs/SWE_AUDIT_CHARTER.md` chartered one on 2026-07-31 and was amended
2026-08-19, after a preflight review found it could not work as the gate its
position implies. The amendment named the 13 graded modules explicitly (130
cells), excluded `scripts/docsync/` and `scripts/dev/` with stated reasons,
defined the A/B/C/D rubric and the Boy Scout history window, read the whole
finding corpus including the archive instead of a closed ID list, required a
provenance block naming the audited SHA, and stated which findings block
Batch 21 WP-1. The permission to cut modules to fit the budget was withdrawn.

Executed 2026-08-20 against `1994673`, whose runtime code is identical to
`bb187ae`. All 130 cells filled in one session: 74 A, 28 B, 8 C, 2 D,
18 N/A. Six net-new findings, F-SWE-2 to F-SWE-7. The weakest principle is
Fail Fast, holding five of the eight C grades. Mutation testing deleted all
81 top-level functions in the graded modules one at a time and the suite
caught every one, so there is no net-new test-vacuity finding. The audit
returned **migration blocked by F-SWE-2** under charter Section 6, which is
an owner decision: fix the two lines, or waive.

The charter was retired in the same commit, per its own output contract.
Status: resolved 2026-08-20; rotates to the archive at Batch 21 close-out.
Report at `docs/history/reports/SWE_PRINCIPLES_AUDIT_2026-08-20.md`.
Source: owner request 2026-07-31.

### F-SWE-2: the album year window is built from naive datetimes

`orchestrator.py:70-71` built the Last.fm fetch window with naive datetimes,
so `.timestamp()` applied the host's local zone. The same shifted timestamps
were reused to filter individual scrobbles. On a UTC-5 host, each boundary
moved five hours into the requested year.

This was the twin of F-B19-6 in `heatmap.py`. The standalone pre-WP-1 fix
adds explicit UTC to both constructors. A deterministic regression drives
`fetch_top_albums_async` through a simulated UTC-5 time boundary and asserts
the literal UTC epochs passed to Last.fm; it failed against the naive window
before passing against the corrected one.

Status: resolved 2026-08-20; rotates to the archive at Batch 21 close-out.
Source: SWE_PRINCIPLES_AUDIT.

---

---

## Rotated 2026-07-24 (PR #162 review follow-up)

### F-FEATURE-2: listening heatmap feature -- RESOLVED (shipped in Batches 18/19)

Last.fm-only scrobble density calendar for the last 365 days, no Spotify
calls. Batch 18 delivered the end-to-end feature; Batch 19 polished the
result frame, KPIs, pill labels, pinwheel animation, and mobile layout.
Rotated per the finding-writing rules since the feature shipped;
performance follow-ups continue as F-B18-11 in the active file.

## Rotated 2026-07-24 (Batch 20 WP-7)

### F-B19-6: naive-tz day-attribution bug -- RESOLVED

This finding closed in two portions that were rotated separately, leaving two
headings under one ID. They were merged here on 2026-09-19 because an F-ID is
a permanent cross-reference key and must resolve to exactly one record; DOC018
reports the split. Both bodies are preserved verbatim below, and the finding
is filed at the rotation that closed it.

**Code fix, rotated with Batch 20 WP-6.** PR #152 review (Gemini) surfaced
that `scrobblescope/heatmap.py` decoded Last.fm UTS values with naive
`datetime.fromtimestamp` and built the fetch window with naive
`datetime.now()`. On Fly.io (UTC container) this was silently fine; on local
Windows dev or any non-UTC host it shifted day attribution by hours. Code
fixed in PR #152 (commit `ccb000f`) with
`tests/test_heatmap.py::TestAggregateDailyCounts::
test_utc_decode_invariant_against_local_tz_drift` as the canonical
regression test.

**Follow-up, rotated with Batch 20 WP-7.** The remaining open portion was
closed in Batch 20 WP-7: the naive-tz vacuous-datetime-test anti-pattern is
now item 6 in the AGENTS.md Anti-Pattern Registry, citing that same
regression test as its canonical example.

## Rotated 2026-07-24 (Batch 20 WP-6)

### F-B20-1: README/SESSION_CONTEXT test-file count drift -- RESOLVED

`README.md` and `.claude/SESSION_CONTEXT.md` claimed "24 test files" while
the tree held 22 pytest modules. Corrected in Batch 20 WP-1 (README) and
via the machine-managed SESSION_CONTEXT refresh; the stale "389 tests,
24 test files" line in the FINDINGS header was the last occurrence, fixed
in WP-6. Recorded for audit completeness and archived immediately.

### Resolved since last update (2026-03-02)

Items from prior audits that have been addressed:

- ~~MEMORY.md stale~~ -- Deleted. Replaced by `AGENT_NOTES.md` (tracked) in Batch 17 WP-4.
- ~~README.md screenshot placeholders~~ -- Owner replaced with "coming soon".
- ~~CI Python version drift~~ -- Aligned to 3.13 in Batch 15.
- ~~docsync cli.py unconditional rewrite~~ -- Gated on changed set (Batch 14).
- ~~Test-count regex defined 3 times~~ -- Consolidated to single `TEST_COUNT_RE`
  in `parser.py`; renderer and logic import it (Batch 14).
- ~~Dedup-sort pattern copy-pasted~~ -- Extracted `_dedup_sorted()` helper in
  `logic.py` (Batch 14).
- ~~Gunicorn HTTP serialization~~ -- Added `--threads 4` to Dockerfile CMD.
  Merged to `main` as `f8a579f` (#57). Deployed and verified.
- ~~Dark mode ignores browser preference~~ -- `theme.js` falls back to
  `matchMedia('prefers-color-scheme: dark')`. Commit `463282e`.
- ~~Log rotation loses data under load~~ -- Increased to 2MB cap, 10 backups.
  Commit `21a3b4c` on `main`.

### F-B18-6: dark mode uses body.dark-mode class, not data attributes -- RESOLVED

CSS uses `.dark-mode` class toggled by `theme.js`. Original Batch 18
definition referenced `[data-theme="dark"]` which does not exist. Corrected
in the audited definition; informational only since then.

### F-B18-8: get_job_context shallow-copies results but not nested dicts -- RESOLVED

**Status:** resolved during PR #152 review (Gemini Code Review catch).
`get_job_context()` now explicitly does `results["daily_counts"] =
dict(results["daily_counts"])` after the outer dict copy, restoring the
function's stated contract for heatmap result shape. Variant chosen over
`copy.deepcopy` because the polling hot path runs every ~1s per active
job and the nested structure is well known. New regression test:
`tests/test_repositories.py::test_get_job_context_nested_daily_counts_is_isolated`.

Historical context: `repositories.py` `get_job_context()` originally
copied list results via `list(results)` but did not copy dict results at
all (returned the original reference). A Boy Scout fix added an
`elif isinstance(results, dict): results = dict(results)` branch, but
that was still a shallow copy, leaving the nested `daily_counts` shared
by reference. PR #152 review surfaced this; the fix above closes it.

### F-B18-9: username not sanitized for JS/SVG injection -- RESOLVED

Routes validate that a username exists on Last.fm but do no input
sanitization beyond that; usernames are echoed back in JSON and rendered
client-side. Addressed during Batch 18: `heatmap.js` renders all
user-supplied strings via `textContent` (never `innerHTML`), with the
criterion cited at the top of the file ("No innerHTML with user data
(XSS criterion F-B18-9)"). Verified still true 2026-07-24.

### F-B19-1: loading state still read as a card -- RESOLVED

Owner review showed the pinwheel centered inside a large Bootstrap card-like
box. That made the loading state feel broken even after the earlier clipping
fix. The follow-up removed the card wrapper and uses an unframed loading panel
with a larger SVG-bounded pinwheel. The final SVG keeps the original
breathing/expanding blade animation; the simplified rotating replacement was
rejected during owner review. Fixed in Batch 19 owner-review follow-up.

### F-B19-2: heatmap sizing needed separate desktop and mobile treatment -- RESOLVED

Desktop screenshots at 1440p and 1080p showed the heatmap grid taking too
little visual space because the result container was still constrained by the
Bootstrap `col-md-8` width. Mobile review showed calendar-constrained layouts
either left excessive side space or made cells too small. The follow-up
widened only `#heatmap-result` on desktop and replaced the mobile layout with
a sequential activity strip that fills the frame width with larger cells,
plus mobile headline fitting. Fixed in Batch 19 owner-review follow-up.

### F-B19-5: visual-verification tooling -- NO ACTION

The Browser plugin/skill is the right Codex-side tool when its browser MCP
tools are exposed. In the Batch 19 session, deferred tool discovery did not
expose a callable browser screenshot tool, and shell-launched headless Chrome
did not emit screenshots in the sandbox. For future UI-heavy batches, enable
a Browser/Playwright MCP path if available. No new Python or Node package is
recommended solely for visual QA.

### Load test data (2026-03-04, local) -- HISTORICAL RECORD

Test environment: Flask dev server (Werkzeug, threaded), local `ss-postgres`
Docker container, all caches cleared between runs.

| Concurrent Users | Per-user elapsed | Wall time | Upstream 429s | Outcome |
|------------------|------------------|-----------|---------------|---------|
| 1 (cached)       | 21s              | 21s       | 0             | OK      |
| 2 (uncached)     | 88-106s          | 107s      | 0             | All OK  |
| 3 (uncached)     | 125-201s         | 202s      | 0             | All OK  |
| 5 (uncached)     | 115-268s         | 269s      | 0             | All OK  |
| 10 (partial)     | 216-353s         | ~6min     | unknown       | 6/10 OK |

**Caveat:** Local tests use Werkzeug (threaded HTTP). Production was single
sync gunicorn worker (no threads) at time of testing.

**Global throttle:** `_GlobalThrottle` serializes all API calls at 10 req/s
across all job threads. Jobs slow linearly: N jobs sharing 10 req/s =
~10/N req/s per job.

**Last.fm rate config:** App configures 10 req/s; official limit is 5 req/s
averaged over 5 minutes. No 429s observed in testing, but aggressive.
