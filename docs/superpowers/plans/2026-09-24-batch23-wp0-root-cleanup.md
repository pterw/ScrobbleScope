# Batch 23 WP-0 Part B: root cleanup (document and config relocation)

**Status: DRAFT, not approved for execution (2026-09-24).** Drafted from
`docs/history/reports/ROOT_CLEANUP_INVENTORY_2026-09-24.md` and reviewed
once. Before Task 1 runs, apply every item in "Revisions pending" at the end
of this file, have the revised plan reviewed again, delete this status
paragraph and the "Revisions pending" section, and only then execute. The
task bodies below are still the unrevised draft.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move `PLAYBOOK.md`, `FINDINGS.md`, `AGENT_NOTES.md`, `HANDOFF_PROMPT.md` from the
repository root to `docs/agents/`, and `.docsync.toml` / `frontend_gate_checks.toml` to
`config/docsync.toml` / `config/frontend_gate_checks.toml`, without a gate going red at any
committed point, and make docsync's own document paths a declared fact instead of a
hard-coded Python literal (`AGENT_NOTES.md` "This repository is also a template being
extracted").

**Architecture:** Three independent clusters, sequenced by blast radius (inventory Section 7,
row 7): the `[documents]` declaration mechanism and the `--config` override land first, as
pure additions with no file movement and no default-value change, so they carry zero risk to
today's corpus; the two `.toml` moves land next, one per commit, each pairing its `git mv`
with the one constant that resolves it; the four `.md` moves land last, in one commit, because
DOC001 cannot pass with the move half-done (inventory Section 7, row 4) -- the file move, the
worktree guard fix, the `[retired.allow_after]` fix, the two behavioural path comparisons in
`scripts/docsync/integrity.py`, and the citation sweep across every always-scanned live
document all have to land together or the tree sits red between commits, which Global
Constraints forbid.

**Tech Stack:** Python 3.13 stdlib (`tomllib`, `pathlib`, `dataclasses`), pytest. No new
dependency.

## Global Constraints

Reused from `docs/superpowers/plans/2026-09-21-batch23-wp0-foundation.md` "Global
Constraints", unchanged, plus one addition:

- **Qualified interpreter only.** `C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe`
  and its sibling `pytest.exe` / `pre-commit.exe`. Never bare `pip`, never a second venv.
- **No new dependency, no version change.**
- **Nothing may break the repository.** No task may leave `pytest -q` red,
  `doc_state_sync.py --check` non-zero, `pre-commit run --all-files` failing, or the frontend
  gate failing.
- **No existing test is modified, except where a task says so and says why.**
- **Do not touch other agents' uncommitted work.** `git status --short` lists the untracked
  set at the time this plan was drafted (`.github/skills/`, `.graphifyignore`,
  `docs/2026-09-14-open-code-review-audit.md`, the two architecture-review HTML/report files,
  `docs/superpowers/handoffs/scrobblescope-handoff-2026-09-23-after-task7.md`,
  `docs/superpowers/plans/architecture-review-*.html`, `docs/superpowers/plans/plan.md`,
  `progress_copy.md`, `scripts/dev/mutation_scope.toml`, `scripts/dev/mutation_test.py`,
  `tests/scripts/dev/test_mutation_test.py`). Never stage, revert or delete them. Re-run
  `git status --short` before Task 1 and treat any new untracked entry the same way.
- **Commit procedure, in this order** (`AGENTS.md` "Commit Rules"): the dated `PLAYBOOK.md`
  Section 4 entry; `doc_state_sync.py --fix`; `pytest -q`; `pre-commit run --all-files`;
  `doc_state_sync.py --check`.
- **A commit that changes the docsync control plane is refused by design.** Any task touching
  `scripts/docsync/`, `scripts/doc_state_sync.py`, `scripts/dev/docsync_preflight.py`, or the
  declarations file (`.docsync.toml` today, `config/docsync.toml` from Task 5 on) exits 3 at
  the preflight. Run `doc_state_sync.py --check` directly at exit 0 first, then commit with
  `SKIP=doc-state-sync-check git commit ...`. Never `--no-verify`.
- **Commit discipline:** Conventional Commits, imperative, no trailing period, subject max 72
  chars. Stage paths by name; `git add -A` and `git add .` are forbidden. No `Co-authored-by`
  or other attribution trailer (`AGENTS.md` "Commit Rules").
- **Quote a measured count.** A Section 4 entry that claims a suite result writes it as
  `` `pytest -q` -- **N passed** ``, re-measured, never copied.
- **`AGENTS.md` stays under 500 lines.** Every edit to it is a replacement or a pointer.
- **ASCII only**: no smart quotes, no em dash -- use `--`.
- **Use `git mv`** for every relocation in this plan, never delete-then-recreate, so
  `git log --follow` and blame survive (inventory Section 7, row 5).

## The verification standard for control-plane tasks

Reused verbatim from the foundation plan. A failing green is worse than a red; a unit test
over an invented fixture is not proof a gate works. Every task in this plan that changes a
check or a path resolver (Tasks 2, 3, 4, 5, 6) is accepted only on a **live probe**:

1. Build a throwaway corpus from the committed tree, at a short path:
   ```bash
   mkdir -p /c/ssprobe && cd /c/ssprobe && rm -rf corpus && mkdir corpus
   git -C "<worktree>" archive HEAD | tar -x -C corpus
   cd corpus && git init -q && git config core.longpaths true && git add -A
   git -c user.email=p@l -c user.name=p commit -qm base && git tag base
   ```
2. Confirm the copy is faithful: `--check` there prints the same summary as in the worktree.
3. **Red:** plant the defect the task targets and run the real CLI. The expected code must
   print and the exit must be nonzero (or zero for a warning-severity code, with the warning
   printed).
4. **Near-miss green:** plant the closest *valid* variant and confirm silence.
5. Reset with `git reset -q --hard base && git clean -qfd` between probes.
6. Paste the probe table (probe, expected, exit, codes) into the task report and the Section 4
   entry. Delete `/c/ssprobe` afterwards.

A task's own unit tests are written first, as the regression guard; the probe is the proof.

## File Structure

| File | Change |
|---|---|
| `scripts/docsync/declarations.py` | New `DocumentsConfig` dataclass, `_validate_documents`, `_documents_config`, `load_documents_config`; `load_declarations` and every `load_*_config` gain an optional `config_path` kwarg; `DECLARATIONS_FILENAME` value changes in Task 5. |
| `scripts/docsync/integrity.py` | `collect_integrity_issues` gains three optional kwargs (`document_paths`, `playbook_relative_path`, `findings_relative_path`), all defaulting to today's literals; new `resolved_live_document_paths(documents)` helper. |
| `scripts/docsync/cli.py` | New `--config` argument; new `CONFIG_PATH` computed once in `main()`; the five `load_archive_config`/`load_closeout_config` call sites and the two `collect_integrity_issues` call sites gain the new kwargs; `_read_live_documents` resolves paths through `load_documents_config`. |
| `scripts/dev/docsync_preflight.py` | `CONTROL_PLANE_FILES` entry changes from `.docsync.toml` to `config/docsync.toml` (Task 5). |
| `scripts/dev/frontend_gate.py` | `CHECK_MANIFEST_PATH` and its two error strings move to `config/` (Task 4). |
| `scripts/dev/_worktree_guard_inspection.py` | The `PLAYBOOK.md` read moves to `docs/agents/PLAYBOOK.md` (Task 6). |
| `config/docsync.toml`, `config/frontend_gate_checks.toml` | New locations (`git mv`, Tasks 4-5); `config/docsync.toml` gains a `[documents]` table (Task 6). |
| `docs/agents/PLAYBOOK.md`, `FINDINGS.md`, `AGENT_NOTES.md`, `HANDOFF_PROMPT.md` | New locations (`git mv`, Task 6). |
| Every always-scanned live document, plus `DEVELOPMENT.md`, `docs/AGENT_DOC_MAP.md`, `docs/agents/domain.md`, `docs/agents/global-rules.md`, `docs/agents/issue-tracker.md`, `.superpowers/cloud-kit/constraints.md`, `PRODUCT.md`, `docs/ARCHITECTURE.md`, `docs/architecture/*.md`, `docs/design/RECONCILIATION.md` | Citations repointed (Task 6). |

---

### Task 1: Record the scope change before touching anything

**Proposal Rule 1** (`AGENTS.md`): scope changes to an open batch are recorded before
execution. Part B of `BATCH23_DEFINITION.md` WP-0 does not yet list the root cleanup; add it.

**Files:**
- Modify: `BATCH23_DEFINITION.md` (Part B, `#### Part B -- Reconcile what earlier batches left
  open`)
- Modify: `PLAYBOOK.md` Section 3, "Next action" ordered list, item 3's closing sentence
  ("Next is the root-cleanup task the owner added on 2026-09-24.")

- [ ] **Step 1: Add the Part B bullet**

  In `BATCH23_DEFINITION.md`, inside `#### Part B -- Reconcile what earlier batches left open`,
  add a new bullet after "The foundation plan's between-batch tasks land here":

  ```markdown
  - [ ] **Root cleanup.** Move `PLAYBOOK.md`, `FINDINGS.md`, `AGENT_NOTES.md` and
    `HANDOFF_PROMPT.md` to `docs/agents/`, and `.docsync.toml` and `frontend_gate_checks.toml`
    to `config/`, per the owner rulings of 2026-09-24. Plan:
    `docs/superpowers/plans/2026-09-24-batch23-wp0-root-cleanup.md`. `AGENTS.md`, `README.md`,
    `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `LICENSE`, `DEVELOPMENT.md`, `DEPLOY.md`,
    `DESIGN.md`, `PRODUCT.md`, `BATCH*_DEFINITION.md`, `fly.toml`, `Dockerfile`, `app.py`,
    `run.py`, `init_db.py`, and the standard Python config files stay at the root.
  ```

  Add its acceptance to Part B's existing acceptance list:

  ```markdown
    - Every task in the root-cleanup plan meets that plan's acceptance, with its live-probe
      table where the plan asks for one.
  ```

- [ ] **Step 2: Repoint PLAYBOOK Section 3**

  Replace "Next is the root-cleanup task the owner added on 2026-09-24." with:

  ```
  Next is the root-cleanup plan,
  `docs/superpowers/plans/2026-09-24-batch23-wp0-root-cleanup.md`.
  ```

- [ ] **Step 3: Gates and commit**

  `doc_state_sync.py --fix`; `pytest -q`; `pre-commit run --all-files`;
  `doc_state_sync.py --check`. Stage `BATCH23_DEFINITION.md` and `PLAYBOOK.md` by name.

  ```bash
  git commit -m "docs(batch23): Add the root-cleanup task to WP-0 Part B"
  ```

**Acceptance:** `doc_state_sync.py --check` exits 0; `BATCH23_DEFINITION.md` Part B lists the
task; PLAYBOOK Section 3 names this plan's path.

---

### Task 2: Declare document paths instead of hard-coding them

**Proposal Rule 4** (refactor requires parity tests): this changes what `collect_integrity_issues`
reads its document set from. Tests first, proving both the parity case (nothing declared,
behaviour unchanged) and the override case (a declared path is honoured), then the mechanism.
**No file moves in this task** -- every default stays today's literal, so every existing test
in `tests/test_docsync_*.py` and `tests/scripts/dev/test_worktree_guard_*.py` passes unedited.

**Files:**
- Modify: `scripts/docsync/declarations.py`
- Modify: `scripts/docsync/integrity.py`
- Modify: `scripts/docsync/cli.py`
- Test: `tests/test_docsync_declarations.py`
- Test: `tests/test_docsync_integrity.py`

**Interfaces:**
- Produces: `declarations.DocumentsConfig` (fields `playbook: str = "PLAYBOOK.md"`,
  `findings: str = "FINDINGS.md"`, `agent_notes: str = "AGENT_NOTES.md"`,
  `handoff_prompt: str = "HANDOFF_PROMPT.md"`), `declarations.load_documents_config(repo_root,
  *, config_path=None) -> DocumentsConfig`.
- Produces: `integrity.resolved_live_document_paths(documents: DocumentsConfig) -> tuple[str, ...]`.
- Consumes: `integrity.LIVE_DOCUMENT_RELATIVE_PATHS` (unchanged tuple, still the five literals),
  `findings.ACTIVE_PATH` (unchanged), `declarations._TOP_LEVEL_SCHEMA` (gains a `"documents"`
  key).

- [ ] **Step 1: Write the failing tests**

  In `tests/test_docsync_declarations.py`, add:

  ```python
  class TestDocumentsConfig:
      def test_absent_table_returns_todays_literal_defaults(self, tmp_path: Path):
          from docsync.declarations import DocumentsConfig, load_documents_config

          assert load_documents_config(tmp_path) == DocumentsConfig()
          assert DocumentsConfig().playbook == "PLAYBOOK.md"
          assert DocumentsConfig().findings == "FINDINGS.md"
          assert DocumentsConfig().agent_notes == "AGENT_NOTES.md"
          assert DocumentsConfig().handoff_prompt == "HANDOFF_PROMPT.md"

      def test_declared_table_overrides_one_field(self, tmp_path: Path):
          from docsync.declarations import load_documents_config

          (tmp_path / ".docsync.toml").write_text(
              '[documents]\nplaybook = "docs/agents/PLAYBOOK.md"\n', encoding="utf-8"
          )
          documents = load_documents_config(tmp_path)
          assert documents.playbook == "docs/agents/PLAYBOOK.md"
          assert documents.findings == "FINDINGS.md"  # untouched field keeps its default

      def test_unknown_key_is_refused(self, tmp_path: Path):
          from docsync.declarations import DeclarationError, load_documents_config

          (tmp_path / ".docsync.toml").write_text(
              '[documents]\nnotebook = "x.md"\n', encoding="utf-8"
          )
          with pytest.raises(DeclarationError, match="unknown key 'notebook'"):
              load_documents_config(tmp_path)

      def test_non_string_value_is_refused(self, tmp_path: Path):
          from docsync.declarations import DeclarationError, load_documents_config

          (tmp_path / ".docsync.toml").write_text(
              "[documents]\nplaybook = 1\n", encoding="utf-8"
          )
          with pytest.raises(DeclarationError, match="not a string"):
              load_documents_config(tmp_path)
  ```

  In `tests/test_docsync_integrity.py`, add:

  ```python
  def test_resolved_live_document_paths_matches_the_default_tuple_by_default():
      from docsync.declarations import DocumentsConfig
      from docsync.integrity import (
          LIVE_DOCUMENT_RELATIVE_PATHS,
          resolved_live_document_paths,
      )

      assert resolved_live_document_paths(DocumentsConfig()) == LIVE_DOCUMENT_RELATIVE_PATHS


  def test_resolved_live_document_paths_honours_an_override():
      from docsync.declarations import DocumentsConfig
      from docsync.integrity import resolved_live_document_paths

      documents = DocumentsConfig(playbook="docs/agents/PLAYBOOK.md")
      resolved = resolved_live_document_paths(documents)
      assert "docs/agents/PLAYBOOK.md" in resolved
      assert "PLAYBOOK.md" not in resolved


  def test_collect_integrity_issues_scans_under_an_overridden_playbook_path():
      """DOC001 must scan the document docsync is told to scan, not the default name,
      or a moved document silently drops out of the scan (a wrong green)."""
      from docsync.integrity import collect_integrity_issues

      issues = collect_integrity_issues(
          repo_root=Path("."),
          live_documents={"docs/agents/PLAYBOOK.md": ["See `NOWHERE.md` for detail."]},
          playbook_lines=["See `NOWHERE.md` for detail."],
          archive_lines=[],
          session_lines=None,
          expected_session_lines=None,
          tracked_paths=frozenset({"AGENTS.md"}),
          document_paths=("docs/agents/PLAYBOOK.md",),
          playbook_relative_path="docs/agents/PLAYBOOK.md",
      )
      assert any(
          issue.code == "DOC001" and issue.path == "docs/agents/PLAYBOOK.md"
          for issue in issues
      )
  ```

- [ ] **Step 2: Run the new tests to verify they fail**

  ```
  .venv/Scripts/pytest.exe tests/test_docsync_declarations.py::TestDocumentsConfig tests/test_docsync_integrity.py -k resolved_live_document_paths -v
  ```
  Expected: `ImportError`/`AttributeError` -- `DocumentsConfig`, `load_documents_config`,
  `resolved_live_document_paths` and the `document_paths`/`playbook_relative_path` kwargs do
  not exist yet.

- [ ] **Step 3: Implement `DocumentsConfig` in `declarations.py`**

  Add near `_TOP_LEVEL_SCHEMA` (extend the dict with a `"documents"` entry whose `"optional"`
  keys are the four field names, each typed `str`), then, following the exact shape of
  `ArchiveConfig`/`_validate_archives`/`_archive_config`/`load_archive_config`:

  ```python
  _TOP_LEVEL_SCHEMA["documents"] = {
      "required": {},
      "optional": {
          "playbook": str,
          "findings": str,
          "agent_notes": str,
          "handoff_prompt": str,
      },
  }


  @dataclasses.dataclass(frozen=True)
  class DocumentsConfig:
      """Where docsync's own live documents live, from [documents] or defaults.

      The defaults are docsync's generic vocabulary -- true for any repository that adopts
      the tool unmodified (AGENT_NOTES.md "This repository is also a template being
      extracted"). This repository overrides every field in its own declarations file,
      once the four documents move under docs/agents/.
      """

      playbook: str = "PLAYBOOK.md"
      findings: str = "FINDINGS.md"
      agent_notes: str = "AGENT_NOTES.md"
      handoff_prompt: str = "HANDOFF_PROMPT.md"


  def _validate_documents(documents: object) -> DocumentsConfig:
      """Check a declared [documents] table and return the resolved paths."""
      if not isinstance(documents, Mapping):
          raise DeclarationError(f"[documents] is {type(documents).__name__}, not a table.")
      schema = _TOP_LEVEL_SCHEMA["documents"]["optional"]
      kwargs: dict[str, str] = {}
      for key, value in documents.items():
          if key not in schema:
              raise DeclarationError(
                  f"[documents] has an unknown key {key!r}. Known keys: "
                  f"{', '.join(sorted(schema))}."
              )
          if not isinstance(value, str) or not value:
              raise DeclarationError(
                  f"[documents] gives {key!r} as {type(value).__name__}, not a string."
              )
          kwargs[key] = value
      return DocumentsConfig(**kwargs)


  def _documents_config(declarations: Mapping) -> DocumentsConfig:
      """Return the document paths for an already-read declarations file."""
      if "documents" not in declarations:
          return DocumentsConfig()
      return _validate_documents(declarations["documents"])


  def load_documents_config(repo_root: Path, *, config_path: Path | None = None) -> DocumentsConfig:
      """Read the repository's document paths, defaults included."""
      return _documents_config(load_declarations(repo_root, config_path=config_path))
  ```

  Add `"documents"` to `collect_declaration_issues`'s eager-validation block (alongside
  `_archive_config(declarations)` and `_closeout_config(declarations)`):
  `_documents_config(declarations)`. `known_tables` already includes every key of
  `_TOP_LEVEL_SCHEMA`, so `"documents"` is accepted automatically -- no separate edit needed
  there.

  Give `load_declarations` the new optional kwarg (every existing caller keeps working since
  the default is `None`):

  ```python
  def load_declarations(repo_root: Path, *, config_path: Path | None = None) -> dict:
      """Read the declarations file, or return nothing if there is none."""
      path = config_path if config_path is not None else repo_root / DECLARATIONS_FILENAME
      if not path.is_file():
          return {}
      ...
  ```

  Give `load_archive_config`, `load_closeout_config`, `load_findings_config` the same
  `*, config_path: Path | None = None` kwarg, each passing it straight through to
  `load_declarations`.

- [ ] **Step 4: Implement `resolved_live_document_paths` in `integrity.py`**

  Add next to `LIVE_DOCUMENT_RELATIVE_PATHS` (which stays exactly as it is):

  ```python
  def resolved_live_document_paths(documents: "DocumentsConfig") -> tuple[str, ...]:
      """Return the five live-document paths this repository currently declares.

      Mirrors LIVE_DOCUMENT_RELATIVE_PATHS's shape and order, but reads AGENT_NOTES.md,
      HANDOFF_PROMPT.md, PLAYBOOK.md and FINDINGS.md's locations from `documents` instead of
      restating them. AGENTS.md is not a `documents` field: it never moves.
      """
      return (
          "AGENTS.md",
          documents.handoff_prompt,
          documents.agent_notes,
          documents.playbook,
          documents.findings,
      )
  ```

  (Import `DocumentsConfig` from `docsync.declarations` for the type hint; the existing
  `from docsync.declarations import ...` import block in `integrity.py` already pulls
  `load_closeout_config`/`load_findings_config` from that module, so add `DocumentsConfig` to
  the same import line.)

- [ ] **Step 5: Give `collect_integrity_issues` its three optional kwargs**

  Add to the signature, each defaulting to today's literal:

  ```python
  def collect_integrity_issues(
      *,
      repo_root: Path,
      live_documents: Mapping[str, list[str]],
      playbook_lines: list[str],
      archive_lines: list[str],
      session_lines: list[str] | None,
      expected_session_lines: list[str] | None,
      tracked_paths: frozenset[str],
      batch_log_lines: Mapping[int, list[str]] | None = None,
      document_paths: tuple[str, ...] = LIVE_DOCUMENT_RELATIVE_PATHS,
      playbook_relative_path: str = "PLAYBOOK.md",
      findings_relative_path: str = findings_module.ACTIVE_PATH,
  ) -> list[IntegrityIssue]:
  ```

  Inside the function body:
  - `documents_to_scan = set(LIVE_DOCUMENT_RELATIVE_PATHS)` becomes
    `documents_to_scan = set(document_paths)`.
  - The two `path == "PLAYBOOK.md"` comparisons (inside the `for path in
    sorted(documents_to_scan):` loop) become `path == playbook_relative_path`.
  - `live_documents.get("FINDINGS.md")` (feeding `_check_findings_header_count`) becomes
    `live_documents.get(findings_relative_path)`.
  - `live_documents.get(findings_module.ACTIVE_PATH)` (feeding the DOC023 rot-issues check)
    becomes `live_documents.get(findings_relative_path)`.

  The twelve `_issue(..., "PLAYBOOK.md", ...)` and four `_issue("PLAYBOOK.md", ...)`
  cosmetic path-label sites (in `_active_definition_reference`, `_unpaired_result_issue`,
  `_check_unbolded_test_counts`, `_check_section3_next_wp` in `integrity.py`, and
  `_admission_issue`/`_claim_issues` in `closeout.py`) are **left unchanged in this task**.
  They only affect the printed `path` string in a diagnostic, never which document is
  scanned or whether a check fires -- a real but cosmetic gap, filed as a finding at the end
  of Task 6 rather than threaded through five more function signatures here (Rule 5, real-world
  KISS: the behavioural fix is required, the label fix is not).

- [ ] **Step 6: Run the tests to verify they pass**

  ```
  .venv/Scripts/pytest.exe tests/test_docsync_declarations.py tests/test_docsync_integrity.py tests/test_docsync_cli.py -v
  ```
  Expected: PASS, including the two existing `TestLiveDocumentPathsSingleSource` tests in
  `tests/test_docsync_cli.py`, unmodified -- they compare the bare default tuples to each
  other, which this task never changes.

- [ ] **Step 7: Full gates and live probe**

  `pytest -q`; `pre-commit run --all-files` will refuse the commit at the preflight (this task
  touches `scripts/docsync/`); run `doc_state_sync.py --check` directly first to confirm exit
  0, then commit with the documented escape.

  Live probe: in `/c/ssprobe/corpus`, add `[documents]\nplaybook = "elsewhere/PLAYBOOK.md"\n`
  to `.docsync.toml` with no other change. **Red:** the probe corpus's real `PLAYBOOK.md` is
  still at the root, so this alone proves nothing about the CLI yet (the CLI does not call
  `load_documents_config` until Task 6) -- record this as "not yet wired" rather than skipping
  the probe silently, and re-run the same probe after Task 6 lands, when it becomes live.

- [ ] **Step 8: Commit**

  ```bash
  doc_state_sync.py --check   # confirm exit 0 first
  SKIP=doc-state-sync-check git commit -m "feat(docsync): Add a declared [documents] table"
  ```

**Acceptance:** `DocumentsConfig` defaults reproduce every current literal; an override is
honoured by `resolved_live_document_paths` and by `collect_integrity_issues`'s new kwargs;
every existing test passes unmodified; `pytest -q` and `doc_state_sync.py --check` both pass.

---

### Task 3: A `--config` override for the docsync CLI

Independent of Task 2's table shape -- this is about *which file* is read, not what it
contains. Small, additive, no file moves.

**Files:**
- Modify: `scripts/docsync/cli.py`
- Test: `tests/test_docsync_cli.py`

**Interfaces:**
- Consumes: `declarations.load_declarations(repo_root, *, config_path=None)` (Task 2).
- Produces: `cli._build_parser()` gains `--config`; `cli.main()` computes `CONFIG_PATH` once.

- [ ] **Step 1: Write the failing test**

  In `tests/test_docsync_cli.py`, in `TestMainArgs` (or a new class beside it):

  ```python
  class TestConfigOverride:
      def test_config_flag_is_accepted_and_parsed(self):
          from docsync.cli import _build_parser

          args = _build_parser().parse_args(["--check", "--config", "somewhere/docsync.toml"])
          assert args.config == "somewhere/docsync.toml"

      def test_config_flag_defaults_to_none(self):
          from docsync.cli import _build_parser

          args = _build_parser().parse_args(["--check"])
          assert args.config is None
  ```

- [ ] **Step 2: Run to verify it fails**

  ```
  .venv/Scripts/pytest.exe tests/test_docsync_cli.py::TestConfigOverride -v
  ```
  Expected: FAIL -- `argparse` raises "unrecognized arguments: --config ...".

- [ ] **Step 3: Add the argument and thread it**

  In `_build_parser()`, add:

  ```python
  parser.add_argument(
      "--config",
      metavar="PATH",
      help=(
          "Path to the declarations file, overriding the repository default "
          "(config/docsync.toml)."
      ),
  )
  ```

  In `main()`, near the top, after `args = parser.parse_args()`:

  ```python
  CONFIG_PATH = Path(args.config) if args.config else None
  ```

  Thread `config_path=CONFIG_PATH` as a new keyword argument at every one of these existing
  call sites (named by enclosing function, not line number -- each is a one-line addition):
  `_archive_store` (`load_archive_config(REPO_ROOT)`), `_drift_updates`
  (`load_archive_config(REPO_ROOT)`), `_close_batch` (both `load_closeout_config(REPO_ROOT)`
  and `load_archive_config(REPO_ROOT)`), `_maintain_archives`
  (`load_archive_config(REPO_ROOT)`), `_collect_issues` (`collect_integrity_issues(...)`,
  which itself forwards to `collect_declaration_issues` and `load_findings_config`/
  `load_closeout_config` inside `integrity.py` -- give `collect_integrity_issues` the same
  `config_path: Path | None = None` kwarg and forward it to those three calls), and
  `_close_batch`'s second `collect_integrity_issues(...)` call.

  Because `main()` is the only place `CONFIG_PATH` is computed, every one of these functions
  that is not already passed `REPO_ROOT` as a parameter needs `CONFIG_PATH` threaded down as
  a parameter too, the same way `REPO_ROOT` already is (module-level constant, read directly,
  since `cli.py`'s existing functions already read `REPO_ROOT` this way rather than taking it
  as an argument). Model `CONFIG_PATH` the same way: a module-level `CONFIG_PATH: Path | None`
  variable, assigned once in `main()` before any of these functions run, read directly by each
  rather than passed as a parameter -- consistent with how `REPO_ROOT` already works in this
  file, and avoiding a signature change on every function that currently reads `REPO_ROOT`
  directly.

- [ ] **Step 4: Run to verify it passes**

  ```
  .venv/Scripts/pytest.exe tests/test_docsync_cli.py -v
  ```

- [ ] **Step 5: Gates and live probe**

  `pytest -q`; `doc_state_sync.py --check` at exit 0 first (this touches `scripts/docsync/`).

  Live probe: in `/c/ssprobe/corpus`, copy `.docsync.toml` to `alt.toml` with one changed
  value (e.g. `[archives] max_lines = 5` instead of `500`). **Red-equivalent (behavioural
  proof):** `python scripts/doc_state_sync.py --check` (no `--config`) ignores `alt.toml`;
  `python scripts/doc_state_sync.py --check --config alt.toml` picks up the changed threshold
  (observable via `--paginate-archives --config alt.toml --as-of <date>` behaving differently
  at the new threshold, or via a unit-level assertion if the CLI has no direct
  threshold-visible `--check` output -- use whichever is actually observable and record which).

- [ ] **Step 6: Commit**

  ```bash
  SKIP=doc-state-sync-check git commit -m "feat(docsync): Add a --config override"
  ```

**Acceptance:** `--config PATH` is accepted, defaults to `None`, and demonstrably changes
which declarations file every mode reads from.

---

### Task 4: Move `frontend_gate_checks.toml` to `config/`

Independent of docsync entirely (inventory Section 7, row 7: no shared code path). The
riskiest single step in this plan by import-time coupling (inventory Section 7, row 1) --
the file move and the constant update must be the same commit.

**Files:**
- Modify: `scripts/dev/frontend_gate.py`
- Test: none need editing (inventory Section 2: the manifest-specific tests build their own
  `tmp_path` manifest and pass it explicitly; only *import* depends on the real path, and
  every `tests/scripts/dev/test_frontend_gate_*.py` module already imports `frontend_gate`
  at collection time, which is exactly what this task's live probe exercises).

- [ ] **Step 1: Move the file and update the constant, in one change**

  ```bash
  mkdir -p config
  git mv frontend_gate_checks.toml config/frontend_gate_checks.toml
  ```

  In `scripts/dev/frontend_gate.py`, change:

  ```python
  CHECK_MANIFEST_PATH = REPO_ROOT / "frontend_gate_checks.toml"
  ```
  to:
  ```python
  CHECK_MANIFEST_PATH = REPO_ROOT / "config" / "frontend_gate_checks.toml"
  ```

  Update the comment immediately above it (currently "Root-level declarations file: which
  checks run is a repository fact, the same pattern `.docsync.toml` sets (facts at the root,
  mechanism under `scripts/`)...") to read "Declarations file under `config/`" and drop the
  now-false "facts at the root" claim.

  Update the two hard-coded strings in `_load_check_manifest`'s `FrontendGateError` messages:
  `"Restore frontend_gate_checks.toml at the repository root."` becomes `"Restore
  frontend_gate_checks.toml at config/frontend_gate_checks.toml."`.

- [ ] **Step 2: Run the collection-dependent tests**

  ```
  .venv/Scripts/pytest.exe tests/scripts/dev/test_frontend_gate_manifest.py tests/scripts/dev/test_frontend_gate_checks.py tests/scripts/dev/test_frontend_gate_layout.py -v
  ```
  (substitute the real set of `test_frontend_gate_*.py` files present; every one that does
  `from scripts.dev import frontend_gate` must still collect and pass.)

- [ ] **Step 3: Full gates**

  `pytest -q`; `python scripts/dev/frontend_gate.py --help` (or equivalent smoke invocation)
  to prove the module still imports cleanly outside pytest; `pre-commit run --all-files`;
  `doc_state_sync.py --check`. This task does not touch `scripts/docsync/`, so the normal
  preflight path applies -- no `SKIP=` needed.

- [ ] **Step 4: Live probe**

  In `/c/ssprobe/corpus`: **red** -- `git rm config/frontend_gate_checks.toml && git commit
  -qm red`, then `python -c "from scripts.dev import frontend_gate"` must raise
  `FrontendGateError: check manifest missing at .../config/frontend_gate_checks.toml`. **Near-
  miss green** -- restore the file with a trailing blank line added (still valid TOML); the
  same import must succeed silently.

- [ ] **Step 5: Commit**

  ```bash
  git commit -m "chore(frontend-gate): Move the check manifest under config/"
  ```

**Acceptance:** the manifest lives at `config/frontend_gate_checks.toml`; every
`frontend_gate`-importing test collects; the live probe's red and near-miss both behave as
specified.

---

### Task 5: Move `.docsync.toml` to `config/`

**Files:**
- Modify: `scripts/docsync/declarations.py` (`DECLARATIONS_FILENAME`)
- Modify: `scripts/dev/docsync_preflight.py` (`CONTROL_PLANE_FILES`)
- Test: `tests/scripts/dev/test_docsync_preflight.py` (`test_control_plane_prefix_matching`)

- [ ] **Step 1: Update the failing test first**

  In `tests/scripts/dev/test_docsync_preflight.py`, in `test_control_plane_prefix_matching`'s
  parametrize list, replace `(".docsync.toml", True)` with `("config/docsync.toml", True)`,
  add a new row `(".docsync.toml", False)` (the retired root name is no longer special), and
  replace `(".docsync.tomlx", False)` with `("config/docsync.tomlx", False)` (keeping the
  exact-match negative control at the new name).

  ```
  .venv/Scripts/pytest.exe tests/scripts/dev/test_docsync_preflight.py::test_control_plane_prefix_matching -v
  ```
  Expected: FAIL -- `"config/docsync.toml"` is not yet in `CONTROL_PLANE_FILES`, and
  `".docsync.toml"` still is.

- [ ] **Step 2: Move the file and update both constants**

  ```bash
  git mv .docsync.toml config/docsync.toml
  ```

  In `scripts/docsync/declarations.py`:
  ```python
  DECLARATIONS_FILENAME = "config/docsync.toml"
  ```
  (its docstring already says "relative to the repo root", which stays true.)

  In `scripts/dev/docsync_preflight.py`:
  ```python
  CONTROL_PLANE_FILES: tuple[str, ...] = (
      "scripts/doc_state_sync.py",
      "scripts/dev/docsync_preflight.py",
      "config/docsync.toml",
  )
  ```

- [ ] **Step 3: Run the updated test, plus the full declarations suite**

  ```
  .venv/Scripts/pytest.exe tests/scripts/dev/test_docsync_preflight.py tests/test_docsync_declarations.py tests/test_docsync_cli.py -v
  ```
  Expected: PASS. No other test in these files reads `DECLARATIONS_FILENAME`'s value directly
  (`tests/test_docsync_declarations.py` goes through the `DECLARATIONS_FILENAME` symbol, not a
  literal, per inventory Section 2).

- [ ] **Step 4: Update `test_staged_preflight_against_real_docsync_checker`**

  This synthetic fixture (`tests/scripts/dev/test_docsync_preflight.py`, the real-git-repo
  end-to-end test) writes `.docsync.toml` at its temporary repo's root, mirroring today's flat
  layout. Change it to write the file at `config/docsync.toml` inside that same temporary repo
  (creating the `config/` subdirectory first), so the fixture exercises the production layout
  this task ships rather than the one it retires. `PLAYBOOK.md`, `AGENTS.md`,
  `HANDOFF_PROMPT.md`, `AGENT_NOTES.md`, `FINDINGS.md` stay at the fixture's root in *this*
  task -- they move in Task 6, and this test moves with them there.

- [ ] **Step 5: Full gates**

  This touches `scripts/docsync/declarations.py` and `scripts/dev/docsync_preflight.py`, both
  control-plane. `doc_state_sync.py --check` directly first (exit 0), then:

  ```bash
  SKIP=doc-state-sync-check git commit -m "chore(docsync): Move .docsync.toml under config/"
  ```

- [ ] **Step 6: Live probe**

  In `/c/ssprobe/corpus`: **red** -- stage a change to `scripts/docsync/declarations.py` (any
  one-line comment edit) alongside a change to `config/docsync.toml`, `git add` both, and run
  `python scripts/dev/docsync_preflight.py --staged`. Expected: nonzero exit, the control-plane
  refusal message, naming `config/docsync.toml`. **Near-miss green** -- stage only the
  `declarations.py` comment change (not `config/docsync.toml`); the same command must exit 0.

**Acceptance:** `config/docsync.toml` is the declarations file docsync reads by default;
`CONTROL_PLANE_FILES` recognizes it; the moved-fixture test still exercises real production
behaviour; the probe confirms the preflight still refuses a staged control-plane change under
the new name.

---

### Task 6: Move the four documents and wire the `[documents]` declaration live

The largest task, and the one that cannot land partially (inventory Section 7, row 4: DOC001
cannot pass with the move half-done). One commit.

**Files:**
- `git mv PLAYBOOK.md docs/agents/PLAYBOOK.md`
- `git mv FINDINGS.md docs/agents/FINDINGS.md`
- `git mv AGENT_NOTES.md docs/agents/AGENT_NOTES.md`
- `git mv HANDOFF_PROMPT.md docs/agents/HANDOFF_PROMPT.md`
- Modify: `config/docsync.toml` (`[documents]` table; four `[retired.allow_after]` keys; the
  `AGENT_NOTES.md` value-site; the comment at the fourth retired block)
- Modify: `scripts/docsync/cli.py` (`_read_live_documents` and the two `collect_integrity_issues`
  call sites now pass the resolved paths for real)
- Modify: `scripts/dev/_worktree_guard_inspection.py`
- Modify: `scripts/dev/_worktree_guard_diagnostics.py` (cosmetic label)
- Modify: `scripts/docsync/renderer.py` (`_build_status_block`, two `` `PLAYBOOK.md` `` prose
  strings)
- Modify: every always-scanned live document's citations (see Step 5)
- Modify: `docs/AGENT_DOC_MAP.md`, `docs/agents/domain.md`, `docs/agents/global-rules.md`,
  `docs/agents/issue-tracker.md`, `DEVELOPMENT.md`, `PRODUCT.md`, `docs/ARCHITECTURE.md`,
  `docs/architecture/*.md` citing any of the four, `docs/design/RECONCILIATION.md` (if it
  cites any of the four -- confirm before editing; inventory Section 3 does not list it under
  any of the four documents' citer tables, so likely no change needed there), and
  `.superpowers/cloud-kit/constraints.md`
- Test: `tests/scripts/dev/test_worktree_guard_playbook.py`
  (`test_the_repository_playbook_parses`)

- [ ] **Step 1: Update the one test that reads the real file, first**

  In `tests/scripts/dev/test_worktree_guard_playbook.py::test_the_repository_playbook_parses`,
  change:
  ```python
  playbook = (REPOSITORY_ROOT / "PLAYBOOK.md").read_text(...)
  ```
  to:
  ```python
  playbook = (REPOSITORY_ROOT / "docs" / "agents" / "PLAYBOOK.md").read_text(...)
  ```

  ```
  .venv/Scripts/pytest.exe tests/scripts/dev/test_worktree_guard_playbook.py -v
  ```
  Expected: FAIL -- `FileNotFoundError` at the new path (it doesn't exist yet); this confirms
  the test is exercising the real repository file, not a fixture.

- [ ] **Step 2: Move the four files**

  ```bash
  mkdir -p docs/agents
  git mv PLAYBOOK.md docs/agents/PLAYBOOK.md
  git mv FINDINGS.md docs/agents/FINDINGS.md
  git mv AGENT_NOTES.md docs/agents/AGENT_NOTES.md
  git mv HANDOFF_PROMPT.md docs/agents/HANDOFF_PROMPT.md
  ```

- [ ] **Step 3: Fix the worktree guard's hard filesystem read (inventory Section 7, row 2)**

  In `scripts/dev/_worktree_guard_inspection.py`, change:
  ```python
  playbook_path = resolved_root / "PLAYBOOK.md"
  ```
  to:
  ```python
  playbook_path = resolved_root / "docs" / "agents" / "PLAYBOOK.md"
  ```

  In `scripts/dev/_worktree_guard_diagnostics.py`, update the `"PLAYBOOK.md"` display label in
  `metadata_unavailable_diagnostic` to `"docs/agents/PLAYBOOK.md"` for a readable error.

  Run the worktree guard's own suite:
  ```
  .venv/Scripts/pytest.exe tests/scripts/dev/test_worktree_guard_playbook.py tests/scripts/dev/test_worktree_guard_base_ref.py tests/scripts/dev/test_worktree_guard_inspection.py tests/scripts/dev/test_worktree_guard_subject.py tests/scripts/dev/test_worktree_guard_topology.py -v
  ```
  Expected: PASS. The synthetic `tmp_path`-based fixtures (`worktree_guard_fakes.py` and the
  other four `test_worktree_guard_*.py` files) write `repo.joinpath("PLAYBOOK.md")` against a
  `resolved_root` the test itself controls -- since the code now reads `resolved_root /
  "docs" / "agents" / "PLAYBOOK.md"`, these fixtures must write their synthetic file to that
  same nested path too, or they will fail with a real `FileNotFoundError` this time (not a
  cosmetic gap -- these fixtures exercise the literal this task just changed). Update each
  fixture's `repo.joinpath("PLAYBOOK.md")` (or equivalent) to
  `repo.joinpath("docs", "agents", "PLAYBOOK.md")`, creating the parent directories first.
  This is a **named, load-bearing test edit**, not the cosmetic-gap kind: run Step 1's test
  file list before and after to confirm each one fails first (proving it depends on the old
  literal) and passes after.

- [ ] **Step 4: Wire `config/docsync.toml`'s `[documents]` table and fix the four
  `allow_after` keys and the `AGENT_NOTES.md` value site**

  Add, in the "Options" section (after `[options]`, mirroring `[archives]`/`[closeout]`'s
  placement):
  ```toml
  # ----------------------------------------------------------------------
  # Document locations
  # ----------------------------------------------------------------------

  # These four documents moved from the repository root to docs/agents/ (root cleanup,
  # 2026-09-24). AGENTS.md itself is not declared here: it never moves.
  [documents]
  playbook = "docs/agents/PLAYBOOK.md"
  findings = "docs/agents/FINDINGS.md"
  agent_notes = "docs/agents/AGENT_NOTES.md"
  handoff_prompt = "docs/agents/HANDOFF_PROMPT.md"
  ```

  Change the `AGENT_NOTES.md` value-site (`[[value.sites]] file = "AGENT_NOTES.md"` under "the
  heatmap window length"):
  ```toml
  [[value.sites]]
  file = "docs/agents/AGENT_NOTES.md"
  pattern = 'last (\d+) days'
  expect = "365"
  ```

  Change all four `[retired.allow_after]` blocks (inventory Section 5, risk 3):
  ```toml
  [retired.allow_after]
  "docs/agents/PLAYBOOK.md" = "## 4. Execution log (for agent handoff)"
  ```

  Update the comment above the fourth block ("needs PLAYBOOK.md's real heading text") to say
  "docs/agents/PLAYBOOK.md's real heading text".

- [ ] **Step 5: Wire `cli.py` to actually consume the new declaration**

  In `_read_live_documents()`, resolve `LIVE_DOCUMENT_PATHS` through the loaded config instead
  of the bare module constant:
  ```python
  def _read_live_documents() -> dict[str, list[str]]:
      """Load canonical documents, root definitions and archived definitions."""
      documents_config = load_documents_config(REPO_ROOT, config_path=CONFIG_PATH)
      live_paths = tuple(
          REPO_ROOT / relative
          for relative in resolved_live_document_paths(documents_config)
      )
      documents = {
          _repository_relative(path): _read_lines(path) for path in live_paths
      }
      ...
  ```
  (add `resolved_live_document_paths` and `DocumentsConfig`/`load_documents_config` to the
  existing `from docsync.integrity import (...)` / `from docsync.declarations import (...)`
  blocks at the top of `cli.py`.)

  `PLAYBOOK_PATH` and `FINDINGS_PATH`, wherever else they are read for direct I/O outside
  `_read_live_documents` (grep `PLAYBOOK_PATH\b` and `FINDINGS_PATH\b` in `cli.py` to find every
  site), become `REPO_ROOT / documents_config.playbook` and `REPO_ROOT /
  documents_config.findings` resolved the same way, computed once per invocation (in `main()`,
  alongside `CONFIG_PATH`) and passed down rather than re-read as bare module constants.

  In `_collect_issues` and `_close_batch`'s `collect_integrity_issues(...)` calls, pass:
  ```python
  document_paths=resolved_live_document_paths(documents_config),
  playbook_relative_path=documents_config.playbook,
  findings_relative_path=documents_config.findings,
  ```
  (`documents_config` computed once, the same object used by `_read_live_documents`).

- [ ] **Step 6: Rewrite renderer.py's prose and the two cosmetic-label call sites you choose to
  fix now**

  In `scripts/docsync/renderer.py`'s `_build_status_block`, change the two
  `"- Source of truth: \`PLAYBOOK.md\` (Section 3 and Section 4)."` lines to
  `"- Source of truth: \`docs/agents/PLAYBOOK.md\` (Section 3 and Section 4)."`.

- [ ] **Step 7: Sweep every bare citation in the five always-scanned documents plus the active
  definition and SESSION_CONTEXT (inventory Section 4, risk 4 -- `--check` cannot pass with
  this half-done)**

  Grep each of these five files plus `BATCH23_DEFINITION.md` and `.claude/SESSION_CONTEXT.md`
  for `` `PLAYBOOK.md` ``, `` `FINDINGS.md` ``, `` `AGENT_NOTES.md` ``, `` `HANDOFF_PROMPT.md` ``
  (backticked form) and rewrite every one to the `docs/agents/` form, **except** any hit inside
  a `PLAYBOOK.md` Section 4 dated entry block (stripped from the DOC001 scan regardless, per
  `_playbook_lines_without_entry_blocks` -- leave those as written, they are point-in-time):

  ```bash
  grep -n '`PLAYBOOK\.md`\|`FINDINGS\.md`\|`AGENT_NOTES\.md`\|`HANDOFF_PROMPT\.md`' \
    AGENTS.md docs/agents/HANDOFF_PROMPT.md docs/agents/AGENT_NOTES.md \
    docs/agents/FINDINGS.md docs/agents/PLAYBOOK.md BATCH23_DEFINITION.md \
    .claude/SESSION_CONTEXT.md
  ```

  `AGENTS.md`'s "Document Roles" table and "Session Bootstrap" numbered list both cite all
  four files by bare name and are the densest hit set here; update every row/step to the
  `docs/agents/` form.

- [ ] **Step 8: Sweep the non-gated live documents** (not scanned by DOC001, per inventory
  Section 4, but still stale prose if left)

  `docs/AGENT_DOC_MAP.md` (routing table, 6+5+2+1 citations), `docs/agents/domain.md`,
  `docs/agents/global-rules.md`, `docs/agents/issue-tracker.md` (these three now sit in the
  *same* directory as the four moved files -- cite them relative, e.g. `` `PLAYBOOK.md` ``
  read as a sibling, since every other citation style in the repository is repo-root-relative
  and consistency with that existing convention outweighs the shorter form here: use
  `` `docs/agents/PLAYBOOK.md` `` even from a same-directory file), `DEVELOPMENT.md`,
  `PRODUCT.md`, `docs/ARCHITECTURE.md`, `docs/architecture/*.md` that cite any of the four
  (`documentation-tooling.md`, `development-cycle.md` per inventory Section 3), and
  `.superpowers/cloud-kit/constraints.md` (including its literal `grep -n "^### .*WP-[0-9]"
  PLAYBOOK.md` command example at line 175 -- rewrite the command itself, not just the prose
  around it, or it silently finds nothing the next time an agent runs it). Confirm
  `docs/design/RECONCILIATION.md`, `README.md` and `DESIGN.md` need no change (inventory
  Section 3: zero hits for `README.md`/`DESIGN.md`; `RECONCILIATION.md` not listed as a citer
  of any of the four).

- [ ] **Step 9: Full test run, gates, and the live probe**

  ```
  pytest -q
  ```
  Expected: every test passes, including the newly-updated worktree-guard fixtures and
  `test_the_repository_playbook_parses`.

  `doc_state_sync.py --check` directly first (this commit touches `scripts/docsync/cli.py`,
  control-plane) -- expect exit 0 once Steps 4-8 are complete; a nonzero exit here before
  Step 8 is finished is expected and not a defect, per the "cannot pass with the move
  half-done" constraint -- do not commit until it is 0.

  Live probe, in `/c/ssprobe/corpus` (rebuilt fresh from HEAD *after* this task's changes are
  staged locally but not yet committed -- build the probe from the working tree, not from the
  last commit, per the verification standard's Step 1 using the worktree as source):
  - **Red 1 (allow_after silently stops applying):** revert only the four
    `[retired.allow_after]` keys in `config/docsync.toml` back to `"PLAYBOOK.md"` while
    leaving everything else moved; run `--check`. Expected: DOC011 fires on the retired-claim
    text still present in `docs/agents/PLAYBOOK.md`'s Section 4 (a false positive, proving the
    key must point at the new path).
  - **Near-miss green 1:** restore the correct `"docs/agents/PLAYBOOK.md"` keys; `--check`
    exits 0 on the same content.
  - **Red 2 (worktree guard):** revert only `_worktree_guard_inspection.py`'s literal back to
    `"PLAYBOOK.md"`; run `python scripts/dev/check_worktree_alignment.py --offline
    --base-ref <base>`. Expected: the metadata-unavailable diagnostic, "PLAYBOOK.md could not
    be read" (or the new label if Step 3's diagnostics fix is also reverted together).
  - **Near-miss green 2:** restore the fix; the same command reads Section 3 successfully.
  - **Red 3 (DOC001 citation sweep):** leave one bare `` `PLAYBOOK.md` `` citation
    un-rewritten inside `AGENTS.md`; run `--check`. Expected: DOC001 fires, naming the stale
    citation.
  - **Near-miss green 3:** the same citation rewritten to `` `docs/agents/PLAYBOOK.md` ``;
    `--check` exits 0.

- [ ] **Step 10: Commit**

  ```bash
  git add docs/agents/PLAYBOOK.md docs/agents/FINDINGS.md docs/agents/AGENT_NOTES.md \
    docs/agents/HANDOFF_PROMPT.md config/docsync.toml scripts/docsync/cli.py \
    scripts/docsync/renderer.py scripts/dev/_worktree_guard_inspection.py \
    scripts/dev/_worktree_guard_diagnostics.py AGENTS.md BATCH23_DEFINITION.md \
    .claude/SESSION_CONTEXT.md docs/AGENT_DOC_MAP.md docs/agents/domain.md \
    docs/agents/global-rules.md docs/agents/issue-tracker.md DEVELOPMENT.md PRODUCT.md \
    docs/ARCHITECTURE.md docs/architecture/documentation-tooling.md \
    docs/architecture/development-cycle.md .superpowers/cloud-kit/constraints.md \
    tests/scripts/dev/test_worktree_guard_playbook.py \
    tests/scripts/dev/worktree_guard_fakes.py tests/scripts/dev/test_worktree_guard_base_ref.py \
    tests/scripts/dev/test_worktree_guard_inspection.py \
    tests/scripts/dev/test_worktree_guard_subject.py tests/scripts/dev/test_worktree_guard_topology.py
  doc_state_sync.py --check   # confirm exit 0 first
  SKIP=doc-state-sync-check git commit -m "chore(docs): Move PLAYBOOK/FINDINGS/AGENT_NOTES/HANDOFF_PROMPT to docs/agents/"
  ```

**Acceptance:** the four files live at `docs/agents/`; `config/docsync.toml` declares their
new paths; the worktree guard reads the new location; the four `allow_after` keys and every
bare citation inside the five always-scanned documents (plus the active definition and
SESSION_CONTEXT) are current; `pytest -q`, `pre-commit run --all-files` and
`doc_state_sync.py --check` all pass; every live-probe row behaves as specified.

---

### Task 7: Reconcile PR #242's repo-assist workflow, or file the follow-up

Owner ruling: PR #242 (`chore/repo-assist-workflow`) adds `.github/workflows/repo-assist.md`
naming `PLAYBOOK.md`/`FINDINGS.md` at the root in its `allowed-files` lists and prose, and the
owner merges #242 before this move lands. This task decides which of the two stated options
applies, at the moment it runs, and does not guess.

**Files:**
- Modify (if present): `.github/workflows/repo-assist.md`
- Modify (if absent): `FINDINGS.md` (post-move: `docs/agents/FINDINGS.md`)

- [ ] **Step 1: Check whether the file exists on this branch**

  ```bash
  git fetch origin
  test -f .github/workflows/repo-assist.md && echo PRESENT || echo ABSENT
  ```

- [ ] **Step 2a: If PRESENT** (PR #242 merged to `main` and `main` has been merged into this
  branch by the time this task runs)

  Update both `allowed-files` lists (`create-pull-request` and
  `push-to-pull-request-branch`) to add `docs/agents/PLAYBOOK.md` and
  `docs/agents/FINDINGS.md` alongside (or in place of, if the owner's #242 merge already
  dropped the root paths as dead) the root-path entries. Update the "Repository Rules" prose
  exclusion ("Never edit ... anything under `scripts/` or `docs/` other than the log files
  ...") to explicitly permit `docs/agents/PLAYBOOK.md` and `docs/agents/FINDINGS.md`, so the
  `allowed-files` grant and the prose prohibition agree. Update the two prose mentions of
  `FINDINGS.md` at lines 10-11 and 316 for consistency. Commit as its own change:
  ```bash
  git commit -m "chore(repo-assist): Point allowed-files at the moved documents"
  ```

- [ ] **Step 2b: If ABSENT** (this task runs before #242 merges)

  File a finding in `FINDINGS.md` (pre-move) or `docs/agents/FINDINGS.md` (if Task 6 has
  already landed) at P1, tagged `F-DOCSYNC-<next>`: "The `chore/repo-assist-workflow` branch
  (PR #242, not yet merged) hard-codes `PLAYBOOK.md`/`FINDINGS.md` at the repository root in
  its `allowed-files` lists and prose; once merged, repoint both to `docs/agents/`." No code
  change in this repository; this is the "stated follow-up" the owner ruling names as the
  alternative, and closing it is future-batch work triggered by #242's merge, not by this
  plan.

**Acceptance:** either `.github/workflows/repo-assist.md` is consistent with the new paths, or
a named finding records the follow-up. One of the two, not neither.

---

## Self-Review

**Spec coverage.** Every item in `.superpowers/sdd/2026-09-24-batch23-root-cleanup/inventory.md`
is accounted for: Section 1's code sites (Tasks 4-6), Section 2's tests (Tasks 1, 5, 6 name
every test that changes and why; the self-consistent synthetic fixtures in `tests/conftest.py`
and `tests/test_docsync_cli.py`'s `CORPUS_*` constants are a deliberate, stated scope cut --
they test docsync's logic generically and gain no regression coverage from mirroring the new
layout, so touching ~45+ call sites for no behavioural gain is declined by Rule 5), Section 3's
citers (Task 6 Steps 7-8), Section 4's DOC001 scan mechanics (Task 2's kwargs, Task 6's sweep),
Section 5's declarations (Task 6 Step 4), Section 6's other entry points (Task 6's sweep list,
Task 7, and the controller list below), Section 7's seven risks (rows 1 and 2 are Tasks 4 and
6's same-commit constraints; row 3 is Task 6 Step 4; row 4 is Task 6's whole-document sweep;
row 5 is the `git mv` rule in Global Constraints; row 6 noted, no defect found; row 7 is why
Tasks 4 and 5 are separate commits from Task 6).

**Placeholder scan.** No task says "add tests" without the test body, no task says "update
references" without naming which ones and where.

**Type consistency.** `DocumentsConfig` is defined once (Task 2) and consumed with the same
field names (`playbook`, `findings`, `agent_notes`, `handoff_prompt`) in Tasks 3 and 6.
`resolved_live_document_paths(documents: DocumentsConfig) -> tuple[str, ...]` is defined once
(Task 2) and called unchanged in Task 6. `collect_integrity_issues`'s three new kwargs
(`document_paths`, `playbook_relative_path`, `findings_relative_path`) are introduced in Task
2 with their final names and used unchanged in Task 6.

---

## Definition of Done

Parts 1-7 each meet their own acceptance. `pytest -q`, `pre-commit run --all-files`,
`doc_state_sync.py --check`, and the frontend gate all pass on the final tree. `PLAYBOOK.md`
Section 4 carries one dated entry per task (untagged, per WP-0's logging rule), with each
task's live-probe table pasted in. Task 7 has landed one of its two branches. The controller
checklist below is handed to the owner, not executed by an implementer.

---

## Controller-only checklist (outside this repository's git tracking)

These cannot be committed by an SDD implementer -- they are either gitignored or outside the
repository entirely. Hand these to the owner or do them yourself once Task 6 has landed:

1. **`CLAUDE.md`** (repo root, gitignored, present on this machine): its Session Bootstrap
   pointer list cites `` `PLAYBOOK.md` ``, `` `.claude/SESSION_CONTEXT.md` ``, `` `AGENT_NOTES.md` ``,
   `` `BATCH*_DEFINITION.md` ``, `` `FINDINGS.md` ``. Repoint the four to `docs/agents/`.
2. **`.claude/CLAUDE.md`**: checked, no reference to any of the six paths -- no edit needed.
3. **`~/.claude` memory files** (`project_batch23_wp0.md` and any sibling that cites `PLAYBOOK.md`/
   `FINDINGS.md`/`AGENT_NOTES.md`/`HANDOFF_PROMPT.md` by bare root path): update once Task 6
   lands, so the next cold-resume session's memory agrees with the tree.
4. **Handoff documents already written** (e.g.
   `docs/superpowers/handoffs/scrobblescope-handoff-2026-09-23-after-task7.md`): point-in-time,
   per DOC001's own exemption rule -- leave as written, no edit.
5. **PR #242** itself: see Task 7. If it merges after this plan's Task 6 has already landed on
   `main`, its author should git-mv the repo-assist workflow's targets against the already-moved
   tree rather than reintroducing root paths that Task 7's finding then has to catch again.

---

## Revisions pending (apply before execution)

The owner answered this draft's open points and ruled on two more items on
2026-09-24; a plan review (read-only, source-verified) found the rest. Each
item says what to change.

1. **New Task 0: merge `origin/main` into this branch before anything else**
   (owner ruling, 2026-09-24). PR #242 merged into `main` as `707eed6`; this
   branch does not contain it. A normal merge commit, no history rewrite.
   Verified with `git merge-tree --write-tree HEAD origin/main` at `151717d`:
   the only conflicts are `PLAYBOOK.md` Section 4 and
   `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`, because both sides
   added untagged entries after the current-batch end marker. Keep every
   entry from both sides, newest first, then let `doc_state_sync.py --fix`
   settle the rotation; `main`'s other changes (`.github/workflows/repo-assist.*`,
   `.github/aw/actions-lock.json`, `.gitattributes`, and a
   `.github/copilot-instructions.md` line byte-identical to this branch's)
   merge cleanly. `main`'s other commits since the merge base (`1d16e18`) are
   merges whose content this branch already holds. The review's claim that
   `AGENTS.md`, `FINDINGS.md`, `AGENT_NOTES.md`, `frontend_gate.py` and a
   test would conflict is disproved by that simulation. Run every gate after
   the merge; its Section 4 entry is untagged.
2. **Task 7 always takes the "present" branch.** After Task 0 the workflow
   is on this branch, so delete the probe and Step 2b (whose "not yet
   merged" wording is now false). Repoint `.github/workflows/repo-assist.md`:
   both `allowed-files` lists name `docs/agents/PLAYBOOK.md` and
   `docs/agents/FINDINGS.md` in place of the root paths; its "Repository
   Rules" prose, which forbids editing `docs/` beyond the log files, must
   permit those two files, and its `FINDINGS.md` mentions become
   `docs/agents/FINDINGS.md`. Then `gh aw compile repo-assist` and commit
   the regenerated `.lock.yml` (a cloud sandbox without the `gh aw`
   extension leaves this task to a local session).
3. **New Task 8: the diagnostics name the declared path** (owner ruling,
   2026-09-24; replaces "file a finding"). Thread the declared playbook path
   into every `_issue(...)` call that prints `"PLAYBOOK.md"` as its location:
   ten label sites across `scripts/docsync/integrity.py` and
   `scripts/docsync/closeout.py` (the draft's "twelve" double-counted the two
   `path ==` comparisons Task 6 already fixes), including the two DOC002
   checks inside `collect_integrity_issues` that the draft never named.
   Tests first, asserting the `docs/agents/` path appears in the diagnostic;
   a live probe that plants a DOC002 or DOC007 defect and shows the new
   path. Remove the draft's open point 2.
4. **Task 6 Step 6 also fixes `SIDE_ARCHIVE_PREFIX`** in
   `scripts/docsync/renderer.py`, the module's third `PLAYBOOK.md` citation
   (inventory Section 1 lists all three).
5. **Task 1 names its own Section 4 entry** (untagged, Part B) explicitly,
   and, since this file is already tracked, its commit also carries the
   plan's approved version (status paragraph and this section removed).
6. **Citation style is settled:** repository-root paths everywhere, including
   between files in `docs/agents/` (DOC001 resolves citations from the
   repository root). Remove the draft's open point 1.
7. **Advisory, decide at dispatch:** Task 6 must be one commit, but may be
   two sequential implementer dispatches over one uncommitted tree (moves
   and wiring, then the citation sweep, tests and the commit).
8. **Interpreter paths:** Global Constraints name the local Windows venv. In
   a cloud session use `.superpowers/cloud-kit/constraints.md` R10 and its
   gates block instead.
