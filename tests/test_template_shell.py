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

    texts = [sheet.read_text(encoding="utf-8") for sheet in sheets]
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
def test_every_page_sets_the_theme_before_first_paint(app, template):
    """The marker must be on <html>, and set in head, or the page flashes."""
    with app.test_request_context("/"):
        html = render_template(template, **TEMPLATE_CONTEXT[template])

    assert 'data-theme="light"' in html
    head = html.split("</head>")[0]
    assert "localStorage.getItem('darkMode')" in head
    assert "use.typekit.net/rwy8ghw.css" in head
