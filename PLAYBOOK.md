# ScrobbleScope Execution Playbook

Date: 2026-02-22
Purpose: Single source of truth for work sequencing and execution history.
Rules for agent behaviour live in `AGENTS.md`; current-state snapshot in
`.claude/SESSION_CONTEXT.md`.

## 1. Why this document exists

- Provide a single source of truth for work sequencing.
- Enable continuation by another agent with minimal context loss.
- Prevent risky refactor-first changes before parity tests exist.

**Implementation principles:**
1. Approval tests before structural refactor.
2. No behavior-breaking refactors without parity checks.
3. Add observability before optimization where possible.
4. Keep changes batch-scoped and reversible.
5. Keep security-safe rendering (`tojson`, escaping) as baseline.

---

## 2. Batch order (strict sequence)

Completed batch definitions are archived individually under `docs/history/`.

### Completed batches (definitions archived)

| Batch | Title | Definition |
|-------|-------|------------|
| 0 | Baseline freeze + approval parity suite | `docs/history/definitions/BATCH0_DEFINITION.md` |
| 1 | Proper upstream failure state + retry UX | `docs/history/definitions/BATCH1_DEFINITION.md` |
| 2 | Personalized minimum listening year | `docs/history/definitions/BATCH2_DEFINITION.md` |
| 3 | Remove nested thread pattern | `docs/history/definitions/BATCH3_DEFINITION.md` |
| 4 | Expand test coverage significantly | `docs/history/definitions/BATCH4_DEFINITION.md` |
| 5 | Docstring + comment normalization | `docs/history/definitions/BATCH5_DEFINITION.md` |
| 6 | Frontend refinement/tweaks | `docs/history/definitions/BATCH6_DEFINITION.md` |
| 7 | Persistent metadata layer (Postgres) | `docs/history/definitions/BATCH7_DEFINITION.md` |
| 8 | Modular refactor (app factory + blueprints) | `docs/history/definitions/BATCH8_DEFINITION.md` |
| 9 | Audit remediation (WP-1 through WP-8) | `docs/history/definitions/BATCH9_DEFINITION.md` |
| 10 | Gemini audit remediation (WP-1 through WP-9) | `docs/history/definitions/BATCH10_DEFINITION_2026-02-21.md` |
| 11 | Gemini Priority 2 audit remediation (SoC, DRY, architecture) | `docs/history/definitions/BATCH11_DEFINITION.md` |
| 12 | Polish and observability (CSS, formatting, SoC, progress) | `docs/history/definitions/BATCH12_DEFINITION.md` |
| 13 | Internal decomposition and coverage hardening | `docs/history/definitions/BATCH13_DEFINITION.md` |
| 14 | Doc hygiene (archive restructure, docsync package, per-batch routing) | `docs/history/definitions/BATCH14_DEFINITION.md` |

### Open decisions (owner confirmation needed)

1. Persistent store choice: Postgres only or Postgres + Redis.
2. Retry UX policy: immediate retry button only, or retry + cooldown messaging.
3. Error copy style and user-facing tone for upstream failures.

---

## 3. Active batch + next action

- **Between batches.** No active batch is open right now.
- **Current mode:** side-task patching and quality fixes only (no new feature batch).
- Future batch feature candidates (confirmed by owner roadmap, batch number TBD):
  - **Top songs**: rank most-played tracks for a year (Last.fm + possibly
    Spotify enrichment, separate background task + loading/results flow).
  - **Listening heatmap**: scrobble density calendar for last 365 days
    (Last.fm-only, lighter background task).
- **Batch 14 is complete.** All 5 WPs done + staleness fix side-task.
  Definition: `docs/history/definitions/BATCH14_DEFINITION.md`.
  - WP-1: archive and rename definition files for batches 11/12/13.
  - WP-2: extract `scripts/docsync/` package and split test monolith.
  - WP-3: per-batch log routing and `--split-archive` migration.
  - WP-4: 12 new tests for WP-3 enhancements (+306 total).
  - WP-5: update `AGENTS.md` with doc-sync architecture + close-out procedure.
- Do not start feature work (top songs, heatmap) until owner defines scope
  and assigns a batch number.

---

## 4. Execution log (for agent handoff)

Keep only the active window here: current batch entries plus the latest 4
non-current operational logs. Older dated entries live in
`docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`.

**How to read dated entries:**
- Each heading `YYYY-MM-DD - ...` is a completion/addendum log.
- Untagged side-task history: `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`.
- Tagged batch history: per-batch logs under `docs/history/logs/`.
- Batch scope/acceptance criteria: definitions under `docs/history/definitions/`.
- Current-batch boundaries are machine-managed (do not move entries manually):
  - `<!-- DOCSYNC:CURRENT-BATCH-START -->`
  - `<!-- DOCSYNC:CURRENT-BATCH-END -->`
- After any edit here, run `python scripts/doc_state_sync.py --fix`.
- Archive search: `rg -n "^### 20" docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`

<!-- DOCSYNC:CURRENT-BATCH-START -->

<!-- DOCSYNC:CURRENT-BATCH-END -->

### 2026-02-27 - Revalidate audit findings and prepare next-agent packet (side-task)

**Scope:** `docs/history/AUDIT_2026-02-27_MULTI_AGENT_SWEEP.md`,
`tests/test_docsync_logic.py` (format-only), repo-wide quality gates.

**Plan vs implementation:**
- Planned: verify previously reported findings against current branch state,
  refresh stale assertions, and produce implementation-ready guidance for the
  next agent handoff.
- Implemented: re-ran full validations, updated stale test baseline and
  resolved-item status in the audit report, and added a scoped next-agent
  implementation packet with acceptance criteria.

**Deviations:**
- No behavioral code changes were required; only audit/report updates plus
  formatter-normalized whitespace in `tests/test_docsync_logic.py`.

**Validation:**
- `pre-commit run --all-files` (pass)
- `pytest -q` (**310 passed**, 3 deprecation warnings from aiohttp connector)
- `python scripts/doc_state_sync.py --check` (pass)

**Forward guidance:**
- Execute the next-agent packet in commit-sized slices: test-module split,
  low-risk orchestrator extraction, then CI/session policy wording alignment.

### 2026-02-27 - Harden docsync non-happy-path coverage + path guidance (side-task)

**Scope:** `tests/test_docsync_logic.py`, `tests/test_docsync_cli.py`,
`AGENTS.md`, `PLAYBOOK.md`.

**Plan vs implementation:**
- Planned: enforce anti-happy-path discipline for docsync archive-link and
  migration handling, and remove path ambiguity between untagged archive,
  per-batch logs, and definitions.
- Implemented: added adversarial tests for `docs/logarchive` link validation
  (exists/missing) and for `--split-archive` missing-input failure (`exit 2`),
  plus explicit archive/log/definition lookup guidance in AGENTS and PLAYBOOK.

**Deviations:**
- One assertion was adjusted to be path-separator-agnostic on Windows
  (`PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` substring) after first run exposed
  slash-vs-backslash brittleness.

**Validation:**
- `pytest -q tests/test_docsync_logic.py tests/test_docsync_cli.py`
  (**57 passed**)
- `pytest -q` (**310 passed**, 3 deprecation warnings from aiohttp connector)
- `python scripts/doc_state_sync.py --check` (pass)

**Forward guidance:**
- Keep new docsync tests behavior-focused (real inputs + failure paths), not
  mock-call-only checks, when adding future archive-routing rules.

### 2026-02-27 - Migrate monolith archive path to docs/logarchive (side-task)

**Scope:** `scripts/docsync` path canonicalization, pointer compatibility docs,
doc references, regression validation.

**Plan vs implementation:**
- Planned: stop using the legacy history monolith paths
  (`docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` and
  `docs/history/logs/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`) as the
  canonical monolith location and move to a dedicated `docs/logarchive/`
  folder with clear pointers from legacy paths.
- Implemented: switched docsync `ARCHIVE_PATH` to
  `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`, copied canonical
  archive content there, converted both legacy monolith files into pointer
  documents, and added `docs/logarchive/README.md` lookup guidance.

**Deviations:**
- Historical documents under `docs/history/definitions/` and batch logs were
  left unchanged to preserve historical wording; compatibility pointers prevent
  breakage for legacy references.

**Validation:**
- `python scripts/doc_state_sync.py --fix`
- `python scripts/doc_state_sync.py --check`
- `pytest -q tests/test_docsync_cli.py tests/test_docsync_logic.py`
  `tests/test_docsync_parser.py tests/test_docsync_renderer.py` (**103 passed**)
- `pytest -q` (**307 passed**, 3 deprecation warnings from aiohttp connector)

**Forward guidance:**
- Use `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` for untagged archive
  search and keep per-batch logs under `docs/history/logs/` as the tagged route.

### 2026-02-27 - Branch hygiene cleanup after main diff review (side-task)

**Scope:** orchestration hygiene (`.gitignore`, PLAYBOOK state consistency,
root audit-file placement), docsync warning cleanup.

**Plan vs implementation:**
- Planned: remove non-actionable docsync warning noise and align tracked state
  with the "local-only" `.claude/SESSION_CONTEXT.md` policy.
- Implemented: scoped `BATCH*_AUDIT*.md` ignore rule to repo root only,
  moved `BATCH14_PROPOSAL_AUDIT1.md` from root into `docs/history/`, and
  recorded the side-task in Section 4.

**Deviations:**
- `git mv` could not be used for `BATCH14_PROPOSAL_AUDIT1.md` because the file
  was not under version control; file-system move was used instead.

**Validation:**
- Ran `python scripts/doc_state_sync.py --fix` and
  `python scripts/doc_state_sync.py --check` after edits.

**Forward guidance:**
- Keep root-only draft/audit patterns scoped with leading `/` in `.gitignore`
  so archive destinations under `docs/history/` remain trackable.
