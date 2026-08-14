# doc_state_sync Audit -- 2026-02-25

**Scope:** `scripts/docsync/` package (all 5 modules), full test suite
(4 test files, 106 docsync tests), and orchestration documents
(AGENTS.md, PLAYBOOK.md, SESSION_CONTEXT.md, DEVELOPMENT.md).

**Goals:** Verify rotation logic, check for monolith growth risk, assess
structural soundness, identify bugs, code smells, DRY/SoC violations,
and evaluate whether DEVELOPMENT.md goals are being met.

---

## Summary table

| # | Severity | Location | Issue |
|---|----------|----------|-------|
| 1 | **BUG** | `cli.py:215-217` | `--fix` always rewrites PLAYBOOK + ARCHIVE unconditionally |
| 2 | Smell | `renderer.py:15`, `logic.py:286,317` | Test-count regex defined 3 times |
| 3 | Smell | `logic.py:61-70`, `logic.py:228-237` | Dedup-sort pattern copy-pasted |
| 4 | Design | `models.py:13`, `logic.py:152-162` | `Entry.start_idx` leaks parse context |
| 5 | Smell | `logic.py:184-188` | Sentinel `-1` for absent current batch |
| 6 | Risk | `parser.py:37` | `ENTRY_BATCH_RE` too loose - misroutes titles |
| 7 | Defensive | `parser.py:102-103` | Asymmetric marker selection, duplicates silently ignored |
| 8 | Hygiene | `logic.py:345-348` | Hardcoded stale-phrase list not maintained |
| 9a | Test | `test_docsync_parser.py:94` | Misleading test docstring |
| 9b | Test | `test_docsync_renderer.py:136` | Weak `or` assertion |
| 9c | Test | `test_docsync_parser.py` | No coverage of duplicate section headings |
| 9d | Test | `test_docsync_parser.py` | No adversarial test for loose ENTRY_BATCH_RE |
| 9e | Test | `test_docsync_logic.py:289` | Test comment implies date-sort guarantee that doesn't exist |
| 10 | Positive | Architecture | Goals of DEVELOPMENT.md are valid and well-executed |
| 11 | Hygiene | `cli.py:115` | Late local import of SyncError inconsistent |

---

## Finding 1 -- BUG: `--fix` unconditionally rewrites PLAYBOOK + ARCHIVE

**File:** `scripts/docsync/cli.py:215-217`

```python
# args.fix block
if changed:
    _write_lines(PLAYBOOK_PATH, result.playbook_lines)   # BUG: always written
    _write_lines(ARCHIVE_PATH, result.archive_lines)     # BUG: always written
    if SESSION_CONTEXT_PATH in changed:                  # correctly gated
        _write_lines(SESSION_CONTEXT_PATH, result.session_lines)
    for batch_num, new_batch_lines in result.batch_log_updates.items():
        batch_log_path = _get_batch_log_path(batch_num)
        if batch_log_path in changed:                    # correctly gated
            _write_lines(batch_log_path, new_batch_lines)
```

SESSION_CONTEXT and per-batch log writes are gated on `if path in changed`.
PLAYBOOK and ARCHIVE are not. Any `--fix` run that has *any* change
(e.g., SESSION_CONTEXT is stale) also rewrites PLAYBOOK.md and the archive
with no content change, advancing their mtime. This causes spurious `git diff`
noise and could confuse downstream tooling that watches file timestamps.

The intent is clearly consistent selective writes -- the rest of the block
already follows that pattern.

**Recommended fix:**

```python
if PLAYBOOK_PATH in changed:
    _write_lines(PLAYBOOK_PATH, result.playbook_lines)
if ARCHIVE_PATH in changed:
    _write_lines(ARCHIVE_PATH, result.archive_lines)
```

---

## Finding 2 -- DRY: Test-count regex defined 3 times

**Files:** `scripts/docsync/renderer.py:15`, `scripts/docsync/logic.py:286`,
`scripts/docsync/logic.py:317`

The pattern `r"\*\*(\d+)\s+(?:tests?\s+)?pass(?:ing|ed)\*\*"` is compiled
three times under two names: `_TEST_COUNT_RE` in renderer, and two `re.compile`
inline calls in logic. All three are identical. Any future change to how agents
format test counts (e.g., `**306 tests pass**`) requires updating three
locations, and a single missed update introduces a silent mismatch where
`_build_status_block` and `_cross_validate` disagree on what counts as valid.

**Recommended fix:** Define once in `parser.py` alongside other compiled
patterns:

```python
TEST_COUNT_RE = re.compile(r"\*\*(\d+)\s+(?:tests?\s+)?pass(?:ing|ed)\*\*")
```

Import in `renderer.py` and `logic.py`. Remove the two inline compiles and
the `_TEST_COUNT_RE` module constant.

---

## Finding 3 -- DRY: Dedup-sort pattern copy-pasted

**File:** `scripts/docsync/logic.py:61-70` and `logic.py:228-237`

The deduplication loop is identical in structure across both sites:

```python
combined_annotated = list(enumerate(combined))
combined_annotated.sort(key=lambda pair: (-_date_key(pair[1].date), pair[0]))
deduped: list[Entry] = []
seen: set[str] = set()
for _, entry in combined_annotated:
    if entry.fingerprint in seen:
        continue
    seen.add(entry.fingerprint)
    deduped.append(entry)
```

The only difference is the input list name and the output variable name.

**Recommended fix:** Extract a private helper:

```python
def _dedup_sorted(entries: list[Entry]) -> list[Entry]:
    annotated = list(enumerate(entries))
    annotated.sort(key=lambda pair: (-_date_key(pair[1].date), pair[0]))
    seen: set[str] = set()
    out: list[Entry] = []
    for _, entry in annotated:
        if entry.fingerprint not in seen:
            seen.add(entry.fingerprint)
            out.append(entry)
    return out
```

Call it from both `_merge_entries_into_log` and `_sync`.

---

## Finding 4 -- Design: `Entry.start_idx` leaks parse context

**Files:** `scripts/docsync/models.py:13-22`, `scripts/docsync/logic.py:152-162`

`Entry.start_idx` records the line index of the heading within the slice that
was passed to `_parse_entries`. It is used for exactly one purpose in logic.py:
classifying whether an entry falls inside the CURRENT-BATCH markers:

```python
current_entries = [
    entry for entry in cleaned_entries
    if marker_start < entry.start_idx < marker_end
]
```

After rotation into an archive or batch log, this index is stale -- it refers
to a position in a PLAYBOOK section that has since been rewritten. The `Entry`
dataclass is used in archive contexts where `start_idx` carries no meaning.

This creates a hidden coupling: test helpers that construct `Entry` objects
with `start_idx=0` (which all current tests do) only avoid bugs because those
tests don't invoke the marker-based partitioning path. If a test were written
that called `_sync` directly with manually constructed entries, wrong
`start_idx` values would silently misclassify entries.

**Recommended approach:** Replace the reliance on `start_idx` with an explicit
partition at the parse boundary. `_parse_entries` could return entries in two
lists (inside_markers, outside_markers), removing the need to carry positional
context in the model at all, or add an `in_current_block: bool` field to Entry
that is set only at the point where section_4 is parsed.

This is a medium-effort refactor; the current code is not broken, but it is
fragile and the `start_idx` field is confusing in non-section-4 contexts.

---

## Finding 5 -- Code smell: Sentinel `-1` for absent current batch

**File:** `scripts/docsync/logic.py:184-188`

```python
current_batch_num = (
    section_3_state.current_batch
    if section_3_state.current_batch is not None
    else -1
)
```

Used four lines later in the always_rotate vs. keepable classification:

```python
if entry_batch is not None and entry_batch != current_batch_num:
    always_rotate.append(entry)
```

The intent is: "if there is no current batch, a tagged entry from any batch
should always rotate." The sentinel `-1` achieves this but relies on the
implicit guarantee that no real batch number is ever -1. This is safe in
practice but reads as a magic number -- a reader seeing `entry_batch != -1`
wouldn't immediately understand its meaning.

**Recommended fix (minor):** Replace with an explicit None-check:

```python
if entry_batch is not None and (
    section_3_state.current_batch is None
    or entry_batch != section_3_state.current_batch
):
    always_rotate.append(entry)
```

Or add an inline comment explaining the sentinel.

---

## Finding 6 -- Risk: `ENTRY_BATCH_RE` is too loose

**File:** `scripts/docsync/parser.py:37`

```python
ENTRY_BATCH_RE = re.compile(r"\bBatch\s+(\d+)\b", re.IGNORECASE)
```

This matches any "Batch N" in an entry title. The intended convention
(documented in AGENTS.md) is the parenthetical suffix `(Batch N WP-X)`.

Failure cases:
- Entry title "Post-Batch 8 cleanup" -> routed to Batch 8's log.
- Entry title "Verified Batch 13 and Batch 14 results" -> tagged as Batch 13
  (first match), routed to Batch 13's log incorrectly.
- Side-task entries that mention a batch number in their descriptive text
  would be silently treated as batch-tagged, bypassing the monolith archive
  and going to a per-batch log instead.

The AGENTS.md side-task guidance specifically says to write entries *without*
the `(Batch N WP-X)` suffix. Any agent writing "Pre-Batch 15 analysis -- side
task" in good faith would accidentally trigger routing.

**Recommended fix:** Tighten to require WP suffix and parenthetical context:

```python
ENTRY_BATCH_RE = re.compile(r"\(Batch\s+(\d+)\s+WP-\d+\)", re.IGNORECASE)
```

This is a breaking regex change -- all existing tagged entries must follow the
`(Batch N WP-X)` format, which they already do by convention. Update
`_collect_wp_numbers` accordingly (it currently scans `entry.heading` for
`\bWP-(\d+)\b`, which is fine). Update AGENTS.md to make the parenthetical
format a hard requirement rather than a convention.

---

## Finding 7 -- Defensive gap: Asymmetric marker selection

**File:** `scripts/docsync/parser.py:102-103`

```python
start_idx = starts[0]   # first start marker
end_idx = ends[-1]      # last end marker
```

If a document contained two CURRENT-BATCH-START markers (e.g., from an agent
manually copying a block), the function silently uses the first start and last
end, potentially spanning content that was not intended to be inside the
markers. No warning is emitted; no error is raised.

This is not a current bug, but a defensive gap. Adding an explicit check:

```python
if len(starts) > 1 or len(ends) > 1:
    raise SyncError(
        f"{label} has duplicate markers: "
        f"{len(starts)} start(s), {len(ends)} end(s). Expected exactly 1 of each."
    )
```

...would surface agent-caused corruption before it silently misroutes entries.
This would also be a useful regression guard for the scenarios `_find_marker_pair`
is intended to protect against.

---

## Finding 8 -- Hygiene: Hardcoded stale-phrase list

**File:** `scripts/docsync/logic.py:345-348`

```python
stale_phrases = [
    "refactor monolithic",
    "Post-Batch 8",
]
```

These phrases were relevant when the project was near Batch 8. "Post-Batch 8"
is now 7+ batches stale. They are baked into the script source with no
mechanism for updates. As the list grows (future maintainers adding phrases,
no one removing old ones), it becomes a collection of false-positive risks for
new content that happens to mention batch numbers.

Three options in order of preference:
1. Remove the list entirely. The "Stale header detected" warning was useful
   during a specific refactor era; it provides little value now.
2. Replace with a single generic pattern that detects file-swapped content
   (e.g., a file that still has another document's title in its first line).
3. Move to a config in AGENTS.md as a documented list that agents are expected
   to maintain.

---

## Finding 9 -- Test suite issues

### 9a. Misleading docstring in TestFindMarkerPair.test_same_line_markers_raises

**File:** `tests/test_docsync_parser.py:94-103`

The docstring reads: `"Start and end on same index (only end marker present
once) -- edge case."` The test body only has `CURRENT_BATCH_START_MARKER` and
no end marker at all. The docstring says "end marker" where it means "start
marker" and is factually wrong.

### 9b. Weak `or` assertion in test_entries_without_wp_tags

**File:** `tests/test_docsync_renderer.py:136`

```python
assert "none" in text.lower() or "unknown" in text.lower()
```

The renderer produces both "none" (completed_wp) and "unknown" (next_wp) for
entries with no WP tags. The `or` means the assertion passes if either word
appears, including any `"none"` or `"unknown"` from unrelated output fields.
Both conditions should be asserted separately:

```python
assert "none" in text.lower()
assert "unknown" in text.lower()
```

### 9c. No test for _find_section with duplicate headings

`_find_section` returns the first match. There is no test documenting this
behavior. If a PLAYBOOK ever had two `## 3. Active batch` headings, the
function silently uses the first -- this should be an explicit test.

### 9d. No adversarial test for ENTRY_BATCH_RE false positives

No test covers titles like "Post-Batch 8 cleanup" or "Covers Batch 13 and
Batch 14" that would expose the loose regex described in Finding 6. Adding
these would pin the current behavior (or document that it is a known limitation
until the regex is tightened).

### 9e. test_multiple_entries_uses_newest depends on file-order assumption

**File:** `tests/test_docsync_logic.py:289`

The test comment says the parser returns entries in file order. This is correct.
The function `_latest_test_count_from_entries` then scans in that order and
returns the first count found. If the file has newest entry first, this gives
the newest count. But if agents write entries oldest-first, the function would
return the oldest count, and the test would not expose the bug because the
test data already has newest-first.

The test is technically valid but could be strengthened by specifically testing
with an oldest-first file ordering to confirm the function relies on file order
(not date order) and documenting this as an invariant expectation for PLAYBOOK
authors.

---

## Finding 10 -- Architecture: DEVELOPMENT.md goals are valid and well-executed

This is a positive finding. The three failure modes DEVELOPMENT.md identifies
(drift, regression, token bloat) are the correct problems to solve for
multi-session LLM-driven development. The solutions are proportionate:

**What works well:**

- **SoC between documents:** AGENTS.md (rules), PLAYBOOK.md (work state),
  SESSION_CONTEXT.md (ephemeral snapshot), archive (history). Each file has a
  single owner and purpose. The anti-duplication rule is effective.

- **Rotation mechanism:** The `--keep-non-current 4` default plus the
  `--keep-non-current 0` close-out sweep keeps PLAYBOOK Section 4 lean. Per-
  batch log routing prevents the monolith from growing with structured work
  entries. This is the correct architecture for token budget management.

- **Determinism:** The SHA-256 fingerprint-based deduplication means the same
  entry can never appear twice, and the idempotency property (`--fix` followed
  by `--check` always exits 0) is verified by tests.

- **Pre-commit hook:** Running `--check` as a pre-commit hook catches drift at
  the commit gate, before it reaches CI. The always_run configuration is correct
  -- it guards against PLAYBOOK changes in any commit, not just Python changes.

- **SESSION_CONTEXT as derived file:** The machine-managed STATUS block means
  SESSION_CONTEXT cannot silently drift from PLAYBOOK truth. An agent that
  forgets to update SESSION_CONTEXT is self-correcting on the next `--fix` run.

**Concerns:**

- **SESSION_CONTEXT Section 7 per-file test breakdown** is manually maintained.
  With 306 tests across 19 files, this table is useful context for agents, but
  it can drift and there is no automated update path. Consider whether the
  total count (machine-managed via STATUS block) is sufficient and the per-file
  breakdown can be dropped or conditionally generated.

- **Monolith archive growth:** Untagged side-task entries accumulate in the
  monolith with no age/size cap. The `--keep-non-current 0` close-out sweep
  only affects PLAYBOOK Section 4, not the archive itself. The archive is
  "append-only plus dedup." This is acceptable for now but worth monitoring
  as the project age increases.

- **Agent drift window:** If an agent runs `--fix` but skips
  `pre-commit run --all-files`, SESSION_CONTEXT can diverge from the committed
  state. This is caught at the next commit. The AGENTS.md checklist correctly
  requires both steps.

---

## Finding 11 -- Minor: Late local import of SyncError in cli.py

**File:** `scripts/docsync/cli.py:115`

```python
from docsync.models import SyncError
```

This import is inside `main()` while `SyncError` is not imported at the top of
`cli.py`. It is used only for except clauses in the CLI. The import works, but
it is inconsistent with Python convention (top-level imports), and it is
redundant given that `docsync.logic` already imports `SyncError` at the module
level (available via `from docsync.logic import ...`).

**Recommended fix (trivial):** Move `from docsync.models import SyncError` to
the top-level imports in `cli.py`.

---

## Overall assessment

**Structural soundness: Good.**
The layered module architecture (`models` <- `parser` <- `renderer` <- `logic`
<- `cli`) is clean and acyclic. Pure-function separation in `logic.py` and
`parser.py` makes the sync algorithm independently testable. The `--check` /
`--fix` / `--split-archive` mode structure is clear and appropriately scoped.

**Rotation logic: Correct, with one bug.**
The main rotation algorithm correctly partitions entries into current-batch,
non-current-kept, and rotated buckets. Per-batch routing vs. monolith routing
is correct. The deduplication is fingerprint-based and reliable.
The sole bug (Finding 1) causes unnecessary mtime updates on PLAYBOOK and
ARCHIVE but does not corrupt data.

**Token bloat: Well-managed.**
The rotating window, per-batch logs, and machine-managed SESSION_CONTEXT are
the right tools. No large monolithic files are being created. The primary risk
is the loose ENTRY_BATCH_RE (Finding 6) silently misrouting entries, which
could cause an entry to disappear from an expected location.

**Agent-to-agent drift: Mitigated.**
The pre-commit hook is the right gate. The derivation relationship between
PLAYBOOK and SESSION_CONTEXT prevents the primary class of subtle drift.
The remaining gap (an agent not running the pre-commit checklist manually) is
a process gap, not a tooling gap.

**Recommendations by priority:**

1. **Fix the PLAYBOOK/ARCHIVE unconditional write** (cli.py:215-217) --
   genuine bug with observable side effects.
2. **Tighten ENTRY_BATCH_RE** (parser.py:37) -- silent misrouting risk.
3. **Consolidate test-count regex** (renderer.py + logic.py) -- DRY fix before
   the format ever needs to change.
4. **Add duplicate-marker detection** (parser.py:102-103) -- defensive guard.
5. **Extract `_dedup_sorted` helper** (logic.py) -- DRY, low risk.
6. **Fix test docstring 9a** and strengthen assertion 9b -- trivial.
7. **Address sentinel -1** (logic.py:184) -- comment or refactor, low priority.
8. **Delete or trim stale-phrases list** (logic.py:345) -- low priority hygiene.
