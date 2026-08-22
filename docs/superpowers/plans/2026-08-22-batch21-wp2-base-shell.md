# Batch 21 WP-2 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to
> implement this plan task-by-task.

**Goal:** Put the first template on Tailwind. Add the base shell, migrate
`error.html` as the pilot, and build the two gates that stop frontend work
from shipping broken.

**Architecture:** Strangler migration, page by page. `base.html` stops loading
Bootstrap globally and moves it to a per-page block, so a migrated page loads
only `tailwind.css` and an unmigrated page keeps Bootstrap. A small
framework-neutral `shell.css` styles the shared header on both kinds of page.
Two new gates protect the work: a `tailwind-css-drift` pre-commit hook that
rebuilds and compares, and `scripts/dev/frontend_gate.py`, a Playwright script
that starts the app and asserts what `pytest` and `pre-commit` cannot see.

**Tech Stack:** Flask, Jinja2, Tailwind v4 (standalone CLI), daisyUI v5,
Playwright 1.62.0, Adobe Fonts kit `rwy8ghw`.

**Baseline:** 633 tests passing, verified by running on 2026-08-22 at
`b020076`. Branch `wip/batch-21`, realigned onto `origin/main`, 0 ahead.

---

## Rules that apply to every task

- **Commit format.** No `Co-Authored-By` trailer. Subject and body wrap at 72
  characters. **Never `git add -A` or `git add .`** -- stage paths by name.
- **Cite by name, not by line.** Name the block, rule or function.
- **Plain English.** Short sentences. Active voice. One idea each.
- **Never hand-edit the test count** in `.claude/SESSION_CONTEXT.md`. Only
  `doc_state_sync.py --fix` writes it.
- Use the qualified binaries under
  `C:\Users\peter\Python Projects\ScrobbleScope\.venv\Scripts\`.
- **`pre-commit` can revert work.** Compare `git write-tree` before and after
  any `--all-files` run. An identical SHA proves nothing moved.

---

## Task 1: Record the type-stack reversal

The owner reversed the self-hosted ruling on 2026-08-22. Adobe Fonts kit
`rwy8ghw` wins. Four documents record the old decision. Fix them before any
code depends on them.

**Files:**
- Modify: `BATCH21_DEFINITION.md` -- owner decision 4, and font check 4 in the
  validation-gates section
- Modify: `docs/design/RECONCILIATION.md` -- decision 1, the `Type families`
  row of the fact-ownership table, and the mono-narrow note
- Modify: `CLAUDE.md` sections 3 and 7 (gitignored -- edit, do not stage)

**Step 1: Rewrite decision 4 in `BATCH21_DEFINITION.md`**

It currently reads "**Fonts (WP-2): SELF-HOSTED** woff2 files under
`static/fonts/` (Geist, Instrument Serif, JetBrains Mono -- all OFL-licensed).
No Google Fonts CDN."

Replace with the Adobe kit, the five families, and the weight scale. Say the
self-hosted ruling is withdrawn and give the date.

**Step 2: Invert font check 4 in the validation-gates section**

It currently reads "**Fonts** -- the self-hosted faces load and no request
leaves for a font CDN (decision 4 is otherwise unverified)."

It must now assert the five kit families resolve. WP-2 writes that check in
Task 7, so the contract has to be right first.

**Step 3: Rewrite `RECONCILIATION.md` decision 1 and the table row**

Decision 1 says kit `rwy8ghw` is not adopted. The `Type families` row says the
snapshot does not agree with the repo. Both now agree with the README.

**Step 4: Correct the mono-narrow note**

The note says the repo permanently runs the full-width face because no narrow
JetBrains Mono exists, and that WP-3 must measure the regression. **The kit
ships `input-mono-narrow`, so the risk resolves.** Say so and drop the
warning.

**Step 5: Update `CLAUDE.md` sections 3 and 7**

Section 7 says "Do not adopt the Adobe Typekit stack." That is now wrong.
`CLAUDE.md` is gitignored -- do not stage it.

**Step 6: Commit**

```bash
git add BATCH21_DEFINITION.md docs/design/RECONCILIATION.md
git commit -m "docs(design): adopt the Adobe Fonts type stack"
```

---

## Task 2: Switch the theme tokens

**Files:**
- Modify: `static/css/tailwind.src.css` -- the `@theme` block
- Modify: `tests/scripts/dev/test_tailwind_build_cli.py` --
  `test_theme_source_locks_the_batch_21_design_tokens`
- Regenerate: `static/css/tailwind.css`

**Step 1: Update the test first**

`test_theme_source_locks_the_batch_21_design_tokens` pins the three old font
lines in its `required_lines` set:

```python
        '--font-sans: "Geist", ui-sans-serif, system-ui, sans-serif;',
        '--font-serif: "Instrument Serif", Georgia, serif;',
        '--font-mono: "JetBrains Mono", ui-monospace, monospace;',
```

Replace with the five Adobe families:

```python
        '--font-sans: "akzidenz-grotesk-next-pro", ui-sans-serif, system-ui, sans-serif;',
        '--font-serif: "instrument-serif", Georgia, serif;',
        '--font-figure: "gotham", ui-sans-serif, sans-serif;',
        '--font-mono: "input-mono", ui-monospace, monospace;',
        '--font-mono-narrow: "input-mono-narrow", "input-mono", ui-monospace, monospace;',
```

Add two assertions that the removed weights cannot come back:

```python
    assert "--font-weight-medium" not in source
    assert "--font-weight-semibold" not in source
```

**Step 2: Run it and watch it fail**

```
.venv\Scripts\pytest.exe tests/scripts/dev/test_tailwind_build_cli.py::test_theme_source_locks_the_batch_21_design_tokens -v
```

Expected: FAIL. The source still has the old families and both weights.

**Step 3: Edit the `@theme` block in `static/css/tailwind.src.css`**

Set the five families as above. **Delete `--font-weight-medium: 500` and
`--font-weight-semibold: 600`.** Keep 300, 400 and 700 -- the kit ships no
500 or 600, so those two tokens only ever produced synthesized fakes.

**Step 4: Run the test again**

Expected: PASS.

**Step 5: Rebuild the stylesheet**

```
python scripts/dev/tailwind_build.py
```

This is the step that matters. `git diff` alone proves only that nobody
hand-edited the file. Confirm `static/css/tailwind.css` actually changed, and
that `font-medium` and `font-semibold` utilities are gone from it.

**Step 6: Run the whole suite**

```
.venv\Scripts\pytest.exe -q
```

Expected: 633 passed. This task adds no tests.

**Step 7: Commit**

```bash
git add static/css/tailwind.src.css static/css/tailwind.css tests/scripts/dev/test_tailwind_build_cli.py
git commit -m "build(css): switch the theme to the Adobe type stack"
```

---

## Task 3: F-B21-7, part one -- short reads are not tampering

`_download_verified` catches `(OSError, URLError)`. `http.client.IncompleteRead`
subclasses `HTTPException`, so it escapes that handler **and** `main`'s, and
reaches the user as a raw traceback.

The quiet case is worse. When a connection closes cleanly mid-body,
`response.read` returns empty, the loop ends, and the short file fails the
digest check. The operator is told `SHA-256 mismatch`, which reads as a
supply-chain compromise. They will investigate the wrong thing.

**Files:**
- Modify: `scripts/dev/tailwind_build.py` -- `_download_verified`
- Test: `tests/scripts/dev/test_tailwind_build.py`

**Step 1: Write the two failing tests**

```python
def test_a_truncated_download_is_reported_as_a_short_read(tmp_path: Path) -> None:
    """A connection that closes mid-body must not be blamed on the digest."""
    spec = _artifact(b"the full body")
    destination = tmp_path / spec.filename

    class _ShortResponse:
        headers = {"Content-Length": str(len(b"the full body"))}

        def read(self, _size: int) -> bytes:
            return b""

        def __enter__(self): return self
        def __exit__(self, *_): return False

    with patch("scripts.dev.tailwind_build.urlopen", return_value=_ShortResponse()):
        with pytest.raises(TailwindBuildError) as error:
            _download_verified(spec, destination)

    message = str(error.value)
    assert "truncated" in message.lower()
    assert "SHA-256 mismatch" not in message


def test_an_incomplete_read_is_translated_not_raised_raw(tmp_path: Path) -> None:
    """IncompleteRead subclasses HTTPException and would otherwise escape."""
    spec = _artifact(b"the full body")

    class _RaisingResponse:
        headers: dict[str, str] = {}

        def read(self, _size: int) -> bytes:
            raise http.client.IncompleteRead(b"partial", 6)

        def __enter__(self): return self
        def __exit__(self, *_): return False

    with patch("scripts.dev.tailwind_build.urlopen", return_value=_RaisingResponse()):
        with pytest.raises(TailwindBuildError):
            _download_verified(spec, tmp_path / spec.filename)
```

**Step 2: Run them and watch them fail**

```
.venv\Scripts\pytest.exe tests/scripts/dev/test_tailwind_build.py -k "truncated or incomplete" -v
```

Expected: the first FAILS on the message, the second FAILS with a raw
`IncompleteRead` escaping.

**Step 3: Fix `_download_verified`**

Add `import http.client` at the top. Then:

- Catch `http.client.HTTPException` alongside `(OSError, URLError)` and
  translate it to `TailwindBuildError`.
- Track bytes written. After the read loop, compare against `Content-Length`
  when the header is present. On a short body raise a distinct error naming
  the expected and received byte counts, and say the download was truncated.
- Raise it **before** the digest is computed, so a network fault can never
  surface as `SHA-256 mismatch`.

**Step 4: Run the tests again**

Expected: PASS.

---

## Task 4: F-B21-7, part two -- prove `bin_dir` is routed

`test_ensure_toolchain_checks_the_executable_and_both_bundles` patches
`required_artifacts` **and** `ensure_artifact` in the same `with` block, so no
integrity code runs inside the one test that names the property. Its assertion
reads `call.args[0]` only, so the `bin_dir` keyword is never inspected.

**Files:**
- Modify: `tests/scripts/dev/test_tailwind_build.py` --
  `test_ensure_toolchain_checks_the_executable_and_both_bundles`

**Step 1: Assert the keyword**

Keep the existing spec assertion and add:

```python
    assert [call.kwargs["bin_dir"] for call in ensure.call_args_list] == [tmp_path] * 3
```

**Step 2: Prove the mutation now fails**

Delete `bin_dir=bin_dir` from the `ensure_artifact` call inside
`ensure_toolchain`, then run the suite:

```
.venv\Scripts\pytest.exe -q
```

Expected: **FAIL.** It currently stays green across all 633 tests, which is
the defect. If it still passes, the assertion is not doing its job.

**Step 3: Restore the source**

```bash
git checkout -- scripts/dev/tailwind_build.py
```

Restore with git, never by hand.

**Step 4: Run the suite and commit**

```
.venv\Scripts\pytest.exe -q
```

Expected: 635 passed -- the 633 baseline plus Task 3's two tests.

```bash
git add scripts/dev/tailwind_build.py tests/scripts/dev/test_tailwind_build.py
git commit -m "fix(build): distinguish short downloads from digest mismatches"
```

---

## Task 5: The `tailwind-css-drift` hook

WP-2 is the first work package where a template consumes the compiled CSS, so
it is the first where drift can ship. Deferring to WP-8 would leave six work
packages unprotected.

**Files:**
- Modify: `.pre-commit-config.yaml`

**Step 1: Add the hook**

Model it on `doc-state-sync-check`, the only existing repo-local Python hook.
Append to the `local` repo block:

```yaml
      - id: tailwind-css-drift
        name: tailwind-css-drift
        entry: python scripts/dev/tailwind_build.py --check
        language: python
        pass_filenames: false
        always_run: true
```

**`always_run: true` and `pass_filenames: false` are load-bearing.** The
top-level `exclude` filters out `static/`, so a filename-driven hook would
silently never run on the one file it exists to check.

**Step 2: Add the `--check` flag to `tailwind_build.py`**

`_parse_args` currently takes only `--watch`. Add `--check`: rebuild, then run
`git diff --exit-code -- static/css/tailwind.css` and return 1 if the
committed output is dirty.

Keep the pathspec. It scopes the check to the generated file, so unrelated
dirty files -- or rewrites left by earlier hooks in the same run -- cannot
produce a false drift failure.

**Step 3: Write the tests**

Add to `tests/scripts/dev/test_tailwind_build_cli.py`:

- `--check` rebuilds and returns 0 when the committed file matches.
- `--check` returns 1 when `git diff` reports the file dirty.
- `--check` and `--watch` together is rejected.

**Step 4: Prove the hook can fail**

Edit one byte of `static/css/tailwind.css` by hand, run the hook, confirm it
fails. Then `git checkout -- static/css/tailwind.css`.

A hook that cannot fail is not a gate.

---

## Task 6: The frontend gate runtime

**Files:**
- Create: `scripts/dev/frontend_gate.py`
- Create: `tests/scripts/dev/test_frontend_gate.py`
- Modify: `requirements-dev.txt`

**Step 1: Pin Playwright**

Add `playwright==1.62.0` to `requirements-dev.txt`. No `package.json`, no Node
project, no pytest plugin, no MCP dependency. The pin selects its matching
browser build.

**Step 2: Write the failing tests**

Three behaviours, all unit-level with no browser:

- A missing `playwright` package fails immediately and prints the exact setup
  command, `python -m playwright install chromium`. It never downloads
  tooling implicitly.
- A missing browser binary does the same.
- The server shuts down in a `finally` block even when a check raises.

**Step 3: Build the runtime**

Start the Flask app on an ephemeral loopback port with
`werkzeug.serving.make_server(host="127.0.0.1", port=0, app=create_app())` in
a thread. Read the real port back from `server.server_port`. Own the
lifecycle, and call `server.shutdown()` in a `finally` block, so the gate
needs neither a separately running app nor an external MCP service.

Give `main` an injectable `argv`, matching `tailwind_build.main` rather than
`docsync.cli.main`. That is what makes the CLI testable the way
`test_tailwind_build_cli.py` already tests one.

**Step 4: Run the tests**

Expected: PASS.

---

## Task 7: The four frontend-gate checks

Checks 5 and 6 belong to WP-5 and WP-6. Do not write them here.

**Files:**
- Modify: `scripts/dev/frontend_gate.py`

**Check 1 -- stylesheet isolation.** Each page loads exactly one framework
stylesheet. Read every `link[rel=stylesheet]` href and assert a page never
carries both a Bootstrap URL and `tailwind.css`.

**Check 2 -- theme tokens.** `--bars-color` equals the theme primary in both
themes, and no cool-grey surface (`#f8f9fa`, `#121212`) is computed anywhere.

**Read this before writing the check.** `getPropertyValue('--bars-color')`
can return the unresolved `var(--color-primary)` text rather than a colour.
Resolve both through a probe element and compare the computed `rgb()` strings:

```js
const probe = document.createElement('div');
document.body.appendChild(probe);
probe.style.backgroundColor = 'var(--bars-color)';
const bars = getComputedStyle(probe).backgroundColor;
probe.style.backgroundColor = 'var(--color-primary)';
const primary = getComputedStyle(probe).backgroundColor;
probe.remove();
```

**Check 3 -- theme persistence.** Toggle the theme, reload, assert it
survived. This is what `F-B21-2` breaks today.

**Check 4 -- fonts.** All five kit families resolve. Await
`document.fonts.ready`, then read the loaded families:

```js
[...document.fonts].filter(f => f.status === 'loaded').map(f => f.family)
```

Assert all five of `akzidenz-grotesk-next-pro`, `instrument-serif`, `gotham`,
`input-mono` and `input-mono-narrow` are present. **Asserting the stylesheet
was requested is not enough** -- a domain-locked kit returns a stylesheet that
loads no faces, and the page falls back silently with no error.

**Step: Prove the gate can fail.** Break one assertion on purpose, run it,
confirm it reports. Then restore. The definition is explicit that it must be
able to fail.

---

## Task 8: Wire the gate into CI

**Files:**
- Modify: `.github/workflows/test.yml` -- the `quality-gate` job

**Step 1: Add two steps after `Install dependencies`**

```yaml
      - name: Install Playwright browser
        run: python -m playwright install --with-deps chromium

      - name: Run frontend gate
        run: python scripts/dev/frontend_gate.py
```

**Step 2: Note the ordering**

Put them after `Verify committed Tailwind CSS`, so a drift failure reports
before the slower browser step runs.

**Step 3: Commit tasks 5 through 8**

```bash
git add .pre-commit-config.yaml scripts/dev/tailwind_build.py scripts/dev/frontend_gate.py tests/scripts/dev/test_tailwind_build_cli.py tests/scripts/dev/test_frontend_gate.py requirements-dev.txt .github/workflows/test.yml
git commit -m "ci(frontend): add the tailwind drift hook and frontend gate"
```

---

## Task 9: `shell.css` and the base shell

**Files:**
- Create: `static/css/shell.css`
- Modify: `templates/base.html`

**Step 1: Write `shell.css`**

Framework-neutral, loaded on every page, so the shared header renders
identically during coexistence. It styles the standing header bar and footer,
and it takes over the wordmark recolor that `global.css` did.

The spec sets the bar at **68px desktop and 60px mobile, fixed**, so the
wordmark sits at the same vertical position on every screen. Single breakpoint
at 860px. **Touch targets never below 44px** -- that closes `F-AUDIT-1`.

WP-8 absorbs this file into `tailwind.src.css`.

**Step 2: Rework `base.html`**

- Add the Typekit link to `head`:
  `<link rel="stylesheet" href="https://use.typekit.net/rwy8ghw.css">`
- Set `<html lang="en" data-theme="light">`.
- Add a small inline script in `head` that reads `localStorage.darkMode` and
  sets `data-theme` **before first paint**. There is no FOUC guard today.
- **Move the Bootstrap link and `global.css` into a new per-page legacy
  block.** Both currently load globally. `global.css` carries
  Bootstrap-coupled `.card` and `.modal-*` rules that would restyle daisyUI
  components on a migrated page.
- Load `shell.css` on every page.
- Add the standing header bar: wordmark left, theme toggle top-right.
- **Delete the `.page-footer-bar` block** and the footer toggle with it. Keep
  `{% block page_footer_extra %}` -- `results.html` injects back-to-top there.

---

## Task 10: `theme.js` dual-writes

**Files:**
- Modify: `static/js/theme.js`

Set `data-theme` on `<html>` **and** `.dark-mode` on `<body>`. daisyUI keys on
`data-theme`; the seven legacy stylesheets still key on `.dark-mode`. WP-8
retires the second write.

Keep the `#back-to-top` binding this file also owns. The toggle moves from the
footer to the header, so update the element lookup.

**This is what closes `F-B21-2`.** Setting `data-theme` also settles the
`prefersdark: true` seam: the compiled `:root:not([data-theme])` rule stops
matching once the attribute is always present.

---

## Task 11: Keep the four unmigrated pages working

**Files:**
- Modify: `templates/index.html`, `templates/loading.html`,
  `templates/results.html`, `templates/unmatched.html`

Each must fill the new legacy block with the Bootstrap CSS link and
`global.css`. **If this is missed, the page loses its theme entirely** --
`global.css` owns every `--bars-color`, `--text-color` and `--bg-color` token
those pages read.

Verify each page renders before moving on. This is the highest-risk task in
the work package and nothing in `pytest` will catch a mistake.

---

## Task 12: The `error.html` pilot

**Files:**
- Modify: `templates/error.html`
- Modify: `static/css/error.css`
- Delete: `static/js/error.js`

**Step 1: Migrate the markup**

46 lines, the smallest page. Replace every Bootstrap class -- `container`,
`col-md-9`, `card`, `btn btn-primary`, `btn btn-outline-secondary`, `lead`,
`text-center`, `mx-auto`, `mb-3`, `mb-4` -- with Tailwind utilities and
daisyUI components.

It loads `tailwind.css` and `shell.css`, and **no Bootstrap**. It must not
fill the legacy block.

**Step 2: Keep the one icon**

The spec says the UI is text-first and there is no icon system: "do not invent
one." That exclamation-circle SVG is the only icon in the whole system. Keep
it.

**Step 3: Delete `error.js`**

It is a two-line comment-only file. Remove it and its `<script>` tag.

**Step 4: Do not touch `routes.py` or `app.py`**

The batch contract reserves them for WP-7. See the finding in Task 13.

**Step 5: Rebuild the stylesheet**

```
python scripts/dev/tailwind_build.py
```

The new utilities in `error.html` change the compiled output. Any WP that
changes templates must rebuild and commit `tailwind.css` in the same commit --
production serves the committed file with no runtime build.

**Step 6: Run the frontend gate**

```
python scripts/dev/frontend_gate.py
```

This is the first real run against a migrated page.

---

## Task 13: Findings and records

**Step 1: File `F-B21-10`**

`error.html` defaults `status_code` to `'400'`, and none of the seven
`render_template("error.html", ...)` call sites pass it. **A 404 therefore
renders the literal text "400".** The two `app_errorhandler` registrations
that would fix it live in `routes.py`, which the batch contract reserves for
WP-7. File it; do not fix it here.

Mirror it to a GitHub issue. The mirror is manual -- `F-B21-9` records that.

**Step 2: Close `F-B21-2`**

All three seams are met: `data-theme` is set, the `prefersdark` rule stops
matching, and Bootstrap no longer collides because each page loads exactly one
framework stylesheet.

**Step 3: Update `F-B21-7`**

Both halves are fixed in Task 3 and Task 4.

**Step 4: Write the PLAYBOOK Section 4 entry**

Scope, plan versus implementation, deviations, validation results, forward
guidance. **Carry the re-derived test count, never a quoted one.**

**Step 5: Update `.claude/SESSION_CONTEXT.md` Section 1**

Hand-maintained and ungated -- no gate reads it. Update the batch status row
**in the same commit** as the PLAYBOOK entry, never afterwards. It is the
first thing a bootstrapping agent reads for state.

**Step 6: Regenerate the STATUS block**

```
python scripts/doc_state_sync.py --fix
```

Then check which entry it rotated:

```bash
git diff docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md
```

`--fix` moves the oldest entry out of Section 4 when the non-current window
exceeds four. That is designed behaviour, not a loss.

**Step 7: Commit tasks 9 through 13**

```bash
git add templates/base.html templates/error.html templates/index.html templates/loading.html templates/results.html templates/unmatched.html static/css/shell.css static/css/error.css static/css/tailwind.css static/js/theme.js FINDINGS.md PLAYBOOK.md .claude/SESSION_CONTEXT.md docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md
git rm static/js/error.js
git commit -m "feat(ui): tailwind base shell, header bar, error page pilot"
```

---

## Final verification

1. `python scripts/dev/check_worktree_alignment.py` -- exit 0.
2. `.venv\Scripts\pytest.exe -q` -- **re-derive the count.** The 633 baseline
   moves; this WP adds frontend-gate and drift tests.
3. `git write-tree` before and after
   `.venv\Scripts\pre-commit.exe run --all-files`, then compare.
4. `python scripts/doc_state_sync.py --check` -- exit 0, with only the known
   active-batch root-definition warning.
5. `python scripts/dev/frontend_gate.py` -- passes, and proven able to fail.
6. **Rebuild, then diff.** `python scripts/dev/tailwind_build.py`, then
   `git diff --exit-code -- static/css/tailwind.css`.
7. Owner visual review of the error page in both themes before WP-3.

## Known risks

- **Task 11 is the one that breaks production silently.** A missed legacy
  block strips a page's theme and no test will say so.
- **The Typekit kit is a third-party runtime dependency now.** The owner
  confirmed the domain allow-list is covered. If check 4 fails everywhere, the
  kit settings are the first place to look, not the code.
- **`doc-state-sync-check` runs on every commit.** DOC001 reads git's index,
  not the filesystem, so stage new files before committing a document that
  links to them.
