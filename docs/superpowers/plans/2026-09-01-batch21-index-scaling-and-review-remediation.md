# Batch 21 Index Scaling and Owner-Review Remediation Implementation Plan

> **How to execute.** Work the tasks in order. Each task is one commit and ends
> at an owner review. Steps use checkbox (`- [ ]`) syntax so a later agent can
> see how far the work got. This plan requires no agent-specific tooling; a
> Claude Code session may drive it with `superpowers:executing-plans`, and any
> other agent follows the steps directly.

**Goal:** Make the desktop index composition grow with the real browser window,
widen the form so it stops floating in dead space, restore the design snapshot
that was edited in place, and finish the two owner-review items that never
shipped.

**Architecture:** Six independent commits. Task 1 repairs document provenance and
is unrelated to the rest, so it lands first and alone. Task 2 replaces the
JavaScript scale with one pure-CSS declaration and, in the same commit, re-points
the browser gate at window geometry that actually exists -- the gate change is
what makes the defect visible, so the two cannot be separated. Task 3 widens the
composition and raises divider contrast. Tasks 4 and 5 are the already-specified
progress-phase and unmatched-empty work. Task 6 is the accessibility pass the
owner asked to run last.

**Tech Stack:** Flask, Python 3.13, Jinja2, vanilla browser JavaScript, Tailwind
v4 generated CSS, pytest, Playwright frontend gate.

---

## Why this plan supersedes the 2026-09-01 remediation plan

`docs/superpowers/plans/2026-09-01-owner-review-remediation.md` is untracked and
was written before the failure was diagnosed. Keep it for reference; do not
execute it. Its Tasks 2 and 3 are sound and are carried forward here almost
unchanged. Its Task 1 rests on four claims that measurement disproved.

| Claim in that plan | Measured reality |
| --- | --- |
| The failure is a Firefox rendering problem; Firefox is the acceptance gate. | The failure reproduces in Chromium. It is engine-independent. |
| The `zoom` mechanism is unproven and may need replacing. | `zoom` is correct and stays. Its *input formula* is wrong. |
| The gate needs 1920x1080, 2560x1440 and 3840x2160 profiles added. | `check_large_display_scale_parity` already has all three, plus 1920x900. That is the bug, not the fix. |
| Move the `ALBUM FILTERING` eyebrow below the H1. | Already below it -- `templates/index.html:44-45`. No change needed. |

A fifth item is now settled by measurement rather than ruling. Playwright's
Firefox build (153.0) was installed on 2026-09-01 and the same page measured in
both engines at four window profiles. **They agree to within 0.1px everywhere:**

| Window | Chromium form width | Firefox form width |
| --- | --- | --- |
| 2560x1440 (gate viewport) | 544.7px | 544.7px |
| 2560x1272 (real maximised 1440p) | 481.1px | 481.1px |
| 2510x1110 (owner capture) | 419.8px | 419.9px |
| 1920x912 (real 1080p) | 408.5px | 408.5px |

`zoom` behaves identically in both. There is no engine component to this defect,
so "Firefox is the acceptance gate" answers a question that does not exist and
would leave the gate's viewport blindness (defect B) untouched. The acceptance
gate is **realistic window geometry, in either engine**.

## Evidence this plan is built on

All figures measured 2026-09-01 against `origin/main` at `f202b81`, in Chromium,
through `scripts/dev/frontend_gate.serve_app`.

**The composition's natural unscaled height is 673px** (hero column 324px, form
column 673px). The scale formula in `static/js/index.js:6-9` divides window
height by `1080`:

```js
Math.min(window.innerWidth / 1920, window.innerHeight / 1080)
```

Dividing by 1080 compares the window against the *design viewport* instead of
against the thing being protected. Because `min()` is unconditional, that
mistaken penalty applies to every window. Browser chrome costs 130-330px of
height and almost no width, so the height term always wins and the width
contribution is discarded entirely.

| Window | scale today | form today | hero scale fixed | form fixed @ 37.5rem | height guard |
| --- | --- | --- | --- | --- | --- |
| 1920x912 (real 1080p) | 1.075 | 408px | 1.075 | 600px | 1.35 |
| 2510x1110 (owner capture) | 1.105 | **420px** | **1.405** | **600px** | 1.65 |
| 2490x1230 (owner capture) | 1.224 | 465px | 1.394 | 600px | 1.83 |
| 2560x1272 (real 1440p) | 1.266 | 481px | 1.433 | 600px | 1.89 |
| 2560x1440 (**gate only**) | 1.433 | 545px | -- | -- | -- |

The `form fixed` column is flat on purpose. Owner ruling 2026-09-01: the form
widens and then locks; it is never zoomed, so its components keep the same
visual size at 1440p as at 1080p. The column that grows is the hero. An earlier
draft of this table multiplied 448px by the hero scale and printed 482/630/642,
which contradicted the rule three paragraphs below it.

The owner sees 420px at 1440p against 408px at 1080p: a 2.9% difference, which
is why the report is "the width of the form is the same". The gate sees 545px
against 408px, a 33% difference, and passes. **The gate measures a geometry no
browser window has**, because `page.set_viewport_size` sets the content box to
exactly the number given. No maximised browser on a 1440p panel has an
`innerHeight` of 1440.

The height-guard column is why the fix is safe: 1.35 to 1.89, always above the
width factor, so the guard never binds on a normal window and still catches a
genuinely short one.

**Two independent defects.** The formula fix moves 420px to 630px at 1440p and
does nothing at 1080p, where the factor is correctly 1.0. The width fix
(`3fr 4fr` plus a `37.5rem` cap) moves 408px to 600px at 1080p. Both are
needed.

**The form must widen, not magnify (owner ruling, 2026-09-01).** `zoom` scales a
composition uniformly, so it buys width by charging height and control size.
Measured at a real 1080p window (1920x912):

| zoom | form width | form height | submit height | document |
| --- | --- | --- | --- | --- |
| 1.0 | 380px | 673px | 48.0px | fits |
| 1.075 (current) | 408px | 723px | 51.6px | fits |
| 1.4 | 532px | 939px | 67.2px | overflows by 211px |

A 40% wider form costs a 40% taller form, a 67px submit button where 48px is
already the touch target, and rendered input text above the design's type scale.
That is why widening to `28rem` and scaling at the same time felt cramped at
1080p: the two mechanisms fight.

**So the two columns take different mechanisms.** The hero is an editorial
composition and keeps `zoom`, preserving the measured wordmark-to-H1
relationship. The form is a tool: it **widens** through `max-width` while its
type, its 44px touch targets and its 16px input floor stay exactly as designed,
then locks at the cap. Never apply `zoom` to `.index-form__inner`.

**Pure CSS is viable and was verified.** A length in `zoom` is invalid and fails
*silently* to `zoom: 1` -- that trap is why the naive `clamp(1.075, 0.056vw,
1.45)` must not be used. `tan(atan2(<length>, <length>))` yields a plain number
and works. There is no `vw` feedback loop inside a zoomed element: with
`zoom: 2` on a parent, a `width: 10vw` child computes `192px` against the true
1920px viewport and renders at `384px`.

**The H1 wraps when windowed, and the cause is a third pinned clamp.**
`.index-hero__headline` is `font-size: clamp(2rem, 6vw, 2.625rem)`. `6vw`
reaches the 42px ceiling at about a 700px viewport, so the H1 is a fixed 42px
across the whole desktop range. Owner report 2026-09-02: it newlines when the
window is not maximised, and it must not.

This is the same defect class as the other two, and worth naming as such: the
composition's unconditional `min()` discards the width term, the header's
`7.25vw` caps at roughly 1600px, and the H1's `6vw` caps at 700px. Three
declarations that read as responsive and are pinned in the range that matters.
**Before trusting any `clamp()` or `min()` in this codebase, compute where it
saturates.**

**The fix is a lower bound on the hero zoom, not a fluid H1.** Wrapping happens
because the hero column narrows while the composition cannot shrink: the scale
is floored at `--index-scale-base` (1.075) and only ever grows. A zoomed
element gets `column_width / zoom` of effective space, so the floor actively
starves the H1 as the window narrows.

Making the H1 alone fluid would break the annotation's own constraint --
"Logo scale should increase slightly, without changing the current rem/px ratio
measurement to `<h1>`". Scaling the composition preserves that ratio for free.

So the `clamp()` in Task 2 takes a floor **below** the base:

```css
zoom: clamp(var(--index-scale-min), <computed>, var(--index-scale-cap));
```

`--index-scale-min` is not a guess. Measure it: the largest value at which the
H1 holds one line at the narrowest desktop window (1200px, the breakpoint),
with the longest headline the page can render. Record the number and the date.
Expect roughly 0.85; do not ship that figure without measuring it.

**Dark divider contrast is a real defect.** `--shell-border` is
`rgba(241, 237, 228, 0.14)` (`static/css/shell.css:41`), which composites to
roughly 1.4:1 against the dark page. The non-text requirement is 3:1.

## Owner decisions needed before Task 2 and Task 3

- [x] **Firefox in the gate -- ADOPTED (owner ruling, 2026-09-01).** The build
      is installed locally. Task 2 adds Firefox alongside Chromium so every
      visual check runs in both engines, and the CI workflow installs it the
      same way it installs Chromium. Note the cost honestly in the PLAYBOOK
      entry: gate wall-time roughly doubles. The two engines measured
      identically here, so the value is regression insurance against a future
      divergence, not a defect this catches today.
- [x] **Header density -- RULED (owner, 2026-09-02).** The header scales with
      the viewport. The baseline is **not** the 1080p rendering: the reference
      is how the navbar renders at 1440p, which is smaller as a fraction of the
      page. So at 1080p the header becomes smaller than it is today, and the
      1440p appearance is what the proportion locks to.

      Measured source today: `.site-header__nav-link` is `min-height: 3rem`
      (48px) with `min-width: clamp(5.75rem, 7.25vw, 7.25rem)`. That clamp
      reaches its 116px cap at roughly 1600px, so 1080p and 1440p render
      identical pixels and only the screen fraction differs. That is why the
      1440p rendering reads as correct and the 1080p one reads as chunky.

      The header stays outside the composition `zoom`; it takes its own
      viewport-proportional sizing. Do not fold it into `--index-scale-*`.

      **Floor: 44px, ruled 2026-09-02.** A strict viewport fraction would take
      the 48px link to `48 * 1920/2560 = 36px` at 1080p, under the touch
      minimum in `AGENTS.md` "UI and Accessibility Rules" item 2 and reversing
      the 48px desktop target F-B21-29 established. So the header scales but
      never goes below 44px on its smaller side: 44px at 1080p, 48px at 1440p,
      growing above that.

      Express it as a clamp on the existing properties rather than a second
      scale variable, so the header keeps one sizing mechanism:

      ```css
      .site-header__nav-link {
        min-height: clamp(2.75rem, 1.875vw, 3.5rem);
        min-width: clamp(5.75rem, 4.53vw, 7.25rem);
      }
      ```

      `1.875vw` is `48px / 2560px`; `4.53vw` is `116px / 2560px`. Both reproduce
      today's 1440p rendering exactly at 2560 CSS px, which is the reference the
      owner approved. Measure the rendered values at both windows before
      accepting; do not trust the arithmetic alone. Mirror the same treatment on
      the theme control and the bar height, and keep one consistent sibling gap
      (F-B21-29).

## Global constraints

- **The working branch is `wip/batch-21`**, at `origin/main` (`f202b81`) in the
  `impeccable-init` worktree. The guard exits 0.

  Work started on `wip/batch-21-owner-review`. The guard raised WT003, because
  PLAYBOOK Section 3 names `wip/batch-21` for the active batch. On 2026-09-01
  the owner ruled the branch should follow the PLAYBOOK, not the reverse. Local
  `wip/batch-21` was reset to `origin/main`. Nothing was lost: `aadf2b7` is
  unchanged on `origin/wip/batch-21` and its content is already in `origin/main`.
  `wip/batch-21-owner-review` still exists at `f202b81` with no unique commits.

  Do not create a worktree, do not reset again, do not force-push without a
  separate owner ruling.
- **Check the upstream before any push.** `git branch -f` reset this branch's
  upstream to `origin/main` as a side effect, and a bare `git push` would then
  target `main`. It was restored. Verify with
  `git rev-parse --abbrev-ref --symbolic-full-name '@{u}'`; the answer must be
  `origin/wip/batch-21`.
- **Run every command from the worktree, and check that first.** There are two
  checkouts and they are on different branches:

  | Path | Branch |
  | --- | --- |
  | `C:\Users\peter\Python Projects\ScrobbleScope` | `codex/impeccable-init`, 27 behind |
  | `C:\Users\peter\.config\superpowers\worktrees\ScrobbleScope\batch-21\impeccable-init` | `wip/batch-21` |

  A session can start with its working directory in the **primary checkout**,
  which is where the SessionStart hook then reads state from. That hook printed
  `Next expected work package: WP-4` and `822 passed` on 2026-09-01 while the
  real answers were WP-5 and 870, because the primary checkout is parked 27
  commits behind on an already-merged branch. Do not take the hook's derived
  state as current until the branch line above it says `wip/batch-21` **and**
  the path is the worktree.

  Both checkouts have uncommitted edits to `PLAYBOOK.md` and
  `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`, for unrelated reasons. A
  bare `git add PLAYBOOK.md` from the wrong directory therefore stages the wrong
  work onto the wrong branch and still looks plausible. Confirm with
  `git rev-parse --abbrev-ref HEAD` before the first `git add` of every task, or
  pass `git -C <worktree>` throughout.
- Preserve the untracked `.impeccable/`, `PRODUCT.md`, `graphify-out/`, and both
  plan files. Never stage them.
- The worktree guard exits 0 on `wip/batch-21`. It reports WARNING WT010 while
  files are uncommitted. That is expected and is not a fault. If WT003 appears,
  the branch is wrong; stop and check, do not edit the PLAYBOOK to match.
- **Commands are written in primary-checkout form**, as every document in this
  repository writes them. `AGENTS.md` "Session Bootstrap" states the single
  conversion rule: from a linked worktree, run each one through the qualified
  path the worktree guard prints. That rule is not repeated at each command
  here. No second virtual environment.
- Every commit carries its dated PLAYBOOK Section 4 entry in the same commit,
  then `doc_state_sync.py --fix`. These are side-task entries: insert directly
  **after** `<!-- DOCSYNC:CURRENT-BATCH-END -->`, untagged.
- Stage paths by name. Never `git add -A` or `git add .`. No `Co-authored-by`.
- Stop for owner review after each task. Do not push, open a PR, or merge.

---

## Task 1: Restore the design snapshot and re-home its decisions

> **ALREADY DONE -- verify, do not redo. Checked 2026-09-01.**
>
> The restoration landed as `eeaa1a8` on `wip/batch-21`, unpushed. It was
> committed by another local process on 2026-09-01 at 22:41, not by the session
> that wrote this plan.
> Confirm in three commands rather than trusting this note:
>
> ```powershell
> git diff --stat b4e23bf HEAD -- docs/design/README.md   # empty = identical
> ls tests/test_design_snapshot.py                        # exists
> rg -c "Header pills|Form help affordance" docs/design/RECONCILIATION.md
> ```
>
> PLAYBOOK Section 4 carries the entry
> "2026-09-01 - Restore design snapshot provenance and re-home overrides".
>
> **Only Step 6 is outstanding, and only in part.** The declaration hardening
> is applied as far as the mechanism allows. `eeaa1a8` added `expect` to the
> snapshot sites whose patterns have a capturing group -- 6 of 8 for the Adobe
> kit id, 3 of 5 for the heatmap window.
>
> **The 44px touch-target declaration cannot be fixed this way.** Its patterns
> carry no capturing group, so they are presence-only and `expect` has nothing
> to bind to. The deadlock is still real there: raising the touch minimum would
> force an edit to three snapshot files that the digest test now forbids. The
> likely remedy is dropping the snapshot sites from that declaration, since the
> snapshot is digest-guarded already. Left open; decide it when the touch
> minimum actually changes.
>
> Steps 1 to 5 below are kept as the record of what was done and why.

`docs/design/README.md` is the verbatim design import and the canonical
specification. Two commits edited it in place: `624ebb9` and `17ca9eb`. Editing
the snapshot to agree with the code destroys its only function, which is the
ability to disagree. `docs/design/RECONCILIATION.md` exists precisely so
overrides live outside the snapshot.

Nothing canonical was lost -- the shadow values survive in
`docs/design/tokens/elevation.css`. The drift is 12 insertions and 11 deletions,
plus a stripped byte-order mark.

**This is not a blind revert.** Several edits encode real decisions made after
the import: the header pills became production navigation, a determinate
hairline replaced the progress bar, the theme marker is `data-theme`, and runs
expire after two idle hours. Those decisions stay. They move to
`RECONCILIATION.md` as override rows.

**Files:**
- Modify: `docs/design/README.md` (restore to the `b4e23bf` import)
- Modify: `docs/design/RECONCILIATION.md` (add override rows)
- Create: `tests/test_design_snapshot.py`
- Modify: `.docsync.toml` (give snapshot sites an explicit `expect`)
- Modify: `PLAYBOOK.md`, `.claude/SESSION_CONTEXT.md`

- [ ] **Step 1: Write the failing snapshot test**

`.pre-commit-config.yaml:2` excludes `docs/` from every hook, so no hook can
guard this. pytest is not excluded, so the guard goes there.

Create `tests/test_design_snapshot.py`:

```python
"""Guard the verbatim design import against in-place edits.

`docs/design/README.md` and the files under `docs/design/tokens/` are a
snapshot of the owner's design project, imported byte-for-byte by `b4e23bf`.
Their value is that they can disagree with the implementation. An agent that
edits the snapshot to match the code silently removes the only independent
check on the code. Overrides belong in `docs/design/RECONCILIATION.md`.

To change a digest here you must be re-importing from the design project, not
reconciling with the repository.
"""

import hashlib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

#: SHA-256 of each imported file, as committed by `b4e23bf`. Update ONLY on a
#: fresh import from the design project.
SNAPSHOT_DIGESTS = {
    "docs/design/README.md": "<fill in Step 3>",
}


@pytest.mark.parametrize("relative_path", sorted(SNAPSHOT_DIGESTS))
def test_imported_design_file_is_unedited(relative_path):
    """The snapshot must match its import digest byte for byte."""
    path = REPO_ROOT / relative_path
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    assert actual == SNAPSHOT_DIGESTS[relative_path], (
        f"{relative_path} was edited in place. Record the override in "
        f"docs/design/RECONCILIATION.md instead, or update this digest only "
        f"when re-importing from the design project."
    )
```

- [ ] **Step 2: Run it and confirm it fails**

```powershell
pytest tests/test_design_snapshot.py -q
```

Expected: FAIL, because the placeholder digest cannot match.

- [ ] **Step 3: Restore the file and record its true digest**

Git Bash mangles `git show <rev>:<path>`; use PowerShell.

```powershell
git show b4e23bf:docs/design/README.md | Set-Content -NoNewline -Encoding utf8 docs/design/README.md
git diff --stat -- docs/design/README.md
```

Confirm the diff reverses exactly the 12 insertions and 11 deletions, and that
the leading byte-order mark returns. Then record the digest:

```powershell
(Get-FileHash docs/design/README.md -Algorithm SHA256).Hash.ToLower()
```

Paste that value into `SNAPSHOT_DIGESTS`.

- [ ] **Step 4: Run the test and confirm it passes**

```powershell
pytest tests/test_design_snapshot.py -q
```

Expected: PASS.

- [ ] **Step 5: Re-home every decision the edits carried**

Add these rows to the override table in `docs/design/RECONCILIATION.md`, so the
restoration loses no decision. Each row names the repository as the owner of the
value, which is the file's stated purpose.

| Point | README says | This repo does | Why |
| --- | --- | --- | --- |
| Header pills | Prototype scaffolding, do not build | Production navigation: Home, Heatmap, Results, Unmatched | Owner decision, `624ebb9` |
| Loading progress signal | A progress bar | One slim determinate hairline; the pinwheel is status motion only | Owner decision, `17ca9eb`; the "exactly one progress signal" rule is preserved, the hairline is that signal |
| Heatmap H1 copy | "A year of listening, *one grid.*" | "Your last 365 days, *one grid.*" | Owner copy change, `17ca9eb` |
| Heatmap mode card copy | "The heatmap always covers the last 365 days. No other settings." | "Your listening heatmap covers the last 365 days." | Owner copy change, `17ca9eb` |
| Release filter label | "Album release filter" | "Release filter" | Owner review, WP-4 |
| Run lifetime | Not specified | In-memory runs expire after two idle hours; clean routes recover the latest run from browser-session pointers | WP-4 |
| Form help affordance | `?` in a circle for tooltips | No `?` control where label and inline copy already explain; a data tooltip stays valid on a heatmap cell | Owner review, `17ca9eb` |

The theme-marker row already exists; do not duplicate it.

- [ ] **Step 6: Stop docsync from asking for snapshot edits**

The digest test and `.docsync.toml` will deadlock without this step, and the
deadlock is the reason the snapshot was edited in the first place.

`.docsync.toml` lists snapshot files as ordinary `[[value]]` sites. A site with
`expect` states its own value, so a code change moves `expect`. A site without
`expect` only has to **agree** with the other sites, so a code change can be
satisfied either by fixing the code or by editing the document. docsync cannot
tell those apart, and the second is cheaper. The gate therefore rewarded exactly
the edit this task is undoing.

Three declarations have snapshot sites with no `expect`:

| Declaration | Snapshot files it can demand edits to |
| --- | --- |
| the 44px minimum touch target | `README.md`, `components/forms/Stepper.prompt.md`, `reference/audit-review.md` |
| the Adobe Fonts kit id | `README.md`, `reference/design-system-readme.md`, `tokens/typography.css`, `tokens/fonts.css` |
| the heatmap window length | `README.md`, `reference/design-system-readme.md`, `components/heatmap/HeatmapFrame.prompt.md` |

Give every `docs/design/` site in those three an explicit `expect` holding what
the snapshot says today. The snapshot then states a value and the code is
compared against it, which is the direction the import was always meant to run.
A future divergence fails with the snapshot named as the authority, and the fix
is a `RECONCILIATION.md` row, not an edit.

`docs/design/RECONCILIATION.md` is **not** a snapshot file. It is the
repository's own override list, written here rather than imported. Leave its
sites alone and keep it out of
`SNAPSHOT_DIGESTS`.

Prove the new `expect` values are live rather than decorative: change one of
them by a digit, re-run `--check`, confirm it fails, and change it back.

- [ ] **Step 7: Document, validate, commit**

Add a PLAYBOOK Section 4 side-task entry directly after
`<!-- DOCSYNC:CURRENT-BATCH-END -->`, explaining that the snapshot was edited in
place, what guards it now, and that the decisions moved rather than vanished.
Leave the Section 3 branch line alone. It names `wip/batch-21` and the work is
now on that branch, so the guard already exits 0.

```powershell
python scripts/doc_state_sync.py --fix
pytest -q
pre-commit run --all-files
python scripts/doc_state_sync.py --check
git diff --check
```

```powershell
git add docs/design/README.md docs/design/RECONCILIATION.md tests/test_design_snapshot.py .docsync.toml PLAYBOOK.md .claude/SESSION_CONTEXT.md docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md
git commit -m "fix(design): restore the imported snapshot and re-home its overrides"
```

Stop for owner review.

---

## Task 2: Make the gate model real windows, then fix the scale in pure CSS

The gate change and the CSS change ship together. The gate change alone turns
the suite red, and a red commit must not be left standing.

**Files:**
- Modify: `scripts/dev/frontend_gate.py` (`check_large_display_scale_parity`)
- Modify: `static/css/index.css:118-133`
- Modify: `static/js/index.js:1-24` (delete the scale block)
- Modify: `PLAYBOOK.md`, `.claude/SESSION_CONTEXT.md`, `FINDINGS.md`,
  `BATCH21_DEFINITION.md`, `docs/design/RECONCILIATION.md`

**Interfaces:**
- Consumes: the `min-width: 1200px` desktop breakpoint, the measured 673px
  natural composition height, the existing 1.075 base, and the 1.45 cap
  resolved in Task 3.
- Produces: one CSS declaration that scales both composition wrappers with
  window width, guarded by window height, with no JavaScript.

- [ ] **Step 1: Replace the gate's viewport matrix with real window geometry**

In `check_large_display_scale_parity`, replace the display-panel dimensions with
window content-box dimensions, and document why.

**Measure the chrome height before writing these numbers. Do not inherit them.**
Owner ruling 2026-09-01: the reference browser is a **default fresh Chrome
install** -- maximised, no extensions, no bookmarks bar, 100% page zoom, 100% OS
scaling. That reference matters because the owner's own Firefox runs the
Sideberry sidebar, which pushes usable width in and makes their captures narrower
than the reference.

The heights below assume 168px of chrome, inherited from a Firefox-with-extras
estimate. Fresh Chrome on Windows 11 is nearer 90px, which would make these
roughly `1920x990`, `2560x1350` and `3840x2070`. Take one real measurement,
maximised on the owner's panel, and record the number and the date:

There is no helper script for this. Run it inline, and close the browser in a
`finally` so a failure cannot leave a window open (Anti-Pattern 5):

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    # channel="chrome" drives the installed Chrome, not Playwright's bundled
    # Chromium, so the toolbar is the real one. Playwright creates a fresh
    # temporary profile per launch, which IS the fresh-install baseline: no
    # extensions, no bookmarks bar, 100% zoom.
    browser = p.chromium.launch(
        headless=False, channel="chrome", args=["--start-maximized"]
    )
    try:
        page = browser.new_context(no_viewport=True).new_page()
        page.goto("about:blank")
        print(page.evaluate(
            "({w: innerWidth, h: innerHeight, "
            " sw: screen.width, sh: screen.height, dpr: devicePixelRatio})"
        ))
    finally:
        browser.close()
```

Three things this gets right, and each was a way to get it wrong:

- **`channel="chrome"`.** Bundled Chromium has a different toolbar from Chrome,
  so its chrome height is not the baseline the owner named.
- **A fresh temporary profile.** Do not measure against the owner's daily
  Chrome. Their profile carries extensions and a bookmarks bar, and the owner's
  Firefox captures are already narrowed by the Sideberry sidebar.
- **`no_viewport=True`.** Without it Playwright forces its own viewport and
  `innerHeight` reports that instead of the real window -- the same blindness
  this whole task exists to fix.

**Measure, do not infer.** Do not reason about whether a bookmarks bar is
showing, or add an allowance for one. Take the number the fresh profile reports,
record it with the date, and use it. Run it once per panel the owner has.

The direction of the error is safe either way -- a shorter assumed window makes
the height guard bind earlier, never later -- but the comment must not state a
number nobody measured.

```python
    #: Real browser windows, not display panels. `set_viewport_size` sets the
    #: content box to exactly the number given, so measuring at 2560x1440 tests
    #: a geometry no reader has: a maximised browser on a 1440p panel reports an
    #: innerHeight well below 1440, because chrome takes the rest. Measuring the
    #: panel height is why the 2026-08-28 scale defect passed this gate while the
    #: owner's window showed 2.9% growth. Reference browser: a default fresh
    #: Chrome install, maximised, no extensions, no bookmarks bar, 100% zoom.
    #: Heights measured <DATE>; re-measure if the reference changes.
    windows = {
        "1080p": (1920, 912),
        "1440p": (2560, 1272),
        "4K": (3840, 1992),
    }
```

- [ ] **Step 2: Add the assertion that would have caught this**

Absolute per-profile scale values are brittle and were the reason the defect hid.
Assert the *relationship* instead: the composition must actually grow between one
window and the next. Add after the existing per-profile checks:

```python
    # The defect this catches: on 2026-08-28 the form measured 408px at 1080p
    # and 420px at 1440p, a 2.9% change the owner correctly read as "the same
    # width". A ratio floor fails on that and cannot be satisfied by a formula
    # that discards the width term.
    # Measure the HERO, not the form. The form caps at 37.5rem and is never
    # zoomed, so it is flat between these two windows by design; asserting
    # growth on it would fail correct code.
    growth = (
        measured_sizes["1440p"]["hero composition"]["width"]
        / at_1080p["hero composition"]["width"]
    )
    if growth < 1.20:
        failures.append(
            f"/: hero composition grows only {growth:.3f}x from a real 1080p "
            f"window to a real 1440p window; expected at least 1.20x"
        )
```

- [ ] **Step 3: Run the gate and confirm it fails**

```powershell
python scripts/dev/frontend_gate.py
```

Expected: FAIL. `form composition grows only 1.029x ...`, plus per-profile scale
mismatches, because the JavaScript formula is height-limited.

- [ ] **Step 4: Replace the JavaScript scale with one CSS declaration**

In `static/css/index.css`, replace the `@media (min-width: 1200px)` scale block
at lines 118-133:

```css
/* Scale each desktop composition as one unit, so the type, control and spacing
   relationships inside both columns are preserved instead of growing selected
   pieces independently.

   The guard divides window height by the composition's own natural height, not
   by the 1080px design viewport. Dividing by 1080 was the 2026-08-28 defect:
   browser chrome keeps innerHeight far below the display height while
   innerWidth stays near it, so an unconditional min() against 1080 discarded
   the width term on every real window and pinned the factor near 1.0.

   `tan(atan2(<length>, <length>))` is the supported way to get a plain number
   from two lengths; `zoom` rejects a length outright and falls back to 1 with
   no error, so a bare `vw` value here would fail silently. The first `zoom`
   line is the fallback for engines without trigonometric functions. */
@media (min-width: 1200px) {
  .index-grid {
    grid-template-columns: 3fr 5fr;
  }

  /* Hero only. The form must never carry zoom -- see "widen, not magnify". */
  .index-hero__inner {
    zoom: var(--index-scale-base);
    zoom: clamp(
      var(--index-scale-base),
      calc(
        var(--index-scale-base) *
        min(
          tan(atan2(100vw, var(--index-scale-width-ref))),
          tan(atan2(100vh, var(--index-natural-height)))
        )
      ),
      var(--index-scale-cap)
    );
  }
}
```

Declare the tokens once, near the top of `static/css/index.css`:

```css
:root {
  /* Measured 2026-09-01 at zoom 1: hero column 324px, form column 673px. The
     height guard uses the taller. Re-measure if the form gains or loses a row;
     an over-large value makes the guard bind too early and stops the growth. */
  --index-natural-height: 673px;
  --index-scale-width-ref: 1920px;
  --index-scale-base: 1.075;
  /* Capped at the 1440p value the owner can verify on real hardware. Width
     beyond 2560 CSS px goes to margin, not magnification. See "Lower the
     hero's cap" in Task 3 for the display-scaling table behind this. */
  --index-scale-cap: 1.45;
}
```

Delete lines 1-24 of `static/js/index.js` -- `WIDE_DESKTOP_BASE_SCALE`,
`WIDE_DESKTOP_SCALE_CAP`, `syncWideDesktopScale`, its call, `scaleAnimationFrame`
and the `resize` listener. Keep everything from `document.addEventListener('DOMContentLoaded'` onward.

- [ ] **Step 5: Run the gate and confirm it passes**

```powershell
python scripts/dev/frontend_gate.py
```

Expected: PASS. Confirm the reported form widths are near 482px at 1920x912 and
630px at 2510x1110. If `clamp()` rejects the custom properties, inline the
literals and keep the comment; verify by reading the computed `zoom`, never by
reading the source.

- [ ] **Step 6: Prove the guard still protects a short window**

```powershell
python scripts/dev/frontend_gate.py
```

The existing compact-height check at 1920x900 must still pass with the decade
selector driven and thresholds open: the submit button's bottom edge at or above
the viewport bottom, with no document scrolling at default zoom. If it fails,
`--index-natural-height` is too small; re-measure rather than guessing.

- [ ] **Step 7: Correct every live document that describes the old formula**

The formula is quoted in more than one place. Grep before editing, per the
Anti-Pattern Registry:

```powershell
rg -n -i 'viewportHeight / 1080|innerHeight / 1080|index-wide-scale|1\.075 .{0,3} max\(1' BATCH21_DEFINITION.md FINDINGS.md PLAYBOOK.md .claude\SESSION_CONTEXT.md docs\design static scripts
```

Correct each active claim. Hits inside dated PLAYBOOK Section 4 entries are
point-in-time records and stay as written. In `FINDINGS.md`, F-B21-24 is
currently marked resolved by the 2026-08-28 refinement; reopen it with the
measured evidence, and state plainly that the cause was the denominator, not the
browser. Do not write that the defect was Firefox-specific.

- [ ] **Step 8: Document, validate, commit**

```powershell
python scripts/doc_state_sync.py --fix
pytest -q
pre-commit run --all-files
python scripts/doc_state_sync.py --check
git diff --check
```

```powershell
git add static/css/index.css static/js/index.js scripts/dev/frontend_gate.py BATCH21_DEFINITION.md FINDINGS.md docs/design/RECONCILIATION.md PLAYBOOK.md .claude/SESSION_CONTEXT.md docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md
git commit -m "fix(index): scale the desktop composition with the real window"
```

Stop for owner review.

---

## Task 3: Widen the composition and raise divider contrast

**Files:**
- Modify: `static/css/index.css` (grid split, form cap)
- Modify: `static/css/shell.css:22, 41` (divider tokens)
- Modify: `static/css/tailwind.src.css` and regenerate `static/css/tailwind.css`
- Modify: `scripts/dev/frontend_gate.py`
- Modify: `tests/test_template_shell.py`
- Modify: `BATCH21_DEFINITION.md`, `docs/design/RECONCILIATION.md`, `PLAYBOOK.md`

- [ ] **Step 1: Add the failing split, cap and contrast checks**

Extend `check_large_display_scale_parity` with:

```python
    if abs(layout_1080p["grid_right"] / layout_1080p["grid_left"] - (4 / 3)) > 0.02:
        failures.append("/: wide index split is not 3fr 4fr")

    # 37.5rem (600px) at a 16px root. No scale factor: the form is not zoomed.
    expected_cap = 37.5 * 16
    for label in ("1080p", "1440p"):
        actual = measured_sizes[label]["form composition"]["width"]
        if abs(actual - expected_cap) > 2:
            failures.append(
                f"/: form cap is {actual:.0f}px at a real {label} window, "
                f"expected {expected_cap:.0f}px"
            )
```

Add a divider-contrast check that composites `--shell-border` over its adjacent
surface in both themes and requires 3:1. Measure the composite, not the token
string -- the token carries alpha and the alpha is the defect.

- [ ] **Step 2: Run the gate and confirm all three fail**

```powershell
python scripts/dev/frontend_gate.py
```

Expected: FAIL on the 5:3 split, on the 408px cap against an expected 482px, and
on dark divider contrast near 1.4:1.

- [ ] **Step 3: Apply the split and the cap**

In `static/css/index.css`, inside the `min-width: 1200px` block, change
`grid-template-columns` to `3fr 4fr`. Then make the form **widen and lock**
rather than magnify -- it must carry no `zoom` at any size:

```css
/* Widens, then locks. Type, 44px touch targets and the 16px input floor stay
   exactly as designed at every display size.
   Derivation: 23.75rem (380px) at the 1200px breakpoint, reaching the 37.5rem
   (600px) lock at 1920px. slope = (600-380)/(1920-1200) = 0.3056 -> 30.56vw;
   intercept = 380 - 0.3056*1200 = 13.3px = 0.83rem.
   Check: 1200px -> 380px, 1920px -> 600px, 2560px -> 795px clamped to 600px,
   so 1080p and 1440p render the same 600px card. */
.index-form__inner {
  width: 100%;
  max-width: clamp(23.75rem, 0.83rem + 30.56vw, 37.5rem);
  margin: 0 auto;
}
```

Update the comment above it, which still explains a 380px cap.

**Lower the hero's cap from `2.15` to `1.45` (resolved 2026-09-01).** The
earlier open question asked the owner to judge a 4K composition. That question
was mostly fictional: scale is driven by the **CSS** viewport, and a 4K desktop
runs at 150% or 200% OS scaling, so the browser reports 2560x1440 or 1920x1080 --
not 3840x2160.

| Display / OS scaling | CSS viewport | scale |
| --- | --- | --- |
| 1080p, 100% | 1920x1080 | 1.075 |
| 1440p 27", 100% | 2560x1440 | 1.433 |
| 4K 27", 200% (typical) | 1920x1080 | 1.075 |
| 4K 27", 150% | 2560x1440 | 1.433 |
| 1440p, 125% | 2048x1152 | 1.147 |
| 4K 32", 100% (rare) | 3840x2160 | 2.150 |

A 4K user at normal scaling lands on one of the two profiles the owner can
verify on their own hardware. Those two cover the great majority of desktop
monitors.

So cap at `1.45`, just above the verifiable 1440p value, and let width beyond
2560 CSS px go to margin rather than magnification. Nothing then ships at a
scale factor nobody has looked at, and a 4K-at-100% user is treated as 1440p,
which is defensible since they already chose small UI at the OS level. Set
`--index-scale-cap: 1.45`. Revisit only if a real 4K-at-100% complaint appears.

**Ultrawide is out of scope.** The owner ruled it a non-issue on 2026-09-01:
those users rarely run a full-width browser window, so it is a fraction of a
fraction. The `1.45` cap already gives an ultrawide a sane composition. Do not
add an ultrawide profile to the gate and do not design for it.

Keep the `@media (max-width: 859.98px)` rule that removes the cap on mobile.
Keep the `min-width: 1200px and max-height: 900px` padding rule.

**The `28rem` cap is superseded. Owner review 2026-09-02.** The owner widened
the card in Chrome DevTools -- source untouched -- and ruled the wider card the
better default. Direction agreed:

- The **card** widens well past `28rem`, then locks. Still never zoomed.
- The **controls do not inherit that width.** Stretching every field is a side
  effect of `width: 100%`, not a decision. At the reviewed width the username
  field ran about 605px for a 6-15 character handle, `Rank by` gave each half
  about 300px, and `Listening year` put its label roughly 600px from its
  stepper. Cap the fields that have no use for the space.
- **Open, needs an owner ruling:** whether to pair fields at the wider card --
  `Listening year` beside `Release filter`, `Rank by` beside `Show`. That uses
  the width structurally and shortens the card, but it is a layout change, not
  a width change.

**The card width is `37.5rem` (600px), owner-set 2026-09-02.** That is the value
the owner reached in DevTools, not a screenshot estimate. It locks at 1920px, so
1080p and 1440p both render a 600px card -- the same visual size on both, which
is what Ruling A asks for. Verify the rendered width before accepting it.

Do not implement the slider treatment for nested cards; that still needs a fresh
owner decision after the visual pass.

- [ ] **Step 4: Raise divider contrast in both themes**

In `static/css/shell.css`, raise the `--shell-border` alpha in each theme block
until the composite clears 3:1 against its adjacent surface. Do not add a shadow.
Mirror any duplicated token in `static/css/tailwind.src.css`, then regenerate:

```powershell
python scripts/dev/tailwind_build.py
git diff --stat -- static/css/tailwind.css
```

A rebuilt but unstaged `tailwind.css` reports as drift because `git diff`
compares the tree to the index. Stage it; that is the hook working.

- [ ] **Step 5: Render the header-density candidate and stop**

Render the 1440p navigation density at 1920x1080 beside the widened form with the
decade selector and thresholds expanded. Record footer space, one-row navigation
and action reachability. Present the comparison and **stop for the owner ruling**
before adopting or discarding it. In either outcome the header stays outside the
composition zoom.

- [ ] **Step 6: Confirm the H1 stays on one line**

The H1 must not wrap or clip at **any** desktop width, not only when
maximised. Owner report 2026-09-02: it newlines when the window is not
maximised. Assert `headline_line_count == 1` across the desktop range -- at
1200px (the breakpoint), at an intermediate windowed width such as 1500px, and
at 1920 and 2560 -- not only at the wide profiles. Below the 860px breakpoint
normal wrapping stays available. This is what `--index-scale-min` buys, so a
failure here means the floor is too high, not that the H1 needs its own rule.

- [ ] **Step 7: Document, validate, commit**

Run the full gate sequence, then:

```powershell
git add static/css/index.css static/css/shell.css static/css/tailwind.src.css static/css/tailwind.css scripts/dev/frontend_gate.py tests/test_template_shell.py BATCH21_DEFINITION.md docs/design/RECONCILIATION.md PLAYBOOK.md .claude/SESSION_CONTEXT.md docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md
git commit -m "refactor(ui): widen the desktop index composition"
```

Stop for owner review.

---

## Task 4: Align visible loading progress with pipeline phases

Carried forward from the superseded plan's Task 2, whose baseline verified
correct: `set_job_progress` has no `phase` keyword, `static/js/loading-progress.js`
does not exist, and `loading.js` and `heatmap.js` each drive the hairline from
top-level progress alone.

**Files:**
- Modify: `scrobblescope/repositories.py:56-91`, `scrobblescope/routes.py:313-344`
- Modify: `scrobblescope/orchestrator.py`, `scrobblescope/heatmap.py`
- Create: `static/js/loading-progress.js`
- Modify: `static/js/loading.js`, `static/js/heatmap.js`,
  `templates/loading.html`, `templates/index.html`
- Modify: `static/css/loading.css`, `static/css/heatmap.css`
- Modify: `tests/test_repositories.py`, `tests/test_routes.py`,
  `tests/services/test_orchestrator_fetch_and_process.py`,
  `tests/services/test_orchestrator_fetch_spotify.py`, `tests/test_heatmap.py`,
  `scripts/dev/frontend_gate.py`

- [ ] **Step 1: Write the failing repository and route contract tests**

`phase` must be copied, not aliased, and must have three distinct update modes.

```python
phase = {"key": "lastfm_fetch", "label": "Fetching scrobbles",
         "unit": "page", "current": 23, "total": 102}
set_job_progress(job_id, progress=20, message="Fetching scrobbles", phase=phase)
phase["current"] = 99
assert get_job_progress(job_id)["phase"]["current"] == 23

set_job_progress(job_id, message="Still fetching")
assert get_job_progress(job_id)["phase"]["key"] == "lastfm_fetch"

set_job_progress(job_id, phase=None)
assert "phase" not in get_job_progress(job_id)
```

Add a `/progress` test asserting the exact JSON phase payload survives the route,
and that the no-job and error responses stay compatible with no `phase` key.

- [ ] **Step 2: Run and confirm they fail**

```powershell
pytest tests/test_repositories.py tests/test_routes.py -q
```

Expected: `set_job_progress()` rejects the unknown `phase` keyword.

- [ ] **Step 3: Add additive repository support with an explicit sentinel**

An omitted argument and an explicit `None` must do different things, so a plain
message-only update cannot silently clear the phase.

```python
_UNSET = object()

def set_job_progress(..., phase=_UNSET):
    ...
    if phase is not _UNSET:
        if phase is None:
            job["progress"].pop("phase", None)
        else:
            job["progress"]["phase"] = dict(phase)
```

In `get_job_progress`, copy `progress["phase"]` when present, as `stats` already
is. Never emit `phase: null`; an absent key keeps current clients unchanged.

- [ ] **Step 4: Populate counted phases and clear uncounted ones**

```python
# Both Last.fm callbacks
phase={"key": "lastfm_fetch", "label": "Fetching scrobbles",
       "unit": "page", "current": pages_done, "total": total_pages}

# Album Spotify search callback
phase={"key": "spotify_search", "label": "Searching Spotify",
       "unit": "album", "current": searches_done, "total": total_searches}

# Album Spotify detail-batch callback
phase={"key": "spotify_details", "label": "Fetching Spotify details",
       "unit": "batch", "current": batches_done, "total": num_batches}
```

Pass `phase=None` explicitly at initialization, aggregation, filtering, result
assembly, error and completion. Keep the top-level percent mappings unchanged.

Extend the service tests to assert the exact phase dictionaries for the Last.fm
`(23, 102)`, Spotify search and Spotify detail paths. Keep their existing
state-side-effect assertions; do not replace them with mock-call-only checks.

- [ ] **Step 5: Create one browser helper and move both clients onto it**

Create `static/js/loading-progress.js` as a small non-module global, loaded
before `loading.js` and `heatmap.js`:

```js
window.ScrobbleProgress = {
  displayPercent(payload) {
    const phase = payload.phase;
    if (Number.isFinite(phase?.current) && Number.isFinite(phase?.total) && phase.total > 0) {
      return Math.max(0, Math.min(100, (phase.current / phase.total) * 100));
    }
    return Math.max(0, Math.min(100, Number(payload.progress) || 0));
  },
  label(payload) {
    const phase = payload.phase;
    if (!phase) return payload.message || 'Initializing...';
    const prefix = phase.label.toUpperCase();
    return Number.isFinite(phase.current) && Number.isFinite(phase.total)
      ? `${prefix} \u00b7 ${phase.unit.toUpperCase()} ${phase.current} / ${phase.total}`
      : prefix;
  },
};
```

Add a shared updater taking `{track, bar, phaseText, payload, previousPhaseKey}`.
When the phase key changes, remove the transition, set `scaleX(0)`, and restore
the transition on the second `requestAnimationFrame` before applying the new
phase-local fraction, so the reset is instant rather than animating backward.
Every update sets `transform: scaleX(displayPercent / 100)`, `aria-valuenow` to
the same rounded percentage, and `aria-valuetext` to `label(payload)`.

Both clients call this helper. Do not animate `width`, `height`, `padding`,
`margin` or `max-width`.

- [ ] **Step 6: Add one opacity-only entrance and reduced-motion behaviour**

Apply the same short entrance to the shared loading composition in `loading.css`
and `heatmap.css`: pinwheel, track, phase line and visible stats animate through
opacity only. The final state must be visible under
`@media (prefers-reduced-motion: reduce)` -- cancelling an animation that fades
in from zero also requires restoring `opacity: 1`. Keep the existing heatmap
cached-result handoff. Do not add a heading, a navigation pill, cancellation, or
a second percentage.

- [ ] **Step 7: Add real-browser progress checks**

Extend the gate with a fixture job returning these sequential payloads to each
client:

```python
{"progress": 20, "phase": {"key": "lastfm_fetch", "label": "Fetching scrobbles", "unit": "page", "current": 23, "total": 102}}
{"progress": 90, "phase": {"key": "lastfm_fetch", "label": "Fetching scrobbles", "unit": "page", "current": 90, "total": 100}}
{"progress": 92, "message": "Counting daily scrobbles"}
```

For the counted frames assert the bar's computed transform matrix and
`aria-valuenow` correspond to `23 / 102` and `90 / 100`, and that
`aria-valuetext` carries the exact label and fraction. For the uncounted frame
assert the bar falls back to top-level 92 and the phase line shows no stale page
count. Run the equivalent checks against album `/loading` and the heatmap
in-page loader.

- [ ] **Step 8: Document, validate, commit**

Update the active WP-4 text in `BATCH21_DEFINITION.md`: counted phases display
their count and drive the hairline; uncounted work clears phase and uses overall
progress. Correct any live statement that `/heatmap_data` is polled as progress
-- the client polls `/progress` and requests heatmap data only after completion.

```powershell
rg -n 'transition:\s*(width|height|padding|margin|max-width)' static\css static\js
```

Must return no production animation of those properties. Then the full sequence:

```powershell
git commit -m "fix(progress): align loading signals with pipeline phases"
```

Stop for owner review.

---

## Task 5: Add the unmatched no-data surface

Carried forward from the superseded plan's Task 3, baseline verified:
`unmatched_page`'s no-job branch calls `_render_no_job_state`
(`scrobblescope/routes.py:561`), which renders `error.html`, while
`results_empty.html`, `heatmap_empty.html` and `empty.css` already exist.

**Files:**
- Modify: `scrobblescope/routes.py`
- Create: `templates/unmatched_empty.html`
- Modify: `tests/test_routes.py`, `scripts/dev/frontend_gate.py`
- Modify: `PLAYBOOK.md`, `.claude/SESSION_CONTEXT.md`

- [ ] **Step 1: Write failing route tests for absent and expired album jobs**

```python
response = client.get("/unmatched")
assert response.status_code == 200
assert b'data-empty-state="unmatched"' in response.data
assert b"No unmatched albums yet" in response.data
assert b'href="/"' in response.data
assert b"Search albums" in response.data
assert b"error-code" not in response.data
```

Create an expired `latest_album_job_id` in the client session, request
`/unmatched`, and assert the pointer is removed and the same template returns.
Keep the existing populated-unmatched and zero-row valid-job tests; they prove
the report route did not change.

- [ ] **Step 2: Run and confirm current behaviour fails**

```powershell
pytest tests/test_routes.py -q
```

Expected: the no-job route renders `error.html`.

- [ ] **Step 3: Create the template and route to it**

Create `templates/unmatched_empty.html` following `results_empty.html`, loading
only `tailwind.css` and `empty.css`:

```html
<main class="empty-page" data-empty-state="unmatched">
  <section class="empty-state" aria-labelledby="unmatched-empty-title">
    <span class="empty-state__signal" aria-hidden="true"></span>
    <h1 id="unmatched-empty-title">No unmatched albums yet</h1>
    <p>Run an album search to find albums that need a review.</p>
    <a class="empty-state__action" href="/">Search albums</a>
  </section>
</main>
```

In the no-valid-album-job and expired-pointer branch of `unmatched_page`, render
this template instead of `_render_no_job_state`. Keep `unmatched.html` for valid
album jobs, including a valid run with zero unmatched rows. Add no outline,
shadow, icon, error status, or Bootstrap dependency.

- [ ] **Step 4: Extend the browser gate**

Add `/unmatched` to `check_destination_empty_states`. Assert no `.card`, no box
shadow on `.empty-state`, a usable Home action, and that the action target is
`/`. Re-run the populated route checks to confirm report navigation still returns
to `/results`.

- [ ] **Step 5: Document, validate, commit**

The PLAYBOOK entry must say this is a normal no-data condition, not an error
treatment, and that valid unmatched reports are unchanged.

```powershell
git commit -m "refactor(ui): unify the unmatched empty state"
```

Stop for owner review.

---

## Task 6: Accessibility pass

Runs after the visual work is accepted, as the owner specified.

- [ ] **Step 1: Contrast**

Small text and both divider tokens, measured as composites in light and dark.
Non-text needs 3:1; small muted copy needs 4.5:1. Keep the 12px small-label
floor, the `0.04em` phrase-mark tracking and the `#6c6676` light muted token --
they already pass; test them rather than replacing them.

- [ ] **Step 2: Keyboard and focus**

Traverse by tab. A scripted `.focus()` stops matching `:focus-visible` once the
page has seen a click, so it reports a missing focus ring that is not missing.
Confirm every control is reachable, including the decade pills, the release-year
field and the thresholds disclosure, which all start hidden.

- [ ] **Step 3: Progress ARIA**

`aria-valuenow` and `aria-valuetext` agree exactly with the displayed fraction in
both clients, across a phase switch and an uncounted frame.

- [ ] **Step 4: Reduced motion**

The loading composition and the index entrance reach their visible final state
with no animation. Confirm no element that fades in from zero is left hidden.

- [ ] **Step 5: Touch targets**

Existing coarse-pointer minimums hold at 44px. Key on
`@media (any-pointer: coarse)`, never on a max-width -- a touch laptop is wide
and touched.

- [ ] **Step 6: Document, validate, commit**

```powershell
git commit -m "fix(a11y): close the owner-review accessibility pass"
```

---

## Final acceptance

- [ ] **Step 1: Sweep the branch diff, not one task's commits**

```powershell
git diff origin/main...HEAD --stat
rg -n -i 'viewportHeight / 1080|3fr 5fr|23\.75rem|index-wide-scale|fills its well|Firefox' BATCH21_DEFINITION.md FINDINGS.md PLAYBOOK.md .claude\SESSION_CONTEXT.md docs\design
```

Correct every active affirmative claim. Hits inside dated Section 4 entries are
point-in-time records and stay. Do not leave any live document saying the scale
defect was Firefox-specific.

- [ ] **Step 2: Run every gate**

```powershell
pytest -q
python scripts/dev/frontend_gate.py
pre-commit run --all-files
python scripts/doc_state_sync.py --check
python scripts/dev/check_worktree_alignment.py
git status --short
```

Status must show only intentional files. `.impeccable/`, `PRODUCT.md`,
`graphify-out/` and both plan files stay untracked.

- [ ] **Step 3: Owner visual acceptance**

At 1080p and 1440p, in the owner's own browser:

1. Wordmark, H1, type, controls and form grow together between the two
   displays; the wordmark-to-H1 relationship holds; the H1 stays on one line.
2. The form occupies materially more of its column than before and the dead
   space is reduced.
3. The header keeps its pills and theme control on one readable row and does not
   inherit the composition scale.
4. Both dividers read clearly in dark mode without shadows.
5. With decade selection and thresholds open at roughly 1920x900, submit and the
   filter tags stay reachable without document scrolling.
6. Both loaders show one pinwheel, one hairline matching `23 / 102` and
   `90 / 100`, correct ARIA, no backward animation at a phase switch, and a
   visible reduced-motion final state.
7. `/unmatched` before a search and after an expired pointer shows the borderless
   no-data page; a real unmatched report still renders its reason groups.

- [ ] **Step 4: Request integration authorization**

Ask whether to push and open a PR from `wip/batch-21`. The push needs
`--force-with-lease`, because local `wip/batch-21` was reset to `origin/main`
while `origin/wip/batch-21` still holds `aadf2b7`. That lease needs its own
owner ruling; it is not covered by this plan. PR #220 is merged and must not be
reopened. Do not rebase-merge, clean up the worktree, or realign anything
without a separate explicit instruction.

## Plan self-review

- **Spec coverage:** Task 1 restores provenance and guards it. Task 2 fixes the
  measured root cause and the gate blindness that hid it. Task 3 delivers the
  width the owner asked for and the contrast defect. Tasks 4 and 5 carry forward
  the two verified-unshipped items. Task 6 is the accessibility pass.
- **Intentional exclusions:** no nested-card slider, no widening past `37.5rem`, no
  cancellation, no navigation regrouping, no WP-5 leaderboard work, no edits to
  dated archive history.
- **Known risk:** `--index-natural-height` is a measured constant that goes stale
  if the form gains or loses a row. Task 2 Step 6 is the check that catches it;
  if it proves fragile in practice, promote it to a `.docsync.toml` DOC009
  declaration so the value cannot drift silently.
