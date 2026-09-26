# Batch 23 WP-0 control-plane plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Clear the control-plane cluster of `BATCH23_DEFINITION.md` WP-0 Part C --
F-DOCSYNC-11, -12, -13, -22, -7, -6, -15, F-MAS-3, F-WORKTREE-3, F-B21-20 and F-B21-25
items 1-2 -- so the Spotify export batch starts with no open control-plane defect and no
green gate hiding a red one. This is item 1 of "After this plan" in
`docs/superpowers/plans/2026-09-23-batch23-wp0-reconcile-and-clear.md`.

**Architecture:** Seven tasks, strictly ordered by what each one touches:

1. **The test-count mechanism** (F-DOCSYNC-11, -12, -13, -22) changes
   `latest_test_count_authority` and the functions around it. It lands first because
   nothing else in this plan may touch that function until its new shape exists.
2. **Repoint and split** (F-DOCSYNC-7, F-MAS-3) moves the tests Task 1 just touched into
   their permanent homes. It lands second so Task 1's own edits do not collide with files
   Task 2 is about to rename.
3. **Work-package completion** (F-DOCSYNC-15, Q4) changes `_collect_wp_numbers` and
   `_next_wp_number`, a different seam of the same package (`scripts/docsync/parser.py` and
   `scripts/docsync/renderer.py`). It waits until Tasks 1-2 have settled the file layout
   those two modules' tests now live in.
4. **Case-consistent batch discovery** (F-DOCSYNC-6) touches `scripts/docsync/cli.py`
   only. Independent of Tasks 1-3; ordered after them because it is lower-risk and
   easier to review once the count-mechanism churn has landed.
5. **Two worktree-guard bugs** (F-WORKTREE-3) touch `scripts/dev/_worktree_guard_*.py`,
   a different package entirely (not gated by the docsync preflight). Independent of
   Tasks 1-4; placed here because it is the next item in the reconcile plan's "After this
   plan" list.
6. **The commit-procedure reorder** (F-B21-20, Q5) is a prose edit to `AGENTS.md` plus a
   live probe against the real `tailwind-css-drift` hook. Independent of every other task.
7. **Bootstrap fast-path and the untracked-essentials manifest** (F-B21-25 items 1-2,
   Q15) is a second, independent `AGENTS.md` prose edit plus one new small module and one
   new declared table. It lands last because it is the newest-designed mechanism (a new
   WT code) and benefits from the worktree-guard familiarity Task 5 just built.

Tasks 1-4 stage files under `scripts/docsync/` and are refused by the commit preflight
(rule R7 below); Tasks 5-7 do not.

**Tech Stack:** Python 3.13 stdlib, pytest, `unittest.mock`. No new dependency.

**Owner rulings, 2026-09-25.** Given after two plan reviews, and final:

- **Q-PIN.** An explicit `--fix --test-count N` persists N in `config/docsync.toml`, as
  a `[test_count]` table (`pinned = N`). The SESSION_CONTEXT STATUS block is rendered
  output and is never read back as an input (`docs/agents/global-rules.md` Rule 7). The
  config file changes on every commit that changes the count; that cost is accepted.
- **Q1.** A new warning, DOC025, fires only when exactly one log entry carries the
  newest date and its count disagrees with the pin. A same-date tie, the F-DOCSYNC-22
  case, stays silent. The warning never changes the exit code.
- **Q2.** A dirty tree adds WT010 only on the local detached branch (WT012), not on a
  recognized-CI checkout (WT011).
- **2026-09-26.** Q-PIN's cost was underestimated: `config/docsync.toml` is also listed in
  `CONTROL_PLANE_FILES`, so every ordinary commit that adds a test (and therefore pins a
  new count) refused itself at the preflight. The pin stays in `config/docsync.toml`
  `[test_count]`; the preflight is changed instead so a staged `config/docsync.toml` counts
  as control-plane only when something outside `[test_count]` changed (Task 8).

## Global Constraints

Every task's requirements include this section.

- **Qualified interpreter only.** This is a linked worktree; the venv lives in the primary
  checkout. Use `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe"`
  and its sibling `pytest.exe` / `pre-commit.exe` in the same `Scripts/` directory. Never
  bare `pip`, never a second venv. Quote every path: it contains a space.
- **No new dependency, no version change** without the owner's approval (`AGENTS.md`
  "Environment Setup").
- **R7 -- docsync control plane** (copied verbatim from
  `docs/superpowers/plans/2026-09-24-batch23-wp0-root-cleanup.md` Global Constraints,
  "A commit that changes the docsync control plane is refused by design"): Any task
  touching `scripts/docsync/`, `scripts/doc_state_sync.py`, `scripts/dev/docsync_preflight.py`,
  or the declarations file (`config/docsync.toml`) exits 3 at the preflight -- except a
  `config/docsync.toml` change confined to the `[test_count]` pin, which is not
  control-plane (owner ruling 2026-09-26; Task 8). Run `doc_state_sync.py --check`
  directly at exit 0 first, then commit with `SKIP=doc-state-sync-check git commit ...`.
  Never `--no-verify`.
- **Logging (owner ruling, 2026-09-23, WP-0).** Every commit logs an **untagged**
  `docs/agents/PLAYBOOK.md` Section 4 entry, placed directly after the
  `<!-- DOCSYNC:CURRENT-BATCH-END -->` marker (top of the non-current list). The heading
  carries no `WP-<digit>` token. Body opens with "Side task, no batch tag: ... part of
  Batch 23 WP-0 Part C." Never move entries across the markers by hand.
- **Section 3 stays true.** Keep `**Next action:** WP-0 is next.` exactly (DOC007 reads
  it). Update only the progress sentence under "the control-plane plan" in Section 3's
  order list.
- **Part C may change behaviour and may edit an existing test, but only where the finding
  being fixed requires it.** The commit body names every changed assertion by test id. A
  commit never mixes this plan's work with any other plan's.
- **Every change to a check is accepted only on a live probe.** Red on the planted
  defect, green on its near miss, run in a scratch copy made with `git archive` outside
  the repository (verification standard below). A task's own unit tests are written
  first as the regression guard; the probe is the proof, not a substitute.
- **Commit procedure, in this order** (`AGENTS.md` "Commit Rules"; corrected by Task 1,
  R3 of the workspace's `constraints.md`, which overrides the order below -- the count
  must be measured before `--fix` can pin it):
  1. write the Section 4 entry (its Validation line quotes the count measured in step 2;
     leave a placeholder and fill it after);
  2. the full suite, to read N;
  3. before Task 1 lands: hand-update the count sites and run `doc_state_sync.py --fix`.
     From Task 1 onward, including Task 1's own commit: `doc_state_sync.py --fix
     --test-count N`, and hand-edit no count site;
  4. stage the changed paths by name;
  5. `pre-commit run --all-files`;
  6. `frontend_gate.py`, only if a task touches `static/`, `templates/` or
     `scripts/dev/_frontend_gate_*` (no task in this plan does);
  7. `doc_state_sync.py --check`, which must exit 0; the only acceptable warning is the
     root `BATCH23_DEFINITION.md` one.
- **Measure the count.** Run the suite as:

  ```
  "C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe" -q --ignore=tests/scripts/dev/test_mutation_test.py -p no:cacheprovider
  ```

  Quote it exactly as `` Validation: `pytest -q` -- **N passed**; the untracked
  mutation-runner tests were excluded. `` A task that adds tests also updates the count
  sites: `.claude/SESSION_CONTEXT.md` Section 1 `Tests` row, its `## 6. Test structure
  (N tests)` heading, and the `FINDINGS.md` header count. From Task 1 onward, do this by
  running `doc_state_sync.py --fix --test-count N` (all four sites, one command) rather
  than hand-editing any of them.
- **Resolving a finding.** Replace its `Status:` line with the canonical record from
  `docs/agents/issue-tracker.md`:
  ```
  - [x] **Status:** resolved
  **Completed:** <YYYY-MM-DD, the commit's date>
  <What fixed it, naming the function.>
  ```
  `--fix` rotates the checked record into `docs/history/findings/FINDINGS_ARCHIVE.md`; stage
  both files. Never write "resolved" about a finding in prose unless its own record is
  checked (DOC023): say "archived" or "settled" instead. A finding that is only partly
  addressed by this plan keeps its existing `Status:` line and gains a dated note instead
  (Tasks 4, 5 and 7 each do this once).
- **Commit discipline.** Conventional Commits, imperative mood, no trailing period,
  subject 72 characters or fewer. Stage paths by name; `git add -A` and `git add .` are
  forbidden. Never `--no-verify`. No `Co-authored-by` trailer and no other attribution
  line (agent-authored commits in this repository carry none).
- **Untracked files belong to other agents.** Never stage, edit or delete them: the
  mutation runner, its scope file and tests, `progress_copy.md`, the review HTML files,
  `plan.md`, the audit documents, and anything under `.superpowers/`.
- **ASCII only** in every file: `--`, not an em dash.
- **The pre-commit `worktree-alignment` hook prints `ERROR WT005 ... origin/main` and
  still passes.** It is advisory; the branch is cut from `test`. Do not act on it.

## The verification standard for control-plane tasks

Every task that changes a check, a path resolver or a diagnostic (Tasks 1, 3, 4, 5, 7) is
accepted only on a live probe:

1. Build a throwaway corpus from the committed tree, at a short path:
   ```bash
   mkdir -p /c/ssprobe && cd /c/ssprobe && rm -rf corpus && mkdir corpus
   git -C "C:/Users/peter/.config/superpowers/worktrees/ScrobbleScope/batch-21/impeccable-init" archive HEAD | tar -x -C corpus
   cd corpus && git init -q && git config core.longpaths true && git add -A
   git -c user.email=p@l -c user.name=p commit -qm base && git tag base
   ```
2. Confirm the copy is faithful: `--check` there prints the same summary as in the
   worktree.
3. **Red:** plant the defect the task targets and run the real CLI. The expected code
   must print and the exit must be nonzero (or zero for a warning-severity code, with the
   warning printed).
4. **Near-miss green:** plant the closest *valid* variant and confirm silence (or the
   expected unchanged behaviour).
5. Reset with `git reset -q --hard base && git clean -qfd` between probes.
6. Paste the probe table (probe, expected, exit, codes) into the task report and the
   Section 4 entry. Delete `/c/ssprobe` afterwards.

## Gates

The exact commands every task's "gates and live probe" step runs, named once here so each
task can reference this block rather than repeat it (a gate-runner agent reads this
section verbatim):

```
suite:      "C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe" -q --ignore=tests/scripts/dev/test_mutation_test.py -p no:cacheprovider
docsync:    "C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe" scripts/doc_state_sync.py --check
precommit:  "C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pre-commit.exe" run --all-files
```

`frontend_gate.py` is not run by any task in this plan: none touches `static/`,
`templates/` or `scripts/dev/_frontend_gate_*`.

---

### Task 1: An explicit `--fix --test-count N` pins the count in `config/docsync.toml` (F-DOCSYNC-11, -12, -13, -22)

**Files:**
- Modify: `scripts/docsync/models.py` (no change -- `TestCountAuthority` is reused as-is)
- Modify: `scripts/docsync/declarations.py` (a new `TestCountConfig`, `_validate_test_count`,
  `_test_count_config`, `load_test_count_config`, mirroring `ArchiveConfig` /
  `_validate_archives` / `_archive_config` / `load_archive_config`)
- Modify: `scripts/docsync/logic.py` (`_sync`, a new `resolved_test_count_authority`, a new
  private helper for the DOC025 newest-entry lookup -- name it in the commit body)
- Modify: `scripts/docsync/renderer.py` (a new `rewrite_recorded_counts`)
- Modify: `scripts/docsync/integrity.py` (the DOC005/006/008 block inside
  `collect_integrity_issues`, importing `resolved_test_count_authority` and
  `load_test_count_config`; a new DOC025 warning)
- Modify: `scripts/docsync/cli.py` (`_build_parser`, `main`, `_drift_updates`,
  `_sync_corpus`, a new `_rewrite_findings_header_count`, a new `_rewrite_test_count_pin`)
- Modify: `config/docsync.toml` (a new `[test_count]` table, written by `--fix
  --test-count N` at runtime, not hand-authored here)
- Modify: `AGENTS.md` ("Which test count is authoritative" paragraph, "How to run", and the
  "Procedure before every commit" numbered list -- see the step below)
- Modify: `docs/architecture/documentation-tooling.md` (the one-line DOC006/DOC008
  description, plus a new DOC025 paragraph)
- Test: `tests/test_docsync_logic.py` (append; Task 2 relocates these),
  `tests/test_docsync_declarations.py` (new `TestCountConfig` tests -- these stay put; Task
  2 only moves classes out of `tests/test_docsync_logic.py`), `tests/test_docsync_cli.py`,
  `tests/test_docsync_integrity.py`

**Interfaces:**
- Produces: `declarations.TestCountConfig` (one field, `pinned: int | None = None`) and
  `declarations.load_test_count_config(repo_root, *, config_path=None) -> TestCountConfig`,
  mirroring `ArchiveConfig` / `_validate_archives` / `_archive_config` /
  `load_archive_config` exactly (`scripts/docsync/declarations.py:328,364,393,407`), reusing
  the existing `_positive_int` helper for the one optional key. Add `"test_count": {
  "required": {}, "optional": {"pinned": int}}` to the `_TOP_LEVEL_SCHEMA` dict literal,
  next to `"archives"`.
- Produces: `logic.resolved_test_count_authority(playbook_lines, archive_lines=None,
  batch_log_lines=None, *, pinned=None, explicit_test_count=None) -> TestCountAuthority`.
  Precedence: `explicit_test_count` > `pinned` > `latest_test_count_authority(...)` as a
  cold-start fallback. This is the one function every count-consuming caller uses from now
  on. It does not take `session_lines`: DOC006's own session-field comparison in
  `integrity.py` already reads `session_lines` directly (unchanged) after computing the
  authority, so the pin resolver has no use for it.
- Produces: `renderer.rewrite_recorded_counts(lines: list[str], count: int, patterns:
  Sequence[re.Pattern[str]]) -> list[str]`. Pure: for each line, the first pattern that
  matches has its group(1) span replaced with `str(count)`; every other character of the
  line is untouched. Task 7 does not use this; only Task 1 does.
- Produces: `cli._rewrite_test_count_pin(text: str, count: int) -> str`. Given the current
  text of `config/docsync.toml`, replaces an existing `[test_count]` table's `pinned =`
  line, or appends a new `[test_count]\npinned = N\n` block at the end of the file's text
  when the table is absent -- never between existing `[[value]]` blocks, since a
  single-bracket table opens and closes no array scope but a wrong insertion point beside
  one has bitten this file before (F-DOCSYNC-8's scoping notice). This is a targeted
  find-or-append of one line, not a general TOML writer, because the stdlib `tomllib` this
  repository already relies on is read-only and no new dependency is allowed.
- Consumes: `integrity.SESSION_CURRENT_COUNT_RES` (unchanged, three patterns: the Section 1
  `Tests` row, the STATUS block's own line, the Section 6 heading) and
  `integrity.FINDINGS_HEADER_COUNT_RE` (unchanged).

**Why the tie-break bug cannot be patched, and why the pin lives in `config/docsync.toml`.**
F-DOCSYNC-11 and F-DOCSYNC-22 are both cases where `latest_test_count_authority`'s
date-then-precedence ordering picks the wrong "newest" entry -- once from a same-date tie,
once from a correction to an *older* entry's text that no ordering rule can see. FINDINGS.md
records the full case for both; Q3's ruling is to stop inferring the count from prose
position and let a human assert it instead. The assertion must persist past one `--fix` run,
or the next bare `--check` recomputes the old ordering and rejects the value just corrected.
Q-PIN (owner ruling, 2026-09-25, above) settles where that persisted value
lives: **`config/docsync.toml`, a `[test_count]` table**, not the SESSION_CONTEXT STATUS
block. The STATUS block is `--fix`'s own rendered output (`renderer._build_status_block`
rewrites it every run), and `.claude/CLAUDE.md`'s "machine-derived; never hand-edit it"
contract and global-rules.md Rule 7 ("rendering, not repair") both say a human assertion
cannot durably live inside it. `config/docsync.toml` is the established authored home for
exactly this kind of fact (global rule 1: "Add a declaration ... when a fact starts living
in two places"), with `ArchiveConfig` already the proven pattern for one declared table.
`latest_test_count_authority` itself is untouched (F-DOCSYNC-7's callers still exist, per
Task 2) and becomes the cold-start fallback, used only when `config/docsync.toml` has no
`[test_count]` table at all.

- [x] **Step 1: Write the failing tests for `rewrite_recorded_counts`.** Append to
  `tests/test_docsync_logic.py` (Task 2 moves this class to
  `tests/test_docsync_test_count.py`):

  ```python
  from docsync.renderer import rewrite_recorded_counts


  class TestRewriteRecordedCounts:
      def test_replaces_only_the_digits_in_a_matching_line(self):
          lines = ["| Tests | **1849 passing** across 68 tracked test modules |"]
          pattern = re.compile(r"^\|\s*Tests\s*\|\s*\*\*(\d+)\s+(?:tests?\s+)?pass(?:ing|ed)\*\*")
          assert rewrite_recorded_counts(lines, 1850, [pattern]) == [
              "| Tests | **1850 passing** across 68 tracked test modules |"
          ]

      def test_leaves_a_non_matching_line_untouched(self):
          pattern = re.compile(r"^## 6\.")
          assert rewrite_recorded_counts(["some other line"], 5, [pattern]) == [
              "some other line"
          ]

      def test_first_matching_pattern_wins(self):
          lines = ["## 6. Test structure (1849 tests)"]
          heading = re.compile(r"^##\s+\d+\.\s+Test structure\s+\((\d+)\s+tests\)\s*$")
          decoy = re.compile(r"nomatch")
          assert rewrite_recorded_counts(lines, 1900, [decoy, heading]) == [
              "## 6. Test structure (1900 tests)"
          ]
  ```

- [x] **Step 2: Run to verify they fail.**

  Run: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe" tests/test_docsync_logic.py -q -k RewriteRecordedCounts`
  Expected: `ImportError` -- `rewrite_recorded_counts` does not exist yet.

- [x] **Step 3: Implement `rewrite_recorded_counts` in `renderer.py`,** beside
  `_count_line`, matching the signature in the Interfaces block above. For each line, try
  each pattern in order and stop at the first match; replace that match's captured group 1
  span with `str(count)`, leaving every other character of the line (label text,
  punctuation, bold markers) untouched; a line no pattern matches passes through unchanged.
  Docstring: used only when an operator has explicitly asserted the true count (`--fix
  --test-count N`), rewriting every hand-maintained field that carries a copy of it from the
  same number in one pass, so the four sites this repository keeps (F-DOCSYNC-12) can never
  drift from each other again.

  Add `import re` and `from collections.abc import Sequence` to `renderer.py` if not
  already present.

- [x] **Step 4: Run to verify it passes.**

  Run: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe" tests/test_docsync_logic.py -q -k RewriteRecordedCounts`
  Expected: PASS.

- [x] **Step 5: Write the failing tests for `TestCountConfig`.** Append to
  `tests/test_docsync_declarations.py`, following the file's existing
  `tmp_path / DECLARATIONS_FILENAME` convention (`DECLARATIONS_FILENAME` is already
  imported at the top of this file):

  ```python
  class TestTestCountConfig:
      def test_absent_table_returns_no_pin(self, tmp_path: Path):
          from docsync.declarations import TestCountConfig, load_test_count_config

          assert load_test_count_config(tmp_path) == TestCountConfig()
          assert TestCountConfig().pinned is None

      def test_a_declared_pin_is_read(self, tmp_path: Path):
          from docsync.declarations import load_test_count_config

          path = tmp_path / DECLARATIONS_FILENAME
          path.parent.mkdir(parents=True, exist_ok=True)
          path.write_text("[test_count]\npinned = 1850\n", encoding="utf-8")
          assert load_test_count_config(tmp_path).pinned == 1850

      def test_a_non_integer_pin_is_refused(self, tmp_path: Path):
          from docsync.declarations import DeclarationError, load_test_count_config

          path = tmp_path / DECLARATIONS_FILENAME
          path.parent.mkdir(parents=True, exist_ok=True)
          path.write_text('[test_count]\npinned = "1850"\n', encoding="utf-8")
          with pytest.raises(DeclarationError):
              load_test_count_config(tmp_path)

      def test_an_unknown_key_is_refused(self, tmp_path: Path):
          from docsync.declarations import DeclarationError, load_test_count_config

          path = tmp_path / DECLARATIONS_FILENAME
          path.parent.mkdir(parents=True, exist_ok=True)
          path.write_text("[test_count]\ncount = 1850\n", encoding="utf-8")
          with pytest.raises(DeclarationError, match="unknown key 'count'"):
              load_test_count_config(tmp_path)
  ```

- [x] **Step 6: Run to verify they fail.**

  Run: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe" tests/test_docsync_declarations.py -q -k TestCountConfig`
  Expected: `ImportError` -- neither name exists yet.

- [x] **Step 7: Implement `TestCountConfig` in `declarations.py`,** mirroring
  `ArchiveConfig` / `_validate_archives` / `_archive_config` / `load_archive_config`
  (`declarations.py:328,364,393,407`) field for field: a frozen dataclass with one field
  (`pinned: int | None = None`), a `_validate_test_count(table: object) -> TestCountConfig`
  that rejects an unknown key the same way `_validate_archives` does and validates `pinned`
  with the existing `_positive_int("[test_count]", "pinned", value)` when the key is
  present, a `_test_count_config(declarations: Mapping) -> TestCountConfig` that returns the
  default when `"test_count"` is absent, and `load_test_count_config(repo_root, *,
  config_path=None) -> TestCountConfig` calling `load_declarations` then
  `_test_count_config`. Add `"test_count": {"required": {}, "optional": {"pinned": int}}`
  to the `_TOP_LEVEL_SCHEMA` dict literal, next to `"archives"`.

- [x] **Step 8: Run to verify they pass.**

  Run: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe" tests/test_docsync_declarations.py -q -k TestCountConfig`
  Expected: PASS.

- [x] **Step 9: Write the failing tests for `resolved_test_count_authority`.** Append to
  `tests/test_docsync_logic.py` (Task 2 moves this class to
  `tests/test_docsync_test_count.py`, alongside `TestRewriteRecordedCounts`):

  ```python
  from docsync.logic import resolved_test_count_authority
  from docsync.models import TestCountAuthority


  class TestResolvedTestCountAuthority:
      def test_explicit_count_always_wins(self):
          playbook = _playbook_with_entry("**999 passed**")
          result = resolved_test_count_authority(
              playbook, pinned=1, explicit_test_count=1850
          )
          assert result == TestCountAuthority(count=1850, ambiguous=False)

      def test_a_pinned_count_outranks_fresh_prose(self):
          """F-DOCSYNC-22: an entry corrected out of position must not shadow
          a value already pinned in config/docsync.toml."""
          # Two same-date entries, the classic F-DOCSYNC-11/-22 tie: the
          # position-based scan alone would pick 1849, not 1850.
          playbook = _playbook_two_same_date_entries(older="1850 passed", newer="1849 passed")
          result = resolved_test_count_authority(playbook, pinned=1850)
          assert result == TestCountAuthority(count=1850, ambiguous=False)

      def test_falls_back_to_prose_when_nothing_is_pinned_yet(self):
          """Cold start: no [test_count] table still resolves from the
          entries, exactly as latest_test_count_authority always has."""
          playbook = _playbook_with_entry("**142 passed**")
          result = resolved_test_count_authority(playbook, pinned=None)
          assert result == TestCountAuthority(count=142, ambiguous=False)
  ```

  Add the two fixture helpers near the top of the test file (or reuse existing PLAYBOOK
  builders already in the file if one already produces a two-entry, same-date PLAYBOOK --
  check `TestSyncIntegration` first):

  ```python
  def _playbook_with_entry(bold_count: str) -> list[str]:
      return _playbook(
          "- **Batch 1 is active.**",
          f"### 2026-09-20 - one entry\n\nBody.\n\n`pytest -q` -- {bold_count}\n",
      )


  def _playbook_two_same_date_entries(older: str, newer: str) -> list[str]:
      # "older" sits closer to the end marker (current-batch, written first,
      # reversed to newest-first) and "newer" is the live side-task entry
      # above the end marker -- the exact F-DOCSYNC-11 shape.
      return _playbook(
          "- **Batch 1 is active.**",
          f"### 2026-09-20 - side task\n\nBody.\n\n`pytest -q` -- **{newer}**\n"
          f"<!-- DOCSYNC:CURRENT-BATCH-END -->\n\n"
          f"### 2026-09-20 - batch entry\n\nBody.\n\n`pytest -q` -- **{older}**\n",
      )
  ```

  (Adapt to whatever `_playbook`/marker-building helper the file already exports; do not
  invent a second one if `TestSyncIntegration` already has an equivalent.)

- [x] **Step 10: Run to verify they fail.**

  Run: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe" tests/test_docsync_logic.py -q -k ResolvedTestCountAuthority`
  Expected: `ImportError` -- the name does not exist yet.

- [x] **Step 11: Implement `resolved_test_count_authority` in `logic.py`,** directly above
  `latest_test_count_authority`, matching the signature in the Interfaces block above
  (`playbook_lines, archive_lines=None, batch_log_lines=None, *, pinned=None,
  explicit_test_count=None`). Three `if`/`return` lines in precedence order: return
  `TestCountAuthority(count=explicit_test_count, ambiguous=False)` when
  `explicit_test_count is not None`; else return `TestCountAuthority(count=pinned,
  ambiguous=False)` when `pinned is not None`; else return
  `latest_test_count_authority(playbook_lines, archive_lines, batch_log_lines)`. Docstring:
  every caller that needs "the count a dashboard field should show" -- `_sync`'s STATUS
  block render and every DOC005/006/008 check in `integrity.py` -- goes through this
  function, so `--fix` and `--check` can never compute two different answers to the same
  question; the pin itself is read by each caller (via `declarations.load_test_count_config`),
  not by this function, so `logic.py` gains no dependency on `declarations.py`.

  `TestCountAuthority` is already imported into `logic.py` from `docsync.models`; add
  `Mapping` to the existing `from collections.abc import ...` import if not already there.

- [x] **Step 12: Run to verify they pass.**

  Run: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe" tests/test_docsync_logic.py -q -k ResolvedTestCountAuthority`
  Expected: PASS.

- [x] **Step 13: Wire `_sync` and `_sync_corpus` to thread the pin through.** In
  `scripts/docsync/logic.py`, `_sync`'s signature gains `pinned: int | None = None` and
  `explicit_test_count: int | None = None`. Inside the `if session_lines is not None:`
  block, replace the `latest_test_count_authority(...)` call that builds `count_authority`
  with `resolved_test_count_authority(playbook_lines, new_archive_lines,
  effective_batch_log_lines, pinned=pinned, explicit_test_count=explicit_test_count)`, kept
  immediately before `status_block = _build_status_block(...)`. After `new_session_lines` is
  assembled, add: when `count_authority.count is not None`, run `new_session_lines =
  rewrite_recorded_counts(new_session_lines, count_authority.count,
  list(SESSION_CURRENT_COUNT_RES))` over the whole rebuilt list. This one pass covers the
  STATUS line, the Section 1 `Tests` row and the Section 6 heading in a single mechanism,
  closing F-DOCSYNC-12 for all three SESSION_CONTEXT sites at once. Import
  `SESSION_CURRENT_COUNT_RES` and `rewrite_recorded_counts` at the top of `logic.py`
  (`SESSION_CURRENT_COUNT_RES` stays defined once in `integrity.py`, since DOC006 already
  owns it, and is imported into `logic.py`).

  In `cli.py`, `_sync_corpus` gains a parameter `explicit_test_count: int | None = None`.
  Before calling `_sync`, load `config = load_test_count_config(REPO_ROOT,
  config_path=CONFIG_PATH)` and forward `pinned=config.pinned,
  explicit_test_count=explicit_test_count` into the `_sync(...)` call. Import
  `load_test_count_config` at the top of `cli.py`, alongside the existing
  `load_archive_config` import.

- [x] **Step 14: Add `--test-count` to the CLI and validate it.** In `cli.py`
  `_build_parser()`, add a `--test-count` `int` argument (`metavar="N"`), documented as the
  measured `pytest -q` result that `--fix` writes to `config/docsync.toml` and all four
  count sites. In `main()`, after the existing mode-exclusivity check and before the
  `--check`/`--fix` branch, refuse it without `--fix` and refuse a negative value (both exit
  2, matching this module's other argument-validation errors). Thread
  `explicit_test_count=args.test_count` into both `_sync_corpus(...)` calls the `--fix`
  branch already makes (the one that builds `result`/`updates`, and the post-publish
  verification call) -- the second call re-derives from the now-pinned config, so passing
  the flag there too is harmless and keeps both calls symmetric.

- [x] **Step 15: `_drift_updates` writes the FINDINGS header and the config pin.**
  `_drift_updates` gains a parameter `explicit_test_count: int | None = None`, threaded into
  both of `main()`'s two call sites (the one whose `updates` actually reaches `_publish`,
  and the post-publish `final_updates` verification call) -- only the first is what the
  eventual write depends on, but threading it into both is harmless and keeps them
  symmetric, the same reasoning Step 14 already gives for `_sync_corpus`'s analogous two
  calls. After the existing rotation-handling block, add two writes, both gated on
  `explicit_test_count is not None`:
  - The FINDINGS header, via a new `_rewrite_findings_header_count(text: str, count: int) ->
    str` beside `_plan_text`: rewrites only the header region (mirroring
    `_check_findings_header_count`'s own header-boundary rule, `_FINDINGS_HEADER_END_RE`,
    the first heading line, so the writer and the DOC008 checker agree on where "the header"
    ends), using `rewrite_recorded_counts` with `FINDINGS_HEADER_COUNT_RE`. Plan it with
    `updates.update(_plan_text(REPO_ROOT / documents.findings, new_findings_text))` when the
    text actually changes.
  - `config/docsync.toml`'s pin, via `_rewrite_test_count_pin(text: str, count: int) -> str`
    (Interfaces block above): read the file's current text from `corpus.declarations_path`
    (default `""` if absent), rewrite it, and plan it the same way, at
    `corpus.declarations_path`.

  Import `_FINDINGS_HEADER_END_RE`, `FINDINGS_HEADER_COUNT_RE` and `rewrite_recorded_counts`
  at the top of `cli.py`.

- [x] **Step 16: Change DOC005/006/008 to use `resolved_test_count_authority`, and add
  DOC025.** In `scripts/docsync/integrity.py`, inside `collect_integrity_issues`, load
  `config = load_test_count_config(repo_root, config_path=config_path)` once near the top
  of the function, and replace every `latest_test_count_authority(playbook_lines,
  archive_lines, batch_log_lines)` call (the DOC006 block and `_check_findings_header_count`'s
  caller) with `resolved_test_count_authority(playbook_lines, archive_lines,
  batch_log_lines, pinned=config.pinned)` (no `explicit_test_count`: `--check` never takes
  that flag, by design -- an assertion is only ever made through `--fix`). Import
  `resolved_test_count_authority` from `docsync.logic` and `load_test_count_config` from
  `docsync.declarations` at the top of `integrity.py`, alongside the existing
  `load_closeout_config`/`load_findings_config` import. No import cycle: `logic.py` does not
  import `declarations.py`, and `integrity.py` already imports both.

  **DOC025 (new, WARNING, Q1 ruling 2026-09-25).** Fires only when `config.pinned is not
  None` and the entry recording the newest date across every source
  `latest_test_count_authority` reads is unique and disagrees with the pin. New private
  helper in `logic.py` (name it in the commit body, e.g. `_newest_dated_test_count`),
  signature `(playbook_lines, archive_lines=None, batch_log_lines=None) -> int | None`.
  Extract the candidate-collection-and-sort prefix `latest_test_count_authority` already
  builds (`ordered_candidates`, entries paired with their clamped date, sorted by date then
  precedence, before a winner is picked) into a helper both functions call. Filter that
  ordering to the entries sharing the maximum date: if more than one, return `None` (a
  same-date tie, the F-DOCSYNC-22 shape, stays silent per the ruling). If exactly one, parse
  its count with `_newest_count`, called on that one-entry list -- the same function
  `latest_test_count_authority` itself calls, first with `allow_legacy_fallback=False`, then,
  if that returns `None`, again with `allow_legacy_fallback=True` (the identical two-pass
  sequence `latest_test_count_authority` runs, restricted to the one candidate). This is
  mandatory, not optional: `_valid_inputs`'s own fixture (`tests/test_docsync_integrity.py`)
  carries `"Validation: **390 passed**."`, with no `` `pytest -q` `` text, so it resolves to
  390 only via the legacy-fallback pass -- a helper built to reuse only the strict
  `FULL_SUITE_RESULT_RE` pass returns `None` for it regardless of the pin, silently
  misreporting "no clean parse" as "no disagreement" on the very fixture the tests below use.
  "Unambiguous" means "not `_AMBIGUOUS_COUNT`" (either pass's result), never "matched only by
  the strict pattern." In `integrity.py`, when this helper's result is not `None` and differs
  from `config.pinned`, append `IntegrityIssue("DOC025", "warning", playbook_relative_path,
  None, <invariant naming the disagreement>, <remediation: --fix --test-count if the entry is
  right, or ignore if the pin still is>)`. Warning severity never flips `main()`'s exit code.

  Tests (in `tests/test_docsync_integrity.py`, reusing `_valid_inputs(tmp_path)`, which
  builds exactly one dated Section 4 entry recording `390`):
  ```python
  def test_pin_disagreeing_with_the_sole_newest_entry_warns(tmp_path: Path):
      """_valid_inputs's one entry reads `Validation: **390 passed**.` -- no
      `pytest -q` text -- so this only fires if the helper's legacy-fallback
      pass actually parses it to 390 and compares that against the pin."""
      inputs = _valid_inputs(tmp_path)
      config_path = tmp_path / DECLARATIONS_FILENAME
      config_path.parent.mkdir(parents=True, exist_ok=True)
      config_path.write_text("[test_count]\npinned = 400\n", encoding="utf-8")

      issues = [i for i in collect_integrity_issues(**inputs) if i.code == "DOC025"]

      assert len(issues) == 1
      assert issues[0].severity == "warning"


  def test_pin_agreeing_with_the_sole_newest_entry_is_silent(tmp_path: Path):
      """Silent because 390 was parsed (via the legacy fallback pass -- this
      fixture has no `pytest -q` text) and matches the pin, not because
      nothing parsed: test_pin_disagreeing_with_the_sole_newest_entry_warns
      uses this identical fixture shape and requires the same parse to
      succeed for DOC025 to fire there, so a helper that silently failed to
      parse anything would fail that test, not this one."""
      inputs = _valid_inputs(tmp_path)
      config_path = tmp_path / DECLARATIONS_FILENAME
      config_path.parent.mkdir(parents=True, exist_ok=True)
      config_path.write_text("[test_count]\npinned = 390\n", encoding="utf-8")

      assert "DOC025" not in [i.code for i in collect_integrity_issues(**inputs)]


  def test_a_same_date_tie_stays_silent(tmp_path: Path):
      """F-DOCSYNC-22 shape: two entries share the newest date, so DOC025
      never pushes anyone to reorder them (Q1 ruling)."""
      inputs = _valid_inputs(tmp_path)
      inputs["playbook_lines"].extend(
          [
              "",
              "### 2026-08-05 - A second same-date entry",
              "",
              "Validation: **500 passed**.",
          ]
      )
      inputs["live_documents"]["PLAYBOOK.md"] = inputs["playbook_lines"]
      config_path = tmp_path / DECLARATIONS_FILENAME
      config_path.parent.mkdir(parents=True, exist_ok=True)
      config_path.write_text("[test_count]\npinned = 400\n", encoding="utf-8")

      assert "DOC025" not in [i.code for i in collect_integrity_issues(**inputs)]


  def test_no_pin_is_silent(tmp_path: Path):
      inputs = _valid_inputs(tmp_path)

      assert "DOC025" not in [i.code for i in collect_integrity_issues(**inputs)]
  ```
  Adjust the disagreement/tie fixtures if `_valid_inputs`'s real single entry does not parse
  as an unambiguous `390` once read -- confirm against the actual DOC006 fixtures already in
  this file first.

- [x] **Step 17: Run every affected test file and fix fixtures the pinning change breaks.**

  ```
  "C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe" tests/test_docsync_logic.py tests/test_docsync_declarations.py tests/test_docsync_cli.py tests/test_docsync_integrity.py tests/scripts/dev/test_docsync_preflight.py -v
  ```

  Expected: most pass unchanged -- most fixtures carry no `[test_count]` table, so
  `resolved_test_count_authority` falls back to prose exactly as `latest_test_count_authority`
  always did. A test fails here only if it relied on the SESSION_CONTEXT STATUS block itself
  acting as the pin (the behaviour this task removes, per Q-PIN). For each such failure, add
  a `[test_count]` table to the fixture's `config/docsync.toml` instead of weakening
  `resolved_test_count_authority`. Name every changed test in the commit body per Global
  Constraints.

- [x] **Step 18: F-DOCSYNC-22's exact reproduction, as a regression test.** Append to
  `tests/test_docsync_cli.py` (an end-to-end case through `main()`, not just `logic.py`
  directly -- this is the shape the root-cleanup ledger actually hit):

  ```python
  def test_fix_test_count_survives_a_same_date_correction_to_an_older_entry(
      sync_env, monkeypatch
  ):
      """F-DOCSYNC-22: correcting an OLDER same-date entry's count, after the
      newer entry above it already recorded a different one, must not make
      --check reject the true count once it has been pinned with --test-count."""
      from docsync import cli as cli_mod

      # Two same-date entries: an upper (newer-written) side-task entry at
      # 1849, a lower (older-written) current-batch entry corrected to 1850.
      _append_same_date_entries(sync_env, newer_count=1849, older_count=1850)

      monkeypatch.setattr(
          "sys.argv", ["doc_state_sync.py", "--fix", "--test-count", "1850"]
      )
      assert cli_mod.main() == 0

      monkeypatch.setattr("sys.argv", ["doc_state_sync.py", "--check"])
      assert cli_mod.main() == 0

      session = (sync_env / ".claude" / "SESSION_CONTEXT.md").read_text(encoding="utf-8")
      findings = (sync_env / "FINDINGS.md").read_text(encoding="utf-8")
      config = (sync_env / "config" / "docsync.toml").read_text(encoding="utf-8")
      assert "**1850 passed**" in session
      assert "**1850 passing**" in session
      assert "## 6. Test structure (1850 tests)" in session or "1850 tests" in session
      assert "1850 tests across" in findings
      assert "[test_count]" in config and "pinned = 1850" in config
  ```

  Write `_append_same_date_entries` following whatever helper `tests/test_docsync_cli.py`
  already uses to grow its `sync_env` PLAYBOOK fixture. Adjust the exact assertion strings
  to match this repository's real rendered format -- confirm by reading one real `--fix`
  output during Step 19's live probe, do not guess the format from memory.

  Run: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe" tests/test_docsync_cli.py -q -k same_date_correction`
  Expected: FAIL before Steps 11-16, PASS after.

- [x] **Step 19: Gates and live probe.** `doc_state_sync.py --check` at exit 0 first (this
  touches `scripts/docsync/`), then per the verification standard, in `/c/ssprobe/corpus`:
  - **Red, prior behaviour (documented, not this task's pair):** from `base` with this
    task's commit reverted, the F-DOCSYNC-22 shape (two same-date entries, older corrected)
    -> bare `--fix` then `--check` -> DOC006/DOC008.
  - **Red, planted:** this task's tree, Section 1 `Tests` row hand-edited wrong, config pin
    left correct -> `--check` -> DOC006.
  - **Green, real workflow:** a fresh copy, new dated entry with the corrected count ->
    `--fix --test-count <N>` -> `config/docsync.toml` gains `pinned = <N>`, all four sites
    show `<N>` -> `--check` -> exit 0.
  - **Near-miss green:** bare `--fix` again -> every site and the pin unchanged -> `--check`
    -> exit 0.
  - **DOC025 (WARNING only):** pinned `<N>`, one further dated entry as the sole newest with
    a different count -> `--check` -> DOC025 printed, exit 0.
  - Paste the probe table into the Section 4 entry.

- [x] **Step 20: Update the prose.** In `AGENTS.md`, "Doc Sync Rules" > "Integrity
  diagnostics", replace the "Which test count is authoritative" paragraph with:

  ```
  **Which test count is authoritative.** `--fix --test-count N` is how a measured count
  enters the corpus: it pins `N` in `config/docsync.toml`'s `[test_count]` table and writes
  the SESSION_CONTEXT STATUS block, the Section 1 `Tests` row, the Section 6 heading and the
  FINDINGS.md header from the same number, in one command. Once a count is pinned, it stays
  authoritative across every later `--fix` (with no `--test-count`) and `--check` --
  Section 4 prose is not re-scanned for it, so a same-date tie or an out-of-position
  correction (F-DOCSYNC-11, F-DOCSYNC-22) can never shadow the true count again. `--check`
  prints a non-blocking DOC025 warning if the single newest dated log entry disagrees with
  the pin. A repository with no pin falls back to the newest full-suite `pytest -q` result
  found in the log, exactly as before.
  ```

  In "How to run", add a line after the first `--fix` example:

  ```
  python scripts/doc_state_sync.py --fix --test-count N   # after measuring the suite; pins N and writes all four count sites
  ```

  Three other sites still instruct the pre-Q-PIN workflow (a hand-edit of a now-rendered
  field, or a bare `--fix` that can no longer "refresh" a changed count); the Pre-Flight
  Checklist line "`pytest -q` passes (baseline count is in SESSION_CONTEXT Section 1)" was
  checked and stays true (Section 1 still shows the count, now rendered from the pin), so it
  needs no edit. Fix the three, one replacement line each:
  - "Side-Task Handling," step 2: "Run `doc_state_sync.py --fix --test-count N` (N =
    the just-measured `pytest -q` result) when the count changed, bare `--fix` otherwise;
    update SESSION_CONTEXT Section 1's batch-status row by hand if project state changed --
    the test-count field is rendered, never hand-edited."
  - "What to update after a WP or side-task commit": "SESSION_CONTEXT Section 1's
    batch-status row by hand if changed (the test-count field is rendered by `--fix
    --test-count N`, never hand-edited)."
  - "Batch Close-Out Procedure," step 5: "**Run `--fix --test-count N`** (N = the
    just-measured `pytest -q` result) if the count changed since step 1's sync, bare `--fix`
    otherwise, to refresh the STATUS block."

  Then reorder the "Procedure before every commit" numbered list so the suite is measured
  before `--fix` runs, since `--fix --test-count N` needs a measured `N`: swap today's step
  2 (`--fix`) and step 3 (`pytest -q`), so the list reads `1` (PLAYBOOK), `2` (`pytest -q`
  -- measure and note `N`), `3` (`python scripts/doc_state_sync.py --fix --test-count N`;
  bare `--fix` remains documented for a commit that does not change the count), `4`
  (`pre-commit run --all-files`), `5` (`--check`), `6` (stage named paths), `7` (commit).
  Task 6 edits this same list again, for staging order, starting from this renumbering.

  In `docs/architecture/documentation-tooling.md`, replace "`DOC006` (every named session
  test count must match the newest full-suite run) and `DOC008` (the findings header count
  must match that same run)" with "`DOC006` (every named session test count must match the
  count pinned in `config/docsync.toml`, or the newest full-suite run if none has been
  pinned) and `DOC008` (the same, for the findings header)". Add one short paragraph after
  the existing DOC024 paragraph: "**DOC025 is a warning-only pin-staleness check**,
  implemented in `scripts/docsync/integrity.py`. It fires only when exactly one Section 4
  entry (across every source `latest_test_count_authority` reads) carries the newest date
  and its count disagrees with `config/docsync.toml`'s `[test_count]` pin; a same-date tie
  or an absent pin stays silent. It never blocks (Q1 ruling, 2026-09-25)."

- [x] **Step 21: Resolve all four findings and commit.** Reason, shared across the four
  records: "an explicit `--fix --test-count N` (`scripts/docsync/cli.py`) pins the count in
  `config/docsync.toml`'s `[test_count]` table (`scripts/docsync/declarations.py`
  `TestCountConfig`), which `resolved_test_count_authority` (`scripts/docsync/logic.py`)
  reads instead of re-deriving from Section 4 prose position; `rewrite_recorded_counts`,
  `_rewrite_findings_header_count` and `_rewrite_test_count_pin` write all four sites plus
  the pin from it in one `--fix` run; a new DOC025 warns, without blocking, when the newest
  dated log entry disagrees with the pin (Q1 ruling)." This task's own commit uses the new
  mechanism it just built:

  ```bash
  "C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe" scripts/doc_state_sync.py --fix --test-count <measured N>
  "C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe" scripts/doc_state_sync.py --check
  SKIP=doc-state-sync-check git commit -m "feat(docsync): Pin the test count in config/docsync.toml"
  ```

**Acceptance:** `--fix --test-count N` pins `N` in `config/docsync.toml` and writes the
STATUS block, the SESSION_CONTEXT Section 1 row, the Section 6 heading and the FINDINGS
header from it; a bare `--fix` or `--check` afterward never overrides a pinned value from
prose; a disagreeing sole-newest entry prints DOC025 without blocking, silent on a same-date
tie or no pin; the F-DOCSYNC-22 reproduction (Step 18) passes; `latest_test_count_authority`
is unchanged and still used as the cold-start fallback; every existing docsync test passes,
with every fixture change named in the commit body.

---

### Task 2: Repoint `TestLatestTestCount`, then split the file (F-DOCSYNC-7, F-MAS-3)

**Files:**
- Modify: `scripts/docsync/logic.py` (delete `_latest_test_count_from_entries`)
- Create: `tests/test_docsync_wp_numbers.py` (from `TestCollectWpNumbers`)
- Modify: `tests/test_docsync_test_count.py` (absorbs the repointed `TestLatestTestCount`)
- Create: `tests/test_docsync_sync_integration.py` (from `TestSyncIntegration`)
- Create: `tests/test_docsync_log_merging.py` (from `TestMergeEntriesIntoLog`)
- Create: `tests/test_docsync_archive_split.py` (from `TestSplitArchive` and
  `TestDedupSorted`)
- Create: `tests/test_docsync_section3_parsing.py` (from
  `TestParseActiveBatchStateConflicting`)
- Delete: `tests/test_docsync_logic.py` (777 lines today, entirely distributed above)

**Interfaces:** Removes `logic._latest_test_count_from_entries`. Nothing in
`scripts/docsync/` calls it (confirmed by Step 1 below); every remaining reference becomes
`logic.latest_test_count_authority(...).count`.

**Why one commit.** F-DOCSYNC-7's own removal note says deleting the wrapper "rewrites
eight test call sites, which is a refactor rather than a review fix" -- exactly the parity
requirement `AGENTS.md` Rule 4 (refactor requires parity tests) exists for, and exactly
what F-MAS-3's file split needs: repointing the eight call sites first, in the file they
already live in, proves the replacement behaves identically before anything moves.

- [x] **Step 1: Confirm nothing outside tests calls the wrapper.**

  ```bash
  git grep -n "_latest_test_count_from_entries" -- '*.py'
  ```

  Expected hits only: the definition in `logic.py`, and the eight in
  `tests/test_docsync_logic.py` (the import and the seven-or-eight call sites inside
  `TestLatestTestCount`, per the finding). Any other hit means a live caller exists: stop
  and report NEEDS_CONTEXT.

- [x] **Step 2: Repoint the eight call sites, in place.** In `tests/test_docsync_logic.py`:
  - Change the import from `from docsync.logic import (_dedup_sorted,
    _latest_test_count_from_entries, _merge_entries_into_log, _split_archive, _sync)` to
    the same list with `latest_test_count_authority` in place of
    `_latest_test_count_from_entries`.
  - Every call `_latest_test_count_from_entries(playbook[, archive_lines])` becomes
    `latest_test_count_authority(playbook[, archive_lines]).count`.
  - `TestLatestTestCount`'s docstring/comment mentioning "`_latest_test_count_from_entries`
    scans in reverse to find newest" is updated to name `latest_test_count_authority`
    instead (the scan-in-reverse behaviour itself is unchanged, only the entry point's
    name).

- [x] **Step 3: Run to verify parity.**

  ```
  "C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe" tests/test_docsync_logic.py -q -k TestLatestTestCount
  ```

  Expected: PASS, same assertions, same count. This is the parity proof Rule 4 requires
  before the split below moves anything.

- [x] **Step 4: Delete the wrapper.** Remove `_latest_test_count_from_entries` whole from
  `scripts/docsync/logic.py`.

  ```
  "C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe" tests/test_docsync_logic.py -q
  ```

  Expected: PASS (the file no longer imports the deleted name).

- [x] **Step 5: Split the file along F-MAS-3's seven concerns.** Move each class, its
  class-local imports, and any module-level helper it alone uses, into the file named
  above. `TestLatestTestCount` (now testing `latest_test_count_authority`), and Task 1's two
  own additions to this file -- `TestRewriteRecordedCounts` and
  `TestResolvedTestCountAuthority` -- all merge into the *existing*
  `tests/test_docsync_test_count.py`, consolidating with that file's `_sync`-level behaviour
  tests -- F-MAS-3 names the `TestLatestTestCount` consolidation explicitly, and Task 1's
  own Files list already promises the other two move here. `TestSplitArchive` and
  `TestDedupSorted` share `tests/test_docsync_archive_split.py`: both exercise the archive
  rotation/dedup seam. Give each new file a one-line module docstring naming its seam (for
  example `"""Tests for docsync.parser._collect_wp_numbers."""`). Every new file keeps only
  the top-of-file imports its own class(es) actually use -- let the first collection run
  name any unused or missing import. `tests/test_docsync_declarations.py`'s own
  `TestTestCountConfig` (Task 1) is not part of this move: it was already appended to its
  permanent home.

- [x] **Step 6: Collect and run every new file.**

  ```
  "C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe" tests/test_docsync_wp_numbers.py tests/test_docsync_test_count.py tests/test_docsync_sync_integration.py tests/test_docsync_log_merging.py tests/test_docsync_archive_split.py tests/test_docsync_section3_parsing.py -v
  ```

  Expected: PASS, same total test count as `tests/test_docsync_logic.py` +
  `tests/test_docsync_test_count.py` carried before the split (no test gained or lost by
  the move itself).

- [x] **Step 7: Delete the now-empty original and run the full docsync corpus.**

  ```bash
  git rm tests/test_docsync_logic.py
  ```

  ```
  "C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe" -q --ignore=tests/scripts/dev/test_mutation_test.py -p no:cacheprovider
  ```

  Expected: PASS, same total suite count as before this task (the split moves tests, it
  does not add or remove any).

- [x] **Step 8: Update the module count.** The suite gained roughly five tracked test
  modules net (six new files minus the one deleted, `test_docsync_test_count.py` already
  existed so does not count as new). Recompute the real number
  (`AGENTS.md` anti-pattern 10 -- re-measure, do not guess) and record it via
  `doc_state_sync.py --fix --test-count N` (Task 1's new mechanism; the total test count is
  unchanged by this task, but the module count in the FINDINGS header and SESSION_CONTEXT
  Section 6 heading text names modules too -- confirm the exact rendered wording matches
  what `--fix` produces before hand-checking anything).

- [x] **Step 9: Gates and commit.** This touches `scripts/docsync/logic.py`
  (R7 applies).

  ```
  "C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe" scripts/doc_state_sync.py --check
  ```

  ```bash
  git add tests/test_docsync_wp_numbers.py tests/test_docsync_test_count.py tests/test_docsync_sync_integration.py tests/test_docsync_log_merging.py tests/test_docsync_archive_split.py tests/test_docsync_section3_parsing.py
  git rm tests/test_docsync_logic.py
  ```

- [x] **Step 10: Resolve both findings.** F-DOCSYNC-7's reason: "the eight
  `TestLatestTestCount` call sites now call `latest_test_count_authority(...).count`
  directly; the wrapper `_latest_test_count_from_entries` is deleted from
  `scripts/docsync/logic.py`." F-MAS-3's reason: "`tests/test_docsync_logic.py` is split
  along its seven seams: WP collection, test-count authority (consolidated into
  `tests/test_docsync_test_count.py`), whole-sync integration, log merging, archive
  splitting plus dedup, and Section 3 parsing." Then:

  ```bash
  SKIP=doc-state-sync-check git commit -m "test(docsync): Repoint the count wrapper's tests, then split test_docsync_logic.py"
  ```

**Acceptance:** `git grep _latest_test_count_from_entries -- '*.py'` returns nothing;
every test that was in `tests/test_docsync_logic.py` still exists, in its new home, and
still passes; the deleted file is gone; the total suite count is unchanged by the move.

---

### Task 3: A work package closes only on an explicit `WP-N complete` line (F-DOCSYNC-15, Q4 = a)

**Files:**
- Modify: `scripts/docsync/parser.py` (`_collect_wp_numbers`)
- Modify: `scripts/docsync/renderer.py` (`_next_wp_number`, `_build_status_block` --
  interface unchanged, only how "completed" is computed)
- Modify: `scripts/docsync/integrity.py` (`_computed_next_wp` -- same computation,
  unaffected call shape)
- Modify: `AGENTS.md` ("Side-Task Handling", "Doc Sync Rules")
- Test: `tests/test_docsync_wp_numbers.py` (Task 2's new home for
  `TestCollectWpNumbers`), `tests/test_docsync_sync_integration.py`,
  `tests/test_docsync_integrity.py`

**Interfaces:** `parser._collect_wp_numbers(entries: list[Entry]) -> list[int]` keeps its
signature and return type; only its rule for "this entry names WP-N as done" changes.
Every caller (`renderer._next_wp_number`, `renderer._build_status_block`) is unaffected by
the signature, only by the set of numbers it now returns for the same input.

**Why this is F-DOCSYNC-15.** `_collect_wp_numbers` today counts every `WP-<n>` heading
token as completed, so a multi-commit work package's first tagged commit already claims the
whole package done -- see FINDINGS.md F-DOCSYNC-15 for the full `BATCH22_LOG.md`
reproduction. Q4's ruling: close on an explicit `**Status:** WP-N complete` body line
instead. `_extract_entry_batch`, `_merge_entries_into_log` and the rotation split in `_sync`
all key off the heading tag already, not off completion, so they are unaffected.

- [x] **Step 1: Write the failing tests.** In `tests/test_docsync_wp_numbers.py` (created
  by Task 2), extend `TestCollectWpNumbers`:

  ```python
  def test_a_heading_tag_alone_does_not_complete_the_work_package(self):
      """F-DOCSYNC-15: the first commit of a multi-commit WP must not claim
      the whole package is done just because its heading names WP-4."""
      entries = [
          _entry(
              heading="### 2026-09-20 - (Batch 22 WP-4)",
              body="Some progress. No explicit completion line.",
          )
      ]
      assert _collect_wp_numbers(entries) == []

  def test_an_explicit_status_line_completes_the_work_package(self):
      entries = [
          _entry(
              heading="### 2026-09-20 - (Batch 22 WP-4)",
              body="**Status:** WP-4 complete\n\nEverything landed.",
          )
      ]
      assert _collect_wp_numbers(entries) == [4]

  def test_the_status_line_is_recognized_case_and_spacing_tolerant(self):
      entries = [
          _entry(heading="### 2026-09-20 - untagged", body="**Status:**   wp-7 Complete")
      ]
      assert _collect_wp_numbers(entries) == [7]

  def test_a_status_line_for_a_different_wp_does_not_complete_this_ones_heading_tag(self):
      entries = [
          _entry(
              heading="### 2026-09-20 - (Batch 22 WP-4)",
              body="**Status:** WP-3 complete (an earlier package finished late)",
          )
      ]
      assert _collect_wp_numbers(entries) == [3]

  def test_several_entries_each_contribute_their_own_completion(self):
      entries = [
          _entry(heading="### 2026-09-19 - a", body="**Status:** WP-1 complete"),
          _entry(heading="### 2026-09-20 - b", body="Body with no completion line."),
          _entry(heading="### 2026-09-21 - c", body="**Status:** WP-2 complete"),
      ]
      assert _collect_wp_numbers(entries) == [1, 2]
  ```

  Add an `_entry(heading, body)` helper if `tests/test_docsync_wp_numbers.py` does not
  already build `Entry` objects directly; construct a real `docsync.models.Entry` with
  `lines=tuple(body.splitlines())` and a `fingerprint` computed the same way
  `parser._fingerprint` does (import and call it, do not hand-write a hash).

- [x] **Step 2: Run to verify they fail.**

  Run: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe" tests/test_docsync_wp_numbers.py -q`
  Expected: the first test (heading-tag-alone) already passes today by accident only if the
  body has no `WP-` token in it either -- re-check against the *current* regex
  (`\bWP-(\d+)\b` scanned over `entry.heading`, which the fixture's heading contains) --
  this test should FAIL today, since today's code reads `WP-4` straight out of the heading.
  The remaining four tests FAIL: today's code never looks at the body at all.

- [x] **Step 3: Implement the new rule.** In `scripts/docsync/parser.py`, add a compiled
  pattern `WP_COMPLETE_STATUS_RE = re.compile(r"^\s*\*\*Status:\*\*\s+WP-(\d+)\s+complete\b",
  re.IGNORECASE)` near `_collect_wp_numbers` itself (not `NEXT_WP_CLAIM_RE`, which lives in
  `scripts/docsync/integrity.py`, not in this file). Replace `_collect_wp_numbers`'s body:
  scan every `entry.lines` line of every entry with `WP_COMPLETE_STATUS_RE`, collect
  `int(match.group(1))` into a `set[int]`, and return it `sorted()` -- the signature and
  return type are unchanged (Interfaces block above); only the source of "this entry
  completed WP-N" moves from the heading tag to this line match. Docstring: a heading's
  `(Batch N WP-X)` tag still identifies which package an entry belongs to (still read by
  `_extract_entry_batch` for rotation); it no longer, by itself, means that package is done
  (F-DOCSYNC-15, Q4 = a).

- [x] **Step 4: Run to verify they pass.**

  Run: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe" tests/test_docsync_wp_numbers.py -q`
  Expected: PASS.

- [x] **Step 5: Sweep every existing test that built a heading-tagged entry expecting it
  to read as complete.** This is the change's real blast radius: any fixture in
  `tests/test_docsync_sync_integration.py` and `tests/test_docsync_integrity.py` that
  asserts a `_next_wp_number`/DOC007 outcome from a `(Batch N WP-X)` heading alone, with no
  `**Status:** WP-N complete` line in the body, now resolves differently.

  ```
  "C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe" tests/test_docsync_sync_integration.py tests/test_docsync_integrity.py tests/test_docsync_cli.py -v
  ```

  For each failure, add the explicit `**Status:** WP-N complete` line to the fixture entry
  that the test's own narrative says finished that package -- do not weaken
  `WP_COMPLETE_STATUS_RE` to match a bare heading tag again, since that is precisely the
  bug. Name every changed fixture/test in the commit body.

- [x] **Step 6: A regression test reproducing the exact BATCH22_LOG.md shape.** Append to
  `tests/test_docsync_sync_integration.py`:

  ```python
  def test_three_tagged_commits_do_not_claim_the_package_done_until_the_last(self):
      """Reproduces docs/history/logs/BATCH22_LOG.md: three (Batch 22 WP-4)
      entries landed before WP-4 was actually finished (F-DOCSYNC-15)."""
      playbook = _playbook(
          "- **Batch 22 is active.**",
          "### 2026-09-20 - (Batch 22 WP-4) first commit\n\nProgress.\n\n"
          "### 2026-09-20 - (Batch 22 WP-4) second commit\n\nMore progress.\n\n"
          "### 2026-09-20 - (Batch 22 WP-4) third commit\n\n"
          "**Status:** WP-4 complete\n\nDone.\n",
      )
      result = _sync(playbook, [], _session_lines_template(), keep_non_current=4)
      status = "\n".join(result.session_lines)
      assert "Completed work packages in current-batch entries: WP-4." in status
  ```

  Adapt the exact STATUS block wording to whatever `_build_status_block` actually renders
  (confirm by reading its current source, already reviewed in this plan's research);
  correct the assertion string if it differs.

  Run: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe" tests/test_docsync_sync_integration.py -q -k three_tagged_commits`
  Expected: PASS after Step 3 (this specific case never needed a fixture fix in Step 5,
  since it names its own completion line correctly by construction).

- [x] **Step 7: Update the prose.** In `AGENTS.md` "Side-Task Handling" or the
  Commit Rules section (wherever the `(Batch N WP-X)` tag is documented), add one sentence:
  "A tagged heading identifies which work package an entry belongs to; only an explicit
  `**Status:** WP-N complete` line in the entry body marks that package done (F-DOCSYNC-15).
  A multi-commit work package's earlier commits carry the tag without that line." Grep for
  any other place `AGENTS.md` or `docs/architecture/documentation-tooling.md` describes
  "a WP-tagged heading is complete" and correct it in the same commit (Anti-Pattern 11).

- [x] **Step 8: Gates and live probe.** This touches `scripts/docsync/parser.py` and
  `renderer.py` (R7 applies). Per the verification standard, in `/c/ssprobe/corpus`:
  - **Red:** BATCH22_LOG.md shape, one `(Batch N WP-X)` heading, no completion line -> the
    STATUS block (and DOC007, if Section 3 claims `WP-<X+1>` next) disagrees with the true
    state -- before this fix, the tool would have already called WP-X complete.
  - **Green:** same fixture plus `**Status:** WP-N complete` -> STATUS block and DOC007
    agree WP-N is done and the next one is named.
  - **Near-miss green:** heading tag, body mentions "WP-4" in ordinary prose, not the exact
    `**Status:** WP-4 complete` shape -> NOT read as complete.

- [x] **Step 9: Resolve F-DOCSYNC-15 and commit.** Reason: "`_collect_wp_numbers`
  (`scripts/docsync/parser.py`) now requires an explicit `**Status:** WP-N complete` line
  in an entry's body; a heading's `(Batch N WP-X)` tag alone no longer marks that package
  done (Q4 = a)."

  ```bash
  "C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe" scripts/doc_state_sync.py --check
  SKIP=doc-state-sync-check git commit -m "fix(docsync): Require an explicit line to close a work package"
  ```

**Acceptance:** a heading-only `(Batch N WP-X)` entry is never read as completing that
package; an explicit `**Status:** WP-N complete` line is; the BATCH22_LOG.md reproduction
(Step 6) passes; every existing test that relied on the old heading-only rule is updated
and named in the commit body; the live probe shows both states correctly.

---

### Task 4: Case-consistent `BATCH*` discovery (F-DOCSYNC-6)

**Files:**
- Modify: `scripts/docsync/cli.py` (`_check_root_batch_files`, `_archived_definitions`,
  `_read_live_documents`)
- Test: `tests/test_docsync_cli.py`

**Interfaces:** Produces `cli._batch_filename_candidates(directory: Path, name_re:
re.Pattern[str]) -> list[Path]`, used by the three call sites above in place of
`directory.glob("BATCH*...")`.

**F-DOCSYNC-6's outside-root item is already fixed -- confirm, do not re-fix.** The
finding's fourth item ("a live document resolving outside the working directory raises
`ValueError` rather than the documented exit 2") was addressed by `88f0514` ("fix(docsync):
Validate declared document paths before reading", 2026-09-25, filed as F-DOCSYNC-21).
`scripts/docsync/declarations.py` `_Files._path` and `_Files._relative` (confirmed present
at lines 684-705 of the current tree) now raise `DeclarationError` -- which `cli.py`
`main()` turns into exit 2, per the documented contract -- instead of letting a bare
`ValueError` propagate. `DeclarationError` is not a `ValueError` subclass check away from
`SyncError`'s own exit-2 handling; it is caught by the same `except SyncError` clause in
`main()`'s `--check`/`--fix` branch since `DeclarationError` subclasses `SyncError`
(confirmed via `tests/test_docsync_declarations.py`'s existing
`test_explicit_missing_path_is_refused`-style coverage). This task's only job for that item
is to record the evidence; it makes no code change for it.

- [x] **Step 1: Confirm the outside-root fix, with evidence, and record it.** Run:

  ```bash
  git log --format="%H %s" -1 88f0514
  git show 88f0514 -- scripts/docsync/declarations.py | grep -n "resolves outside"
  ```

  Expected: the commit exists on this branch's history and its diff adds the
  `"... resolves outside the repository root"` `DeclarationError` messages at
  `_Files._path` and `_Files._relative`. Paste this evidence into the Section 4 entry as:
  "F-DOCSYNC-6's outside-root item was confirmed already fixed by `88f0514`
  (F-DOCSYNC-21); no code change made for it here."

- [x] **Step 2: Write the failing test for case-consistent discovery.** Append to
  `tests/test_docsync_cli.py`:

  ```python
  def test_batch_definition_discovery_is_case_consistent_across_platforms(tmp_path):
      """F-DOCSYNC-6: Path.glob's case sensitivity follows the OS (insensitive
      on Windows, sensitive on POSIX). A directory-listing scan matched with
      the same case-insensitive regex used everywhere else in this module
      finds the same files on both, instead of one platform silently missing
      a lower-case batch definition the other would see."""
      from docsync.cli import _batch_filename_candidates
      from docsync.parser import root_definition_pattern

      names = [
          "BATCH23_DEFINITION.md",
          "batch24_definition.md",
          "Batch25_Definition.md",
          "not_a_batch.md",
          "BATCH26_PROPOSAL.md",
      ]
      for name in names:
          (tmp_path / name).write_text("x", encoding="utf-8")

      found = set()
      for n in (23, 24, 25, 26):
          found.update(
              p.name for p in _batch_filename_candidates(tmp_path, root_definition_pattern(n))
          )
      assert found == {
          "BATCH23_DEFINITION.md",
          "batch24_definition.md",
          "Batch25_Definition.md",
          "BATCH26_PROPOSAL.md",
      }
  ```

  Use different batch numbers per case-variant deliberately: on a case-insensitive
  filesystem (default Windows/macOS), `tmp_path / "BATCH23_DEFINITION.md"` and `tmp_path /
  "batch23_definition.md"` would be the *same* file, so a same-number variant would corrupt
  the fixture rather than test discovery.

- [x] **Step 3: Run to verify it fails.**

  Run: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe" tests/test_docsync_cli.py -q -k case_consistent`
  Expected: `ImportError` -- `_batch_filename_candidates` does not exist yet.

- [x] **Step 4: Implement the case-insensitive scan.** In `scripts/docsync/cli.py`, add near
  `_BATCH_LOG_RE`: `_batch_filename_candidates(directory: Path, name_re: re.Pattern[str]) ->
  list[Path]` -- return `[]` when `directory` is not a directory, otherwise the sorted list
  of files in `directory.iterdir()` whose name matches `name_re`. Docstring: `Path.glob`'s
  case sensitivity follows the OS (insensitive on Windows, sensitive on POSIX) while every
  regex this module already filters glob's candidates with (`_BATCH_LOG_RE`,
  `root_definition_pattern`) is `re.IGNORECASE` -- that mismatch meant a lower-case batch
  file was visible to discovery on Windows and invisible on Linux (F-DOCSYNC-6); scanning
  the listing directly with the same regex everywhere makes discovery identical on every
  platform.

  Replace each of the three call sites:
  - `_check_root_batch_files`: `for f in sorted(root.glob("BATCH*.md")):` becomes
    `for f in _batch_filename_candidates(root, re.compile(r"^BATCH.*\.md$", re.IGNORECASE)):`
  - `_archived_definitions`: `for path in sorted(directory.glob("BATCH*_DEFINITION.md"))`
    becomes `for path in _batch_filename_candidates(directory, re.compile(r"^BATCH\d+_DEFINITION\.md$", re.IGNORECASE))`
  - `_read_live_documents`: `for definition_path in REPO_ROOT.glob("BATCH*.md"):` becomes
    `for definition_path in _batch_filename_candidates(REPO_ROOT, re.compile(r"^BATCH.*\.md$", re.IGNORECASE)):`

  `_get_batch_log_path`/`_read_batch_log_lines`'s `LOGS_DIR.glob("BATCH*_LOG.md")` sites are
  left unchanged in this task: they are already filtered by `_BATCH_LOG_RE` immediately
  after the glob, but converting them too is in scope only if the live probe (Step 6) shows
  the same platform mismatch there. Check first; if it reproduces, convert them with the
  same helper and say so in the commit body.

- [x] **Step 5: Run to verify it passes, then the full docsync corpus.**

  ```
  "C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe" tests/test_docsync_cli.py -q
  "C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe" -q --ignore=tests/scripts/dev/test_mutation_test.py -p no:cacheprovider
  ```

- [x] **Step 6: Gates and live probe.** In `/c/ssprobe/corpus`:
  - **Red:** create a lower-case `batch99_definition.md` inside
    `docs/history/definitions/`; before this task's fix, whether it is discovered depends
    on the probe host's OS (this repository's CI and the owner's machine are different
    platforms, which is the actual defect) -- run `--check` and record whatever the current
    behaviour is on this probe's host as the "before" baseline. This item's live probe is
    necessarily host-dependent for the *before* state; the *after* state is not.
  - **Green (after the fix):** same fixture; confirm `_batch_filename_candidates` finds it
    identically regardless of host, proven by the unit test in Step 2 (which does not
    depend on real OS case-folding, since it uses distinct filenames per case-variant) --
    the live probe here demonstrates the real CLI path (`--check`/`--close-batch`) treats
    the file the same way, by running `--check` twice: once via the normal `Path.glob`
    build (pre-fix corpus) and once via this task's tree, both reading the same
    lower-case-named fixture file, and confirming both report seeing it.
  - **Near-miss green:** a correctly-cased file; unaffected either way.

- [x] **Step 7: Resolve F-DOCSYNC-6 and commit.** Reason: "the case-inconsistent-glob item
  is fixed by `_batch_filename_candidates` (`scripts/docsync/cli.py`), matched with the
  same case-insensitive regex every other discovery site already uses; the outside-root
  item was confirmed already fixed by `88f0514` (F-DOCSYNC-21); the three remaining items
  (four-space indentation scan, no-check on trailing prose, deleted-but-unstaged files) are
  the owner's 2026-09-23 accepted design boundaries and stay as documented." This finding
  is now fully resolved (5 of 5 items accounted for).

  ```bash
  "C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe" scripts/doc_state_sync.py --check
  SKIP=doc-state-sync-check git commit -m "fix(docsync): Discover BATCH* files case-consistently"
  ```

**Acceptance:** `_batch_filename_candidates` finds the same files regardless of the host
OS's filesystem case sensitivity (proven by Step 2's distinct-filenames test, which does
not depend on which OS runs it); F-DOCSYNC-6 is fully resolved, with cited evidence for the
already-fixed outside-root item rather than a repeated fix.

---

### Task 5: Two worktree-guard bugs (F-WORKTREE-3)

**Files:**
- Modify: `scripts/dev/_worktree_guard_lineage.py` (`classify_lineage`)
- Modify: `scripts/dev/_worktree_guard_diagnostics.py` (`missing_base_diagnostic`,
  `missing_base_remediation`)
- Test: `tests/scripts/dev/test_worktree_guard.py`, `tests/scripts/dev/test_worktree_guard_base_ref.py`

**Interfaces:** No signature changes to either function's callers; `missing_base_
remediation(base_ref: str) -> str` now expects the *raw* ref (its existing type), not a
pre-labelled display string -- `missing_base_diagnostic` is the one caller and this task
changes what it passes.

This task does not touch `scripts/docsync/`, `config/docsync.toml` or
`scripts/dev/docsync_preflight.py`, so R7 does not apply: commit with every hook, no
`SKIP=`.

**Bug 1: WT010 never fires for a detached, dirty worktree.** See FINDINGS.md F-WORKTREE-3.
`classify_lineage`'s `if snapshot.detached:` branch returns before ever reaching either
`if snapshot.dirty:` check further down, both of which live only in the non-detached path,
so a detached, dirty, non-CI worktree today reports WT012 alone.

- [x] **Step 1: Write the failing test.** In `tests/scripts/dev/test_worktree_guard.py`,
  extend `test_detached_ci_skips_and_detached_local_fails` or add beside it:

  ```python
  def test_detached_and_dirty_reports_both_wt012_and_wt010():
      """F-WORKTREE-3: a detached, dirty, local worktree must not hide its
      dirty state behind WT012 alone -- both are independent facts a reader
      needs before touching history."""
      issues = classify_lineage(_snapshot(actual_branch=None, detached=True, dirty=True))
      assert [issue.code for issue in issues] == ["WT012", "WT010"]

  def test_detached_ci_dirty_still_only_reports_wt011():
      """A recognized CI checkout is not local work in progress; its
      dirtiness (if any -- typically build artifacts) is not the same signal
      WT010 exists to protect (F-WORKTREE-3 names the local case only)."""
      issues = classify_lineage(
          _snapshot(actual_branch=None, detached=True, recognized_ci=True, dirty=True)
      )
      assert [issue.code for issue in issues] == ["WT011"]
  ```

- [x] **Step 2: Run to verify the first fails.**

  Run: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe" tests/scripts/dev/test_worktree_guard.py -q -k detached_and_dirty`
  Expected: FAIL -- today's result is `["WT012"]`, not `["WT012", "WT010"]`.

- [x] **Step 3: Fix it.** In `scripts/dev/_worktree_guard_lineage.py`, `classify_lineage`,
  the WT012 branch currently returns a one-element list built from a single `issue(...)`
  call immediately. Change it to build that same list under a name (`issues = [...]`),
  append `_dirty(snapshot)` to it when `snapshot.dirty` is true, and `return issues` --
  exactly the pattern the non-detached path below it already uses for the same check. Leave
  the WT011 (`recognized_ci`) branch unchanged: a recognized CI checkout is not the "local
  work in progress" state WT010 exists to flag, and the finding names the detached *local*
  case specifically.

- [x] **Step 4: Run to verify it passes.**

  Run: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe" tests/scripts/dev/test_worktree_guard.py -q`
  Expected: PASS, including the existing `test_detached_ci_skips_and_detached_local_fails`
  (unaffected: it does not set `dirty=True`).

**Bug 2: the doubled base-ref label.** See FINDINGS.md F-WORKTREE-3. `missing_base_diagnostic`
passes the already-labelled `label` into `missing_base_remediation`, which then branches
against that pre-labelled value instead of the real ref -- an unsafe ref labels to the
literal `"configured base ref"` (no `/`), so it always falls into the "local ref" branch
regardless of the real ref's shape, and that branch's template substitutes the same
pre-labelled string again, rendering "the local base ref configured base ref exists and is
current".

- [x] **Step 5: Write the failing test.** In `tests/scripts/dev/test_worktree_guard_base_ref.py`,
  extend the `test_missing_base_remediation_matches_selected_ref` parametrize table with a
  case whose ref is display-unsafe (so `base_ref_label` substitutes it) *and* contains a
  `/` (so the branch-decision bug is observable, not just the label text):

  ```python
  @pytest.mark.parametrize(
      ("base_ref", "remediation"),
      [
          (
              "upstream/trunk",
              "Refresh or otherwise verify the selected base ref upstream/trunk exists "
              "locally and is current, then rerun the guard. This guard does not fetch.",
          ),
          (
              "main",
              "Verify the local base ref main exists and is current, then rerun the "
              "guard. This guard does not fetch.",
          ),
          (
              "origin/bad ref",
              "Refresh or otherwise verify the selected base ref configured base ref "
              "exists locally and is current, then rerun the guard. This guard does "
              "not fetch.",
          ),
      ],
      ids=("custom-remote", "local-ref", "unsafe-remote-like"),
  )
  def test_missing_base_remediation_matches_selected_ref(tmp_path, base_ref, remediation):
      """Missing custom and local bases never prescribe the origin remote, and
      an unsafe ref never doubles 'base ref' into its own remediation text
      (F-WORKTREE-3)."""
      repo, responses = repository(tmp_path, base_ref=base_ref)
      responses[("rev-parse", "--verify", f"{base_ref}^{{commit}}")] = fail()
      diagnostics = inspect_worktree(repo, base_ref=base_ref, runner=FakeGit(responses))
      assert codes(diagnostics) == ["WT007"]
      assert diagnostics[0].remediation == remediation
  ```

  `"origin/bad ref"` contains a space, so `is_display_safe_ref` refuses it and
  `base_ref_label` substitutes `"configured base ref"`; it also contains a `/`, so the
  *correct* branch is the "custom remote" one (`"Refresh or otherwise verify the selected
  base ref ..."`), not the "local ref" one -- today's bug picks the wrong branch and the
  message reads "Verify the local base ref configured base ref exists...".

- [x] **Step 6: Run to verify it fails.**

  Run: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe" tests/scripts/dev/test_worktree_guard_base_ref.py -q -k unsafe_remote_like`
  Expected: FAIL -- today's message is the doubled, wrong-branch text.

- [x] **Step 7: Fix it.** In `scripts/dev/_worktree_guard_diagnostics.py`,
  `missing_base_remediation(base_ref: str) -> str` keeps its signature and its three-way
  branch (`origin/main`; no `/` or starts with `refs/`, "local ref" phrasing; otherwise
  "custom remote" phrasing) unchanged in shape, but every branch decision and every
  `f"..."` substitution that currently reads the *parameter* `base_ref` after it has been
  reassigned to `base_ref_label(base_ref)` must instead read the real `base_ref` for the
  branch decision, computing `label = base_ref_label(base_ref)` only at the point each
  branch's message text substitutes it -- so the branch is chosen from the real ref (whose
  `/` the label may have stripped) and only the rendered text uses the label. In
  `missing_base_diagnostic`, the only change is that its call to `missing_base_remediation`
  now passes the raw `base_ref` instead of the already-computed `label` (the diagnostic's
  own `subject` field keeps using `label`, unchanged).

- [x] **Step 8: Run to verify it passes.**

  Run: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe" tests/scripts/dev/test_worktree_guard_base_ref.py -q`
  Expected: PASS, all three cases, including the two pre-existing ones (both display-safe
  refs, where `label == base_ref`, so this change is a no-op for them -- confirming no
  regression).

- [x] **Step 9: Full worktree-guard corpus, gates and live probe.**

  ```
  "C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe" tests/scripts/dev/test_worktree_guard*.py -q
  ```

  Live probe, per the verification standard, using
  `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe"
  scripts/dev/check_worktree_alignment.py --advisory` directly in `/c/ssprobe/corpus`
  (this check has no docsync preflight involvement, so the probe runs the real CLI entry
  point rather than `doc_state_sync.py`):
  - **Red (WT010/detached):** `git checkout --detach HEAD` plus an unstaged edit, pre-fix
    tree (`base`) -> WT012 only.
  - **Green:** same state, this task's tree -> both WT012 and WT010.
  - **Near-miss green:** detached, clean (no edits) -> WT012 alone, still no WT010.
  - **Red (base-ref label):** `--base-ref "bad ref/with space"` against a repo with no such
    ref, pre-fix tree -> the doubled "local base ref configured base ref" text.
  - **Green:** same invocation, this task's tree -> "Refresh or otherwise verify the
    selected base ref configured base ref exists locally..." (correct branch, single
    mention of the placeholder).

- [x] **Step 10: Resolve F-WORKTREE-3 and commit.** Reason: "WT010 now fires for a
  detached, dirty, local (non-CI) worktree (`classify_lineage`,
  `scripts/dev/_worktree_guard_lineage.py`); `missing_base_remediation` now branches on the
  raw base ref instead of an already-labelled placeholder, so an unsafe ref's remediation
  text names the placeholder once, in the correct branch
  (`scripts/dev/_worktree_guard_diagnostics.py`). The between-batch ancestry skip remains
  the owner's 2026-09-23 accepted design boundary." This finding is now fully resolved (3
  of 3 items accounted for).

  ```bash
  git add scripts/dev/_worktree_guard_lineage.py scripts/dev/_worktree_guard_diagnostics.py tests/scripts/dev/test_worktree_guard.py tests/scripts/dev/test_worktree_guard_base_ref.py FINDINGS.md docs/history/findings/FINDINGS_ARCHIVE.md docs/agents/PLAYBOOK.md
  git commit -m "fix(worktree-guard): Fire WT010 when detached and fix the doubled base-ref label"
  ```

**Acceptance:** a detached, dirty, non-CI worktree reports both WT012 and WT010; a
detached, dirty, recognized-CI worktree still reports WT011 alone; an unsafe base ref's
WT007 remediation names the placeholder once, in the branch its real ref value deserves;
both existing safe-ref cases are unchanged; F-WORKTREE-3 is fully resolved.

---

### Task 6: Stage named paths before `pre-commit run --all-files` (F-B21-20, Q5 = a)

**Files:**
- Modify: `AGENTS.md` ("Commit Rules" > "Procedure before every commit")
- Test: none (a documented procedure, not code); verified by the live probe only

**F-B21-20's bug, precisely.** `AGENTS.md`'s numbered commit procedure runs `pre-commit
run --all-files` (step 4) before "Stage specific paths by name" (step 6). The
`tailwind-css-drift` hook rebuilds `static/css/tailwind.css` from source and then runs
`git diff --exit-code` *against the index*. When staging has not happened yet, the index
still holds the previously-committed bytes, so any legitimate, correctly rebuilt CSS change
reads as drift and the hook fails for the same reason a genuinely stale build would --
there is no way to tell the two apart from inside step 4, because nothing has been staged
for the hook to compare against yet.

- [ ] **Step 1: Reorder the procedure, starting from the list as Task 1 left it.** Task 1
  already swapped `--fix` and `pytest -q` and added `--test-count N`, so the numbered list
  reads: `1` PLAYBOOK, `2` `pytest -q`, `3` `--fix --test-count N` (bare `--fix` when the
  count is unchanged), `4` `pre-commit run --all-files`, `5` `--check`, `6` Stage specific
  paths by name, `7` Commit after each WP. In `AGENTS.md`, "Commit Rules" > "Procedure
  before every commit", swap steps 4 and 6 so staging happens before `pre-commit run
  --all-files`, producing: `1` PLAYBOOK, `2` `pytest -q`, `3` `--fix --test-count N`, `4`
  Stage specific paths by name (**Never `git add -A` or `git add .`** -- the prohibition is
  on the command, since it silently picks up whatever else is in the tree, even when every
  changed file belongs to this WP; stage `.claude/SESSION_CONTEXT.md` together with
  PLAYBOOK whenever it changed; staging now, before `pre-commit run --all-files`, is
  required: the `tailwind-css-drift` hook rebuilds the compiled stylesheet and diffs it
  against the index, so an unstaged source edit always reads as drift whether or not the
  rebuild is correct, F-B21-20), `5` `pre-commit run --all-files` (a hook that rewrites a
  file, for example `tailwind-css-drift` itself or an auto-formatter, leaves the working
  tree ahead of the index again; re-stage the paths it touched before the next step), `6`
  `--check` -- exits 0 on the final state (the root `BATCHN_DEFINITION.md` warning is
  expected while a batch is active), `7` Commit after each WP.

  Preserve every other sentence in the block verbatim (the standing exception about
  review-fix commits, the co-author prohibition reference, etc. -- confirm nothing else in
  the surrounding prose cites a step by number and needs repointing; grep `AGENTS.md` for
  "step 4", "step 6" or similar numeric citations first). If Task 1 has not landed yet when
  this task is implemented, apply both reorders in one pass instead and say so in the commit
  body.

- [ ] **Step 2: Grep for stale numeric citations elsewhere.**

  ```bash
  git grep -n "step 4\|step 6\|procedure.*step" -- '*.md' ':!docs/history' ':!docs/logarchive'
  ```

  Correct any live document citing the old step numbers by name of the step (its verb),
  not by number, so a future reorder cannot silently strand the citation again.

- [ ] **Step 3: Live probe against the real hook.** Per the verification standard, in
  `/c/ssprobe/corpus`:
  - **Red (old order):** make a legitimate source edit to `static/css/tailwind.src.css`
    (one token value change) and rebuild `static/css/tailwind.css` from it by running
    `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe"
    scripts/dev/tailwind_build.py` (bare invocation rebuilds; this repository has no
    `package.json` and no Node tooling, per `docs/agents/global-rules.md` and F-B21-18), but
    do **not** stage either file. Run:
    ```
    "C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pre-commit.exe" run tailwind-css-drift --files static/css/tailwind.src.css static/css/tailwind.css
    ```
    Expected: FAIL -- the freshly rebuilt file differs from the still-unstaged index.
  - **Green (new order):** same corpus state, `git add static/css/tailwind.src.css
    static/css/tailwind.css`, then run the same `pre-commit run tailwind-css-drift`
    command. Expected: PASS.
  - **Near-miss green:** a genuinely stale build (edit the source, do not rebuild, stage
    both anyway) -> hook still correctly FAILS: staging order removes only the false
    failure, not a real drift defect.
  - Reset the probe corpus between each (`git reset -q --hard base && git clean -qfd`).

- [ ] **Step 4: Section 4 entry and commit.** This task touches only `AGENTS.md`; no R7
  concern.

  ```bash
  "C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe" scripts/doc_state_sync.py --fix
  "C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe" -q --ignore=tests/scripts/dev/test_mutation_test.py -p no:cacheprovider
  git add AGENTS.md
  "C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pre-commit.exe" run --all-files
  "C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe" scripts/doc_state_sync.py --check
  ```

- [ ] **Step 5: Resolve F-B21-20 and commit.** Reason: "`AGENTS.md`'s commit procedure now
  stages named paths (step 4) before `pre-commit run --all-files` (step 5), so the
  `tailwind-css-drift` hook's index comparison sees the change being committed instead of
  the prior commit's bytes (Q5 = a)."

  ```bash
  git commit -m "docs(agents): Stage before running pre-commit in the commit procedure"
  ```

**Acceptance:** the live probe shows a correct CSS rebuild passing `tailwind-css-drift`
under the new order and failing under the old one, with a genuinely stale build still
correctly failing either way; no other document cites the old step numbers.

---

### Task 7: Bootstrap fast-paths move below the list; `skills-lock.json` gets a warn-only manifest (F-B21-25 items 1-2, Q15 = a)

**Files:**
- Modify: `AGENTS.md` ("Session Bootstrap (in order)")
- Modify: `scripts/docsync/declarations.py` (a new `UntrackedEssentialsConfig`,
  `_validate_untracked_essentials`, `_untracked_essentials_config`,
  `load_untracked_essentials_config`)
- Modify: `config/docsync.toml` (a new `[untracked_essentials]` table)
- Create: `scripts/dev/_worktree_guard_essentials.py`
- Modify: `scripts/dev/_worktree_guard_inspection.py` (`inspect_worktree` -- wire the new
  check in)
- Modify: `scripts/dev/worktree_guard.py` (re-export `essentials_diagnostics`)
- Test: `tests/test_docsync_declarations.py`, a new
  `tests/scripts/dev/test_worktree_guard_essentials.py`, and
  `tests/scripts/dev/test_worktree_guard_inspection.py` (wiring)

**Interfaces:**
- Produces: `declarations.UntrackedEssentialsConfig` (field `paths: tuple[str, ...] = ()`),
  `declarations.load_untracked_essentials_config(repo_root, *, config_path=None) ->
  UntrackedEssentialsConfig`. Third table of this shape in `declarations.py`
  (`ArchiveConfig`, Task 1's `TestCountConfig`, now this one) -- Rule 3 is satisfied by
  naming the shared scaffold once (Mapping check, unknown-key check, `_config`/`load_config`
  wrapper pair) rather than building a fourth abstraction for it: the three tables' fields
  differ enough in kind (two required ints, one optional int, one optional string list)
  that a shared validator would be indirection for its own sake.
- Produces: `_worktree_guard_essentials.essentials_diagnostics(repo_root: Path) ->
  list[Diagnostic]`. One `WT015` `WARNING` per declared path that does not exist. `WT015`
  is the next free code (`WT000`-`WT014` are all in use today).

**Part A: move the two fast-path paragraphs.** In `AGENTS.md`, "Session Bootstrap (in
order)" currently opens with "**Fast-path for Copilot comment jobs:** ..." and "**Fast-path
for targeted review-comment jobs:** ..." *above* the numbered bootstrap list (items 1-8).
F-B21-25's finding: "a skim finds the exemption before the obligation." Q15's fix: move
both paragraphs below the numbered list.

- [ ] **Step 1: Move the two paragraphs.** In `AGENTS.md`, cut both fast-path paragraphs
  (from `**Fast-path for Copilot comment jobs:**` through the end of `**Fast-path for
  targeted review-comment jobs:**`'s paragraph) from their current position immediately
  above item `1. AGENTS.md (this file) -- rules, ...` and paste them immediately after item
  `8. docs/agents/FINDINGS.md -- read on demand only: ...` and before the "This is the
  single canonical bootstrap order ..." paragraph that currently follows the list. Do not
  change either paragraph's wording -- this is a placement fix only, per Q15's scope
  ("MINUS the findings/issues sync" and nothing else added).

- [ ] **Step 2: Grep for anything that assumed the old position.**

  ```bash
  git grep -n "Fast-path" -- '*.md' ':!docs/history' ':!docs/logarchive'
  ```

  Confirm no other document describes the fast-paths as "at the top of Session Bootstrap"
  or similar; correct any such phrasing found.

**Part B: the `skills-lock.json` warn-only manifest.**

- [ ] **Step 3: Write the failing declarations test.** Append to
  `tests/test_docsync_declarations.py`:

  ```python
  class TestUntrackedEssentialsConfig:
      def test_absent_table_returns_an_empty_tuple(self, tmp_path: Path):
          from docsync.declarations import (
              UntrackedEssentialsConfig,
              load_untracked_essentials_config,
          )

          assert load_untracked_essentials_config(tmp_path) == UntrackedEssentialsConfig()
          assert UntrackedEssentialsConfig().paths == ()

      def test_declared_paths_are_read(self, tmp_path: Path):
          from docsync.declarations import load_untracked_essentials_config

          path = tmp_path / DECLARATIONS_FILENAME
          path.parent.mkdir(parents=True, exist_ok=True)
          path.write_text(
              '[untracked_essentials]\npaths = ["skills-lock.json"]\n', encoding="utf-8"
          )
          config = load_untracked_essentials_config(tmp_path)
          assert config.paths == ("skills-lock.json",)

      def test_a_non_string_entry_is_refused(self, tmp_path: Path):
          from docsync.declarations import DeclarationError, load_untracked_essentials_config

          path = tmp_path / DECLARATIONS_FILENAME
          path.parent.mkdir(parents=True, exist_ok=True)
          path.write_text(
              "[untracked_essentials]\npaths = [1]\n", encoding="utf-8"
          )
          with pytest.raises(DeclarationError):
              load_untracked_essentials_config(tmp_path)

      def test_an_unknown_key_is_refused(self, tmp_path: Path):
          from docsync.declarations import DeclarationError, load_untracked_essentials_config

          path = tmp_path / DECLARATIONS_FILENAME
          path.parent.mkdir(parents=True, exist_ok=True)
          path.write_text(
              '[untracked_essentials]\nfiles = ["x"]\n', encoding="utf-8"
          )
          with pytest.raises(DeclarationError, match="unknown key 'files'"):
              load_untracked_essentials_config(tmp_path)
  ```

- [ ] **Step 4: Run to verify it fails.**

  Run: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe" tests/test_docsync_declarations.py -q -k UntrackedEssentialsConfig`
  Expected: `ImportError`.

- [ ] **Step 5: Implement `UntrackedEssentialsConfig` in `declarations.py`,** mirroring
  `ArchiveConfig` / `_validate_archives` / `_archive_config` / `load_archive_config`
  (`declarations.py:328,364,393,407`) and Task 1's `TestCountConfig` field for field: a
  frozen dataclass with one field (`paths: tuple[str, ...] = ()`), a
  `_validate_untracked_essentials(table: object) -> UntrackedEssentialsConfig` that rejects
  an unknown key and validates `paths` with the existing `_mismatch(_ListOf(str), paths)`,
  an `_untracked_essentials_config(declarations: Mapping) -> UntrackedEssentialsConfig` that
  returns the default when `"untracked_essentials"` is absent, and
  `load_untracked_essentials_config(repo_root, *, config_path=None) ->
  UntrackedEssentialsConfig` calling `load_declarations` then that mapper. Add
  `"untracked_essentials": {"required": {}, "optional": {"paths": _ListOf(str)}}` to the
  `_TOP_LEVEL_SCHEMA` dict literal. `_ListOf` and `_mismatch` already exist in
  `declarations.py`; reuse them, do not redefine.

- [ ] **Step 6: Run to verify it passes.**

  Run: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe" tests/test_docsync_declarations.py -q -k UntrackedEssentialsConfig`
  Expected: PASS.

- [ ] **Step 7: Declare `skills-lock.json` in `config/docsync.toml`.** Add, after the
  `[documents]` table:

  ```toml
  # ----------------------------------------------------------------------
  # Untracked-essential files
  # ----------------------------------------------------------------------

  # Gitignored files the workflow depends on but Git cannot protect
  # (F-B21-25 item 3 of its causes: "what was lost was gitignored"). WARNING
  # only -- the worktree guard cannot create or fetch a missing one, it can
  # only tell the reader it is gone.
  [untracked_essentials]
  paths = ["skills-lock.json"]
  ```

- [ ] **Step 8: Write the failing worktree-guard test.** Create
  `tests/scripts/dev/test_worktree_guard_essentials.py`:

  ```python
  """Behavior tests for the untracked-essentials WARNING check (F-B21-25)."""

  from pathlib import Path

  from scripts.dev._worktree_guard_essentials import essentials_diagnostics


  def test_a_missing_declared_path_warns(tmp_path: Path):
      (tmp_path / "config").mkdir()
      (tmp_path / "config" / "docsync.toml").write_text(
          '[untracked_essentials]\npaths = ["skills-lock.json"]\n', encoding="utf-8"
      )
      diagnostics = essentials_diagnostics(tmp_path)
      assert [(d.code, d.severity) for d in diagnostics] == [("WT015", "WARNING")]
      assert diagnostics[0].subject == "skills-lock.json"


  def test_a_present_declared_path_is_silent(tmp_path: Path):
      (tmp_path / "config").mkdir()
      (tmp_path / "config" / "docsync.toml").write_text(
          '[untracked_essentials]\npaths = ["skills-lock.json"]\n', encoding="utf-8"
      )
      (tmp_path / "skills-lock.json").write_text("{}", encoding="utf-8")
      assert essentials_diagnostics(tmp_path) == []


  def test_no_declaration_is_silent(tmp_path: Path):
      assert essentials_diagnostics(tmp_path) == []
  ```

- [ ] **Step 9: Run to verify it fails.**

  Run: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe" tests/scripts/dev/test_worktree_guard_essentials.py -q`
  Expected: `ImportError` -- the module does not exist yet.

- [ ] **Step 10: Implement `essentials_diagnostics`.** Create
  `scripts/dev/_worktree_guard_essentials.py`, importing `issue` from
  `scripts.dev._worktree_guard_diagnostics`, `Diagnostic` from
  `scripts.dev._worktree_guard_types`, and `load_untracked_essentials_config` from
  `scripts.docsync.declarations`. `essentials_diagnostics(repo_root: Path) ->
  list[Diagnostic]`: load the config, and for each declared path not present as a file
  under `repo_root`, append `issue("WARNING", "WT015", relative, "declared
  untracked-essential file is missing.", "Restore it or ask the owner where its current
  copy lives; this guard does not create or fetch it.")`. Docstring: these files are
  gitignored by design (F-B21-25), so no gate before this one even looks; WARNING only,
  since this guard cannot restore a missing one either.

- [ ] **Step 11: Run to verify it passes.**

  Run: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe" tests/scripts/dev/test_worktree_guard_essentials.py -q`
  Expected: PASS.

- [ ] **Step 12: Wire it into `inspect_worktree`.** In
  `scripts/dev/_worktree_guard_inspection.py`, import `essentials_diagnostics` from
  `scripts.dev._worktree_guard_essentials`, and after the existing
  `diagnostics.extend(venv_diagnostics)` line, add:

  ```python
      diagnostics.extend(essentials_diagnostics(resolved_root))
  ```

  (`resolved_root` is already in scope at that point, per the surrounding code building
  `venv, venv_diagnostics = resolve_venv(repo_root=resolved_root, ...)`.) In
  `scripts/dev/worktree_guard.py`, add `essentials_diagnostics` to the import from
  `scripts.dev._worktree_guard_essentials` and to `__all__`, alphabetically.

- [ ] **Step 13: Write the failing wiring test.** In
  `tests/scripts/dev/test_worktree_guard_inspection.py`, add a case (using whatever fixture
  helper the file already builds a repo with, per its existing parametrize table -- the
  one already covering `("wip/batch-21", "0\t0\n", "?? notes.txt\n", ["WT010", "WT000"])`)
  where `config/docsync.toml` declares an untracked-essential path that the fixture
  repository does not create, and asserts `WT015` appears in the returned codes.

- [ ] **Step 14: Run the full worktree-guard corpus.**

  ```
  "C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe" tests/scripts/dev/test_worktree_guard*.py -q
  ```

- [ ] **Step 15: Gates and live probe.** This task stages `config/docsync.toml` and
  `scripts/docsync/declarations.py` (R7 applies to the whole commit, even though the
  worktree-guard files alone would not trigger it).

  ```
  "C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe" scripts/doc_state_sync.py --check
  ```

  Live probe, per the verification standard, using
  `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe"
  scripts/dev/check_worktree_alignment.py --advisory` in `/c/ssprobe/corpus`:
  - **Red:** no `skills-lock.json` (a fresh `git archive` checkout has no gitignored files
    by default) -> `WARNING WT015 skills-lock.json -- declared untracked-essential file is
    missing.` prints, exit 0 (confirm 0 without `--advisory` too: WARNING severity never
    blocks, per `main()`'s `any(d.severity == "ERROR" ...)` check).
  - **Green (near-miss):** create an empty `skills-lock.json` in the probe corpus root;
    re-run; confirm WT015 no longer prints.

- [ ] **Step 16: Update `AGENTS.md`'s note about the manifest, if F-B21-25's own prose in
  `AGENTS.md` needs it.** Check whether `AGENTS.md` currently says anything about
  `skills-lock.json` being unprotected; if so, add one sentence pointing to the new
  `config/docsync.toml` `[untracked_essentials]` table and the `WT015` warning, per the
  Anti-duplication rule (link, do not restate the mechanism).

- [ ] **Step 17: Record the partial progress on F-B21-25 and commit.** F-B21-25 is not
  fully resolved by this task (the remaining "origin narrative" `AGENTS.md` defect and any
  other open items stay open); add a dated note under its existing entry, per the pattern
  the reconcile plan's Task 12 used for F-DOCSYNC-6/F-WORKTREE-3's partial rulings:

  ```
  **2026-09-25 (control-plane plan).** Items 1-2 are done: the two fast-path paragraphs
  moved below the numbered bootstrap list, and `skills-lock.json` is declared in
  `config/docsync.toml` `[untracked_essentials]`, warned about (WT015) by
  `scripts/dev/_worktree_guard_essentials.py` when missing. The findings/issues sync
  (item 2's other half) is not built: findings are not mirrored to GitHub (owner ruling,
  2026-09-25). The remaining AGENTS.md origin-narrative defect stays open.
  ```

  Keep the `Status:` line as `partly closed` (unchanged).

  ```bash
  git add AGENTS.md scripts/docsync/declarations.py config/docsync.toml scripts/dev/_worktree_guard_essentials.py scripts/dev/_worktree_guard_inspection.py scripts/dev/worktree_guard.py tests/test_docsync_declarations.py tests/scripts/dev/test_worktree_guard_essentials.py tests/scripts/dev/test_worktree_guard_inspection.py FINDINGS.md docs/agents/PLAYBOOK.md
  SKIP=doc-state-sync-check git commit -m "feat(worktree-guard): Warn on a missing skills-lock.json and reorder bootstrap fast-paths"
  ```

**Acceptance:** the two fast-path paragraphs sit below the numbered bootstrap list; a
missing declared untracked-essential file prints `WT015` at WARNING severity and never
blocks; a present one is silent; F-B21-25 gains a dated note recording items 1-2 done and
stays `partly closed`.

---

### Task 8: A pin-only `config/docsync.toml` change is not control-plane (owner ruling 2026-09-26)

Ran before Task 5, since the plan had no Task 8 text until it landed. Task 1 (`8f56c17`)
put the test-count pin in `config/docsync.toml` `[test_count]`; because the preflight's
`CONTROL_PLANE_FILES` also lists that file, every ordinary commit that adds a test staged a
"control-plane" file and was refused, forcing `SKIP=` on routine commits. Owner ruling: keep
the pin in `config/docsync.toml`, change the preflight so a staged `config/docsync.toml`
counts as control-plane only when something outside `[test_count]` changed.

**Files:** `scripts/dev/docsync_preflight.py` (`staged_control_plane_paths`, a new
`_docsync_toml_pin_only_change` helper); `tests/scripts/dev/test_docsync_preflight.py`;
`AGENTS.md`, `docs/architecture/documentation-tooling.md` (prose); this plan.

- [x] Step 1: Failing tests for the seven cases (pin-only, pin plus another table, another
      table only, table added where HEAD had none, absent at HEAD, invalid index TOML,
      pin-only alongside a real control-plane file).
- [x] Step 2: Implement per Design (fail closed on any ambiguous case).
- [x] Step 3: Green -- the preflight test file, then the full suite.
- [x] Step 4: Mutation proof (L14) in a scratch copy.
- [x] Step 5: Live probe in an independent clone -- Red/Green/near-miss.
- [x] Step 6: Prose in `AGENTS.md` and `documentation-tooling.md`; swept sibling claims.
- [x] Step 7: This section and the owner-rulings bullet.
- [x] Step 8: Commit.

**Acceptance:** a commit whose only control-plane change is the `[test_count]` pin passes
`doc-state-sync-check` without `SKIP=`; any other `config/docsync.toml` change, and every
other control-plane path, is still refused; every ambiguous case fails closed.

---

## Self-Review

**Spec coverage.** Every finding named in the dispatch has a task: F-DOCSYNC-11/-12/-13/-22
(Task 1), F-DOCSYNC-7/F-MAS-3 (Task 2), F-DOCSYNC-15 (Task 3), F-DOCSYNC-6 with the
outside-root item confirmed already fixed (Task 4), F-WORKTREE-3's two bugs (Task 5),
F-B21-20 (Task 6), F-B21-25 items 1-2 with the findings/issues sync excluded (Task 7). The
"After this plan" bullet's own order is preserved.

**Placeholder scan.** No step says "add tests" without the test body; no step says "update
references" without naming the grep and the expected hits.

**Type consistency.** `resolved_test_count_authority` and `rewrite_recorded_counts` (Task 1)
are each used unchanged by every later caller named in this plan. `_collect_wp_numbers`'s
signature is unchanged across Task 3; only its body's rule changes.
`_batch_filename_candidates` (Task 4) and `essentials_diagnostics` (Task 7) are each defined
once and used once.

## Definition of Done

Tasks 1-7 each meet their own acceptance. `pytest -q`, `pre-commit run --all-files` and
`doc_state_sync.py --check` all pass on the final tree. `docs/agents/PLAYBOOK.md` Section 4
carries one dated, untagged entry per task, each with its live-probe table where the task
has one. F-DOCSYNC-11, -12, -13, -22, -7, -6, -15, F-MAS-3 and F-WORKTREE-3 are fully
resolved; F-B21-20 is fully resolved; F-B21-25 carries a dated note and stays `partly
closed`. This is item 1 of the reconcile plan's "After this plan"; the frontend plan and
the test-infrastructure plan follow, per that plan's stated order.

## Controller-only checklist (outside this repository's git tracking, or owner-only)

1. **`skills-lock.json` in the owner's real checkouts.** Once Task 7 lands, `WT015` warns on
   any machine with no `skills-lock.json`; expected on a fresh clone, not a defect here.
2. **`~/.claude` memory files** describing the old commit-procedure step numbers (Task 6) or
   the old STATUS-block pinning behaviour (Task 1): update once this plan lands.
3. **A cloud-kit `constraints.md` copy**, if one exists for this plan's execution: its R7/R10
   text should already match this plan's Global Constraints verbatim; no change needed
   unless a future edit here is not mirrored there.
4. **Whether WT010 should also fire on a detached, dirty, recognized-CI checkout** (Task 5
   scopes the fix to the local/WT012 case only, per Q2's ruling, (a)). Settled; no follow-up.
