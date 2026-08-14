### WP-1 Revision: Archival Naming Conventions

**Rationale (Repo Audit Findings):**
The drafted WP-1 instructs the agent to move `BATCH13_PROPOSAL.md` into the history folder without changing its suffix, explicitly citing `BATCH12_PROPOSAL.md` as the precedent. 

A review of the repository's `docs/history/` directory reveals that this is a false precedent. The established convention for completed and archived batches is the `_DEFINITION.md` suffix (e.g., `BATCH0_DEFINITION.md` through `BATCH10_DEFINITION_2026-02-21.md`). The term "Proposal" dictates an unexecuted, pending state, whereas the `history` folder is meant to act as a permanent record of what was defined and executed. Batch 14 is specifically a "Doc Hygiene" batch, making this the correct time to enforce structural consistency across the archives rather than perpetuating a recent anomaly.

**Required Changes to WP-1:**
Modify the deliverables in WP-1 to enforce the standard naming convention:

1. **Modify the Archival Target:** When moving the root file, rename it. 
   * Execute: `git mv BATCH13_PROPOSAL.md docs/history/BATCH13_DEFINITION.md`
2. **Retroactive Cleanup:** Fix the anomaly introduced during Batch 12. 
   * Execute: `git mv docs/history/BATCH12_PROPOSAL.md docs/history/BATCH12_DEFINITION.md`
3. **Link Updates:** Ensure that the PLAYBOOK Section 2 table updates explicitly link to these newly standardized `_DEFINITION.md` filenames, rather than `_PROPOSAL.md`.

### WP-2 Revision: Structural Package Extraction (Zero Logic Changes)

**Rationale (Repo Audit Findings):**
The drafted WP-2 proposes injecting complex new routing logic, a `--split-archive` migration function, and root-level file scanning directly into `scripts/doc_state_sync.py`. Currently, this script is a ~450-line monolith handling everything from regex parsing to file I/O. Furthermore, the draft's WP-3 proposes splitting the *test* file into five separate files. Mapping five isolated test files back to a single monolithic source script creates a severe architectural asymmetry and violates the Single Responsibility Principle. 

To maintain system stability, you must execute a pure structural package extraction *before* introducing the new batch-routing features.

**Required Changes to WP-2:**
Completely rewrite WP-2 to focus strictly on structural decomposition. Move the proposed feature additions (per-batch routing and migration) to a new WP-3.

1. **Package Creation:** Create a new directory `scripts/docsync/` with an `__init__.py`.
2. **Module Decomposition:** Extract the contents of the monolithic `doc_state_sync.py` into strictly scoped modules:
   * `models.py`: Extract all pure dataclasses (`Entry`, `ActiveBatchState`, `SyncResult`).
   * `parser.py`: Extract all regex constants and extraction logic (`_find_section`, `_parse_entries`, `_extract_entry_batch`, `_parse_active_batch_state`).
   * `renderer.py`: Extract markdown formatting logic (`_render_section4`, `_render_archive`, `_build_status_block`).
   * `logic.py`: Extract the core domain rules (`_sync`, `_cross_validate`). Ensure it orchestrates the parser and renderer without directly calling `path.read_text()` if possible.
   * `cli.py`: Extract `main()`, `argparse` configuration, and file I/O helpers (`_read_lines`, `_write_lines`).
3. **Entrypoint Preservation:** Replace the original `scripts/doc_state_sync.py` with a thin wrapper that simply imports and executes `docsync.cli.main()`. This guarantees existing CI pipelines and playbook commands do not break.
4. **Test Alignment:** Pull the test-splitting logic previously proposed in the draft's WP-3 into this package extraction. The new test files (e.g., `test_parser.py`, `test_renderer.py`) must map 1:1 with the newly created modules.
5. **Acceptance Criteria:** Zero feature changes. Running `python scripts/doc_state_sync.py --check` and the test suite must pass exactly as they did before the refactor.

### WP-3 Revision: Per-Batch Routing & Migration Feature Implementation

**Rationale (Repo Audit Findings):**
The drafted BATCH14_PROPOSAL.md originally conflated this feature work into WP-2 inside the monolithic `scripts/doc_state_sync.py` file. Because we are now executing a strict package extraction first (our new WP-2), the implementation of the per-batch routing, `--split-archive` migration, and root-level scanning must be strictly mapped into the new `docsync/` package modules. We must aggressively prevent I/O operations from leaking into the pure logic modules.

**Required Changes to WP-3:**
Define WP-3 as the explicit feature implementation phase, dictating exactly which modules from the newly created `docsync/` package will house the new functions:

1. **Distribute to `cli.py` (I/O & Orchestration):**
   * Add the `--split-archive` flag to `argparse`.
   * Implement `_get_batch_log_path(batch_num)`.
   * Implement the file-system operations for `_check_root_batch_files(root: Path)` (scanning the directory for `BATCH*.md`).
   * Modify `main()` to handle reading the new `BATCHN_LOG.md` files, passing their contents to the logic layer, and writing the updated logs back to disk.

2. **Distribute to `logic.py` (Core Data Manipulation):**
   * Modify the core `_sync` function to return the proposed `batch_log_updates: dict[int, list[str]]` within the `SyncResult`.
   * Implement the pure-Python logic for `_merge_entries_into_log` (taking existing lines and new entries, returning deduplicated string lists).
   * Implement the pure-Python logic for `_split_archive` (taking the full monolith string list, returning grouped string lists mapped by batch number, without executing any `Path.write_text` calls).

3. **Execution Steps (Preserved but Adapted):**
   * Retain the instruction to execute the migration live during this WP:
     * Run `python scripts/doc_state_sync.py --split-archive`
     * Run `python scripts/doc_state_sync.py --check` (must show zero drift).
   * Require two distinct commits: one for the feature implementation (`feat(doc-sync):...`) and one for the resulting archive split (`chore(history):...`).

   ### WP-4 Revision: Archival Test Coverage Alignment

**Rationale (Repo Audit Findings):**
The drafted WP-4 proposes creating a standalone test file named `test_doc_state_sync_archival.py` to house the 12 new tests for the routing and migration features. 

This violates a fundamental testing architecture principle: tests must be organized by the structural component they verify, not by the historical batch or feature ticket that introduced them. Because our revised WP-2 enforces a strict 1:1 mapping between source modules (`logic.py`, `cli.py`) and their test files (`test_logic.py`, `test_cli.py`), creating a distinct `_archival.py` file breaks this symmetry. It creates an orphaned test file that cross-contaminates boundaries by testing logic from multiple different modules.

**Required Changes to WP-4:**
Rewrite WP-4 to eliminate the creation of a standalone feature-based test file. The new tests must be integrated directly into the modular test files established in WP-2.

1. **Eliminate the Orphan File:** Remove all references to creating `tests/test_doc_state_sync_archival.py`.
2. **Distribute to `test_logic.py`:** Instruct the agent to add the tests concerning core data manipulation to the logic test suite. This includes:
   * `test_tagged_entry_routed_to_batch_log` (`_sync` integration)
   * `test_untagged_entry_stays_in_monolith` (`_sync` integration)
   * `test_two_batches_in_one_sync` (`_sync` integration)
   * `test_batch_log_created_on_first_entry` (`_merge_entries_into_log`)
   * `test_batch_log_deduplicates_entries` (`_merge_entries_into_log`)
   * `test_split_archive_routes_by_batch` (`_split_archive`)
   * `test_split_archive_retains_untagged_in_monolith` (`_split_archive`)
   * `test_split_archive_deduplicates_on_merge` (`_split_archive`)
3. **Distribute to `test_cli.py`:** Instruct the agent to add the tests concerning file path resolution, I/O scanning, and end-to-end execution to the CLI test suite. This includes:
   * `test_get_batch_log_path_returns_correct_path` (`_get_batch_log_path`)
   * `test_check_root_batch_files_warns` (`_check_root_batch_files`)
   * `test_check_root_batch_files_no_warn_when_clean` (`_check_root_batch_files`)
   * `test_fix_then_check_clean_with_batch_logs` (`main()` end-to-end)
4. **Acceptance Criteria Update:** Ensure the validation command explicitly runs the full suite (e.g., `pytest tests/ -v`) to verify the +12 test delta, rather than targeting an isolated, incorrectly named file.

### WP-5 Revision: AGENTS.md Close-out Procedure & `MEMORY.md` Hallucination

**Rationale (Repo Audit Findings):**
The drafted WP-5 proposes adding a formal close-out procedure to `AGENTS.md` that instructs the outgoing agent to: *"Update MEMORY.md: new test count, completed batch, next batch plan..."*.

A strict audit of the repository's file structure confirms that a `MEMORY.md` file **does not exist** anywhere in the project. This is a severe hallucination based on generic agent workflows rather than the specific architecture of this repository. The actual file responsible for maintaining agent state and session handoffs is `.claude/SESSION_CONTEXT.md`. 

Furthermore, `scripts/doc_state_sync.py` is already explicitly programmed to *automatically* update the status block of `.claude/SESSION_CONTEXT.md` when the `--fix` command is run. Instructing an agent to manually update a non-existent `MEMORY.md` file creates operational friction, breaks the automated pipeline, and introduces conflicting sources of truth.

**Required Changes to WP-5:**
Revise the close-out procedure deliverables in WP-5 to align strictly with the repository's actual synchronization mechanics:

1. **Eradicate `MEMORY.md`:** Remove all references to `MEMORY.md` from `BATCH14_PROPOSAL.md` and the proposed text for `AGENTS.md`.
2. **Correct the Handoff Mechanism:** Update the step (5c) and checklist to reflect the correct architecture:
   * The outgoing agent's final task is to verify that `.claude/SESSION_CONTEXT.md` was successfully and automatically updated by the `doc_state_sync.py --fix` execution.
   * Any subjective context or architectural handoff notes (e.g., explaining the new per-batch log routing to the incoming agent) must be documented in the `PLAYBOOK.md` under the active batch or "Next action" section, ensuring `PLAYBOOK.md` remains the absolute source of truth.
3. **Verify the Close-Out Checklist:** Ensure the 7-step checklist explicitly names `.claude/SESSION_CONTEXT.md` and `PLAYBOOK.md` (Sections 3 and 4) as the only files dictating state transition.