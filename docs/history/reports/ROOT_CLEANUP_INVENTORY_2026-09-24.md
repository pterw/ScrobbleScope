# Inventory: root file move (PLAYBOOK.md, FINDINGS.md, AGENT_NOTES.md, HANDOFF_PROMPT.md -> docs/agents/; .docsync.toml, frontend_gate_checks.toml -> a config folder)

**Point-in-time report, 2026-09-24.** Read at commit `b1b8c0c` by a
read-only research agent for the root-cleanup plan
(`docs/superpowers/plans/2026-09-24-batch23-wp0-root-cleanup.md`). Line
numbers and counts are as of that commit; the plan, not this file, owns
what changes.

Read at commit `b1b8c0c`. All `file:line` references are against that commit unless
marked otherwise. Six paths under review: `PLAYBOOK.md`, `FINDINGS.md`,
`AGENT_NOTES.md`, `HANDOFF_PROMPT.md`, `.docsync.toml`, `frontend_gate_checks.toml`.

Orientation was taken from `graphify query` (graphify-out/graph.json, 5191 nodes)
before grepping; the node lists it returned (scripts/docsync/*, scripts/dev/
docsync_preflight.py, tests/test_docsync_declarations.py, tests/scripts/dev/
test_docsync_preflight.py, etc.) matched what direct `git grep` at b1b8c0c
confirmed below.

---

## 1. Code/config that resolves each path

### How docsync finds `.docsync.toml` today

**Fixed filename at the repo root -- no search.** `scripts/docsync/declarations.py:41`
declares `DECLARATIONS_FILENAME = ".docsync.toml"`. It is turned into an absolute
path only at `scripts/docsync/declarations.py:552`: `path = repo_root / DECLARATIONS_FILENAME`
inside `load_declarations(repo_root)`. `repo_root` is supplied by the caller;
`scripts/docsync/cli.py:78` sets `REPO_ROOT = Path(".")` -- i.e. docsync trusts the
process's current working directory to already be the repo root (consistent with
AGENTS.md's "run from the repo root" instruction; there is no upward directory
search, no `git rev-parse --show-toplevel` call in cli.py's own resolution). Every
`REPO_ROOT`-relative constant in cli.py (`PLAYBOOK_PATH`, `FINDINGS_PATH`,
`SESSION_CONTEXT_PATH`, `LIVE_DOCUMENT_PATHS`, ...) inherits this same fragility.

### How `frontend_gate.py` finds its manifest

**Also a fixed filename at the repo root, but resolved robustly via `__file__`,**
not cwd. `scripts/dev/frontend_gate.py:30`: `REPO_ROOT = Path(__file__).resolve().parents[2]`.
`scripts/dev/frontend_gate.py:384`: `CHECK_MANIFEST_PATH = REPO_ROOT / "frontend_gate_checks.toml"`.
Critically, `scripts/dev/frontend_gate.py:434-436` calls
`REQUIRED_CHECKS, DISABLED_CHECKS = _load_check_manifest()` **at module import
time**, with no argument, so it always resolves the real `CHECK_MANIFEST_PATH` --
this runs the instant anything does `from scripts.dev import frontend_gate` or
`import scripts.dev.frontend_gate`, in production and in every test that imports
the module (see Section 7, risk 1).

### Path constants and literal path sites (file : line -- what it is)

- `scripts/docsync/cli.py:79` -- `PLAYBOOK_PATH = Path("PLAYBOOK.md")` (joined against `REPO_ROOT`).
- `scripts/docsync/cli.py:88` -- `FINDINGS_PATH = Path(findings_module.ACTIVE_PATH)`.
- `scripts/docsync/cli.py:89` -- `LIVE_DOCUMENT_PATHS = tuple(Path(r) for r in LIVE_DOCUMENT_RELATIVE_PATHS)`.
- `scripts/docsync/findings.py:23` -- `ACTIVE_PATH = "FINDINGS.md"` (single source; `cli.py` and `integrity.py` both import this rather than re-stating the literal -- see the comment at `integrity.py:112-117`).
- `scripts/docsync/findings.py:24` -- `ARCHIVE_PATH = "docs/history/findings/FINDINGS_ARCHIVE.md"` (unaffected -- stays).
- `scripts/docsync/integrity.py:119-124` -- the canonical scan list:
  ```
  LIVE_DOCUMENT_RELATIVE_PATHS: tuple[str, ...] = (
      "AGENTS.md",
      "HANDOFF_PROMPT.md",
      "AGENT_NOTES.md",
      "PLAYBOOK.md",
      findings_module.ACTIVE_PATH,
  )
  ```
  All literal (`AGENTS.md` stays at root; the other three move). `cli.py` imports
  this tuple rather than restating it (see Section 4).
- `scripts/docsync/integrity.py:268,285,546,619,640,739,750,763,937,948,970,975` --
  `"PLAYBOOK.md"` used as the `_issue(...)` path label reported to the user, and
  as a literal comparison (`if path == "PLAYBOOK.md"`) that selects the
  Section-4-block-stripping branch during the DOC001 scan (see Section 4).
- `scripts/docsync/integrity.py:901` -- `"FINDINGS.md"` issue-path literal (DOC008).
- `scripts/docsync/integrity.py:1137` -- `live_documents.get("FINDINGS.md")`.
- `scripts/docsync/closeout.py:507,526,537,547` -- `"PLAYBOOK.md"` issue-path literals (close-out admission/claim checks).
- `scripts/docsync/renderer.py:18,173,184` -- prose strings citing `` `PLAYBOOK.md` `` inside generated remediation text (cosmetic but user-facing).
- `scripts/dev/docsync_preflight.py:82-85` -- `CONTROL_PLANE_FILES` tuple:
  ```
  CONTROL_PLANE_FILES: tuple[str, ...] = (
      "scripts/doc_state_sync.py",
      "scripts/dev/docsync_preflight.py",
      ".docsync.toml",
  )
  ```
  Exact-match (not prefix) against `git diff --cached --name-status` paths -- see
  the "naive prefix matching" comment at `docsync_preflight.py:75-77`. This is
  what refuses a commit that stages a docsync-control-plane change alongside a
  document check (`_is_control_plane_path`, `docsync_preflight.py:87-90`). **Must
  be updated to the new `.docsync.toml` location or the guard silently stops
  recognizing it as control-plane.**
- `scripts/dev/frontend_gate.py:381-384` -- `CHECK_MANIFEST_PATH` (above); its
  own `FrontendGateError` messages at lines 403-405 hard-code the string
  `"Restore frontend_gate_checks.toml at the repository root."` -- needs rewording
  once it is not at the repository root.
- `scripts/dev/_worktree_guard_inspection.py:172` -- `playbook_path = resolved_root / "PLAYBOOK.md"`,
  read at line 174 (`playbook_path.read_text(...)`) to parse Section 3 for the
  active batch/branch. This is the worktree guard's WT002/WT003 mechanism that
  CLAUDE.md and AGENTS.md describe as blocking every commit on the wrong branch.
  **This is a hard filesystem read of a literal root path -- the single highest-
  severity code site in this move** (see Section 7, risk 2).
- `scripts/dev/_worktree_guard_diagnostics.py:116` -- `"PLAYBOOK.md"` used only as
  the diagnostic's display label (`metadata_unavailable_diagnostic`), not a
  filesystem read; cosmetic but should track the real path for readable errors.
- `.docsync.toml` itself: see Section 5.

### Other config/hook/workflow files checked (task's explicit list)

- `.pre-commit-config.yaml:29` -- comment only ("docsync_preflight.py, .docsync.toml"); the hook entries reference `scripts/dev/docsync_preflight.py` by invocation, not the six paths directly. No literal path resolution of the six files found elsewhere in this file.
- `.github/workflows/test.yml` -- no reference to any of the six paths (checked in full, 96 lines).
- `.github/PULL_REQUEST_TEMPLATE.md:10-11` -- plain-text "PLAYBOOK Section 3" / "PLAYBOOK Section 4" (no backticked path, no `.md` extension) -- a human-facing checklist item, not resolved by tooling.
- `.github/copilot-instructions.md` -- no reference to any of the six paths at b1b8c0c (case-insensitive check). Note: `git status` at session start shows this file modified in the working tree right now (out of scope, in-flight).
- `.github/instructions/` -- only `mermaid.instructions.md`, unrelated.
- `.codacy.yml` -- no reference; `exclude_paths` names test/scratch trees only, not these six files.
- `.gitattributes` -- empty / no matches.
- `.gitignore:64` -- a comment, not a rule: `# HANDOFF_PROMPT.md and AGENT_NOTES.md are committed -- shared cross-agent bootstrap.` Documents that these two are deliberately NOT gitignored (unlike the root `CLAUDE.md`, which is). No ignore *rule* keys off the six paths.
- `.graphifyignore` (untracked, working tree only) -- excludes `docs/history/`, `docs/logarchive/`, `docs/superpowers/plans|specs|handoffs/`, and `.github/` from the graph, but does **not** exclude `docs/agents/` -- so the graph will pick the four moved files up correctly at their new location without a `.graphifyignore` edit.

---

## 2. Tests that name any of the six paths

18 test files contain at least one hit (206 raw line hits across them; see
detail below). Grouped by what they actually depend on:

### Tests reading the REAL repository file (break immediately on `git mv`, independent of any fixture)

- **`tests/scripts/dev/test_worktree_guard_playbook.py:150`**, test
  `test_the_repository_playbook_parses` -- `REPOSITORY_ROOT = Path(__file__).resolve().parents[3]`
  (line 9), then `playbook = (REPOSITORY_ROOT / "PLAYBOOK.md").read_text(...)`.
  This reads the actual `PLAYBOOK.md` in the working tree, not a fixture. **Must
  be updated to `docs/agents/PLAYBOOK.md`** or it raises `FileNotFoundError` the
  moment the file moves, regardless of code changes elsewhere.
- **`tests/scripts/dev/test_frontend_gate_manifest.py`** -- imports
  `from scripts.dev import frontend_gate` at module scope. Because
  `frontend_gate.py` evaluates `_load_check_manifest()` at import time against the
  real `CHECK_MANIFEST_PATH` (Section 1), **this whole test module -- and every
  other `tests/scripts/dev/test_frontend_gate_*.py` module that imports
  `frontend_gate`** -- fails at collection if `frontend_gate_checks.toml` moves
  before `frontend_gate.py:384`'s constant is updated in the same commit. The
  manifest-specific tests themselves (`test_disabling_a_required_check_is_refused`
  L39, `test_unknown_check_name_is_refused_not_ignored` L52,
  `test_malformed_manifest_is_refused_not_a_traceback` L69) build their own
  `tmp_path / "frontend_gate_checks.toml"` and call `_load_check_manifest(manifest)`
  with an explicit path, so they are otherwise location-independent.

### `scripts/dev/docsync_preflight.py` real-checkout fixture

- **`tests/scripts/dev/test_docsync_preflight.py`**:
  - `test_staged_paths_expands_rename_to_both_names` (L152,160) -- parametrizes on
    the literal string `.docsync.toml` (and a negative-control `.docsync.tomlx`)
    to prove exact-match, not prefix-match, detection.
  - `test_staged_preflight_against_real_docsync_checker` (L597-699, the largest
    single test in the corpus) builds a **real git repository** in `tmp_path` and
    writes `PLAYBOOK.md`, `.docsync.toml`, `AGENTS.md`, `HANDOFF_PROMPT.md`,
    `AGENT_NOTES.md`, `FINDINGS.md` **all at that repo's root** (mirrors today's
    flat layout, not `docs/agents/`), then exercises `candidate_corpus()` /
    `run_staged()` / `run_worktree()` against it end-to-end. It is a synthetic
    fixture (its own `tmp_path` repo), so it does not break on the real
    repository's `git mv`, but it currently asserts the *pre-move* layout is what
    production code expects -- if `docsync_preflight.py`'s `CONTROL_PLANE_FILES`
    or `docsync/cli.py`'s path constants change, this fixture's corpus should be
    updated to mirror the new layout, or it stops testing what production does.

### `tests/conftest.py` -- shared `sync_env` fixture

- `sync_env` (fixture, `tests/conftest.py:129-183`) builds a synthetic
  `tmp_path` corpus and `monkeypatch.setattr(cli_module, "PLAYBOOK_PATH", tmp_path / "PLAYBOOK.md")`
  (L141) plus writes `.docsync.toml` (L162), `PLAYBOOK.md` (L166), `AGENTS.md`
  (L177), `HANDOFF_PROMPT.md` (L178), `AGENT_NOTES.md` (L179), `FINDINGS.md`
  (L182) -- all at `tmp_path` root. Every test that uses this fixture (widely
  used across `tests/test_docsync_cli.py`) is internally self-consistent (the
  monkeypatched constant and the file it writes always agree), so it will not
  fail as a mechanical consequence of the real move. It **should still change**
  if the plan wants the test corpus to mirror the new subdirectory layout for
  realism (e.g. to catch a `docs/**/*.md` glob-coverage regression).

### `tests/test_docsync_cli.py`

Heaviest single file (~45 hits). Builds its own corpus constants
`CORPUS_PLAYBOOK`, `CORPUS_FINDINGS`, `CORPUS_TOML` and writes them under keys
`"PLAYBOOK.md"`, `"FINDINGS.md"`, `".docsync.toml"`, `"AGENTS.md"`,
`"HANDOFF_PROMPT.md"`, `"AGENT_NOTES.md"` (first appearance ~L712-721,
repeated through many individual `test_*` bodies to L1184+). Same shape as
`sync_env`: self-consistent synthetic corpus, not a hard dependency on the real
file locations, but should mirror the new layout if the plan wants that.

### `tests/test_docsync_declarations.py`

Uses helper fixtures `_repo()` (L36) and `_files()` (L45) that build a synthetic
repo directory and write `.docsync.toml` via the `DECLARATIONS_FILENAME`
constant imported from `docsync.declarations` (L15, `assert issues[0].path ==
DECLARATIONS_FILENAME` at L234, 913, 930, 1019, and `(tmp_path /
DECLARATIONS_FILENAME).write_text(...)` at L1260, 1439, 1453, 1471, 1506, 1564,
1604, 1690, 1700, 1712, 1796). Because this always goes through the
`DECLARATIONS_FILENAME` constant rather than a hard-coded literal, **it needs no
change purely because `.docsync.toml` moves** -- but note `DECLARATIONS_FILENAME`
itself is still `".docsync.toml"` (a bare filename); if the destination config
folder means the declared file is looked up by a *different* mechanism (not
`repo_root / DECLARATIONS_FILENAME`), this constant and every test built on it
changes together.

### Other test files with a hit (lighter, mostly cosmetic/docstring)

- `tests/scripts/dev/test_docsync_hook.py:241` -- docstring only, mentions
  "AGENTS.md / AGENT_NOTES.md" in prose explaining a CRLF hook bug; no path
  literal driving behaviour.
- `tests/scripts/dev/test_worktree_guard_base_ref.py:55`,
  `test_worktree_guard_inspection.py:27-28,51`,
  `test_worktree_guard_subject.py:124`, `test_worktree_guard_topology.py:43`,
  `tests/scripts/dev/worktree_guard_fakes.py:43` -- all write a synthetic
  `repo.joinpath("PLAYBOOK.md")` inside a `tmp_path`-based fake repo to feed
  `scripts/dev/worktree_guard.py` / `_worktree_guard_inspection.py` under test.
  Self-consistent fixtures (the guard code under test is itself told where to
  look via `resolved_root`, a `tmp_path` in these tests) -- not a hard
  dependency on the real repository's file location, but they are exactly the
  fixtures that exercise the literal `resolved_root / "PLAYBOOK.md"` in
  `_worktree_guard_inspection.py:172` (Section 1), so if that literal ever grows
  a subdirectory join, these fixtures must grow the matching subdirectory.
- `tests/test_docsync_closeout.py`, `tests/test_docsync_findings.py`,
  `tests/test_docsync_integrity.py`, `tests/test_docsync_logic.py`,
  `tests/test_docsync_renderer.py` -- all reference `"PLAYBOOK.md"` /
  `"FINDINGS.md"` as dict keys / literal strings inside synthetic
  `live_documents` mappings passed straight to `collect_integrity_issues(...)`
  or similar pure functions; not filesystem reads, so they exercise the code's
  *logic* against the string keys `LIVE_DOCUMENT_RELATIVE_PATHS` will use. No
  change needed unless `LIVE_DOCUMENT_RELATIVE_PATHS`'s literal strings change
  (see Section 4 -- they should NOT change; docsync's internal dict keys can stay
  bare filenames even after the real file moves, see risk 3).
- `tests/test_template_shell.py` -- one incidental hit, unrelated to the docsync
  mechanism (a CSS token comment matched a substring); not a real dependency.

---

## 3. Live documents (excluding `docs/history/` and `docs/logarchive/`) that cite each path

Counted per file, split backticked-citation vs. plain-text mention (a
backticked `` `PLAYBOOK.md` `` is the shape DOC001/DOC010/DOC011 pattern-match
on; a plain mention is prose only). **Point-in-time files** (`docs/superpowers/
plans/*`, `docs/superpowers/handoffs/*`, and dated PLAYBOOK Section 4 entries
inside `PLAYBOOK.md` itself) are marked `[point-in-time]` -- these describe what
was true on the date they were written and are not expected to track the move.

### PLAYBOOK.md (34 files, ~155 backticked + ~62 plain occurrences)
Top non-point-in-time citers: `DEVELOPMENT.md` (7 bt/2 plain), `docs/
AGENT_DOC_MAP.md` (6/0), `.docsync.toml` (0/5 -- see Section 5),
`AGENTS.md` (3/0), `FINDINGS.md` (3/0), `.claude/SESSION_CONTEXT.md` (2/0),
`.superpowers/cloud-kit/constraints.md` (2/0), `AGENT_NOTES.md` (2/0),
`PRODUCT.md` (2/0), `docs/ARCHITECTURE.md` (2/0), `docs/agents/domain.md` (2/0),
`docs/architecture/development-cycle.md` (0/1), `docs/architecture/
documentation-tooling.md` (0/1).
`[point-in-time]`: 20 files under `docs/superpowers/plans/` and one handoff-named
plan, contributing the bulk of the raw count (e.g.
`2026-09-11-batch21-document-orderliness-remediation.md` 17 bt/8 plain).

### FINDINGS.md (34 files, ~90 backticked + ~28 plain)
Top non-point-in-time citers: `docs/agents/issue-tracker.md` (6/1), `PLAYBOOK.md`
(3/2 -- self, live), `docs/AGENT_DOC_MAP.md` (5/0), `docs/SWE_AUDIT_CHARTER.md`
(2/3), `AGENTS.md` (3/1), `FINDINGS.md` (4/0 -- self-reference), `BATCH23_
DEFINITION.md` (2/0), `DEVELOPMENT.md` (2/0), `docs/agents/global-rules.md`
(2/0), `.claude/SESSION_CONTEXT.md` (0/1), `.superpowers/cloud-kit/
constraints.md` (1/0), `docs/ARCHITECTURE.md` (1/0), `docs/agents/domain.md`
(1/0), `docs/design/RECONCILIATION.md` (1/0).
`[point-in-time]`: ~19 plan/handoff files.

### AGENT_NOTES.md (21 files)
Non-point-in-time: `DEVELOPMENT.md` (5/0), `docs/SWE_AUDIT_CHARTER.md` (4/0),
`AGENTS.md` (3/0), `FINDINGS.md` (1/1), `PLAYBOOK.md` (2/0), `.docsync.toml`
(0/1 -- see Section 5, the `AGENT_NOTES.md` value site), `PRODUCT.md` (1/0),
`docs/AGENT_DOC_MAP.md` (1/0), `docs/agents/domain.md` (1/0), `docs/
architecture/development-cycle.md` (0/1), `docs/architecture/documentation-
tooling.md` (1/0).
`[point-in-time]`: 9 plan/handoff files, e.g. `docs/superpowers/handoffs/
2026-09-05-batch21-task-4-review-handoff.md`.

### HANDOFF_PROMPT.md (10 files)
Non-point-in-time: `AGENTS.md` (3/0), `DEVELOPMENT.md` (3/0), `docs/
AGENT_DOC_MAP.md` (2/0), `PLAYBOOK.md` (1/0), `docs/architecture/
documentation-tooling.md` (0/1).
`[point-in-time]`: 5 plan files (`2026-08-05-docsync-content-integrity.md`,
`2026-08-05-worktree-safety-guard.md`, `2026-09-12-repository-agnostic-plan-
spec-guards.md`, `2026-09-21-batch23-wp0-foundation.md`, and a spec under
`docs/superpowers/specs/`).

### .docsync.toml (18 files)
Non-point-in-time: `docs/architecture/documentation-tooling.md` (6/1),
`FINDINGS.md` (5/0), `DEVELOPMENT.md` (4/0), `AGENT_NOTES.md` (3/0),
`.superpowers/cloud-kit/constraints.md` (1/0), `AGENTS.md` (1/0), `docs/
ARCHITECTURE.md` (1/0), `docs/agents/global-rules.md` (1/0), `frontend_gate_
checks.toml` (1/0, comment cross-reference -- see Section 1).
`[point-in-time]`: 8 plan/spec files.

### frontend_gate_checks.toml (5 files)
`PLAYBOOK.md` (5/0 -- all inside its own dated Section 4 entries, i.e.
point-in-time within a live file -- see Section 4 on the entry-block exemption),
`docs/superpowers/plans/2026-09-21-batch23-wp0-foundation.md` (3/0,
point-in-time), `docs/superpowers/plans/2026-09-21-frontend-gate-decomposition.md`
(2/0, point-in-time), `DEVELOPMENT.md` (1/0), `docs/architecture/
documentation-tooling.md` (1/0).

**Not cited anywhere in this corpus:** `README.md`, `DESIGN.md` -- zero hits for
any of the six terms (checked in full at b1b8c0c).

---

## 4. DOC001 and similar checks -- exact scan scope

Read from `scripts/docsync/integrity.py:collect_integrity_issues` (L906-989) and
`scripts/docsync/declarations.py` (`check_anchor` / `check_retired`).

**Which documents does DOC001 scan?** Only:
`set(LIVE_DOCUMENT_RELATIVE_PATHS)` = `{AGENTS.md, HANDOFF_PROMPT.md,
AGENT_NOTES.md, PLAYBOOK.md, FINDINGS.md}` (`integrity.py:119-124`), **plus**
the active batch's root definition file (e.g. `BATCH23_DEFINITION.md`, added at
`integrity.py:948` only when one is currently declared active), **plus**
`.claude/SESSION_CONTEXT.md` (`SESSION_CONTEXT_RELATIVE_PATH`, added at
`integrity.py:950` when session lines are supplied). That is the complete
`documents_to_scan` set (`integrity.py:944-949`) -- **nothing under `docs/` is
ever in it.**

**Does it scan dated Section 4 entries?** No -- for `PLAYBOOK.md` specifically,
the scan uses `_playbook_lines_without_entry_blocks(playbook_lines)`
(`integrity.py:969-972`) rather than the raw lines, i.e. **every dated Section 4
execution-log entry is stripped out before DOC001 ever sees it.** No other
document in the scan set gets this treatment -- `FINDINGS.md`, `AGENT_NOTES.md`
and `HANDOFF_PROMPT.md` are scanned in full, with no comparable per-entry
exemption.

**Does it scan the archives (`docs/history/`, `docs/logarchive/`)?** No -- they
are simply never added to `documents_to_scan`; DOC001 has no notion of them at
all (consistent with the `.docsync.toml` anchor/retired declarations' own
`allow_files = ["docs/history/*", "docs/logarchive/*", ...]` exemptions, which
exist for the *other* checks that do scan broadly -- see below).

**Would a backticked `FINDINGS.md` inside an old dated entry fail after the
move?** Depends on where the citation lives:
- Inside a `PLAYBOOK.md` Section 4 dated entry block: **no** -- stripped from the
  DOC001 scan regardless of the move.
- Inside `docs/history/*` or `docs/logarchive/*`: **no** -- never scanned by
  DOC001, and explicitly `allow_files`-exempted for the anchor/retired checks.
- Anywhere else inside the five always-scanned documents (`AGENTS.md`,
  `HANDOFF_PROMPT.md`, `AGENT_NOTES.md`, `FINDINGS.md`, and `PLAYBOOK.md`
  outside its Section 4 blocks), or inside the active `BATCH*_DEFINITION.md` or
  `.claude/SESSION_CONTEXT.md`: **yes, it would newly fail.** DOC001
  (`integrity.py:977-989`) flags a backticked `` `word.md` `` reference
  (`BACKTICK_MD_RE`, `integrity.py:34`) whose target is not in
  `tracked_paths` (from `git ls-files`). Once `PLAYBOOK.md` is tracked at
  `docs/agents/PLAYBOOK.md` instead of `PLAYBOOK.md`, every remaining bare
  `` `PLAYBOOK.md` ``/`` `FINDINGS.md` ``/`` `AGENT_NOTES.md` ``/`` `HANDOFF_PROMPT.md` ``
  citation in those always-scanned documents must be rewritten to the new
  relative path, or DOC001 raises one issue per stale citation. This is the
  single most mechanical, highest-volume piece of the move.

**`.docsync.toml`/`frontend_gate_checks.toml` citations are never checked by
DOC001** regardless of the move: `BACKTICK_MD_RE` only matches a trailing
`\.md`, so a backticked `` `.docsync.toml` `` citation is structurally invisible
to DOC001 (it would need its own anchor/value declaration to be checked at all --
see Section 5).

**Is there an allow/exemption mechanism?** Yes, two, both declared in
`.docsync.toml`, both implemented in `scripts/docsync/declarations.py`:
- `allow_files` (glob list) -- exempts whole files from an `[[anchor]]` (DOC010)
  or `[[retired]]` (DOC011) declaration's scan. Every such declaration in this
  repository's `.docsync.toml` sets `allow_files = ["docs/history/*",
  "docs/logarchive/*", "CLAUDE.md"]` (one adds `"docs/superpowers/*"`).
- `allow_after` (a `{file: marker-line}` mapping) -- exempts the part of one
  named file *below* a literal marker line, used so a live document's own
  dated log can keep an old (retired) claim without failing DOC011
  (`check_retired`, `declarations.py:973-1042`; the marker match is
  `line.strip() == marker.strip()` against the **exact rel_path string**
  returned by the glob-based scan expansion -- see Section 5, this is the
  concrete break point).

Anchor/retired `scan` patterns are TOML globs matched via
`Path.glob(pattern)` inside `_expand` (`declarations.py:1171-1191`, called from
`_effective_scan`, `declarations.py:1195-1212`). Because every declared `scan`
in this repository uses `["*.md", "docs/**/*.md", ".claude/SESSION_CONTEXT.md"]`
(sometimes plus `static/css/*.css`, `scripts/dev/*.py`), and `pathlib.Path.glob`
treats `**` as arbitrary depth, **moving the four `.md` files from root into
`docs/agents/` does not remove them from these declared scans** -- they drop out
of the `"*.md"` (root-only) match but remain covered by `"docs/**/*.md"`
automatically, with no `.docsync.toml` edit required for the `scan` lists
themselves. The declarations that DO need editing are the literal (non-glob)
site paths -- see Section 5.

---

## 5. Declarations in `.docsync.toml` that name any of the six paths

Exact line numbers (`git show b1b8c0c:.docsync.toml`):

- **Line 527** -- `[[value.sites]] file = "AGENT_NOTES.md"` under `name = "the
  heatmap window length"` (`pattern = 'last (\d+) days'`, `expect = "365"`).
  Literal, non-glob file path. **Must become `"docs/agents/AGENT_NOTES.md"`.**
- **Lines 634, 647, 675, 704** -- four separate `[retired.allow_after]` tables,
  each `"PLAYBOOK.md" = "## 4. Execution log (for agent handoff)"` (one per
  `[[retired]]` declaration: the `limit_results` reversal, the self-hosted-fonts
  reversal, the DOC001-DOC011 catalogue reversal, and the DOC001-DOC023/024
  catalogue reversal). The key is matched verbatim against the `rel_path`
  string `_effective_scan` yields for each scanned file
  (`allow_after.get(rel_path)`, `declarations.py:1014`); once `PLAYBOOK.md`'s
  scanned `rel_path` becomes `docs/agents/PLAYBOOK.md`, `allow_after.get(...)`
  returns `None` for all four and the Section-4 exemption silently stops
  applying (a lookup miss, not an error -- see Section 7, risk 1). **All four
  keys must become `"docs/agents/PLAYBOOK.md"` in the same commit as the
  `git mv`.**
- **Line 700** -- a comment (not a declaration) explaining that the `allow_after`
  key must match "PLAYBOOK.md's real heading text" -- update for consistency
  once the key changes.
- No `[[anchor]]` declaration `target`s any of the six paths (targets are
  `AGENTS.md`, `docs/design/README.md`, `docs/agents/ui-accessibility.md` -- none
  of which move).
- No `[[value]]`/`[[value.sites]]` other than the one `AGENT_NOTES.md` line
  above names any of the six paths as a `file =` site.
- `.docsync.toml` never names itself or `frontend_gate_checks.toml` anywhere in
  its own text.

Related, in code rather than TOML: `scripts/dev/docsync_preflight.py:84`'s
`CONTROL_PLANE_FILES` literal `".docsync.toml"` (Section 1) is the other place
a bare-filename assumption about this file's location is baked in outside the
declarations file itself.

---

## 6. Other agents' and tools' entry points that hard-code the paths

- **`CLAUDE.md`** (repo root, gitignored, present on disk -- confirmed via `.gitignore:64`
  comment and by reading it directly): explicitly numbers a bootstrap order
  citing `` `AGENTS.md` ``, `` `PLAYBOOK.md` `` Section 3/4, `` `.claude/
  SESSION_CONTEXT.md` ``, `` `AGENT_NOTES.md` ``, `` `BATCH*_DEFINITION.md` ``,
  `` `FINDINGS.md` ``. This file is **not tracked** (`git ls-files .claude/`
  and `git ls-files CLAUDE.md` do not list it at repo root either -- it exists
  only on this machine), so it cannot be `git mv`-ed with the others; whoever
  owns it locally must hand-edit it, and it will not be caught by any grep of
  tracked files or by docsync (it is one of the two files that anchor/retired
  `allow_files` explicitly exempt, alongside `docs/history/*`/`docs/logarchive/*`
  -- see Section 4).
- **`.claude/CLAUDE.md`** -- present on disk but not tracked (`git show
  b1b8c0c:.claude/CLAUDE.md` -> "exists on disk, but not in b1b8c0c"; `git status
  --short .claude/` shows nothing, i.e. gitignored). Its content only points at
  the graphify skill trigger; it cites none of the six paths, so no edit needed
  there.
- **`docs/AGENT_DOC_MAP.md`** -- the densest live citer outside the moved files
  themselves: 6 backticked `PLAYBOOK.md`, 5 `FINDINGS.md`, 2 `HANDOFF_PROMPT.md`,
  1 `AGENT_NOTES.md` citations (counts from Section 3), including a routing
  table (`docs/AGENT_DOC_MAP.md:63-68`) that names each file by bare filename as
  "where to look" for a given task. **Not scanned by DOC001** (Section 4), so
  these citations will not be caught by the automated gate at all -- a manual
  sweep target.
- **`docs/agents/domain.md`, `docs/agents/global-rules.md`,
  `docs/agents/issue-tracker.md`** -- all cite `AGENT_NOTES.md`, `PLAYBOOK.md`,
  `FINDINGS.md` and/or `.docsync.toml` by bare filename (`domain.md:12-17`,
  `global-rules.md:75,81`, `issue-tracker.md:1,3,12,48,55,60,74`). These three
  files will sit in the **same destination directory** as `PLAYBOOK.md`,
  `FINDINGS.md`, `AGENT_NOTES.md`, `HANDOFF_PROMPT.md` once those move -- the plan
  should decide whether citations become relative (`PLAYBOOK.md`, since they'd
  be siblings) or repo-relative (`docs/agents/PLAYBOOK.md`, for consistency with
  every other citation style in this repository, which is always repo-root-relative).
- **`README.md`** project-structure block -- checked in full: **zero** references
  to any of the six paths. Nothing to update here.
- **`.superpowers/cloud-kit/constraints.md`** (tracked; used to brief cloud-run
  subagents) -- cites `` `PLAYBOOK.md` `` twice (L29, L175, the latter inside a
  literal `grep` command example: `` grep -n "^### .*WP-[0-9]" PLAYBOOK.md ``),
  `` `FINDINGS.md` `` once (L51), and `` `.docsync.toml` `` once (L77). The L175
  grep example is a literal shell command an agent is told to run -- it will
  silently no-op (find nothing) rather than error if not updated.
- **The repo-assist workflow, branch `chore/repo-assist-workflow`**
  (`.github/workflows/repo-assist.md`, read via
  `MSYS_NO_PATHCONV=1 git show "chore/repo-assist-workflow:.github/workflows/repo-assist.md"`
  -- Git Bash on Windows mis-parses an unescaped `branch:path` argument as a
  Windows path and fails without that env var; noting this as a Windows
  tooling gotcha for whoever else touches this branch, not a runtime risk):
  - `allowed-files` lists for **both** `create-pull-request` (L179-190) and
    `push-to-pull-request-branch` (L194-205) safe-outputs each hard-code
    `"PLAYBOOK.md"` and `"FINDINGS.md"` as literal root paths the automated
    agent may write to.
  - The prompt body's "Repository Rules" section (L317) simultaneously
    instructs the agent: "Never edit ... anything under `scripts/` or `docs/`
    other than the log files your Section 4 entry rotates into, or any file
    under `.github/`." **This is a direct conflict with the move**: if
    `PLAYBOOK.md` and `FINDINGS.md` relocate under `docs/agents/`, the
    `allowed-files` lists must add the new paths *and* the prose exclusion
    rule must be amended to still permit those two specific files under
    `docs/` -- otherwise Repo Assist's own instructions become
    self-contradictory (allowed-files says yes, prose says no) the moment the
    files move. This branch is not merged and not part of the active worktree,
    but any plan for the move should flag it as a dependency to reconcile
    before or alongside a future merge of that branch.
  - Lines 10-11 and 316 mention `FINDINGS.md` in prose describing what the
    workflow does; not path-resolution-critical, but should stay consistent.

---

## 7. Risks and ordering constraints

1. **`frontend_gate_checks.toml` move breaks `frontend_gate.py` at import time,
   not just at "run the gate" time.** `_load_check_manifest()` runs unconditionally
   at module load (`frontend_gate.py:434-436`), so the moment
   `frontend_gate_checks.toml` is `git mv`-ed, every test file that does
   `from scripts.dev import frontend_gate` (all of `tests/scripts/dev/
   test_frontend_gate_*.py`, not only the manifest-specific one) fails
   collection with `FrontendGateError: check manifest missing at ...`, and
   running `scripts/dev/frontend_gate.py` directly fails identically. **The
   `git mv` and the `CHECK_MANIFEST_PATH` constant update (plus its two
   hard-coded message strings at `frontend_gate.py:403-405`) must land in the
   same commit** -- there is no safe intermediate state, and this is the
   fastest way the move would "go red mid-move" if sequenced wrong.

2. **`PLAYBOOK.md` move breaks the worktree guard's own commit gate.**
   `_worktree_guard_inspection.py:172` does `resolved_root / "PLAYBOOK.md"` and
   reads it to determine the active batch/branch (WT002/WT003 -- the mechanism
   CLAUDE.md itself calls out as failing "any commit on a branch PLAYBOOK
   Section 3 does not name"). If this literal is not updated in the same commit
   as the `git mv`, the guard cannot read `PLAYBOOK.md` at all, which -- per its
   own `except OSError` branch (`_worktree_guard_inspection.py:179-181`) --
   reports "PLAYBOOK.md could not be read" and returns a metadata-unavailable
   diagnostic. Depending on how the guard's caller treats that diagnostic, this
   risks **blocking every subsequent commit** (including the follow-up commits
   the move itself would need) until fixed. This code path runs *before*
   docsync's own check in the local commit sequence (worktree-alignment is a
   separate pre-commit hook from doc-state-sync-check; check `.pre-commit-
   config.yaml` for their relative ordering before sequencing the move) -- so a
   guard failure here can strand the migration mid-flight in a way a docsync
   failure alone would not (docsync's `--fix` can repair many things
   automatically; the guard has no autofix).

3. **The four `[retired.allow_after]` markers in `.docsync.toml` fail silently,
   not loudly, if left unupdated.** `allow_after.get(rel_path)` (Section 5)
   returns `None` on a key miss with no error and no warning -- `F-DOCSYNC-16`
   (referenced in the `.docsync.toml` comment at line 700) already documents
   that an unmatched `allow_after` marker is silently ignored. If the four
   `"PLAYBOOK.md"` keys are not updated to `"docs/agents/PLAYBOOK.md"` in the
   same commit, PLAYBOOK's own Section 4 dated entries that still mention the
   retired claims would **start failing DOC011** with no signal that the cause
   is a stale `allow_after` key rather than a genuine regression -- a likely
   source of confusing gate failures during the move.

4. **DOC001 will flag every un-rewritten bare-filename citation inside the five
   always-scanned live documents** (Section 4) -- this is expected, high-volume,
   and mechanical, not a design risk, but it means **`--check` cannot pass with
   the move half-done**: the files must move and every backticked citation
   inside `AGENTS.md`, `HANDOFF_PROMPT.md`, `AGENT_NOTES.md`, `FINDINGS.md`,
   `PLAYBOOK.md` (outside Section 4), the active `BATCH23_DEFINITION.md`, and
   `.claude/SESSION_CONTEXT.md` must be corrected together, or `doc_state_sync.py
   --check` goes red for the length of the migration. `--fix` does not appear to
   auto-rewrite citation targets (it repairs managed blocks and headers, not
   arbitrary prose citations) -- confirm this against `scripts/docsync/logic.py`
   before assuming `--fix` can shortcut this step.

5. **Git history/blame continuity**: use `git mv` (or stage delete+add of
   byte-identical content, which Git's own rename detection -- used by
   `staged_paths()`'s `-M` flag in `docsync_preflight.py:169-186` -- will treat
   equivalently) rather than a delete-then-recreate-with-edits in the same
   commit, so `git log --follow` and blame continuity survive. Note
   `staged_control_plane_paths` (`docsync_preflight.py:196-203`) already
   expects renames to surface both the old and new path from `git diff --cached
   --name-status -M`, and a `.docsync.toml` rename would be caught as
   control-plane-sensitive on *both* names -- bundling the `.docsync.toml`
   `git mv` with any other control-plane code edit in the same commit will trip
   the preflight refusal (`_print_control_plane_refusal`,
   `docsync_preflight.py:206-227`); keep the `.docsync.toml` move in a commit
   that touches no other control-plane file, or use the documented
   `SKIP=doc-state-sync-check` escape and run `doc_state_sync.py --check`
   directly afterward (never `--no-verify` -- forbidden by the owner ruling
   `docsync_preflight.py:222-224` cites).

6. **Windows path/tool gotchas for whoever executes the move**: (a) Git Bash
   (MSYS) mis-parses a bare `branch:path` revision argument containing both a
   colon and forward slashes as a Windows path unless `MSYS_NO_PATHCONV=1` is
   set -- relevant to anyone diffing branches or reading a `branch:file` outside
   the current checkout during the move; (b) all the path constants audited
   here are `pathlib.Path` joins or POSIX-style string literals compared
   against `git`-reported paths (which are always forward-slash), so no
   backslash-vs-forward-slash defect was found in the six-path code paths
   themselves.

7. **Two files, two destinations, different blast radius.** The four `.md`
   files move together to one new directory (`docs/agents/`) and can likely be
   moved and fixed up in one commit since they share the same `LIVE_DOCUMENT_
   RELATIVE_PATHS` mechanism and the same `allow_after`/DOC001 exposure. The two
   `.toml` files move to a *different*, not-yet-named destination and are
   consumed by two independent, unrelated mechanisms (`docsync.declarations`'s
   fixed-filename lookup vs. `frontend_gate.py`'s import-time load) with no
   shared code path -- there is no structural reason these two moves need to
   happen in the same commit, and splitting them reduces the blast radius of
   risk 1 and risk 2 landing together.
