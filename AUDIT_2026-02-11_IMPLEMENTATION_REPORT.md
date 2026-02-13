# ScrobbleScope Implementation Audit Report

Date: 2026-02-11

Status note (2026-02-12):
- This report is a baseline audit captured before Batch 3 completion.
- For latest state, consult `EXECUTION_PLAYBOOK_2026-02-11.md` Section 2 and Section 10.

## 1) Why this report exists
This report summarizes:
- What was changed during the latest optimization and audit cycle.
- What regressions/issues were observed.
- What major logic now differs from the original app flow.
- How fixes were selected and validated.
- What remains incomplete.

## 2) Baseline problem statements observed
- Runtime regression from prior baseline (user-reported).
- `AsyncLimiter` loop reuse warning:
  - `RuntimeWarning: This AsyncLimiter instance is being re-used across loops.`
- Increased instability under aggressive tuning:
  - Last.fm transient 5xx in some runs.
  - Spotify 429 spikes in some runs.
- Prior concern that inline template variable injection into JS could be unsafe.
- Prior concern that unmatched modal rendering could be vulnerable to XSS.

## 3) Major logic changes vs original app

### A. Job-scoped state model (instead of a single global progress payload)
Implemented:
- Per-job IDs (`create_job`) and in-memory job store (`JOBS` dict + lock).
- Job-scoped progress, results, params, and unmatched data.
- Job APIs now require `job_id`:
  - `/progress`
  - `/unmatched`
  - `/reset_progress`
- Loading/results pages now bridge and submit `job_id`.

Why:
- Prevent cross-user state collisions.
- Make concurrent requests safe.
- Eliminate global mutable state conflicts.

### B. Username pre-validation endpoint
Implemented:
- `/validate_user` endpoint for blur-time username check from index form.

Why:
- Faster feedback before running long fetch/Spotify processing.

### C. JS data injection safety improvements
Implemented:
- `window.SCROBBLE` and `window.APP_DATA` are now injected via `|tojson` in templates.

Why:
- Avoid unsafe string interpolation in `<script>` blocks.

### D. Unmatched modal XSS mitigation
Implemented:
- `escapeHtml()` used when rendering artist/album/reason in unmatched modal.
- Additional sanitization for unmatched modal error display.

Why:
- Prevent unsafe HTML insertion from dynamic values.

### E. Async limiter lifecycle fix
Implemented:
- Rate limiters are now loop-scoped (`WeakKeyDictionary`) instead of single globals.

Why:
- Fixes `AsyncLimiter` reused-across-event-loop warning.
- Avoids undefined limiter behavior when background jobs run in separate loops.

### F. Retry/semaphore behavior hardening
Implemented:
- Retry waits are not done while holding concurrency slots in key paths.
- Minor jitter added to Spotify retry sleeps to reduce synchronized retry bursts.

Why:
- Prevent throughput collapse when many requests retry simultaneously.

## 4) Performance tuning path and decision method
Method used:
- Controlled benchmarks with fixed user/scenario:
  - Username: `flounder14`
  - Listening year: `2025`
  - Release scope: `same`
  - Show all results
  - Default thresholds
- Isolated timing per stage:
  - Last.fm page fetch
  - Spotify search
  - Spotify details batch

Findings:
- Spotify search stage is dominant bottleneck in normal conditions.
- Aggressive Spotify rate/concurrency improved best-case time but increased 429 frequency.
- Some Last.fm runs showed upstream 500/502/timeout bursts unrelated to code path determinism.

Decision:
- Revert defaults to conservative baseline-safe throughput:
  - Last.fm: 10 req/s, 10 concurrent
  - Spotify: 10 req/s, 10 concurrent, 3 retries
- Keep tuning controls env-driven for explicit override when desired.

## 5) Regressions and issues faced

### A. Aggressive default tuning caused new 429 behavior
Observed:
- Spotify 429 bursts under raised defaults (18 req/s + 18 concurrency).

Fix:
- Defaults rolled back to conservative settings:
  - `MAX_CONCURRENT_LASTFM=10`
  - `LASTFM_REQUESTS_PER_SECOND=10`
  - `SPOTIFY_SEARCH_CONCURRENCY=10`
  - `SPOTIFY_REQUESTS_PER_SECOND=10`
  - `SPOTIFY_SEARCH_RETRIES=3`
  - `SPOTIFY_BATCH_RETRIES=3`

### B. Last.fm 5xx variance
Observed:
- Some runs had heavy 500/502 bursts and timeouts.
- Other runs remained fast and clean.

Interpretation:
- Upstream variability is present; not every slow run is caused by local logic.

### C. Frontend template integrity
Observed:
- Extra closing `</div>` in `templates/error.html`.

Fix:
- Removed the extra closing tag.

## 6) Validation performed
- `pre-commit run --all-files`: passed.
- `pytest -q`: passed (7 tests).
- Manual run checks with `flounder14` and invalid numeric username.

## 7) Current status matrix

### Security / correctness
- Inline JS injection safety (`tojson`): **Done**.
- Unmatched modal XSS mitigation: **Done** (field escaping + safer error message rendering).
- HTTPS for Last.fm endpoints: **Done** (`https://ws.audioscrobbler.com/2.0/` is used).

### UX/UI
- Better upstream-failure-specific user messaging: **Partially done**.
  - Errors are surfaced, but explicit dedicated retry UX for Last.fm upstream failures is still limited.
- Mobile dark-mode toggle overlap risk: **Not fully addressed** (toggle still fixed in top-right globally).

### Architecture
- Per-job state storage: **Done (in-memory dict)**.
- Redis-backed job storage: **Not implemented**.
- Nested thread pattern elimination: **Not implemented** (still thread -> `background_task` -> `run_async_in_thread`).

### Testing
- Added route/job-flow tests around validation and no-match rendering: **Done**.
- Broader coverage (async pipeline, error states, frontend behavior): **Not done yet**.

## 8) Remaining high-value follow-ups
1. Remove nested thread pattern:
   - Run async pipeline directly in the worker thread (single thread hop).
2. Add explicit upstream-failure error state:
   - Distinguish "no albums found" vs "Last.fm temporarily unavailable".
   - Present user-facing retry action on loading/error states.
3. Move fixed dark-mode toggle into page header/action region on mobile breakpoints.
4. Add Redis for job state in production/deploy mode.
5. Expand tests:
   - Last.fm/Spotify retry behavior.
   - Upstream failure mapping.
   - Job expiry and concurrent-job isolation.
   - Frontend rendering safety checks for unmatched modal payloads.

## 9) Feasibility note: user-specific minimum listening year
Feasible and recommended:
- On username validation success, call Last.fm `user.getinfo` and read registration timestamp.
- Compute `registered_year`.
- Dynamically set `#year` input `min=registered_year`.
- Add inline validation message when entered year is lower:
  - Example: `"User flounder14 only has data starting from 2016."`

Notes:
- Last.fm registration date does not strictly guarantee scrobble-start date, but it is a good UX baseline.
- Should still allow server-side guard/error for malformed or bypassed client input.
