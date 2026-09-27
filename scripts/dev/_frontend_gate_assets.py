"""Stylesheet isolation: each page loads exactly one framework stylesheet.

A slice of the frontend gate (F-B21-51). Bootstrap and daisyUI both claim
.btn, .card and .modal, and Tailwind's preflight would reset a Bootstrap page,
so two framework sheets on one page is a collision, not a style choice.
"""

from __future__ import annotations

import re
from pathlib import Path

from scripts.dev._frontend_gate_shared import ALL_PAGES

#: Marker that identifies a Bootstrap stylesheet in a link href.
BOOTSTRAP_MARKER = "bootstrap"

#: Marker that identifies the compiled Tailwind stylesheet in a link href.
TAILWIND_MARKER = "tailwind.css"

REPO_ROOT = Path(__file__).resolve().parents[2]

#: The two inline mark assets the mark-colouring mechanism relies on
#: (F-B21-23): no per-wrapper CSS list, so the assets have to colour
#: themselves.
INLINE_MARK_TEMPLATES = (
    REPO_ROOT / "templates" / "inline" / "scrobble_scope_inline.svg",
    REPO_ROOT / "templates" / "inline" / "scrobble_scope_lockup_inline.svg",
)

#: A literal hex colour anywhere in the file means the asset stopped
#: colouring itself and some wrapper would need naming again.
_HEX_COLOUR_RE = re.compile(r"#[0-9a-fA-F]{6}")


def _stylesheet_hrefs(page) -> list[str]:
    """Return the href of every stylesheet link the page loads."""
    return page.eval_on_selector_all(
        "link[rel=stylesheet]", "nodes => nodes.map(node => node.href)"
    )


def check_stylesheet_isolation(page, base_url: str) -> list[str]:
    """Each page loads exactly one framework stylesheet.

    Bootstrap and daisyUI both claim .btn, .card and .modal, and Tailwind's
    preflight would reset a Bootstrap page. Loading both is the collision the
    strangler migration exists to avoid.
    """
    failures = []
    for path in ALL_PAGES:
        page.goto(f"{base_url}{path}", wait_until="load")
        hrefs = _stylesheet_hrefs(page)
        framework = [
            href
            for href in hrefs
            if BOOTSTRAP_MARKER in href.lower() or TAILWIND_MARKER in href.lower()
        ]
        # Exactly one, not merely "not both". Two Bootstrap links is the
        # cdnjs/jsdelivr split this batch tracks as F-B20-3, and it fails here.
        if len(framework) != 1:
            failures.append(
                f"{path} loads {len(framework)} framework stylesheets, "
                f"expected exactly 1: {framework}"
            )
    return failures


def check_inline_marks_need_no_wrapper_list(page, base_url: str) -> list[str]:
    """The inline mark assets colour themselves; no wrapper has to list them.

    An asset-content fact, not a rendered one (F-B21-23): each SVG template
    is read directly off disk. `fill="currentColor"` on the root element and
    `stroke: var(--bars-color)` in the `<style>` block are what let any
    wrapper that merely sets `color` produce a correct mark; a literal hex
    colour anywhere in the file means that mechanism has been undone.
    """
    failures = []
    for template in INLINE_MARK_TEMPLATES:
        text = template.read_text(encoding="utf-8")
        if 'fill="currentColor"' not in text:
            failures.append(f'{template.name} is missing fill="currentColor"')
        if "stroke: var(--bars-color)" not in text:
            failures.append(f"{template.name} is missing stroke: var(--bars-color)")
        hex_hits = _HEX_COLOUR_RE.findall(text)
        if hex_hits:
            failures.append(f"{template.name} has a literal hex colour: {hex_hits}")
    return failures
