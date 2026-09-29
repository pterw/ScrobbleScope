"""Stylesheet isolation: each page loads exactly one framework stylesheet.

A slice of the frontend gate (F-B21-51). Bootstrap and daisyUI both claim
.btn, .card and .modal, and Tailwind's preflight would reset a Bootstrap page,
so two framework sheets on one page is a collision, not a style choice.
"""

from __future__ import annotations

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

#: Two wrappers that differ in both the `color` a mark takes its letterforms
#: from and the `--bars-color` its bars take their stroke from. The marks are
#: rendered inside each, so what is judged is what the browser paints.
_WRAPPER_PAINTS = (
    {"color": "rgb(10, 120, 30)", "bars": "rgb(200, 30, 90)"},
    {"color": "rgb(240, 200, 20)", "bars": "rgb(20, 60, 220)"},
)

#: Renders `markup` once per wrapper and reads back the computed paint: the
#: root element's own fill, the fill of every drawn shape that is not a bar,
#: and the stroke of every bar (the elements the style rule names `.cls-1`).
_MARK_PAINT_JS = """([markup, wrappers]) => wrappers.map(wrapper => {
    const host = document.createElement('div');
    host.style.color = wrapper.color;
    host.style.setProperty('--bars-color', wrapper.bars);
    host.innerHTML = markup;
    document.body.appendChild(host);
    const root = host.querySelector('svg');
    const shapes = [...root.querySelectorAll('path, rect, circle, line, polyline, polygon')];
    const bars = shapes.filter(el => el.matches('.cls-1'));
    const report = {
        expected: wrapper,
        hostColor: getComputedStyle(host).color,
        rootFill: getComputedStyle(root).fill,
        letterFills: [...new Set(shapes.filter(el => !el.matches('.cls-1'))
            .map(el => getComputedStyle(el).fill))],
        barStrokes: [...new Set(bars.map(el => getComputedStyle(el).stroke))],
        letterCount: shapes.length - bars.length,
        barCount: bars.length,
    };
    host.remove();
    return report;
})"""


def mark_paint_failures(name: str, reports: list[dict]) -> list[str]:
    """Judge what the browser painted for one mark in each wrapper.

    The root element's own `fill` and every letterform's fill must resolve to
    the wrapper's `color`, and every bar's stroke to the wrapper's
    `--bars-color`. A literal colour, a child `fill`, a stroke override later
    in the style rule, or `currentColor` that only survives in a comment all
    change what is painted, so all of them show here and none of them need a
    substring to be looked for.
    """
    failures = []
    for report in reports:
        wanted = report["hostColor"]
        bars = report["expected"]["bars"]
        if report["letterCount"] < 1 or report["barCount"] < 1:
            failures.append(
                f"{name} draws {report['letterCount']} letterform shapes and "
                f"{report['barCount']} bars; expected both"
            )
            continue
        if report["rootFill"] != wanted:
            failures.append(
                f"{name} root fill paints {report['rootFill']} inside a wrapper "
                f"whose color is {wanted}"
            )
        wrong_fills = [fill for fill in report["letterFills"] if fill != wanted]
        if wrong_fills:
            failures.append(
                f"{name} letterforms paint {wrong_fills} inside a wrapper "
                f"whose color is {wanted}"
            )
        wrong_strokes = [s for s in report["barStrokes"] if s != bars]
        if wrong_strokes:
            failures.append(
                f"{name} bars stroke {wrong_strokes} inside a wrapper whose "
                f"--bars-color is {bars}"
            )
    return failures


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

    Rendered, not read (F-B21-23): each SVG template is placed inside two
    wrappers that set different `color` and `--bars-color`, and the painted
    fill and stroke must follow each wrapper. `fill="currentColor"` on the
    root element and `stroke: var(--bars-color)` in the `<style>` block are
    what make that true; anything that undoes them changes a painted colour.
    """
    failures = []
    for template in INLINE_MARK_TEMPLATES:
        reports = page.evaluate(
            _MARK_PAINT_JS,
            [template.read_text(encoding="utf-8"), list(_WRAPPER_PAINTS)],
        )
        failures.extend(mark_paint_failures(template.name, reports))
    return failures
