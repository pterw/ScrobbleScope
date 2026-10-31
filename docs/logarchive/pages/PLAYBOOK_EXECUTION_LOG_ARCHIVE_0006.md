<!-- DOCSYNC:ARCHIVE-PAGE v1 -->
# PLAYBOOK_EXECUTION_LOG_ARCHIVE -- page 0006

### 2026-08-06 - PR #169 review remediation: guard and integrity defects (side-task)

- Scope: fixed every defect confirmed by the PR #169 review round -- three
  GitHub Copilot comments plus an independent audit of the guard subsystem,
  the docsync integrity subsystem, and the canonical document corpus.
- Plan vs implementation:
  - Worktree guard. Lineage verdicts named PLAYBOOK's expected branch while
    the ancestry counts and tree identities were measured from HEAD, so
    WT004's lease-protected force-push guidance could point at a branch the
    guard never inspected; they now name the checked-out branch. Branch state
    is classified before base-ref collection, so a missing `origin/main` no
    longer masks the wrong-checkout finding and no longer errors between
    batches. Section 3 parsing accepts ordinary prose and the bold
    `**Branch:**` style instead of failing closed on them. WT008 stops naming
    a primary environment that does not exist, WT009 warns rather than blocks
    in an ordinary checkout so a fresh clone can reach Environment Setup, and
    WT002 no longer republishes raw `OSError` text or absolute paths. A
    `--debug` flag separates a guard defect from an environment failure.
  - Docsync. The documented close-out command `--fix --keep-non-current 0`
    left the repository unrepairable: the authoritative count was read after
    rotation had emptied the live window, so a superseded value was written
    and then failed DOC006, with `--fix` reporting no changes and still
    exiting 1. The count is now derived from the pre-rotation document and
    from rotated archive entries, so retention settings cannot change it.
    DOC001 was narrowed to repository-relative references and now skips fenced
    blocks; DOC003 requires a backticked all-hexadecimal token and reports the
    violation that actually occurred; DOC002 names the competing declarations;
    generated per-batch logs are no longer reported as dead links.
  - Documents. The new qualified-tool rule shipped with eighteen pre-existing
    violations in its own corpus, now covered by one conversion rule rather
    than eighteen rewrites. Corrected references to the removed
    cross-validation, restored AGENTS ownership of the test-count rule,
    documented exit code 2 and the guard's non-blocking edge states, and
    removed a restatement and a normative claim that crossed document roles.
- Deviations: `_cross_validate` and its thirteen tests were removed rather
  than repaired -- the function lost its only production caller when the CLI
  moved to the integrity layer, and both checks it performed are now enforced
  more strictly by DOC006 and DOC001. This also reduces
  `tests/test_docsync_logic.py` from 904 to 725 lines against F-MAS-3. No
  dependency, installation, destructive Git action, history rewrite, or push
  beyond the standing review-fix authorization was required.
- Validation: `pytest -q` -- **561 passed** with 3 existing aiohttp/Python
  3.13 warnings. All 10 pre-commit hooks pass. `doc_state_sync.py --check` --
  exit 0 with the expected root-BATCH warning. Mutation-checked: the guard
  suite now fails when the diagnostic subject is wrong, where previously both
  the defect and its fix left it fully green. The close-out command was
  rehearsed end to end on a throwaway clone -- exit 1 with a corrupted count
  before, exit 0 with the correct count after. Every guard production file is
  at or below the measured 236-line peer cap.
- Forward guidance: execute the chartered full F-SWE-1 audit next; Batch 21
  WP-1 remains queued immediately after that sweep. After the rebase merge,
  expect the tree-identical ahead/behind artifact on `wip/batch-21` and use
  the guard's WT004 output as the first live confirmation of that path.

### 2026-08-05 - Combined integrity and guard final-review fixes (side-task)

- Scope: resolved the four final combined-branch review blockers in the
  docsync integrity gate and read-only worktree guard tests.
- Plan vs implementation:
  - Replaced Windows-separator literals with host-rendered `Path` expectations
    while retaining explicit Windows/POSIX selection, symlink reuse, and the
    simulated POSIX inspection boundary.
  - Added optional SESSION_CONTEXT DOC001 scanning with original line numbers;
    absent-session behavior, schematic exclusions, and deterministic ordering
    remain unchanged.
  - Made the Section 3 declaration the sole normalized tracked root candidate
    for the exact current batch token, covering duplicates, `BATCH210`, root
    `BATCH21.md`, subdirectories, generic templates, untracked supplied content,
    and between-batches state.
  - Sanitized every tracked-file Git failure to one stable invocation error;
    CLI exit 2 contains no stderr, traceback, credential, path, or command text.
  - Marked the approved design implemented and aligned both implementation
    plans with the verified final contracts.
- Deviations: none. No dependency, installation, destructive Git action,
  environment creation, history rewrite, push, or DEVELOPMENT workflow change
  was required.
- Validation: platform-path RED -- 1 expected failure; behavioral RED -- 5
  expected failures; focused GREEN -- **68 passed**; complete docsync suite --
  **164 passed**; complete guard suite -- **84 passed**; full `pytest -q` --
  **521 passed** with 3 existing aiohttp/Python 3.13 warnings. Production and
  guard-test files remain within their measured peer caps.
- Forward guidance: execute the chartered full F-SWE-1 audit next; Batch 21
  WP-1 remains queued immediately after that sweep.

### 2026-08-05 - Worktree guard POSIX fixture remediation (side-task)

- Scope: corrected the final-review test fixture so host-neutral guard tests
  exercise the virtualenv layout selected on Windows and POSIX runners.
- Plan vs implementation:
  - Made the shared repository fixture derive its default tool layout from the
    host OS and removed sibling `Scripts/*.exe` assumptions from inspection and
    topology tests. Direct resolver tests retain explicit Windows, POSIX,
    primary-only, missing-tool, and symlink cases.
  - Added an optional `os_name` inspection boundary whose default remains
    host-derived, then drove the public inspection-to-virtualenv path with a
    deterministic simulated POSIX linked-worktree acceptance test.
  - Updated the authoritative plan interface and fixture/topology expectations;
    the stable `scripts.dev.worktree_guard` facade exports are unchanged.
- Deviations: none. No new file, dependency, Git mutation, environment creation,
  package installation, amend, or push was required.
- Validation: simulated-POSIX RED -- 1 expected failure; focused GREEN -- **1
  passed**; all shared-fixture consumers -- **46 passed**; complete guard suite
  -- **84 passed**; full `pytest -q` -- **513 passed** with 3 existing
  aiohttp/Python 3.13 warnings. All hooks and final docsync checks pass. File
  caps, facade smoke, and live online/offline guard acceptance remain green.
- Forward guidance: execute the chartered full F-SWE-1 audit next; Batch 21
  WP-1 remains queued immediately after that sweep.

### 2026-08-05 - Worktree guard final-review remediation (side-task)

- Scope: resolved all five final plan-review findings without changing the
  guard's read-only Git contract, selected-base behavior, or public facade.
- Plan vs implementation:
  - Split the 522-line `worktree_guard.py` into a 50-line stable facade plus
    diagnostics, inspection, lineage, runner/discovery, types, and virtualenv
    modules. Every guard production file is at or below the measured 236-line and
    8,754-byte pre-existing peer caps; every new test file is at or below the
    measured 184-line and 6,615-byte test peer caps.
  - Added ERROR WT014 for unexpected inspection/runtime failures, suppressed
    subprocess exception chains, caught generic `OSError`, kept explicit
    offline WT013 final, and added a second fail-closed CLI boundary. Output
    contains neither traceback nor sensitive command/URL text.
  - Added exact `(code, severity)` coverage for WT000 through WT014 and real
    inspection-through-CLI blocking, warning-only, success, detached-CI, and
    offline-failure paths. A temporary WT006 severity downgrade produced three
    expected failures and changed both blocking CLI exits from 1 to 0.
  - Clarified the sole initial stdlib-only guard-launch exception, retained
    DEVELOPMENT as human-only rationale, and refreshed the authoritative plan
    file map and reproducible split-suite RED/GREEN commands. Aligned the design
    spec's failure contract and split test map, then refreshed README and
    SESSION_CONTEXT structure, dependency, and test inventories from the
    measured final state.
- Deviations: the final review required a plan-wide SRP split after Task 2 had
  shipped; the facade preserves every accepted import and behavior. No
  destructive Git action, environment creation, dependency install, or push
  was performed.
- Validation: pre-split facade parity -- **55 passed**; new RED suite -- 11
  expected failures and 23 passes; minimal GREEN -- **34 passed**; post-split
  original parity -- **55 passed** with 2 new cases deselected; complete focused
  suite -- **83 passed**; severity mutation restore -- **26 passed**. Full
  `pytest -q` -- **512 passed** with 3 existing aiohttp/Python
  3.13 warnings. Pre-commit and final docsync gates pass. Dirty offline live
  acceptance reports WT010, WT000 (0 behind/12 ahead, linked primary tools),
  then final WT013.
- Forward guidance: execute the chartered full F-SWE-1 audit next; Batch 21
  WP-1 remains queued immediately after that sweep. Use the stable
  `scripts.dev.worktree_guard` facade for all imports.

### 2026-08-05 - Worktree guard default remediation compatibility (side-task)

- Scope: restored the established WT007 operator guidance for the canonical
  `origin/main` base without changing the review-approved behavior for custom
  or local refs.
- Plan vs implementation:
  - Added an exact regression that failed against the neutralized default
    wording and protects both the explicit `git fetch --prune origin` action
    and the offline local-ref fallback.
  - Added one exact-default branch to missing-base remediation. Custom
    `upstream/trunk` and local `main` retain their selected-ref-specific,
    command-neutral guidance; WT013 ordering and exit behavior are unchanged.
- Deviations: none; this is a compatibility correction only, with no Git
  command, collector sequence, diagnostic code, or dependency change.
- Validation: focused guard suite -- **55 passed**. `pytest -q` -- **484
  passed** with 3 existing aiohttp/Python 3.13 warnings. All hooks and final
  docsync checks pass.
- Forward guidance: execute the chartered full F-SWE-1 audit next; Batch 21
  WP-1 remains queued immediately after that sweep.

### 2026-08-05 - Worktree guard review remediation (side-task)

- Scope: corrected the two Task 2 review findings without changing the
  guard's read-only architecture or Git command sequence.
- Plan vs implementation:
  - Added final informational WT013 to every offline result, after state and
    environment diagnostics. WT000 remains success-only; offline lineage and
    virtualenv errors now retain explicit local-ref-only context.
  - Replaced hard-coded origin recovery prose with selected-base guidance.
    WT004 names the display-safe comparison ref, while WT007 uses neutral
    selected-ref or local-ref wording and never constructs a shell command.
  - Added exact inspection and CLI regressions for error-path WT013 ordering,
    custom `upstream/trunk` guidance, and the local-only `main` edge.
- Deviations: added stable code WT013 and corrected the approved plan's
  detached-CI wording so WT011 remains its only topology diagnostic while
  explicit offline mode can add the independent qualifier. Custom-base tests
  live in a new peer-sized file rather than overgrowing an existing peer.
- Validation: focused guard suite -- **54 passed**. `pytest -q` -- **483
  passed** with 3 existing aiohttp/Python 3.13 warnings. All hooks and final
  docsync checks pass.
- Forward guidance: execute the chartered full F-SWE-1 audit next; Batch 21
  WP-1 remains queued immediately after that sweep.

### 2026-08-05 - Read-only worktree bootstrap guard (side-task)

- Scope: completed the repository-integrity worktree safeguard before the
  F-SWE-1 audit and Batch 21 WP-1.
- Plan vs implementation:
  - Added sanitized, injectable Git collection for repository topology,
    PLAYBOOK branch metadata, base ancestry, dirty state, and tree identity.
    Missing repositories/refs, wrong or detached local branches, behind-only
    branches, and both forms of divergence fail without changing Git.
  - Added a thin CLI with stable diagnostic rendering, explicit offline
    labeling, recognized detached-CI skip behavior, and qualified primary
    checkout Python, pytest, and pre-commit paths for linked worktrees.
  - Made the read-only command a canonical post-document bootstrap gate;
    HANDOFF points to that owner, while DEVELOPMENT records only the human
    rationale and the deliberate separation from CI topology enforcement.
  - Exercised the live linked worktree offline: WT010 identified the
    intentional dirty candidate, WT000 reported 0 behind/9 ahead, and all
    three tools resolved under the primary checkout's existing `.venv`.
- Deviations: split collector acceptance across peer-sized inspection,
  topology, runner, and CLI files instead of expanding the existing classifier
  file past its directory peers; no dependencies, environment creation,
  package installs, or Git mutation.
- Validation: focused guard suite -- **49 passed**. `pytest -q` -- **478
  passed** with 3 existing aiohttp/Python 3.13 warnings. All hooks and final
  docsync checks pass.
- Forward guidance: execute the chartered full F-SWE-1 audit next; Batch 21
  WP-1 remains queued immediately after that sweep.

### 2026-08-05 - Worktree classifier review remediation (side-task)

- Scope: resolved the first review round for Task 1 without expanding the
  pure classifier into Task 2's Git discovery or bootstrap integration.
- Plan vs implementation:
  - Restored Steps 2, 4, and 6 of the authoritative plan to run only the
    parser/lineage test file that exists at those stages; Step 10 onward keeps
    both focused paths after the venv test file is created.
  - Added parameterized both-sided-divergence coverage for a missing head tree,
    missing base tree, and both trees missing. Every unavailable-tree state now
    asserts WT005, while only two present matching IDs assert WT004.
  - Replaced remediation-fragment checks with the full mandated WT004 and WT005
    strings, protecting dirty reconciliation, refreshed-base/tree verification,
    owner authorization, force-push-with-lease boundaries, and the explicit
    prohibition on reset, rebase, or force-push for true divergence.
  - Mutation verification weakened both remediation constants and treated two
    missing IDs as equal; the strengthened suite produced five expected
    failures before the original correct behavior was restored.
- Deviations: none; production behavior was already correct, so this round
  strengthens regression protection and repairs plan execution order only.
- Validation: parser/lineage suite -- **23 passed**; complete focused guard
  suite -- **30 passed**. `pytest -q` -- **459 passed** with 3 existing
  aiohttp/Python 3.13 warnings. Final hooks and docsync gates pass.
- Forward guidance: proceed to Task 2's read-only CLI and bootstrap wiring;
  F-WORKTREE-1 and F-WORKTREE-2 remain open until its live linked-worktree
  acceptance passes.

### 2026-08-05 - Pure worktree safety classification (side-task)

- Scope: implemented the pure, read-only classification layer for the
  worktree-safety guard without wiring it into bootstrap or running Git.
- Plan vs implementation:
  - Added strict PLAYBOOK Section 3 parsing that ignores historical log text,
    preserves missing active-branch metadata, and rejects missing, duplicate,
    or malformed active state rather than guessing.
  - Added deterministic lineage diagnostics for detached CI/local states,
    missing or wrong active branches, dirty trees, behind-only state, and both
    content-identical rebase artifacts and true divergence. Remediation is
    diagnostic only and performs no repository mutation.
  - Added platform-aware environment resolution for ordinary and linked
    checkouts. Linked worktrees reuse the primary checkout `.venv`; distinct
    secondary environments and missing required tools fail with actionable
    diagnostics, while a symlink/junction alias to the primary environment is
    accepted.
  - Corrected two plan-interface contradictions while preserving its safety
    policy: lineage snapshots now carry the parsed active-batch discriminator,
    and the WT005 test verifies that remediation explicitly prohibits reset
    without contradicting the mandated `do not reset` wording.
  - Split immutable value types and virtualenv tests into focused peer-sized
    files to satisfy the repository's new-file size gate; the public imports
    and focused test command remain explicit in the corrected plan.
- Deviations: specification-preserving interface/test corrections only; no
  dependencies, package installs, Git commands, automatic repairs, or
  bootstrap enforcement were added.
- Validation: focused worktree-guard suite -- **27 passed**. `pytest -q` --
  **456 passed** with 3 existing aiohttp/Python 3.13 warnings. Final hooks and
  docsync gates pass.
- Forward guidance: Task 2 must add the thin read-only CLI, canonical bootstrap
  rule, and real linked-worktree acceptance before F-WORKTREE-1 and
  F-WORKTREE-2 can close. The pure classifier is testable but is not yet a
  mandatory bootstrap command.

### 2026-08-05 - Docsync content-integrity plan final remediation (side-task)

- Scope: closed the plan-wide final review findings without changing the
  approved deterministic-only enforcement architecture.
- Plan vs implementation:
  - Made the newest live full-suite `pytest -q` validation in PLAYBOOK the
    authoritative test count, including side-task entries outside the
    current-batch markers; the renderer and DOC006 now share that result and
    reject conflicting named SESSION_CONTEXT count fields.
  - Tightened active-definition matching to a complete numeric batch token
    and limited DOC001's exemption to the exact Section 3 declaration.
  - Converted Git invocation `OSError` failures to sanitized `SyncError`
    diagnostics so the CLI returns 2 without a traceback, preserved analyzer
    input immutability, and strengthened the two-reference regression.
  - Refreshed the docsync package/dependency inventory and all measured test
    counts; DEVELOPMENT remains explanatory human documentation only.
- Deviations: none; no dependencies, semantic auto-fixes, or Git history
  changes.
- Validation: focused docsync suite -- **156 passed**. `pytest -q` --
  **429 passed** with 3 existing aiohttp/Python 3.13 warnings. Final hooks and
  docsync gates pass.
- Forward guidance: implement the read-only worktree-safety guard; only
  F-WORKTREE-1 and F-WORKTREE-2 remain open P0 gates before Batch 21 WP-1.

### 2026-08-05 - Docsync integrity review remediation (side-task)

- Scope: addressed the first Task 2 review round without changing the
  approved enforcement design.
- Plan vs implementation:
  - Added CLI regression coverage proving `--fix` returns 1 with DOC001 for
    an unresolved dead live reference and emits no stale DOC005 after it
    repairs the session block.
  - Moved resolved F-DOCSYNC-5 out of the active P0 section, leaving only the
    two worktree safeguards as open P0 gates.
  - Corrected the Task 2 focused-suite record to the measured post-remediation
    count.
- Deviations: none.
- Validation: specified docsync suite -- **112 passed**. `pytest -q` --
  **420 passed** with 3 existing aiohttp/Python 3.13 warnings. Final hooks and
  docsync gates pass.
- Forward guidance: implement the read-only worktree-safety guard; only
  F-WORKTREE-1 and F-WORKTREE-2 remain open P0 gates before Batch 21 WP-1.

### 2026-08-05 - Docsync content-integrity enforcement (side-task)

- Scope: wired the reviewed pure live-document integrity analyzer into the
  local and CI docsync gate, closing F-DOCSYNC-5 before Batch 21 WP-1.
- Plan vs implementation:
  - Made the side-task archive prologue renderer-owned, so `--check` detects
    a stale prefix and `--fix` restores it without changing dated entries.
  - Added stable blocking `ERROR DOC...` CLI diagnostics for live integrity
    defects. `--fix` writes deterministic output first and revalidates the
    final on-disk state; unresolved semantic defects still exit 1.
  - Retained missing optional SESSION_CONTEXT support and the existing root
    BATCH-file warnings, while removing legacy warning-only CLI validation.
- Deviations: none.
- Validation: targeted docsync suite -- **111 passed**. `pytest -q` --
  **419 passed** with 3 existing aiohttp/Python 3.13 warnings. Final hooks and
  docsync gates pass.
- Forward guidance: implement the separate read-only worktree-safety guard;
  F-WORKTREE-1 and F-WORKTREE-2 remain the P0 gate before Batch 21 WP-1.

### 2026-08-05 - Docsync integrity analyzer review remediation (side-task)

- Scope: corrected two review findings in the pure analyzer before its
  deferred CLI/CI wiring task.
- Plan vs implementation:
  - Active definitions now require both supplied live-document content and a
    tracked path; an untracked declaration reports DOC002 at its Section 3
    declaration line rather than being masked by the DOC001 exemption.
  - Replaced ignored dated Section 4 entry lines with blank placeholders, so
    later PLAYBOOK diagnostics retain their original file line numbers.
  - Added separate regression tests that first reproduced both defects.
- Deviations: none; integration remains intentionally out of scope.
- Validation: `pytest -q` -- **415 passed** with 3 existing aiohttp/Python
  3.13 warnings. Final hook and docsync gates pass.
- Forward guidance: Task 2 can consume the corrected pure analyzer without
  reimplementing its active-definition or PLAYBOOK source-location rules.

### 2026-08-05 - Docsync live-document integrity analyzer (side-task)

- Scope: added the pure live-document integrity analyzer for the P0
  repository-content safeguard; enforcement is intentionally deferred to the
  next ordered task.
- Plan vs implementation:
  - Added deterministic `IntegrityIssue` diagnostics DOC001 through DOC006
    for dead concrete references, active-definition drift, volatile Branch
    metadata, archive-prologue drift, stale managed session content, and
    contradictory current test counts.
  - Added adversarial pure-unit coverage for literal-reference extraction,
    tracked-path normalization, active-definition metadata, archive/session
    comparison, and deterministic ordering. The analyzer is not yet wired
    into the docsync hook or CI gate, so F-DOCSYNC-5 remains open.
- Deviations: none; CLI integration and severity changes remain the next task.
- Validation: `pytest -q` -- **413 passed** with 3 existing aiohttp/Python
  3.13 warnings. Final hook and docsync gates pass.
- Forward guidance: integrate the pure analyzer without duplicating its
  parsing or changing the established sync behavior before enforcement.

### 2026-08-05 - P0 integrity/worktree implementation plans (side-task)

- Scope: translated the owner-approved repository-integrity/worktree-safety
  specification into executable, test-first implementation plans.
- Plan vs implementation:
  - Split the two independent safeguards into ordered plans so each produces
    a reviewable, independently testable result: CI-blocking docsync content
    integrity first, then local worktree lineage and shared-virtualenv safety.
  - Mapped exact files, interfaces, diagnostic codes, adversarial tests,
    canonical documentation ownership, fault-injection evidence, validation
    gates, and commit boundaries. Each code step includes concrete signatures
    or snippets rather than delegating design decisions to the executor.
  - Self-reviewed both plans against every approved-spec section, checked type
    and diagnostic-name consistency, removed placeholders, balanced Markdown
    code fences, and kept the second plan smaller than its peer per the new-file
    size rule.
- Deviations: the single specification becomes two sequential plans because
  repository-content integrity and local Git topology are independent failure
  domains. Scope and execution order are unchanged.
- Validation: plan self-review -- pass. `pytest -q` -- **390 passed** with 3
  existing aiohttp/Python 3.13 warnings. `pre-commit run --all-files` -- all
  10 hooks pass. Final `doc_state_sync.py --check` -- exit 0 with the expected
  active-root `BATCH21_DEFINITION.md` warning.
- Forward guidance: choose Subagent-Driven execution (recommended) or Inline
  Execution. Complete both plans before F-SWE-1; Batch 21 WP-1 remains gated.

### 2026-08-05 - Repository-integrity and worktree-guard design (side-task)

- Scope: investigated why canonical documentation drift and repeated
  post-rebase worktree divergence survived green local and CI gates, then
  captured the owner-approved remediation as a written design.
- Plan vs implementation:
  - Realigned the clean, tree-identical `wip/batch-21` branch from the
    post-PR-#168 3/3 divergence to `origin/main` and force-pushed with lease
    after explicit owner authorization.
  - Split the remediation into a blocking repository-content integrity layer
    inside docsync and a separate read-only local worktree alignment guard;
    detached CI runs the former and unit-tests the latter, but does not
    pretend to validate local worktree topology.
  - Logged F-WORKTREE-1 and F-WORKTREE-2, and reopened F-DOCSYNC-5 as P0
    items until mechanical prevention lands. The second worktree finding was
    reproduced during validation: a linked root has no gitignored `.venv`, so
    the test gate must reuse the qualified environment under the primary
    checkout. Updated DEVELOPMENT.md with the human-readable incidents and
    design rationale while preserving AGENTS.md as the future owner of
    agent-facing rules.
  - Wrote the approved design at
    `docs/superpowers/specs/2026-08-05-repository-integrity-worktree-alignment-design.md`.
- Deviations: implementation is deliberately deferred until the owner reviews
  the written specification, as required by the selected design workflow.
- Validation: written-spec self-review -- pass. Qualified shared-venv
  `pytest -q` -- **390 passed** with 3 existing aiohttp/Python 3.13 warnings.
  `pre-commit run --all-files` -- all 10 hooks pass. Final
  `doc_state_sync.py --check` -- exit 0 with the expected active-root
  `BATCH21_DEFINITION.md` warning.
- Forward guidance: review the written specification. After approval, create
  the implementation plan, land both P0 safeguards, then execute the full
  F-SWE-1 sweep; Batch 21 WP-1 remains gated behind the remediation.
