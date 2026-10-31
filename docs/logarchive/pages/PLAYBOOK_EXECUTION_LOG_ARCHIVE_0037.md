<!-- DOCSYNC:ARCHIVE-PAGE v1 -->
# PLAYBOOK_EXECUTION_LOG_ARCHIVE -- page 0037

### 2026-10-31 - Pin the pip-audit action to its commit SHA

Side task, no batch tag, branch `ci/pin-pip-audit-action`: the third-party
action `pypa/gh-action-pip-audit` in `.github/workflows/test.yml` was
referenced by the mutable tag `v1.1.0`, which its owner can move. zizmor (run
by qlty on every PR) flags that as `unpinned-uses`, qlty's one blocking issue,
and the 2026-09-14 code-review audit asked for the same pin. That one `uses:`
line now names commit `1220774d901786e6f652ae159f7b6bc8fea6d266` with a
`# v1.1.0` comment; the SHA was resolved with
`gh api repos/pypa/gh-action-pip-audit/git/ref/tags/v1.1.0` (`type: commit`).
The `actions/*` references stay on tags because zizmor allows them (owner
ruling O33). No new test: `tests/test_ci_workflows.py` does not pin this
reference, and a test pinning a SHA string would pin wording, not behaviour.
Forward guidance: pin any new third-party action to a commit SHA with the tag
in a trailing comment.

Deviations: none.

Validation: `pytest -q` -- **3158 passed** (the `config/docsync.toml` pin;
the full suite was not re-run because no Python changed; the workflow tests
`tests/test_ci_workflows.py` and `tests/scripts/dev/test_ci_jobs.py` passed,
46 tests).

### 2026-10-31 - Write the canonical status line for 24 findings

Side task, no batch tag, branch `docs/canonical-finding-status`: 24 findings
in `docs/agents/FINDINGS.md` stated their status only in prose
(`Status: open (P2).`), so docsync's finding-lifecycle checks, which read only
`- [ ] **Status:** <value>`, never saw them. Each now carries that line, in
place, with the finding's own words as the value: F-B21-25, F-B23-11,
F-B23-9, F-B22-4, F-B22-3, F-B23-1, F-B23-4, F-B23-13, F-B21-61, F-B21-54,
F-DATA-1, F-DOCSYNC-2, F-DOCSYNC-3, F-B21-57, F-MAS-5, F-MAS-6, F-MAS-7,
F-MAS-8, F-SWE-7, F-LOAD-3, F-LOAD-4, F-LOAD-5, F-DOCSYNC-14 and
F-FEATURE-1 (whose inline sentence moved to its own line). The values are
transcriptions, not verdicts, and no box was checked. Forward guidance: the
24 are now visible to the lifecycle checks.

Deviations: none. Docs only; no code or test changed.

Validation: `pytest -q` -- **3158 passed** (the `config/docsync.toml` pin;
the suite was not re-run because no code changed).

### 2026-10-31 - Record the CI parallel jobs execution

Side task, no batch tag, branch `ci/parallel-jobs`: the plan
`docs/superpowers/plans/2026-10-31-ci-parallel-jobs.md` gets an Execution
record and its done boxes ticked. Run 41223708194 at head `3ca1f53b` ran all
four jobs green: `changes` 7 s, `checks` 74 s, `browser` 313 s, `quality-gate`
4 s, 5 min 32 s in all against 6 min 47 s for PR #284's single job. Reviews:
the plan once and then fixed in 2 rounds, the second without its own
re-review, the split after 1 (`fbb6f449`), the docs sweep
approved. Acceptance (b1) passed locally; (b2) stays open for the first
documentation-only pull request after merge, because this PR changes the
workflow and so runs `browser` on every head. Also: `development-cycle.md`,
`documentation-tooling.md` and `README.md` point at `scripts/dev/ci_jobs.py`
as the owner of the docs-only path list instead of paraphrasing it, and the
README wrap around the docs-only note is fixed.

Deviations: none. Docs only; no code or test changed.

Validation: `pytest -q` -- **3157 passed**.

### 2026-10-31 - Describe the parallel CI jobs

Side task, no batch tag, branch `ci/parallel-jobs`: the documentation sweep
for the four-job workflow. `DEVELOPMENT.md` (the `tests/frontend/` paragraph),
`docs/architecture/development-cycle.md` (the CI paragraph) and
`docs/architecture/documentation-tooling.md` (the CI summary near the end)
now name `changes`, `checks`, `browser` and the `quality-gate` aggregator, say
which pull requests skip `browser`, and point at `scripts/dev/ci_jobs.py`. The
run time reads about 1.5 minutes for a docs-only pull request and about 5
minutes for any other. `README.md` notes the skip and the
`tests/scripts/dev/test_frontend_gate.py` docstring says "CI browser job". No
Mermaid node changed: "GitHub Actions Quality Gate" and its edges stay true.
Point-in-time records are untouched.

Validation: `pytest -q` -- **3157 passed**.

### 2026-10-31 - Tighten the CI split tests after review

Side task, no batch tag, branch `ci/parallel-jobs`: fixes from the review of
the split commit, tests only. In `tests/scripts/dev/test_ci_jobs.py` the
192-row `aggregate` table and its `_allowed` oracle are replaced by one test
that loops the full product against a hand-written set of accepted tuples
and lists every mismatch; `test_aggregate_rejects_an_empty_or_unknown_docs_only_value`
and the duplicate `()` row are removed; the misnamed
`test_main_aggregate_accepts_an_empty_docs_only_value` is replaced by
`test_main_aggregate_rejects_an_empty_docs_only_given_as_a_separate_argument`;
`test_main_aggregate_exits_nonzero_when_a_required_flag_is_missing` is added;
the docs-only table gains `.superpowers-old/x.py`, `build.cmd`,
`src/my file.py` and `my notes.md`. In `tests/test_ci_workflows.py` the
parametrized app-jobs test is split into
`test_app_jobs_set_flask_env` and
`test_the_workflow_passes_no_secret_outside_a_step_env`, so the whole-file
secret scan runs once. No script or workflow change.

Validation: `pytest -q` -- **3157 passed**.

### 2026-10-31 - Run the quality gate as parallel jobs

Side task, no batch tag, branch `ci/parallel-jobs`. The one CI job took about
7 minutes, 4.5 of them in the browser gate. `.github/workflows/test.yml` now
has four jobs: `changes` (is the pull request docs-only), `checks` (install,
preflight, pre-commit, pytest with coverage, pip-audit), `browser` (Playwright
and the frontend gate) and `quality-gate`, the one required context, which
aggregates the other three. `scripts/dev/ci_jobs.py` holds the two decisions
(`docs-only` path classification and `aggregate`), with truth-table tests in
`tests/scripts/dev/test_ci_jobs.py`; `tests/test_ci_workflows.py` reads
per-job blocks. A docs-only pull request skips `browser`; any other skip, or
a failed or cancelled job, turns `quality-gate` red.

Deviations: an empty or unrecognised `--docs-only` value fails the
aggregator even when all three jobs succeeded (fail closed). `browser` has
no Tailwind asset cache: nothing it runs reads `scripts/bin`.

Validation: `pytest -q` -- **3347 passed**.
