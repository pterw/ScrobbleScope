# BATCH17: Multi-Agent Orchestration, CI/CD, and Security Headers

**Status:** In Progress
**Branch:** `wip/batch-17`
**Baseline:** 350 tests passing

---

## Context

This batch addresses problems in three layers of the project: the agent
bootstrapping system, the CI/CD pipeline, and HTTP response security.

**Bootstrapping gaps:** A session review identified three concrete problems in
`HANDOFF_PROMPT.md`. First, a flow conflict with `AGENTS.md`: `AGENTS.md`
Side-Task Handling says commit code first then log in `PLAYBOOK`; `HANDOFF`
Section 5 reads as update `PLAYBOOK` first then commit, causing agents to
create documentation commits before their code commits. Second, the batch
definition path hint in Section 3 says "file is at the repo root" but between
batches no definition file exists there, misleading arriving agents. Third,
`MEMORY.md` (root) is absent from the bootstrap read list -- it is the only
persistent cross-agent memory available to non-Claude-Code agents (Copilot,
Codex, Gemini, Jules), and agents following `HANDOFF_PROMPT.md` never read it.

**`SESSION_CONTEXT.md` staleness:** Section 1 "What is ScrobbleScope?" is
25 lines of product description that belongs in `README.md` (where it already
exists). An agent state dashboard should contain only runtime facts. The section
adds overhead to every bootstrap read with no information gain. Removing and
renumbering requires coordinated cross-reference updates in `AGENTS.md` and
`HANDOFF_PROMPT.md` to keep section number references consistent.

**CI gaps:** The pipeline has a redundant standalone flake8 step (pre-commit
already runs it, identical config, identical output) that adds ~20s to every run.
No pip caching means full dependency reinstall on each run. `coverage.xml` is
generated but discarded. No automated dependency update mechanism exists.

**Security:** The app has no HTTP security headers. `Content-Security-Policy`,
`X-Frame-Options`, `X-Content-Type-Options`, and `Referrer-Policy` are all absent.
Input validation and Jinja2 auto-escaping are already correct; the gap is
response headers. A template audit confirmed the CDN allowlist: `cdnjs.cloudflare.com`
(Bootstrap CSS/JS, html2canvas), `cdn.jsdelivr.net` (Bootstrap JS), `i.scdn.co` /
`*.scdn.co` (Spotify album art). All frontend API calls are same-origin. Flask-Talisman
is the standard, GoogleCloudPlatform-maintained extension for this.

**Out of scope:**
- Feature work (top songs, heatmap) -- owner roadmap, separate batch
- AGENTS.md structural changes -- 295 lines is not oversized (degradation above ~500)
- Branch protection merge strategy -- no workflow rules set at this stage
- Orchestrator decomposition or horizontal scaling architecture

---

## 1. Scope and goals

- Fix three concrete problems in `HANDOFF_PROMPT.md` (conflict, stale path hint,
  missing `MEMORY.md`)
- Remove `SESSION_CONTEXT.md` Section 1 product context; renumber sections; update
  cross-references in `AGENTS.md` and `HANDOFF_PROMPT.md` to match
- Improve CI pipeline: remove duplicate flake8 step, add pip caching, add coverage
  artifact upload, add pip-audit security scan, add dependabot
- Add PR template with pre-commit/docsync/scope checklist
- Add Flask-Talisman security headers (CSP, X-Frame-Options, X-Content-Type-Options,
  Referrer-Policy, conditional HSTS)
- Add 3 automated tests verifying security headers are present on responses

---

## 2. Work Packages

### WP-1: HANDOFF_PROMPT.md -- fix conflict, path hint, and MEMORY.md

**Goal:** Three targeted edits to `HANDOFF_PROMPT.md` that remove confirmed
bootstrapping problems. No changes to `AGENTS.md` structure or content.

**Files:**
- `HANDOFF_PROMPT.md`

**Edit 1 -- Section 3, batch definition path.** The current text says "Active
batch: file is at the repo root (`BATCHN_DEFINITION.md`)" with no qualification.
Between batches, no definition file exists at root. Replace with:

> "Active batch: definition file is at repo root (`BATCHN_DEFINITION.md`).
>  Between batches: no definition file exists yet -- skip this step."

**Edit 2 -- Section 5, commit order conflict.** Section 5 describes the
documentation close-out commit (PLAYBOOK + SESSION_CONTEXT). An agent reading
it cold interprets it as "update PLAYBOOK before committing code," conflicting
with `AGENTS.md` Side-Task Handling ("commit normally, THEN add PLAYBOOK entry").
Fix: add one sentence at the start of Section 5:

> "After your code changes are committed (following AGENTS.md commit rules
>  and side-task handling), document completion:"

The five steps that follow remain unchanged.

**Edit 3 -- Section 1, add MEMORY.md as step 5.** After the SESSION_CONTEXT
step, add:

> "5. `MEMORY.md` (repo root) -- user preferences, workflow conventions, local
>    dev setup, discovered constraints. This is the only persistent cross-agent
>    memory; non-Claude-Code agents do not have access to any other memory layer.
>    Read it even if it appears similar to `AGENTS.md`; it contains facts that
>    `AGENTS.md` explicitly does not duplicate."

**Acceptance criteria:**
- All three edits applied with exact text as specified
- `AGENTS.md` is unchanged
- `pytest -q` passes (350 passed -- no code changes)
- `pre-commit run --all-files` passes
- `python scripts/doc_state_sync.py --check` exits 0

**Net tests:** +0
**Commit:** `docs(agents): fix HANDOFF_PROMPT conflict, path hint, and MEMORY.md bootstrap`

---

### WP-2: CI/CD pipeline improvements

**Goal:** Remove duplicate lint step, add caching and artifact upload, add
automated dependency update and security audit tooling.

**Files:**
- `.github/workflows/test.yml` (edit in-place)
- `.github/dependabot.yml` (new)

**Workflow changes:**

Rename `name:` from `"CI Pipeline"` to `"Quality Gate"` and job id from `test`
to `quality-gate`. Once branch protection requires this check by name, the name
must not change without also updating the branch protection rule.

Remove the standalone "Lint code with flake8" step. Pre-commit runs flake8 with
the same `.flake8` config in the preceding step; the standalone step is a pure
duplicate that adds ~20s and produces identical output.

Add pip caching via `setup-python` built-in (cache key hashes
`requirements-dev.txt`; invalidates automatically when dependencies change):
```yaml
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: '3.13'
    cache: 'pip'
    cache-dependency-path: requirements-dev.txt
```

Add coverage artifact upload after the test step:
```yaml
- name: Upload coverage report
  uses: actions/upload-artifact@v4
  with:
    name: coverage-xml
    path: coverage.xml
    retention-days: 14
```

Add pip-audit security scan (informational; `continue-on-error: true` so findings
do not block builds -- review manually when the step shows warnings):
```yaml
- name: Security audit (pip-audit)
  uses: pypa/gh-action-pip-audit@v1.1.0
  with:
    inputs: requirements.txt
  continue-on-error: true
```

**dependabot.yml** (new file at `.github/dependabot.yml`):
```yaml
version: 2
updates:
  - package-ecosystem: pip
    directory: /
    schedule:
      interval: weekly
    open-pull-requests-limit: 5
  - package-ecosystem: github-actions
    directory: /
    schedule:
      interval: weekly
    open-pull-requests-limit: 3
```
Weekly cadence and a 5-PR cap surfaces updates without noise. Dependabot PRs
go through the same CI gate as any PR.

**Acceptance criteria:**
- CI passes end-to-end on push to `wip/batch-17`
- Standalone flake8 step is absent from the workflow
- Job id is `quality-gate`; workflow name is `Quality Gate`
- Pip cache populated on first run; cache hit on second push with no dep changes
- `coverage.xml` appears in the Artifacts section of the Actions run (14-day retention)
- pip-audit step is present and runs (findings may exist; step must not fail build)
- `dependabot.yml` is valid YAML (`check-yaml` hook passes)
- `pytest -q` passes (350 passed)
- `pre-commit run --all-files` passes

**Net tests:** +0
**Commit:** `ci: rename to Quality Gate, remove duplicate flake8, add caching, artifact, pip-audit, dependabot`

---

### WP-3: PR template

**Goal:** Add a standard PR description template with a validation checklist so
every PR -- batch WP or side-task -- surfaces the same documentation gates at
creation time. The checklist mirrors existing requirements from `AGENTS.md` and
`HANDOFF_PROMPT.md`; it adds no new requirements.

**Files:**
- `.github/PULL_REQUEST_TEMPLATE.md` (new)

**Content:**
```markdown
## Summary

<!-- What changed and why -->

## Checklist

- [ ] `pytest -q` passes (update SESSION_CONTEXT Section 1 if test count changed)
- [ ] `pre-commit run --all-files` passes (all hooks)
- [ ] `python scripts/doc_state_sync.py --check` exits 0
- [ ] PLAYBOOK Section 3 reflects current WP/task state
- [ ] PLAYBOOK Section 4 has a dated log entry:
      - Batch WP: inside `DOCSYNC:CURRENT-BATCH-START/END` markers
      - Side task: after `DOCSYNC:CURRENT-BATCH-END` marker
- [ ] Changes are within scope of the active batch definition
      (or deviation is logged in the Section 4 entry)
```

Note: "SESSION_CONTEXT Section 1" refers to the post-WP-4 numbering (current state
table). The section number in the template will match after WP-4 is committed.

**Acceptance criteria:**
- Opening a new PR on GitHub shows the template pre-populated
- File passes `check-yaml` hook
- `pytest -q` passes (350 passed -- no code changes)
- `pre-commit run --all-files` passes

**Net tests:** +0
**Commit:** `ci: add PR template with validation checklist`

---

### WP-4: SESSION_CONTEXT.md cleanup + cross-reference updates

**Goal:** Remove the product description section from the agent state dashboard
and fix stale content. Because section numbers shift, all cross-references in
`AGENTS.md` and `HANDOFF_PROMPT.md` must be updated in the same commit to avoid
leaving stale section number references.

**Files:**
- `.claude/SESSION_CONTEXT.md`
- `AGENTS.md` (section number references only)
- `HANDOFF_PROMPT.md` (section number references only)

**SESSION_CONTEXT.md changes:**

Delete Section 1 "What is ScrobbleScope?" (product context: what the app does,
upcoming features, tech stack, deployment). This information exists in full in
`README.md`. An agent state dashboard contains runtime facts only.

Renumber remaining sections: current Section 2 → Section 1, Section 3 → Section 2,
Section 4 → Section 3, Section 5 → Section 4, and so on.

Fix staleness in new Section 1 (was Section 2):
- "Last updated: 2026-03-04"
- app.py row: "~152 lines" (was ~142)
- Add Batch 17 row: `**Active**. Branch: wip/batch-17. Definition: BATCH17_DEFINITION.md.`

Fix environment notes section: add `--workers 1 --threads 4` reference to the
`dev_start.py` description line.

Run `python scripts/doc_state_sync.py --fix` after editing to refresh the
`DOCSYNC:STATUS` block. Commit `SESSION_CONTEXT.md` together with PLAYBOOK
and the reference updates below.

**AGENTS.md cross-reference updates:**
Locate and update all explicit SESSION_CONTEXT section number references. The
section numbers shift by -1 (Section 2 → 1, Section 3 → 2, etc.):
- "Sections 2-5 of `.claude/SESSION_CONTEXT.md`" → "Sections 1-4"
- "SESSION_CONTEXT Section 2 (test count...)" → "Section 1"
- "Section 4 (project structure)" → "Section 3"
- "Section 5 (dependency graph)" → "Section 4"

**HANDOFF_PROMPT.md cross-reference updates:**
- "Read Section 2 (current state + test count) and Section 3 (status block)...
  Sections 4-5 if you need architecture" → "Read Section 1 (current state +
  test count) and Section 2 (status block) at minimum. Sections 3-4 if you need
  architecture or dependency detail."

**Acceptance criteria:**
- SESSION_CONTEXT has no product description section; Section 1 is the current
  state table
- AGENTS.md section number references are updated and match the new numbering
- HANDOFF_PROMPT.md section number references are updated and match
- `python scripts/doc_state_sync.py --check` exits 0
- `pytest -q` passes (350 passed -- no code changes)
- `pre-commit run --all-files` passes

**Net tests:** +0
**Commit:** `docs(session-context): remove product context section, renumber, update cross-refs`

---

### WP-5: Flask-Talisman security headers

**Goal:** Add HTTP security response headers via Flask-Talisman. The app currently
sends no security headers. A template audit confirmed the full CDN allowlist needed
for the Content Security Policy.

**CDN allowlist (from template audit, 2026-03-04):**
- `cdnjs.cloudflare.com`: Bootstrap CSS + JS, html2canvas (`results.html`)
- `cdn.jsdelivr.net`: Bootstrap JS (`index.html`)
- `i.scdn.co` / `*.scdn.co`: Spotify album artwork (dynamic, from backend)
- `data:`: base64 inline images / placeholders
- All JS fetch/XHR calls are same-origin (`/progress`, `/validate_user`, etc.)

**Files:**
- `requirements.txt` -- add `flask-talisman>=1.1.0`
- `requirements-dev.txt` -- add `flask-talisman>=1.1.0`
- `app.py` -- add Talisman init inside `create_app()`, after `csrf.init_app(application)`
- `tests/test_app_factory.py` -- add 3 security header tests

**`app.py` changes:**

```python
from flask_talisman import Talisman

# CSP allowlist -- verified against template audit (2026-03-04).
# If a future feature adds a new CDN resource (e.g., a chart library for
# heatmap), add its domain to the appropriate directive here.
_CSP = {
    "default-src": "'self'",
    "script-src": ["'self'", "cdn.jsdelivr.net", "cdnjs.cloudflare.com"],
    "style-src": ["'self'", "cdn.jsdelivr.net", "cdnjs.cloudflare.com"],
    "img-src": ["'self'", "data:", "i.scdn.co", "*.scdn.co"],
    "font-src": ["'self'", "cdn.jsdelivr.net", "cdnjs.cloudflare.com"],
    "connect-src": "'self'",
    "object-src": "'none'",
    "frame-ancestors": "'none'",
    "base-uri": "'self'",
    "form-action": "'self'",
}

Talisman(
    application,
    force_https=False,                         # Fly.io terminates TLS at the load
                                               # balancer; app sees plain HTTP
                                               # internally -- forced redirect loops
    strict_transport_security=not debug_mode,  # HSTS only in production
    content_security_policy=_CSP,
    x_frame_options="DENY",
    x_content_type_options=True,
    referrer_policy="strict-origin-when-cross-origin",
)
```

**Tests to add to `tests/test_app_factory.py`:**
- `test_security_header_x_frame_options` -- GET `/` returns response with
  `X-Frame-Options: DENY`
- `test_security_header_x_content_type_options` -- GET `/` returns response with
  `X-Content-Type-Options: nosniff`
- `test_security_header_csp_present` -- GET `/` returns response with a
  `Content-Security-Policy` header (presence check; exact policy is integration-level)

**Mandatory local verification before committing:**
1. Run the app (`python app.py`), open a browser, perform a normal search.
2. Open DevTools → Console. Confirm zero CSP violation errors.
3. Confirm album artwork loads (Spotify CDN images must appear).
4. Confirm the image export feature works (html2canvas from `cdnjs.cloudflare.com`
   must load).

If any CSP violation appears, add the missing domain to the appropriate directive
in `_CSP` before committing. Do not commit a CSP that breaks existing functionality.

**Future-proofing notes:**
- New CDN resources (top songs chart library, heatmap date picker, etc.) require
  adding the domain to `_CSP`. One-line change, documented by the comment above.
- Monolith decomposition: `Talisman(application, ...)` moves with `create_app()`
  unchanged.
- Horizontal scaling: Talisman is stateless request middleware; scales transparently.
- html2canvas cross-origin canvas tainting: a pre-existing browser security boundary
  (separate from CSP) may affect image export if Spotify image CORS headers change.
  This is not introduced by Talisman; see existing note in `DEVELOPMENT.md`.

**Acceptance criteria:**
- `pip install flask-talisman>=1.1.0` succeeds (package exists on PyPI)
- `pytest -q` passes (≥353 passed -- 350 + 3 new header tests)
- All 3 new header tests pass
- Browser: zero CSP console errors on a complete search + results flow
- Browser DevTools Network tab: `X-Frame-Options`, `X-Content-Type-Options`,
  `Content-Security-Policy` visible on responses
- Album artwork loads; image export (html2canvas) functions
- `pre-commit run --all-files` passes

**Net tests:** +3
**Commit:** `feat(security): add Flask-Talisman CSP and security headers`

---

## 3. Summary table

| WP | Priority | Deliverable | Net tests |
|----|----------|-------------|-----------|
| WP-1 | P0 | Fix 3 HANDOFF_PROMPT.md problems (conflict, path hint, MEMORY.md) | +0 |
| WP-2 | P1 | CI rename, remove dup flake8, add caching + artifact + pip-audit + dependabot | +0 |
| WP-3 | P1 | PR template with validation checklist | +0 |
| WP-4 | P1 | Remove SESSION_CONTEXT product context, renumber, update cross-refs | +0 |
| WP-5 | P1 | Flask-Talisman security headers + 3 tests | +3 |

**Total after Batch 17:** 350 + 3 = **353 tests passing**

---

## 4. Execution order

1. WP-1 (bootstrapping fix -- no dependencies; highest risk to agent workflow if left unresolved)
2. WP-2 (CI -- independent of all other WPs)
3. WP-3 (PR template -- independent; best committed before any PR is opened for this batch)
4. WP-4 (SESSION_CONTEXT -- independent; commit SESSION_CONTEXT + AGENTS.md + HANDOFF_PROMPT together)
5. WP-5 (Talisman -- independent; requires local browser verification before committing)

---

## 5. Verification (per WP)

```bash
pytest -q
pre-commit run --all-files
python scripts/doc_state_sync.py --check
```

For WP-5 additionally: local browser test (zero CSP violations, artwork loads,
image export works).

---

## 6. Deferred

- Branch protection rules and merge strategy -- no workflow rules set at this stage;
  revisit when team size or review process warrants it
- Coverage PR comments -- requires a separate action setup; future CI batch candidate
- mypy / type checking in CI -- future batch candidate
- html2canvas CDN hosting locally -- reduces CSP surface area; future batch candidate
- Feature work (top songs, heatmap) -- owner-defined scope, separate batch

---

## Supplementary Info

### Owner: Post-Batch Agent Hand-Off Best Practices

This section is for the repo owner. It documents the recommended procedure when
ending one agent session and starting another -- whether that is a different agent
type (Copilot, Gemini, Codex) or a new Claude Code session.

**After all WPs are committed and the batch close-out is done:**

**1. Verify clean state.**
```bash
git status                                        # clean working tree
git log --oneline -3                              # close-out commit is latest
pytest -q                                         # count matches SESSION_CONTEXT Section 1
python scripts/doc_state_sync.py --check          # exits 0
```

**2. Confirm SESSION_CONTEXT.md is committed and current.**
`SESSION_CONTEXT.md` is the shared cross-agent dashboard committed to the repo.
Every agent reads it first. If it is stale (wrong test count, old batch status,
wrong branch), the next agent starts from incorrect assumptions.
- Check: "Last updated" date, test count in Section 1, Batch N row status.
- If stale: edit, run `python scripts/doc_state_sync.py --fix`, commit as
  `docs(session-context): update state after batch N`.

**3. Review MEMORY.md (root) for updates.**
`MEMORY.md` is the only cross-agent persistent memory. Claude Code's auto-memory
is Claude-Code-specific. After each batch, check whether any new architectural
decisions, discovered constraints, or environment facts should be recorded.
- Do not duplicate facts already in `AGENTS.md`.
- Good entries: new modules added, env var changes, load-test constraints,
  Windows-specific workarounds, non-obvious design decisions.

**4. Starting a new Claude Code session.**
Claude Code bootstraps from its auto-memory, which references `MEMORY.md`.
The recommended first message for a new session is the text of `HANDOFF_PROMPT.md`
verbatim, or: "Please read `HANDOFF_PROMPT.md` as your first action."

**5. Starting a session with Copilot, Codex, Gemini, or Jules.**
These agents have no auto-memory. Their context window starts empty each session.
Recommended first message:
```
Read the following files before doing anything else:
1. AGENTS.md
2. MEMORY.md
3. PLAYBOOK.md (Sections 3 and 4 only)
4. .claude/SESSION_CONTEXT.md (Sections 1-2 only)

After reading, confirm: current branch, last commit SHA, and next WP.
Do not start any work until you have confirmed these three facts.
```
Do not rely on the agent to proactively read `MEMORY.md`; it will not unless
explicitly listed in the first message.

**6. Before writing the next batch definition.**
Per `AGENTS.md` Proposal and Design Rules: a definition file (`BATCH18_DEFINITION.md`)
with acceptance criteria for every WP must be committed before any WP work begins.
Plan the batch, write the definition, commit it, then start WP-1.
