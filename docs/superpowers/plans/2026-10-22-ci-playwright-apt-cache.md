# CI Playwright Package Cache Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stop a slow Ubuntu mirror from stalling the Quality Gate: keep the Ubuntu packages that `playwright install --with-deps` downloads in the Actions cache, so a run downloads only a package newer than the cached one.

**Architecture:** One side-task branch, `ci/playwright-apt-cache`, cut from `main` once PR #266 (the last of the side-task train) has merged. Two commits: the plan, then the workflow change with its structural test and finding. The real proof is two CI runs: the first fills the cache, a re-run reads it.

**Tech Stack:** GitHub Actions (`actions/cache@v6` and its `restore` and `save` sub-actions, ubuntu-latest runner, apt), pytest.

**Evidence (2026-10-22, PR #265's CI run 39847888664, step "Install Playwright browser"):** `apt-get update` fetched 12.5 MB in 16 s; "Need to get 53.7 MB of archives" (8 upgraded, 40 newly installed) then "Fetched 53.7 MB in 20min 32s (43.5 kB/s)" from `azure.archive.ubuntu.com`; the four browser downloads from `cdn.playwright.dev` took 14 s together. So the package download is the whole stall, and the browsers are not worth a cache (several hundred MB to save 14 s). PR #266's first CI attempt stalled in the same step and was cancelled and re-run. PR #266's re-run at 20:57 took 22 s in the same step, so the mirror recovers, but nothing stops the next slow day.

**Owner rulings:** 2026-10-22, on the lasting fix (cache the packages, or give apt short timeouts): "Yes, on the lasting fix. Worth doing". Standing: tests assert intended behaviour, not the code as written.

## Global Constraints

- Worktree `C:/ssw/ci`, branch `ci/playwright-apt-cache`. Tools from the primary checkout: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe"` (`PY`), and its `pre-commit.exe`.
- Side-task logging and commit procedure exactly as `docs/superpowers/plans/2026-10-22-pre-batch23-side-tasks.md` Global Constraints state them (untagged Section 4 entry after the end marker; `pytest -q` -> `--fix --test-count N` -> stage by name, including whatever `--fix` rewrote or rotated -> `pre-commit run --all-files` -> `--check` -> commit). Workspace `constraints.md` R1-R13 bind every task.
- No new action repository: `actions/cache/restore` and `actions/cache/save` are sub-actions of the `actions/cache@v6` already pinned here (controller ruling 2026-10-22), and no new dependency. Keep the step name "Install Playwright browser" (the controller's CI watcher refers to it).
- The workflow keeps least privilege: no `permissions:` change, no secret, no `${{ }}` expression inside a `run:` script (zizmor template-injection).
- Commit messages: Conventional Commits, subject <= 72 characters measured before committing, no attribution line. Never `--no-verify`, `--amend`, rebase, reset or `sed -i`.
- Finding ids: F-B23-57 (next free after PR #266's F-B23-51..56, which are on `main` when this branch is cut).

---

### Task 0: Commit this plan

**Files:** Create `docs/superpowers/plans/2026-10-22-ci-playwright-apt-cache.md`; modify `docs/agents/PLAYBOOK.md` (Section 3, Section 4).

- [ ] **Step 1:** Copy the plan into place with any review fixes the dispatch names; `git add` it before `--fix` (DOC001 resolves Section 3's backticked paths through the index).
- [ ] **Step 2:** PLAYBOOK Section 3, "Before WP-1" bullet: insert before "the documentation refresh merges last" the clause "a CI change keeps Playwright's Ubuntu packages in the Actions cache so a slow mirror cannot stall the gate (branch `ci/playwright-apt-cache`, plan `docs/superpowers/plans/2026-10-22-ci-playwright-apt-cache.md`);", so the list reads "...runs next (...); a CI change ...; the documentation refresh merges last."
- [ ] **Step 3:** Section 4 entry `### <commit date, date +%F> - Plan the CI package cache`; commit procedure; message `docs(plan): Plan the CI cache for Playwright's Ubuntu packages`.

---

### Task 1: Keep Playwright's Ubuntu packages in the Actions cache (F-B23-57)

**Files:**
- Modify: `.github/workflows/test.yml` (the steps before and at "Install Playwright browser")
- Modify: `tests/test_ci_workflows.py`
- Modify: `docs/agents/FINDINGS.md` (file F-B23-57 as resolved), `docs/agents/PLAYBOOK.md` (Section 4), (no other live doc: Step 7).

- [ ] **Step 1: Write the failing test** at the end of `tests/test_ci_workflows.py`:

```python
IMAGE_STEP = "Read the runner image version"
RESTORE_STEP = "Restore Playwright system packages"
INSTALL_STEP = "Install Playwright browser"
SAVE_STEP = "Save Playwright system packages"
APT_ARCHIVES = "/var/cache/apt/archives"


def _steps(workflow_text: str) -> dict[str, list[str]]:
    """Return each step's lines, keyed by its name, in file order."""
    steps: dict[str, list[str]] = {}
    current = None
    for line in _lines(workflow_text):
        stripped = line.strip()
        if line.startswith("      - name: "):
            current = stripped.removeprefix("- name: ")
            steps[current] = []
        elif current is not None and (not line.strip() or _indent(line) > 6):
            steps[current].append(line)
        elif current is not None:
            current = None
    return steps


def _code(step: list[str]) -> list[str]:
    """Return a step's stripped, non-blank, non-comment lines."""
    stripped = (line.strip() for line in step)
    return [line for line in stripped if line and not line.startswith("#")]


def _value(step: list[str], key: str) -> str | None:
    """Return the value of the step's first ``key: value`` line, if any."""
    prefix = f"{key}: "
    for line in _code(step):
        if line.startswith(prefix):
            return line.removeprefix(prefix)
    return None


def _first_restore_key(step: list[str]) -> str | None:
    """Return the first line under the step's ``restore-keys: |`` block."""
    code = _code(step)
    for i, line in enumerate(code):
        if line.startswith("restore-keys:"):
            return code[i + 1] if i + 1 < len(code) else None
    return None


def _copies(line: str, source: str, target: str) -> bool:
    """True if the ``cp`` line names ``source`` before ``target``."""
    start = line.find(source)
    return (
        "cp" in line.split()
        and start != -1
        and line.find(target, start + len(source)) != -1
    )


def test_playwright_packages_are_restored_seeded_and_saved_around_the_install():
    """The packages are restored before the install, copied into apt's cache
    directory before it, copied back after it and saved even when a later
    step fails, so a slow mirror is paid for at most once (F-B23-57)."""
    steps = _steps(WORKFLOW.read_text(encoding="utf-8"))
    names = list(steps)
    for name in (IMAGE_STEP, RESTORE_STEP, INSTALL_STEP, SAVE_STEP):
        assert name in names, f"step {name!r} is missing from {names}"
    order = [
        names.index(n) for n in (IMAGE_STEP, RESTORE_STEP, INSTALL_STEP, SAVE_STEP)
    ]
    assert order == sorted(order), f"steps are out of order: {names}"

    restore, install, save = steps[RESTORE_STEP], steps[INSTALL_STEP], steps[SAVE_STEP]
    restore_id = _value(restore, "id")
    image_id = _value(steps[IMAGE_STEP], "id")
    assert restore_id, "the restore step needs an id for the save step to read"
    assert image_id, "the runner-image step needs an id for the key to read"
    assert str(_value(restore, "uses")).startswith("actions/cache/restore@")
    assert str(_value(save, "uses")).startswith("actions/cache/save@")

    path = _value(restore, "path")
    assert path, "the restore step has no path"
    assert _value(save, "path") == path, "restore and save use different paths"
    assert _value(save, "key") == (
        "${{ steps." + restore_id + ".outputs.cache-primary-key }}"
    ), "the save step must store under the restore step's primary key"
    assert _value(save, "if") == (
        "steps." + restore_id + ".outputs.cache-hit != 'true'"
    ), "the save step must run only when the exact key was not found"

    key = _value(restore, "key") or ""
    assert f"steps.{image_id}.outputs." in key, "the key omits the runner image"
    prefix = _first_restore_key(restore)
    assert prefix and key.startswith(prefix), "restore-keys is not a key prefix"

    code = _code(install)
    runs = [
        i for i, line in enumerate(code) if "playwright install --with-deps" in line
    ]
    assert len(runs) == 1, f"expected one browser install line, found {runs}"
    seeds = [line for line in code[: runs[0]] if _copies(line, path, APT_ARCHIVES)]
    saves = [line for line in code[runs[0] + 1 :] if _copies(line, APT_ARCHIVES, path)]
    assert seeds, "no line before the install copies the cache into apt's archives"
    assert saves, "no line after the install copies apt's archives back to the cache"
```

- [ ] **Step 2: Run to verify it fails.** `PY -m pytest tests/test_ci_workflows.py -q`. Expected: the new test fails on `step 'Read the runner image version' is missing` (no such step yet); the existing tests pass.
- [ ] **Step 3: Implement.** In `.github/workflows/test.yml`, replace the existing step

```yaml
      # Last on purpose. Starting a browser costs far more than a lint, a
      # rebuild or the suite, so every cheaper gate reports first.
      - name: Install Playwright browser
        run: |
          python -m playwright install --with-deps chromium firefox
```

with

```yaml
      - name: Read the runner image version
        id: runner-image
        run: echo "version=${ImageOS:-unknown}-${ImageVersion:-unknown}" >> "$GITHUB_OUTPUT"

      # --with-deps installs about 50 MB of Ubuntu packages (48 of them on
      # 2026-10-22) from the runner's Azure mirror on every run. That day the
      # mirror served them at 43.5 kB/s and the step took 21 minutes instead
      # of about one (F-B23-57). The packages are kept between runs here, so
      # apt downloads only a package newer than the cached one; its index
      # still comes from the mirror (12.5 MB in 16 s that day). The runner
      # image version is in the key, so the cache refreshes with the image,
      # and the restore key reuses the previous image's packages meanwhile.
      - name: Restore Playwright system packages
        id: playwright-apt
        uses: actions/cache/restore@v6
        with:
          path: ~/.cache/playwright-apt
          key: playwright-apt-${{ runner.os }}-${{ runner.arch }}-${{ steps.runner-image.outputs.version }}-${{ hashFiles('requirements-dev.txt') }}
          restore-keys: |
            playwright-apt-${{ runner.os }}-${{ runner.arch }}-

      # Last on purpose. Starting a browser costs far more than a lint, a
      # rebuild or the suite, so every cheaper gate reports first.
      - name: Install Playwright browser
        run: |
          # apt reads packages from a root-owned directory the cache action
          # cannot write, so the cached ones are copied in first and the
          # current set copied back after; autoclean drops versions the
          # mirror no longer serves, so the cache does not grow without end.
          mkdir -p ~/.cache/playwright-apt
          find ~/.cache/playwright-apt -name '*.deb' -exec sudo cp -t /var/cache/apt/archives/ {} +
          python -m playwright install --with-deps chromium firefox
          sudo apt-get autoclean -q
          rm -f ~/.cache/playwright-apt/*.deb
          find /var/cache/apt/archives -maxdepth 1 -name '*.deb' -exec cp -t ~/.cache/playwright-apt/ {} +
          echo "cached packages: $(find ~/.cache/playwright-apt -name '*.deb' | wc -l)"
          du -sh ~/.cache/playwright-apt

      # Saved here, not by the cache action's own post-job step: that one
      # saves only when the whole job succeeds, so a failed frontend gate or
      # a stalled run the owner cancels would never fill the cache, and the
      # slow-mirror days are exactly the runs that get cancelled. A hit on
      # the exact key means the cache is already stored under it.
      - name: Save Playwright system packages
        if: steps.playwright-apt.outputs.cache-hit != 'true'
        uses: actions/cache/save@v6
        with:
          path: ~/.cache/playwright-apt
          key: ${{ steps.playwright-apt.outputs.cache-primary-key }}
```

- [ ] **Step 4: Run to verify it passes.** `PY -m pytest tests/test_ci_workflows.py -q`: all pass. Validate the YAML parses: `PY -c "import yaml,sys; yaml.safe_load(open('.github/workflows/test.yml', encoding='utf-8'))"` (PyYAML is a pre-commit dependency; if it is not importable, `pre-commit run check-yaml --all-files` instead).
- [ ] **Step 5: Planted defects** (copy the workflow aside first and copy it back after each; never `git checkout` it). Run `PY -m pytest tests/test_ci_workflows.py -q` for each; every one must FAIL, and the restored file must PASS. (a) Change the restore step's `path:` to `~/.cache/apt-other`. (b) Move the whole restore step to after the install step. (c) Delete the copy-back `find /var/cache/apt/archives ... -exec cp -t ~/.cache/playwright-apt/` line. (d) Delete the seed `find ~/.cache/playwright-apt ... sudo cp -t /var/cache/apt/archives/` line. (e) Point the copy-back at `~/.cache/other/` instead of `~/.cache/playwright-apt/`. (f) Move the whole save step to before the install step. (g) Change the save step's `key:` to `playwright-apt-${{ runner.os }}`. Also worth one run each: (h) delete the save step's `if:` line; (i) rename the `runner-image` step id so the key still names the old one. Record each FAIL line and the final PASS.
- [ ] **Step 6:** File F-B23-57 in FINDINGS as resolved, under `## Resolved this batch`, heading `### F-B23-57: CI downloads Playwright's Ubuntu packages from a slow mirror on every run`; body: the evidence above (PR #265's run: 53.7 MB at 43.5 kB/s, 20 min 32 s; index and browsers fast; PR #266's first attempt stalled in the same step and was cancelled), the fix (packages in the Actions cache keyed by runner image and `requirements-dev.txt`, saved by a step right after the install so a failed or cancelled later step cannot prevent it; apt index and browser downloads unchanged; `autoclean` bounds the cache), and what is NOT covered (a cache miss on a slow mirror still waits, once per runner image or dependency change; on an exact key hit nothing is re-saved, so a package newer than the cached copy downloads on every run until the runner image or `requirements-dev.txt` changes the key); `- [x] **Status:** resolved`, `**Completed:** 2026-10-22`, `Source: PR #265 and #266 CI runs and controller log analysis, 2026-10-22.`
- [ ] **Step 7:** No other live doc describes this CI step (sweep at d26db01: the only live hits are `.github/workflows/test.yml` itself, `DEVELOPMENT.md`'s local `python -m playwright install chromium firefox` and `scripts/dev/_frontend_gate_runtime.py`'s `SETUP_COMMAND`, both local setup without `--with-deps` and unaffected). Change none of them; if the grep `git grep -n "with-deps\|Install Playwright browser"` at your HEAD shows a new live hit, report it.
- [ ] **Step 8:** Section 4 entry `### <commit date, date +%F> - CI keeps Playwright's Ubuntu packages between runs`; commit procedure (N rises by 1; the test module is not new, so the module count is unchanged); message `ci(workflow): Cache Playwright's Ubuntu packages between runs`.

---

## Verification on CI (controller)

1. Push; the first run misses the cache (or restores nothing), installs as before, and the "Save Playwright system packages" step saves `~/.cache/playwright-apt` right after the install (the log's "Cache saved" line and size), whether or not the frontend gate later passes.
2. Re-run the job: the restore step logs a hit, the save step is skipped, and the install step's apt line reads "Need to get 0 B/53.7 MB of archives" (or a small figure for a few newer packages); the step finishes in about a minute even if the mirror is still slow. The step's own log shows `cached packages: N` and the cache directory size.
3. Record both runs' step durations and the "Need to get" lines in the PR body. If the re-run still downloads the whole set, return to Task 1 (systematic-debugging): the likely causes are apt deleting archives after install (the `cached packages: N` line of the first run shows it: N would be 0; check for a `docker-clean`-style apt config on the runner) or a key that changes every run (check that `ImageOS` and `ImageVersion` are not both `unknown` in the key).

## Self-review

- Coverage: the owner's "lasting fix" -- the measured bottleneck (package download) is cached; the apt index and browser downloads, measured fast, are left alone.
- Names: `_lines`, `_indent`, `WORKFLOW` exist in `tests/test_ci_workflows.py` at d26db01; `actions/cache@v6` is the pin the Tailwind step uses, and `actions/cache/restore@v6` and `actions/cache/save@v6` are its sub-actions.
