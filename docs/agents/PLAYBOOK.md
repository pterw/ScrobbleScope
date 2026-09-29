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

### Batch index (completed batches archived; the active batch, if any, is listed last)

| Batch | Title | Definition | Log |
|-------|-------|------------|-----|
| 0 | Baseline freeze + approval parity suite | `docs/history/definitions/BATCH0_DEFINITION.md` | -- |
| 1 | Proper upstream failure state + retry UX | `docs/history/definitions/BATCH1_DEFINITION.md` | -- |
| 2 | Personalized minimum listening year | `docs/history/definitions/BATCH2_DEFINITION.md` | -- |
| 3 | Remove nested thread pattern | `docs/history/definitions/BATCH3_DEFINITION.md` | `docs/history/logs/BATCH3_LOG.md` |
| 4 | Expand test coverage significantly | `docs/history/definitions/BATCH4_DEFINITION.md` | `docs/history/logs/BATCH4_LOG.md` |
| 5 | Docstring + comment normalization | `docs/history/definitions/BATCH5_DEFINITION.md` | `docs/history/logs/BATCH5_LOG.md` |
| 6 | Frontend refinement/tweaks | `docs/history/definitions/BATCH6_DEFINITION.md` | `docs/history/logs/BATCH6_LOG.md` |
| 7 | Persistent metadata layer (Postgres) | `docs/history/definitions/BATCH7_DEFINITION.md` | `docs/history/logs/BATCH7_LOG.md` |
| 8 | Modular refactor (app factory + blueprints) | `docs/history/definitions/BATCH8_DEFINITION.md` | `docs/history/logs/BATCH8_LOG.md` |
| 9 | Audit remediation (WP-1 through WP-8) | `docs/history/definitions/BATCH9_DEFINITION.md` | `docs/history/logs/BATCH9_LOG.md` |
| 10 | Gemini audit remediation (WP-1 through WP-9) | `docs/history/definitions/BATCH10_DEFINITION_2026-02-21.md` | `docs/history/logs/BATCH10_LOG.md` |
| 11 | Gemini Priority 2 audit remediation (SoC, DRY, architecture) | `docs/history/definitions/BATCH11_DEFINITION.md` | `docs/history/logs/BATCH11_LOG.md` |
| 12 | Polish and observability (CSS, formatting, SoC, progress) | `docs/history/definitions/BATCH12_DEFINITION.md` | `docs/history/logs/BATCH12_LOG.md` |
| 13 | Internal decomposition and coverage hardening | `docs/history/definitions/BATCH13_DEFINITION.md` | `docs/history/logs/BATCH13_LOG.md` |
| 14 | Doc hygiene (archive restructure, docsync package, per-batch routing) | `docs/history/definitions/BATCH14_DEFINITION.md` | `docs/history/logs/BATCH14_LOG.md` |
| 15 | Alignment, hardening, and handoff | `docs/history/definitions/BATCH15_DEFINITION.md` | `docs/history/logs/BATCH15_LOG.md` |
| 16 | Script hygiene, local dev hardening, and integration testing | `docs/history/definitions/BATCH16_DEFINITION.md` | `docs/history/logs/BATCH16_LOG.md` |
| 17 | Agent bootstrap hardening, CI/CD improvements, and dep pinning | `docs/history/definitions/BATCH17_DEFINITION.md` | `docs/history/logs/BATCH17_LOG.md` |
| 18 | Scrobble heatmap -- iteration 1 | `docs/history/definitions/BATCH18_DEFINITION.md` | `docs/history/logs/BATCH18_LOG.md` |
| 19 | Heatmap polish -- frame, KPIs, mobile layout | `docs/history/definitions/BATCH19_DEFINITION.md` | `docs/history/logs/BATCH19_LOG.md` |
| 20 | File-hygiene + docs methodology refresh | `docs/history/definitions/BATCH20_DEFINITION.md` | `docs/history/logs/BATCH20_LOG.md` |
| 21 | UI overhaul -- Tailwind + daisyUI migration | `docs/history/definitions/BATCH21_DEFINITION.md` | `docs/history/logs/BATCH21_LOG.md` |
| 22 | Enrichment providers and original release years | `docs/history/definitions/BATCH22_DEFINITION.md` | `docs/history/logs/BATCH22_LOG.md` |
| 23 | Spotify Extended Streaming History import | `BATCH23_DEFINITION.md` | active -- Section 4 |

A batch's close-out entry sits in its per-batch log only when the heading
carried a `(Batch N WP-X)` tag (as Batch 18's did). Close-outs tagged
`(Batch N close-out)` are not parser-recognized and were routed to the
monolith archive instead -- Batches 19 and 20 are the current examples.
See FINDINGS F-DOCSYNC-3.

### Open decisions (owner confirmation needed)

1. Persistent store choice: Postgres only or Postgres + Redis.
2. Retry UX policy: immediate retry button only, or retry + cooldown messaging.
3. Error copy style and user-facing tone for upstream failures.

---

## 3. Active batch + next action

- **Batch 23 is active.** Definition: `BATCH23_DEFINITION.md`.
  Branch: `feat/batch23-wp0-hygiene`. The branch was cut from `test`; run the
  worktree guard with `--base-ref origin/test`.
- **Next action:** WP-0 is next.
  Part A and Part B are complete. Part C continues through the three
  follow-on plans in the order recorded under "After this plan" in
  `docs/superpowers/plans/2026-09-23-batch23-wp0-reconcile-and-clear.md`:
  control-plane, frontend, then test infrastructure and dependencies.
  The control-plane plan is written and reviewed:
  `docs/superpowers/plans/2026-09-25-batch23-wp0-control-plane.md`. Its eight
  tasks are all complete (Task 7 landed `8cf5fd4`..`c39da3c`). The frontend
  and test-infrastructure/dependencies plans are now written and reviewed:
  `docs/superpowers/plans/2026-09-26-batch23-wp0-frontend.md` and
  `docs/superpowers/plans/2026-09-26-batch23-wp0-test-infra-deps.md`. The
  frontend plan and the test-infrastructure/dependencies plan are both fully
  executed (every task in each has landed). The three plans' carried items
  are closed out, and their final code review of the whole branch ran on
  2026-09-27; its one fix wave has landed and passed a scoped re-review
  (see Section 4). Next action: the WP-0 close-out below. The
  definition owns WP-0 scope and acceptance; `docs/agents/FINDINGS.md`
  owns open finding status.
- **WP-0 close-out:** Re-review `e7e076b` independently, review the whole
  branch, verify Part C's listed findings member by member, and run the
  final gates in the definition. Then write one tagged `(Batch 23 WP-0)`
  Section 4 entry, carrying an explicit `**Status:** WP-0 complete` line
  (DOC007 requires it before the package reads done). Earlier WP-0 commits
  remain untagged by the owner's 2026-09-23 ruling in the definition.
- **Batch 23 close-out obligation:** WP-7 includes the deferred Batch 21
  frontend and accessibility audit; the batch cannot close without it.

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
  - `<!-- DOCSYNC:CURRENT-BATCH-END -->

<!-- DOCSYNC:CURRENT-BATCH-START -->

<!-- DOCSYNC:CURRENT-BATCH-END -->

### 2026-09-29 - Show the whole focus ring on the unmatched album links

Side task, no batch tag: the album title link and the provider badge on the unmatched report now show their whole keyboard focus ring, part of Batch 23 WP-0 Part C. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

The fault came from the controller's keyboard check of the rebuilt page (owner ruling 8). The text column carried `overflow-hidden`, which cut the title's ring to its bottom edge and the badge's to two sides. The class is gone; the table cell's own overflow and padding contain the column, and the title still wraps while the artist line still ends in an ellipsis.

The frontend gate's unmatched check now reaches both links by real Tab presses and judges each ring on painted pixels: a focused screenshot against a blurred one, each side outside the box. A cut ring computes the same outline as a whole one, so no computed style is read. Its fixture gains one Deezer row, still twelve rows, so a badge renders. Live probes: red with the class planted back and red with the clip moved into CSS, green on the fix.

Validation: `pytest -q` -- **2130 passed**.

### 2026-09-29 - docsync refuses a path that leaves the repository by a junction

Side task, no batch tag: docsync's path boundary and its declared-path spelling, part of Batch 23 WP-0 Part C. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

The Task 10 review raised two Minors, and the controller's probe widened the first. On Windows a directory junction is not a symlink to `Path.is_symlink()`, so `resolve_within` walked straight through one, and its containment test ran only when the leaf existed. A new file reached through a junction was accepted and resolved outside the root; the same path with an existing leaf was refused. A publish creating that file would have written outside the repository.

`resolve_within` now refuses a junction wherever it refuses a symlink, and tests containment on the deepest existing ancestor, so a leaf that does not exist yet is no longer a way round. Either change alone closes the probe; a mount point is the same class. `_validate_documents` turns the `ValueError` from `relative_to` into the `DeclarationError` it already raises for a path outside the repository, so the CLI prints a typed diagnostic, not a traceback. `[untracked_essentials]` now refuses a path not written in normalised form, naming the spelling to write, as `[documents]` does, so `./x.json` and `x.json` are no longer reported as two files.

The tests build real junctions with `mklink /J` and remove them with `os.rmdir`. Each change was proved by mutation.
Validation: `pytest -q` -- **2126 passed**.

### 2026-09-29 - Heatmap focus ring paints whole; grid keys leave shortcuts alone

Side task, no batch tag: second code-review findings E1, E2, E3, E4, E5, E7 and E10 on the heatmap grid, part of Batch 23 WP-0 Part C. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

E1, E4: the cell outline was covered by later cells and clipped by the SVG, yet every computed-style check passed. One ring rect is now painted after every cell and moved to the keyboard-focused one. The SVG may paint past its box into 4px of room #heatmap-grid keeps round it, so the grid does not move: the viewBox, cell size and frame match the old layout at 390px and 1280px. The gate now reads the ring off screenshot pixels (first, interior and last cell, both profiles) instead of computed outline values, and asserts the grid still spans its frame.

E2, E3: a scroll no longer re-shows the hidden tooltip of a clicked cell, and a held Alt, Ctrl, Meta or Shift leaves the arrow, Home and End keys to the browser. E10: the A3 probe now records that its scroll happened.

E5: a breakpoint re-render gives focus back to the same day, and the new gate check `heatmap focus survives breakpoint` covers it. E7: the vacuous HEATMAP_PATH test is gone.

Owner ruling 11 (2026-09-29, "Consider ammending the CI and frontend_gate.toml, test, and files."): both heatmap keyboard-focus checks join `required` in `config/frontend_gate_checks.toml`, so neither can be disabled; the manifest test pins the new set. The gate goes from 38 to 39 checks and 63 to 64 runs.

Live probes: base code, ring painted first, no room in the grid's clip, a clipping SVG, the grid-moving viewBox padding, and each single fix reverted all went red; the fix stayed green.
Validation: `pytest -q` -- **2118 passed**.

### 2026-09-29 - Repo Assist pins the count it measures and skips browser tests

Side task, no batch tag: Repo Assist's rules and file grant, part of Batch 23 WP-0 Part C. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.
Review findings G1-G3: Repo Assist's rules predated the pinned test count and the browser marker, so a PR from it could not pass. Rule 4 now runs `--fix --test-count N` and never edits a count by hand. Owner ruling 11 (2026-09-29, "Consider ammending the CI and frontend_gate.toml, test, and files.") allowed the widened grant: both `allowed-files` lists gain `config/docsync.toml`, and the lock was regenerated with `gh aw compile repo-assist`, not edited.
Rule 5 runs `-m "not browser"` and counts the 43 browser tests by `--collect-only`, so N is still the whole suite. Task 4 audits both requirements files. `test.yml` runs `-m browser` without the directory, so the marker decides what runs; the same 43 tests run either way.
The new `tests/test_ci_workflows.py` checks that the compiled lock grants every file the procedure writes and that the source and the lock agree.
Validation: `pytest -q` -- **2117 passed**.
