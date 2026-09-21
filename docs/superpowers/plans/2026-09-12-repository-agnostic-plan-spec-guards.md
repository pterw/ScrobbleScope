# Repository-Agnostic Plan and Spec Guards Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Status:** Deferred. Do not execute this plan until the owner has accepted the
Unmatched UI, the current design-system reconciliation plan has completed its
remaining phases, and PLAYBOOK Section 3 explicitly opens this work.

**Goal:** Put plans and specifications inside the deterministic documentation
integrity boundary while reducing, rather than increasing, the mixed
responsibilities in `scripts/docsync/integrity.py` and
`scripts/docsync/declarations.py`.

**Architecture:** Extract a small repository-agnostic contract kernel behind
the current public functions. The kernel resolves a bounded repository corpus,
named document sets, lifecycle records and authority references; repository
names and paths remain declarative policy. Existing DOC001-DOC012 behavior and
CLI diagnostics remain stable while new DOC021-DOC022 checks close the
source-of-intent gap.

**Tech Stack:** Python 3.13 standard library, TOML, Git, pytest, pre-commit.

## Global Constraints

- This is future work, not a new Batch 21 work package.
- UI completion comes first. Do not modify `templates/`, `static/`, or
  `scripts/dev/frontend_gate.py` under this plan.
- The new generic kernel modules must not contain `ScrobbleScope`,
  `PLAYBOOK.md`, `Batch`, `WP`, or `docs/superpowers/` policy literals.
  Those belong in repository configuration or the retained policy facade.
- Add no dependency. Continue using `tomllib`, `pathlib`, and the existing
  `IntegrityIssue`/`SyncError` result contract.
- Preserve `collect_integrity_issues()`, `collect_declaration_issues()`,
  `load_declarations()`, `collect_tracked_paths()`, and current exit-code
  semantics during migration.
- Refactor by responsibility, not line count. Keep compatibility re-exports
  until all repository callers and tests have moved.
- Every extraction begins with parity tests. Every new guard must be observed
  failing against its named mutation before it may be called protective.
- The central lifecycle registry is authoritative. A plan cannot establish its
  own authority merely by declaring itself active.
- A close-of-task reconciliation sweep remains required. It supplements the
  deterministic guards; it does not replace them.
- The Progress section of
  `docs/superpowers/plans/2026-09-11-batch21-design-system-reconciliation.md`
  outranks that plan's body. The traversal report at
  `docs/history/reports/BATCH21_PLAN_TRAVERSAL_2026-09-11.md` records the
  verified interpretation.

---

## File Structure

### New generic kernel files

- `scripts/docsync/corpus.py` -- repository-bounded path normalization,
  tracked-file discovery, live-document overlays, cached reads and glob
  expansion.
- `scripts/docsync/markdown.py` -- Markdown reference, heading, list and
  cross-line match primitives with source-line preservation.
- `scripts/docsync/contracts.py` -- typed document-set, lifecycle and authority
  configuration plus deterministic resolution.
- `scripts/docsync/intent.py` -- DOC021-DOC022 evaluation over resolved contract
  objects; no repository-specific names.

### Existing files retained as facades

- `scripts/docsync/integrity.py` -- ScrobbleScope policy checks and stable
  `collect_integrity_issues()` facade.
- `scripts/docsync/declarations.py` -- DOC009-DOC011 evaluators and stable
  `collect_declaration_issues()` facade.
- `scripts/docsync/cli.py` -- command modes, rendering and exit codes; consumes
  the facades without learning contract internals.
- `scripts/docsync/models.py` -- existing shared results plus the new immutable
  contract records.

### Configuration and tests

- `.docsync.toml` -- repository-local document sets, lifecycle inventory,
  authority references and DOC009-DOC011 declarations.
- `tests/test_docsync_corpus.py` -- path, overlay, tracked-set and glob behavior.
- `tests/test_docsync_markdown.py` -- extracted Markdown primitives.
- `tests/test_docsync_contracts.py` -- schema and resolution behavior.
- `tests/test_docsync_intent.py` -- DOC021-DOC022 regression and mutation tests.
- `tests/test_docsync_integrity.py` -- facade-level parity and integration.
- `tests/test_docsync_declarations.py` -- facade-level parity and named-set
  scanning.

## Interfaces

```python
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Mapping, Sequence

from docsync.models import IntegrityIssue

LifecycleState = Literal[
    "active", "deferred", "complete", "superseded", "reference"
]


@dataclass(frozen=True)
class DocumentSetSpec:
    name: str
    include: tuple[str, ...]
    exclude: tuple[str, ...] = ()
    require_tracked: bool = True


@dataclass(frozen=True)
class IntentDocument:
    path: str
    set_name: str
    kind: Literal["plan", "spec"]
    state: LifecycleState
    superseded_by: str | None = None


@dataclass(frozen=True)
class AuthoritySpec:
    name: str
    source: str
    pattern: str
    set_name: str
    allowed_states: tuple[LifecycleState, ...]
    minimum: int
    maximum: int

@dataclass(frozen=True)
class ContractConfig:
    document_sets: tuple[DocumentSetSpec, ...]
    documents: tuple[IntentDocument, ...]
    authorities: tuple[AuthoritySpec, ...]



class RepositoryCorpus:
    def __init__(
        self,
        repo_root: Path,
        live_documents: Mapping[str, Sequence[str]],
        tracked_paths: frozenset[str] | None = None,
    ) -> None: ...

    def lines(self, rel_path: str) -> list[str] | None: ...
    def expand(self, patterns: Sequence[str]) -> tuple[str, ...]: ...
    def is_tracked(self, rel_path: str) -> bool: ...


def load_contracts(repo_root: Path) -> ContractConfig: ...


def resolve_document_sets(
    config: ContractConfig, corpus: RepositoryCorpus
) -> Mapping[str, tuple[str, ...]]: ...


def collect_intent_issues(
    config: ContractConfig, corpus: RepositoryCorpus
) -> list["IntegrityIssue"]: ...
```

`DocumentSetSpec` discovers the bounded universe. `IntentDocument` assigns
each discovered plan or spec exactly one centrally recorded lifecycle state.
`AuthoritySpec` reads repository-owned pointers and verifies that every
captured path resolves into the permitted set and lifecycle state.

## Configuration Contract

The exact repository policy lives in `.docsync.toml`; the parser understands
only the generic tables below:

```toml
[[document_set]]
name = "intent-documents"
include = ["docs/superpowers/plans/*.md", "docs/superpowers/specs/*.md"]
exclude = []
require_tracked = true

[[intent_document]]
path = "docs/superpowers/plans/example.md"
set = "intent-documents"
kind = "plan"
state = "deferred"

[[authority]]
name = "current implementation plan"
source = "PLAYBOOK.md"
pattern = 'Work from `(docs/superpowers/plans/[^`]+\.md)`'
set = "intent-documents"
allowed_states = ["active"]
minimum = 1
maximum = 1
```

DOC021 owns document-set and lifecycle integrity:

- every included path is repository-bounded and tracked;
- every discovered path has exactly one lifecycle record;
- no lifecycle record names a path outside its declared set;
- `superseded` requires a tracked `superseded_by` target;
- the target cannot itself be superseded and supersession cannot cycle.

DOC022 owns authority integrity:

- the source exists and is tracked;
- the regex has exactly one capture group;
- captured paths satisfy the declared cardinality;
- every captured path belongs to the declared set;
- every captured path has an allowed lifecycle state.

Existing DOC010 and DOC011 declarations gain an optional `scan_set` field.
Exactly one of `scan` and `scan_set` must be present. This lets retired-claim
and reference checks operate on a resolved active-intent set without embedding
plan paths in Python.

---

### Task 1: Freeze the existing public behavior

**Files:**

- Create: `tests/test_docsync_contract_compat.py`
- Modify: none
- Test: `tests/test_docsync_contract_compat.py`

**Interfaces:**

- Consumes: current public docsync functions and `IntegrityIssue`.
- Produces: a parity boundary that every extraction task must keep green.

- [ ] **Step 1: Write facade-level characterization tests**

Cover these observable contracts without importing new modules:

```python
from pathlib import Path

from docsync.declarations import collect_declaration_issues
from docsync.integrity import collect_integrity_issues
from docsync.renderer import SIDE_ARCHIVE_PREFIX


def _valid_inputs(tmp_path: Path) -> dict[str, object]:
    """Build the smallest internally consistent active document set."""
    definition = [
        "# BATCH21",
        "",
        "**Branch:** `test` (lineage lives in PLAYBOOK Section 4).",
    ]
    playbook = [
        "# PLAYBOOK",
        "",
        "## 3. Active batch + next action",
        "",
        "- **Batch 21 is active.** Definition: `BATCH21_DEFINITION.md`.",
        "",
        "## 4. Execution log",
        "",
        "<!-- DOCSYNC:CURRENT-BATCH-START -->",
        "",
        "### 2026-09-12 - Current work (Batch 21 WP-0)",
        "",
        "Validation: **1 passed**.",
        "",
        "<!-- DOCSYNC:CURRENT-BATCH-END -->",
    ]
    live_documents = {
        "AGENTS.md": ["See `FINDINGS.md`."],
        "HANDOFF_PROMPT.md": ["Read `AGENTS.md`."],
        "AGENT_NOTES.md": ["Rules: `AGENTS.md`."],
        "PLAYBOOK.md": playbook,
        "FINDINGS.md": ["No current references."],
        "BATCH21_DEFINITION.md": definition,
    }
    return {
        "repo_root": tmp_path,
        "live_documents": live_documents,
        "playbook_lines": playbook,
        "archive_lines": list(SIDE_ARCHIVE_PREFIX),
        "session_lines": None,
        "expected_session_lines": None,
        "tracked_paths": frozenset(live_documents),
    }


def test_integrity_facade_returns_stably_sorted_diagnostics(tmp_path: Path):
    """The aggregate facade retains deterministic path ordering."""
    inputs = _valid_inputs(tmp_path)
    inputs["live_documents"]["AGENTS.md"] = ["See `z-missing.md`."]
    inputs["live_documents"]["HANDOFF_PROMPT.md"] = ["See `a-missing.md`."]

    issues = collect_integrity_issues(**inputs)

    assert [(issue.code, issue.path, issue.line) for issue in issues] == [
        ("DOC001", "AGENTS.md", 1),
        ("DOC001", "HANDOFF_PROMPT.md", 1),
    ]


def test_declaration_facade_prefers_live_document_bytes(tmp_path: Path):
    """A just-rendered in-memory document remains newer than disk."""
    (tmp_path / ".docsync.toml").write_text(
        """
[[retired]]
name = "the retired phrase"
pattern = "retired text"
scan = ["plan.md"]
strikethrough_exempt = false
""".lstrip(),
        encoding="utf-8",
    )
    (tmp_path / "plan.md").write_text("retired text\n", encoding="utf-8")
    issues = collect_declaration_issues(
        repo_root=tmp_path,
        live_documents={"plan.md": ["replacement text"]},
    )
    assert issues == []
```

- [ ] **Step 2: Run the characterization and existing focused suites**

Run:

```bash
pytest tests/test_docsync_contract_compat.py tests/test_docsync_integrity.py tests/test_docsync_declarations.py -q
```

Expected: PASS with the current diagnostic text and ordering.

- [ ] **Step 3: Commit the characterization boundary**

```bash
git add tests/test_docsync_contract_compat.py
git commit -m "test(docsync): Pin integrity facade behavior"
```

### Task 2: Extract the repository corpus

**Files:**

- Create: `scripts/docsync/corpus.py`
- Create: `tests/test_docsync_corpus.py`
- Modify: `scripts/docsync/declarations.py`
- Modify: `scripts/docsync/integrity.py`
- Modify: `scripts/docsync/cli.py`
- Test: `tests/test_docsync_corpus.py`

**Interfaces:**

- Consumes: repository root, live document mapping and tracked paths.
- Produces: `RepositoryCorpus`, `normalize_reference()` and
  `collect_tracked_paths()`.

- [ ] **Step 1: Write failing corpus tests**

Prove live bytes beat disk, equivalent path spelling uses the same cache key,
missing files return `None`, unmatched globs remain visible, duplicate glob
matches collapse, and `..` plus symlink escapes raise `SyncError`.

- [ ] **Step 2: Run the new tests and observe the missing module failure**

Run:

```bash
pytest tests/test_docsync_corpus.py -q
```

Expected: FAIL because `docsync.corpus` does not exist.

- [ ] **Step 3: Move the shared repository behavior**

Implement the interface above in `corpus.py`. A missing `tracked_paths`
value supports the existing declaration-only temporary repositories; checks
that require tracked membership must reject an absent tracked set. Move
`collect_tracked_paths()` from `integrity.py` and the behavior of `_Files`
from `declarations.py`. Leave compatibility imports in the old modules:

```python
from docsync.corpus import RepositoryCorpus, collect_tracked_paths

_Files = RepositoryCorpus
```

Update `cli.py` to import `collect_tracked_paths` from `docsync.corpus`.

- [ ] **Step 4: Run corpus and facade parity tests**

Run:

```bash
pytest tests/test_docsync_corpus.py tests/test_docsync_contract_compat.py tests/test_docsync_integrity.py tests/test_docsync_declarations.py tests/test_docsync_cli.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit the corpus extraction**

```bash
git add scripts/docsync/corpus.py scripts/docsync/declarations.py scripts/docsync/integrity.py scripts/docsync/cli.py tests/test_docsync_corpus.py
git commit -m "refactor(docsync): Extract the repository corpus"
```

### Task 3: Extract Markdown matching primitives

**Files:**

- Create: `scripts/docsync/markdown.py`
- Create: `tests/test_docsync_markdown.py`
- Modify: `scripts/docsync/declarations.py`
- Modify: `scripts/docsync/integrity.py`
- Test: `tests/test_docsync_markdown.py`

**Interfaces:**

- Consumes: Markdown line sequences and compiled patterns.
- Produces: normalized repository references, headings/list targets and matches
  retaining their original 1-based source line.

- [ ] **Step 1: Move existing adversarial examples into module-level tests**

Include fenced-code exclusion, Markdown links, backticked paths, wrapped
phrases, line anchors, indentation normalization, strikethrough spans,
parenthetical heading suffixes and numbered-list targets.

- [ ] **Step 2: Run the tests and observe the missing module failure**

```bash
pytest tests/test_docsync_markdown.py -q
```

- [ ] **Step 3: Move primitives without changing their behavior**

Move `_normalize_reference`, `_concrete_references`, `_headings`,
`_list_numbers_under`, `_joined_text`, `_declared_matches`, `_line_of` and
`_is_struck_through` into `markdown.py`. Keep temporary re-exports where
existing tests import private names.

- [ ] **Step 4: Run all docsync tests**

```bash
pytest tests/test_docsync_contract_compat.py tests/test_docsync_corpus.py \
  tests/test_docsync_markdown.py tests/test_docsync_cli.py \
  tests/test_docsync_declarations.py tests/test_docsync_integrity.py \
  tests/test_docsync_logic.py tests/test_docsync_parser.py tests/test_docsync_renderer.py tests/test_docsync_test_count.py -q
```

Expected: PASS with unchanged diagnostics.

- [ ] **Step 5: Commit the Markdown extraction**

```bash
git add scripts/docsync/markdown.py scripts/docsync/declarations.py scripts/docsync/integrity.py tests/test_docsync_markdown.py
git commit -m "refactor(docsync): Extract Markdown contract primitives"
```

### Task 4: Parse typed document contracts

**Files:**

- Create: `scripts/docsync/contracts.py`
- Create: `tests/test_docsync_contracts.py`
- Modify: `scripts/docsync/models.py`
- Modify: `scripts/docsync/declarations.py`
- Test: `tests/test_docsync_contracts.py`

**Interfaces:**

- Consumes: `.docsync.toml` and `RepositoryCorpus`.
- Produces: immutable `ContractConfig`, resolved document sets and declaration
  input errors reported as `DeclarationError` with exit code 2.

- [ ] **Step 1: Write schema-failure tests**

Test unknown tables and keys, wrong container/item types, duplicate set names,
empty include lists, invalid lifecycle states, duplicate lifecycle records,
missing `superseded_by`, invalid authority cardinality, patterns with zero or
multiple capture groups and a reference to an unknown set.

- [ ] **Step 2: Write resolution tests**

Test stable path ordering, include/exclude behavior, tracked-only enforcement,
an unmatched include pattern, path escape rejection and live-document use.

- [ ] **Step 3: Run the new tests and observe failure**

```bash
pytest tests/test_docsync_contracts.py -q
```

- [ ] **Step 4: Implement typed parsing and resolution**

Keep `load_declarations()` as the raw-dict compatibility facade. Add
`load_contracts()` for typed consumers; do not make `integrity.py` understand
TOML table shapes.

- [ ] **Step 5: Run contract and declaration suites**

```bash
pytest tests/test_docsync_contracts.py tests/test_docsync_declarations.py tests/test_docsync_contract_compat.py -q
```

- [ ] **Step 6: Commit typed contracts**

```bash
git add scripts/docsync/contracts.py scripts/docsync/models.py scripts/docsync/declarations.py tests/test_docsync_contracts.py
git commit -m "feat(docsync): Add typed document contracts"
```

### Task 5: Add DOC021 lifecycle coverage

**Files:**

- Create: `scripts/docsync/intent.py`
- Create: `tests/test_docsync_intent.py`
- Modify: `scripts/docsync/integrity.py`
- Test: `tests/test_docsync_intent.py`

**Interfaces:**

- Consumes: typed contract configuration and resolved corpus.
- Produces: DOC021 diagnostics for membership and lifecycle defects.

- [ ] **Step 1: Write failing DOC021 tests**

Cover an unregistered discovered plan, a duplicate record, an untracked plan,
a record outside its set, a superseded record without a target, a missing
target, a superseded target and a two-document supersession cycle.

- [ ] **Step 2: Run the tests and confirm DOC021 is absent**

```bash
pytest tests/test_docsync_intent.py -q
```

- [ ] **Step 3: Implement lifecycle validation in `intent.py`**

Return one actionable `IntegrityIssue` per defect and sort by path, line and
code. The evaluator receives resolved objects; it must not load TOML or inspect
ScrobbleScope filenames.

- [ ] **Step 4: Integrate through the stable integrity facade**

`collect_integrity_issues()` constructs the corpus once, calls
`collect_intent_issues()`, then preserves the final stable sort. Keep every
existing DOC001-DOC012 call unchanged.

- [ ] **Step 5: Prove a mutation fails**

Remove one lifecycle record from the fixture. Record that the test fails with
DOC021 and names the unregistered path; restore it and rerun green.

- [ ] **Step 6: Commit DOC021**

```bash
git add scripts/docsync/intent.py scripts/docsync/integrity.py tests/test_docsync_intent.py
git commit -m "feat(docsync): Guard intent document lifecycles"
```

### Task 6: Add DOC022 authority resolution

**Files:**

- Modify: `scripts/docsync/intent.py`
- Modify: `tests/test_docsync_intent.py`
- Modify: `scripts/docsync/integrity.py`
- Test: `tests/test_docsync_intent.py`

**Interfaces:**

- Consumes: `AuthoritySpec`, central lifecycle records and corpus bytes.
- Produces: DOC022 diagnostics for missing, ambiguous, outside-set or
  lifecycle-incompatible authority pointers.

- [ ] **Step 1: Write failing authority tests**

Cover zero matches where one is required, two matches where one is allowed,
an untracked capture, a capture outside the set, a deferred document where
active is required, a superseded document and a valid active pointer.

- [ ] **Step 2: Implement authority evaluation**

Evaluate only configured source bytes. Normalize captures through
`RepositoryCorpus`, then check cardinality, set membership and lifecycle in
that order so diagnostics point at the earliest repairable defect.

- [ ] **Step 3: Prove stale authority fails**

Change the fixture's active plan to `superseded` without changing the source
pointer. Record that DOC022 fails before restoring the state.

- [ ] **Step 4: Run the complete intent and parity suites**

```bash
pytest tests/test_docsync_intent.py tests/test_docsync_contracts.py tests/test_docsync_contract_compat.py tests/test_docsync_integrity.py -q
```

- [ ] **Step 5: Commit DOC022**

```bash
git add scripts/docsync/intent.py scripts/docsync/integrity.py tests/test_docsync_intent.py
git commit -m "feat(docsync): Guard document authority pointers"
```

### Task 7: Let declared checks consume named sets

**Files:**

- Modify: `scripts/docsync/contracts.py`
- Modify: `scripts/docsync/declarations.py`
- Modify: `tests/test_docsync_declarations.py`
- Test: `tests/test_docsync_declarations.py`

**Interfaces:**

- Consumes: `scan_set = "<name>"` on DOC010/DOC011 declarations.
- Produces: the same evaluators operating over a centrally resolved set.

- [ ] **Step 1: Write exclusive-input schema tests**

Prove that `scan` alone and `scan_set` alone are valid, while both together or
neither are `DeclarationError`. Prove an unknown or empty named set blocks
rather than silently scanning nothing.

- [ ] **Step 2: Write behavior tests**

Use one active, one deferred and one superseded document. Resolve an
active-only set and prove DOC011 reports the retired phrase only in the active
document while DOC010 resolves citations from that same set.

- [ ] **Step 3: Implement named-set consumption**

Pass the resolved sets into the DOC010/DOC011 evaluators. Keep their existing
raw `scan` behavior and direct test helpers available during migration.

- [ ] **Step 4: Run declaration and integration tests**

```bash
pytest tests/test_docsync_declarations.py tests/test_docsync_contracts.py tests/test_docsync_intent.py tests/test_docsync_integrity.py tests/test_docsync_cli.py -q
```

- [ ] **Step 5: Commit named-set scanning**

```bash
git add scripts/docsync/contracts.py scripts/docsync/declarations.py tests/test_docsync_declarations.py
git commit -m "feat(docsync): Scan resolved document sets"
```

### Task 8: Register the ScrobbleScope intent corpus

**Files:**

- Modify: `.docsync.toml`
- Modify: `AGENTS.md`
- Modify: `PLAYBOOK.md`
- Modify: `.claude/SESSION_CONTEXT.md` only through docsync-managed output
- Test: `tests/test_docsync_intent.py`

**Interfaces:**

- Consumes: tracked plans/specs and authoritative pointers in repository docs.
- Produces: a complete central lifecycle inventory and active-intent named set.

- [ ] **Step 1: Inventory the tracked intent corpus**

Run:

```bash
git ls-files "docs/superpowers/plans/*.md" "docs/superpowers/specs/*.md"
```

Add one `[[intent_document]]` entry for every returned path. Classify a
document from current repository evidence, never from its unchecked prose:

- `active`: PLAYBOOK currently directs execution from it;
- `deferred`: approved future work whose prerequisite has not opened;
- `complete`: its deliverable landed and no current authority points to it;
- `superseded`: another tracked document replaces its instructions;
- `reference`: deliberately retained context that never directs execution.

- [ ] **Step 2: Review the lifecycle inventory with the owner**

Present the exact path/state table before changing authority declarations.
Resolve disagreements in the registry; do not weaken coverage or add blanket
exclusions to make the gate green.

- [ ] **Step 3: Declare repository-specific authority sources**

Add `[[authority]]` entries for every current PLAYBOOK plan/spec pointer and
make the active-intent document set available to DOC010/DOC011 through
`scan_set`.

- [ ] **Step 4: Update the documented DOC range**

Change live descriptions from DOC001-DOC012 to DOC001-DOC022 and update the
existing declaration that rejects retired range claims. Run the check
immediately after `.docsync.toml` changes:

```bash
python scripts/doc_state_sync.py --check
```

Expected initially: deterministic DOC021/DOC022 findings for real lifecycle or
authority drift. Repair the documents or registry based on repository truth;
never exempt an active contradiction.

- [ ] **Step 5: Prove the current failure class**

In a temporary test corpus, leave an obsolete plan's prose unchanged, mark it
`superseded`, and point the authority source at it. Confirm DOC022 fails. Point
the source at the active replacement and confirm it passes.

- [ ] **Step 6: Sync and commit the repository policy**

```bash
python scripts/doc_state_sync.py --fix
pytest tests/test_docsync_contract_compat.py tests/test_docsync_corpus.py \
  tests/test_docsync_markdown.py tests/test_docsync_contracts.py \
  tests/test_docsync_intent.py tests/test_docsync_cli.py \
  tests/test_docsync_declarations.py tests/test_docsync_integrity.py \
  tests/test_docsync_logic.py tests/test_docsync_parser.py tests/test_docsync_renderer.py tests/test_docsync_test_count.py -q
pre-commit run --all-files
python scripts/doc_state_sync.py --check
git diff --check
```

Stage each changed path by name, including PLAYBOOK and SESSION_CONTEXT
together if docsync changed both. Commit:

```bash
git commit -m "feat(docsync): Guard plan and spec authority"
```

### Task 9: Reduce the two facade modules without a big-bang rewrite

**Files:**

- Modify: `scripts/docsync/integrity.py`
- Modify: `scripts/docsync/declarations.py`
- Modify: `scripts/docsync/__init__.py`
- Modify: `tests/test_docsync_integrity.py`
- Modify: `tests/test_docsync_declarations.py`
- Test: all docsync tests

**Interfaces:**

- Consumes: the extracted corpus, Markdown and contract kernel.
- Produces: facades that orchestrate policy checks without owning shared
  parsing, storage or configuration responsibilities.

- [ ] **Step 1: Remove compatibility imports only after caller migration**

Use:

```bash
rg -n "docsync\.(integrity|declarations) import.*(_Files|_normalize_reference|_joined_text|_declared_matches|_headings|_list_numbers_under)" scripts tests
```

Move each remaining caller to the owning module. The command must return no
private compatibility imports before aliases are deleted.

- [ ] **Step 2: Group repository policy checks by responsibility**

Keep DOC001-DOC008 and DOC012 behavior unchanged, but move their helpers into
focused modules only where a complete responsibility moves with its tests:

- reference/tracked-path policy;
- active-definition and next-work policy;
- test-count authority policy;
- archive/session rendering policy.

`integrity.py` remains the stable aggregate facade. Do not create one module
per DOC code.

- [ ] **Step 3: Separate declaration parsing from evaluation**

Leave DOC009-DOC011 evaluation together where they share matching behavior;
move TOML shape validation into `contracts.py` and repository access into
`corpus.py`. `declarations.py` remains the stable aggregate facade.

- [ ] **Step 4: Run mutation and full parity tests after each move**

```bash
pytest tests/test_docsync_contract_compat.py tests/test_docsync_corpus.py \
  tests/test_docsync_markdown.py tests/test_docsync_contracts.py \
  tests/test_docsync_intent.py tests/test_docsync_cli.py \
  tests/test_docsync_declarations.py tests/test_docsync_integrity.py \
  tests/test_docsync_logic.py tests/test_docsync_parser.py tests/test_docsync_renderer.py tests/test_docsync_test_count.py -q
python scripts/doc_state_sync.py --check
```

Expected: identical diagnostics for existing fixtures and active repository
state.

- [ ] **Step 5: Commit the bounded facade reduction**

Stage only the modules and tests actually moved, then commit:

```bash
git commit -m "refactor(docsync): Separate contract and policy layers"
```

### Task 10: Final verification and documentation

**Files:**

- Modify: `PLAYBOOK.md`
- Modify: `.claude/SESSION_CONTEXT.md` through docsync
- Modify: `docs/history/reports/` only if execution reveals a material audit
  result
- Test: full repository gates

- [ ] **Step 1: Read every cumulative changed file whole**

Derive the set from:

```bash
git diff --name-only origin/main...HEAD
```

Confirm no generic kernel module contains repository policy vocabulary and no
live document still states DOC001-DOC012 as the full range.

- [ ] **Step 2: Run the full ordered gate**

```bash
python scripts/doc_state_sync.py --fix
pytest -q
pre-commit run --all-files
python scripts/doc_state_sync.py --check
git diff --check
```

Expected: all commands exit 0, apart from the documented active root batch
warning if a later batch is open.

- [ ] **Step 3: Repeat the two required mutations**

Temporarily remove an intent lifecycle record and verify DOC021 fails. Restore
it; temporarily point an authority at a superseded plan and verify DOC022
fails. Restore the files and rerun the full ordered gate.

- [ ] **Step 4: Record completion and commit**

Update PLAYBOOK Sections 3-4, run docsync again, stage exact paths and commit:

```bash
git commit -m "docs(docsync): Record guarded intent authority"
```

## Plan Self-Review

- The plan guards the source of intended truth instead of relying on a final
  human sweep.
- The engine remains repository-agnostic; all ScrobbleScope vocabulary is
  confined to configuration and repository policy.
- `integrity.py` and `declarations.py` are reduced through tested seams, not
  rewritten at once.
- Existing public facades, diagnostic ordering and CLI exit codes remain
  stable throughout migration.
- The central registry prevents a document from making itself authoritative.
- The frontend gate is deliberately outside this plan and has its own deferred
  plan.

