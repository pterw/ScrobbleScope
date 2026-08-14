# WP-5 Fail-Open Follow-Up (Deferred)

Date: 2026-02-21  
Status: Deferred by owner (no code change in this pass)

## Context

WP-5 added server-side registration-year validation in `results_loading` and
intentionally chose fail-open behavior when the Last.fm registration check is
unavailable.

## Why this note exists

The current fail-open behavior is acceptable for request availability, but
there is a semantic edge case in upstream error handling that should be tracked
for a later patch.

## Issue summary

1. `check_user_exists()` returns `{"exists": True, "registered_year": None}`
   on broad exceptions, including upstream failures.
2. This can make `/validate_user` report "Username found" even when Last.fm is
   unavailable.
3. `results_loading` then skips the registration-year guard (by design) and
   proceeds, which is correct for availability but ambiguous for user feedback.

## Affected locations

- `scrobblescope/lastfm.py`
- `scrobblescope/routes.py`
- `tests/test_routes.py`
- `tests/services/test_lastfm_service.py`

## Recommended future fix

1. Replace boolean-only `exists` semantics with an explicit status contract
   (example: `ok`, `not_found`, `unavailable`).
2. Keep fail-open in `results_loading` for `unavailable`.
3. Return degraded/unavailable response from `/validate_user` when status is
   `unavailable` (do not map upstream failure to "username found").
4. Add route-level tests for degraded `/validate_user` behavior and preserve
   existing WP-5 boundary tests.

## Non-goals in this deferred note

- No behavior changes applied.
- No policy change to fail-open in `results_loading` in this pass.
