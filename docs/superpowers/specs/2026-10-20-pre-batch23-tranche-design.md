# Pre-Batch-23 tranche design

Date: 2026-10-20

Status: design approved by the owner section by section on 2026-10-20.

## Purpose and scope

Batch 23 imports the Spotify Extended Streaming History export. Before WP-1
starts, a tranche of side-task PRs makes the repository accurate and ready:
documentation that describes the system as it is, diagrams that match the
source, a consistent interface, backend hygiene, and four of the architecture
seams the 2026-09-30 review proposed. None of this is a Batch 23 work
package; each PR logs untagged PLAYBOOK Section 4 entries, as side tasks do.

Rules stay owned by [AGENTS.md](../../../AGENTS.md) and the architectural
invariants by [global-rules.md](../../agents/global-rules.md). Batch scope
stays owned by `BATCH23_DEFINITION.md`. This specification records the
approved tranche, not a second ruleset.

## Owner rulings this design rests on (2026-10-20)

- One branch and one PR per planned component; well-sliced tasks; parallel
  subagents, up to eight at a time. "Make sure to keep commits atomic in case
  a roll back is needed to a prior commit."
- "Any new tests should always test inteded behavior and not that the
  func/code works as written."
- Review: "reviewing something already reviewd can slow work and lead to
  blocks, getting caught in review loops is costly. Getting it right the
  first time is important." When a re-review finds issues, the cause is
  investigated with the systematic-debugging skill before any fix.
- Planned scope in `BATCH23_DEFINITION.md`, `.claude/SESSION_CONTEXT.md` and
  `docs/agents/PLAYBOOK.md` are kept current per the repository rules, and
  pre-commit runs before every commit.
- Seams: option B -- the four seams that do not keep the database awake
  (the metadata-encoding seam reworks the cache module but adds no
  database traffic). Job persistence waits, because a database-backed job
  store would keep the database awake (see Hosting cost ceiling).
- Answers to the 2026-10-20 standup questions: Adobe Fonts and the CDN
  scripts stay as they are; key rotation, Fly monitoring and control-plane
  tooling are out of scope; `scripts/dev/mutation_test.py` stays untracked;
  the codebase-knowledge notes stay local; the docstring rule does not cover
  nested closures or one-line helpers.

## Hosting cost ceiling

Fly.io waives a personal organisation's monthly invoice under $5 (stated by
Fly staff on the community forum; the pricing page does not mention it). The
owner's cost explorer showed $4.90 for 1-20 October 2026 with the database
always on. On 2026-10-20 the database machine's `FLY_SCALE_TO_ZERO=1h` was
restored, so it stops after an idle hour again. The app machine stays at one
shared-CPU machine running one gunicorn worker with threads. Any change that
keeps the database awake, or adds a machine or a service, needs the owner's
ruling against this ceiling.

## The PRs

| # | Branch | Scope | Starts |
|---|--------|-------|--------|
| 1 | `feat/include-unmatched` | the include-unmatched control (in flight) | -- |
| 2 | `chore/pre-batch23-hygiene` | this spec and the plans; ruff `target-version = "py313"` (autofixes in their own commit); `requests` to the development requirements; `page_motion.js` renamed `page-motion.js`; a check that the pinned test count includes browser-marked tests | now |
| 3 | `refactor/album-request-module` | review card B-1: form to validated request or typed refusal; one Last.fm pre-check with a short timeout; one admission path | after #1 merges |
| 4 | `refactor/lastfm-scrobbles` | review card B-3 and the earlier scrobble design: parity tests first, public seams, scrobbles not pages, one typed album aggregate; Last.fm usernames leave the logs (F-B23-40) | parity tests now; the rest after #3 |
| 5 | `refactor/metadata-encoding` | review card B-5: the cache takes and returns `AlbumMetadata` and owns its connection lifetime | after #4 |
| 6 | `refactor/statistics-module` | review card B-4: statistics computed in Python in UTC; the browser renders | after #4 |
| 7 | `feat/ui-consistency` | CSS-only items first, then owner screenshot rounds | after #1 merges; template work after #6 |
| 8 | `docs/pre-batch23-refresh` | README audit, DEVELOPMENT.md history, every Mermaid diagram, drift fixes | drafting now; merged last |

The seams' sources are the 2026-09-30 review
(`docs/history/reports/architecture-review-20260930-0040.html`) and the
pre-merge designs and briefs for Tasks 21, 23, 26, 27 and 28. Those were
written before PR #245 merged; each is refreshed against current `main`
before any code is written.

## Rules for every PR

- Every commit is atomic and carries its own untagged Section 4 entry
  directly after the current-batch end marker. Every commit runs
  `doc_state_sync.py --fix` (with `--test-count N` when the count changed),
  `pre-commit run --all-files` and `doc_state_sync.py --check`.
- Section 3 is updated as each PR lands, so it always names the work still
  ahead of WP-1.
- When a seam changes what a Batch 23 work package may assume, the same PR
  amends `BATCH23_DEFINITION.md`: #3 for WP-4's validators, #4 for WP-2's
  record shape, #5 for WP-3's metadata shape, #6 for WP-6's helper.
- Each seam PR updates its own architecture diagrams and SESSION_CONTEXT
  Sections 3-4 (AGENTS.md "Silent doc staleness"); the docs PR reconciles,
  it is not the only place they change.
- A refactor starts from parity tests in a preceding commit (AGENTS.md
  "Refactor requires parity tests"). New behavioural tests assert intended
  behaviour and carry mutation evidence: the planted defect named, the test
  shown failing.
- A fact newly stated in two documents is declared in `config/docsync.toml`
  in its own commit, which needs `SKIP=doc-state-sync-check` and a manual
  `doc_state_sync.py --check` afterwards (never `--no-verify`).
- Browser gates run one at a time on the owner's machine.

## Review policy

1. Briefs first: each refreshed brief gets one brief review before any code.
2. One code review per task. Critical or Important findings get one fix
   round, and only the fix delta is re-checked. Minor findings are folded
   in at landing through the landing context and are not re-reviewed.
3. A landing gets a gate run, not a review, unless it adds behaviour the
   code review did not see; then a review scoped to that part.
4. No whole-PR review for small PRs; CI and the gates suffice. PR #4, four
   commits deep, gets one whole-PR review before push.
5. A re-review that still finds issues triggers systematic debugging of the
   cause before another fix round.

## Documentation PR (#8)

README: keep the current format; audit every claim against source; condense
"Current Status & Roadmap" into a short forward view, with the history moving
to DEVELOPMENT.md. Deepen Architecture with:

- graceful degradation as the design rule: an outage yields a partial result
  that says so, never a false "no match";
- the metadata cache: optional to run, the main reason a repeat search is
  fast (a hit skips every provider call), 30-day expiry;
- API stewardship per provider: Spotify (single-flight token refresh, the
  per-job breaker, at most 3 search results), MusicBrainz (about one request
  per second, a contact User-Agent), Deezer (limits as observed; it publishes
  none), and the Retry-After cap for all;
- why the Spotify batch-details call has a fallback: Get Several Albums is
  removed for Development Mode apps created after Spotify's February 2026
  changes and postponed with no date for existing ones; a 403, 404 or 410
  switches to one request per album, and what Spotify cannot answer goes to
  Deezer;
- the album pipeline as ETL: extract Last.fm pages; transform (normalize,
  aggregate, threshold partition); enrich (cache, Spotify search and details,
  single-album fallback, Deezer); filter by release window; publish results
  and the unmatched report;
- the correction worker: one thread, a FIFO queue of jobs, MusicBrainz at
  one request per second, started after a job succeeds, correcting reissue
  years in place;
- the hosting cost ceiling and what it shapes: one machine, one worker,
  in-memory jobs, a database that sleeps, the release-command retry, no
  Redis or task queue;
- the job trust model: a job id is an unlisted link while the data is
  public; binding a job to the browser session arrives with the export
  upload (Batch 23 WP-4).

The README stays human (owner, 2026-09-29: "Keep the readme human, no
pointers"): no task or finding ids, no internal-document links, no
machine-checked figures that go stale. DEVELOPMENT.md tells the project's
history per the Task 21 brief.

Diagrams: every Mermaid block (README and the five files under
`docs/architecture/`) is checked against current source, corrected, run
through the Mermaid validator before commit, and given a fresh "Last
verified" date. Known drift in `top-albums-sequence.md`: the Spotify
unavailability path, the 303 redirect to `/loading`, the 500-row exclusion
cap, and the MusicBrainz "skipped" outcome.

Drift fixes: SESSION_CONTEXT Section 3's tree; `.env.example`
(`FLASK_ENV` is read by nothing; `DB_CONNECT_*` are read but undocumented);
`.codacy.yml`'s path for its `nosec` note; `config.py`'s line-number citations
replaced by names.

README sections are drafted in parallel into workspace files and landed by
one integrator, because parallel patches to one file collide. Each diagram
file is its own parallel task.

## UI PR (#7)

Round 1, CSS only: the results table's play count uses the figure face
(`--font-figure`, Gotham, weight 400 -- never bold, as the heatmap KPI rule
records). A frontend-gate check asserts the intended behaviour: the computed
font of a results play count equals that of a heatmap KPI value, at every
viewport the gate runs.

Later rounds come from the owner's annotated screenshots: one brief and one
implementer per round, the frontend gate, then the owner's review in Firefox.
Standing rules: use controls the shipped UI already has; text contrast aims
at 7:1 in both themes with 4.5:1 as the floor; mobile is the breakpoint of
concern. Template changes wait for #6, which edits the same templates.

## Out of scope

Job persistence; the tooling package and any control-plane change; key
rotation; Fly monitoring; self-hosting fonts or adding SRI; Batch 23 WP-1
onward.
