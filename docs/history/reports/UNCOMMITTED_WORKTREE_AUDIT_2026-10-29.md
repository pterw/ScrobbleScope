# Uncommitted worktree audit - 2026-10-29

Scope: read-only inspection of the owner preview and registered worktree
status during the Listening handoff. No owner files were staged, changed or
removed. This report is source-review evidence, not a mutation-test run.

## Preview reconciliation

Preview: `preview/streamgraph-context-halo` at `a968b863`. Feature baseline:
`feat/streamgraph-bursts` at `dd69ddd7`, PR #280. All ten tracked product
modifications and the untracked Listening illustration match feature HEAD
by Git-normalized blob hash. They are local previews of committed work.

| Preview path | Result |
|---|---|
| scrobblescope/routes/__init__.py | Matches feature HEAD |
| static/css/empty.css | Matches feature HEAD |
| static/css/heatmap.css | Matches feature HEAD |
| static/css/index.css | Matches feature HEAD |
| static/js/heatmap.js | Matches feature HEAD |
| static/js/index.js | Matches feature HEAD |
| templates/heatmap_empty.html | Matches feature HEAD |
| templates/index.html | Matches feature HEAD |
| templates/partials/_heatmap_form.html | Matches feature HEAD |
| templates/partials/_heatmap_result.html | Matches feature HEAD |
| templates/partials/_listening_example.html | Matches feature HEAD; untracked on preview branch |

The other thirteen untracked paths are independent owner material. Paths
below are inventory text, not claims that the files are tracked or approved.

| Owner path | Review boundary |
|---|---|
| .mcp.json | Valid JSON; configuration keys reviewed, values omitted |
| app.json | Valid JSON; deployment snapshot keys reviewed, values omitted |
| docs/superpowers/plans/2026-10-01-f-swe-7-utils-split.md | Independent F-SWE-7 plan; execution not audited |
| docs/superpowers/plans/ScrobbleScope_A_DoublePrime_Context_Halo_Spec.md | Owner design reference |
| docs/superpowers/plans/design_handoff_scrobblescope_audit/README.md | Reference bundle inventory |
| docs/superpowers/plans/design_handoff_scrobblescope_audit/ScrobbleScope Audit v6.dc.html | Inventoried, not executed or semantically audited |
| docs/superpowers/plans/design_handoff_scrobblescope_audit/docs/assets/scrobble_scope_lockup_dark.svg | Reference asset inventory |
| docs/superpowers/plans/design_handoff_scrobblescope_audit/docs/assets/scrobble_scope_lockup_light.svg | Reference asset inventory |
| docs/superpowers/plans/design_handoff_scrobblescope_audit/support.js | Reference bundle inventory; not executed |
| docs/superpowers/plans/design_handoff_scrobblescope_audit/uploads/pasted-1793117816284-0.png | Reference image inventory |
| scripts/dev/mutation_scope.toml | Unadopted tooling; F-SWE-8 |
| scripts/dev/mutation_test.py | Unadopted tooling; F-SWE-8 |
| tests/scripts/dev/test_mutation_test.py | Unadopted tooling tests; F-SWE-8 |

## Fresh F-SWE-8 evidence

The existing owner-gated finding in `docs/agents/FINDINGS.md` owns adoption
and status. These source observations reinforce its existing restriction:
keep the tooling out of unrelated commits and do not use its output as
verification evidence. No mutation run or dependency installation occurred.

- Runner lines 245-264 flatten serialized WorkItem/WorkResult pairs, while
  lines 307-318 expect an embedded outcome. Installed cosmic-ray 8.7.0
  serializes separate paired records (its cli.py lines 204-229). A pure
  authentic-shape reproduction classified one mutant as unknown, with no
  recognized survivor; the runner's final return expression was still zero.
- Runner lines 543-578 ignore execution/dump return status and succeed when
  the recognized survivor set is empty, including unknown or missing results.
- Tests lines 58-72 and 512-530 use an invented merged result schema, so
  their apparent success does not challenge the installed serialization.
- Runner lines 231-238 escape TOML without shell-quoting the interpreter.
  The installed testing.py lines 62-63 use shlex.split. A pure check with
  the qualified Windows interpreter produced a different first token.
- Classify line 318 compares stdout instead of the verdict. Passing pytest
  output differing only in elapsed time was classified as killed.
- Dirty detection at lines 436-453 fails open on Git failures. Digest
  verification at lines 557-565 is outside finally, so early returns,
  errors or interruption skip it. The wrapper supplies no backup/restore.
- cosmic-ray 8.7.0 is installed locally but was not found in the inspected
  requirements, pyproject, pre-commit or workflow declarations. Adoption
  needs a reproducible dependency decision before installation elsewhere.

Both Python files compiled in memory. The TOML parsed, and its seven scoped
modules and eight test paths exist. These checks establish syntax and paths
only. Reproduce and repair the findings in a separately authorized F-SWE-8
work package, using real tool records and failure-path tests.

## Other registered worktrees

Counts are a point-in-time status inventory, not a content or ownership audit.
Dirty work was preserved. No worktree was removed.

| Checkout | Dirty paths |
|---|---:|
| Primary Python Projects checkout | 1: untracked .codex/hooks.json |
| C:/ssw/proto | 11 |
| C:/ssw/sg-live-integration | 4 |
| C:/ssw/t1 | 6 |
| C:/ssw/t2 | 4 |
| C:/ssw/t3 | 6 |
| C:/ssw/t4 | 12 |
| C:/ssw/t5 | 2 |
| C:/ssw/t6 | 3 |
| C:/ssw/t7 | 2 |
| C:/ssw/t8-gate | 1 |
| C:/ssw/t8-renderer | 2 |
| C:/ssw/t9-backend | 4 |
| C:/ssw/t10-gate | 2 |
| C:/ssw/t10-ui | 3 |
| C:/ssw/u5 | 0 |
| C:/ssw/u7 at audit start | 0 |
| Owner preview | 24 |

Graph evidence was Tier 2, generation 2026-10-29T07:12:48Z, with changed
metadata freshness. Direct source and normalized-blob comparisons support
these conclusions. Reference SVG/PNG files were excluded from the graph;
index.css has a recorded parse gap at line 333, checked directly.
