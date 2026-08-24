"""Every page renders and loads exactly one framework stylesheet.

WP-2 moves Bootstrap and global.css out of base.html and into a per-page
block. A page that ends up with neither loses its theme completely, and a page
that ends up with both gets a Bootstrap/daisyUI class collision. Neither shows
up in any other test, and neither is visible until someone opens the page.

The browser gate checks the two pages it can reach over HTTP. This checks all
five, including the three that need a live job to reach.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from flask import render_template

from app import create_app

BOOTSTRAP = "bootstrap"
TAILWIND = "tailwind.css"

STATIC_CSS = Path(__file__).resolve().parents[1] / "static" / "css"
INLINE_SVG = Path(__file__).resolve().parents[1] / "templates" / "inline"

#: The bar baseline docs/design/README.md "Wordmark animation" names, and the
#: value shell.css uses as transform-origin for the pulse.
BAR_BASELINE = 63.5

#: The lockup's frame. The design project's own asset uses 0 0 453 69, which
#: cuts 3.2 units off the p descender in "Scope"; the owner took the extra 5
#: units on 2026-08-24. docs/design/RECONCILIATION.md records the deviation.
LOCKUP_VIEWBOX = "0 0 453 74"

#: Minimum context each template needs to render at all. The values are never
#: asserted on; they exist so Jinja can finish.
TEMPLATE_CONTEXT = {
    "index.html": {},
    "error.html": {},
    "loading.html": {
        "job_id": "job-1",
        "username": "someone",
        "year": "2024",
        "sort_by": "plays",
        "release_scope": "any",
        "decade": "",
        "release_year": "",
    },
    "results.html": {
        "job_id": "job-1",
        "username": "someone",
        "year": "2024",
    },
    "unmatched.html": {"reasons": {}},
}

#: Pages migrated to Tailwind. Every other page must still carry Bootstrap.
MIGRATED = {"error.html"}


@pytest.fixture
def app():
    """The application, for rendering templates outside a request."""
    application = create_app()
    application.config["TESTING"] = True
    return application


def _stylesheets(html: str) -> list[str]:
    """Return the href of every stylesheet link in the rendered page."""
    return re.findall(r'<link[^>]+rel="stylesheet"[^>]+href="([^"]+)"', html)


def _local_sheets(hrefs: list[str]) -> list[Path]:
    """Return the repository file behind every href that names a local sheet."""
    names = [href.rsplit("/", 1)[-1] for href in hrefs if "//" not in href]
    return [STATIC_CSS / name for name in names]


def _without_comments(text: str) -> str:
    """Return the stylesheet with every /* */ block removed.

    Both directions need this. A comment that names a token must not count as
    a definition, and prose that mentions var(--x) must not count as a read.
    """
    return re.sub(r"/\*.*?\*/", " ", text, flags=re.S)


def _declared(text: str) -> set[str]:
    """Return every custom property the stylesheet defines."""
    return set(re.findall(r"^\s*(--[\w-]+)\s*:", text, re.M))


def _read_without_fallback(text: str) -> set[str]:
    """Return every custom property the stylesheet reads with no fallback.

    A var() that carries a fallback still resolves when the token is absent,
    so only the bare form can break a declaration.
    """
    return {
        token
        for token, following in re.findall(r"var\(\s*(--[\w-]+)\s*(.?)", text)
        if following != ","
    }


@pytest.mark.parametrize("template", sorted(TEMPLATE_CONTEXT))
def test_every_page_loads_exactly_one_framework_stylesheet(app, template):
    """Two frameworks collide on .btn and .card; none strips the page's theme."""
    with app.test_request_context("/"):
        html = render_template(template, **TEMPLATE_CONTEXT[template])

    sheets = _stylesheets(html)
    bootstrap = [href for href in sheets if BOOTSTRAP in href.lower()]
    tailwind = [href for href in sheets if TAILWIND in href.lower()]

    assert len(bootstrap + tailwind) == 1, (
        f"{template} loads {len(bootstrap + tailwind)} framework stylesheets: "
        f"{bootstrap + tailwind}"
    )


@pytest.mark.parametrize("template", sorted(TEMPLATE_CONTEXT))
def test_each_page_loads_the_framework_its_markup_is_written_for(app, template):
    """A migrated page must not silently fall back to the legacy stack."""
    with app.test_request_context("/"):
        html = render_template(template, **TEMPLATE_CONTEXT[template])

    sheets = " ".join(_stylesheets(html)).lower()
    if template in MIGRATED:
        assert TAILWIND in sheets and BOOTSTRAP not in sheets
    else:
        assert BOOTSTRAP in sheets and TAILWIND not in sheets


@pytest.mark.parametrize("template", sorted(TEMPLATE_CONTEXT))
def test_every_page_carries_the_shared_shell(app, template):
    """The header bar and its stylesheet are on every page, migrated or not."""
    with app.test_request_context("/"):
        html = render_template(template, **TEMPLATE_CONTEXT[template])

    assert "css/shell.css" in html
    assert 'class="site-header"' in html
    # The frontend gate clicks .first, so a second match would silently decide
    # which control it drives.
    assert html.count("data-theme-toggle") == 1


@pytest.mark.parametrize("template", sorted(TEMPLATE_CONTEXT))
def test_every_custom_property_a_page_reads_is_defined_by_a_sheet_it_loads(
    app, template
):
    """An undefined var() with no fallback voids the whole declaration.

    It fails silently: no console error, no failing request, just a rule that
    stops applying. Tailwind emits a theme variable only when a generated
    utility uses it, so five tokens error.css reads were pruned out of the
    compiled sheet and the card lost its rounding. @theme static fixes that;
    this proves it, for every page rather than only the one that broke.

    The sheets are read back from the rendered page, so a template that starts
    or stops loading one is covered without editing this test. Bootstrap is a
    CDN file and is not checked; a var() it owns fails here, which is the
    right answer for a token the repository cannot see.

    Only handwritten sheets are checked as readers. tailwind.css is generated,
    and daisyUI leaves one dangling var() of its own in it -- .btn reads
    --fx-noise, which its suppressed :root block would have defined. That one
    is harmless, because the layer it paints is sized by --noise and every
    theme sets --noise to 0. Upstream quirks are not this test's business.
    """
    with app.test_request_context("/"):
        html = render_template(template, **TEMPLATE_CONTEXT[template])

    sheets = _local_sheets(_stylesheets(html))
    assert sheets, f"{template} loads no local stylesheet"

    texts = [_without_comments(sheet.read_text(encoding="utf-8")) for sheet in sheets]
    defined = set().union(*(_declared(text) for text in texts))

    for sheet, text in zip(sheets, texts):
        if sheet.name == TAILWIND:
            continue
        undefined = sorted(_read_without_fallback(text) - defined)
        assert not undefined, (
            f"{template} loads {sheet.name}, which reads {undefined} "
            f"with no fallback and no definition in "
            f"{sorted(other.name for other in sheets)}"
        )


@pytest.mark.parametrize("template", sorted(TEMPLATE_CONTEXT))
def test_the_header_mark_carries_no_smil_animation(app, template):
    """CSS cannot stop SMIL, so prefers-reduced-motion would never reach it.

    An <animate> with repeatCount="indefinite" ignores the media query
    entirely. The mark sits in a fixed header on every page and never
    scrolls away, so this would be permanent motion for a reader who asked
    for none. The bars animate from shell.css instead.

    Scoped to the header: the index hero wordmark and the pinwheel still
    carry SMIL, and those belong to F-B21-5.
    """
    with app.test_request_context("/"):
        html = render_template(template, **TEMPLATE_CONTEXT[template])

    header = html.split('<header class="site-header"', 1)[1]
    header = header.split("</header>", 1)[0]

    assert "<animate" not in header, (
        f"{template} ships SMIL inside the standing header, which no CSS "
        f"media query can pause"
    )


@pytest.mark.parametrize("template", sorted(TEMPLATE_CONTEXT))
def test_every_page_wraps_its_footer_extras(app, template):
    """The wrapper centres and spaces whatever a page adds after the content.

    Asserting the exact empty markup does double duty. It proves base.html
    still emits the wrapper, and it proves the tags stay on one line --
    `.page-footer-extras:empty` is what collapses the wrapper on the pages
    that add nothing, and a newline between the tags is a text node that
    stops :empty matching.
    """
    with app.test_request_context("/"):
        html = render_template(template, **TEMPLATE_CONTEXT[template])

    if template == "results.html":
        wrapper = html.split('<div class="page-footer-extras">', 1)[1]
        assert 'id="back-to-top"' in wrapper.split("</div>", 1)[0]
    else:
        assert '<div class="page-footer-extras"></div>' in html


def test_shell_stops_both_animations_under_reduced_motion():
    """Both rules are load-bearing and neither is obvious from its selector.

    The bar rule is the whole reason the SMIL was stripped. The footer rule
    restores opacity: cancelling a forwards animation that fades in from 0
    would otherwise hide the control permanently.
    """
    shell = (STATIC_CSS / "shell.css").read_text(encoding="utf-8")
    reduced = shell.split("@media (prefers-reduced-motion: reduce)", 1)[1]

    assert "#horizontal_bars path:nth-of-type(-n+5)" in reduced
    assert "opacity: 1;" in reduced


def _lockup() -> str:
    """The header lockup markup."""
    return (INLINE_SVG / "scrobble_scope_lockup_inline.svg").read_text(encoding="utf-8")


def _bar_feet(svg: str) -> list[float]:
    """Return where each vertical bar path ends, in SVG user units."""
    return [
        round(float(top) + float(length), 2)
        for _x, top, length in re.findall(r'd="M([\d.]+),([\d.]+)v([\d.]+)"', svg)
    ]


def test_the_lockup_bars_share_the_baseline_shell_css_scales_from():
    """Each bar must end at 63.50 or it pulses from the wrong foot.

    shell.css pins transform-origin to 0 63.5px for all five at once. The
    bars used to end between 63.46 and 63.70, so each one drifted a little
    as it scaled. Nothing rendered wrongly enough to notice, which is why a
    test holds it now.
    """
    feet = _bar_feet(_lockup())

    assert len(feet) == 5, f"expected five bars, found {len(feet)}"
    assert set(feet) == {BAR_BASELINE}, f"bars end at {sorted(set(feet))}"


def test_the_lockup_seats_its_letterforms_on_the_bar_baseline():
    """Without the transform the word floats above the bars.

    The lockup drops the tagline that the bars used to descend alongside, so
    the letterforms need seating on the bar baseline. This is a static
    attribute -- geometry, not motion. The letterforms never animate, which
    docs/design/README.md "Wordmark animation" requires.
    """
    group = re.search(r'<g id="logo-text"[^>]*>', _lockup())

    assert group is not None, "the lockup has no #logo-text group"
    assert "transform=" in group.group(
        0
    ), "#logo-text lost its transform, so the word floats above the bars"
    assert "scale(1.1)" in group.group(0)


def test_the_lockup_frame_keeps_the_whole_descender():
    """A clipped descender is invisible to every other gate.

    The design project's own lockup uses 0 0 453 69 and cuts the p in
    "Scope". Nothing else here would catch that, so the frame is pinned.
    """
    assert f'viewBox="{LOCKUP_VIEWBOX}"' in _lockup()


@pytest.mark.parametrize("template", sorted(TEMPLATE_CONTEXT))
def test_every_page_sets_the_theme_before_first_paint(app, template):
    """The marker must be on <html>, and set in head, or the page flashes."""
    with app.test_request_context("/"):
        html = render_template(template, **TEMPLATE_CONTEXT[template])

    assert 'data-theme="light"' in html
    head = html.split("</head>")[0]
    assert "localStorage.getItem('darkMode')" in head
    assert "use.typekit.net/rwy8ghw.css" in head
