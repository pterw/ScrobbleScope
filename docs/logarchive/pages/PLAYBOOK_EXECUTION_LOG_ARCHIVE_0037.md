<!-- DOCSYNC:ARCHIVE-PAGE v1 -->
# PLAYBOOK_EXECUTION_LOG_ARCHIVE -- page 0037

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
