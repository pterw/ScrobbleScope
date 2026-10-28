# Deezer egress incident, Deezer 403 without retries, MusicBrainz 1.2s spacing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stop a Deezer HTTP 403 from being retried, space MusicBrainz request starts 1.2 seconds apart, and write the 2026-10-28 Deezer egress incident down where the next operator will find it.

**Architecture:** Three atomic commits on `fix/deezer-egress-incident` (worktree `C:/ssw/u6`, cut from `main` at e1ea6008), one PR. T1, T2 and T3 are built as three parallel code phases (O7, C12), each in its own detached worktree `C:/ssw/t<N>` at e1ea6008 that returns a patch, then reviewed in parallel and landed one at a time in `C:/ssw/u6` in the order T1, T2, T3. Their Touches are pairwise disjoint, and no patch touches a landing-only shared file. T1 raises the existing `deezer_unavailable` error from inside the attempt, so the retry loop never sees a 403 as a retryable answer. T2 changes one config default and every live line that states it. T3 documents the incident, the recovery recipe and the 503 convention, after the code it describes has shipped.

**Tech Stack:** Python 3.13, aiohttp, pytest (fakes only), Markdown docs, Fly.io CLI (documented, never run).

## Global Constraints

Source: `.superpowers/sdd/2026-10-28-deezer-egress/context.md` (facts F1-F9, rulings O1-O7, C1-C13) and `constraints.md` (R1-R13, Gates). Both are binding for every task.

- O7 / C12 (owner): atomic commits, small slices, parallel in implement and review. Every task is `Mode: code`; the code phase never commits and never writes a shared file (`docs/agents/PLAYBOOK.md`, `.claude/SESSION_CONTEXT.md`, `docs/agents/FINDINGS.md`, the findings archive, `config/docsync.toml`, per `constraints.md` "Shared files"). Those, the Section 4 entry, `doc_state_sync.py --fix` and the commit are the task's `MODE: land` step. Each code report's Handoff section drafts the landing text.
- O5 (owner): the new finding tag is `OPS`; T3 adds it to the tag lists in `AGENTS.md` and `docs/agents/issue-tracker.md` and files `F-OPS-1`.
- O6 (owner, supersedes the draft's "leave it open"): `F-OPS-1` is written as-is, marked resolved per the Finding-Writing Rules, and rotated to `docs/history/findings/FINDINGS_ARCHIVE.md` by `doc_state_sync.py --fix`, both at T3's landing; the recurrence risk (F9) is recorded as a possible issue in `AGENTS.md` and `DEPLOY.md`.
- C5 / C7: the DEPLOY probe and the clone, probe, destroy, confirm steps are C5's, verbatim (verified in the incident session). C6: `tests/test_utils.py:153` belongs to T2. C8-C11: see T2 greps, the callers sentence, T1 acceptance check 3 and T3 placement.

- O2 / C1: a Deezer 403 sends ONE request, no retry, and is still raised as `deezer_unavailable`; never read as a miss. 429 and 5xx stay retried; quota code 4 stays retried.
- O3: MusicBrainz request starts are spaced 1.2 seconds (config default). Point-in-time files (`docs/history/`, `docs/logarchive/`, `docs/superpowers/`, dated Section 4 entries, `docs/design/`) are never edited by hand (R10); the one exception is the findings archive `docs/history/findings/FINDINGS_ARCHIVE.md`, which `doc_state_sync.py --fix` writes at T3's landing (O6).
- O1 / O4 / C2 / C3: the incident report is a FINDINGS entry plus a `DEPLOY.md` section; the 503 convention gets one human-facing line in README (shipped by T2, C12) and is named in the report, not in a second code comment.
- C13: the AGENTS.md note is an Anti-Pattern Registry item in the house style of item 4 (see T3).
- C4 out of scope: a per-job Deezer circuit breaker, Spotify 403 handling, the static egress IP itself.
- R2: no schema change, no new dependency, no new verdict script (so no mutants file).
- R3 / R4 / R5: landing commit procedure, Validation line `` Validation: `pytest -q` -- **N passed**. `` with N the sum of the three `suite-*` gates run at that landing, subject <= 72 characters, no attribution trailer.
- R1: each landing commit writes an untagged Section 4 entry directly after the `<!-- DOCSYNC:CURRENT-BATCH-END -->` marker LINE in `docs/agents/PLAYBOOK.md`; heading `### <commit date, date +%F> - <title>`, no `WP-<digit>` token; body opens `Side task, no batch tag: <what>, on \`fix/deezer-egress-incident\`, a branch off \`main\`.`
- R9: one test per behaviour, parametrize near-duplicates, extend an existing test before adding one; prove each new or edited test red against the unchanged code, then green, quoting both lines. Fakes only.
- R7: ASCII only in hand-written files and commit messages. `PY` = `C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe`.
- Update `Last updated:` in every doc a commit changes that carries one (FINDINGS.md, SESSION_CONTEXT.md; `grep -n "Last updated"` to find others). For a doc in a patch this is the code phase's job; for a shared file it is the landing's.

## Verified mechanism (read from the source at e1ea6008)

- `scrobblescope/deezer.py` `_deezer_request` (lines 37-73): line 59 `if response.status >= 500 or response.status == 403:` returns `(None, None, False)`. `done=False` with no `retry_after` makes `retry_with_semaphore` (`scrobblescope/utils.py:416`) sleep `backoff` and try again; after `retries` attempts it raises `failure("unavailable")`. That is why a 403 costs `DEEZER_SEARCH_RETRIES` / `DEEZER_DETAIL_RETRIES` (both 3) requests (F1: 51x403 for 17 albums).
- `done=True` with a `None` result is a MISS (`search_once` returns "no candidate", `fetch_deezer_album` returns None). Do not use that shape.
- An exception raised inside the attempt: `retry_with_semaphore` has `except reraise: raise` first (line 495), then a broad `except Exception` (line 503). With `failure` given, an exception that is not in `PROVIDER_FAILURES` (`aiohttp.ClientError`, `asyncio.TimeoutError`, `json.JSONDecodeError`; `ProviderError` is not one) is logged as `Error in <label>: ProviderError` at ERROR and re-raised at once, without retry. So a `ProviderError` raised inside the attempt already propagates unretried, but with a spurious ERROR line; passing `reraise=(ProviderError,)` makes it propagate silently. `scrobblescope/spotify.py` does exactly this: `_refused()` returns `provider_failure("spotify")("unavailable")`, callers raise it, and the three Spotify calls pass `reraise=(ProviderError,)` (lines 439, 515, 640).
- FROZEN mechanism: `_deezer_request` raises `provider_failure("deezer")("unavailable")` (already imported in `deezer.py`) on `response.status == 403`, and both `retry_with_semaphore` calls (`search_deezer_album`, `_fetch_deezer_json`) pass `reraise=(ProviderError,)`. The 403 branch leaves the `>= 500` branch alone (a 5xx is still `done=False`, retried). The raise leaves the `async with limiter` / `async with session.get` blocks normally (the context managers exit cleanly). `ProviderError` is imported from `scrobblescope.errors` in `deezer.py` for the `reraise` tuple. The per-provider call log (`api_logging.py`, the `Deezer: N calls ... Nx403` line) hangs off the aiohttp trace, not the return value, so the 403 is still counted once.
- Both entry points go through `_deezer_request`: `search_deezer_album` (search_once) and `_fetch_deezer_json` (fetch_once, used for `deezer.album_details` and `deezer.album_tracks`). The only caller of `search_deezer_album` and `fetch_deezer_album` is `scrobblescope/orchestrator/_deezer_fallback.py` (lines 100-104), which catches `ProviderError`, adds the key to `unchecked` and records the album as Deezer-down. No caller changes. (C9: `_search.py` and `release_checks.py` catch Spotify's and MusicBrainz's errors, not Deezer's; do not look there.)

## File structure

| File | Task | Responsibility |
|---|---|---|
| `scrobblescope/deezer.py` | T1 | 403 raised from the attempt; `reraise`; docstrings |
| `tests/services/test_deezer_service.py` | T1 | existing 403 test re-pointed and parametrized |
| `scrobblescope/config.py`, `scrobblescope/utils.py`, `static/js/results-release-checks.js` | T2 | default and the comments stating it |
| `tests/test_config.py`, `tests/test_utils.py` | T2 | expected default and expected throttle spacing |
| `README.md`, `docs/architecture/runtime-system.md` | T2 | live prose stating 1.1; the one-sentence 503 convention (O4, C12) |
| `DEPLOY.md`, `AGENTS.md`, `docs/agents/issue-tracker.md` | T3 | recovery recipe, new finding tag, Anti-Pattern item, recurrence-risk notes |
| Landing only, never in a patch: `docs/agents/PLAYBOOK.md` (every landing), `.claude/SESSION_CONTEXT.md` (T2 line 292 and `--fix`, every landing), `config/docsync.toml` `[test_count]` (`--fix`), `docs/agents/FINDINGS.md` and `docs/history/findings/FINDINGS_ARCHIVE.md` (T3 landing) | landing | Section 4 entry, count sites, F-OPS-1 entry and its rotation |

---

### Task 1: A Deezer 403 is one request, raised as unavailable

**Wave:** 1 | **After:** none | **Mode:** code in `C:/ssw/t1` (lands first)
**Touches:**
- Modify: `scrobblescope/deezer.py` (`_deezer_request` 403 branch and comment; both `retry_with_semaphore` calls; module/function docstrings that describe 403 as retried: `_deezer_request` comment at line 60-61, `search_deezer_album` docstring "through every retry, a 5xx")
- Modify: `tests/services/test_deezer_service.py` (`test_deezer_http_403_raises_unavailable_not_no_match`, line 668)
- Shared files: none. The patch touches no landing-only file; PLAYBOOK, SESSION_CONTEXT and `[test_count]` are the landing's.

**Interfaces:**
- Consumes: `provider_failure(source)` from `scrobblescope.errors` (returns a factory; `provider_failure("deezer")("unavailable")` is a `ProviderError` with `.code == "deezer_unavailable"`); `retry_with_semaphore(..., reraise=(...), failure=...)`.
- Produces: unchanged public signatures `search_deezer_album(session, artist, album, retries=...)` and `fetch_deezer_album(session, album_id, retries=...)`. New contract: a 403 on any Deezer request raises `ProviderError("deezer", "unavailable")` after exactly one request for that call, with no sleep.

**Behaviour:** an HTTP 403 from Deezer means the egress address is blocked (F2), which a retry cannot cure. Send it once, raise `deezer_unavailable`. Every other status keeps its behaviour: 429 honours Retry-After and is retried, 5xx is retried, other non-200 is a terminal miss, body code 4 is retried, other body codes are a terminal miss. The comment on the 403 branch and the docstrings change to say a 403 is raised at once, not retried, and a 5xx is retried.

- [ ] **Step 1: Re-point the existing test (red).** Turn `test_deezer_http_403_raises_unavailable_not_no_match` into a parametrized test over three calls: `search` (`search_deezer_album`), `album_details` (`fetch_deezer_album` whose `/album/1` answers 403), `album_tracks` (`fetch_deezer_album` whose `/album/1` answers 200 with `_GOOD_ALBUM` and whose `/album/1/tracks` answers 403). Route the fake `session.get` by URL for the last two exactly as `test_fetch_deezer_album_is_a_miss_when_the_track_call_ends_in_an_error` does (`url.endswith("/tracks")`). Use `retries=2`, `patch("scrobblescope.deezer.get_deezer_limiter", ...)` and `patch("asyncio.sleep", new_callable=AsyncMock)` as the current test does. Assert: `ProviderError` with `code == "deezer_unavailable"`; `session.get.call_count` equals the parameter's expected request count (1, 1, 2: no repeat of the 403 URL); the patched `asyncio.sleep` was never awaited. Update the GIVEN/WHEN/THEN docstring (a 403 once, not on every attempt). Do not add a second test.
- [ ] **Step 2: Run it and confirm RED.**
  Run: `"$PY" -m pytest -q -p no:cacheprovider tests/services/test_deezer_service.py -k http_403`
  Expected: all three cases FAIL on the unchanged code, on the request count (2 instead of 1; 3 instead of 2) or the sleep assertion. Quote one failing line per case.
- [ ] **Step 3: Implement (frozen mechanism above).** Add the 403 branch ahead of the `>= 500` branch (the 5xx branch drops its `or response.status == 403`), raising `provider_failure("deezer")("unavailable")`; import `ProviderError`; add `reraise=(ProviderError,)` to the `retry_with_semaphore` calls in `search_deezer_album` and `_fetch_deezer_json`; fix the comment and the docstrings.
- [ ] **Step 4: Run focused tests and confirm GREEN.**
  Run: `"$PY" -m pytest -q -p no:cacheprovider tests/services/test_deezer_service.py` (the only test file that imports `scrobblescope.deezer` at e1ea6008; re-check with `git grep -l "scrobblescope.deezer\|from scrobblescope import deezer" tests/`).
  Expected: all pass, including the existing 5xx test ("unavailable after every retry", line ~413) and the 429 tests, which prove the other statuses still retry. Quote the 403 lines and the last line.
- [ ] **Step 5: Stage, pre-commit, handoff (code phase; no commit).** Stage the two files by name in `C:/ssw/t1`, run `pre-commit run --files` on them, then follow the code-mode procedure. The Handoff section drafts the landing text (R1/R3/R4/R5 apply at landing). Section 4 heading: `### <date> - A Deezer 403 is one request, not three`. The body names the existing test edited: `test_deezer_http_403_raises_unavailable_not_no_match` (re-pointed, parametrized over search, album details, album tracks). Test count: N rises by 2 (one test becomes three cases); the landing takes N from the three `suite-*` gates, not from this note. The landing does the Section 4 entry, `--fix --test-count N`, the gates and the commit.
  Commit subject (54 chars, measured): `fix(deezer): Treat an HTTP 403 as final, not retryable`

**Acceptance checks:**
1. A 403 on search, on `/album/{id}` and on `/album/{id}/tracks` each raises `ProviderError` `deezer_unavailable` after one request for the call, with no sleep.
2. The 5xx, 429 and quota-code tests pass unchanged (still retried).
3. No `Error in deezer...: ProviderError` line is logged for a 403 (the `reraise` path); confirm by reading the focused run's output, not by a new test. This is the one unguarded decision (C10): `reraise=(ProviderError,)` only silences a log line, matches `spotify.py`, and no test pins it (lean-suite rule); deleting it passes every test and the 403 is still not retried.
4. `git grep -n "403" scrobblescope/deezer.py` shows no comment or docstring that says a 403 is retried.

**Red-then-green (R9):** Step 2 red lines and Step 4 green lines quoted in the report.

---

### Task 2: MusicBrainz request starts 1.2 seconds apart

**Wave:** 1 | **After:** none (lands second) | **Mode:** code in `C:/ssw/t2`
**Touches:**
- Modify: `scrobblescope/config.py` (comment line 74, default on line 81), `scrobblescope/utils.py` (docstring line 172), `static/js/results-release-checks.js` (comment line 4)
- Modify: `tests/test_config.py` (lines 86, 88, 94), `tests/test_utils.py` (lines 153, 164)
- Modify: `README.md` (lines 217, 242, 322, 833, plus one new sentence in the same paragraph, see "README 503 line" below), `docs/architecture/runtime-system.md` (line 134)
- Shared files: none in the patch. `.claude/SESSION_CONTEXT.md:292` also states 1.1 but is landing-only: the Handoff drafts that one-line edit and the T2 landing makes it (so it is not in the patch). `docs/agents/PLAYBOOK.md` and `config/docsync.toml` `[test_count]` (unchanged, N does not move) are the landing's.

**Interfaces:**
- Consumes: `_positive_seconds(name, default)` in `config.py`; `utils._MUSICBRAINZ_THROTTLE._min_interval`, which is built from `config.MUSICBRAINZ_MIN_INTERVAL_SECONDS`.
- Produces: `config.MUSICBRAINZ_MIN_INTERVAL_SECONDS == 1.2` by default, and the throttle spacing equal to the setting. The env override `MUSICBRAINZ_MIN_INTERVAL_SECONDS` and the ignored old `MUSICBRAINZ_REQUESTS_PER_SECOND` behave as before.

**Behaviour:** O3 asks for more delay between MusicBrainz requests (F8: MusicBrainz 503s were its own load, but spacing is cheap). Change the default `"1.1"` to `"1.2"` and change every live line that states the value. The sweep (`sweep-1.1s.md`) is the list; it misses one line the plan adds: `tests/test_utils.py:153` holds the bare number `1.1` in the parametrize (the sweep listed only the docstring on line 164). Point-in-time files in the sweep's last section are never edited.

*README 503 line* (O4, moved here from T3 by C12; same paragraph as the line-833 edit): in the paragraph that explains the `MusicBrainz: 17 calls over 12.1s ... 16x200, 1x503` summary (re-find by `git grep -n "MusicBrainz: 17 calls"`; about README.md:839-846), add one sentence: MusicBrainz answers a rate limit or a busy moment with HTTP 503, not 429 (an older convention); the client retries it like a 429, so an occasional `503` count there is normal. ASCII only, no `--` inside code spans beyond the sample. `musicbrainz.py` is untouched (C2). Setting-name-only lines (`config.py:80, :86`, `utils.py:20, :93`, `test_config.py:79`) stay.

- [ ] **Step 1: Re-grep at HEAD.** Run `git grep -nE "1\.1( ?s\b|\b)" -- . ':!docs/history' ':!docs/logarchive' ':!docs/superpowers' ':!*.svg' ':!static/css'` (C8: the pattern also matches `1.1s` and `1.1 s`, which a bare `\b` misses; `SESSION_CONTEXT.md:292` (the landing's), `utils.py:172`, `test_config.py:94`, `test_utils.py:164` must appear) and compare with the Touches list. Any live line stating the MusicBrainz value that is not listed: report it, change it only if it states the value.
- [ ] **Step 2: Edit the tests first (red).** In `tests/test_config.py` change the two expected `"1.1"` to `"1.2"` and the docstring "default 1.1s" to "default 1.2s". In `tests/test_utils.py` change `("_MUSICBRAINZ_THROTTLE", 1.1)` to `1.2` and the docstring "1.1s" to "1.2s". These two tests already assert that the throttle's real spacing follows the setting; keep that assertion, add no new test.
- [ ] **Step 3: Run and confirm RED.**
  Run: `"$PY" -m pytest -q -p no:cacheprovider tests/test_config.py tests/test_utils.py -k "musicbrainz"`
  Expected: the default-env case and the old-rate case of the spacing test fail (`'1.1'` vs `'1.2'`), and the MusicBrainz case of `test_global_throttles_space_request_starts_by_their_interval` fails (1.1 vs 1.2). The `{MB_INTERVAL: "2.0"}` case passes. Quote the failing lines.
- [ ] **Step 4: Change the code and the live prose.** `config.py` default `"1.2"` and its comment; `utils.py` docstring; the JS comment (no daisyUI class words in JS comments, R13); README lines 217, 242 (inside a Mermaid block: change only the digits `1.1` to `1.2`, keep the rest of the line byte for byte), 322, 833; `runtime-system.md:134` (Mermaid again: digits only); the README 503 sentence. Do NOT edit `SESSION_CONTEXT.md:292` (landing-only; put the edit in the Handoff). Keep each sentence's wording; where a sentence reasons about the margin ("a margin over the policy"), it stays true at 1.2.
- [ ] **Step 5: Run focused tests and confirm GREEN.**
  Run the two files above in full, plus `git grep -l "MUSICBRAINZ_MIN_INTERVAL_SECONDS\|_MUSICBRAINZ_THROTTLE" tests/` matches.
  Expected: pass. Then the Step 1 `git grep -nE "1\.1( ?s\b|\b)"` over the live set must show none that states the MusicBrainz spacing.
- [ ] **Step 6: Stage, pre-commit, frontend-gate, handoff (code phase; no commit).** The patch changes `static/` (a JS comment), so the code phase runs the `frontend-gate` in `C:/ssw/t2` (Gates block, `when: a commit that changes templates/, static/ ...`), through `with_browser_lock.py` as written. Only T2 uses the browser lock. The Handoff drafts the landing text: the SESSION_CONTEXT line 292 edit and the Section 4 entry. Section 4 heading: `### <date> - MusicBrainz request starts 1.2 seconds apart`; existing tests edited: `test_musicbrainz_spacing_is_the_interval_setting_and_the_old_rate_is_ignored`, `test_global_throttles_space_request_starts_by_their_interval` (expected value only); the body also names the README 503 sentence.
  Commit subject (50 chars, measured): `fix(musicbrainz): Space requests 1.2 seconds apart`

**Acceptance checks:**
1. With no env, `config.MUSICBRAINZ_MIN_INTERVAL_SECONDS` prints `1.2` and so does the throttle's `_min_interval`; `2.0` in the env still gives `2.0` for both.
2. Two same-instant reservations on `_MUSICBRAINZ_THROTTLE` are 1.2s apart; the Spotify throttle case is unchanged.
3. No live line outside the point-in-time files states 1.1 or 1.1s for MusicBrainz (the Step 5 grep, which sees all 14 lines; the SESSION_CONTEXT line is checked at landing).
4. The Mermaid lines (`README.md:242`, `runtime-system.md:134`) differ from HEAD only in the digit; the controller renders them (the implementer cannot).
5. README has exactly one new sentence, about the 503 convention (O4); `scrobblescope/musicbrainz.py` is untouched (C2).

**Red-then-green (R9):** Step 3 and Step 5 lines quoted.

---

### Task 3: The incident report, the recovery recipe, the 503 line

**Wave:** 1 | **After:** none to build; lands third, after T1 and T2 (the report states 403 is not retried and spacing is 1.2s; both must already be shipped when it lands) | **Mode:** code in `C:/ssw/t3`
**Touches:**
- Modify: `DEPLOY.md` (new section after "Idle exit", before "Where the config lives"; includes the recurrence-risk note, O6)
- Modify: `AGENTS.md` ("Finding-Writing Rules" item 1: add the source tag `OPS`, O5; "Anti-Pattern Registry": one new last item, O6, C13) and `docs/agents/issue-tracker.md` ("Creating a finding": add `OPS`)
- Shared files: none in the patch. The FINDINGS.md entry and its rotation to the findings archive are landing-time (see "Landing handling of F-OPS-1"), as are PLAYBOOK, SESSION_CONTEXT and `[test_count]`. README is T2's.

**Interfaces:**
- Consumes: the facts F1-F9, O1, O2, O4-O6 and C5 in `context.md` (quote them, do not re-derive); T1's contract (403 raised at once) and T2's value (1.2).
- Produces: finding id `F-OPS-1` (grep `F-OPS` first: none exists at e1ea6008), written and rotated at the landing, not in the patch; a `DEPLOY.md` section titled `## Deezer blocks the machine's egress address`; an `AGENTS.md` Anti-Pattern Registry item.

**Behaviour:**

*FINDINGS entry, drafted by the code phase in its Handoff, written by the landing* (`### F-OPS-1: Akamai blocked the app machine's egress address, so every Deezer call returned 403`, written under the empty `## Resolved this batch` heading, C11; not under P2). Fields per the Finding-Writing Rules, written resolved (O6): one-sentence problem statement first, then the body, then `- [x] **Status:** RESOLVED`, `- **Completed:** 2026-10-28` (the commit date, `date +%F`) and `Source: production incident, 2026-10-28 (owner session).` (copy the field layout of `F-B18-12` in the archive). The resolving (landing) commit writes the lifecycle record itself, so this is the author's verdict and the owner has ruled on it (O6). Body, in short ASCII sentences, covers in order:
  1. Symptom (F1): "Deezer could not be reached for some albums" on every production run; `Deezer: 51 calls over 5.0s (1.1s in calls) -- 51x403` and `72 calls ... 72x403` on machine `807339f1595248`; local runs fine.
  2. Diagnosis (F2, F3): same request from the machine got 403 from `AkamaiGHost` for any User-Agent and client; from the owner's PC (AS577 Bell Canada) 200. Machine egress `185.156.47.129` (AS60068 Datacamp, Toronto): Fly's default egress is the host's address and can change. api.deezer.com has no AAAA record.
  3. What was tried (F4, F5): a static egress IP (`209.71.99.215`, $3.60/month) made Deezer return 200 and was released on the owner's word; a restart and a `fly deploy` did not help (same machine id, host, IP: a deploy updates the machine in place).
  4. Fix applied (F6): `fly machine clone 807339f1595248 --region yyz` made `8e762ec1ed4538` with egress `185.156.47.130` (same /24) -> Deezer 200; old machine destroyed. So Akamai blocked one address, not the range. The clone kept `IDLE_EXIT_MINUTES=20`, autostop off, autostart on, restart on-failure. The fix was operational: no code change.
  5. Unknowns, stated as unknown (F7): why Akamai blocked `.129`; why the machine was recreated at 2026-10-27T17:49:55Z, about four minutes after the first idle exit stopped the old one at 17:45:54Z.
  6. MusicBrainz 503s the same day (F8, O4): `87 calls ... 60x200, 27x503` were MusicBrainz-side (12 requests at 1.1s spacing from the owner's PC got 4x503, from Fly 2x503, at the same moment). MusicBrainz answers a rate limit or busy state with 503, not 429 (an older convention); the client treats 429 and 503 alike (`_RATE_LIMIT_STATUS` in `scrobblescope/musicbrainz.py`) and retries.
  7. Code changes that came with it (shipped by T1 and T2): a Deezer 403 is one request, raised as `deezer_unavailable`; MusicBrainz spacing 1.2s (O3).
  8. Recurrence risk (F9): any move of the machine to another host changes the egress IP, and the idle exit (PR #276) makes stop and start frequent. Remedy: `DEPLOY.md` section above. The finding is resolved because the incident is over; the risk is carried as a possible issue in `AGENTS.md` and `DEPLOY.md` (O6), not as an open finding. Out of scope here (C4): a per-job Deezer circuit breaker, Spotify 403 handling, the static egress IP.
  Status lines: `- [x] **Status:** RESOLVED` and `- **Completed:** <date +%F>`. `doc_state_sync.py --fix` rotates the entry to `docs/history/findings/FINDINGS_ARCHIVE.md` in the T3 landing commit (AGENTS.md "Finding-Writing Rules" item 3; the archive heading gets the `-- RESOLVED` suffix).

*Landing handling of F-OPS-1* (T3's `MODE: land`): after applying the patch, write the Handoff entry text under the empty `## Resolved this batch` heading of `docs/agents/FINDINGS.md` (C11), update its `Last updated:`, run `doc_state_sync.py --fix --test-count N` (it rotates the entry into `docs/history/findings/FINDINGS_ARCHIVE.md` and raises the header count), and stage `FINDINGS.md` and the archive as `--fix` leaves them. No code phase and no earlier landing writes either file.

*DEPLOY.md section* (house style of "Idle exit": plain paragraphs, a code fence per command, a rollback-style closing paragraph). Content:
  - Symptom: the Results page says "Deezer could not be reached for some albums" on every run, and the log summary shows `Deezer: N calls ... Nx403`.
  - How to confirm: the probe command from C5, copied verbatim into a fenced `bash` block (Git Bash quoting; verified in the incident session, so the implementer copies it and does not run it). Copy it from `context.md` C5 exactly:

    ```bash
    fly ssh console -a scrobblescope -C "python -c \"import urllib.request as u,urllib.error as e
    ip=u.urlopen('https://api.ipify.org',timeout=10).read().decode()
    try:
      s=u.urlopen(u.Request('https://api.deezer.com/search/album?q=radiohead&limit=1',headers={'User-Agent':'ScrobbleScope/probe'}),timeout=10).status
    except e.HTTPError as x:
      s=x.code
    print('PROBE',ip,s)\""
    ```

    It prints `PROBE <egress-ip> <status>`: `200` is healthy, `403` means Deezer blocks this machine's address. Add `--machine <id>` to probe one specific machine. In the incident it printed `PROBE 185.156.47.129 403` on the blocked machine and `PROBE 185.156.47.130 200` on the clone; the section must not carry those ids or IPs (recipe only), so describe the output shape with placeholders.
  - Free fix (C5, as run): `fly machine clone <blocked-id> --region yyz`; probe the clone with the probe above plus `--machine <new-id>`; if it prints 200, `fly machine destroy <blocked-id> --force`; confirm with `fly machine list` that one machine remains and that it keeps `IDLE_EXIT_MINUTES` (the clone keeps the machine's config: env, restart policy, autostop). If the clone's address is also blocked, destroy the clone and clone again. Say what the incident showed: the clone landed on the next address of the same /24 and Deezer answered 200. Add `-a scrobblescope` where a command does not run inside the repo's `fly.toml` directory.
  - Paid fix: `fly ips allocate-egress -r yyz -a scrobblescope` (a static egress IP; $3.60 a month at the time of writing; the owner's ceiling is machine plus cache under $5 a month), `fly ips list -a scrobblescope` to read it, `fly ips release-egress <ip> -a scrobblescope` to drop it. Say it did make Deezer answer 200 during the incident and was released to keep the cost down.
  - A deploy or restart does not change the egress IP: `fly deploy` updates the machine in place (same id, host and IP). Only a new machine on another host does; the idle exit makes the machine stop and start often, so a block can come back.
  - Possible issue (O6): this can happen again. A new machine on another host gets a new egress address that Akamai may block; closing the finding does not remove the risk. Say it in two plain sentences, and point at the recipe above.
  - Do not paste the incident's machine ids or IPs here (the finding is in the findings archive after rotation: `F-OPS-1`); this section is a recipe.

*AGENTS.md item* (O6, C13): AGENTS.md has no deployment or Fly section (grep for `Fly`, `deploy`, `egress` finds nothing; `DEPLOY.md` owns those facts). The home is the "Anti-Pattern Registry", as one new last numbered item (16) in the house style of item 4 (bold title, parenthesised incident, then a short explanation): **Debugging a provider-wide 403 as a code defect (F-OPS-1, incident 2026-10-28):** every call to one provider refused from production while local runs work means check the machine's egress IP first, not the code; the probe and the fix are in `DEPLOY.md` "Deezer blocks the machine's egress address". Pointer only: no machine id, IP, command or other fact from the recipe is repeated in AGENTS.md. ASCII only. If the T3 implementer finds a better existing home by grep, report it rather than adding a section.

*README 503 line:* not in T3. It moved to T2 (C12), whose Touches already include that README paragraph.

*New source tag* (O5): add `OPS` to the tag lists in `AGENTS.md` (Finding-Writing Rules, item 1) and `docs/agents/issue-tracker.md` ("Creating a finding"), as the rules require ("extend the list here, never leave a tag undocumented"). Add it to the end of each list; the only other AGENTS.md change is the Anti-Pattern item above.

- [ ] **Step 1: Re-check the facts** against `context.md` (every number in the entry matches F1-F9) and `git grep -n "F-OPS" -- docs AGENTS.md` (none before this commit).
- [ ] **Step 2: Write** the patch artifacts above (DEPLOY section, tag lists, AGENTS.md item) and draft the FINDINGS entry text in the Handoff. No code, no test, no README.
- [ ] **Step 3: Stage and pre-commit (code phase; no commit).** Stage `DEPLOY.md`, `AGENTS.md`, `docs/agents/issue-tracker.md` by name in `C:/ssw/t3`; `pre-commit run --files` on them (a DOC rule that rejects a sentence is fixed by rewording, not by suppressing). Do not run `doc_state_sync.py --fix` in the code phase.
- [ ] **Step 4: Landing (T3 `MODE: land`, last), per R1/R3/R4/R5.** Apply the patch, write the FINDINGS entry as in "Landing handling of F-OPS-1", run `--fix --test-count N`; it rotates `F-OPS-1` to the archive and raises the header count; confirm with `git grep -n "F-OPS-1" docs/` that the entry is now only in `docs/history/findings/FINDINGS_ARCHIVE.md` (heading ends `-- RESOLVED`), then `--check` exits 0. Stage the archive and FINDINGS.md as rewritten. Section 4 heading: `### <date> - Record the Deezer egress block and its recovery`; existing tests edited: none; Deviations: new `OPS` source tag (O5), finding resolved and rotated in the same commit (O6).
  Commit subject (58 chars, measured): `docs(ops): Record the Deezer egress block and its recovery`

**Acceptance checks:**
1. After the landing's `--fix`, `F-OPS-1` is in `docs/history/findings/FINDINGS_ARCHIVE.md` (heading ends `-- RESOLVED`, `- [x] **Status:** RESOLVED`, `**Completed:**` set) and is no longer in `docs/agents/FINDINGS.md`; it states F1-F9, names F7's two unknowns as unknown, and says the fix was operational. `doc_state_sync.py --check` exits 0 with no new warning.
2. A reader can follow the DEPLOY section with no other document: C5's probe verbatim (prints `PROBE <ip> <status>`), clone, probe the clone, destroy, `fly machine list` confirmation, paid fix with cost and `release-egress`, the statement that a deploy or restart keeps the IP, and the possible-issue note.
3. `AGENTS.md` carries the `OPS` tag in the Finding-Writing list and the new Anti-Pattern item 16 (house style of item 4, pointer to `DEPLOY.md`, no duplicated facts); `docs/agents/issue-tracker.md` carries `OPS`.
4. The patch touches no README (the 503 sentence is T2's) and no landing-only shared file; `musicbrainz.py` is untouched (C2).
5. After landing, the only file under `docs/history/` that changed is `docs/history/findings/FINDINGS_ARCHIVE.md` (the `--fix` rotation, O6); nothing under `docs/logarchive/`, `docs/superpowers/` or `docs/design/` changed (R10 allows the rotation: it is the tool's own output).

**Red-then-green:** none (docs only, no test). Evidence: the `pre-commit` output on the patch, and at landing `doc_state_sync.py --check` before and after `--fix`; quote the last line of each.

---

## Dispatch

All three tasks are code phases in wave 1 (O7, C12). Each is one atomic commit, built in its own detached worktree at e1ea6008, returning a patch and a code report; none commits.

| Task | Wave | Mode | Worktree | Patch | Lands |
|---|---|---|---|---|---|
| T1 | 1 | code | `C:/ssw/t1` | `task-1-code.patch` | 1st |
| T2 | 1 | code | `C:/ssw/t2` | `task-2-code.patch` | 2nd |
| T3 | 1 | code | `C:/ssw/t3` | `task-3-code.patch` | 3rd (last) |

Disjoint Touches (checked): T1 = `scrobblescope/deezer.py`, `tests/services/test_deezer_service.py`. T2 = `scrobblescope/config.py`, `scrobblescope/utils.py`, `static/js/results-release-checks.js`, `tests/test_config.py`, `tests/test_utils.py`, `README.md`, `docs/architecture/runtime-system.md`. T3 = `DEPLOY.md`, `AGENTS.md`, `docs/agents/issue-tracker.md`. No file appears twice, so any landing order applies cleanly; T3 still lands last because it states what T1 and T2 ship (docs after code, C12).

Landing-only shared files, per task:
- T1 patch: touches none. Its landing writes the PLAYBOOK Section 4 entry, and SESSION_CONTEXT and `[test_count]` via `--fix --test-count N`.
- T2 patch: touches none. `.claude/SESSION_CONTEXT.md:292` (states 1.1) is edited by T2's landing, drafted in T2's Handoff; PLAYBOOK entry and `--fix` as for T1.
- T3 patch: touches none. T3's landing writes the `F-OPS-1` FINDINGS.md entry (text from T3's Handoff) under `## Resolved this batch`, runs `--fix --test-count N`, which rotates it into `docs/history/findings/FINDINGS_ARCHIVE.md`, and stages both with the PLAYBOOK entry and SESSION_CONTEXT.

Peak agents: 3 code implementers, each with at most one nested `gate-runner` running, so at most 6 live at once in the code phase; then 3 `sdd-reviewer` agents in parallel (one per patch, each against e1ea6008); then landing is serial, one `MODE: land` implementer and its `gate-runner` (2 at once).

Gates in each code phase (R11: run only the touched test files and what imports a changed module; the full shards run at landing). The controller passes this scoping to the nested gate-runner as CONTEXT, because the Gates block marks the `suite-*` gates `when: every commit`:

| Task | Own tests | pre-commit | frontend-gate | results-behavior |
|---|---|---|---|---|
| T1 | `tests/services/test_deezer_service.py` | `--files` on the 2 files | no | no |
| T2 | `tests/test_config.py`, `tests/test_utils.py` (and any test importing the two settings) | `--files` on the changed files | **yes** (JS comment in `static/`) | no (`results.js` untouched) |
| T3 | none (docs only) | `--files` on the 3 files | no | no |

Gates after each landing (T1, T2, T3 in turn, in `C:/ssw/u6`): one `gate-runner` per landing commit, before the next landing starts, with the commit-time set from the Gates block: `suite-docsync`, `suite-subdirs`, `suite-core` started together; `doc_state_sync.py --fix --test-count N` (run by the land implementer before the commit); `pre-commit run --all-files`; `docsync-check`. `frontend-gate` also runs at T2's landing (`static/` changes); `results-behavior` does not run at a landing. N is re-measured at each landing from the three `suite-*` gates (T1 raises it by 2; T2 and T3 leave it). Land BASE for T2 is T1's landing commit and for T3 is T2's. The patches were cut from e1ea6008, so each land step runs `git apply --check --index` first and returns NEEDS_CONTEXT on a failure (none is expected, the files are disjoint).

Final: after T3's landing, one `gate-runner` dispatch at the branch head running every gate in the Gates block, including `frontend-gate` and `results-behavior` ("and the final head"). The controller then pushes and `ci-watcher` watches the `quality-gate` job. Implementers never push. Scratch files go under `<scratchpad>/dzr-<task>/` (R8), never inside a worktree; each code phase removes its scratch directory after.

## Owner questions: answered

None open. Ruled: the finding tag is `OPS` (O5); `F-OPS-1` is filed resolved and rotated to the findings archive, with the recurrence risk noted as a possible issue in `AGENTS.md` and `DEPLOY.md` (O6); the probe command is C5's, verified (C5, C7). All three are applied in T3 above, at its landing.

## Recorded, no fix round

- C10: `reraise=(ProviderError,)` in T1 is untested by design (T1 acceptance check 3).
