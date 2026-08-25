# Batch 21 WP-3 Implementation Plan: the index page

**Goal:** Migrate `templates/index.html` and everything on it from Bootstrap
5.1.3 to Tailwind v4 + daisyUI, delete the welcome modal and the Bootstrap
popovers, and close the remaining SMIL accessibility defect across all four
pages that carry the wordmark.

**Architecture:** Strangler migration, one page at a time. `base.html` carries
Bootstrap and `global.css` as the default body of its `legacy_css` block; a
migrated page overrides that block with an empty one and loads
`static/css/tailwind.css` instead. `error.html` is the shipped example. The
index is the second page to migrate and the first large one.

**Tech stack:** Flask + Jinja2, Tailwind CSS v4 (standalone CLI, no Node
project), daisyUI v5 restricted to nine components, Adobe Fonts kit `rwy8ghw`,
Playwright + Chromium for the frontend gate.

---

## Read this first if you have no context

This plan is written to be executed by any agent, not only the one that wrote
it. Everything you need is in tracked files.

**Bootstrap the session** in the order set by `AGENTS.md` "Session Bootstrap":
`AGENTS.md`, then `PLAYBOOK.md` Sections 3 and 4, then
`BATCH21_DEFINITION.md`, then `.claude/SESSION_CONTEXT.md` Sections 1 and 2,
then `AGENT_NOTES.md`. Open `FINDINGS.md` when a task names an `F-` ID.

**The design contract.** `docs/design/README.md` is canonical.
`docs/design/RECONCILIATION.md` is the override list; read it with the README,
never instead of it. Component specs are under `docs/design/components/`. Each
task below names the section to read **before** building, not after.

**The environment.** This is a linked worktree. Run
`python scripts/dev/check_worktree_alignment.py` first and use the qualified
tool paths it prints for every later command. Do not create a second
virtualenv. `md5sum`, `sha256sum`, `xargs` and `grep` are not on PATH; use
`Get-FileHash` and `rg`.

**Four facts that are easy to get wrong.**

1. `@theme static` in `static/css/tailwind.src.css` is load-bearing. Tailwind
   v4 emits a theme variable only when a generated utility uses it, so a token
   read only by handwritten CSS gets pruned. An undefined `var()` with no
   fallback then voids the whole declaration, silently.
2. `pre-commit run --all-files` does not see untracked files. Run
   `git add -N <path>` on every new file, or `black` aborts your commit.
3. `git diff` on `static/css/tailwind.css` proves only that nobody hand-edited
   it, not that a rebuild reproduces it. The `tailwind-css-drift` hook
   rebuilds then diffs, so an honestly rebuilt but unstaged file reports as
   drift. Stage it.
4. Cite `AGENTS.md` and `static/css/tailwind.css` by rule or block name, never
   by line number. Both have moved under citations four times this batch. That
   is `F-STYLE-1`.

---

## Rules that apply to every task

- `AGENTS.md` "Commit Rules" governs commit format. Conventional Commits,
  imperative subject, no trailing period, subject and body wrapped at 72
  characters. **No `Co-authored-by` trailer.** Never `git add -A` or
  `git add .`; stage paths by name. Never `--no-verify`.
- Write plain English. Short sentences, active voice, one idea each. This
  applies to commit messages, log entries, findings and code comments.
- ASCII only in tracked Markdown outside `docs/design/`. Use `--`, not an
  em-dash. Where this plan writes `>=`, the rendered UI copy uses the U+2265
  glyph, which `docs/design/README.md` "Content rules" requires.
- Every commit runs, in this order:

```
pytest -q
pre-commit run --all-files
python scripts/doc_state_sync.py --check
python scripts/dev/frontend_gate.py
```

- **Prove every new guard can fail.** Mutate the thing it protects, watch the
  test go red, revert. WP-2 caught two vacuous assertions this way.
- **Before deleting a container, grep for what it styled.** WP-2 removed
  `.page-footer-bar` and silently unstyled `#back-to-top`, which has no CSS of
  its own anywhere.
- Do not push and do not open a pull request without explicit owner
  instruction.

---

## Decisions already made

Do not re-open these. Each is recorded with its source.

| Decision | Ruling | Source |
| --- | --- | --- |
| Scope | Full index migration, including the heatmap form, loading panel and result frame | Owner, 2026-08-23 |
| WP-6 | Absorbed into WP-3. Every WP-6 deliverable is on this page; there is no `heatmap.html` | Owner, 2026-08-23 |
| Separate heatmap page | Not built. Extract partials instead and file the split as a finding | Owner, 2026-08-23 |
| Hero layout | README two-column `1.1fr 1fr`. This rules `F-B21-4` item 1 | Owner, 2026-08-23 |
| Mode pills | WP-3 rebuilds them as `<button>` and equalises width, closing `F-B18-12` | Owner, 2026-08-23 |
| SMIL | Stripped from the pinwheel and the full wordmark, covering all four pages | Owner, 2026-08-23 |
| Username validation | Keep `/validate_user`. The README's ">2 characters" is prototype simplification | Owner, 2026-08-23 |
| Loading partial | Built here; WP-4 adopts it into `loading.html` | Owner, 2026-08-23 |
| Heatmap cell geometry | Keep the 14px cell. Take the README's gap: 2px desktop, 1px mobile. Radius 2px already matches | This plan, resolving `RECONCILIATION.md` section 7 |
| `--heatmap-empty` | Take the README values `#e8e2d6` light, `#262230` dark | `RECONCILIATION.md` section 7, which rules the README wins on this token |
| `rocket_r` ramp in CSS | Mirror `--rocket-5` only. `static/js/heatmap.js` stays the owner of all seven stops | This plan. The absorbed WP-6 item asks for one accent, so one stop is all that is needed |
| Mobile stylesheet | No separate Bootstrap sheet for mobile. Instead the frontend gate grows a 390x844 pass and a touch-target check, in Task 13 | Owner, 2026-08-24. Reasoning under Task 13 |

**Do not re-open the 16px mobile input.** `static/css/index.css` forces
`font-size: 16px` on mobile inputs to stop iOS auto-zoom, and
`docs/design/components/forms/Input.prompt.md` mandates it. The README's
9.5-13px mono sizes are desktop values. Keep the override in the rewrite.

**Do not add a tenth daisyUI component.** The `@plugin` block in
`static/css/tailwind.src.css` includes exactly nine: `button, card, modal,
toggle, input, select, tab, toast, alert`. This page needs `card`, `input`,
`select`, `button` and `tab`. The stepper, the disclosure and the segmented
control are hand-built.

---

## Commit map

Six commits. Each is separately reviewable and separately revertible.
Documentation leads, because `AGENTS.md` "Commit Rules" requires the doc
update before the gate that checks it.

| Commit | Subject | Tasks |
| --- | --- | --- |
| 1 | `docs(batch): fold WP-6 into WP-3 and record the index scope` | 1, 2 |
| 2 | `fix(a11y): strip SMIL from the pinwheel and the full wordmark` | 3, 4 |
| 3 | `feat(ui): add the index page tokens to the tailwind theme` | 5 |
| 4 | `feat(ui): rebuild index page on tailwind` | 6-12 |
| 5 | `test(ui): extend the frontend gate and shell tests to the index` | 13, 14 |
| 6 | `docs(state): record WP-3 and close three findings` | 15, 16 |

**A page migration is atomic.** The moment `legacy_css` is emptied, Bootstrap
and `global.css` both leave the page. There is no half-migrated index, which
is why commit 4 is large. Commits 1 to 3 exist to take out of it everything
that does not have to be in it.

---

## Progress -- read this before starting anything

Kept current by hand as each commit lands. PLAYBOOK Section 4 stays empty of
a WP-3 entry until commit 6, because DOC007 derives the next work package
from it and an early entry would claim WP-3 is finished. So this section is
the only record of where inside WP-3 the work stands.

| Commit | State | SHA |
| --- | --- | --- |
| 1 -- record the scope | done | `03ce1f8` |
| (unplanned) lockup alignment | done | `46fe475` |
| 2 -- strip the SMIL | done | `b17a741` |
| (unplanned) plan amendment | done | `89a5da2` |
| 3 -- the tokens | done | `a1e607b` |
| 4 -- rebuild the page | done | `b1374b1` |
| (unplanned) one wordmark | done | `e7ce039` |
| (unplanned) hidden collision | done | `fa381d2` |
| (unplanned) design refresh | done | `6e3f0ad` |
| (unplanned) hero scale, mobile | done | `c0dadb0` |
| 5 -- extend the gates | done | `9ca9598` |
| 6 -- record it | **next** | -- |

Nothing is pushed. The owner has not authorised a push or a pull request.

**Fifteen deviations so far. Commit 6 must record all fifteen honestly.**

1. **The lockup was realigned**, which the plan never scoped. Removing the
   tagline in WP-2 left the letterforms floating about 13 units above the bar
   baseline. `templates/inline/scrobble_scope_lockup_inline.svg` now carries
   the design project's own static transform on `#logo-text`, all five bars
   end at exactly 63.50, and the viewBox is `0 0 453 74`. Owner ruled the
   frame on 2026-08-24. `docs/design/RECONCILIATION.md` section 10 has it.
2. **`tests/test_routes.py` was edited**, which the plan did not list. It
   asserted `animateTransform` as a stand-in for "the pinwheel is here", and
   stripping the SMIL broke it.
3. **Task 13 grew a mobile viewport pass**, owner decision 2026-08-24. See
   the decisions table and Task 13.
4. **A page background rule was added to `static/css/tailwind.src.css`.**
   daisyUI's `rootcolor` base module emits nothing while `themes: false`, so
   no rule set a background on `html` or `body` and a migrated page took the
   browser's own canvas. In dark mode that is a cool grey the batch exists to
   remove, arriving behind the gate that forbids it. Fixed for every migrated
   page, not just the index, because the cause is shared.
5. **Four more tokens landed in commit 4**, not commit 3:
   `--ss-surface-card`, `--ss-surface-sunken`, `--heatmap-surface` and
   `--ss-bad`. The design has three surfaces and daisyUI's base ramp matches
   only two of them, differently in each theme. Task 14 should add all four
   to `INDEX_TOKENS`.
6. **The daisyUI component classes were dropped from the index.** The plan
   expected `card`, `input`, `select`, `button` and `tab`. The design fixes
   radius, height, family and colour for every control, so each daisyUI class
   was fully overridden wherever it appeared. `error.html` still uses them.
7. **The Info button is deleted, not rebuilt as a small about panel.**
   `BATCH21_DEFINITION.md` decision 2 says it becomes one, but the design's
   IndexScreen has no Info control and the hero plus the three capability
   marks now carry what the modal said. Owner ruled it on 2026-08-24.
8. **The plan's one expected red does not happen.** Task 12 step 8 says
   `check_stylesheet_isolation` fails between commits 4 and 5 because `/` is
   still in `LEGACY_PAGES`. It does not: that check counts framework
   stylesheets rather than naming which framework a page should carry, so a
   page that swaps one for the other stays green. Commit 4 is green on all
   four gate commands. The index is simply still outside `check_theme_tokens`
   and `check_fonts` until Task 13 moves it.
9. **The header wordmark is hidden on the index** (`e7ce039`). The header
   carries the lockup on every page and the hero carries it again, about
   60px apart. Owner ruled the header must not repeat the asset. The rule
   lives in `static/css/index.css` with a pointer comment beside the header
   rule in `shell.css`.
10. **`limit_results` went back into the card** (`6e3f0ad`), reversing
    `BATCH21_DEFINITION.md` decision 3. Owner ruled the design's placement
    wins: how many albums you list is not part of what counts as listened.
11. **The heatmap result was rebuilt against the design mock** (`6e3f0ad`):
    a mono eyebrow carrying the range, the headline shortened to "A year of
    <name>", `Save image` and `Search again` as hairline peers beside the
    title, the ramp raised onto the KPI value line, and daily average
    replacing active days in the KPI row. **`Save image` is a new feature
    the plan never scoped** -- about 120 lines in `heatmap.js` that draw a
    canvas by hand. Owner approved it knowing the labels inside the
    serialized SVG fall back to a plain monospace stack.
12. **The index is full bleed and the hero scales past 1500px**
    (`6e3f0ad`, `c0dadb0`). The 1180px page cap left a narrow block floating
    in a wide window, and the design caps results and the heatmap but never
    the index. The hero mark now grows to 820px and the headline to 56px,
    both past the design's stated 560px and 42px. Owner ruled both.
13. **Task 14's `limit_results` assertion is inverted** (`9ca9598`). The plan
    asks for a test that the field renders inside the thresholds disclosure.
    The owner reversed that placement on 2026-08-24, so the test asserts the
    opposite: the field renders above the disclosure, and the order in the
    markup is what it checks.
14. **The gate now runs two viewports and two new checks**, one more than the
    plan asked for. Task 13 scoped a touch-target check; `check_initial_visibility`
    is added beside it, because the `.hidden` collision in commit 4 proved
    that asserting a class name proves nothing.
15. **`error.css` was edited in this commit** (`9ca9598`), though the plan
    assigns that file to WP-8. The new touch check measured its daisyUI
    buttons at 40px against the design's 44px minimum. Fixing it was cheaper
    than shipping a gate with a known failure in it, and a gate that fails on
    purpose stops being read. WP-8 still owns the rest of the file, including
    its 600px breakpoint.

**Two facts commits 4 onward depend on, both established after the plan was
written.**

- **The animation wrapper classes are load-bearing.** `static/css/shell.css`
  animates `.ss-mark svg #horizontal_bars path:nth-of-type(-n+5)` and
  `.ss-pinwheel svg > g`. Any markup that includes a wordmark or the pinwheel
  must carry the matching class or it renders correctly and never moves, with
  no error anywhere. This bites Task 6 hardest: the extracted
  `_loading.html` carries the pinwheel, and the existing shell test checks
  rendered pages rather than partials.
- **The new colour tokens are `--ss-` prefixed, not the design's names.**
  They are `--ss-text-body`, `--ss-text-muted`, `--ss-border-default` and
  `--ss-accent-soft`, plus `--ss-surface-card`, `--ss-surface-sunken`,
  `--heatmap-surface`, `--ss-bad`, `--heatmap-empty`, `--rocket-5`,
  `--radius-xs` and `--radius-md`. The design calls the first two
  `--text-body` and
  `--text-muted`, but `--text-*` is Tailwind v4's font-size namespace and
  `--text-body: 1rem` already exists, so a colour under that name shadows the
  type scale and `.text-body` silently stops working.
- **Two classes the JS reads were renamed, and both were repointed.**
  `.heatmap-spinner-wrapper` is `.wait-panel__mark`, because the partial is
  shared, and `static/js/heatmap.js` queries it in two places to hide the
  pinwheel on error. `.invalid-feedback` is `.field__error` in both scripts.
  Renaming either without the other is silent: the pinwheel keeps spinning
  behind an error message, or a validation message renders unstyled.
- **A hex in a comment fails the source guard.**
  `tests/scripts/dev/test_tailwind_build_cli.py` forbids both cool greys in
  `static/css/tailwind.src.css` by plain substring, so a comment that names
  one to explain why it is wrong reads as a reintroduction. Describe the
  colour in words there.
- **A page stylesheet loads after `tailwind.css`, so it beats a utility of
  equal specificity.** `.index-grid { display: grid }` overrode Tailwind's
  `.hidden`, and the scripts then hid an element that stayed on screen with
  the class applied. `.index-grid.hidden` restores it. The same ordering
  trap bit a second time inside `index.css` itself: a `@media` block placed
  above the base rule it meant to override did nothing at all, and the
  measurements came back byte-identical to before. **Measure after the
  change, not only before.**
- **Assert computed style, never a class name.** The probe that was meant to
  prove the grid hid asserted `className`, passed, and missed a live defect.
  `scripts/dev/frontend_gate.py` should gain a check that walks every id the
  scripts toggle and asserts `display: none` -- Task 13.
- **Four tokens landed in commit 4, not commit 3**: `--ss-surface-card`,
  `--ss-surface-sunken`, `--heatmap-surface` and `--ss-bad`. Task 14 must
  add all four to `INDEX_TOKENS`. Done in `9ca9598`.
- **A gate check that measures only what is on screen measures almost
  nothing.** The first touch-target run passed every hidden control, because
  the decade pills, the release-year field and the heatmap form all start
  hidden. The check now drives the page into four states before measuring,
  and the pills failed immediately. Any later check over page elements needs
  the same treatment.
- **A `<label for>` and its input are one target.** Measuring both fails
  correct markup every time, and measuring neither is what let six small
  targets ship. The rule is: measure the input where it is visible, measure
  the label where the input is clipped to 1x1.

---

## How to look at the page

The plan requires a visual pass and the gates cannot do it, so here is the
mechanism rather than only the instruction. This works for any agent.

**Prefer a script that owns its own server.** Write one script that starts
the app, drives Chromium, measures, screenshots, and shuts the server down --
all in one process. `serve_app()` in `scripts/dev/frontend_gate.py` is the
construction to copy: `make_server` on port 0, `serve_forever` on a daemon
thread, and `shutdown()` in a `finally` block so a failing check can never
leave a socket listening. Playwright is pinned in `requirements-dev.txt` at
1.62.0 with Chromium provisioned.

Do **not** use `python app.py`. Its `__main__` block calls
`webbrowser.open()` and opens a real window on the owner's desktop.

**A persistent server is allowed here, by owner exception granted
2026-08-24.** `AGENTS.md` Anti-Pattern Registry item 5 says never to start a
server from the Bash tool, because an abandoned one blocks the owner's
terminal. The owner lifted that for visual inspection in this work package,
"unless it causes issues". So a background server on a fixed port is
available when you need one that outlives a single command -- driving the
page through the Playwright MCP tools, for example. The obligation the rule
exists for does not lift: stop it when you are done, and stop it on failure.

**Measure, do not only look.** The self-contained script is the better tool
for a reason beyond tidiness: it reads computed values. Commit 4's worst
defect was a page with no background at all, inheriting the browser's own
canvas. Every screenshot of it looked correct.

Screenshots default to the repository root and dirty the tree. Write them to
`.playwright-mcp/`, which `.gitignore` already covers.

Five things that produced wrong readings during this WP:

- **Read colours as computed values, not from a screenshot.** Both themes use
  close neighbours and a JPEG-eyeball is not evidence.
- **Wait out the transition.** `shell.css` transitions `background-color`
  over 0.3s, so `getComputedStyle` immediately after a theme toggle returns
  the old colour. Dark mode first read as `#f8f9fa`.
- **The welcome modal auto-opens and its backdrop covers the header.** Until
  commit 4 deletes it, remove `#welcomeModal` from the DOM before measuring.
  Calling Bootstrap's `hide()` during its opening transition is ignored.
- **Element screenshots crop to the element box.** The pinwheel paints
  outside its wrapper with `overflow: visible`, so shoot a roomier parent.
- **A rect is not a touch target.** `getBoundingClientRect()` on a control
  misses a hit area drawn by a pseudo element, and reports 1px for a
  visually hidden input whose label is the real target. Both appear on this
  page. Hit-test with `elementFromPoint`, or size the control itself.

`flounder14` is a real Last.fm account the owner supplied for live checks. It
returns `registered_year: 2016`, which is what the join-year hint floors the
year input at.

---

## Commit 1: record the scope

### Task 1: Amend the batch definition

**Files:** Modify `BATCH21_DEFINITION.md`

**Step 1.** In the WP-3 section, add the deliverables the scope ruling moved
in: the heatmap form, the shared loading partial, the heatmap result frame,
the mode pills as real buttons, the SMIL strip, and the three Jinja partials.

**Step 2.** Replace the WP-6 section body with an absorbed stub. Keep the
heading and the number. Do **not** renumber WP-7 or WP-8; renumbering breaks
every citation of them across `PLAYBOOK.md`, `FINDINGS.md` and
`AGENT_NOTES.md`, which is the `F-STYLE-1` failure mode.

```markdown
### WP-6 -- Heatmap seam removal (ABSORBED INTO WP-3, 2026-08-23)

The heatmap has no page of its own. Every deliverable below is on
`index.html` and shipped with the index rebuild. This stub stays so that
criteria 2, 3 and 8 and the PLAYBOOK Section 4 entries keep resolving.

- Page background and frame unified with the global themes -- WP-3
- The `:root` token block leaves `heatmap.css` -- WP-3
- Month labels to mono small-caps -- WP-3
- One warm `rocket_r` accent in the page UI -- WP-3
- Headline nowrap clip fixed -- WP-3
- `.mode-pill` min-width equalized, closing F-B18-12 -- WP-3
```

**Use that heading text exactly.** DOC007 reads the definition's own
`### WP-N` headings to learn which work packages are real, and drops any whose
heading matches `WP_SKIPPED_RE` in `scripts/docsync/integrity.py`. The three
recognised phrasings are `absorbed into`, `dropped` and `merged into`, case
insensitive. Verified against the merged check on 2026-08-24: with this
heading the planned set is `(0,1,2,3,4,5,7,8)`, and the next work package
after WP-5 computes as WP-7. Paraphrasing breaks it silently --
`(ABSORBED, see WP-3)` and `(folded into WP-3)` both fail to match, and
DOC007 would then demand a WP-6 that will never ship.

**Step 3.** Record the two rulings this WP owes: `F-B21-4` item 1 resolves to
the README two-column hero, and `RECONCILIATION.md` section 7's cell geometry
resolves as the table above states. One sentence each.

**Step 4.** Set the status line at the top of the file to say WP-3 is **in
progress**. Do not write "WP-4 is next" yet -- see Task 15 and the
coordination note at the end.

**Step 5.** Verify: `python scripts/doc_state_sync.py --check` exits 0 with
only the expected active-batch root-definition warning.

### Task 2: Move PLAYBOOK and SESSION_CONTEXT with it

**Files:** Modify `PLAYBOOK.md`, `.claude/SESSION_CONTEXT.md`

**Step 1.** `PLAYBOOK.md` Section 3: change the next action to say WP-3 is in
progress and name its scope in two sentences.

**Step 2.** `.claude/SESSION_CONTEXT.md` Section 1, the Batch 21 status row.
This row is hand-maintained prose and no gate reads it, so it drifts silently.
`AGENTS.md` "What to update after a WP or side-task commit" requires it to
move with the batch status, in the same commit.

**Step 3.** Do **not** hand-edit the test count. It is machine-derived from
PLAYBOOK Section 4 by `latest_test_count_authority()` in
`scripts/docsync/logic.py` and enforced by `scripts/docsync/integrity.py`.

**Step 4.** Run `python scripts/doc_state_sync.py --fix`, then check
`git diff docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` to see whether an
entry rotated out.

**Step 5.** Commit.

```
docs(batch): fold WP-6 into WP-3 and record the index scope

The heatmap has no page of its own, so every WP-6 deliverable is on
index.html. Fold them into WP-3 and leave WP-6 as an absorbed stub
rather than renumbering WP-7 and WP-8, whose citations would break.

Record the two rulings WP-3 owes: F-B21-4 item 1 takes the canonical
README two-column hero, and the heatmap cell geometry keeps the 14px
cell while taking the README gap.
```

---

## Commit 2: strip the SMIL

Read `docs/design/README.md` "Wordmark animation" before starting. It
specifies the CSS route, the `nth-of-type(-n+5)` cap and the
`transform-box: view-box` requirement, and it was written before anyone hit
these defects.

### Task 3: Strip SMIL and animate from CSS

**Files:**
- Modify `templates/inline/scrobblescope_pinwheel.svg`
- Modify `templates/inline/scrobble_scope_inline.svg`
- Modify `static/css/shell.css`
- Modify `templates/index.html`, `templates/loading.html`,
  `templates/results.html`, `templates/unmatched.html` -- one wrapper class
  each, nothing else

`scrobble_scope_inline.svg` is included by all four templates, so fixing only
the index would leave three pages animating unstoppably -- `AGENTS.md`
Anti-Pattern Registry item 11.

**Step 1.** Remove every `<animate>` and `<animateTransform>` element from
both SVGs. Change nothing else -- no path data, no `viewBox`, no `id`.

**Step 2.** In `static/css/shell.css`, generalise the existing bar animation.
It currently selects `.site-header__mark svg #horizontal_bars path`. Add a
shared class so the same rules reach the hero and the three legacy pages.
Keep `transform-box: view-box` and `transform-origin: 0 63.5px` exactly as
they are. The comment above that block explains, with a measurement, why the
origin is not corrected for the `viewBox` offset. Do not change the number.

**Step 3.** Add pinwheel keyframes to `static/css/shell.css`. `shell.css` is
the framework-neutral sheet loaded on every page, which is why it is the right
home. The design specifies a 2.5s cycle, 1080 degrees of rotation with a
5.4-unit blade expansion, reading `--bars-color`.

**Step 4.** Extend the existing `@media (prefers-reduced-motion: reduce)`
block to cancel both animations. **Restore `opacity: 1` for anything that
fades in from 0.** Cancelling a forwards animation that starts transparent
hides the element permanently, for exactly the readers who asked for less
motion.

**Step 5.** Add the wrapper class to the four templates. Markup only -- adding
one class to one element per file. Do not restructure anything on the three
unmigrated pages.

### Task 4: Prove the guard can fail

**Files:** Modify `tests/test_template_shell.py`

**Step 1.** `test_the_header_mark_carries_no_smil_animation` currently slices
the page down to the `<header>` and its docstring says the index hero wordmark
and the pinwheel still carry SMIL. That is no longer true. Widen it to the
whole rendered page and rewrite the docstring to match.

**Step 2.** Add a test asserting `shell.css` carries pinwheel keyframes and
that the reduced-motion block cancels them.

**Step 3.** Mutation proof. Re-add one `<animate>` element to
`scrobblescope_pinwheel.svg`, run the widened test, confirm it fails, revert.
Repeat for `scrobble_scope_inline.svg`. Then delete the reduced-motion
pinwheel rule, confirm the second test fails, revert.

**Step 4.** Visual check. Open all four pages in both themes with
`prefers-reduced-motion: reduce` set. Playwright sets this on the context
directly. Confirm the bars and the pinwheel are still **and still visible**.

**Step 5.** Run the four gate commands, then commit.

---

## Commit 3: the tokens

### Task 5: Add the index page tokens to the theme

**Files:** Modify `static/css/tailwind.src.css`, `static/css/tailwind.css`,
`tests/test_template_shell.py`

Read `docs/design/README.md` "Design tokens" and `RECONCILIATION.md`
section 3 first. Section 3 lists exactly which README tokens the theme already
carries and which are absent, so you do not have to re-derive it.

**Step 1.** Add to the `@theme static` block: `--radius-xs: 4px` and
`--radius-md: 10px`. `RECONCILIATION.md` section 6 records these two as the
missing steps.

**Step 2.** Add the four absent text and border tokens to both theme blocks,
using the README's light and dark values: body text, muted text, default
border, accent tint.

**Step 3.** Add `--rocket-5: #f0903a` to both theme blocks, with a comment
naming `static/js/heatmap.js` as the owner of all seven ramp stops and saying
that only this one is mirrored, for the mode-tab mark that
`docs/design/components/navigation/ModeTabs.prompt.md` specifies.

**Step 4.** Add `--heatmap-empty`, `#e8e2d6` light and `#262230` dark.

**Step 5.** Rebuild: `python scripts/dev/tailwind_build.py`. Run it a second
time and confirm the two outputs are byte-identical with `Get-FileHash`.

**Step 6.** Confirm every new token is present in the built
`static/css/tailwind.css`. Nothing reads them yet at this commit, so `@theme
static` is the only reason they survive. If one is missing, that is the
pruning failure mode from note 1 above, not a typo.

**Step 7.** Add an assertion to `tests/test_template_shell.py` that the new
tokens are defined in the compiled sheet. Mutation proof: change one token
name in the source, rebuild, confirm the test fails, revert.

**Step 8.** Stage `static/css/tailwind.css` together with the source. Run the
four gate commands, then commit.

---

## Commit 4: rebuild the page

This is the switch. Work through tasks 6 to 12 without committing between
them; the page does not render correctly until all seven are done.

### Task 6: Extract the three partials

**Files:**
- Create `templates/partials/_loading.html`
- Create `templates/partials/_heatmap_form.html`
- Create `templates/partials/_heatmap_result.html`

**Step 1.** `git add -N` each new file immediately, so `pre-commit` sees them.

**Step 2.** `_loading.html` must be framework-neutral. WP-3 renders it on a
migrated page; WP-4 will render it on `loading.html`, which is still a
Bootstrap page at that point. It carries the pinwheel, a mono uppercase phase
line and the error block. Read
`docs/design/components/feedback/Pinwheel.prompt.md` and
`docs/design/components/feedback/ProgressBar.prompt.md` first.

**Step 3.** Keep every element `id` that `static/js/heatmap.js` and
`static/js/loading.js` read. Moving markup into a partial must not rename
anything. Grep both files for `getElementById` and check the list before you
finish.

**Step 4 (added after commit 2).** **Carry the `ss-pinwheel` class into the
partial.** `static/css/shell.css` animates `.ss-pinwheel svg > g` and
`.ss-pinwheel svg > g > g`; the pinwheel's own SMIL was stripped in commit 2,
so the class is now the only thing that makes it move. Drop it and the
pinwheel renders perfectly and sits still, with no error and nothing in the
console. The wrapper in `index.html` today reads:

```html
<div class="heatmap-spinner-wrapper ss-pinwheel" aria-label="Loading animation" role="img">
```

The same applies to `ss-mark` anywhere a wordmark is included. Task 14 should
assert the partial carries it, because the existing shell test renders whole
pages and would not catch a partial that lost the class.

### Task 7: The hero and the mode tabs

**Files:** Modify `templates/index.html`

Read `docs/design/README.md` screen 1 "Index" and
`docs/design/components/navigation/ModeTabs.prompt.md` first.

**Step 1.** Two-column grid, `1.1fr 1fr`, both columns top-anchored, stacking
to one column at 860px. That is the single breakpoint for the whole design and
`static/css/shell.css` already uses it.

**Step 2.** Use the **lockup** in the hero, not the full wordmark:
`templates/inline/scrobble_scope_lockup_inline.svg`. `docs/design/README.md`
known constraint 6 says the tagline lives inside the full logo art, so the
lockup is correct anywhere an h1 already states the proposition. Cap it at
560px and give the wrapper an explicit `height: auto`; constraint 5 records
what happens otherwise.

**Step 3.** Rebuild the mode pills as real `<button type="button">` elements.
They are `span[role="button"][tabindex="0"]` today, which is one of the three
defects in `F-B21-5`. Give both tabs the same `min-width` so they are equal,
closing `F-B18-12`. The Heatmap tab's square mark takes `var(--rocket-5)`.

**Step 4.** Copy comes from `docs/design/README.md` screen 1, "Copy, exactly".
Sentence case throughout -- the shipped Title Case labels are legacy.

### Task 8: The albums form

**Files:** Modify `templates/index.html`

Read `docs/design/components/forms/Field.prompt.md`, `Input.prompt.md`,
`Select.prompt.md`, `PillGroup.prompt.md`, `SegmentedControl.prompt.md`,
`Stepper.prompt.md` and `docs/design/components/layout/Disclosure.prompt.md`
first.

**Step 1.** Group the fields as the batch definition requires: identity,
filtering, display, thresholds.

**Step 2.** Replace every `data-bs-toggle="popover"` span. Obvious fields get
nothing or an inline hint. Only the ambiguous ones -- release scope and sort
-- get a hint. **The hints must open on keyboard focus and on tap, not on
hover alone.** A hover-only disclosure is unreachable by keyboard and on
touch, which turns "removed the Popover dependency" into "removed the
explanation for some users". The batch definition states this as a
requirement.

**Step 3. REVERSED 2026-08-24 (owner) -- do not do this.** Keep
`limit_results` a visible field in the card, above the disclosure. The
original step, and the reasoning that no longer applies, follow.

~~Move `limit_results` inside the thresholds disclosure.~~ Owner
decision 3 in `BATCH21_DEFINITION.md` keeps the control and relocates it; it
is a real Spotify-load saving on large libraries. Do not drop it and do not
half-wire it.

**Step 4.** Replace the two threshold `<select>` elements with steppers over
real number inputs, plus a reset affordance. The disclosure is closed by
default with a dashed 1px top border, and its summary shows `>=N plays -
>=N tracks` using the U+2265 glyph.

**Step 5.** Every input keeps a programmatic label association. Focus stays
visible on every interactive element in both themes -- the design calls the
2px accent ring at 2px offset non-negotiable.

**Step 6.** Keep the year input's `min`, `max`, `inputmode` and `required`
attributes exactly as they are. **Validation parity is a requirement**: the
rebuilt form must reject exactly what the current form rejects and accept
exactly what it accepts. The server contract does not change in this WP, so
any behavioural difference is a regression.

### Task 9: Heatmap mode and the result frame

**Files:** Modify `templates/index.html`

Read `docs/design/README.md` screen 1's heatmap-mode paragraph and screen 4
"Heatmap", plus `docs/design/components/heatmap/HeatmapFrame.prompt.md`.

**Step 1.** In heatmap mode the card collapses to a single line and the filter
tags are replaced by a bordered preview panel, closed by an 8px `rocket_r`
gradient bar.

**Step 2.** Include the three partials from Task 6.

**Step 3.** Delete the welcome modal markup entirely. This closes `F-B21-11`,
where the Bootstrap `.modal-backdrop` at z-index 1050 covers the 1030 header
and makes the theme toggle unclickable on first visit.

**Step 4.** Delete the `bootstrap_js` block from this template. `index.html`
is the only page that loads the jsdelivr bundle; `unmatched.html` keeps its
own until WP-7.

**Step 5.** Override `legacy_css` with an empty block, exactly as
`templates/error.html` does, and load `tailwind.css` in the `stylesheets`
block. **This is the switch.** Copy the comment from `error.html` explaining
why.

### Task 10: index.js

**Files:** Modify `static/js/index.js`

**Step 1.** Delete the welcome-modal block and the `bootstrap.Popover` loop.
Those are the only two `bootstrap` global references in this file; after this
the page has no Bootstrap JS dependency.

**Step 2.** Wire the steppers, the disclosure and the CSS-only hints. Prefer
CSS for the hints and the disclosure; use `<details>`/`<summary>` where it
does the job, and add JS only for what CSS cannot express.

**Step 3.** Leave `validateYear`, `validateReleaseYear`, `updateDecadePills`
and the `/validate_user` blur handler behaving identically. Restyle only. The
debounce, the `registered_year` floor and the decade cross-validation all
stay.

### Task 11: heatmap.js

**Files:** Modify `static/js/heatmap.js`

**Step 1.** Replace `d-none` with Tailwind's `hidden`. There are about ten
sites; grep rather than counting from this plan. `@source "../../static/js"`
in `static/css/tailwind.src.css` means the extractor sees JS string literals,
so `hidden` will be generated.

**Step 2.** Leave `is-valid` and `is-invalid` named as they are. They are
state classes, not framework classes; Task 12 gives them real declarations in
the page stylesheet. Renaming them would churn JS for nothing.

**Step 3.** Update the mode-pill handler for `<button>` elements. The
`keydown` handling that existed for `span[role="button"]` is no longer needed;
a real button handles Enter and Space itself.

**Step 4.** Month labels to mono small-caps. These are SVG `<text>` nodes
generated in this file, so the change is here, not in CSS.

**Step 5.** Cell gap to 2px desktop and 1px mobile. Keep the 14px cell.
`static/js/heatmap.js` owns this geometry.

**Step 6.** `getEmptyCellColor` reads
`document.body.classList.contains('dark-mode')`. Leave it. `static/js/theme.js`
still dual-writes that marker and WP-8 owns its retirement. Update the two
hardcoded hex values to the new `--heatmap-empty` values.

### Task 12: The two stylesheets

**Files:** Modify `static/css/index.css`, `static/css/heatmap.css`,
`static/css/tailwind.css`

**Step 1.** Both files are rewritten. They stay separate: `index.css` owns the
hero, the form chrome and the disclosure; `heatmap.css` owns the heatmap
surface. Two responsibilities, and the split keeps the diff reviewable.

**Step 2.** `heatmap.css` reads `--text-color`, `--border-color` and
`--error-accent` in 13 places. Only `static/css/global.css` defines them, and
`global.css` leaves the page at Task 9. Repoint all 13 at theme tokens.
`global.css` is also the only definer of `#f8f9fa` and `#121212`, the two
surfaces the frontend gate's `check_theme_tokens` forbids, so it has to go.

Commit 3 landed the tokens to repoint them at. **Use these names, not the
design's.** `--text-*` is Tailwind v4's font-size namespace and
`--text-body: 1rem` already exists, so a colour called `--text-body` shadows
the type scale and `.text-body` silently stops setting a font size.

| Need | Token | Light | Dark |
| --- | --- | --- | --- |
| Paragraph text | `--ss-text-body` | `#4a4456` | `#c5bfb1` |
| Hints, eyebrows, meta | `--ss-text-muted` | `#6f6a7a` | `#908a9a` |
| Every hairline | `--ss-border-default` | `#e5dfd1` | `#2a2434` |
| Accent tint | `--ss-accent-soft` | `#efe9fa` | `#2a1f44` |
| Empty heatmap cell | `--heatmap-empty` | `#e8e2d6` | `#262230` |
| Mode-tab mark | `--rocket-5` | `#f0903a` | same |

Headings and values take `--color-base-content`; the page and card surfaces
take `--color-base-100` and `--color-base-200`; the accent is
`--color-primary`. Radius now has five steps: `--radius-xs` 4px,
`--radius-sm` 8px, `--radius-md` 10px, `--radius-lg` 14px, `--radius-full`.

The error accent has no token yet. The README specifies `--ss-bad` `#b03434`
light and `#e07070` dark, and the theme still carries Bootstrap's `#dc3545`
in `--color-error`. Either add `--ss-bad` in this commit or use
`--color-error` and note the deviation; do not leave a bare hex.

**Step 3.** Delete the `:root` block in `heatmap.css` above
`.heatmap-headline`. Its three tokens move into the theme or into the rules
that used them. This is the absorbed WP-6 deliverable.

**Step 4.** Fix the headline nowrap clip. `.heatmap-headline` already carries
`overflow-wrap: anywhere`; check the mobile media query for a surviving
`white-space: nowrap`.

**Step 5.** Keep the 16px mobile input override. See the decisions table.

**Step 6.** Grep for what each deleted rule styled before deleting it.

**Step 7.** Rebuild `tailwind.css` and stage it with everything else.

**Step 8.** Run the four gate commands. The frontend gate still has the index
in `LEGACY_PAGES` at this point, so `check_stylesheet_isolation` will fail
until Task 13. That failure is expected here and only here.

**Step 9.** Commit tasks 6 to 12 together.

---

## Commit 5: extend the gates

### Task 13: The frontend gate

**Files:** Modify `scripts/dev/frontend_gate.py`

**Step 1.** Move `"/"` from `LEGACY_PAGES` to `MIGRATED_PAGES`. `LEGACY_PAGES`
becomes empty of the index but keeps the pages WP-4 onward will move.

**Step 2.** Correct the `check_theme_persistence` docstring. It currently
explains that the check avoids the index because the welcome modal covers the
toggle. That reason is gone. This is the same class of staleness that cost
PR #216 its second review round.

**Step 3.** Run the gate. The index now sits inside the theme-token, font and
persistence checks. Do not quote a check count from this plan -- read it off
the run, because step 4 changes it.

**Step 4 (added 2026-08-24, owner).** **Give the gate a mobile viewport.**
`main()` calls `browser.new_page()` with no viewport, so every check this
batch has built runs at Playwright's 1280x720 default. Mobile is verified by
owner review and nothing else, and WP-2 shipped two live rendering defects
past all four gates. Run the visual checks at the design's mobile reference
canvas, 390x844, as well as at desktop, and report which viewport a failure
came from. `docs/design/README.md` "Responsive" fixes the single breakpoint
at 860px, so the two sides are the whole matrix.

**Step 5.** Add a touch-target check at the mobile viewport: every
interactive element on a migrated page is at least 44px on its smaller axis.
The README calls this non-negotiable and criterion 8 names it, and `F-AUDIT-1`
was closed against the toggle alone with nothing holding the rest.

**Why not a separate mobile stylesheet.** The owner asked on 2026-08-24
whether Bootstrap should stay for mobile only. It cannot: a media-scoped link
is still a loaded stylesheet, so `check_stylesheet_isolation` -- which asserts
exactly one framework sheet, not merely "not both" -- fails on every page, and
on mobile both sheets would apply, which is the `.btn`/`.card`/`.modal`
collision the strangler exists to avoid. It would also leave criterion 1 and
`F-B20-3` permanently unclosable. The measured work it would save is small:
14 responsive Bootstrap grid classes across all six templates, five of them
in `index.html` and deleted by commit 4 anyway. Tailwind is mobile-first, so
the unprefixed utilities are the mobile case. The real gap the question
exposed is the desktop-only gate, which steps 4 and 5 close.

**Also worth recording:** the repository currently uses four breakpoints --
860px in `shell.css`, 620px in `results.css`, 768px in `heatmap.css` and
600px in `error.css` -- against a design that mandates one. Task 12 rewrites
two of those files and should land on 860px. `error.css` belongs to WP-8.

### Task 14: The shell tests

**Files:** Modify `tests/test_template_shell.py`

**Step 1.** Add `"index.html"` to the `MIGRATED` set. Two existing
parametrised tests then invert for that template automatically.

**Step 2.** Add index-specific assertions:

- the mode tabs are `<button>` elements, and there is no
  `role="button"` span left on the page;
- the page loads no Bootstrap JS bundle;
- no `data-bs-` attribute survives anywhere in the rendered page;
- `limit_results` renders **above** the thresholds disclosure, not inside
  it (reversed 2026-08-24, owner);
- the welcome modal id is absent.

**Step 3.** Mutation proof each new assertion individually. Five assertions,
five mutations, five confirmed failures, five reverts. Do not batch them --
that is how a vacuous assertion hides behind a real one.

**Step 4.** Note that
`test_every_custom_property_a_page_reads_is_defined_by_a_sheet_it_loads`
now covers the index automatically, because it reads the stylesheet list back
off the rendered page. It is what catches a missed token in Task 12.

**Step 5.** Run the four gate commands, then commit.

---

## Commit 6: record it

### Task 15: PLAYBOOK, SESSION_CONTEXT and the status line

**Files:** Modify `PLAYBOOK.md`, `.claude/SESSION_CONTEXT.md`,
`BATCH21_DEFINITION.md`

**Step 1.** Write the dated Section 4 entry inside the current-batch markers,
tagged `(Batch 21 WP-3)`. `AGENTS.md` "Markdown Authoring Rules" says what to
cover: scope, plan against implementation, deviations, validation results with
the test count, and forward guidance. Search the archive first for a title or
date collision:
`rg -n "^### 20" docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`.

**Step 2.** Record the deviations honestly: WP-6 absorbed, the loading partial
built a WP early, the validation restyle that keeps `/validate_user` against
the README's simpler rule, and the heatmap geometry ruling.

**Step 3.** Now move all three status legs to WP-4 **in this one commit**:
PLAYBOOK Section 3, `BATCH21_DEFINITION.md`'s status line, and
`.claude/SESSION_CONTEXT.md` Section 1. `AGENTS.md` "Session Bootstrap" makes
their agreement the condition for bootstrap to complete, and this line has
gone stale twice already.

**Step 4.** Run `python scripts/doc_state_sync.py --fix`. It regenerates the
test count from the Section 4 entry. Never hand-edit it.

**Step 5.** Update `.claude/SESSION_CONTEXT.md` Section 3 for the new
`templates/partials/` directory and its three files.

### Task 16: Findings

**Four findings this work surfaced, all owner-acknowledged. File them here.**

1. **The heatmap has no non-colour path to its data.** Measured with the
   `dataviz` skill's validator and by hand: the rocket ramp itself is sound
   -- strictly monotonic in OKLab lightness, steps 0.107 to 0.144 -- but the
   ends nearly vanish into their own surface. `#f9d576` sits at 1.34:1
   against the light frame and `#03051a` at 1.12:1 against the dark one. The
   only relief that exists is a mouse hover: cells are not focusable, so a
   keyboard reader cannot reach any day's value, and there is no table view.
   The ramp is fixed by the design contract, so the fix is relief, not
   re-tinting. **Owner ruled this critical on 2026-08-24** while noting that
   a sighted mouse user sees no problem -- record that scope in the finding.
2. **The page split is deferred.** Cross-reference the `GET /heatmap/<user>`
   item under "Out of scope"; the split only pays for itself alongside it.
   Owner decision 3, 2026-08-23.
3. **`unmatched.html` loads the Bootstrap JS bundle but no `data-bs-*`
   attribute on it uses the bundle.** It may already be dead weight. WP-7
   should check rather than assume.
4. **The heatmap export saves whatever layout is on screen.**
   `docs/design/README.md` screen 4 asks for the desktop 53x7 grid even on a
   phone. `saveHeatmapImage` does not re-render for export.



**Files:** Modify `FINDINGS.md`

**Step 1.** Close `F-B21-11`. The welcome modal is gone, so the backdrop can
no longer cover the header toggle.

**Step 2.** Close `F-B18-12`. The mode pills are equal width.

**Step 3.** Update `F-B21-5`. The SMIL item is now fully resolved across all
four pages. The mode-pill item is resolved. The `opacity: 0.5` KPI label item
in `static/css/heatmap.css` is **also** in this WP's territory now that WP-6
is absorbed -- fix it with a real muted token in Task 12 and close the finding,
or state plainly why it is still open.

**Step 4.** Update `F-B21-4`. Item 1 is decided; items 2, 3 and 4 stay open
for WP-4, WP-5 and WP-7. Do not close the finding.

**Step 5.** File the heatmap page split as a new finding. Check the highest
existing `F-B21-N` before choosing the ID -- the parallel branch may have
taken the next one. Cross-reference the deferred
`GET /heatmap/<username>` item in `BATCH21_DEFINITION.md` "Out of scope", and
say that the split only pays for itself alongside that feature.

**Step 6.** Move the header count. `FINDINGS.md` carries a bare line reading
`NNN tests across NN test modules.` Once `F-B21-13`'s DOC008 check has landed,
that line is gated against the same authority as SESSION_CONTEXT, so it must
move in this commit alongside the Section 4 entry. Keep the line's exact shape
-- DOC008 matches a bare line and does not see a bolded one, so reformatting it
switches the check off silently.

**Step 7.** Findings are mirrored to GitHub issues by hand and the mirror
drifts; `F-B21-9` records that the owner accepted this. Do not try to sync it.

**Step 8.** Run the four gate commands, then commit.

---

## Final verification

Run all four gate commands on the finished tree and record the real numbers.
Do not quote a test count without re-running.

```
pytest -q
pre-commit run --all-files
python scripts/doc_state_sync.py --check
python scripts/dev/frontend_gate.py
```

Then the visual pass. **The automated gates will not catch what matters most
on this page.** Seven review comments landed on PR #216 across three rounds;
every one was valid and not one was caught by `pytest`, `pre-commit`, the
frontend gate or the Quality Gate. Two were live rendering defects on the
pilot page.

1. Both themes, light and dark, on the whole page.
2. Both sides of the 860px breakpoint. The mobile reference canvas is
   390x844.
3. `prefers-reduced-motion: reduce`. The pinwheel and all five wordmark bars
   still, and still visible.
4. Keyboard traversal of the whole form. Every hint opens on focus. Focus is
   visible on every interactive element in both themes.
5. Touch targets at or above 44px.
6. The three unmigrated pages -- loading, results, unmatched -- unchanged
   apart from the wordmark's reduced-motion behaviour.
7. Both heatmap paths: a successful fetch to a rendered grid, and a failure to
   the error block with Retry. Use `flounder14` for the success path -- the
   owner supplied it and `/validate_user` returns
   `{"valid": true, "registered_year": 2016}` against the live API. A
   nonsense username exercises the not-found path without touching the
   pipeline.

---

## Known risks

1. **Token pruning.** If a rule silently stops applying in commit 4, check the
   compiled sheet for the token before debugging the rule. See fact 1 above.
2. **Commit 4 is large and cannot be split.** Emptying `legacy_css` takes
   Bootstrap off the page in one step. Review it as a whole page, not as a
   diff; contradictions hide in the unchanged text next to an edit.
3. **The frontend gate fails between commit 4 and commit 5.** By design, and
   the only expected failure in the sequence. Do not push commit 4 alone --
   the Quality Gate runs on push to `wip/**`.
4. **`heatmap.js` is 741 lines and is not being rewritten.** Task 11 changes
   its class contract and two constants. Nothing more.
5. **The design bundle contradicts itself in places.** `RECONCILIATION.md`
   section 7 lists the known cases and `README.md` wins. Check there before
   treating a disagreement as new.

---

## Coordination with the parallel branch

A second agent is closing `F-B21-13` on `wip/f-b21-13-docsync-gate`, branched
from the same commit. It adds DOC007 and DOC008 checks to
`scripts/docsync/integrity.py` so that the three bootstrap legs are gated
rather than hand-maintained. It touches `scripts/docsync/integrity.py`,
`tests/test_docsync_integrity.py`, its own finding in `FINDINGS.md`, and one
`PLAYBOOK.md` entry. It has been told not to touch `BATCH21_DEFINITION.md`,
`templates/` or `static/`.

**What the two checks actually assert**, read off `f15e7e7` on 2026-08-24 and
verified by probing the functions directly rather than by reading them:

- **DOC007** derives the next work package from PLAYBOOK **Section 4** entry
  headings -- the WP numbers tagged there, then the lowest positive integer not
  among them -- and compares that to the claim in the definition's `**Status:**`
  line and in Section 3. A status line with no parseable claim makes the check
  silent rather than failing.
- **DOC008** compares the `FINDINGS.md` header line, which must read exactly
  `NNN tests across NN test modules.`, against the same authority DOC006 uses.

**This is why the status line moves in commit 6, not commit 1.** The
constraint is not what Section 3 says at the time -- it is that the definition
may not claim WP-4 is next until a WP-3 entry exists in Section 4. Commit 1
writes "WP-3 is in progress", which parses as no claim and is silent; commit 6
adds the Section 4 entry and moves all three legs together.

**Commit 6 must also move the `FINDINGS.md` header count**, in the same commit
as the Section 4 entry. DOC008 blocks otherwise. Write the entry so the count
is unambiguous -- one `pytest -q` result, not several bold numbers -- because
an ambiguous authority blocks DOC008 too.

**That branch is merged.** PR #217 landed on `main` as `8ed1650` on
2026-08-24, and `wip/batch-21` is rebased onto it. The summary above was read
off the merged code, not off the PR.

DOC007 handles the absorbed WP-6 correctly, which was not true of the version
first pushed to that PR -- it used a lowest-unused-integer rule that could not
express a gap and would have demanded WP-6 for the rest of the batch. The
merged version reads the definition's planned set instead. Task 1 carries the
heading wording that rule depends on.

Two things not to redo:

- **Do not tag one log entry with two WP numbers** to record an absorbed
  package as done. `_extract_entry_batch()` returns `None` for a two-WP
  heading, so rotation misfiles the entry into the monolith archive instead of
  `docs/history/logs/BATCH21_LOG.md`. Tested on 2026-08-24.
- **Do not reformat the `FINDINGS.md` header line.** DOC008 now accepts a
  bold or blockquoted form and is scoped to the header region above the first
  heading, so a historical example inside a finding no longer counts. Keep the
  line where it is.

Remaining coordination, if that branch or another one moves again:

1. A conflict in the `.claude/SESSION_CONTEXT.md` managed block is not a real
   conflict. That block is deterministic output. Take either side, then re-run
   `python scripts/doc_state_sync.py --fix`.
2. A conflict in PLAYBOOK Section 4 will be two dated entries wanting the same
   place. Keep both, newest first.
3. Whoever merges second re-runs the suite and moves the count.
4. Re-check the highest `F-B21-N` before writing the new finding ID in
   Task 16.
