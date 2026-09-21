"""State and helpers more than one frontend gate slice reads.

F-B21-51 splits the gate by concern. What lives here is what two or more
slices read, so each slice can import it without importing the facade that
imports them (a cycle). The page inventories and `GATE_JOB_IDS` are mutated in
place by `serve_app` for the length of a run; importing them by name keeps
every module on the same objects, and nothing may rebind them.
"""

from __future__ import annotations

#: Clicking budget for the theme toggle. Short, because a miss means the
#: control is absent or unclickable, and waiting 30s does not change that.
TOGGLE_TIMEOUT_MS = 5000

#: Any unknown URL renders error.html through the app_errorhandler(404) in
#: scrobblescope/routes.py. There is no direct route to the error page.
ERROR_PAGE_PATH = "/no-such-page-for-the-gate"

#: Consumed by check_theme_tokens and check_fonts. Pages already migrated to
#: Tailwind. Each work package adds its page here, one line.
#:
#: Only migrated pages belong here. A Bootstrap page has no --color-primary
#: and loads no kit faces, so pointing those two checks at every page would
#: park four permanent failures in the output until WP-7 -- and a gate with
#: expected failures in it stops being read.
MIGRATED_PAGES = ["/", "/results", "/heatmap", "/unmatched", ERROR_PAGE_PATH]

#: Throwaway jobs owned by serve_app and driven by pipeline checks.
GATE_JOB_IDS: dict[str, str] = {}

#: Pages still served by Bootstrap. The tailwind migration is complete, so this
#: list is empty and stays declared: ``check_stylesheet_isolation`` takes both
#: inventories because "exactly one framework stylesheet" is a claim about every
#: page, migrated or not, and ``ALL_PAGES`` below consumes both. A future page
#: that reverts to a second framework belongs here rather than in
#: ``MIGRATED_PAGES``, which theme-token and font checks read.
#:
#: This replaces a comment that described the migration as still in progress
#: ("the job-backed Results and Unmatched templates remain on Bootstrap until
#: their work packages") above an already-empty list. Every template now carries
#: its own opt-out note -- results.html and unmatched.html both say "Migrated to
#: Tailwind, so this page opts out of the legacy Bootstrap stack" -- and README
#: states plainly that "Bootstrap is gone". The only Bootstrap left in this
#: module is ``BOOTSTRAP_MARKER``, which lets the isolation check prove a page
#: *would* collide if it reintroduced a Bootstrap stylesheet link, by reading
#: hrefs rather than serving one. Reading the stale comment as current is what
#: F-B21-61 warns about; the list, not the comment, was true.
LEGACY_PAGES = []

#: Consumed by check_stylesheet_isolation. Exactly one framework stylesheet is
#: a claim about every page, migrated or not, so this check takes both lists.
ALL_PAGES = [*LEGACY_PAGES, *MIGRATED_PAGES]


def _reach_state(page, actions) -> None:
    """Drive the page into one state, using real clicks and selections.

    Real interactions rather than dispatched events: a synthetic event can
    reach a listener that a genuine click could never trigger, and the check
    is about what a finger can do.
    """
    for action in actions:
        kind, selector = action[0], action[1]
        target = page.locator(selector).first
        if kind == "click":
            target.click(timeout=TOGGLE_TIMEOUT_MS)
        elif kind == "select":
            target.select_option(action[2], timeout=TOGGLE_TIMEOUT_MS)
        else:  # pragma: no cover - a typo in the table, not a page fault
            raise ValueError(f"unknown touch-target action {kind!r}")
