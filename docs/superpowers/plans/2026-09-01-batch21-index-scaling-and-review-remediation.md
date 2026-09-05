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
JavaScript scale with one shared pure-CSS factor applied through layout values
and, in the same commit, re-points the browser gate at window geometry that
actually exists -- the gate change is what makes the defect visible, so the two
cannot be separated. Task 3 widens the composition and raises divider contrast.
Tasks 4 and 5 are the already-specified progress-phase and unmatched-empty work.
Task 6 is the accessibility pass the owner asked to run last.

**Tech Stack:** Flask, Python 3.13, Jinja2, vanilla browser JavaScript, Tailwind
v4 generated CSS, pytest, Playwright frontend gate.

---

## Why this plan supersedes the 2026-09-01 remediation plan

`docs/superpowers/plans/2026-09-01-owner-review-remediation.md` is a tracked
historical plan written before the failure was diagnosed. This plan is the
canonical execution plan, subject to later owner rulings and the active batch
definition. Keep the earlier plan for reference; do not execute it. Its Tasks 2 and 3 are sound and are carried forward here almost
unchanged. Its Task 1 rests on four claims that measurement disproved.

| Claim in that plan | Measured reality |
| --- | --- |
| The failure is a Firefox rendering problem; Firefox is the acceptance gate. | The failure reproduces in Chromium. It is engine-independent; Firefox remains required regression coverage. |
| The `zoom` mechanism is unproven and may need replacing. | Engine parity proved only that both browsers implement it alike. The owner rejected `zoom` on 2026-09-04; replace it with layout-aware proportional values. |
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
so Firefox alone would leave the gate's viewport blindness (defect B)
untouched. Firefox is still adopted as independent regression coverage. The
acceptance gate is **realistic window geometry in both engines**.

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

| Window | scale today | form today | corrected factor | form @ 28rem base | height guard |
| --- | --- | --- | --- | --- | --- |
| 1920x912 (real 1080p) | 1.075 | 408px | 1.075 | 482px | 1.35 |
| 2510x1110 (owner capture) | 1.105 | **420px** | **1.405** | **629px** | 1.65 |
| 2490x1230 (owner capture) | 1.224 | 465px | 1.394 | 625px | 1.83 |
| 2560x1272 (real 1440p) | 1.266 | 481px | 1.433 | 642px | 1.89 |
| 2560x1440 (**gate only**) | 1.433 | 545px | 1.433 | 642px | 2.14 |

The corrected factor applies to the complete index composition. The form card,
its type, controls, spacing, hero and wordmark all grow by the same relationship
from 1080p through the 2.15 4K ceiling. The header remains shell-sized and
independent. The 28rem value is the remediation plan's unscaled form cap; its
rendered width expands with the shared factor.

The owner sees 420px at 1440p against 408px at 1080p: a 2.9% difference, which
is why the report is "the width of the form is the same". The gate sees 545px
against 408px, a 33% difference, and passes. **The gate measures a geometry no
browser window has**, because `page.set_viewport_size` sets the content box to
exactly the number given. No maximised browser on a 1440p panel has an
`innerHeight` of 1440.

The height-guard column is why the fix is safe: 1.35 to 1.89, always above the
width factor, so the guard never binds on a normal window and still catches a
genuinely short one.

**Two independent defects.** The formula uses the display height instead of the
673px natural composition height, so browser chrome suppresses cross-monitor
growth. The layout also keeps the old `3fr 5fr` split and 23.75rem base form
cap instead of the remediation plan's `3fr 4fr` split and 28rem base cap.

**Proportional layout, no CSS `zoom` (owner clarification, 2026-09-04).** The
staged scale checkpoint in `stash@{0}` proves the intended relationship:
hero, form, fields and mode controls grow together while navigation does not.
Its CSS `zoom` plus JavaScript implementation is not approved. Do not use CSS
`zoom`, browser zoom, or a visual-only `transform`; all three obscure layout,
focus, scrolling or engine behavior.

Use one dimensionless `--index-scale` computed from real viewport geometry,
then apply it through layout-aware CSS values: the form's max width, type,
control sizes, padding, margins and gaps. Preserve the repository unit rule:
remains in rem-based calculations; borders, outlines, radii and other fine
detail stay px. The frontend gate measures rendered rectangles and ratios, not
the implementation property, so an omitted dimension cannot hide behind a
plausible scale token.

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

**The fix is a measured lower bound on the shared layout factor, not a fluid H1.**
Wrapping happens because the hero column narrows while the current composition
cannot shrink: its factor is floored at 1.075 and only ever grows.

Making the H1 alone fluid would break the annotation's own constraint --
"Logo scale should increase slightly, without changing the current rem/px ratio
measurement to `<h1>`". Scaling the composition preserves that ratio for free.

So the `clamp()` in Task 2 takes a floor **below** the base:

```css
--index-scale: clamp(var(--index-scale-min), <computed>, 2.15);
```

`--index-scale-min` is not a guess. Measure it: the largest value at which the
H1 holds one line at the narrowest desktop window (1200px, the breakpoint),
with the longest headline the page can render. Record the number and the date.
Expect roughly 0.85; do not ship that figure without measuring it.

**Dark divider contrast is a real defect.** `--shell-border` is
`rgba(241, 237, 228, 0.14)` (`static/css/shell.css:41`), which composites to
roughly 1.4:1 against the dark page. The non-text requirement is 3:1.

## Owner decisions governing Task 2 and Task 3

- [x] **Complete composition scaling, without `zoom` -- CLARIFIED (owner,
      2026-09-04).** `docs/superpowers/plans/2026-09-01-owner-review-remediation.md`
      remains authoritative for the outcome: hero, wordmark, form, type,
      controls and spacing grow proportionally from 1080p through the 4K cap.
      The form width expands; it is not a fixed 600px card. CSS `zoom`,
      browser zoom and visual-only transforms are rejected implementation
      mechanisms. Use layout-aware responsive values and prove the rendered
      ratios in both engines. The header alone remains independent.
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

      The header stays outside the composition scale; it takes its own
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

- **The working branch is `wip/batch-21`** in the existing
  `impeccable-init` worktree. It is the source branch for PR #221; do not
  assume it is still parked at the historical `f202b81` base. Refresh
  `origin` and let `check_worktree_alignment.py` report the current
  comparison before each task. Do not create another worktree, reset history
  or force-push without a separate owner ruling.
- **Check the upstream before any push.** `git branch -f` reset this branch's
  upstream to `origin/main` as a side effect, and a bare `git push` would then
  target `main`. It was restored. Verify with
  `git rev-parse --abbrev-ref --symbolic-full-name '@{u}'`; the answer must be
  `origin/wip/batch-21`.
- **Run every command from the worktree, and check that first.** There are two
  checkouts; only this exact path is the execution target:

  | Path | Branch |
  | --- | --- |
  | `C:\Users\peter\Python Projects\ScrobbleScope` | primary checkout; tool provider only |
  | `C:\Users\peter\.config\superpowers\worktrees\ScrobbleScope\batch-21\impeccable-init` | `wip/batch-21` |

  A session can start in the primary checkout and read plausible but unrelated
  state. Confirm the path and `wip/batch-21` before the first command and
  before every staging operation.
- Preserve the untracked `.impeccable/`, `PRODUCT.md`, `graphify-out/`, and
  `docs/superpowers/plans/2026-09-01-owner-review-remediation.md`. The Batch
  21 plan in this PR is tracked and is staged only when intentionally changed.
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
> The restoration landed as `eeaa1a8` on `wip/batch-21`. It was
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
> Steps 1 to 5 below are kept as the record of what was done and why. Checked
> boxes are supported by the tree and commits `eeaa1a8` and `5b7e675`;
> `eeaa1a8` restored README, and `5b7e675` extended its guard to all 61 files.
> Step 2 remains unchecked
> because the historical placeholder-digest failure was not independently
> observed during this verification.

`docs/design/README.md` is part of the verbatim design import and is historical
evidence, not current visual authority. Two commits edited it in place:
`624ebb9` and `17ca9eb`. Editing the snapshot to agree with the code destroys
its only function, which is the ability to disagree.
`docs/design/RECONCILIATION.md` exists precisely so repository decisions live
outside the snapshot.

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

- [x] **Step 1: Write the snapshot test -- complete in `eeaa1a8`**

`.pre-commit-config.yaml:2` excludes `docs/` from every hook, so no hook can
guard this. pytest is not excluded, so the guard goes there.

Create `tests/test_design_snapshot.py`:

```python
"""Guard the verbatim design import against in-place edits.

The 61 design-project files under `docs/design/` are a byte-for-byte snapshot
imported by `b4e23bf`; `f857ac2` later corrected the location of `styles.css`
without changing its bytes. Their value is that they can disagree with the
implementation. An agent that edits the snapshot to match the code silently
removes the only independent check on the code. Overrides belong in the
repository-owned `docs/design/RECONCILIATION.md`, which is excluded here.

To change a digest here you must be re-importing from the design project, not
reconciling with the repository.
"""

import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_ROOT = REPO_ROOT / "docs" / "design"
REPOSITORY_OWNED_PATHS = frozenset({"RECONCILIATION.md"})

#: Aggregate manifest of every imported path and byte. Update ONLY on a fresh
#: import from the design project.
SNAPSHOT_FILE_COUNT = 61
SNAPSHOT_TREE_DIGEST = "<fill in Step 3>"


def _snapshot_tree_digest() -> tuple[int, str]:
    """Hash the complete imported manifest with stable, unambiguous framing."""
    paths = sorted(
        (
            path
            for path in SNAPSHOT_ROOT.rglob("*")
            if path.is_file()
            and path.relative_to(SNAPSHOT_ROOT).as_posix() not in REPOSITORY_OWNED_PATHS
        ),
        key=lambda path: path.relative_to(SNAPSHOT_ROOT).as_posix(),
    )
    digest = hashlib.sha256()
    for path in paths:
        relative_bytes = path.relative_to(SNAPSHOT_ROOT).as_posix().encode("utf-8")
        content = path.read_bytes()
        digest.update(len(relative_bytes).to_bytes(4, "big"))
        digest.update(relative_bytes)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return len(paths), digest.hexdigest()


def test_imported_design_tree_is_unedited() -> None:
    """Every imported design path and byte must match the guarded manifest."""
    actual = _snapshot_tree_digest()
    expected = (SNAPSHOT_FILE_COUNT, SNAPSHOT_TREE_DIGEST)
    assert actual == expected, (  # nosec B101 - pytest rewrites assertions.
        f"docs/design snapshot changed: expected {expected}, got {actual}. "
        "Record repository overrides in docs/design/RECONCILIATION.md, or "
        "update this manifest only when re-importing from the design project."
    )
```

- [ ] **Step 2: Run it and confirm it fails -- historical red run not verified**

```powershell
pytest tests/test_design_snapshot.py -q
```

Expected: FAIL, because the placeholder digest cannot match. The failure prints
the actual file count and aggregate digest.

- [x] **Step 3: Restore the file and record the true tree manifest -- complete through `5b7e675`**

Git Bash mangles `git show <rev>:<path>`; use PowerShell.

```powershell
git restore --source=b4e23bf --worktree -- docs/design/README.md
git diff --stat -- docs/design/README.md
```

Confirm the diff reverses exactly the 12 insertions and 11 deletions, and that
the leading byte-order mark returns. Run the focused test again and copy the
reported `(file count, digest)` into `SNAPSHOT_FILE_COUNT` and
`SNAPSHOT_TREE_DIGEST`:

```powershell
pytest tests/test_design_snapshot.py -q
```

This manifest covers every imported file, not only README or the token
directory. A file edit, rename, addition or deletion must change it.

- [x] **Step 4: Run the test and confirm it passes -- current test is green**

```powershell
pytest tests/test_design_snapshot.py -q
```

Expected: PASS.

- [x] **Step 5: Re-home every decision the edits carried -- complete in `eeaa1a8`**

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

- [ ] **Step 6: Stop docsync from asking for snapshot edits -- partially complete**

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
sites alone and keep it in `REPOSITORY_OWNED_PATHS`, outside the aggregate
snapshot manifest.

Prove the new `expect` values are live rather than decorative: change one of
them by a digit, re-run `--check`, confirm it fails, and change it back.

Commit `eeaa1a8` began hardening snapshot sites whose declaration pattern exposes
a captured value. The 44px touch-target sites remain presence-only and cannot
bind an `expect`; keep that deadlock deferred unless the touch minimum changes.

- [x] **Step 7: Document, validate, commit -- complete in `eeaa1a8`**

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

**Execution checkpoint 2026-09-05:** Task 2 implementation is complete and
validated; owner review is the remaining gate. The two-engine runner and CSS
dimension inventory are implemented locally, and the complete frontend gate
passed in isolation (22 checks, 62 runs, Chromium and Firefox). Measurements
and the expanded-state guard correction are recorded in `FINDINGS.md`
F-B21-38. PLAYBOOK Sections 3-4 own current status and validation results.
The original owner-review notes remain historical; this plan owns the
superseding execution requirements.

The gate change and the CSS change ship together. The gate change alone turns
the suite red, and a red commit must not be left standing.

**Files:**
- Modify: `scripts/dev/frontend_gate.py` (browser lifecycle and
  `check_large_display_scale_parity`)
- Modify: `tests/scripts/dev/test_frontend_gate.py`
- Modify: `.github/workflows/test.yml`
- Modify: `static/css/index.css:118-133`
- Modify: `static/js/index.js:1-24` (delete the scale block)
- Modify: `.docsync.toml` (repoint scale declarations to CSS ownership)
- Modify: `PLAYBOOK.md`, `.claude/SESSION_CONTEXT.md`, `FINDINGS.md`,
  `BATCH21_DEFINITION.md`, `docs/design/RECONCILIATION.md`

**Interfaces:**
- Consumes: the `min-width: 1200px` desktop breakpoint, the measured 673px
  natural composition height, the existing 1.075 base, and the remediation
  plan's 2.15 cap.
- Produces: one shared, dimensionless CSS layout factor that scales the full
  index composition with real window geometry, with no JavaScript, CSS
  `zoom`, or visual transform.

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

- [ ] **Step 2: Run the complete visual matrix in Chromium and Firefox**

The owner adopted Firefox for regression insurance, so changing only the scale
check is incomplete. Make the browser lifecycle itself engine-aware:

1. Set `BROWSER_NAMES = ("chromium", "firefox")` and change
   `SETUP_COMMAND` to `python -m playwright install chromium firefox`.
2. Replace `_launch_chromium` with
   `_launch_browser(playwright, browser_name, *, headless=True)`. Resolve the
   Playwright browser by name, preserve the `--headed` flag, and name the
   missing engine plus `SETUP_COMMAND` in its error.
3. In `main`, launch each browser in order, run the entire `CHECKS` matrix,
   prefix every returned failure with the browser name, and close that browser
   in `finally` before launching the next one. One engine failing must not
   leave the other process open.
4. Multiply `PLANNED_RUNS` by `len(BROWSER_NAMES)`, and print both browser
   names in the success line. This makes a silently skipped engine visible.
5. Extend `tests/scripts/dev/test_frontend_gate.py` to prove selection,
   default/headed launch options, actionable per-engine missing-binary errors,
   both-engine execution, failure prefixes, and closure on a raised check.
6. Change the CI install command to:

   ```powershell
   python -m playwright install --with-deps chromium firefox
   ```

The real-window dimensions in Step 1 still come from the owner-approved fresh
Chrome reference. Both Playwright engines consume those same content-box
profiles; Firefox is a second renderer, not a second geometry specification.
Record in PLAYBOOK that the complete gate's wall time is expected to roughly
double.

- [ ] **Step 3: Make the gate assert rendered proportional relationships**

`check_large_display_scale_parity` was written around the staged JavaScript
plus CSS-`zoom` attempt. Step 5 removes that mechanism but preserves its
intended complete-composition growth. Retune the gate away from a computed
`zoom` property and toward rendered rectangles, type sizes and ratios.

In `scripts/dev/frontend_gate.py`, inside `check_large_display_scale_parity`:

1. Delete the per-profile `zoom` checks for both wrappers. Assert instead that
   their rendered width/height relationships follow the same expected factor.
2. Keep `input` and `mode tab` in `scalable_dimensions`, and add the form
   card, submit button, representative type and vertical spacing. These are
   part of the complete composition, not fixed shell dimensions.
3. Keep
   `expected_form_width = 23.75 * 16 * expected_scales[label]` through Task 2.
   Task 3 changes only the unscaled base cap from 23.75rem to 28rem; the factor
   remains.
4. Recompute `expected_scales` from the real windows fixed in Step 1, the
   1920px width reference, the measured 673px natural-height guard, the
   measured minimum, the 1.075 base and the 2.15 remediation ceiling.
5. Keep page navigation, the theme control, borders, outlines and radii in the
   fixed/fine-detail set. The header must not inherit `--index-scale`.

On mobile, assert the desktop factor is absent and the existing one-column,
coarse-pointer behavior is unchanged. Do not assert a `zoom` value that the
approved implementation is forbidden to set.

Then add the relationship check. Absolute per-profile scale values are brittle
and were the reason the defect hid. Assert the *relationship* instead: the
composition must actually grow between one window and the next. Add after the
existing per-profile checks:

```python
    # The defect this catches: on 2026-08-28 the form measured 408px at 1080p
    # and 420px at 1440p, a 2.9% change the owner correctly read as "the same
    # width". A ratio floor fails on that and cannot be satisfied by a formula
    # that discards the width term.
    for name in ("hero composition", "form composition"):
        growth = (
            measured_sizes["1440p"][name]["width"]
            / at_1080p[name]["width"]
        )
        if growth < 1.20:
            failures.append(
                f"/: {name} grows only {growth:.3f}x from a real 1080p "
                f"window to a real 1440p window; expected at least 1.20x"
            )
```

Before choosing the floor, measure it at the boundary that constrains it. At a
1200px-wide desktop viewport, test both mode headlines and sweep candidate
layout-factor values through the same explicit dimensions Step 5 will ship.
Choose the largest value for which the longest headline still has one rendered
line; record the value, browser, and date. Expect roughly 0.85, but do not turn
that estimate into source. Task 3 Step 6 makes the one-line relationship a
permanent multi-width assertion.

- [ ] **Step 4: Run the gate and confirm it fails**

```powershell
python scripts/dev/frontend_gate.py
```

Expected: FAIL. Both composition wrappers report growth well below the required
relationship at the owner's real 1440p geometry, because the JavaScript formula
is height-limited. A failure naming only the hero is incomplete.

- [ ] **Step 5: Replace JavaScript and `zoom` with a CSS layout factor**

Delete lines 1-24 of `static/js/index.js` -- `WIDE_DESKTOP_BASE_SCALE`,
`WIDE_DESKTOP_SCALE_CAP`, `syncWideDesktopScale`, its call,
`scaleAnimationFrame` and the `resize` listener. Keep everything from
`document.addEventListener('DOMContentLoaded'` onward.

In `static/css/index.css`, replace the `@media (min-width: 1200px)` scale
block. The factor is inherited data for explicit layout calculations; it is
not itself a rendering shortcut:

```css
/* Scale the complete desktop composition through its authored dimensions.
   Never apply this factor through zoom or transform: both hide whether layout,
   scrolling, focus geometry and touch targets actually grew.

   The guard divides window height by the composition's own natural height, not
   by the 1080px design viewport. Dividing by 1080 was the 2026-08-28 defect:
   browser chrome keeps innerHeight far below the display height while
   innerWidth stays near it, so an unconditional min() against 1080 discarded
   the width term on every real window and pinned the factor near 1.0.

   `tan(atan2(<length>, <length>))` turns each viewport/reference pair into a
   dimensionless number. The first assignment is a deliberate fallback; the
   two-engine rendered-ratio gate stays red if an engine cannot use the fluid
   expression. */
@media (min-width: 1200px) {
  .index-grid {
    --index-scale: var(--index-scale-base);
    --index-scale: clamp(
      var(--index-scale-min),
      calc(
        var(--index-scale-base) *
        min(
          tan(atan2(100vw, var(--index-scale-width-ref))),
          tan(atan2(100vh, var(--index-natural-height)))
        )
      ),
      var(--index-scale-cap)
    );
    grid-template-columns: 3fr 5fr;
  }

  .index-hero__mark {
    max-width: calc(35rem * var(--index-scale));
  }

  .index-hero__headline {
    font-size: calc(2.625rem * var(--index-scale));
  }

  .index-form__inner {
    max-width: calc(23.75rem * var(--index-scale));
  }
}
```

Those three declarations are examples, not the complete inventory. Sweep every
non-fine-detail dimension below `.index-hero__inner` and
`.index-form__inner`: type sizes and line heights, control dimensions, card
padding, field margins, gaps, disclosure/stepper geometry and submit sizing.
Express each from its existing rem base and `var(--index-scale)`. Do not scale
borders, outlines or radii, and do not weaken coarse-pointer 44px minimums.
After the sweep, the gate's wordmark/H1, field/submit and inter-control ratios
must match the 1080p baseline in both engines.

Declare the tokens once, near the top of `static/css/index.css`:

```css
:root {
  /* Measured 2026-09-01 at zoom 1: hero column 324px, form column 673px. The
     height guard uses the taller. Re-measure if the form gains or loses a row;
     an over-large value makes the guard bind too early and stops the growth. */
  --index-natural-height: 42.0625rem;
  --index-scale-width-ref: 1920px;
  --index-scale-base: 1.075;
  /* The floor sits below the base so the complete composition can contract at
     the 1200px boundary. Measure it with the longest headline; do not ship the
     roughly-0.85 estimate without rendered evidence. */
  --index-scale-min: <measured in Step 3>;
  /* The owner remediation requires proportional growth through 4K. */
  --index-scale-cap: 2.15;
}
```

`--index-scale-base` stays the multiplier inside the calculation.
The measured 673px height is 42.0625rem at the measured 16px root. Keep that
denominator font-relative so it follows the content when a reader raises the
default font size. Exercise a 20px root in both engines and restore page state
after the check; an enlarged root must not be treated as a fixed-pixel panel.
`--index-scale-min` governs contraction below the 1920px reference, and 2.15
is the 4K ceiling from the owner remediation. If the CSS arithmetic is not
supported in either engine, stop and choose another layout-aware mechanism;
never fall back to `zoom` or `transform`.

- [ ] **Step 6: Run the gate and confirm it passes**

```powershell
python scripts/dev/frontend_gate.py
```

Expected: PASS in both engines. Before Task 3 changes the base cap, the form is
about 408px at a real 1080p window and 545px at a real 1440p window; the exact
figures come from the measured window matrix. Confirm both hero and form cross
the 1.20 growth floor and their representative type, controls and spacing keep
the baseline ratios. Verify rendered geometry, never only the custom-property
string.

- [ ] **Step 7: Prove the guard still protects a short window**

```powershell
python scripts/dev/frontend_gate.py
```

The existing compact-height check at 1920x900 must still pass with the decade
selector driven and thresholds open: the submit button's bottom edge at or above
the viewport bottom, with no document scrolling at default zoom. If it fails,
`--index-natural-height` is too small; re-measure rather than guessing.

- [ ] **Step 8: Correct every live document that describes the old formula**

The formula is quoted in more than one place. Grep before editing, per the
Anti-Pattern Registry:

```powershell
rg -n -i 'viewportHeight / 1080|innerHeight / 1080|index-wide-scale|1\.075 .{0,3} max\(1' BATCH21_DEFINITION.md FINDINGS.md PLAYBOOK.md .claude\SESSION_CONTEXT.md docs\design static scripts
```

Correct each active claim. Hits inside dated PLAYBOOK Section 4 entries are
point-in-time records and stay as written. In `FINDINGS.md`, F-B21-24 is already
reopened; preserve that status and update its evidence to state plainly that the
cause was the denominator, not the browser. Do not write that the defect was
Firefox-specific or mark it resolved until the replacement passes the rendered
gate.

In `.docsync.toml`, repoint the wide-desktop baseline and cap sites from the
deleted JavaScript constants to `--index-scale-base` and
`--index-scale-cap` in `static/css/index.css`. Keep the mechanism generic:
the TOML names this repository's duplicated facts; no ScrobbleScope scale name
belongs in `scripts/docsync/`.

- [ ] **Step 9: Document, validate, commit**

```powershell
python scripts/doc_state_sync.py --fix
pytest -q
pre-commit run --all-files
python scripts/doc_state_sync.py --check
git diff --check
```

```powershell
git add static/css/index.css static/js/index.js scripts/dev/frontend_gate.py tests/scripts/dev/test_frontend_gate.py .github/workflows/test.yml .docsync.toml BATCH21_DEFINITION.md FINDINGS.md docs/design/RECONCILIATION.md PLAYBOOK.md .claude/SESSION_CONTEXT.md docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md
git commit -m "fix(index): scale the desktop composition with the real window"
```

Stop for owner review.

---

## Task 3: Widen the composition and raise divider contrast

**Owner clarification 2026-09-05:** The 28rem base cap is approved at 1080p
too. Retain the Task 3 instructions below; Task 2 keeps its interim 23.75rem
base until this task runs.

**Files:**
- Modify: `static/css/index.css` (grid split, form cap)
- Modify: `static/css/shell.css` (divider tokens and ruled header sizing)
- Modify: `static/css/tailwind.src.css` and regenerate `static/css/tailwind.css`
- Modify: `scripts/dev/frontend_gate.py`
- Modify: `tests/scripts/dev/test_frontend_gate.py`
- Modify: `tests/test_template_shell.py`
- Modify: `BATCH21_DEFINITION.md`, `docs/design/RECONCILIATION.md`, `PLAYBOOK.md`

- [ ] **Step 1: Add the failing split, cap and contrast checks**

Change `check_large_display_scale_parity`, rather than adding alongside it.
The split and form-cap assertions below **replace** existing ones; leaving the
originals in place is the same defect Task 2 Step 3 exists to prevent.

The split check already exists and reads the ratio the other way round. Retune
it in place -- `measure_wide_layout` returns `applicationWidth` and `heroWidth`,
and no `grid_left` or `grid_right` key exists:

```python
    # Was 5 / 3. Task 3 narrows the application column to 3fr 4fr.
    split_ratio = layout_1080p["applicationWidth"] / layout_1080p["heroWidth"]
    if abs(split_ratio - (4 / 3)) > 0.02:
        failures.append(
            f"/: wide desktop split is {split_ratio:.3f}, expected 4:3 application-to-hero"
        )
```

Then replace only the unscaled base in Task 2's proportional form-width
assertion:

```python
    # 28rem is the remediation plan's base cap. The rendered card expands by
    # the same layout factor as the rest of the composition.
    expected_base_cap = 28 * 16
    for label in ("1080p", "1440p", "4K"):
        expected = expected_base_cap * expected_scales[label]
        actual = measured_sizes[label]["form composition"]["width"]
        if abs(actual - expected) > 2:
            failures.append(
                f"/: form cap is {actual:.0f}px at a real {label} window, "
                f"expected proportional {expected:.0f}px"
            )
```

Do not add a fixed control cap. Keep the Task 2 proportional assertions for
field width and height, mode tabs, card padding, submit sizing, type and gaps;
Task 3 changes their 1080p base through the 28rem form cap and preserves every
ratio at 1440p and 4K. Drive both mode panels before measuring; hidden controls
are not evidence.

Also assert computed `zoom` is `1`/`normal` and `transform` is `none` on
both composition wrappers, both cards and representative controls.
Mutation-check each prohibition by temporarily adding `zoom: 1.1` and then
`transform: scale(1.1)` to a wrapper and confirming the gate fails.

Add a divider-contrast check that composites `--shell-border` over its adjacent
surface in both themes and requires 3:1. Measure the composite, not the token
string -- the token carries alpha and the alpha is the defect.

Add the ruled header assertions in the same real-window measurement. At 1080p
and 1440p respectively, a page-nav link must compute to 44px and 48px high and
92px and 116px wide; the theme control must follow the same 44px/48px height
curve; the bar must be smaller at 1080p and reproduce its current 76px height
at 1440p. Assert that the nav and action controls stay on one row and use the
same sibling-gap token. These are computed-style and geometry checks, not
source-string checks.

- [ ] **Step 2: Run the gate and confirm the new contract fails**

```powershell
python scripts/dev/frontend_gate.py
```

Expected: FAIL on the 5:3 split, on the 23.75rem base form cap against the
expected 28rem base, on the unchanged 1080p header dimensions, and on dark
divider contrast near 1.4:1. The form already expands between real profiles
after Task 2; this task increases its proportional base width.

- [ ] **Step 3: Apply the split and proportional 28rem base cap**

In `static/css/index.css`, inside the `min-width: 1200px` block, change
`grid-template-columns` to `3fr 4fr`. Change the form's unscaled base cap
from 23.75rem to the remediation plan's 28rem. The shared Task 2 layout factor
makes the rendered width expand proportionally:

```css
/* 28rem is the unscaled design cap. The complete form composition consumes
   --index-scale through explicit layout values; this wrapper never uses zoom
   or transform. */
.index-form__inner {
  width: 100%;
  max-width: calc(28rem * var(--index-scale));
  margin: 0 auto;
}
```

Update the comment above it, which still explains a fixed 380px cap.

**Keep the remediation ceiling at `2.15` (owner clarification 2026-09-04).**
The acceptance source requires proportional growth through a 3840x2160 CSS
viewport. OS display scaling may map a physical 4K panel to a smaller CSS
viewport, but that does not remove the 4K-at-100% contract:

| Display / OS scaling | CSS viewport | scale |
| --- | --- | --- |
| 1080p, 100% | 1920x1080 | 1.075 |
| 1440p 27", 100% | 2560x1440 | 1.433 |
| 4K 27", 200% (typical) | 1920x1080 | 1.075 |
| 4K 27", 150% | 2560x1440 | 1.433 |
| 1440p, 125% | 2048x1152 | 1.147 |
| 4K 32", 100% (rare) | 3840x2160 | 2.150 |

The 2.15 ceiling prevents growth beyond the 4K reference. Ultrawide-specific
layout remains out of scope; a wider viewport still receives the same capped
composition.

Keep the `@media (max-width: 859.98px)` rule that removes the cap on mobile.
Keep the `min-width: 1200px and max-height: 900px` padding rule.

**The fixed 37.5rem card and fixed-width controls are superseded.** The
authoritative remediation keeps a 28rem unscaled cap and requires the card,
fields, mode tabs, type and spacing to follow the shared factor. Preserve the
existing single-column field structure; pairing fields or introducing the
slider treatment remains a separate owner decision after the proportional
visual pass.

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

- [ ] **Step 5: Apply the recorded header ruling and verify it**

The decision ledger already marks this ruling complete; do not stop for it
again. Apply the exact navigation clamps recorded there:

```css
:root {
  --shell-control-gap: 0.75rem;
  --shell-height: clamp(4.25rem, 2.96875vw, 4.75rem);
}

.site-header,
.site-header__nav {
  gap: var(--shell-control-gap);
}

.site-header__nav-link,
.site-header__theme-toggle {
  min-height: clamp(2.75rem, 1.875vw, 3.5rem);
}

.site-header__nav-link {
  min-width: clamp(5.75rem, 4.53vw, 7.25rem);
}

.site-header__theme-choice {
  min-height: clamp(2.25rem, 1.5625vw, 2.5rem);
}
```

The bar clamp preserves a 68px floor at 1080p and the current 76px reference
at the 2560px-wide 1440p profile: `2560px * 2.96875 / 100 = 76px`, where the profile
label names the panel resolution. The choice clamp lets the outer theme control
actually reach the ruled 44px/48px curve instead of its child forcing a fixed
48px height. Keep the header outside `--index-scale`.

Render both engines at the real 1080p and 1440p windows beside the proportional
form, with decade selection and thresholds expanded. Confirm the computed
dimensions from Step 1, one-row navigation, action reachability and available
footer space. Extend `tests/test_template_shell.py` to hold the shared gap
token and clamp declarations; the frontend gate remains the rendered proof.

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
git add static/css/index.css static/css/shell.css static/css/tailwind.src.css static/css/tailwind.css scripts/dev/frontend_gate.py tests/scripts/dev/test_frontend_gate.py tests/test_template_shell.py BATCH21_DEFINITION.md docs/design/RECONCILIATION.md PLAYBOOK.md .claude/SESSION_CONTEXT.md docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md
git commit -m "refactor(ui): widen the desktop index composition"
```

Stop for owner review.

---

## Task 4: Align visible loading progress with pipeline phases

**Loading composition corrections (owner screenshot, 2026-09-04):** remove the
secondary sentence that repeats the active phase, center the stat group when
only Pages fetched is visible, and remove `rocket scale` from the loading
parameter summary. Keep useful username and date-window context. Validate the
one-stat and multi-stat states; hiding two children must not reserve empty
columns. Counts remain subject to the accuracy contract below.

**Accuracy prerequisite (owner, 2026-09-04).** Share presentation, not pipeline
or polling state. Albums fetch Last.fm (overall 5-20%), search Spotify (20-40%)
and fetch Spotify details (40-60%) before final assembly. Heatmap fetches only
Last.fm (5-80%), then aggregates. Keep those overall mappings and each client's
retry, terminal-error and destination behavior. A phase reaching 100% must not
trigger result navigation; only overall completion with ready results does.

Counts come from the server's current phase, never reverse-calculated from
overall progress or elapsed polling ticks. Polling may skip intermediate
updates; render the latest observed snapshot without inventing missing counts.
Use distinct units for page attempts, album searches and detail batches. Cache
hits, empty phases and failures must not leave a stale preceding fraction.

F-B21-33 records two prerequisites found during the owner-requested source
check. Heatmap uses an interval that can overlap requests and apply older
responses last. Prevent overlapping polls and invalidate in-flight responses
on job replacement, stop, retry and completion; stopping a timer alone does
not cancel a pending response. Preserve its existing transient-network retry
behavior. Last.fm's callback counts completed attempts even for failed pages;
do not label that value as successfully received pages. Keep received-page
stats tied to actual successful data, and label the phase's attempted work
honestly. Include `scrobblescope/lastfm.py` and its service tests if the callback
contract must be extended; retain existing callers' compatibility.

The permanent browser checks must delay and reverse responses, replace a job
while a response is pending, and prove that stale responses cannot regress the
label, restart polling or fetch the new job's result. Exercise each pipeline's
phase transitions separately, including cache-only album work, a failed page,
unknown/zero totals, and a phase at 100% while overall progress is below 100%.
Prove returned phase snapshots remain isolated through both repository readers.

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
Exercise both repository read paths because `get_job_progress` and
`get_job_context` each construct their own progress copy:

```python
phase = {"key": "lastfm_fetch", "label": "Fetching scrobbles",
         "unit": "page", "current": 23, "total": 102}
set_job_progress(job_id, progress=20, message="Fetching scrobbles", phase=phase)
phase["current"] = 99
assert get_job_progress(job_id)["phase"]["current"] == 23
assert get_job_context(job_id)["progress"]["phase"]["current"] == 23

progress_view = get_job_progress(job_id)
context_view = get_job_context(job_id)
progress_view["phase"]["current"] = 77
context_view["progress"]["phase"]["current"] = 88
assert get_job_progress(job_id)["phase"]["current"] == 23
assert get_job_context(job_id)["progress"]["phase"]["current"] == 23

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

In both `get_job_progress` and `get_job_context`, copy `progress["phase"]` when
present, as each path already copies `stats`. The regression tests above must
mutate each returned nested dictionary and prove that neither mutation reaches
shared job state. Never emit `phase: null`; an absent key keeps current clients
unchanged.

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
    return Number.isFinite(phase.current) && Number.isFinite(phase.total) && phase.total > 0
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
the same rounded percentage, and both the visible phase line and
`aria-valuetext` to `label(payload)`. The owner confirmed on 2026-09-04 that
accurate counted phases should display their count, reaffirming the September 1
owner-remediation plan and superseding the August 28 operation-only ruling.

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
`aria-valuenow` correspond to `23 / 102` and `90 / 100`, `aria-valuetext`
carries the exact label and fraction, and the visible phase line contains the
same accurate phase-specific count. For the uncounted frame assert the bar falls back to top-level 92 and
the phase line shows no stale count. Run the equivalent checks against album
`/loading` and the heatmap in-page loader.

- [ ] **Step 8: Document, validate, commit**

Preserve the revised owner decision in `BATCH21_DEFINITION.md`: counted phase
fractions drive the visible phase line, hairline and ARIA, while uncounted work
clears phase and uses overall progress. Correct any
live statement that `/heatmap_data` is polled as progress
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

`aria-valuenow` and `aria-valuetext` agree exactly with the fraction represented
by the hairline in both clients, across a phase switch and an uncounted frame.
The visible phase line carries the same accurate phase count.

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
rg -n -i 'viewportHeight / 1080|3fr 5fr|23\.75rem|index-wide-scale|fills its well|Firefox-specific|Firefox rendering problem|Firefox is the acceptance gate|fixed 600px|37\.5rem|1\.45|hero-only' BATCH21_DEFINITION.md FINDINGS.md PLAYBOOK.md .claude\SESSION_CONTEXT.md docs\design
rg -n -i '(^|[;{[:space:]])zoom[[:space:]]*:|transform[[:space:]]*:[^;]*scale[[:space:]]*\(' static scripts templates
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
`graphify-out/` and the owner-review remediation plan stay untracked.

- [ ] **Step 3: Owner visual acceptance**

At 1080p and 1440p in the owner's own browser, plus the automated 4K
profile in both engines:

1. Wordmark, H1, type, controls and form grow together between the two
   displays; the wordmark-to-H1 relationship holds; the H1 stays on one line.
2. The form occupies materially more of its column than before and the dead
   space is reduced.
3. The header keeps its pills and theme control on one readable row and does not
   inherit the composition scale.
4. The composition wrappers, cards and representative controls compute to
   `zoom: 1`/`normal` and `transform: none`; their growth comes from layout
   dimensions, not page or visual magnification.
5. Both dividers read clearly in dark mode without shadows.
6. With decade selection and thresholds open at roughly 1920x900, submit and the
   filter tags stay reachable without document scrolling.
7. Both loaders show one pinwheel, one accurate counted phase label, one hairline
   matching `23 / 102` and `90 / 100`, matching ARIA,
   no backward animation at a phase switch, and a
   visible reduced-motion final state.
8. `/unmatched` before a search and after an expired pointer shows the borderless
   no-data page; a real unmatched report still renders its reason groups.

- [ ] **Step 4: Request integration authorization**

Refresh the remote, run the worktree guard, and inspect the current upstream
and PR state. Ask for the integration action appropriate at that time. Use a
normal fast-forward push only when the branch permits it; any force-push or
history rewrite needs its own explicit owner ruling. PR #220 is merged and must
not be reopened. Do not rebase-merge, clean up the worktree, or realign anything
without a separate explicit instruction.

## Plan self-review

- **Spec coverage:** Task 1 restores provenance and guards it. Task 2 fixes the
  measured root cause and the gate blindness that hid it. Task 3 delivers the
  width the owner asked for and the contrast defect. Tasks 4 and 5 carry forward
  the two verified-unshipped items. Task 6 is the accessibility pass.
- **Intentional exclusions:** no nested-card slider, no base-cap expansion
  beyond 28rem, no cancellation, no navigation regrouping, no WP-5 leaderboard
  work, no edits to dated archive history.
- **Known risk:** `--index-natural-height` is a measured constant that goes stale
  if the form gains or loses a row. Task 2 Step 7 is the check that catches it;
  if it proves fragile in practice, promote it to a `.docsync.toml` DOC009
  declaration so the value cannot drift silently.
