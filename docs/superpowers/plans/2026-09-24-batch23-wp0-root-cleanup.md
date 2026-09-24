# Batch 23 WP-0 Part B: root cleanup (document and config relocation)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move `PLAYBOOK.md`, `FINDINGS.md`, `AGENT_NOTES.md`, `HANDOFF_PROMPT.md` from the
repository root to `docs/agents/`, and `.docsync.toml` / `frontend_gate_checks.toml` to
`config/docsync.toml` / `config/frontend_gate_checks.toml`, without a gate going red at any
committed point, and make docsync's own document paths a declared fact instead of a
hard-coded Python literal (`AGENT_NOTES.md` "This repository is also a template being
extracted").

**Architecture:** Task 0 first merges `origin/main` into this branch, so PR #242's workflow
moves with the files. Then three independent clusters, sequenced by blast radius (inventory
Section 7, row 7): the `[documents]` declaration mechanism and the `--config` override land first, as
pure additions with no file movement and no default-value change, so they carry zero risk to
today's corpus; the two `.toml` moves land next, one per commit, each pairing its `git mv`
with the one constant that resolves it; the four `.md` moves land last, in one commit, because
DOC001 cannot pass with the move half-done (inventory Section 7, row 4) -- the file move, the
worktree guard fix, the `[retired.allow_after]` fix, the two behavioural path comparisons in
`scripts/docsync/integrity.py`, and the citation sweep across every always-scanned live
document all have to land together or the tree sits red between commits, which Global
Constraints forbid. Task 7 then repoints PR #242's workflow at the moved documents, and Task
8 makes every docsync diagnostic print the declared document path instead of a bare root
name (owner ruling, 2026-09-24).

**Tech Stack:** Python 3.13 stdlib (`tomllib`, `pathlib`, `dataclasses`), pytest. No new
dependency.

## Global Constraints

Reused from `docs/superpowers/plans/2026-09-21-batch23-wp0-foundation.md` "Global
Constraints", unchanged, plus one addition:

- **Qualified interpreter only.** The repository's one `.venv/` (`AGENTS.md` "Environment
  Setup"): `.venv/bin/python -m pytest` and `.venv/bin/pre-commit` on Linux, as
  `.superpowers/cloud-kit/constraints.md` R10 and its gates block (2b) state; on the owner's
  Windows machine, the `.venv/Scripts/` equivalents. Commands below use the Linux form. Never
  bare `pip`, never a second venv.
- **No new dependency, no version change.**
- **Nothing may break the repository.** No task may leave `pytest -q` red,
  `doc_state_sync.py --check` non-zero, `pre-commit run --all-files` failing, or the frontend
  gate failing. A cloud sandbox cannot run the frontend gate
  (`docs/history/reports/HANDOFF_2026-09-24.md` section 2): a task that needs it (Task 4)
  runs it locally or relies on CI's `quality-gate` on the pushed commit, and its Section 4
  entry says which.
- **No existing test is modified, except where a task says so and says why.**
- **Do not touch other agents' uncommitted work.** Run `git status --short` before each task;
  anything already untracked or modified that the task did not create belongs to someone
  else. Never stage, revert or delete it. (The owner's machine carries a standing untracked
  set; a fresh cloud clone carries none.)
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

Reused from the foundation plan, with the probe corpus under `/tmp/ssprobe` (cloud-kit
R10). A failing green is worse than a red; a unit test over an invented fixture is not proof
a gate works. Every task in this plan that changes a check, a path resolver or a diagnostic
(Tasks 2, 3, 4, 5, 6, 8) is accepted only on a **live probe**:

1. Build a throwaway corpus from the committed tree, at a short path:
   ```bash
   mkdir -p /tmp/ssprobe && cd /tmp/ssprobe && rm -rf corpus && mkdir corpus
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
   entry. Delete `/tmp/ssprobe` afterwards.

A task's own unit tests are written first, as the regression guard; the probe is the proof.

## File Structure

| File | Change |
|---|---|
| `PLAYBOOK.md`, `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` | Merge conflicts resolved when `origin/main` is merged in (Task 0). |
| `scripts/docsync/declarations.py` | New `DocumentsConfig` dataclass, `_validate_documents`, `_documents_config`, `load_documents_config`; `load_declarations`, every `load_*_config` and `collect_declaration_issues` gain an optional `config_path` kwarg (Tasks 2-3); `DECLARATIONS_FILENAME` value and the `_TOP_LEVEL_SCHEMA` comment change in Task 5. |
| `scripts/docsync/integrity.py` | `collect_integrity_issues` gains three optional path kwargs (`document_paths`, `playbook_relative_path`, `findings_relative_path`, Task 2) and `config_path` (Task 3); new `resolved_live_document_paths(documents)` helper; two `.docsync.toml` comments (Task 5); every diagnostic path label threads the declared path (Task 8). |
| `scripts/docsync/closeout.py` | The `.docsync.toml` remediation string (Task 5); the four `"PLAYBOOK.md"` diagnostic labels (Task 8). |
| `scripts/docsync/findings.py`, `scripts/docsync/archives.py` | The `.docsync.toml` remediation string and comment (Task 5); `findings.py`'s eleven `ACTIVE_PATH` diagnostic labels (Task 8). |
| `scripts/docsync/cli.py` | New `--config` argument and module-level `CONFIG_PATH` (Task 3); the five `load_archive_config`/`load_closeout_config` call sites and the two `collect_integrity_issues` call sites gain the new kwargs; `PLAYBOOK_PATH` and `FINDINGS_PATH` give way to paths read from `[documents]` (Task 6). |
| `scripts/docsync/renderer.py` | The two status-block `PLAYBOOK.md` lines and `SIDE_ARCHIVE_PREFIX` (Task 6). |
| `scripts/dev/docsync_preflight.py` | `CONTROL_PLANE_FILES` entry and its comment change from `.docsync.toml` to `config/docsync.toml` (Task 5). |
| `scripts/dev/frontend_gate.py` | `CHECK_MANIFEST_PATH`, its comment and its one error string move to `config/` (Task 4); the `AGENT_NOTES.md` docstring citation (Task 6). |
| `scripts/dev/_worktree_guard_inspection.py`, `scripts/dev/_worktree_guard_diagnostics.py` | The `PLAYBOOK.md` read and its display label move to `docs/agents/PLAYBOOK.md` (Task 6). |
| `config/docsync.toml`, `config/frontend_gate_checks.toml` | New locations (`git mv`, Tasks 4-5); `config/docsync.toml` gains a `[documents]` table (Task 6). |
| `docs/agents/PLAYBOOK.md`, `FINDINGS.md`, `AGENT_NOTES.md`, `HANDOFF_PROMPT.md` | New locations (`git mv`, Task 6). |
| `.pre-commit-config.yaml` | The top-level `exclude` stops hiding `docs/agents/` (Task 6, owner ruling 2026-09-24). |
| `.github/workflows/repo-assist.md` and its compiled `.lock.yml` | `allowed-files` and prose repointed, then recompiled (Task 7). |
| Tests | Named per task: the declarations-file fixtures (Task 5), the worktree-guard fixtures, the renderer status-block tests and the `sync_env` monkeypatch (Task 6). |
| Every always-scanned live document, plus `DEVELOPMENT.md`, `docs/AGENT_DOC_MAP.md`, `docs/agents/domain.md`, `docs/agents/global-rules.md`, `docs/agents/issue-tracker.md`, `.superpowers/cloud-kit/constraints.md`, `PRODUCT.md`, `docs/ARCHITECTURE.md`, `docs/architecture/*.md`, `docs/design/RECONCILIATION.md`, `docs/history/reports/HANDOFF_2026-09-24.md` | Citations repointed (Task 6). |

---

### Task 0: Merge `origin/main` into this branch

Owner ruling, 2026-09-24: PR #242 merged into `main` as `707eed6` and this branch does not
contain it. Merge it in before any file moves, so its workflow and its Section 4 entry move
with the documents. A normal merge commit: no rebase, no history rewrite.

**Files:**
- Merge-conflict resolution: `PLAYBOOK.md` (Section 4 only),
  `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`
- Arrive cleanly from `main`: `.github/workflows/repo-assist.md`,
  `.github/workflows/repo-assist.lock.yml`, `.github/aw/actions-lock.json`, `.gitattributes`,
  and a `.github/copilot-instructions.md` line byte-identical to this branch's

- [x] **Step 1: Confirm the conflict set before merging**

  ```bash
  git fetch origin main
  git merge-tree --write-tree --name-only HEAD origin/main
  ```
  Expected: exactly `PLAYBOOK.md` and `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`
  listed as conflicted (verified at `151717d` and again at `85f47a0`). Any other conflicted
  path means `main` moved: stop and report it to the controller.

- [x] **Step 2: Merge and resolve**

  ```bash
  git merge --no-ff --no-commit origin/main
  ```
  Both conflicts are the same shape: each side added untagged entries after the
  current-batch end marker. Keep every entry from both sides, newest first, with no text
  changed inside any entry; then run `doc_state_sync.py --fix` and let it settle the rotation
  (Lesson L1). Never move an entry across the DOCSYNC markers by hand.

- [x] **Step 3: Section 4 entry, gates, commit**

  In PLAYBOOK Section 3's "Next action" order list, item 3, add after the root-cleanup
  sentences: "Its Task 0 (`origin/main` merged in, bringing PR #242) is done, YYYY-MM-DD."
  Add one untagged Section 4 entry directly after the current-batch end marker, headed
  `### YYYY-MM-DD - main is merged in before the root cleanup`, opening with the
  cloud-kit R1 sentence (Part B). Then `--fix`, `pytest -q`, `pre-commit run --all-files`,
  `--check`. Stage the two resolved files, the files that arrived from `main`, and anything
  `--fix` rotated, by name.

  ```bash
  git commit -m "chore(merge): Merge main into feat/batch23-wp0-hygiene"
  ```

**Acceptance:** the merge commit's parents are the branch head and `origin/main`; every
Section 4 entry from both sides survives, in date order; `.github/workflows/repo-assist.md`
exists on the branch; all four gates pass.

---

### Task 1: Record the scope change before touching anything

**Proposal Rule 1** (`AGENTS.md`): scope changes to an open batch are recorded before
execution. Part B of `BATCH23_DEFINITION.md` WP-0 does not yet list the root cleanup; add it.

**Files:**
- Modify: `BATCH23_DEFINITION.md` (Part B, `#### Part B -- Reconcile what earlier batches left
  open`)
- Modify: `PLAYBOOK.md` Section 3, "Next action" ordered list, item 3's closing sentence
  ("Next is the root-cleanup task the owner added on 2026-09-24.")

- [x] **Step 1: Add the Part B bullet**

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

- [x] **Step 2: Repoint PLAYBOOK Section 3**

  In the "Next action" order list, item 3, replace everything from "Next is the root-cleanup
  task the owner added on 2026-09-24." to the end of that item (the sentences describing the
  plan as a draft or under review, and Task 0's progress note) with:

  ```
  Next is the root-cleanup plan,
  `docs/superpowers/plans/2026-09-24-batch23-wp0-root-cleanup.md`, approved
  YYYY-MM-DD: Task 0 (`main` merged in) and Task 1 are done; Tasks 2-8 remain.
  ```
  Keep `**Next action:** WP-0 is next.` exactly (cloud-kit R2).

- [x] **Step 3: Mark this plan approved**

  In this file, delete the status paragraph under the title and the "Revisions applied"
  section at the end. The plan is committed in its approved form in this same commit.

- [x] **Step 4: Section 4 entry, gates and commit**

  Add one untagged Section 4 entry directly after the current-batch end marker, headed
  `### YYYY-MM-DD - The root cleanup joins WP-0 Part B`, opening with the cloud-kit R1
  sentence (Part B). Then `doc_state_sync.py --fix`; `pytest -q`; `pre-commit run
  --all-files`; `doc_state_sync.py --check`. Stage `BATCH23_DEFINITION.md`, `PLAYBOOK.md`,
  this plan, and anything `--fix` rotated, by name.

  ```bash
  git commit -m "docs(batch23): Add the root-cleanup task to WP-0 Part B"
  ```

**Acceptance:** `doc_state_sync.py --check` exits 0; `BATCH23_DEFINITION.md` Part B lists the
task; PLAYBOOK Section 3 names this plan's path; this plan carries no status paragraph and no
"Revisions applied" section.

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

- [x] **Step 1: Write the failing tests**

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

- [x] **Step 2: Run the new tests to verify they fail**

  ```
  .venv/bin/python -m pytest tests/test_docsync_declarations.py::TestDocumentsConfig tests/test_docsync_integrity.py -k resolved_live_document_paths -v
  ```
  Expected: `ImportError`/`AttributeError` -- `DocumentsConfig`, `load_documents_config`,
  `resolved_live_document_paths` and the `document_paths`/`playbook_relative_path` kwargs do
  not exist yet.

- [x] **Step 3: Implement `DocumentsConfig` in `declarations.py`**

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

- [x] **Step 4: Implement `resolved_live_document_paths` in `integrity.py`**

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

- [x] **Step 5: Give `collect_integrity_issues` its three optional kwargs**

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

  The diagnostic path labels (the fourteen `PLAYBOOK.md` and twelve `FINDINGS.md` sites Task
  8 lists) are **left unchanged in this task**: they change only the printed `path`
  of a diagnostic, never which document is scanned or whether a check fires. Task 8 threads
  the declared path into them (owner ruling, 2026-09-24).

- [x] **Step 6: Run the tests to verify they pass**

  ```
  .venv/bin/python -m pytest tests/test_docsync_declarations.py tests/test_docsync_integrity.py tests/test_docsync_cli.py -v
  ```
  Expected: PASS, including the two existing `TestLiveDocumentPathsSingleSource` tests in
  `tests/test_docsync_cli.py`, unmodified -- they compare the bare default tuples to each
  other, which this task never changes.

- [x] **Step 7: Full gates and live probe**

  `pytest -q`; `pre-commit run --all-files` will refuse the commit at the preflight (this task
  touches `scripts/docsync/`); run `doc_state_sync.py --check` directly first to confirm exit
  0, then commit with the documented escape.

  Live probe. The CLI does not read document paths from `[documents]` until Task 6, but
  `collect_declaration_issues` validates every table eagerly, so the table's admission is
  observable now. In `/tmp/ssprobe/corpus`:
  - **Baseline (before this task's code):** append `[documents]\nplaybook = "PLAYBOOK.md"\n`
    to `.docsync.toml` in a corpus built from the pre-task commit; `--check` refuses it as an
    unknown table (record the exit code and message).
  - **Red:** in a corpus built from this task's tree, append
    `[documents]\nnotebook = "x.md"\n`; `--check` refuses it, naming the unknown key
    `'notebook'` (record the exit code).
  - **Near-miss green:** reset, then append `[documents]\nplaybook = "PLAYBOOK.md"\n`;
    `--check` prints the same summary as the unmodified corpus and exits 0.
  Task 6 Step 10 proves the path-honouring half once the CLI consumes the table.

- [x] **Step 8: Commit**

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
- Modify: `scripts/docsync/declarations.py` (`load_declarations`, `collect_declaration_issues`)
- Modify: `scripts/docsync/integrity.py` (`collect_integrity_issues` forwards `config_path`)
- Test: `tests/test_docsync_cli.py`, `tests/test_docsync_declarations.py`

**Interfaces:**
- Consumes: `declarations.load_declarations(repo_root, *, config_path=None)` (Task 2).
- Produces: `cli._build_parser()` gains `--config`; a module-level `cli.CONFIG_PATH` that
  `main()` sets for the length of one invocation;
  `declarations.collect_declaration_issues(..., config_path=None)` and
  `integrity.collect_integrity_issues(..., config_path=None)`.

- [ ] **Step 1: Write the failing tests**

  In `tests/test_docsync_declarations.py`, add (an explicit path that is missing must be an
  error: the absent-file-means-no-declarations rule is for the default path only, or a
  mistyped `--config` would run every check with nothing declared and pass):

  ```python
  class TestExplicitConfigPath:
      def test_explicit_missing_path_is_refused(self, tmp_path: Path):
          from docsync.declarations import DeclarationError, load_declarations

          with pytest.raises(DeclarationError, match="nowhere.toml"):
              load_declarations(tmp_path, config_path=tmp_path / "nowhere.toml")

      def test_default_missing_path_still_means_no_declarations(self, tmp_path: Path):
          from docsync.declarations import load_declarations

          assert load_declarations(tmp_path) == {}

      def test_explicit_path_is_read_instead_of_the_default(self, tmp_path: Path):
          from docsync.declarations import load_declarations

          alt = tmp_path / "alt.toml"
          alt.write_text("[options]\n", encoding="utf-8")
          assert load_declarations(tmp_path, config_path=alt) == {"options": {}}
  ```

  In `tests/test_docsync_cli.py`, beside `TestMainArgs`, add a class that drives `main()`
  in-process through the `sync_env` fixture (which chdirs into a synthetic corpus whose
  declarations file passes `--check`):

  ```python
  class TestConfigOverride:
      def test_config_flag_defaults_to_none(self):
          from docsync.cli import _build_parser

          assert _build_parser().parse_args(["--check"]).config is None

      def test_config_selects_the_declarations_file_every_check_reads(
          self, sync_env, monkeypatch, capsys
      ):
          # sync_env's raw corpus fails --check with DOC005 (exit 1; see
          # TestMainArgs.test_check_fails_on_stale_session_context). A copy of its
          # declarations with an unknown table is refused as malformed input (exit 2)
          # instead, which can only happen if --config changed the file read.
          from docsync import cli as cli_mod
          from docsync.declarations import DECLARATIONS_FILENAME

          default = sync_env / DECLARATIONS_FILENAME
          alt = sync_env / "alt.toml"
          alt.write_text(
              default.read_text(encoding="utf-8") + "\n[nonsense]\n", encoding="utf-8"
          )
          monkeypatch.setattr("sys.argv", ["doc_state_sync.py", "--check"])
          assert cli_mod.main() == 1
          capsys.readouterr()
          monkeypatch.setattr(
              "sys.argv", ["doc_state_sync.py", "--check", "--config", str(alt)]
          )
          assert cli_mod.main() == 2
          assert "nonsense" in capsys.readouterr().err

      def test_main_restores_config_path_after_the_run(self, sync_env, monkeypatch):
          # Tests call main() in-process; a --config from one call must not leak into
          # the next test's direct calls.
          from docsync import cli as cli_mod
          from docsync.declarations import DECLARATIONS_FILENAME

          monkeypatch.setattr(
              "sys.argv",
              [
                  "doc_state_sync.py",
                  "--check",
                  "--config",
                  str(sync_env / DECLARATIONS_FILENAME),
              ],
          )
          cli_mod.main()
          assert cli_mod.CONFIG_PATH is None
  ```

  (`DeclarationError` subclasses `SyncError`, which `main()` turns into exit 2; the argv
  form matches `TestMainArgs`. If the unknown-table message goes to stdout rather than
  stderr, assert on the stream it uses.)

- [ ] **Step 2: Run to verify they fail**

  ```
  .venv/bin/python -m pytest tests/test_docsync_declarations.py::TestExplicitConfigPath tests/test_docsync_cli.py::TestConfigOverride -v
  ```
  Expected: FAIL -- `load_declarations` has no `config_path` refusal yet, and `argparse`
  rejects `--config`.

- [ ] **Step 3: Add the argument and thread it**

  In `declarations.py`, make `load_declarations` refuse an explicit path that is not a file,
  and name the path it actually read in its errors:

  ```python
  def load_declarations(repo_root: Path, *, config_path: Path | None = None) -> dict:
      """Read the declarations file, or return nothing if there is none.

      A repository with no declarations file at the default path is not an error.
      An explicit ``config_path`` that does not exist is: a mistyped --config
      would otherwise run every check with nothing declared, and pass.
      """
      path = config_path if config_path is not None else repo_root / DECLARATIONS_FILENAME
      if not path.is_file():
          if config_path is not None:
              raise DeclarationError(f"--config names {path}, which is not a file.")
          return {}
      ...  # the TOML error message names `path`, not DECLARATIONS_FILENAME
  ```

  Give `collect_declaration_issues` a `config_path: Path | None = None` kwarg, passed to its
  `load_declarations` call. Give `collect_integrity_issues` the same kwarg and forward it to
  its three reads: `collect_declaration_issues`, `load_findings_config` and
  `load_closeout_config`.

  In `cli.py`'s `_build_parser()`, add:

  ```python
  parser.add_argument(
      "--config",
      metavar="PATH",
      help=(
          "Path to the declarations file, overriding the repository default "
          f"({DECLARATIONS_FILENAME})."
      ),
  )
  ```

  (Interpolating `DECLARATIONS_FILENAME` keeps the help text true across Task 5's move.)

  Add a module-level `CONFIG_PATH: Path | None = None` beside `REPO_ROOT`, with a comment
  saying `main()` sets it for one invocation. `REPO_ROOT` is a true constant, so there is no
  existing pattern to copy: `main()` must declare `global CONFIG_PATH`, set it from
  `args.config` before any mode runs, and restore the previous value in a `finally`. Without
  the `global`, the assignment binds a local and every other function reads `None`; without
  the `finally`, an in-process `main()` call in one test leaks its `--config` into the next
  (`tests/test_docsync_cli.py` calls `cli_mod.main()` directly).

  Pass `config_path=CONFIG_PATH` at every declarations read in `cli.py`, named by enclosing
  function: `load_archive_config(REPO_ROOT)` in `_archive_store`, `_drift_updates`,
  `_close_batch` and `_maintain_archives`; `load_closeout_config(REPO_ROOT)` in
  `_close_batch`; and both `collect_integrity_issues(...)` calls (`_collect_issues`,
  `_close_batch`). Then grep `cli.py` for `load_declarations(`, `load_.*_config(` and
  `collect_.*_issues(` and confirm no read is left without it.

- [ ] **Step 4: Run to verify they pass**

  ```
  .venv/bin/python -m pytest tests/test_docsync_cli.py tests/test_docsync_declarations.py tests/test_docsync_integrity.py -v
  ```

- [ ] **Step 5: Gates and live probe**

  `pytest -q`; `doc_state_sync.py --check` at exit 0 first (this touches `scripts/docsync/`).

  Live probe, in `/tmp/ssprobe/corpus`:
  - **Red 1 (the flag changes the file read):** `cp .docsync.toml alt.toml` and append
    `[nonsense]` to `alt.toml` only. `--check` alone exits 0 with the corpus's usual summary;
    `--check --config alt.toml` is refused, naming the unknown table.
  - **Red 2 (a mistyped path is not a green):** `--check --config nowhere.toml` is refused,
    naming `nowhere.toml`.
  - **Near-miss green:** reset; `cp .docsync.toml alt.toml` unchanged;
    `--check --config alt.toml` prints the same summary as `--check` and exits 0.

- [ ] **Step 6: Section 4 entry and commit**

  One untagged Section 4 entry (cloud-kit R1), with the probe table.

  ```bash
  SKIP=doc-state-sync-check git commit -m "feat(docsync): Add a --config override"
  ```

**Acceptance:** `--config PATH` changes which declarations file every mode and every check
reads (the declared-fact checks included); a `--config` naming a missing file is refused,
while a missing default file still means "nothing declared"; `CONFIG_PATH` is `None` again
after `main()` returns.

---

### Task 4: Move `frontend_gate_checks.toml` to `config/`

Independent of docsync entirely (inventory Section 7, row 7: no shared code path). The
riskiest single step in this plan by import-time coupling (inventory Section 7, row 1) --
the file move and the constant update must be the same commit.

**Files:**
- Modify: `scripts/dev/frontend_gate.py`
- Modify: `config/frontend_gate_checks.toml` (its header comment, after the move)
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

  The manifest's own header comment says the same thing ("it sits here at the root, the same
  split `.docsync.toml` uses: facts here, mechanism in `scripts/`"). Rewrite it to say the
  file sits under `config/`, and name the docsync declarations file without a path until
  Task 5 moves it (Task 5 Step 5 then names `config/docsync.toml`).

  Update the one hard-coded location in `_load_check_manifest`'s `FrontendGateError`
  messages: `"Restore frontend_gate_checks.toml at the repository root."` becomes `"Restore
  config/frontend_gate_checks.toml."`. Its other two raises interpolate `{path}` and need no
  edit. Grep `frontend_gate.py` for `repository root` and `frontend_gate_checks` afterwards:
  only `CHECK_MANIFEST_PATH` and this message may name the file.

- [ ] **Step 2: Run the collection-dependent tests**

  ```
  .venv/bin/python -m pytest tests/scripts/dev/test_frontend_gate*.py -v
  ```
  (twelve modules at `85f47a0`; every one must still collect and pass.)

- [ ] **Step 3: Full gates**

  `pytest -q`; `python scripts/dev/frontend_gate.py --help` (or equivalent smoke invocation)
  to prove the module still imports cleanly outside pytest; `pre-commit run --all-files`;
  `doc_state_sync.py --check`. This task does not touch `scripts/docsync/`, so the normal
  preflight path applies -- no `SKIP=` needed.

  The frontend gate itself reads the moved manifest, so it must pass on this commit: run
  `.venv/bin/python scripts/dev/frontend_gate.py` locally, or, in a cloud sandbox that cannot
  run it, rely on CI's `quality-gate` job for the pushed commit. The Section 4 entry names
  which, with the gate's last line or the CI run.

- [ ] **Step 4: Live probe**

  In `/tmp/ssprobe/corpus`: **red** -- `git rm config/frontend_gate_checks.toml && git commit
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

Every test fixture that writes a declarations file must follow the file, or it writes where
docsync no longer reads, and `load_declarations` treats a missing default file as "nothing
declared". A controller probe of the draft (the move plus the two constants alone, at
`85f47a0`) left `--check` at exit 0 but failed 25 docsync tests: the 2 this task always named
plus 23 from fixtures it did not. Fix the class, not the instance (`AGENTS.md` anti-pattern 11).

**Files:**
- `git mv .docsync.toml config/docsync.toml`
- Modify: `scripts/docsync/declarations.py` (`DECLARATIONS_FILENAME`; the `_TOP_LEVEL_SCHEMA`
  comment at `:219`)
- Modify: `scripts/dev/docsync_preflight.py` (`CONTROL_PLANE_FILES` and its comment's example)
- Modify: `scripts/docsync/findings.py` (`collect_rot_issues`' DOC023 remediation string),
  `scripts/docsync/closeout.py` (`_admission_issue`'s DOC019 remediation string),
  `scripts/docsync/archives.py` (comment), `scripts/docsync/integrity.py` (two comments near
  the declared-fact and DOC019 blocks)
- Modify: the live prose citing `.docsync.toml` (Step 5)
- Test: `tests/scripts/dev/test_docsync_preflight.py` (`test_control_plane_prefix_matching`,
  `test_staged_preflight_against_real_docsync_checker`)
- Test (fixtures, repointed at the `DECLARATIONS_FILENAME` symbol): `tests/conftest.py`
  (`sync_env`), `tests/test_docsync_cli.py` (`CORPUS_*` / `_make_corpus` keys),
  `tests/test_docsync_integrity.py` (`_write_closeout_boundary` and
  `test_doc023_honours_the_repositorys_grandfather_list`)

- [ ] **Step 1: Repoint every declarations fixture at the symbol, before the move**

  Find every test that writes a declarations file by literal name:

  ```bash
  git grep -n -F '.docsync.toml' -- tests
  ```
  At `85f47a0` the writers are `tests/conftest.py:162`, `tests/test_docsync_cli.py` (keys at
  `:718`, `:893`, `:1081`, `:1331`, `:1501`, `:1538`, `:1598`),
  `tests/test_docsync_integrity.py` (`_write_closeout_boundary`, and the grandfather-list test
  near `:1907`) and `tests/scripts/dev/test_docsync_preflight.py:630`. Change each writer to
  build its path from `DECLARATIONS_FILENAME` (imported from `docsync.declarations`) and to
  create the parent directory first (`path.parent.mkdir(parents=True, exist_ok=True)`);
  `_make_corpus`'s own `_write` helper already does. Rows that assert on the
  preflight's name matching (`test_control_plane_prefix_matching`, `:152` and the
  `.docsync.tomlx` row) are not writers: Step 2 handles them.

  ```
  .venv/bin/python -m pytest -q -p no:cacheprovider tests/test_docsync_cli.py tests/test_docsync_logic.py tests/test_docsync_integrity.py tests/scripts/dev/test_docsync_preflight.py
  ```
  Expected: PASS, unchanged count -- the symbol still equals `.docsync.toml`, so this is a
  pure parity step. These are named test edits; the commit body lists them and says why.

- [ ] **Step 2: Update the name-matching test first**

  In `tests/scripts/dev/test_docsync_preflight.py`, in `test_control_plane_prefix_matching`'s
  parametrize list, replace `(".docsync.toml", True)` with `("config/docsync.toml", True)`,
  add a new row `(".docsync.toml", False)` (the retired root name is no longer special), and
  replace `(".docsync.tomlx", False)` with `("config/docsync.tomlx", False)` (keeping the
  exact-match negative control at the new name).

  ```
  .venv/bin/python -m pytest tests/scripts/dev/test_docsync_preflight.py::test_control_plane_prefix_matching -v
  ```
  Expected: FAIL -- `"config/docsync.toml"` is not yet in `CONTROL_PLANE_FILES`, and
  `".docsync.toml"` still is.

- [ ] **Step 3: Move the file and update both constants**

  ```bash
  mkdir -p config
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
  and rewrite the comment above it so its exact-match example names `config/docsync.tomlx`
  and `config/docsync.toml`.

- [ ] **Step 4: Repoint the diagnostics and comments that name the file**

  - `scripts/docsync/findings.py`, `collect_rot_issues`: the DOC023 remediation tells the
    reader to edit `` `.docsync.toml` ``; name `` `config/docsync.toml` ``. Better, interpolate
    `DECLARATIONS_FILENAME` so the next move cannot strand it.
  - `scripts/docsync/closeout.py`, `_admission_issue`: the DOC019 remediation ("Lower
    `admit_from_batch` in .docsync.toml ..."), the same way.
  - Comments: `scripts/docsync/declarations.py` (the `_TOP_LEVEL_SCHEMA` note),
    `scripts/docsync/archives.py`, `scripts/docsync/integrity.py` (two, near the
    declared-fact and DOC019 blocks).

  Then `git grep -n -F '.docsync.toml' -- scripts` must print only lines that deliberately
  name the retired spelling (none are expected).

- [ ] **Step 5: Sweep the live prose, by grep (no gate catches it)**

  The controller probe showed DOC001 does not resolve a bare `` `.docsync.toml` `` citation, so
  `--check` stays green while every live mention goes stale. Sweep by hand:

  ```bash
  git grep -n -F '.docsync.toml' -- ':!docs/history' ':!docs/logarchive' ':!tests' ':!scripts'
  ```
  Rewrite every present-tense claim about where the file is, or a pointer telling the reader
  to edit it, to `config/docsync.toml`. Leave as written: dated `PLAYBOOK.md` Section 4
  entries, closed or dated finding records describing a past edit (e.g. `FINDINGS.md`'s
  "corrected in `.docsync.toml` (2026-09-24, Task 5 ..." note), and plans or specs of
  completed work. At `85f47a0` the live set is: `AGENTS.md`, `AGENT_NOTES.md` (3),
  `DEVELOPMENT.md` (4), `docs/ARCHITECTURE.md`, `docs/agents/global-rules.md`,
  `docs/architecture/documentation-tooling.md` (7, including its mermaid node label and the
  sentence that says the file sits "at the repository root"), `FINDINGS.md` (open records
  only), `.superpowers/cloud-kit/constraints.md` (R7), `.pre-commit-config.yaml` (comment),
  `config/frontend_gate_checks.toml` (header comment), `scrobblescope/heatmap.py` (comment)
  and `static/css/tailwind.src.css` (comment). The last one is under `static/`: rebuild with
  the `tailwind-css-drift` hook and run the frontend gate, or rely on CI's `quality-gate`, as
  Task 4 does, and say which.

- [ ] **Step 6: Run the updated tests**

  ```
  .venv/bin/python -m pytest -q -p no:cacheprovider tests/scripts/dev/test_docsync_preflight.py tests/test_docsync_declarations.py tests/test_docsync_cli.py tests/test_docsync_logic.py tests/test_docsync_integrity.py
  ```
  Expected: PASS, including `test_staged_preflight_against_real_docsync_checker` now that
  Step 1 made it write its declarations at `config/docsync.toml` inside its temporary repo.
  `PLAYBOOK.md`, `AGENTS.md`, `HANDOFF_PROMPT.md`, `AGENT_NOTES.md` and `FINDINGS.md` stay at
  that fixture's root in *this* task; Task 6 decides whether they follow.

- [ ] **Step 7: Live probe**

  In `/tmp/ssprobe/corpus`, built from this task's tree:
  - **Faithful copy:** `--check` prints the same summary as the worktree (the declarations
    are read from `config/docsync.toml`; a copy that silently read none would still pass, so
    also confirm a declared check is live: append a `[nonsense]` table to
    `config/docsync.toml` and see `--check` refuse it, then reset).
  - **Red (the new name is control plane):** edit a comment in `config/docsync.toml` only,
    `git add` it, run `python scripts/dev/docsync_preflight.py --staged`. Expected: exit 3,
    the control-plane refusal, naming `config/docsync.toml`.
  - **Near-miss green (the retired name is not):** reset; create a root `.docsync.toml` with
    any content, `git add` only it, run the same command. Expected: no control-plane refusal
    (exit 0 on this clean corpus).
  (Staging a `scripts/docsync/` edit alone is refused under either name, since that
  directory is matched as a prefix, so it cannot serve as the near-miss.)

- [ ] **Step 8: Gates, Section 4 entry and commit**

  One untagged Section 4 entry (cloud-kit R1), with the probe table and the named test
  edits. This touches the control plane: `doc_state_sync.py --check` directly first (exit
  0), then:

  ```bash
  SKIP=doc-state-sync-check git commit -m "chore(docsync): Move .docsync.toml under config/"
  ```

**Acceptance:** `config/docsync.toml` is the declarations file docsync reads by default;
`CONTROL_PLANE_FILES` recognizes it and no longer recognizes the root name; every test
fixture writes its declarations where docsync reads them (no suite count change beyond the
parametrize row); no live, present-tense citation names `.docsync.toml`; the probe
behaves as specified.

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
- Modify: `scripts/docsync/cli.py` (`_read_live_documents`, every `PLAYBOOK_PATH` /
  `FINDINGS_PATH` read and write, and the two `collect_integrity_issues` call sites now use
  the declared paths)
- Modify: `scripts/dev/_worktree_guard_inspection.py`
- Modify: `scripts/dev/_worktree_guard_diagnostics.py` (display label)
- Modify: `scripts/docsync/renderer.py` (`_build_status_block`'s two `` `PLAYBOOK.md` `` lines
  and `SIDE_ARCHIVE_PREFIX`)
- Modify: `scripts/dev/frontend_gate.py` (the `` `AGENT_NOTES.md` `` citation in
  `_load_check_manifest`'s docstring)
- Modify: `.pre-commit-config.yaml` (top-level `exclude`, Step 9, owner ruling 2026-09-24)
- Modify: every always-scanned live document's citations (Step 7)
- Modify: `docs/AGENT_DOC_MAP.md`, `docs/agents/domain.md`, `docs/agents/global-rules.md`,
  `docs/agents/issue-tracker.md`, `DEVELOPMENT.md`, `PRODUCT.md`, `docs/ARCHITECTURE.md`,
  `docs/architecture/*.md` citing any of the four, `docs/design/RECONCILIATION.md` (one
  `` `FINDINGS.md` `` citation at `:667`, confirmed at `85f47a0`),
  `.superpowers/cloud-kit/constraints.md`, and the entry-point handoff
  `docs/history/reports/HANDOFF_2026-09-24.md` (Step 8)
- Test: `tests/scripts/dev/test_worktree_guard_playbook.py`
  (`test_the_repository_playbook_parses`)
- Test: the worktree-guard fixtures (Step 3), `tests/conftest.py` (`sync_env`'s
  `PLAYBOOK_PATH` monkeypatch, Step 5), `tests/test_docsync_renderer.py` (the two status-block
  tests, Step 6)

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
  .venv/bin/python -m pytest tests/scripts/dev/test_worktree_guard_playbook.py -v
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
  .venv/bin/python -m pytest tests/scripts/dev/test_worktree_guard_playbook.py tests/scripts/dev/test_worktree_guard_base_ref.py tests/scripts/dev/test_worktree_guard_inspection.py tests/scripts/dev/test_worktree_guard_subject.py tests/scripts/dev/test_worktree_guard_topology.py tests/scripts/dev/test_worktree_guard_cli_e2e.py -v
  ```
  Expected: PASS. `test_worktree_guard_cli_e2e.py` edits nothing itself but drives the real
  inspection through `worktree_guard_fakes.repository()`, so it proves the fakes fix end to
  end. The synthetic `tmp_path`-based fixtures (`worktree_guard_fakes.py:43`,
  `test_worktree_guard_base_ref.py:55`, `test_worktree_guard_inspection.py:27-28,51`,
  `test_worktree_guard_subject.py:124`, `test_worktree_guard_topology.py:43` at `85f47a0`)
  write `repo.joinpath("PLAYBOOK.md")` against a
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

  Add one helper beside `_read_lines`, and read every document path through it:

  ```python
  def _documents() -> DocumentsConfig:
      """Return the document paths declared for this invocation's config file."""
      return load_documents_config(REPO_ROOT, config_path=CONFIG_PATH)
  ```
  (Reading a small TOML file a few times per run is cheaper than threading one object
  through every mode; `CONFIG_PATH` already makes every read agree -- Task 3.)

  - `_read_live_documents()` reads `REPO_ROOT / relative` for each path in
    `resolved_live_document_paths(_documents())` instead of `LIVE_DOCUMENT_PATHS`.
    `LIVE_DOCUMENT_PATHS` itself stays, unchanged, as the default tuple that
    `TestLiveDocumentPathsSingleSource` compares.
  - Every `PLAYBOOK_PATH` and `FINDINGS_PATH` use becomes `REPO_ROOT / _documents().playbook`
    or `REPO_ROOT / _documents().findings`. At `85f47a0` they are `cli.py:284`, `:295`, `:460`,
    `:486`, `:636`, `:637`, `:782` and `:805` (reads and writes both); grep
    `PLAYBOOK_PATH\b\|FINDINGS_PATH\b` to confirm none is left, then delete the two
    constants, so nothing can read the retired default by accident.
  - In `_collect_issues` and `_close_batch`'s `collect_integrity_issues(...)` calls, pass:
    ```python
    document_paths=resolved_live_document_paths(documents),
    playbook_relative_path=documents.playbook,
    findings_relative_path=documents.findings,
    ```
    with `documents = _documents()` read once at the top of each function.
  - Add `resolved_live_document_paths`, `DocumentsConfig` and `load_documents_config` to the
    existing `from docsync.integrity import (...)` / `from docsync.declarations import (...)`
    blocks.

  **Named test edit:** `tests/conftest.py`'s `sync_env` monkeypatches
  `cli_module.PLAYBOOK_PATH` (`:141` at `85f47a0`). With the constant deleted, `setattr`
  raises; delete that one line. The fixture already chdirs into its corpus and writes no
  `[documents]` table, so the default relative `PLAYBOOK.md` resolves to the same file.

- [ ] **Step 6: The status block and the archive prologue stop naming a path**

  `scripts/docsync/renderer.py` renders two texts that cite `` `PLAYBOOK.md` ``:
  `_build_status_block`'s "- Source of truth: `PLAYBOOK.md` (Section 3 and Section 4)." (two
  copies) and `SIDE_ARCHIVE_PREFIX`'s "rotated out of `PLAYBOOK.md` Section 4". Hard-coding
  `docs/agents/PLAYBOOK.md` there would put a document path back into `scripts/docsync/`,
  which the owner's ruling rules out (paths are declared in `config/docsync.toml`); asked
  again on 2026-09-24, the owner restated that they do not want hard-coding and left the
  choice to the controller. Drop the path instead: "- Source of truth: PLAYBOOK Section 3 and Section 4." and "rotated out of
  PLAYBOOK Section 4". The hand-written line above the managed block in
  `.claude/SESSION_CONTEXT.md` Section 2 carries the real path (Step 7 repoints it).
  (Rejected alternative: thread the declared playbook path from `cli.py` through `logic.py`'s
  `_build_status_block` caller and turn `SIDE_ARCHIVE_PREFIX` into a function. It keeps a
  path in the generated text at the cost of a signature on three modules and a changed
  import in every test that uses the constant.)

  Consequences to handle in the same commit:
  - `SIDE_ARCHIVE_PREFIX` is a contract, not prose: `integrity.py` raises DOC004 unless
    `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`'s prologue equals it. Run `--fix` (it
    renders the archive through this constant when it writes it) and confirm the real
    archive's prologue matches; if `--fix` did not rewrite it, edit that one line by hand to
    match the constant exactly.
  - `.claude/SESSION_CONTEXT.md`'s managed status block is refreshed by `--fix`.
  - **Named test edits:** `tests/test_docsync_renderer.py`'s
    `test_declared_batch_with_no_entries_renders_as_open` (`:502`) and
    `test_between_batches_block_carries_the_count` (`:527`) copy the status-block line by
    value in a full-list `==`; update both to the new text. Tests that import
    `SIDE_ARCHIVE_PREFIX` by symbol need no edit.

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

  Citation style is settled: repository-root paths everywhere, including between files that
  share `docs/agents/` (DOC001 resolves citations from the repository root). Write
  `` `docs/agents/PLAYBOOK.md` `` even from `docs/agents/domain.md`.

  Sweep: `docs/AGENT_DOC_MAP.md` (routing table, 6+5+2+1 citations), `docs/agents/domain.md`,
  `docs/agents/global-rules.md`, `docs/agents/issue-tracker.md`, `DEVELOPMENT.md`,
  `PRODUCT.md`, `docs/ARCHITECTURE.md`, `docs/architecture/*.md` that cite any of the four
  (`documentation-tooling.md`, `development-cycle.md` per inventory Section 3),
  `docs/design/RECONCILIATION.md:667` (one `` `FINDINGS.md` `` citation),
  `scripts/dev/frontend_gate.py`'s `_load_check_manifest` docstring (`` `AGENT_NOTES.md` ``),
  and `.superpowers/cloud-kit/constraints.md` -- including its literal
  `grep -n "^### .*WP-[0-9]" PLAYBOOK.md` command: rewrite the command itself, not just the
  prose around it, or it silently finds nothing the next time an agent runs it.

  `docs/history/reports/HANDOFF_2026-09-24.md` is a dated report, but it is also the current
  entry point for a cold session until a newer handoff supersedes it. Repoint its commands
  and read-order paths (section 2's setup block, section 3's read list, section 8's grep
  trap); leave its narrative of past sessions as written.

  Confirmed at `85f47a0` to need no change: `README.md`, `DESIGN.md`, `CONTRIBUTING.md`,
  `DEPLOY.md`, `.github/copilot-instructions.md`, `.superpowers/cloud-kit/agents/*.md` (zero
  hits). Plans and specs of other work, and every `docs/history/` document other than the
  handoff, are point-in-time: leave them.

- [ ] **Step 9: Keep the moved documents under the file hooks** (owner ruling,
  2026-09-24: approved)

  `.pre-commit-config.yaml`'s top-level `exclude` lists `docs`, so after the move four hooks
  stop seeing the four documents: `trailing-whitespace`, `end-of-file-fixer`,
  `check-merge-conflict` and `detect-private-key`. (`doc-state-sync-check`,
  `tailwind-css-drift` and `worktree-alignment` are `always_run` with no filenames and are
  unaffected.) Losing `check-merge-conflict` on `docs/agents/PLAYBOOK.md` matters most: it is
  the file that conflicts on merges (Task 0).

  Change `docs` in that alternation to `docs(?!/agents/)`, so `docs/agents/` stays checked
  and the rest of `docs/` stays excluded. The lookahead goes before the slash because the
  pattern's `/` sits outside the group and is shared by every alternative: `docs/(?!agents/)`
  would then require `docs//` and silently un-exclude all of `docs/`. This also brings the
  three documents already in `docs/agents/` (`domain.md`, `global-rules.md`,
  `issue-tracker.md`) under the hooks for the first time; run `pre-commit run --all-files`
  and stage whatever the whitespace fixers change.

  Probe, in a scratch copy:
  - **Red:** plant a `<<<<<<< HEAD` line in `docs/agents/PLAYBOOK.md`;
    `pre-commit run check-merge-conflict --all-files` fails with the new exclude.
  - **Near-miss green:** move the planted line to `docs/history/reports/` (any file there);
    the same command passes, proving the rest of `docs/` is still excluded.
  - Before running either, check the pattern itself:
    `python -c "import re,yaml; p=yaml.safe_load(open('.pre-commit-config.yaml'))['exclude']; print([bool(re.search(p,x)) for x in ('docs/agents/PLAYBOOK.md','docs/history/x.md','docs/x.md')])"`
    prints `[False, True, True]`.

- [ ] **Step 10: Full test run, gates, and the live probe**

  ```
  .venv/bin/python -m pytest -q -p no:cacheprovider
  ```
  Expected: every test passes, including the updated worktree-guard fixtures, the renderer
  status-block tests and `test_the_repository_playbook_parses`.

  `doc_state_sync.py --check` directly first (this commit touches `scripts/docsync/`,
  control plane) -- expect exit 0 once Steps 4-9 are complete; a nonzero exit before the
  sweeps are finished is expected, per the "cannot pass with the move half-done" constraint.
  Do not commit until it is 0.

  Live probe, in `/tmp/ssprobe/corpus`, built from the working tree with this task's changes
  (`git archive $(git stash create) | tar -x -C corpus`, which leaves the stash list
  untouched), not from the last commit:
  - **Red 1 (allow_after silently stops applying):** revert only the four
    `[retired.allow_after]` keys in `config/docsync.toml` back to `"PLAYBOOK.md"`; run
    `--check`. Expected: DOC011 fires on the retired-claim text in
    `docs/agents/PLAYBOOK.md`'s Section 4 (a false positive, proving the key must follow the
    file).
  - **Near-miss green 1:** restore the `"docs/agents/PLAYBOOK.md"` keys; `--check` exits 0.
  - **Red 2 (worktree guard):** revert only `_worktree_guard_inspection.py`'s literal to
    `"PLAYBOOK.md"`; run `python scripts/dev/check_worktree_alignment.py --offline
    --base-ref <base>`. Expected: the metadata-unavailable diagnostic.
  - **Near-miss green 2:** restore the fix; the same command reads Section 3 successfully.
  - **Red 3 (DOC001 citation sweep):** leave one bare `` `PLAYBOOK.md` `` citation in
    `AGENTS.md`; run `--check`. Expected: DOC001 names it (a controller probe at `85f47a0`
    confirmed DOC001 flags an unresolved backticked `.md` basename).
  - **Near-miss green 3:** the same citation as `` `docs/agents/PLAYBOOK.md` ``; exit 0.
  - **Red 4 (`[documents]` is honoured, closing Task 2's probe):** set
    `playbook = "docs/agents/NOWHERE.md"` in `[documents]`; `--check` fails, naming the missing
    file (`_read_lines` raises rather than reading nothing).
  - **Near-miss green 4:** restore `playbook = "docs/agents/PLAYBOOK.md"`; exit 0.

- [ ] **Step 11: Section 4 entry and commit**

  One untagged Section 4 entry (cloud-kit R1) in `docs/agents/PLAYBOOK.md`, with the probe
  table, the named test edits and the pre-commit ruling. Stage by name every path this task
  changed -- `git status --short` must show nothing unstaged of this task's afterwards. At
  `85f47a0` that is: the four moved documents; `config/docsync.toml`;
  `scripts/docsync/cli.py`, `scripts/docsync/renderer.py`;
  `scripts/dev/_worktree_guard_inspection.py`, `scripts/dev/_worktree_guard_diagnostics.py`,
  `scripts/dev/frontend_gate.py`; `.pre-commit-config.yaml`;
  `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` (prologue, and any rotation);
  `AGENTS.md`, `BATCH23_DEFINITION.md`, `.claude/SESSION_CONTEXT.md`;
  `docs/AGENT_DOC_MAP.md`, `docs/agents/domain.md`, `docs/agents/global-rules.md`,
  `docs/agents/issue-tracker.md`, `DEVELOPMENT.md`, `PRODUCT.md`, `docs/ARCHITECTURE.md`,
  `docs/architecture/documentation-tooling.md`, `docs/architecture/development-cycle.md`,
  `docs/design/RECONCILIATION.md`, `docs/history/reports/HANDOFF_2026-09-24.md`,
  `.superpowers/cloud-kit/constraints.md`; and the tests `tests/conftest.py`,
  `tests/test_docsync_renderer.py`, `tests/scripts/dev/test_worktree_guard_playbook.py`,
  `tests/scripts/dev/worktree_guard_fakes.py`, `tests/scripts/dev/test_worktree_guard_base_ref.py`,
  `tests/scripts/dev/test_worktree_guard_inspection.py`,
  `tests/scripts/dev/test_worktree_guard_subject.py`,
  `tests/scripts/dev/test_worktree_guard_topology.py`.

  ```bash
  .venv/bin/python scripts/doc_state_sync.py --check   # confirm exit 0 first
  SKIP=doc-state-sync-check git commit -m "chore(docs): Move the four agent documents to docs/agents/"
  ```
  (The draft's subject, "Move PLAYBOOK/FINDINGS/AGENT_NOTES/HANDOFF_PROMPT to docs/agents/",
  is 78 characters, over the 72-character limit.)

**Acceptance:** the four files live at `docs/agents/`; `config/docsync.toml` declares their
new paths; the worktree guard reads the new location; the four `allow_after` keys and every
bare citation inside the five always-scanned documents (plus the active definition and
SESSION_CONTEXT) are current; `cli.py` reads and writes every document through
`[documents]`, with `PLAYBOOK_PATH` and `FINDINGS_PATH` gone; no generated text under
`scripts/docsync/` names a document path; the pre-commit exclude keeps `docs/agents/`
checked and the rest of `docs/` excluded; `pytest -q`, `pre-commit run --all-files` and
`doc_state_sync.py --check` all pass; every live-probe row behaves as specified.

---

### Task 7: Point PR #242's repo-assist workflow at the moved documents

PR #242 merged into `main` (`707eed6`) and Task 0 merges it here, so the workflow is on this
branch when this task runs; the draft's "absent" branch (file a finding instead) no longer
applies. `.github/workflows/repo-assist.md` names `PLAYBOOK.md` and `FINDINGS.md` at the
root, and its compiled `.github/workflows/repo-assist.lock.yml` carries its own copies.

**Environment:** needs the `gh aw` extension to recompile. A cloud sandbox without it (no
`gh` CLI at all in the 2026-09-24 cloud session) leaves this task to a local session; do not
hand-edit the lock file. Pushing a change under `.github/workflows/` also needs a token with
the `workflow` permission (handoff section 8).

**Files:**
- Modify: `.github/workflows/repo-assist.md`
- Regenerate: `.github/workflows/repo-assist.lock.yml` (`gh aw compile`)

- [ ] **Step 1: Repoint the source**

  In `.github/workflows/repo-assist.md` (line numbers at `origin/main` `707eed6`):
  - Both `allowed-files` lists (`create-pull-request`, `:189`/`:191`, and
    `push-to-pull-request-branch`, `:204`/`:206`) name `docs/agents/PLAYBOOK.md` and
    `docs/agents/FINDINGS.md` in place of the root paths.
  - The "Repository Rules" prose that forbids editing anything under `docs/` other than the
    log files must permit exactly those two files, so the grant and the prohibition agree.
  - Its prose mentions of `FINDINGS.md` and `PLAYBOOK.md` (`:10-11`, `:322-324`) become the
    `docs/agents/` paths.

- [ ] **Step 2: Recompile and check the copies**

  ```bash
  gh aw compile repo-assist
  git grep -n -e 'PLAYBOOK\.md' -e 'FINDINGS\.md' -- .github/workflows/repo-assist.lock.yml
  ```
  Every hit must carry the `docs/agents/` prefix. At `707eed6` the lock file carries the paths
  on six lines: the two `allowed_files` JSON configs (`GH_AW_SAFE_OUTPUTS_CONFIG` and
  `GH_AW_SAFE_OUTPUTS_HANDLER_CONFIG`) and the embedded workflow description. If the compile
  also asks for `--approve` (a changed memory-validation script), review the change first.

- [ ] **Step 3: Section 4 entry, gates, commit**

  One untagged Section 4 entry (cloud-kit R1). Gates as usual.

  ```bash
  git commit -m "chore(repo-assist): Point allowed-files at the moved documents"
  ```

**Acceptance:** neither workflow file names a root `PLAYBOOK.md` or `FINDINGS.md`; the
allowed-files grant and the "Repository Rules" prose agree; the lock file was regenerated by
`gh aw compile`, not edited by hand.

---

### Task 8: Diagnostics name the declared document path

Owner ruling, 2026-09-24: the docsync diagnostics that print a bare `PLAYBOOK.md` as their
location are fixed in this plan, not deferred to a finding. After Task 6 they point a reader
at a file that no longer exists. Labels change only the printed `path`, never whether a
check fires, so this task is safe to land after Task 6.

**Scope (at `85f47a0`; re-grep before starting, since Tasks 2-6 move lines):**
- `"PLAYBOOK.md"` labels, fourteen: `scripts/docsync/integrity.py` --
  `_active_definition_reference` (two, built as `IntegrityIssue(path="PLAYBOOK.md")`
  directly, not through `_issue`), `_unpaired_result_issue` (one), `_check_unbolded_test_counts`
  (two), `_check_section3_next_wp` (three), `collect_integrity_issues` (two DOC002);
  `scripts/docsync/closeout.py` -- `_admission_issue` (one), `_claim_issues` (three). (The
  draft said "ten": that is `integrity.py`'s count alone. The two `path == "PLAYBOOK.md"`
  comparisons are behavioural and are Task 2's.)
- `FINDINGS.md` labels, twelve, the same defect for the other moved document (owner ruling,
  2026-09-24: they join this task): `_check_findings_header_count`'s DOC008 label
  (`integrity.py:901`) and every diagnostic in `scripts/docsync/findings.py` that prints
  `ACTIVE_PATH` as its location -- eleven sites (`:220`, `:233`, `:250`, `:262`, `:274`,
  `:286`, `:297`, `:318`, `:344`, `:437`, `:459`), covering DOC013-DOC018 and DOC023; the
  DOC023 warning at `:459` is built as `IntegrityIssue` directly.

None of these functions receives a document path today. Thread the declared path down from
`collect_integrity_issues`'s `playbook_relative_path` / `findings_relative_path` (Task 2) as
a keyword argument defaulting to today's literal, so direct callers and existing tests keep
working; for `closeout.py`, from its caller in `collect_integrity_issues` or `cli.py`'s
`_close_batch`, whichever builds the issue. Grep for the literal afterwards: no
`"PLAYBOOK.md"` may remain as a diagnostic path in `scripts/docsync/`.

**Files:**
- Modify: `scripts/docsync/integrity.py`, `scripts/docsync/closeout.py`,
  `scripts/docsync/findings.py`, `scripts/docsync/cli.py`
  (if `_close_batch` must pass the path)
- Test: `tests/test_docsync_integrity.py`, `tests/test_docsync_closeout.py`,
  `tests/test_docsync_findings.py`

- [ ] **Step 1: Tests first**

  For each check family -- DOC002 (`_active_definition_reference` and the two
  `collect_integrity_issues` sites), DOC007, DOC012, the close-out admission and claim
  issues, DOC008, and each findings code (DOC013-DOC018, DOC023) -- one test that calls the check
  with `playbook_relative_path="docs/agents/PLAYBOOK.md"` (or the findings equivalent) on
  input that raises it, and asserts the issue's `path` is the declared one. Each must fail
  first: today every one prints the bare root name.

- [ ] **Step 2: Thread the path and run the tests**

  ```
  .venv/bin/python -m pytest tests/test_docsync_integrity.py tests/test_docsync_closeout.py tests/test_docsync_findings.py -v
  ```

- [ ] **Step 3: Gates and live probe**

  Control plane: `--check` at exit 0 first, then commit with `SKIP=doc-state-sync-check`.
  In `/tmp/ssprobe/corpus` built from this task's tree:
  - **Red (DOC007):** make `docs/agents/PLAYBOOK.md` Section 3's `**Next action:**` line
    name a work package that disagrees with the definition; `--check` prints DOC007 with the
    location `docs/agents/PLAYBOOK.md:<line>`.
  - **Red (DOC002):** point Section 3's active-definition reference at a missing file;
    DOC002 prints `docs/agents/PLAYBOOK.md` as its location.
  - **Near-miss green:** reset; `--check` exits 0.
  - Record each diagnostic's printed location in the probe table.

- [ ] **Step 4: Section 4 entry and commit**

  ```bash
  SKIP=doc-state-sync-check git commit -m "fix(docsync): Name the declared document path in diagnostics"
  ```

**Acceptance:** every docsync diagnostic about a moved document prints its declared path;
no `"PLAYBOOK.md"` literal remains as a diagnostic location under `scripts/docsync/` (nor
`FINDINGS.md`); each new test fails without the change; the probe shows the new
location.

---

## Self-Review

**Spec coverage.** Every item in `docs/history/reports/ROOT_CLEANUP_INVENTORY_2026-09-24.md`
is accounted for, plus what the 2026-09-24 pre-flight found beyond it: Section 1's code sites
(Tasks 4-6, 8), Section 2's tests (Tasks 1, 3, 5, 6 name every test that changes and why),
Section 3's citers (Task 5 Step 5, Task 6 Steps 7-8), Section 4's DOC001 scan mechanics (Task
2's kwargs, Task 6's sweep; DOC001 checks backticked `.md` references and not `.toml`, so the
`.docsync.toml` sweep is by grep), Section 5's declarations (Task 6 Step 4), Section 6's
other entry points (Task 6's sweep list, Task 7, and the controller list below), and Section
7's seven risks (rows 1 and 2 are Tasks 4 and 6's same-commit constraints; row 3 is Task 6
Step 4; row 4 is Task 6's whole-document sweep; row 5 is the `git mv` rule in Global
Constraints; row 6 noted, no defect found; row 7 is why Tasks 4 and 5 are separate commits
from Task 6). Beyond the inventory: the pre-commit exclude (Task 6 Step 9), the lock file
(Task 7), the declarations-file fixtures (Task 5 Step 1), the renderer tests and the archive
prologue contract (Task 6 Step 6).

**Scope cut, narrowed.** The synthetic fixtures in `tests/conftest.py` and
`tests/test_docsync_cli.py`'s `CORPUS_*` constants keep their four documents at the fixture
root: with no `[documents]` table the defaults are the root names, so they still test
docsync's generic behaviour and gain nothing from mirroring this repository's layout (Rule
5). Their declarations file is not cut: it follows `DECLARATIONS_FILENAME` (Task 5 Step 1),
or those fixtures would run with nothing declared.

**Placeholder scan.** No task says "add tests" without the test body or the assertion it must
make, and no task says "update references" without naming which ones and where.

**Type consistency.** `DocumentsConfig` is defined once (Task 2) and consumed with the same
field names (`playbook`, `findings`, `agent_notes`, `handoff_prompt`) in Tasks 6 and 8.
`resolved_live_document_paths(documents: DocumentsConfig) -> tuple[str, ...]` is defined once
(Task 2) and called unchanged in Task 6. `collect_integrity_issues`'s three path kwargs
(`document_paths`, `playbook_relative_path`, `findings_relative_path`) are introduced in Task
2 and used unchanged in Tasks 6 and 8; its `config_path` kwarg, and
`collect_declaration_issues`', arrive in Task 3.

---

## Definition of Done

Tasks 0-8 each meet their own acceptance. `pytest -q`, `pre-commit run --all-files`,
`doc_state_sync.py --check`, and the frontend gate (locally or CI's `quality-gate`) all pass
on the final tree. `docs/agents/PLAYBOOK.md` Section 4 carries one dated entry per task
(untagged, per WP-0's logging rule), each with its live-probe table where the task has one.
The controller checklist below is handed to the owner, not executed by an implementer.

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
4. **Handoff documents already written** (e.g. the untracked
   `docs/superpowers/handoffs/scrobblescope-handoff-2026-09-23-after-task7.md` on the owner's
   machine): point-in-time -- leave as written. The tracked entry-point handoff is repointed
   in Task 6 Step 8.
5. **A local session for Task 7** if this plan runs in a cloud sandbox without `gh aw`.
