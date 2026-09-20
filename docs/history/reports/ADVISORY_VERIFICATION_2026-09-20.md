# Review-advisory verification: PR #233, #234 and #235

Date: 2026-09-20
Scope: every substantive finding raised by Codacy, graphify and qlty across the
three PRs in the `test` integration series, checked against the on-disk code
rather than taken at face value.

Why this exists: PR #233 and #234 merged with their review threads
deliberately unaddressed, so acting on them became the pre-integration task.
A stale or unverified advisory is worse than no advisory, because acting on a
false one costs a real change and buries the true ones beside it. Each claim
below is therefore stated, then checked, then given a verdict.

Method: read the threads from the GitHub API
(`repos/pterw/ScrobbleScope/pulls/234/comments`, `/reviews`,
`/issues/234/comments`), then verify each claim by grepping the current tree,
reading the cited function, or running the cited gate. Nothing here was
verified by re-reading the bot's own summary.

## Summary

| # | Claim | Source | Severity claimed | Verdict |
|---|-------|--------|------------------|---------|
| 1 | Terminal-outcome detector treats negated prose ("not yet resolved") as completed | Codacy, graphify | MEDIUM | **Refuted** -- already handled and tested |
| 2 | `_PROSE_OUTCOME_RE` does not escape `_TERMINAL_SUFFIXES` keys | Codacy | LOW | **Refuted** -- already escaped |
| 3 | `as_cache_row` positional tuple is coupled to the unpack order | Codacy | LOW | **Partly true, wrong risk** -- see F-B22-7 |
| 4 | Blank line before a rotated block is skipped when `newest` is 0 | Codacy | LOW | **Refuted** -- guarded deliberately, and tested |
| 5 | `AlbumMetadata` cache-row method renamed and requires extra arguments | graphify | high | **Refuted** -- no caller at all; see F-B22-7 |
| 6 | Existing v1 paginated archives are hard-failed | graphify | high | **By design** -- documented refusal, Rule 7 |
| 7 | DOC023 documented as both blocking and non-blocking | graphify | medium | **Refuted** -- the catalogue states both roles precisely |
| 8 | Complexity and coupling ("fans out to N callees") | Codacy, graphify | various | **Not actionable** -- out of scope by owner ruling |

## 1. Negated prose treated as a completed finding

Claim: the DOC023 prose detector "may be prone to false positives (e.g., if
'resolved' appears in a negative context like 'not yet resolved')".

Verdict: refuted. `_NEGATED_OUTCOME_RE`
(`scripts/docsync/findings.py:368`) suppresses a claim when a `not` directly
qualifies the outcome word, and `_claims_a_terminal_outcome` applies it to the
text preceding every match.

Evidence: 14 synthetic findings were run through the real gate,
`collect_rot_issues`, by a probe that stores its own output
(`tmp/_zG_doc023_verdict.py` -> `tmp/_zG_doc023_verdict.txt`). Every negation
spelling is handled -- `not yet resolved`, `not resolved`, `**not** resolved`,
`not<TAB>yet resolved`, `NOT YET RESOLVED` -- while honest positives
(`This is resolved.`, `Resolved in WP-3.`, `Closed as no action.`) still block,
and words that merely contain a token (`unresolved`, `resolver`) do not.

The probe carries a vacuity guard, and it earned its place: the first run used
an `##` heading, which `FINDING_HEADING_RE` does not match, so every case
returned "blocks = False" and the table looked like a clean refutation of
nothing. The guard reports `VACUOUS PROBE` when no case parses. A summary of
"all cases passed" from that first run would have been a false green.

One boundary is worth recording, because it is deliberate: a `not` much
earlier in the sentence does not suppress a later real claim, so "we do not
know why. Resolved in WP-3." still blocks. That is asserted by
`test_negation_does_not_reach_across_a_sentence`.

The residual: outcome compounds negated by sense rather than by `not`. "No
action needed yet." and "No action taken so far." block. Filed as
F-DOCSYNC-14 and deliberately left alone -- see that entry for why widening
the window is the wrong trade.

## 2. `_TERMINAL_SUFFIXES` keys are not escaped

Claim: "The construction of `_PROSE_OUTCOME_RE` does not escape the keys from
`_TERMINAL_SUFFIXES`."

Verdict: refuted. The pattern is built as
`re.escape(key).replace(r"\ ", r"[-\s]")` (`scripts/docsync/findings.py:354`).
`re.escape` is present and wraps every key; the `.replace` that follows widens
a literal space to a whitespace class, which does not remove the escaping.

## 3. `as_cache_row` is coupled to the persistence unpack order

Claim (Codacy, LOW): the positional tuple is "tightly coupled to the database
persistence layer's unpack order. This makes the persistence contract
fragile."

Verdict: the coupling is real; the stated risk is not. See F-B22-7. The method
has no production caller, so no call site can break when the order moves. What
is actually wrong is the reverse of the concern: the order now has two owners,
and a test asserts the copy that nothing writes.

## 4. Blank line skipped when `newest` is 0

Claim: "The insertion of a blank line before a rotated block is skipped if
`newest` is 0."

Verdict: refuted as a defect. The guard is
`if newest > 0 and archive_lines[newest - 1].strip():`
(`scripts/docsync/findings.py:548`). `newest == 0` means an archive whose first
line is already an entry boundary, with no prologue; inserting a blank line at
index 0 would put a leading blank line at the top of the file, which is worse
than the spacing it would fix. The reviewer's own note concedes a prologue is
the normal case, and that case is handled -- it is exactly the bug `495e9c2`
fixed.

Evidence: `test_first_rotation_keeps_a_blank_line_under_the_prologue`
(`tests/test_docsync_findings.py:106`) asserts the first-rotation spacing.

## 5. AlbumMetadata cache-row method renamed and needs extra arguments

Claim (graphify, high): "AlbumMetadata cache-row method was renamed and now
requires extra arguments."

Verdict: refuted, and the high rating is unsupported. The method is
`as_cache_row` (`scrobblescope/enrichment.py:19`) and it has not been renamed.
It does take two arguments, `artist_norm` and `album_norm`, but no production
caller exists to pass them: a search across `scrobblescope/`, `tests/`,
`scripts/`, `templates/` and `static/` finds it at its definition and in
`tests/services/test_enrichment.py:14,42` only. Nothing is broken, because
nothing calls it.

That the claim is wrong does not make the site healthy. It surfaced a real
defect of a different kind, filed as F-B22-7.

## 6. Existing v1 paginated archives are hard-failed

Claim (graphify, high): existing v1 paginated archives now hard-fail.

Verdict: by design, and documented. `archives.structure_issue`
(`scripts/docsync/archives.py:86-115`) raises every archive-layout
disagreement as a blocking `DOC020`, and its docstring states why it refuses
rather than repairs: when an index and the pages beside it disagree, "deleting
the page the index does not name loses history, and rewriting the index to
match the files loses the record that the page existed. Only a reader knows
which happened."

That is Rule 7 ("never guess ... it reports and halts") and the
conflict-resolution rule "a wrong green is worse than a red", applied to a
migration. The cost is real and belongs to the owner: a repository carrying a
pre-reorder archive index must regenerate it by hand, which is what `4b36d6a`
implements. This repository has already migrated -- `doc_state_sync.py
--check` exits 0 on the current archive.

## 7. DOC023 documented as both blocking and non-blocking

Claim (graphify, medium): AGENTS.md contradicts the catalogue about DOC023.

Verdict: refuted. The two statements describe two different populations.

- `docs/architecture/documentation-tooling.md:216` -- DOC023 blocks "on an
  active finding whose prose claims a terminal outcome ... while carrying no
  lifecycle record."
- The same section, lines 221-223 -- findings listed under `[findings]
  grandfathered` are "reported once as a non-blocking warning carrying their
  live count."

`scripts/docsync/findings.py` implements exactly that split: `severity="error"`
for an unrecorded finding (`collect_rot_issues`, line 415) and
`severity="warning"` for the grandfathered count (line 436). AGENTS.md's own
sentence is about proven defects -- "A proven defect prints as a stable ERROR
DOC... diagnostic" -- and the grandfather warning is a counted advisory, not a
proven defect. The catalogue is the named owner of the full list, and AGENTS.md
links to it rather than restating it.

Worth noting for scope: `grandfathered` is currently empty
(`.docsync.toml`), so the warning branch has no members in this repository.
The behaviour is covered by
`test_a_grandfathered_finding_warns_once_with_a_live_count`.

## 8. Complexity and coupling findings

Not adjudicated, by owner ruling: complexity and coupling advisories are not
P0, P1 or P2 items and are not to be treated as actionable ahead of a sound
fix or a verified bug. The excluded set on PR #234 comprises the
`run_release_checks` complexity score, the repeated "contributes significantly
to the increased complexity of this file" comments, and graphify's coupling
deltas ("fans out to 7 callees", "9 callers depend on it").

Recorded so nobody re-adjudicates them as unaddressed findings. Rule 3 also
bears directly on one of them: the Codacy duplication request to merge the two
Deezer request prologues was declined at the second occurrence, and the
duplication was extracted inside the module instead (`a8e426f`).

## 14. "Residual Bootstrap" in the frontend gate

Claim (owner's working description, and the gate's own comment): the frontend
gate must "prevent DaisyUI, Tailwind v4, and residual Bootstrap from
colliding", implying pages still on Bootstrap.

Verdict: **there is no residual Bootstrap, and the comment saying so was
itself the defect.** `LEGACY_PAGES = []`. Every template carries an explicit
opt-out note (`results.html:5` and `unmatched.html:5` both read "Migrated to
Tailwind, so this page opts out of the legacy Bootstrap stack"), `static/css/`
contains no Bootstrap file, and README already stated "Bootstrap is gone".

What was wrong was `frontend_gate.py:209-215`, whose comment read "Pages still
served by Bootstrap. Move each one into MIGRATED_PAGES in the work package
that migrates it... The job-backed Results and Unmatched templates remain on
Bootstrap until their work packages" -- sitting directly above an
already-empty list. A reader trusting the comment would conclude two page
families were still unmigrated; the list, and the templates, said otherwise.

Corrected in place, with the real state and the reason an empty list stays
declared: `check_stylesheet_isolation` consumes both inventories because
"exactly one framework stylesheet" is a claim about every page, migrated or
not, so the list is a legitimate landing place for a future page that reverts.
The Bootstrap material still in the module is `bootstrap_fixture` and
`BOOTSTRAP_MARKER`, which serve a synthetic stylesheet so the isolation check
can prove a page *would* collide if it loaded both -- a test fixture, not a
live framework.

This is anti-pattern 15 in miniature: the architecture comment had drifted
from the code it described, and only reading the source rather than the
comment surfaced it.

## What this changed, in full

Before the fixes below, nothing in `scripts/docsync/` or the gate logic needed
repair for the four refuted claims, the escaped pattern, or the two deliberate
behaviours. What the verification actually produced:

| Change | Kind |
|---|---|
| `F-B22-7` filed -- `as_cache_row` unreachable from application code | Finding |
| `F-DOCSYNC-14` filed -- DOC023 blocks on the outcome-vocabulary compounds | Finding |
| `F-B22-2` retitled and extended from 3 sites to 6, stale line corrected | Finding corrected |
| `frontend_gate.py` stale Bootstrap comment replaced | **Defect fixed** |
| This report | Record |

The two findings are records, not repairs, and each says why the fix is an
owner decision rather than a mechanical one.

---

# PR #235 (test -> main)

PR #235 is the integration PR, 74 commits, 135 files. It had no substantive
logic findings of its own; its threads are the same class of advisory as
above, re-raised against the same code, plus two real security-flagged items
worth adjudicating because a security claim never gets the benefit of the
doubt.

## 9. qlty: 58 "blocking issues"

Claim: 58 blocking issues, itemised as function-parameter counts, return
counts, file complexity, one duplicated block and one deeply nested flow.

Verdict: not actionable, by the same owner ruling that governs the Codacy
complexity class. The categories are structural metrics, with no defect
asserted and no failing behaviour. The single duplication item ("found 30 lines
of similar code in 2 locations") is the class Rule 3 answers directly:
duplication is correct until the third occurrence, so a request to consolidate
at the second is a deviation request that may be declined by citing the rule.

## 10. `assert` at `scripts/docsync/findings.py:132`

Claim (Codacy, HIGH RISK): replace the `assert` with a conditional raise.

Verdict: **true, and it is the fourth site of a class already filed.** This is
not a new finding. `assert heading_match is not None` in `_build` is the same
`python -O` pattern as `F-B22-2`, which until now named only three
`album_flow.py` sites. Grepping for the pattern rather than for the reported
line found six sites across three files, including two in `spotify.py` that no
reviewer had flagged: `assert SPOTIFY_CLIENT_ID is not None` and the same for
the client secret. F-B22-2 has been retitled and extended to the whole class,
and its stale citation (line 302, now 309) corrected.

This is the instance-versus-class anti-pattern in miniature: acting on the
review comment alone would have fixed one of six, in the package the reviewer
happened to open.

## 11. `os.chmod(hook_path, 0o755)` in the hook installer

Claim (Codacy, HIGH RISK): set `0o700` instead, so that "only the user who
created the hook can read or execute it".

Verdict: **refuted.** The premise is that the file is confidential. It is not,
in three independent ways:

1. **It holds no secret.** The wrapper is a generated shell script whose whole
   content is a `case` statement on `SKIP` and an `exec` of
   `python -m pre_commit hook-impl`. It embeds two paths and no credential.
2. **It is reproducible from public source.** The generator,
   `scripts/dev/install_docsync_hook.py`, is committed. Anyone who can read the
   hook can read the file that writes it, and derive the contents exactly.
3. **`0o755` is git's own convention.** `git init` writes its sample hooks
   `0o755`, and a live hook must be executable. Restricting to `0o700` would
   make this file the odd one out in `.git/hooks/` with no confidentiality
   gained.

The residual is that the wrapper embeds filesystem paths, which discloses a
home-directory layout to another local user. That is not incremental exposure:
the same paths are in the committed generator, and the same local user can
already read them there. Adopting `0o700` would be a change with no threat
model behind it, so it is declined rather than applied to look responsive.

## 12. Coverage below the requirement

Claim (Codacy): new Batch 22 logic fails to satisfy coverage requirements.

Verdict: **misattributed.** The repository's own floor is
`--cov-fail-under=70` (`.github/workflows/test.yml:109`), and the measured
suite stands at 89% (SESSION_CONTEXT Section 1). What failed is Codacy's own
diff-coverage policy over the newly added lines, which is Codacy's threshold
and not this repository's gate. The Quality Gate badge reflects the
repository's gate, and it is green.

## 13. Title and description non-descriptive; split the PR

Claim (Codacy): the title "Test" and description "TO BE FILLED" are
non-descriptive, and a change of this size should be split.

Verdict: **the first half is true and was the real defect.** The metadata was
indeed a placeholder, and it is corrected in this PR. The second half is
declined: #235 is the `test` -> `main` integration PR, and its breadth is what
an integration PR is for. Splitting it would require either rewriting 74
commits of already-reviewed history or opening several PRs that each merge the
same branch, and "regressive changes must not reach `main`" is served by the
sequence `feature -> test -> main`, not by atomising the final hop.