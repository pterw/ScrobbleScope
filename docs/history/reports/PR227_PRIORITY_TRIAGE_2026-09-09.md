# PR 227 priority triage -- 2026-09-09

This report records the route-triage snapshot. Later owner-approved Results
refinements and publication validation are recorded in PLAYBOOK Section 4.

## Scope and evidence

The owner requested current comments, including assertions and deleted TODOs,
with only top-priority fixes implemented. This supplements
[the earlier review](PR227_REVIEW_2026-09-07.md), whose body filter excluded
comments containing "assert"; that filter was not applied here.

GitHub was read on 2026-09-09: PR #227 is open, base `355aac2`, published head
`a53e412`. Local branch `test` is at `3db9662`, with `16fbf92` (review
remediation) and `3db9662` (hygiene/audit) not included in that published head.
The PR body describes some of those local fixes already. No commit, push,
review reply or thread resolution is part of this pass.

Fetched the complete connector timeline (552 entries: 518 inline comments,
5 nonempty conversation/review bodies, 29 empty review submissions) and 503
review threads; 362 threads were unresolved. Repeated bodies are not distinct
defects. There are 268 inline B101-bearing comments across seven test files
and 135 TODO-rule comments: 15 route locations reported nine times.
Both review summaries and the collapsed low-confidence scope warning were read.

The existing Graphify graph located route, repository and gate seams; current
files and Git history determine the verdicts. No graph rebuild was performed.
Existing uncommitted results/shell styling and F-B21-52/F-B21-53 were excluded
from this fix.

## Audit summary

| Concern | Priority and disposition | Evidence / owner |
|---|---|---|
| Job pages send 200 while painting an unrelated 400 badge | P1: fixed locally | F-B21-49; real Flask response regressions |
| Results DOM insertion and checkout credential persistence | Earlier local fixes retained | `16fbf92`: text nodes, `persist-credentials: false` |
| Assertion scanner flood | P2 tooling: logged, no assertion removal | F-B21-54 |
| Floating-point equality and callback dictionary comparison | No defect demonstrated | Detailed assessment below |
| CSS token strings and filter-description fixture reported as secrets | Declined | Token names and test expression, not credentials |
| Remaining gate size / repeated geometry-label literals | Deferred housekeeping | F-B21-51; existing issue #228 covers constants |
| Full orchestrator / utils decomposition | Existing scheduled work | F-B20-2 / F-SWE-7; no scope expansion |
| Unmatched redesign and retirement of compatibility POST | Deferred | WP-7 and F-B21-50 |
| API-key startup assertions outside the test reports | Existing P1, not newly introduced by these comments | F-SWE-4 |
| Toolchain/dependency changes bundled with UI | Process concern, including low-confidence finding | F-B21-50; no history rewrite |
| Header, typography and other visual claims | Existing local changes or owner-review work | F-B21-45, F-B21-52/F-B21-53 and Task 6; no new visual acceptance claim |

No new P0 defect was established in the reviewed comments. Scanner labels such
as "critical" and "blocking" were evaluated against the actual trigger rather
than copied into findings.

## Per-comment assessment

### Assertions, including bundled warnings

B101 comments cite `tests/scripts/dev/test_frontend_gate.py`,
`tests/services/test_lastfm_service.py`,
`tests/services/test_orchestrator_fetch_and_process.py`,
`tests/services/test_orchestrator_fetch_spotify.py`, `tests/test_heatmap.py`,
`tests/test_routes.py` and `tests/test_template_shell.py`. These assertions
check parser results, job state, validation, route responses and template
contracts. Removing them would remove test protection. No production
authorization or credential validation depends on these test statements.
The separate production credential assertions in `spotify.py` remain owned
by F-SWE-4; the test-noise verdict does not excuse them.

The six S1244 warnings bundled with B101 were assessed separately:

- [419](https://github.com/pterw/ScrobbleScope/pull/227#discussion_r3945124079),
  [420](https://github.com/pterw/ScrobbleScope/pull/227#discussion_r3945124082)
  and [431](https://github.com/pterw/ScrobbleScope/pull/227#discussion_r3945124091):
  black/white luminance endpoints and identical-color contrast are fixed
  boundary invariants. Grey is tested by ordering, and the nontrivial contrast
  result uses `pytest.approx`. The symmetric comparison deliberately checks
  order independence. No blanket approximate-comparison rewrite is warranted.
- [787](https://github.com/pterw/ScrobbleScope/pull/227#discussion_r3945202193),
  [788](https://github.com/pterw/ScrobbleScope/pull/227#discussion_r3945202195)
  and [789](https://github.com/pterw/ScrobbleScope/pull/227#discussion_r3945202198):
  current `test_parse_matrix_scalex_recovers_scale_and_handles_boundaries`
  already uses `pytest.approx` for 0.2255, 0.9 and 1.0. Exact zero assertions
  cover explicit fallback values. Owner replies asking for verification are
  addressed by these code reads and the passing suite.

[S5727](https://github.com/pterw/ScrobbleScope/pull/227#discussion_r3945202229)
and the owner's [reply](https://github.com/pterw/ScrobbleScope/pull/227#discussion_r3946742823)
claim `observed_phase == {...}` is always false. The async fake invokes the
real progress callback and assigns its result through `nonlocal
observed_phase`; the expected value is a dictionary, not the initial None.
Deleting phase propagation would leave None and fail the test. Retain it.

### Earlier remediation and remaining advisories

- B106/B107 strings `--shell-border` and `--ss-border-divider` are CSS
  variable identifiers passed to contrast diagnostics. They are not passwords.
- TruffleHog's repeated `tests/test_routes.py` locations refer to the historical
  `_get_filter_description(...) == expected` fixture expression. The current
  test still exercises the eight release-scope branches. No credential was
  established, so no secret rotation or broad secret-scanner exclusion follows.
- Results toast and metric HTML construction now uses `createElement`,
  `textContent` and `replaceChildren`; `results.js` contains no
  `innerHTML`. The existing browser check injects markup-shaped metric data
  and rejects rendered image nodes. The hardening predates this pass.
- `window.html2canvas` and the computed body background already replace the
  implicit global and hardcoded export background. Spotlight diagnostics use
  separate console arguments; the old interpolated warning is gone.
- Metric-button weight is already 700 in the local stylesheet. Selection uses
  colors and `aria-pressed`; the former 500/400 contradiction is gone.
- `spotlight.py` owns aggregate ranking/sample selection, with deterministic
  job-seeded sampling and a justified B311 annotation. Its purpose is not
  cryptographic. `_artist_spotlight_details` owns shared Spotify normalization.
  Optional API failures retain the client candidate's album art; route and
  Spotify service tests exercise fallback paths.
- Gate fixture loading is lazy-cached with retry after a failed read; the
  theme expression, phase labels and progress selectors have shared owners.
  Gate runners and progress helpers were decomposed in `16fbf92`.
  Repeated geometry-key text remains a low-priority housekeeping concern.
- `set_job_progress` deliberately distinguishes omitted fields, explicit
  clearing and partial updates. A generic dictionary API solely to reduce
  parameter count would change that contract without a demonstrated defect.
- `[0-9]` in the gate's formatting pattern specifies ASCII output. Replacing
  it with Unicode digit matching is not an equivalent readability fix.
- `loading-progress.js` already separates range metadata and bar rendering.
  Full orchestrator and gate splits remain their existing findings.
- Workflow permissions are `contents: read`; local checkout uses
  `persist-credentials: false`. The latter is absent from published
  `a53e412`, so its live comment is not proof the local fix failed.

### Present and deleted TODOs

A case-insensitive search found no TODO/FIXME in the inspected application,
template, JavaScript, test and developer-script sources (vendor/bin fixtures
excluded). Git history shows `769f0aa` introduced these 15 route notes and
`16fbf92` removed them. The table uses their published review line numbers,
not current source positions.

| Original route line | Request | Current disposition |
|---|---|---|
| 495 | Friendly 500 retry copy and logging | Existing handler copy and Flask exception logging; explicit badge fixed in `16fbf92` |
| 499 | Results errors and empty states | Empty states exist; missing HTTP/badge contract fixed here (F-B21-49) |
| 672 | Unmatched GET and client experience | GET and dedicated absent/expired empty states exist; visual redesign remains WP-7 |
| 737 | Refactor unmatched client experience | Deferred WP-7, not completed by deleting the note |
| 745 | Consider retiring legacy POST | Deferred; compatibility wrapper intentionally remains |
| 746 | Support GET | `/unmatched` already delegates to the same renderer |
| 874 | Client username-presence validation | Required field and submit validity guard exist |
| 889 | Handle unavailable user service | JSON message/retryable flag consumed by Heatmap error UI |
| 902 | Handle unknown user | Nonretryable response rendered by same client error path |
| 916 | Handle private profile | Privacy response and client validation exist |
| 928 | Handle unavailable privacy service | Retryable response consumed by client error UI |
| 942 | Handle capacity limit | 429 payload and Retry control exist |
| 960 | Handle failed job startup | Cleanup and retryable error response exist |
| 979 | Handle missing heatmap job ID | Error JSON consumed by heatmap-data error path |
| 986 | Handle unavailable heatmap job | Error JSON consumed by same error path |

This corrects the earlier "13 implemented / two genuine" summary: twelve notes
describe existing behavior, two retain deferred work, and the results note
contained the remaining response-contract defect. Comments after a return
statement are not executable unreachable code; their placement alone was not
a runtime defect.

The owner's conversation TODOs also remain in scope of the audit: spotlight
fallbacks have implementation and regression coverage; the PR body is now
written, but describes unpushed code; blanket mutation testing and broad
orchestrator decomposition were not performed here. Only the touched route
contracts received fresh failing-before/fixed-after evidence.

## Fix and validation

F-B21-49 now gives the same status to Flask and the badge: missing ID 400;
missing/expired/wrong-mode job 404; pending results 202; retryable processing
failure 503; unknown-user failure 404; unclassified processing failure 500.
404 matches the existing JSON APIs and does not claim the absent job is known
to have existed. No expiration tombstone is stored to justify 410.
Saved Results/Unmatched empty states remain 200 and evict stale session IDs.

Five existing assertions were strengthened and thirteen route cases added.
Before the source change: 18 failed, 89 passed. After: 107 route tests passed.
Full `pytest -q`: **975 passed**. A focused read-only reviewer found no
regression; their diff access failed, so they reviewed live files against the
explicit change inventory.

The baseline pre-commit run passed every hook except `tailwind-css-drift`,
which rebuilt the already-dirty generated stylesheet for the owner's existing
results markup. The hook's comparison is against the Git index, so an
unstaged generated stylesheet keeps it red. No source CSS/template edit was
made by this pass. Full browser acceptance was not rerun for this route-only
change; the route tests render the real templates and check response bodies.
Final docsync and diff-whitespace checks pass. Ruff reformatted the new tests;
its recheck passes, as do the other hooks except the existing Tailwind drift.

## Original route-only commit candidate

Before the later UI follow-up, the separable candidate was: `fix(routes): Align job-page HTTP statuses and badges`.
Scope: `routes.py`, its tests, findings, this report, PLAYBOOK and synchronized
dashboard/archive output. Net tests: +13. Keep the owner's styling work out of
that commit. No commit or push was made.

## Batched PR reply draft -- not posted

Acted on locally: F-B21-49 job-page response/badge mismatch; 975 tests pass.
Earlier local remediation `16fbf92` covers results DOM construction, workflow
credential persistence, exports, Spotify normalization and focused extraction.

Declined: test B101 warnings, fixed-boundary float warnings, the callback
dictionary false positive, CSS identifiers/fixture expressions reported as
secrets, and treating comments after return as executable code.

Deferred: F-B21-54 scanner scope; F-B21-51 / issue #228 housekeeping;
F-B20-2 / F-SWE-7 broad refactors; WP-7 unmatched redesign and compatibility
retirement. Published PR head remains older than the local remediation.
