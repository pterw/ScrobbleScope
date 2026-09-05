# ScrobbleScope Findings & Open Issues

Last updated: 2026-08-28
Status: Batch 21 (UI overhaul -- Tailwind + daisyUI migration) is ACTIVE;
WP-0 through WP-3 done. PR #171 merged 2026-08-19 (`bb187ae`). F-SWE-2 was
resolved 2026-08-20, clearing the F-SWE-1 migration block. The root-hygiene
side task closed 2026-08-20 and the design handoff imported 2026-08-21. Two
WP-1 review items were filed as F-B21-6 and F-B21-7 on 2026-08-22, and
F-B21-8 records the Tailwind source-scope defect PR #173 exposed. WP-2
resolved F-B21-2, F-B21-7 and F-AUDIT-1 on 2026-08-23, and filed F-B21-10,
F-B21-11 and F-B21-12. PR #216 review filed F-B21-13. WP-3 resolved F-B21-11
and F-B18-12 and filed F-B21-14 through F-B21-20. The owner's review of the
deployed merge then added F-B21-21 (resolved the same day), F-B21-22,
F-B21-23 and F-B21-24, and the workflow review that followed it added
F-B21-25. The production differential on 2026-08-28 added F-B21-26 and the
private-profile submission defect F-B21-27. Recent owner review also filed
F-B21-28 through F-B21-30. The canonical routing and navigation prerequisite
and WP-4 unified loading rebuild are complete;
**WP-5 is next.**
872 tests across 40 test modules.

**Rotation policy:** resolved and no-action findings rotate to
`docs/history/findings/FINDINGS_ARCHIVE.md` at batch close-out or during
findings-cleanup WPs; nothing is deleted. Every item uses an
`F-<context>-<N>:` heading (format: AGENTS.md "Finding-Writing Rules").
Read this file on demand -- when a task or PLAYBOOK entry references an
F-* ID or a P0/P1 item -- not as part of the standard bootstrap order.

---

## Severity Key

| Level | Meaning |
|-------|---------|
| **P0** | Fix before next deploy or next batch |
| **P1** | Next batch |
| **P2** | Scaling roadmap / future consideration |
| **Info** | Documented design choice, no action needed now |

---

## P0 -- Fix before next deploy

### F-B21-26: the Tailwind index dropped its page-entry motion

The WP-3 index migration stopped loading `global.css` and removed the
existing entrance motion without giving that behaviour a Tailwind-owned
replacement.

`templates/index.html` empties the `legacy_css` block. The old index therefore
lost the `.card` opacity entrance and the slower `#logo-wrapper svg` fade that
still live in `static/css/global.css`. Neither the deployed `origin/main` tree
at `1bf888f` nor the current PR #220 Tailwind source defines an equivalent
page-entry animation.

The PR #220 mode-copy transition is a different interaction. It cross-fades
the Top Albums and Heatmap copy after a mode change; it does not animate the
composition when the page first appears. Merging that PR would restore the
mode-copy transition but would not close this finding.

Restore a Tailwind-owned, opacity-only entrance for the index composition and
leave its final state visible under `prefers-reduced-motion`. Add a browser
check against computed animation state so a stylesheet opt-out cannot remove
the behaviour silently again.

The deployed Adobe font faces loaded during the same browser comparison. The
visible type-scale difference is the older production calibration already
owned by F-B21-24 and corrected in the undeployed PR #220, not evidence of a
new font-loading defect.

Status: resolved locally; deploy before the next production release.
Source: owner report and production/browser differential, 2026-08-28.

---

### F-B21-28: cached heatmap completion snaps from loading to a fully drawn result

When a saved heatmap job is already complete, the client sees 100 percent,
builds the complete result, hides the loading stage, and starts three nested
result fades in the same turn. The reader receives no painted handoff and the
whole screen appears at once. The loading phase also duplicates the `Pages
fetched` stat's page count, and its later detail claims "Building one day at a
time" after aggregation has already happened.

Keep the determinate hairline driven by the backend percentage, make the
stat the only page-count presentation, and crossfade exactly one prepared
result root with the loading stage. Use opacity and transforms only; retain a
motion-free direct result for reduced-motion readers. Replace the normal
loading route's `Back home` link with an honest `Cancel and return home`
control on both workflows. It returns home and does not cancel the background
job.

Status: resolved locally; deploy before the next production release.
Source: owner visual review and Impeccable performance finding, 2026-08-28.

---

### F-B21-29: wide-index form ignores the shared composition cap

At the wide-desktop breakpoint, `.index-form__inner` resets its 23.75rem cap
to `none` while the hero remains constrained. The form then fills the entire
right well instead of scaling as one composition, producing the owner-reported
oversized card and unstable side gutters. The shared header uses 44px page
links inside a 68px bar with narrow inter-link gaps, making the desktop
navigation feel cramped at browser zoom.

Restore the scaled form cap and centre it in symmetric inline padding. Give
the desktop header links and theme control a 48px target inside a taller bar
with one consistent sibling gap. Do not apply the hero scale to the header or
change the compact mobile shell.

Status: resolved locally; deploy before the next production release.
Source: owner browser review, 2026-08-29.

---

### F-B21-30: unmatched report describes zero rows as a populated exclusion list

The unmatched route passes `total_count=0` correctly, but its template always
states that albums were found and did not match the filter. The following
total of zero contradicts that claim and makes a successful no-unmatched state
look like a backend error.

When the count is zero, render a direct no-unmatched state and retain the
search settings plus existing navigation actions. Do not change the route,
the API, or the job's unmatched payload; this is a presentation condition.

Status: resolved locally; deploy before the next production release.
Source: owner browser review, 2026-08-29.

---

### F-B21-27: private Last.fm profiles start jobs they cannot complete

The index validates only `user.getinfo`, which may confirm that a Last.fm
account exists while its recent listening remains private. The later
`user.getrecenttracks` call returns Last.fm error `17` with HTTP `403` for
that privacy setting. The heatmap then presents a misleading zero-scrobble
state after it has already started work.

Preflight `user.getrecenttracks` with `limit=1` during username validation.
Classify exactly error `17` / `403` as a private profile, tell the reader to
make recent listening public, and prevent submission. Enforce the same result
in both start routes; other failed responses remain service failures rather
than privacy claims. Do not reject a public profile simply because it has no
listening history.

Status: resolved locally; deploy before the next production release.
Source: owner report and Last.fm API response classification, 2026-08-28.

---

## Resolved this batch

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

### F-B21-35: the proposed scale height guard ignored root-font enlargement

Task 2's fixed 673px natural-height denominator would not follow its rem-sized
content when the reader enlarged the root font.

The plan now expresses the measured denominator as 42.0625rem and requires
enlarged-root browser validation. Production replacement remains Task 2.

Status: resolved in the plan, 2026-09-04.
Source: late PR #221 review thread 3938613711.

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

## P1 -- Next batch candidates

### F-B21-36: heatmap loading repeats context and reserves hidden stat columns

The loading detail repeats the active phase, the lone page stat occupies the
left third of a three-column grid, and the parameter summary adds rocket-scale
copy that does not help the current wait.

Status: open; owner screenshot corrections assigned to Task 4.
Source: annotated owner heatmap-loading screenshot, 2026-09-04.

### F-B21-33: heatmap progress can apply stale responses and mislabel failed pages

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

Status: open; owner-approved Task 4 prerequisite for accurate visible counts.
Source: owner-requested polling audit, 2026-09-04; current Last.fm callback,
heatmap worker and browser polling, plus reversed-response execution probe.

### F-B21-1: a failed event-loop setup leaks a job slot

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
code. The diagrams now state the limit instead of claiming the release is
unconditional.
Status: open. Source: PR #171 diagram verification, 2026-08-15.

### F-B21-2: three dormant Tailwind seams that WP-2 meets at once

WP-1 shipped the compiled Tailwind and daisyUI CSS, but no template consumes
it, so three defects sit dormant and the first migrated template hits all
three together.

**Nothing sets `data-theme`.** daisyUI keys both themes on that attribute.
The live control was `body.classList.toggle('dark-mode')` in
`static/js/theme.js`, which no daisyUI rule reads. A migrated template
therefore renders the light theme in both modes. `BATCH21_DEFINITION.md` WP-2
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
`BATCH21_DEFINITION.md` WP-2 moves the Bootstrap link into a per-page block
so each template loads exactly one framework stylesheet. That removes the
collision rather than re-ordering it, and it supersedes the cascade-layering
approach this finding first proposed. This is a cascade-ordering defect,
distinct from the CDN-provider split in F-B20-3, which Batch 21 closes by
removing Bootstrap at WP-8.

Nothing is broken in production today, which is why WP-1's gates passed over
all three.

**Resolved by WP-2 on 2026-08-23.** All three seams are closed. `theme.js`
dual-writes `data-theme` on `<html>` and `.dark-mode` on `<body>`, and an
inline script in `base.html` sets the attribute before first paint. Setting
it always also stops the `:root:not([data-theme])` rule matching, which
settles the `prefersdark` seam. The Bootstrap link and `global.css` moved
into a per-page `legacy_css` block, so each page loads exactly one framework
stylesheet and the two frameworks never meet. The frontend gate asserts all
three, and `tests/test_template_shell.py` asserts the stylesheet rule for
every page.
Status: resolved (Batch 21 WP-2, 2026-08-23). Source: WP-1 final review,
2026-08-20.

### F-B21-3: 115 dependency advisories, and unused packages ship to production

The Quality Gate's `pip-audit` step reported `Found 115 known vulnerabilities
in 12 packages` (run 32444711411, 2026-08-21). The step is
`continue-on-error: true` in `.github/workflows/test.yml`, so the gate stays
green and the count reaches nobody. That disposition is deliberate and is
recorded in `AGENT_NOTES.md`; the disposition is not the problem, the number
is. Nobody reads a green check.

**Unused packages ship to production.** The Dockerfile installs
`requirements.txt`, and that file reads like a `pip freeze` dump: it pins
developer tooling (`virtualenv`, `distlib`, `filelock`, `platformdirs`)
beside real runtime dependencies. Six packages are imported nowhere in
tracked Python: `pypdf`, `pdf2image`, `pillow`, `virtualenv`, `ipinfo`,
`cachetools`. `pypdf` alone carries seven of the advisories. All six
entered in the initial `0ea2313` "Fresh start" commit rather than alongside
any feature, which fits a `pip freeze` taken from a wider environment.

The PDF packages are not the JPEG export, which is entirely client-side --
`static/js/results.js:178-266` uses `html2canvas` and
`canvas.toDataURL('image/jpeg', 0.95)`, and no server-side image or PDF code
exists. Poppler *is* installed on the owner's development machine, so
`pdf2image` could run there; it cannot run in production, because the
`Dockerfile` is a bare `python:3.13-slim` that installs no system packages at
all. Confirm the local workflow before removing them.

**The advisories that matter here sit on the outbound path** to Last.fm and
Spotify. `requests` 2.32.3 can leak `.netrc` credentials on crafted URLs
(PYSEC-2026-1872, fixed in 2.32.4). `urllib3` 2.2.3 forwards headers across
origin on redirect and decompresses without bound (PYSEC-2026-141, -1994,
-1996, -1998). By contrast the `werkzeug` `safe_join` advisories are
Windows-only and `send_from_directory` is never called, so they are noise for
this deployment -- count them out before anyone reacts to the raw 115.

A shape, not a decision: split runtime from developer requirements, drop what
nothing imports, then upgrade the outbound HTTP libraries. Resolve the
dependency graph before removing anything -- `pillow` is plausibly present as
`pdf2image`'s dependency rather than on its own.
Status: open. Source: Quality Gate run 32444711411, 2026-08-21.

### F-B21-4: four screens where the design bundle contradicts itself

The design handoff imported to `docs/design/` carries two documents that
disagree. `docs/design/README.md` is canonical. `docs/design/reference/
audit-review.md` is a later second-pass critique, and it dissents on four
screens:

1. **Index hero -- DECIDED 2026-08-24 (owner), README wins.** WP-3 shipped
   the two-column split. Items 2, 3 and 4 stay open for WP-4, WP-5 and WP-7;
   do not close this finding on the strength of this one ruling.
   The README specifies a two-column `1.1fr 1fr` editorial
   split. The review calls it a generic SaaS landing layout applied to a tool
   whose users arrive to type a username and press go, and asks for a single
   centred column. It names this "the thing to challenge first".
2. **Loading signals.** The README specifies pinwheel, phase line, progress
   bar, three stats and a parameter tag row. The review counts that as five
   simultaneous progress signals and wants the pinwheel and phase line always,
   the bar only when the value is real.
3. **Results KPIs.** The README specifies three sidebar stat blocks. The
   review says two of them restate row 1 of the list, and only albums matched
   versus albums seen earns a card.
4. **Unmatched fix line.** The README sets it at 9px mono uppercase. The
   review says the most actionable text in the product is at the smallest,
   hardest-to-read size, and asks for 11px sentence case.

`BATCH21_DEFINITION.md` encodes the README's side on the first two: WP-3 says
"Editorial hero", WP-4 specifies the pinwheel, bar, phase label, four-KPI
strip and chip row together.

Item 2 has support inside the canonical bundle itself:
`docs/design/components/feedback/ProgressBar.d.ts` documents `value` as "Only
show it when the value is real; otherwise show the pinwheel alone." WP-4
should read that before deciding.

Status: open. The README is canonical and is the default, but it does not
automatically retire an audit finding. Each item is decided at the WP that
builds the screen -- WP-3 hero, WP-4 loading, WP-5 results KPIs, WP-7 fix line
-- and the decision is recorded on that WP's PLAYBOOK entry. Do not close this
finding by ruling on all four at once. Cross-references F-B21-2.
Source: design handoff import, 2026-08-21. Owner ruling on precedence the
same day. See `docs/design/RECONCILIATION.md`.

### F-B21-5: accessibility defects the design handoff does not resolve

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

Status: resolved 2026-08-25 by WP-3, all three items.

- The KPI labels take `var(--ss-text-muted)` in the rewritten
  `static/css/heatmap.css`; the `opacity: 0.5` text is gone. A real token was
  the prescribed fix and it is what shipped.
- The mode pills are `<button>` elements. A test asserts both, and asserts
  that no `role="button"` survives anywhere on the page -- the class, not the
  instance.
- The SMIL is gone from every mark on every page, animated from CSS keyframes
  with a reduced-motion guard.

Source: design handoff import, 2026-08-21.

### F-B21-6: the year gate reads host-local time, the fetch window reads UTC

`scrobblescope/routes.py` calls naive `datetime.now()` in three places:
`:135` (the `current_year` template global), `:302` (the results-page year
fallback), and `:436` (the submit-path validation gate). F-SWE-2 corrected
the same pattern in `orchestrator.py` and did not touch `routes.py`.

`:436` is the one with a consequence. It derives `current_year` from
host-local time and refuses any request where `year > current_year`. The data
window for an accepted year is then built in UTC at
`scrobblescope/orchestrator.py:70-71`. Gate and window now disagree by the
host's UTC offset, and the disagreement is observable only in the hours
around New Year:

- Host behind UTC: UTC has rolled over, the gate has not. A request for the
  new year is refused as out of range.
- Host ahead of UTC: the gate has rolled over, UTC has not. The request is
  accepted and the orchestrator builds a window entirely in the future, so
  the fetch returns nothing.

The two agreed before F-SWE-2, because both were naive. Fixing the window was
correct; it left the gate behind. **Do not fix this by reverting
`orchestrator.py`** -- move the three call sites to
`datetime.now(timezone.utc)`.

Production runs UTC, so this is a developer-host defect rather than a
production one. That is the reason it is not P0, not a reason to leave it.

Status: open. Found in the WP-1 review on 2026-08-20 and left unfiled; filed
and re-verified against the code 2026-08-22.
Source: WP-1 parallel review.

### F-B21-7: the toolchain integrity test patches away the code it names

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
Status: resolved (Batch 21 WP-2, 2026-08-23). Found in the WP-1 review on
2026-08-20 and left unfiled; filed 2026-08-22 after the mutation was run.
Source: WP-1 parallel review.
### F-B21-8: Tailwind scanned the whole repository, and no test would say so

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

Status: open for the missing local check; the `@source` scope itself is fixed
on `wip/batch-21`. WP-2 closes the remainder with the drift hook.
Source: PR #173 Quality Gate failure, 2026-08-22.
### F-B21-9: the findings-to-issues mirror is manual

Open findings were mirrored to GitHub issues #174-#215 on 2026-08-22. The
mirror ran once, from a script that was not committed.

Nothing keeps it current. A new finding does not open an issue. A resolved
finding does not close one. The two lists will drift.

This was deliberate, not an oversight. A sync script is code. It needs tests
and a work package. It did not belong in the documentation PR that created
the mirror.

What a sync needs: open an issue for each finding that has none, close the
issue when its finding resolves, and never write back to `FINDINGS.md`. The
file stays the source of truth. Issues are a read-only mirror.

Status: open, deferred on purpose. The owner accepted the drift on
2026-08-22 and asked that the work be recorded rather than done now.
Source: findings mirror, 2026-08-22.

### F-B21-10: every error page reports 400, whatever the real status

`templates/error.html` renders `{{ status_code|default('400') }}`, and not
one of the seven `render_template("error.html", ...)` call sites passes
`status_code`. Six are in `scrobblescope/routes.py` and the seventh is the
CSRF handler in `app.py`. So a 404 renders the literal text "400", a 500
renders "400", and the number is decorative rather than informative.

The two `app_errorhandler` registrations that would supply it live in
`routes.py`, which the batch contract reserves for WP-7. WP-2 migrated this
template's markup and deliberately did not change the default or the call
sites: doing so means editing a reserved file for a defect that predates the
migration.

The fix is to pass the real status at each call site, or to have the error
handlers supply it, and then to drop the `default('400')` so a missing value
fails loudly instead of lying quietly.

Status: open. WP-7 candidate, because it owns `routes.py`.
Source: WP-2 template migration, 2026-08-23.

### F-B21-11: the welcome modal covers the new header theme toggle

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

`BATCH21_DEFINITION.md` owner decision 2 already deletes the welcome modal at
WP-3, which removes the cause. Nothing is needed beyond that, but the
interaction is recorded so the deletion is not treated as cosmetic.

The frontend gate's theme-persistence check runs on a migrated page rather
than the index for this reason, and says so in its docstring.

Status: resolved 2026-08-25. WP-3 deleted the welcome modal, so nothing
covers the header on the index. The gate's theme-persistence check now runs on
every migrated page including `/`, and passes at both viewports, which is the
evidence rather than the deletion itself.
Source: WP-2 frontend gate run, 2026-08-23.

### F-B21-12: four pinned CI actions target a deprecated Node runtime

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

Status: open. Not urgent, but the deadline belongs to GitHub rather than to
this repository.
Source: PR #216 Quality Gate annotation, 2026-08-23.

### F-B21-13: bootstrap state lives in three files and only one is gated

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

- `BATCH21_DEFINITION.md` still said WP-2 was next after WP-2 shipped. WP-1's
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

Status: closed. DOC007 and the SESSION_CONTEXT renderer now call the same
finite, plan-aware next-WP helper. The CLI supplies the active definition's
planned headings, so absorbed gaps are skipped and an all-complete plan
terminates instead of hanging. DOC007 checks both the definition Status line
and PLAYBOOK's actual Next action bullet; a missing parseable claim remains
silent because it is a different defect. DOC008 applies the shared count
authority to the FINDINGS header with header-specific remediation, including
rotated per-batch logs and deterministic same-date batch ordering. Regression
tests cover agreeing, disagreeing, unparseable, absorbed-gap, all-complete,
header-scope, ambiguity and rotated-authority cases.
Source: PR #216 review round two, 2026-08-23.

### F-B21-14: the heatmap has no path to its data that is not colour

Every value in the grid is encoded once, as a fill. The only way to read a
day is a mouse hover: the cells are `<rect>` elements with no `tabindex`, so
a keyboard reader cannot reach any of them, and there is no table view.

The ramp itself is sound. Measured in OKLab, `rocket_r` runs strictly
monotonic in lightness from 0.13 to 0.884 in steps of 0.107 to 0.144 -- a
reader who cannot separate the hues can still separate the values, which is
what a sequential ramp has to do. The `dataviz` skill's validator fails it,
but that validator is scoped to categorical palettes by its own footer, and
lightness monotonicity is the right test here.

The defect is at the ends, against their own surface. `#f9d576` sits at
1.34:1 on the light frame and `#03051a` at 1.12:1 on the dark one, so the
busiest and quietest days both disappear into the background they are drawn
on. The ramp is fixed by the design contract, so the fix is relief and not
re-tinting: make the cells focusable and give each an accessible name, or
ship a table view, or both.

**Owner ruled this critical on 2026-08-24**, while noting that a sighted
mouse user sees no problem. Both halves of that are the finding: it is
severe for the readers it affects and invisible to everyone else, which is
why no review caught it and no gate can.

Status: open. Owner-ruled critical. Not scheduled to a work package.
Source: Batch 21 WP-3, `dataviz` skill pass, 2026-08-24.

### F-B21-15: the heatmap stays on the index page, and the split waits

WP-3 kept the heatmap form, wait panel and result frame on `index.html` and
extracted three Jinja partials instead of a page. The Batch 18 decision that
all states live on one page with no navigation still stands, and the owner
reaffirmed it on 2026-08-23.

The split only pays for itself alongside the deferred
`GET /heatmap/<username>` item under "Out of scope" in
`BATCH21_DEFINITION.md`. Without a route, a separate template cannot be
reached, linked or shared, and the frontend gate cannot see it either --
which is the same reason `LEGACY_PAGES` is empty.

The partials are the enabler. `templates/partials/_loading.html` is
framework-neutral and parameterised by id, so a future page can include it
without inheriting the index's script wiring.

Status: open, deferred. Do this with the GET route or not at all.
Source: Batch 21 WP-3, owner decision 3, 2026-08-23.

### F-B21-16: unmatched.html loads a Bootstrap bundle nothing on it uses

`templates/unmatched.html` pulls the Bootstrap JS bundle, and no `data-bs-*`
attribute on that page uses it. It may already be dead weight, in which case
WP-7 deletes a script tag rather than migrating a dependency.

Check rather than assume. The quick-view modal was deleted earlier in this
batch's plan and the bundle may simply have outlived it, but a `dropdown` or
`collapse` initialised from `unmatched.js` would not show up in a
`data-bs-` grep.

Status: open. WP-7 verifies before removing.
Source: Batch 21 WP-3 review of the remaining legacy pages, 2026-08-25.

### F-B21-17: a third of this batch's review comments were one fact written twice

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

Status: resolved 2026-08-25. Built as DOC009, DOC010 and DOC011 in
`scripts/docsync/declarations.py`, declared in `.docsync.toml`, stdlib
only. Each check was proved against the real defect it was built for by
restoring that defect and watching the check name it. On its first run,
before any test existed, it found `static/css/shell.css` stopping at
`max-width: 860px` where every other stylesheet stops at `859.98px` --
so both the mobile and desktop rules applied at exactly 860 -- and
`AGENTS.md` describing the integrity codes as DOC001-DOC006, four checks
after that stopped being true.
Source: Batch 21 WP-3 review analysis, 2026-08-25.

### F-B21-18: browser JavaScript has no automated unit coverage

There are more than 2,400 lines under `static/js/`, with no `package.json`,
test runner or `.test.js` anywhere in the repository.
`docs/SWE_AUDIT_CHARTER.md` also excludes `static/js/` from the audit, on the
grounds that Batch 21 rewrites it -- which is true, and leaves the rewritten
code as the only code in the batch that nothing checks at unit level.

Five of the first nineteen review comments in this batch came from that gap: a
validation message never cleared, a join year leaking between accounts, a
daily average rounding a positive total to zero, a form that submitted a
username it had already been told was invalid, and an export header laid out
for one screen width that painted over itself on another.

The export is the sharpest case. `saveHeatmapImage` draws a canvas by hand,
and it cannot be reached by any check as it stands: it needs a rendered
heatmap, so it needs live Last.fm data and a key, which does not belong in
CI.

Independent PR review confirmed the untested path is already off contract:
`docs/design/components/heatmap/HeatmapFrame.prompt.md` requires JPEG export
to render the desktop 53x7 grid at every viewport, while
`saveHeatmapImage()` serializes whichever mobile or desktop SVG is on screen.
Its own docstring records the deviation, but no owner ruling adds that
deviation to `docs/design/RECONCILIATION.md`. A pure render seam would make the
contract testable without a Last.fm key and let mobile export use the desktop
geometry without changing the visible page.

**Do not add Node.** The batch decided against a `package.json`, and the
repository already owns a JavaScript engine it paid for -- Chromium, through
the pinned Playwright runtime the frontend gate uses. The blocker is only
that every module is an IIFE with no exports. A guarded seam, exposing pure
functions when a test flag is set and nothing otherwise, would put
`rocketColor`, `countToNorm`, `computeStreak` and the export's header layout
under test for about eighty lines of harness.

DOM-state defects are a different half and are already being covered where
they bite: `check_validation_feedback` in the frontend gate was written after
this batch's stale-message defect and fails on both forms when the fix is
removed.

The two username validators are also duplicated state machines:
`static/js/index.js` owns the album version and `static/js/heatmap.js` owns the
heatmap version. Their success work differs, but request freshness, outage and
failure semantics do not. The independent review first found that only the
heatmap catch discarded a stale failed request. The sibling fix compared field
values in both consumers, and the final self-review found that still fails an
A-to-B-to-A sequence because the oldest and newest requests carry the same
text. Both now use request generations, with the browser gate holding the ABA
case. Centralise that shared base only after broader browser parity checks
cover both consumers; refactoring it before then would trade a demonstrated
shotgun-surgery bug for an unproved rewrite.

Status: open, and **scheduled**. The owner ruled on 2026-08-26 that this
becomes a work package of its own, sequenced before WP-5, and is not folded
into WP-4. Scope is the pure-function seam only -- `rocketColor`,
`countToNorm`, `computeStreak` and the export header layout -- on the
Chromium the frontend gate already owns. No Node, no `package.json`.

The timing is the reason for that position. WP-5 and WP-7 are the two
remaining JavaScript-heavy pages, so a seam built before WP-5 still guards
work this batch does; built at WP-8 it would guard nothing here. The DOM
half is deliberately excluded, because the frontend gate already covers it
where it bites -- 2026-08-26 is the worked example: a real pre-paint theme
defect was caught by a browser check reading `data-theme` under blocked
storage, which no unit test of a pure function could have seen.

Placing it needs care. `WP_SKIPPED_RE` and the DOC007 derivation read work
package numbers from PLAYBOOK Section 4 headings, and WP-6 is already
absorbed into WP-3, so the number this takes and how the definition records
it must be settled before the first commit rather than discovered by a red
gate.
Source: Batch 21 WP-3 review analysis, 2026-08-25. Scheduled by owner
ruling, 2026-08-26.

### F-B21-19: heatmap mobile and day-detail behaviour drifted from the design

Two canonical heatmap requirements have no ruling and do not match the PR:

- `docs/design/components/heatmap/HeatmapFrame.prompt.md` requires four
  stacked, season-labelled 13-week strips on a phone with the same cell size.
  `BATCH21_DEFINITION.md` and the WP-3 plan also say to keep the 14px cell.
  `renderHeatmapMobile()` instead chooses 10 to 28 columns and 18px to 28px
  cells from container width, producing one unlabelled sequential grid. The
  product README was rewritten to describe that implementation, but the
  reconciliation file has no owner-approved override.
- `docs/design/README.md` says hovering a day reveals what was played. The
  heatmap payload contains only `daily_counts`, and the tooltip renders only
  date plus count, so the client has no track detail it could reveal.

The export sibling is recorded under F-B21-18 rather than duplicated here.
The mobile requirement needs a product ruling before code: implement the four
strips, or explicitly override the canonical handoff. Day detail changes the
response contract and is a future-batch feature if the canonical requirement
stands.

Status: open. Owner decision required; not assigned to a work package.
Source: independent PR #218 specification review, 2026-08-25.

### F-B21-20: the Tailwind hook and commit procedure disagree on staging order

`AGENTS.md` requires `pre-commit run --all-files` to pass before any path is
staged. The `tailwind-css-drift` hook rebuilds `static/css/tailwind.css`, then
runs `git diff --exit-code` against the index. A correct source-and-output edit
therefore fails before staging for the same reason a stale output fails: both
make the generated file differ from the index. Rebuilding again does not
change that answer.

The hook passes at commit time after the source and generated output are
staged, which is the state its Batch 21 acceptance criterion describes. The
manual commit procedure demands the opposite state. This review had to run
all hooks with an exact-name staged candidate, compare the index tree before
and after, and restore the index afterward; otherwise the final gate could
never be green.

Do not silently reorder the repository-wide commit procedure or rewrite the
hook inside a UI review. The owner needs to choose one contract: stage named
paths before pre-commit, or make `--check` compare the freshly built bytes with
the bytes present before the build instead of comparing the working file with
the index. Either choice needs a regression test for an intentionally changed,
already rebuilt stylesheet.

Status: open. Owner decision required; not assigned to a work package.
Source: PR #218 final verification, 2026-08-25.

### F-B21-21: the index hero wordmark ignores the theme

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

Status: **resolved** 2026-08-26. `.index-hero__mark` joins `.site-header__mark`
on both declarations in `shell.css`, and the hero now measures ink `#1a1820`
light / `#f1ede4` dark, identical to the header. `.ss-mark` is not yet the
selector: `shell.css` loads after `global.css`, so a rule on the shared class
would also win on loading, results and unmatched, whose values differ and
which no gate can render. WP-8 makes that move when `global.css` retires.
`check_mark_follows_theme` in the frontend gate now fails if a migrated
wrapper is missed; reverting the fix reproduces the failure by name.
Source: owner review of the deployed merge, 2026-08-26. Verified in Chromium.

### F-B21-22: theme follows the system only until the toggle is first used

`templates/base.html` picks the pre-paint theme with
`saved === 'true' || (saved === null && matchMedia('(prefers-color-scheme: dark)').matches)`.
That is correct for a first visit. But the toggle is a two-state switch that
writes `'true'` or `'false'`, and `saved === null` is then never true again, so
one click permanently detaches the page from the system preference. There is no
way back to "follow the system" short of clearing site data.

Owner reported being served light while their system default is dark, which
this explains: a stored `'false'` from earlier review outranks the media query.
`theme.js` writes only on `change`, so nothing persists a value the reader did
not choose -- the mechanism is working, the model is missing a third state.

Remedy: store `'system'` as a third value and default to it, or drop the key
when the chosen state matches the system so the preference reattaches. Either
needs the pre-paint script and `theme.js` to agree, and a gate check that a
stored choice still survives a reload.

Status: open, low severity. Owner decision on whether a three-state control is
wanted before WP-8 retires the second theme write.
Source: owner review of the deployed merge, 2026-08-26.

### F-B21-23: the inline marks diverge from the design contract on colour

`docs/design/README.md` "Assets" specifies the two inline variants as
**theme-reactive: text `currentColor`, bars `var(--bars-color)`**. Neither
shipped asset does it. `templates/inline/scrobble_scope_lockup_inline.svg` and
`scrobble_scope_inline.svg` contain zero occurrences of `currentColor`; the
letterforms carry no fill rule at all and the bars are pinned by an embedded
`<style>` to a literal `#6a4baf`.

This is the real cause of F-B21-21, which was fixed at the symptom. Because
the asset does not react to anything, every wrapper that displays it has to be
named explicitly in a stylesheet, and the index hero was the wrapper somebody
forgot. The list will need extending again for every mark WP-4 through WP-8
adds, and the gate check added with F-B21-21 exists only to catch that.

Doing what the contract says removes the class. Give the letterforms
`fill="currentColor"` and the bars `stroke: var(--bars-color)`, then any
wrapper that sets `color` and defines that token gets a correct mark with no
selector naming it. The per-wrapper list in `shell.css` collapses to nothing.

Two reasons it was not done in the F-B21-21 fix. The assets are shared with the
four Bootstrap pages, which currently colour them through `global.css`
`.dark-mode`, and those pages render only from a POST with session state, so no
gate can show the result. And `--bars-color` is a `global.css` token while the
migrated pages use `--shell-accent`; the two carry different dark values
(`#9370DB` against `#b39dde`), so unifying the asset means first deciding which
value wins.

Status: open. Right shape for WP-8, alongside retiring `global.css` and the
second `.dark-mode` theme write. Doing it there makes one change instead of
three.
Source: F-B21-21 follow-up, 2026-08-26.

### F-B21-24: the index does not use large displays well

The owner runs a 1080p and a 1440p monitor and reports that dragging the window
to the larger one leaves too much whitespace: the content keeps its size and
the margins absorb the extra width.

PR #220 added a source-level viewport-scale path, the compact-height padding
rule, the 12px label floor, reduced capability-mark tracking, and the light
muted-text contrast. The source path did not ship usable proportional
composition scaling. The later owner-review layout, hierarchy, boundary,
loading-progress, and unmatched-empty-state work also remains incomplete. In
particular, the live source still uses the interim wide split and a centred
`23.75rem` form cap.

Measurement on 2026-09-01 named the cause. The formula divides window height by
the 1080px design viewport instead of by the composition's own 673px height,
and an unconditional `min()` then lets browser chrome discard the width term on
every real window. The browser gate missed it because `set_viewport_size` sets
the content box exactly, so the gate measured `2560x1440` -- a geometry no
maximised window has. Chromium and Firefox measured the same composition width
to within 0.1px at four window sizes, so this is not an engine defect and
Firefox evidence is not the acceptance condition. Realistic window geometry is.

`docs/superpowers/plans/2026-09-01-batch21-index-scaling-and-review-remediation.md`
is the sole acceptance specification for the reopened work. It records the
1080p comparison needed before any global header-density decision.

Status: reopened; owner-review remediation is planned, not implemented.
Source: owner large-display review, 2026-08-28; owner clarification and
measurement, 2026-09-01.

### F-B21-25: every gate runs at commit time, so the session is unguarded

The documentation integrity gate, the compiled-CSS drift hook and the test
suite all run through `pre-commit`. They work: each was mutation-tested on
2026-08-26 and each caught its defect with the right code. They also share
one blind spot.

**Nothing runs at session time or at filesystem time.** Deleting local
files, removing a worktree, deleting a branch and force-replacing its
remote produce no commit, so no gate is consulted. On 2026-08-25 a session
branched from `origin/main`, made three commits with no PLAYBOOK Section 4
entry, renamed the branch over the retained one and replaced its remote.
Every gate stayed green. A reviewer caught the missing entry, not a check.

Three causes, each fixable on its own:

1. **The worktree guard was wired to nothing.** It exits 1 on an ERROR
   diagnostic and 0 otherwise, so it was built to gate, but it appeared in
   no hook and ran only when somebody chose to run it.
2. **Bootstrap was self-referential.** The rule that says to read
   `AGENTS.md` lives in `AGENTS.md`. A session that does not open it never
   learns it should. `.claude/settings.local.json` carried a permission
   allowlist and no hooks at all.
3. **What was lost was gitignored.** `skills-lock.json` is still missing.
   Git protects tracked files; the workflow depends on untracked ones and
   nothing declares which of them matter.

**Two structural defects in `AGENTS.md` itself.** Its "Session Bootstrap
(in order)" section opens with two fast-path paragraphs that authorise
skipping bootstrap, placed above the numbered list, so a skim finds the
exemption before the obligation. And the file has accumulated origin
narrative: agents editing it explain why a rule came to be written, which
serves the editor and not the reader. A bootstrap ruleset is read cold and
under pressure. Rationale belongs in a finding or a PLAYBOOK entry; the
rule should state the intent and stop. This is the specific mechanism
behind the length problem, and it is narrower than `F-STYLE-1`.

**Partly closed on 2026-08-26.** The guard now runs as the
`worktree-alignment` pre-commit hook, verbose so lineage is visible on a
passing run, and **advisory**: it prints and never gates.

That last word was wrong twice before it was right. The hook first shipped
gating, on the claim that only WT002, WT007 and WT014 are errors. A PR #220
reviewer corrected it: eleven of the fifteen codes are errors -- WT001,
WT002, WT003, WT004, WT005, WT006, WT007, WT008, WT012, WT014, and WT009
inside a linked worktree. WT003 fires for any branch the active batch does
not name, and WT004 for the identical-tree divergence a rebase merge always
leaves, so the gating version would have refused every commit on a feature
branch and every commit after a merge until realignment. The owner ruled it
advisory on 2026-08-26: the problem was that the guard's output was
invisible, not that commits needed a new gate. `--advisory` carries that,
and a test asserts it exits 0 on an ERROR while the same run without the
flag still exits 1.

The claim was wrong because the severity check grepped two of the guard's
six modules and generalised. That is the same incomplete-sweep mistake
`AGENTS.md` names, made while writing this finding about mechanisms that
only hold in one place.

It is skipped in CI, and the reason is worth keeping: the
first push went red on `ERROR WT007`, because `actions/checkout` makes a
shallow single-branch clone with no `origin/main`, so the guard failed
closed on a base ref that is legitimately absent. The guard measures
developer worktree lineage and a runner has no worktree topology to
protect, so the step sets `SKIP: worktree-alignment` rather than fetching
a base ref to satisfy a check that would then measure nothing. The
failure is itself an instance of this finding: a check added without
asking where it runs, whose assumptions held on one machine only. A `SessionStart` hook injects branch, working-tree state,
guard codes and the machine-managed status block into every new Claude
Code session, so the state arrives without depending on effort level,
model, or the model choosing to read. The second virtualenv the allowlist
had been authorising is deleted.

Remaining, and not started: a declared manifest of untracked-but-essential
files, in the shape of `.docsync.toml` so the mechanism carries no
repository facts; the two `AGENTS.md` defects above; and an equivalent
entry point for Codex and Copilot, which have no session hook and for whom
the top of `AGENTS.md` is the only forcing function there is.

Status: partly closed. The remaining items need an owner ruling, because
two of them edit `AGENTS.md`.
Source: workflow review after the worktree retirement, 2026-08-26.

### F-DOCSYNC-6: known DOC001 and count-derivation boundaries

Cases the PR #169 review round confirmed and deliberately left unfixed
because each needs a design decision rather than a patch:
four-space indented blocks are still scanned for references, because the
canonical documents use that indentation for list continuations and
excluding it would silently disable DOC001 across much of AGENTS.md;
prose added after the last Section 4 entry is never reference-checked;
`cli.py` glob discovery is case-insensitive on Windows and case-sensitive
on Linux while candidate matching uses `re.IGNORECASE`; a live document
resolving outside the working directory raises `ValueError` rather than
the documented exit 2; and a file deleted on disk with the deletion
unstaged still counts as tracked.
Status: open. Source: PR #169 independent review.

### F-WORKTREE-3: guard boundaries outside the design decision table

Confirmed but unaddressed: between batches the guard skips every ancestry
check by design, which is exactly when the rebase-merge artifact appears,
so a genuinely diverged branch passes silently; WT010 never fires for a
detached dirty worktree, which returns WT012 alone; and
`missing_base_remediation` receives an already-labelled ref, so an unsafe
ref name renders as "the local base ref configured base ref".

The fourth item originally listed here -- `resolve_venv` deriving the primary
checkout from the common Git directory's parent -- was fixed in this PR's
round-2 remediation, which discovers the main working tree with
`git worktree list --porcelain` and passes it in. The remaining three are
unchanged.
Status: open. Source: PR #169 independent review.

### F-DOCSYNC-7: `_latest_test_count_from_entries` has no production caller

The bare-count wrapper lost its last production caller when the integrity gate
moved to `latest_test_count_authority`. It is now exercised only by its own
unit tests in `tests/test_docsync_logic.py`, which is the same condition that
led to `_cross_validate` being removed rather than kept.

Deliberately not removed in the review round that created the condition:
deleting it also rewrites eight test call sites, which is a refactor rather
than a review fix. Remove it and repoint those tests at
`latest_test_count_authority` in a hygiene pass.
Status: open. Source: PR #169 review round 5.

### F-WORKTREE-4: three guard files exceed their directory peer caps

Review remediation grew three files past the peer-size rule in the Proposal
and Design Rules. Measured, with the pre-existing peer that sets each cap:

| File | Lines | Peer cap |
|------|-------|----------|
| `scripts/dev/_worktree_guard_inspection.py` | 256 | 236 (`scripts/dev/dev_start.py`) |
| `tests/scripts/dev/test_worktree_guard_venv.py` | 270 | 184 (`tests/scripts/dev/test_dev_start.py`) |
| `tests/scripts/dev/test_worktree_guard_inspection.py` | 192 | 184 (same) |

All three were within their caps before the review rounds -- inspection was
217, then 227 -- and crossed while fixing confirmed defects. Splitting them
was considered and declined by the owner: the rule exists to prevent
unmaintainable monoliths, none of these approaches that, and restructuring
files mid-review invites another round of inventory drift for no
maintainability gain. Recorded rather than fixed so no document claims a
compliance that does not hold.

Revisit when any of these files next changes substantially; the natural seam
in the collector is Git/topology collection versus diagnostic orchestration.
Status: open (accepted deviation). Source: PR #169 review round 4.

### F-B20-2: orchestrator.py second-pass decomposition (promoted from F-B18-1)

`scrobblescope/orchestrator.py` (916 lines) mixes album workflow, Spotify
batch processing, error mapping, progress tracking, and result assembly.
Now that `heatmap.py` provides a second pipeline, extract the shared
patterns (event loop setup including the win32 Proactor guard, progress
mapping, error guards) into a common module and split the orchestrator
into pipeline / processing / result-shaping modules. Also on the README
roadmap; absorbs F-B18-7. Status: open. Source: Batch 18 audit.

### F-B20-3: Bootstrap loads from two CDN providers

`base.html` loads Bootstrap CSS from cdnjs while `index.html` loads the
JS bundle from jsdelivr; other pages use cdnjs. The original remedy
(consolidate to one provider before a Bootstrap 5.1 -> 5.3 upgrade) is
dead: Batch 21 removes Bootstrap entirely and resolves the split by
elimination (`BATCH21_DEFINITION.md` WP-8 "closes F-B20-3").
Status: open; closes at Batch 21 WP-8. Source: F-B19-4 owner review.

### F-B20-4: UI overhaul (driven by owner audit)

Scope, locked decisions, and acceptance criteria live entirely in
`BATCH21_DEFINITION.md` (active batch) -- this entry is a pointer, not a
second copy. Status: in progress (Batch 21 active, WP-0 done).
Source: owner audit (UI Audit v3) + F-B19-4 owner review.

### F-B18-11: heatmap Last.fm page fetch is rate-limit bound

Fetch time is bound by page count and the shared 10 req/s throttle
(2026-05-16: 103 pages, 10.9s vs a 10.3s floor; fetching is already
concurrent at `limit=200`). Options: heatmap-specific caching,
progressive rendering, or a higher rate limit (not recommended). Status:
open; no fetch-speed work scheduled. Source: Batch 18 audit + perf
session 2026-05-16.

### F-LOAD-1: concurrent-user UX when job slots are full

With all `MAX_ACTIVE_JOBS` slots busy (default 5 since 2026-07-31; was
10), users get "Too many requests in progress" with no occupancy hint.
An "N/<cap> slots in use" hint would help, with the cap read from the
configured `MAX_ACTIVE_JOBS` at render time rather than written as a
literal -- deployments that override the env var must show their own
capacity, and a literal silently goes stale at the next default change
(it read "N/10" until 2026-07-31).
Status: open. Source: load testing 2026-03-04.

### F-AUDIT-1: dark-mode toggle placement on mobile

Fixed-position footer toggle may overlap content on small screens.
Batch 21 moves the toggle into the standing header bar; its acceptance
criterion on tap-target size names this finding as closed by that work.

**Resolved by WP-2 on 2026-08-23.** The footer bar is deleted and the toggle
now sits in the standing header. Both it and the wordmark link carry
`min-height: 44px` in `static/css/shell.css`, which is the floor the design
system sets. The control is a visible label over a visually hidden checkbox,
so it stays keyboard reachable and keeps its accessible name; on narrow
screens the label text is hidden visually only, never with `display: none`.
Status: resolved (Batch 21 WP-2, 2026-08-23). Source: AUDIT_2026-02-11.

### F-LOAD-2: no integration tests in CI

All tests mock dependencies; an in-process `/results_loading ->
/progress -> /results_complete` test is on the README roadmap.
Status: open. Source: load testing 2026-03-04.

### F-MAS-1: mocks may drift from API reality

No contract tests or recorded API fixtures; upstream format changes would
pass mocked tests. Status: open. Source: MULTI_AGENT_SWEEP.

### F-MAS-2: no automated JS tests

Theme toggle, export, polling, and heatmap rendering have no automated
coverage. Status: open. Source: MULTI_AGENT_SWEEP.

### F-DOCSYNC-1: ENTRY_BATCH_RE too loose

`parser.py` batch-tag regex can misroute entries whose titles contain
"Batch N" substrings; tightening needs backward-compat testing. On the
README roadmap. Status: open. Source: DOCSYNC_AUDIT Finding 6.

### F-MAS-3: test_docsync_logic.py covers several unrelated seams

One module holds WP collection, test-count authority, whole-sync
integration, log merging, archive splitting, dedup, and Section 3 parsing.
Splitting along those class boundaries stays worthwhile. The originally
suggested `cross-validate` seam no longer exists -- that helper and its
tests were removed on this branch. Count authority is now split across two
files rather than extracted from this one: `TestLatestTestCount` still holds
the unit cases here, while `tests/test_docsync_test_count.py` covers the
behaviour through `_sync`. Consolidating them is part of the same split.

No line count is quoted here deliberately: the figure in the original
finding went stale as soon as the file changed, and size was never the
defect. Compare against the largest peer in the directory when deciding
whether the split is due.
Status: open. Source: MULTI_AGENT_SWEEP.

### F-MAS-4: broad `except Exception` catches

17 instances across `scrobblescope/*.py` (recounted 2026-07-24; 14 at
the original sweep); narrow or add structured logging per exception
class. Status: open. Source: MULTI_AGENT_SWEEP.

### F-STYLE-1: repository prose is denser than it needs to be

The goal is writing that is easier to read, not conformance to a standard.
ASD-STE100 Simplified Technical English names the target well: short
sentences, active voice, one idea per sentence, lean docstrings that say what
a function does and why, and no coined compound terms where a plain phrase
exists. It is an example of the goal, not a standard this repository adopts.

**This is not a gate and cannot become one.** The ASD-STE100 dictionary is
licensed and unavailable here, so no agent can check anything against it, and
no automated check scores prose quality. Declaring it a rule would also
trigger anti-pattern 11 in `AGENTS.md`, which requires a claim to be applied
across the corpus in the commit that states it -- a sweep far larger than the
benefit. Treat this as standing guidance for text you are already editing.

Concrete instance: `AGENTS.md` carries the coined term "blast-radius"
hyphenated in two places, and the spaced phrase "blast radius" in one more.
Locate them by the term; the line numbers drift with every insertion above
them. Later agent sessions copy it from there. Replace it with the
plain phrase, such as "search the repo for other copies of the same claim",
when those lines are next edited for another reason.
Status: open (guidance, never a gate). Source: owner style direction,
2026-08-19.

### F-STYLE-2: Python style settings disagree, and Ruff is planned but unwritten

Three separate problems that one decision settles.

**Docstring convention.** Measured 2026-08-19 across tracked Python outside
`tests/` (38 files, via `git ls-files "*.py"` plus an `ast` walk of every
function, async function and class): 204 definitions, 171 carrying a
docstring (84%), and 4 using Google sections such as `Args:` or `Returns:`
(2%). Adopting Google sections everywhere is a 167-definition sweep across
the documented ones, plus 33 that carry no docstring at all. That size is why
this is a finding and not a rule. Re-measure before quoting these numbers.

**Line length.** `black` has no `[tool.black]` section in `pyproject.toml`,
so it wraps at its default 88. `.flake8` sets `max-line-length = 120`.
Nothing reconciles the two.

**A stale note.** `.flake8` still describes its five ignored codes as
temporary, for an incremental cleanup that has since finished.

Ruff is the planned replacement for black, isort, autoflake and flake8, as
part of a CI modernization, and it also settles the line-length
disagreement -- so do not open that as a separate question. The plan is not
written down anywhere it would be found: the only tracked traces are
`.ruff_cache/` in `.dockerignore` and one line in
`docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`. Defer the sweep; record
the decision.
Status: open. Source: root-hygiene side task, 2026-08-19.

### F-SWE-4: the production entrypoint never validates API keys

`config.ensure_api_keys()` (`config.py:37-40`) raises when any of the three
API keys is missing, and it is called only inside the `__main__` guard at
`app.py:140-145`. Production starts with `gunicorn app:app`
(`Dockerfile:15`), which imports the module rather than running it, so the
check never fires. Verified: with all three keys unset, `import app`
succeeds and serves, while `ensure_api_keys()` would have raised.

The same file gets the neighbouring case right. `_validate_secret_key` is
called from `create_app()` (`app.py:111`) and refuses to start in
production. One secret is checked at startup and three are not.

`spotify.py:26-27` is the only remaining guard for two of them, and it uses
`assert`, which `python -O` strips. Without the startup check a missing key
surfaces as a per-request failure, classified as an upstream outage.

Fix: call `ensure_api_keys()` from `create_app()`. One line, and it closes
two C cells in the audit matrix.
Status: open (P1). Source: SWE_PRINCIPLES_AUDIT.

### F-SWE-5: the two background entry points disagree about terminal job state

`heatmap_task` and `background_task` answer the same question two different
ways, and both answers are wrong.

`heatmap.py:218-221` catches every exception and reports
`lastfm_unavailable`. `_fetch_and_process_heatmap` has no inner handler, so
this is the only handler on the path and it fires for any failure at all.
Verified: a `ZeroDivisionError` raised inside the aggregation step reaches
the user as a Last.fm outage message, with `error_source: lastfm` and
`retryable: True`. The app blames a third party for its own bug and invites
a retry that will fail the same way.

`orchestrator.py:912-913` has the mirror-image gap: it logs and sets no job
state, so the job never reaches progress 100 and the loading page polls
forever. This half needs the inner handler at `orchestrator.py:851` to fail
first, which nothing observed can cause, so the finding is recorded rather
than treated as blocking. F-SWE-6 compounds it -- a polled job never
expires.

Fix: give each entry point a terminal state that names what actually
failed, using an `ERROR_CODES` entry for an unclassified internal error
rather than borrowing an upstream one.
Status: open (P1). Source: SWE_PRINCIPLES_AUDIT.

---

## P2 -- Scaling roadmap

### F-DATA-1: reissue editions collapse onto the original's cache row

`normalize_name()` strips `deluxe`/`edition`/`remastered`/`anniversary`
and seven more words from the album string, so
`"viagr aboys (Deluxe Edition)"` and `"viagr aboys"` both normalize to
`viagr aboys`. The `spotify_cache` primary key is
`artist_norm + album_norm`, so **both editions share one row** holding
whichever release populated it first, for the 30-day TTL. When the
reissue wins that race its `release_date` is served for the original.

Observed 2026-07-31: Viagra Boys "viagr aboys" (2025) appears under
`release_scope: same` for 2026, matching the JP deluxe released
2026-01-09, on an account that never played the deluxe.

The collapse is not a bug on its own -- it is what makes matching work
across Last.fm's inconsistent album strings, where the same record is
scrobbled as `Album`, `Album (Deluxe Edition)`, and `Album - Deluxe`
depending on the reporting client. Keying editions apart would fragment
one album into several leaderboard rows with split playcounts, which is
a worse defect than an occasional wrong year. Collapsing is correct for
*counting* and wrong for *dating*; the two need decoupling, not one
shared key.

Candidate fix (untested): keep the collapse for aggregation, but when
resolving `release_date`, select the **earliest** date among candidate
Spotify matches instead of whichever cached first. The original predates
its reissues by construction, and this approximates the "Original
Release Date" that Deezer's API team confirmed is a separate field from
the digital release date labels supply. No schema change required.

Rejected: a boolean `is_deluxe` discriminator. The stopword list has 11
entries that combine freely (deluxe, expanded, anniversary, JP deluxe),
so a boolean still collides variant-against-variant. Retaining the
stripped tokens as a variant tag would work but reintroduces the
fragmentation above.

Open questions, answerable by investigation rather than speculation:
1. Do the scrobbles themselves carry the deluxe title? Last.fm stores
   whatever album metadata the player reported, which is a second
   independent path to the same result.
2. Which other albums are affected? **Not answerable from the cache
   alone:** `(artist_norm, album_norm)` is the primary key
   (`init_db.py:42`) and the upsert overwrites the single stored
   `release_date`, so there are no sibling rows and no losing candidate
   dates to compare against. Detection requires re-running the Spotify
   search for each cached album and flagging rows whose stored date is
   later than the earliest candidate in the fresh result set, or
   cross-checking against an external original-release source
   (MusicBrainz, per the note below).
3. Can both a Latin-script deluxe and a JP deluxe surface at once? Only
   if the JP title carries Japanese characters -- NFKC preserves those,
   so it would not collapse; a Latin-script `(Deluxe Edition)` always
   merges to one row.

Note: Spotify exposes no original-release-date field. `release_date`
belongs to the matched release object, and `release_date_precision`
(`year`/`month`/`day`) only reports granularity. Disambiguation must
come from the search result set, the discarded `(Deluxe Edition)`
suffix, or `total_tracks`. MusicBrainz does carry original release
dates -- a lookup narrowed to that single field, cached, is far smaller
than the full-enrichment attempt abandoned in 2025.

Status: open (P2). Low user impact -- one recalled instance across ~14
years of scrobbles, and `release_scope: all` bypasses date filtering
entirely. Source: session 2026-07-31.

### F-DOCSYNC-2: STATUS block misreports current batch between batches

When a close-out entry (untagged `(Batch N close-out)` suffix) still sits
inside the CURRENT-BATCH markers, `renderer.py:85-86` falls back to
`last_completed + 1` even though the Section 3 parse correctly returns
the between-batches state. Transient: rotation self-corrects it when the
next batch's WP-0 entry lands. Fix candidates: prefer the between-batches
branch whenever the parse returns none, or make close-out tags parseable.
Status: open (P2). Source: PR #162 review round 4.

### F-DOCSYNC-3: close-out entries route to the monolith, not the batch log

Close-out headings use a `(Batch N close-out)` suffix that `ENTRY_BATCH_RE`
does not recognize as batch-tagged, so rotation routes them into the
untagged monolith archive instead of `docs/history/logs/BATCHN_LOG.md`.
Affects only close-outs written with that suffix: BATCH19_LOG.md and
BATCH20_LOG.md lack their close-out entries (both sit in the monolith),
while Batch 18's close-out was tagged `(Batch 18 WP-5)` and routed
correctly. Per-batch history is therefore incomplete for the affected
batches without a monolith grep. Fix belongs in a docsync
WP together with F-DOCSYNC-1/F-DOCSYNC-2 (make close-out tags parseable,
then one-time re-route of the existing close-out entries); hand-retagging
machine-rotated archive content was declined in PR #162 round 3 and again
in PR #163 round 3 on the same point-in-time principle.
Status: open (P2). Source: PR #163 review round 3.

### F-MAS-5: in-memory JOBS dict limits horizontal scaling

Process-local dict breaks polling under multiple workers/machines;
migration path is Redis or a Postgres-backed job table.
Status: open (P2). Source: MULTI_AGENT_SWEEP.

### F-MAS-6: Celery/Redis RQ for task queue

**Owner decision:** out of scope until features complete.
Status: open (P2, owner-gated). Source: MULTI_AGENT_SWEEP.

### F-MAS-7: process-local Spotify token cache

Redundant refreshes under multiple workers; acceptable at current scale.
Status: open (P2). Source: MULTI_AGENT_SWEEP.

### F-MAS-8: REQUEST_CACHE growth with always-on machines

Cleanup is opportunistic (at job start); TTL mitigates, does not cap.
Status: open (P2). Source: MULTI_AGENT_SWEEP.

### F-SWE-3: a Spotify server error bypasses the configured retries

`spotify.py:67-68` returns `(None, None, True)` for every non-200, non-429
response, and `is_done=lambda t: t[2]` treats that `True` as terminal. A 500
or 503 therefore ends the attempt loop after one try, while
`SPOTIFY_SEARCH_RETRIES` is set to 3 -- verified by running it. The retries
only ever fire for 429. `fetch_spotify_album_details_batch` has the same
shape at `spotify.py:129-132`.

The consequence is narrow: an album that _is_ on Spotify can be recorded as
unmatched when a second attempt would have found it.

**Rescoped by the owner, 2026-08-20, and the correction is worth keeping.**
The audit first filed this as a user-facing mislabelling -- `spotify.py:75`
returns the same value for a genuine empty result, so
`orchestrator.py:250-262` records the album with the reason
`No Spotify match`, and the report treated that label as wrong. It is not.
Thousands of Last.fm-scrobbled albums genuinely have no Spotify release, so
the label is accurate for the ordinary case and what the user sees is
correct. What survives is the defect above -- configured retries that never
run -- which is a smaller thing than the audit claimed. Severity drops from
P1 to P2 and the finding moved from the P1 section to this one.

The related UI need -- the unmatched modal and page should say plainly that
an album had no Spotify match -- is already Batch 21 WP-7 scope
(the `WP-7 -- Unmatched page + reason_code` section of
`BATCH21_DEFINITION.md`: the `no_spotify_match` reason code and two
reason cards with human copy). It is not extra work and is not tracked here.
Status: open (P2). Source: SWE_PRINCIPLES_AUDIT, rescoped by owner review.

### F-SWE-6: reading a job renews its TTL, so a polled job never expires

`get_job_progress`, `get_job_unmatched` and `get_job_context` each write
`updated_at` (`repositories.py:163`, `:175`, `:199`) while their docstrings
promise only to return a copy. `cleanup_expired_jobs` reaps on that same
field, so every `/progress` poll renews the lease.

Verified: a job backdated to three hours old, against a two-hour
`JOB_TTL_SECONDS`, survives `cleanup_expired_jobs` after a single read,
while an identical job that was never read is reaped. A browser sitting on
the loading page therefore keeps its `JOBS` entry alive indefinitely, which
matters most for a job whose thread died without setting a terminal state
(F-SWE-5).

Touch-on-access may well be intended -- results should not vanish while a
user is reading them. Nothing says so. Either document the side effect in
the three docstrings and in the `JOB_TTL_SECONDS` comment, or stop writing
from a getter and refresh the lease explicitly where it is wanted.
Status: open (P2). Source: SWE_PRINCIPLES_AUDIT.

### F-SWE-7: utils.py holds five unrelated concerns

One 346-line module carries API rate limiting (`utils.py:29-121`), aiohttp
session construction (`:155-188`), an in-memory response cache
(`:192-242`), duration formatting for display (`:245-283`) and a generic
async retry loop (`:286-346`). Nothing binds them together except the file
name, and `utils` is the name that accretes.

Each function is individually clean, which is why SRP grades B while SoC
grades C. The cost is discoverability: the response cache that F-MAS-8
tracks lives in the same file as `format_seconds`, and a reader looking for
either has no reason to look here.

A split into rate limiting, HTTP and caching, and formatting is a sibling
of the F-B20-2 orchestrator decomposition and belongs in the same batch as
it, not before Batch 21.
Status: open (P2). Source: SWE_PRINCIPLES_AUDIT.

---

## Info -- Design decisions (no action needed)

### F-LOAD-3: in-memory REQUEST_CACHE is intentional

Avoids re-fetching Last.fm on re-searches; clears on machine sleep.
Status: standing design decision. Source: load testing 2026-03-04.

### F-LOAD-4: Spotify cache TTL is ToS-compliant

Hits do NOT refresh `updated_at`; 30-day expiry from last API call.
Status: standing design decision. Source: cache verification 2026-03-04.

### F-LOAD-5: pre-slicing reduces Spotify API load

Playcount filter + 500-album playtime cap applied before cache lookup.
Status: standing design decision. Source: load testing 2026-03-04.

---

## Deferred / future-batch candidates (Batch 18/19 audits)

One-line cross-references; detailed bodies live in pre-Batch-20
`FINDINGS.md` (git history before `494f2c7`) or the `docs/history/`
audits; 2026-03-04 load-test data is in the findings archive.

- F-B18-1: orchestrator monolith -- promoted to F-B20-2 above.
- F-B18-2: JOBS dict lacks TypedDict/dataclass annotations.
- F-B18-3: `loading.js` album messaging; extract shared polling utility
  if a third feature emerges.
- F-B18-4: `_check_user_exists` creates a throwaway event loop per call.
- F-B18-5: inline SVG payload growth; lazy-load or sprite if more added.
- F-B18-7: duplicated win32 event-loop guard -- absorbed into F-B20-2.
- F-B18-10: heatmap + album jobs share the 10 req/s throttle (by design).
- F-B18-12: mode pills differ in width (no `min-width` on `.mode-pill`)
  -- RESOLVED 2026-08-25 by Batch 21 WP-3. They are equal-width `<button>`
  elements in a two-column grid, which also closes the `span[role="button"]`
  item in F-B21-5.
- F-B19-3: last.timer aggregate endpoints are not a drop-in heatmap
  speedup; future perf experiments listed in the archive.
- F-B19-4: front-end UI audit notes -- basis of `BATCH21_DEFINITION.md`.

---

## Feature preparation notes

### F-FEATURE-1: top songs feature

Rank most-played tracks for a year (separate task type + loading/results
flow). Status: deferred; on the README roadmap. Source: owner roadmap.

- F-FEATURE-2: listening heatmap -- shipped in Batches 18/19, archived;
  perf follow-ups continue as F-B18-11.

---

## Source documents

- `docs/history/reports/DOCSYNC_AUDIT_2026-02-25.md` -- 11 findings, detailed code refs
- `docs/history/reports/AUDIT_2026-02-27_MULTI_AGENT_SWEEP.md` -- Full architecture sweep
- `docs/history/reports/AUDIT_2026-02-11_IMPLEMENTATION_REPORT.md` -- Earlier audit
- `docs/history/reports/AUDIT_2026-01-10.md` -- Rate limit regression audit
- `docs/history/findings/FINDINGS_ARCHIVE.md` -- Rotated resolved/no-action items
- Agent memory: load-test-findings.md (not a repository file) -- raw load
  test data and analysis
